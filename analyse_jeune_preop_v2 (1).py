"""
=============================================================================
ANALYSE STATISTIQUE DU JEÛNE PRÉOPÉRATOIRE
Hôpital Général de Douala — Chirurgie Élective 2026
=============================================================================
Auteur   : Script d'analyse — Étude transversale descriptive
Version  : 2.0 (colonnes corrigées après inspection du fichier Excel brut)
Standard : STROBE / bonnes pratiques épidémiologiques
Logiciel : Python 3 — pandas, numpy, matplotlib, seaborn, scipy
=============================================================================
MAPPING DÉFINITIF DES COLONNES (après inspection du fichier brut) :
  [0]  date_inclusion      [3]  sexe
  [4]  age                 [5]  antecedents
  [7]  nb_operations       [9]  score_asa
  [10] imc                 [11] type_chirurgie
  [13] specialite          [15] type_anesthesie
  [18] instructions_recues [21] source_instructions
  [24] consigne_liquide    [27] consigne_solide
  [30] patient_compris     [32] duree_jeune_solide
  [34] duree_jeune_liquide [36] retard_chirurgie
  [38] duree_retard
=============================================================================
"""

# ─────────────────────────────────────────────────────────────────────────────
# 0. IMPORTS ET CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
import pandas as pd
import numpy as np
import re
import os
import warnings
import matplotlib
matplotlib.use('Agg')                          # Rendu sans affichage graphique
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy import stats
from scipy.stats import chi2_contingency, mannwhitneyu, kruskal

warnings.filterwarnings('ignore')

# ── Chemins entrée / sortie ───────────────────────────────────────────────────
INPUT_FILE = '/mnt/user-data/uploads/collecte_de_données_1.xlsx'
OUTPUT_DIR = '/home/claude/jeune_preop/images'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Thème graphique global ────────────────────────────────────────────────────
sns.set_theme(style='whitegrid', font='DejaVu Sans')
PALETTE_SET2   = sns.color_palette('Set2',   12)
PALETTE_PAIRED = sns.color_palette('Paired', 12)
PALETTE_HUSL   = sns.color_palette('husl',   10)

plt.rcParams.update({
    'figure.dpi'       : 150,
    'axes.titlesize'   : 13,
    'axes.titleweight' : 'bold',
    'axes.labelsize'   : 11,
    'xtick.labelsize'  : 9,
    'ytick.labelsize'  : 9,
    'legend.fontsize'  : 9,
    'figure.titlesize' : 14,
    'figure.titleweight': 'bold',
})

# ── Seuils recommandés SFAR / ASA 2017 ───────────────────────────────────────
SEUIL_SOLIDE  = 6.0   # heures (solides légers)
SEUIL_LIQUIDE = 2.0   # heures (liquides clairs)


# ─────────────────────────────────────────────────────────────────────────────
# 1. FONCTIONS UTILITAIRES
# ─────────────────────────────────────────────────────────────────────────────
def parse_age(v):
    """Extrait l'entier depuis des valeurs mixtes : '39 ans', 54, 'M, 26ans'."""
    if pd.isna(v):
        return np.nan
    m = re.search(r'\d+', str(v))
    return int(m.group()) if m else np.nan


def parse_heure(v):
    """
    Convertit '08h00', '08H00', '8h', '8' → 8.0 (heures décimales).
    Format dominant dans le fichier : 'NNh00' où NN = heures.
    """
    if pd.isna(v):
        return np.nan
    s = str(v).strip().upper()
    # Pattern NNhMM ou NNH (ex : 08h00, 14h00, 06h00)
    m = re.match(r'^(\d{1,2})[Hh](\d{0,2})$', s)
    if m:
        hours   = int(m.group(1))
        minutes = int(m.group(2)) if m.group(2) else 0
        return round(hours + minutes / 60, 2)
    # Cas dégradé : chiffre seul
    m2 = re.search(r'\d+', s)
    return float(m2.group()) if m2 else np.nan


def normalize_sexe(v):
    """F/Féminin → 'Féminin' ; M/Masculin → 'Masculin'."""
    if pd.isna(v):
        return np.nan
    v = str(v).strip().upper()
    if v.startswith('F'):
        return 'Féminin'
    if v.startswith('M'):
        return 'Masculin'
    return np.nan


def normalize_asa(v):
    """ASAI / ASA I / AsAII → 'ASA I' ou 'ASA II'."""
    if pd.isna(v):
        return np.nan
    v = str(v).strip().upper().replace(' ', '')
    if 'ASAII' in v or 'ASA2' in v:
        return 'ASA II'
    if 'ASAI' in v or 'ASA1' in v:
        return 'ASA I'
    return np.nan


def normalize_specialite(v):
    """Harmonise les libellés de spécialité (minuscules, variantes multiples)."""
    if pd.isna(v):
        return 'Non renseigné'
    v = str(v).lower().strip()
    if any(k in v for k in ['orl', 'oph', 'ccf', 'oto']):
        return 'ORL / Ophtalmo'
    if any(k in v for k in ['gynéco', 'gyneco', 'gynécolog', 'obs']):
        return 'Gynécologie'
    if 'urol' in v:
        return 'Urologie'
    if any(k in v for k in ['neurochir', 'neurochi', 'neuro']):
        return 'Neurochirurgie'
    if any(k in v for k in ['orthop', 'ortho', 'othop']):
        return 'Orthopédie'
    if any(k in v for k in ['vasc', 'cv ', 'vascu']):
        return 'Chir. vasculaire'
    if any(k in v for k in ['viscér', 'visceral', 'visc', 'viscérale']):
        return 'Chir. viscérale'
    return 'Autre'


def normalize_anesthesie(v):
    """AG+IOT, AG, ALR, RA, AL, APD → libellé standardisé."""
    if pd.isna(v):
        return 'Non renseigné'
    v = str(v).strip().upper()
    if 'IOT' in v:
        return 'AG + IOT'
    if 'AG' in v:
        return 'AG seule'
    if 'APD' in v:
        return 'APD'
    if any(k in v for k in ['ALR', 'RA ']):
        return 'ALR / RA'
    if 'AL' in v:
        return 'AL'
    return 'Autre'


def norm_oui_non(v):
    """Normalise oui/OUI/o → 'OUI' ; non/NON → 'NON'."""
    if pd.isna(v):
        return 'Non renseigné'
    v = str(v).strip().lower()
    if v in ['oui', 'o', 'yes']:
        return 'OUI'
    if v in ['non', 'n', 'no']:
        return 'NON'
    return 'Non renseigné'


def norm_source(v):
    """Catégorise la source des instructions de jeûne."""
    if pd.isna(v):
        return 'Non renseigné'
    v = str(v).lower()
    if 'sage' in v:
        return 'Sage-femme'
    if 'infirm' in v:
        return 'Infirmier(ère)'
    if any(k in v for k in ['médecin', 'anesth', 'docteur']):
        return 'Médecin / Anesthésiste'
    return 'Autre soignant'


def savefig(fig, name):
    """Sauvegarde une figure et affiche un message de confirmation."""
    path = f'{OUTPUT_DIR}/{name}'
    fig.savefig(path, bbox_inches='tight', dpi=150)
    plt.close(fig)
    print(f"  → {name} sauvegardé")
    return path


# ─────────────────────────────────────────────────────────────────────────────
# 2. CHARGEMENT ET NETTOYAGE DES DONNÉES
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("  ÉTAPE 1 — CHARGEMENT ET NETTOYAGE DES DONNÉES")
print("="*70)

raw = pd.read_excel(INPUT_FILE, header=0)

# ── Extraction des colonnes utiles par index de position ─────────────────────
# (les en-têtes Excel contiennent des doublons : données réelles dans col+1)
df = pd.DataFrame({
    'date_inclusion'     : raw.iloc[:, 0],
    'nom'                : raw.iloc[:, 2],
    'sexe'               : raw.iloc[:, 3].apply(normalize_sexe),
    'age'                : raw.iloc[:, 4].apply(parse_age),
    'antecedents'        : raw.iloc[:, 5],
    'nb_op'              : raw.iloc[:, 7],
    'score_asa'          : raw.iloc[:, 9].apply(normalize_asa),
    'imc'                : pd.to_numeric(raw.iloc[:, 10], errors='coerce'),
    'type_chirurgie'     : raw.iloc[:, 11],
    'specialite'         : raw.iloc[:, 13].apply(normalize_specialite),
    'type_anesthesie'    : raw.iloc[:, 15].apply(normalize_anesthesie),
    'instructions_recues': raw.iloc[:, 18].apply(norm_oui_non),
    'source_instructions': raw.iloc[:, 21].apply(norm_source),
    'consigne_liquide'   : raw.iloc[:, 24].apply(norm_oui_non),
    'consigne_solide'    : raw.iloc[:, 27].apply(norm_oui_non),
    'patient_compris'    : raw.iloc[:, 30].apply(norm_oui_non),
    'duree_solide_h'     : raw.iloc[:, 32].apply(parse_heure),
    'duree_liquide_h'    : raw.iloc[:, 34].apply(parse_heure),
    'retard_chirurgie'   : raw.iloc[:, 36].apply(norm_oui_non),
    'duree_retard_h'     : raw.iloc[:, 38].apply(parse_heure),
})

# ── Suppression des lignes vides (pas de nom et pas d'âge) ───────────────────
df = df.dropna(subset=['nom', 'age']).reset_index(drop=True)

# ── Variables dérivées ────────────────────────────────────────────────────────
# Catégorie IMC (classification OMS)
bins_imc   = [0, 18.5, 24.99, 29.99, 100]
labels_imc = ['Insuffisance pondérale\n(<18,5)',
               'Poids normal\n(18,5–24,99)',
               'Surpoids\n(25–29,99)',
               'Obésité\n(≥30)']
df['imc_cat'] = pd.cut(df['imc'], bins=bins_imc, labels=labels_imc, right=True)

# Variable binaire : jeûne solide prolongé (> 9h)
def categorize_jeune(v):
    if pd.isna(v):
        return np.nan
    return 'Prolongé (>9h)' if v > 9 else 'Acceptable (≤9h)'
df['jeune_prolonge'] = df['duree_solide_h'].apply(categorize_jeune)

# Antécédents opératoires binaire
def antecedent_op(v):
    if pd.isna(v):
        return np.nan
    v = str(v).lower()
    return 'Oui' if 'opér' in v and 'jamais' not in v else 'Non'

df['antecedent_op_bin'] = df['antecedents'].apply(antecedent_op)

N = len(df)
print(f"  → {N} patients retenus après nettoyage")
print(f"  → {df['duree_solide_h'].notna().sum()} durées solide renseignées")
print(f"  → {df['duree_liquide_h'].notna().sum()} durées liquide renseignées")
print(f"  → {df['imc'].notna().sum()} IMC renseignés")


# ─────────────────────────────────────────────────────────────────────────────
# 3. OBJECTIF 1 — CARACTÉRISTIQUES SOCIODÉMOGRAPHIQUES ET CLINIQUES
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("  OBJECTIF 1 — CARACTÉRISTIQUES SOCIODÉMOGRAPHIQUES ET CLINIQUES")
print("="*70)

# ── 3.1 SEXE ──────────────────────────────────────────────────────────────────
print("\n── Sexe ──")
sexe_tab = (df['sexe'].value_counts(dropna=False)
              .rename_axis('Sexe').reset_index(name='n'))
sexe_tab['%'] = (sexe_tab['n'] / N * 100).round(1)
print(sexe_tab.to_string(index=False))

fig, ax = plt.subplots(figsize=(6, 5))
colors_s = [PALETTE_SET2[0], PALETTE_SET2[1], 'lightgrey']
valids   = sexe_tab[sexe_tab['Sexe'].notna() & (sexe_tab['Sexe'] != 'Non renseigné')]
bars = ax.bar(valids['Sexe'], valids['n'],
              color=[PALETTE_SET2[0], PALETTE_SET2[1]],
              edgecolor='white', linewidth=1.5, width=0.45)
for bar, (_, row) in zip(bars, valids.iterrows()):
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 0.5,
            f'{row["n"]} ({row["%"]}%)',
            ha='center', va='bottom', fontweight='bold', fontsize=11)
ax.set_title(f'Répartition par sexe (N = {N})')
ax.set_xlabel('Sexe')
ax.set_ylabel('Effectif')
ax.set_ylim(0, valids['n'].max() * 1.2)
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout()
savefig(fig, '01_sexe.png')

# ── 3.2 ÂGE ───────────────────────────────────────────────────────────────────
print("\n── Âge ──")
age = df['age'].dropna()
print(f"  n={len(age)} | Moyenne={age.mean():.1f} ans | Médiane={age.median():.0f} ans "
      f"| ET={age.std():.1f} | Min={age.min():.0f} | Max={age.max():.0f}")
print(f"  Q1={age.quantile(0.25):.0f} | Q3={age.quantile(0.75):.0f}")

# Groupes d'âge pédiatriques vs adultes
df['groupe_age'] = pd.cut(df['age'],
    bins=[0, 15, 30, 45, 60, 150],
    labels=['<15 ans', '15–30 ans', '31–45 ans', '46–60 ans', '>60 ans'])
age_grp = df['groupe_age'].value_counts().sort_index().reset_index()
age_grp.columns = ['Groupe', 'n']
age_grp['%'] = (age_grp['n'] / N * 100).round(1)
print(age_grp.to_string(index=False))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
# Histogramme
ax1.hist(age, bins=16, color=PALETTE_SET2[2], edgecolor='white', linewidth=1)
ax1.axvline(age.mean(),   color='red',  ls='--', lw=2,
            label=f'Moyenne = {age.mean():.1f} ans')
ax1.axvline(age.median(), color='navy', ls=':',  lw=2,
            label=f'Médiane = {age.median():.0f} ans')
ax1.set_title('Distribution des âges')
ax1.set_xlabel('Âge (ans)')
ax1.set_ylabel('Effectif')
ax1.legend()
ax1.spines[['top', 'right']].set_visible(False)
# Barres par groupe d'âge
bars2 = ax2.bar(age_grp['Groupe'], age_grp['n'],
                color=sns.color_palette('Blues_d', len(age_grp)),
                edgecolor='white', linewidth=1)
for bar, row in zip(bars2, age_grp.itertuples()):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
             f'{row.n}\n({row._3}%)',
             ha='center', va='bottom', fontsize=9, fontweight='bold')
ax2.set_title('Effectifs par groupe d\'âge')
ax2.set_xlabel('Groupe d\'âge')
ax2.set_ylabel('Effectif')
ax2.set_ylim(0, age_grp['n'].max() * 1.25)
ax2.spines[['top', 'right']].set_visible(False)
fig.suptitle(f'Analyse de l\'âge (n = {len(age)})')
plt.tight_layout()
savefig(fig, '02_age.png')

# ── 3.3 IMC ───────────────────────────────────────────────────────────────────
print("\n── IMC ──")
imc = df['imc'].dropna()
print(f"  n={len(imc)} | Moyenne={imc.mean():.1f} | Médiane={imc.median():.1f} | ET={imc.std():.1f}")
imc_cat_tab = (df['imc_cat'].value_counts().reindex(labels_imc)
                 .reset_index())
imc_cat_tab.columns = ['Catégorie', 'n']
imc_cat_tab['%'] = (imc_cat_tab['n'] / len(imc) * 100).round(1)
print(imc_cat_tab.to_string(index=False))
n_surpoids = imc_cat_tab.loc[
    imc_cat_tab['Catégorie'].str.contains('Surpoids|Obésité', na=False), 'n'].sum()
pct_surpoids = round(n_surpoids / len(imc) * 100, 1) if len(imc) > 0 else 0
print(f"  → Surpoids + Obésité : {n_surpoids}/{len(imc)} ({pct_surpoids}%)")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
ax1.hist(imc, bins=14, color=PALETTE_SET2[3], edgecolor='white', linewidth=1)
ax1.axvline(18.5,  color='blue',   ls=':', lw=1.5, label='Seuil sous-poids (18,5)')
ax1.axvline(25.0,  color='orange', ls=':', lw=1.5, label='Seuil surpoids (25)')
ax1.axvline(30.0,  color='red',    ls=':', lw=1.5, label='Seuil obésité (30)')
ax1.axvline(imc.mean(), color='black', ls='--', lw=2,
            label=f'Moyenne = {imc.mean():.1f}')
ax1.set_title('Distribution de l\'IMC')
ax1.set_xlabel('IMC (kg/m²)')
ax1.set_ylabel('Effectif')
ax1.legend(fontsize=7.5)
ax1.spines[['top', 'right']].set_visible(False)
colors_imc = [PALETTE_SET2[i] for i in range(len(imc_cat_tab))]
bars_imc = ax2.barh(imc_cat_tab['Catégorie'], imc_cat_tab['n'],
                    color=colors_imc, edgecolor='white', linewidth=1)
for bar, row in zip(bars_imc, imc_cat_tab.itertuples()):
    ax2.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2,
             f'{row.n} ({row._3}%)',
             va='center', fontsize=9, fontweight='bold')
ax2.set_title('Répartition par catégorie IMC (OMS)')
ax2.set_xlabel('Effectif')
ax2.set_xlim(0, imc_cat_tab['n'].max() * 1.4)
ax2.spines[['top', 'right']].set_visible(False)
fig.suptitle(f'Indice de Masse Corporelle (n = {len(imc)})')
plt.tight_layout()
savefig(fig, '03_imc.png')

# ── 3.4 SCORE ASA ─────────────────────────────────────────────────────────────
print("\n── Score ASA ──")
asa_df = df.dropna(subset=['score_asa'])
asa_tab = (asa_df.groupby('score_asa')
           .agg(n=('score_asa', 'count'),
                age_moy=('age', lambda x: round(x.mean(), 1)),
                age_et=('age',  lambda x: round(x.std(), 1)))
           .reset_index())
asa_tab['%'] = (asa_tab['n'] / N * 100).round(1)
print(asa_tab.to_string(index=False))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
asa_colors = [PALETTE_SET2[i] for i in range(len(asa_tab))]
# Pie
wedges, texts, autos = ax1.pie(
    asa_tab['n'], labels=asa_tab['score_asa'],
    autopct='%1.1f%%',
    colors=asa_colors,
    startangle=90,
    pctdistance=0.72,
    wedgeprops=dict(edgecolor='white', linewidth=2))
for a in autos:
    a.set_fontsize(11); a.set_fontweight('bold')
ax1.set_title('Répartition par score ASA')
# Barres âge moyen par ASA
ax2.bar(asa_tab['score_asa'], asa_tab['age_moy'],
        color=asa_colors, edgecolor='white', linewidth=1.5, width=0.45,
        yerr=asa_tab['age_et'], capsize=6,
        error_kw=dict(ecolor='gray', linewidth=1.5))
for i, row in asa_tab.iterrows():
    ax2.text(i, row['age_moy'] + row['age_et'] + 1,
             f'{row["age_moy"]} ans\n(n={row["n"]})',
             ha='center', va='bottom', fontsize=9, fontweight='bold')
ax2.set_title('Âge moyen par score ASA (± ET)')
ax2.set_xlabel('Score ASA')
ax2.set_ylabel('Âge moyen (ans)')
ax2.set_ylim(0, asa_tab['age_moy'].max() + asa_tab['age_et'].max() + 15)
ax2.spines[['top', 'right']].set_visible(False)
plt.tight_layout()
savefig(fig, '04_asa.png')

# ── 3.5 SPÉCIALITÉ CHIRURGICALE ───────────────────────────────────────────────
print("\n── Spécialité chirurgicale ──")
spec_tab = (df['specialite'].value_counts().reset_index())
spec_tab.columns = ['Spécialité', 'n']
spec_tab['%'] = (spec_tab['n'] / N * 100).round(1)
print(spec_tab.to_string(index=False))

fig, ax = plt.subplots(figsize=(10, 6))
palette_sp = sns.color_palette('tab10', len(spec_tab))
bars_sp = ax.barh(spec_tab['Spécialité'], spec_tab['n'],
                  color=palette_sp, edgecolor='white', linewidth=1)
for bar, row in zip(bars_sp, spec_tab.itertuples()):
    ax.text(bar.get_width() + 0.3,
            bar.get_y() + bar.get_height()/2,
            f'{row.n} ({row._3}%)',
            va='center', fontsize=9, fontweight='bold')
ax.set_title(f'Répartition par spécialité chirurgicale (N = {N})')
ax.set_xlabel('Effectif')
ax.set_xlim(0, spec_tab['n'].max() * 1.35)
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout()
savefig(fig, '05_specialite.png')

# ── 3.6 TYPE D'ANESTHÉSIE ─────────────────────────────────────────────────────
print("\n── Type d'anesthésie ──")
anes_tab = df['type_anesthesie'].value_counts().reset_index()
anes_tab.columns = ['Type', 'n']
anes_tab['%'] = (anes_tab['n'] / N * 100).round(1)
print(anes_tab.to_string(index=False))

fig, ax = plt.subplots(figsize=(8, 5))
bars_a = ax.bar(anes_tab['Type'], anes_tab['n'],
                color=sns.color_palette('Paired', len(anes_tab)),
                edgecolor='white', linewidth=1.5, width=0.55)
for bar, row in zip(bars_a, anes_tab.itertuples()):
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 0.3,
            f'{row.n}\n({row._3}%)',
            ha='center', va='bottom', fontsize=9, fontweight='bold')
ax.set_title(f'Répartition par type d\'anesthésie (N = {N})')
ax.set_xlabel('Type d\'anesthésie')
ax.set_ylabel('Effectif')
ax.set_ylim(0, anes_tab['n'].max() * 1.25)
ax.tick_params(axis='x', rotation=20)
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout()
savefig(fig, '06_anesthesie.png')

# ── 3.7 ANTÉCÉDENTS OPÉRATOIRES ───────────────────────────────────────────────
print("\n── Antécédents opératoires ──")
ant_tab = df['antecedent_op_bin'].value_counts().reset_index()
ant_tab.columns = ['Antécédents', 'n']
ant_tab['%'] = (ant_tab['n'] / N * 100).round(1)
print(ant_tab.to_string(index=False))

fig, ax = plt.subplots(figsize=(6, 5))
ax.bar(ant_tab['Antécédents'], ant_tab['n'],
       color=[PALETTE_SET2[4], PALETTE_SET2[5]],
       edgecolor='white', linewidth=1.5, width=0.45)
for i, row in ant_tab.iterrows():
    ax.text(i, row['n'] + 0.5, f'{row["n"]} ({row["%"]}%)',
            ha='center', va='bottom', fontweight='bold', fontsize=11)
ax.set_title('Antécédents d\'opérations antérieures')
ax.set_xlabel('Déjà opéré')
ax.set_ylabel('Effectif')
ax.set_ylim(0, ant_tab['n'].max() * 1.2)
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout()
savefig(fig, '07_antecedents.png')


# ─────────────────────────────────────────────────────────────────────────────
# 4. OBJECTIF 2 — DURÉE DU JEÛNE PRÉOPÉRATOIRE
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("  OBJECTIF 2 — DURÉE DU JEÛNE PRÉOPÉRATOIRE")
print("="*70)

sol = df['duree_solide_h'].dropna()
liq = df['duree_liquide_h'].dropna()

# ── Statistiques descriptives ─────────────────────────────────────────────────
print("\n── Statistiques jeûne solide ──")
print(f"  n={len(sol)} | Moy={sol.mean():.2f}h | Méd={sol.median():.1f}h "
      f"| ET={sol.std():.2f}h | Min={sol.min():.0f}h | Max={sol.max():.0f}h")
n_sol_prolonge = int((sol > 9).sum())
n_sol_sup_rec  = int((sol > SEUIL_SOLIDE).sum())
pct_sol_pro    = round(n_sol_prolonge / len(sol) * 100, 1)
pct_sol_rec    = round(n_sol_sup_rec  / len(sol) * 100, 1)
print(f"  Solide > {SEUIL_SOLIDE}h (recommandation) : {n_sol_sup_rec}/{len(sol)} ({pct_sol_rec}%)")
print(f"  Solide > 9h                      : {n_sol_prolonge}/{len(sol)} ({pct_sol_pro}%)")

print("\n── Statistiques jeûne liquide ──")
print(f"  n={len(liq)} | Moy={liq.mean():.2f}h | Méd={liq.median():.1f}h "
      f"| ET={liq.std():.2f}h | Min={liq.min():.0f}h | Max={liq.max():.0f}h")
n_liq_sup_rec = int((liq > SEUIL_LIQUIDE).sum())
n_liq_sup6    = int((liq > 6).sum())
pct_liq_rec   = round(n_liq_sup_rec / len(liq) * 100, 1)
pct_liq6      = round(n_liq_sup6    / len(liq) * 100, 1)
print(f"  Liquide > {SEUIL_LIQUIDE}h (recommandation) : {n_liq_sup_rec}/{len(liq)} ({pct_liq_rec}%)")
print(f"  Liquide > 6h                       : {n_liq_sup6}/{len(liq)} ({pct_liq6}%)")

# ── Figure distributions ──────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
for ax, data, seuil, titre, couleur, xtxt in [
    (ax1, sol, SEUIL_SOLIDE,  'Jeûne SOLIDE', PALETTE_SET2[0],
     f'Recommandation ≤{int(SEUIL_SOLIDE)}h (SFAR/ASA)'),
    (ax2, liq, SEUIL_LIQUIDE, 'Jeûne LIQUIDE', PALETTE_SET2[3],
     f'Recommandation ≤{int(SEUIL_LIQUIDE)}h (liquides clairs)'),
]:
    bins_h = np.arange(int(data.min()), int(data.max()) + 2, 1)
    ax.hist(data, bins=bins_h, color=couleur, edgecolor='white',
            linewidth=1, alpha=0.85)
    ax.axvline(seuil, color='red', ls='--', lw=2.5, label=xtxt)
    ax.axvline(data.mean(), color='navy', ls=':', lw=2,
               label=f'Moy. observée = {data.mean():.1f}h')
    ax.axvspan(seuil, data.max() + 1, alpha=0.08, color='red',
               label='Zone de dépassement')
    ax.set_title(titre)
    ax.set_xlabel('Durée (heures)')
    ax.set_ylabel('Effectif')
    ax.legend(fontsize=8)
    ax.spines[['top', 'right']].set_visible(False)
fig.suptitle('Distribution des durées de jeûne préopératoire\n'
             'versus recommandations internationales SFAR / ASA 2017')
plt.tight_layout()
savefig(fig, '08_distribution_jeune.png')

# ── Boxplots comparatifs ──────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 6))
bp_data = [sol.values, liq.values]
bp = ax.boxplot(bp_data, vert=True, patch_artist=True, widths=0.5,
                boxprops=dict(facecolor='lightblue', alpha=0.7),
                medianprops=dict(color='navy', linewidth=2.5),
                flierprops=dict(marker='o', markerfacecolor='red', markersize=5, alpha=0.5),
                whiskerprops=dict(linewidth=1.5),
                capprops=dict(linewidth=1.5))
bp['boxes'][0].set_facecolor(PALETTE_SET2[0])
bp['boxes'][1].set_facecolor(PALETTE_SET2[3])
ax.axhline(SEUIL_SOLIDE,  color='green',  ls='--', lw=2,
           label=f'Max recommandé solide ({int(SEUIL_SOLIDE)}h)')
ax.axhline(SEUIL_LIQUIDE, color='orange', ls='--', lw=2,
           label=f'Max recommandé liquide ({int(SEUIL_LIQUIDE)}h)')
ax.set_xticks([1, 2])
ax.set_xticklabels([f'Jeûne solide\n(n={len(sol)})',
                    f'Jeûne liquide\n(n={len(liq)})'], fontsize=11)
ax.set_ylabel('Durée (heures)')
ax.set_title('Boxplots des durées de jeûne\nvs recommandations SFAR/ASA 2017')
ax.legend(fontsize=9)
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout()
savefig(fig, '09_boxplots_jeune.png')

# ── Durées par spécialité ─────────────────────────────────────────────────────
print("\n── Jeûne moyen par spécialité ──")
jeune_spec = (df.groupby('specialite')
              .agg(n=('duree_solide_h', 'count'),
                   sol_moy=('duree_solide_h', lambda x: round(x.mean(), 1)),
                   sol_et =('duree_solide_h', lambda x: round(x.std(),  1)),
                   liq_moy=('duree_liquide_h', lambda x: round(x.mean(), 1)))
              .reset_index())
jeune_spec = jeune_spec[jeune_spec['specialite'] != 'Non renseigné']
print(jeune_spec.to_string(index=False))

fig, ax = plt.subplots(figsize=(12, 6))
x = np.arange(len(jeune_spec))
w = 0.36
b1 = ax.bar(x - w/2, jeune_spec['sol_moy'], w,
            label='Solide moyen (h)', color=PALETTE_SET2[0],
            edgecolor='white', yerr=jeune_spec['sol_et'], capsize=4,
            error_kw=dict(ecolor='gray', linewidth=1))
b2 = ax.bar(x + w/2, jeune_spec['liq_moy'], w,
            label='Liquide moyen (h)', color=PALETTE_SET2[3], edgecolor='white')
for bar in list(b1) + list(b2):
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 0.1,
            f'{bar.get_height():.1f}h',
            ha='center', va='bottom', fontsize=7.5, fontweight='bold')
ax.axhline(SEUIL_SOLIDE,  color='red',    ls='--', lw=2,
           label=f'Seuil solide ({int(SEUIL_SOLIDE)}h)')
ax.axhline(SEUIL_LIQUIDE, color='orange', ls='--', lw=2,
           label=f'Seuil liquide ({int(SEUIL_LIQUIDE)}h)')
ax.set_xticks(x)
ax.set_xticklabels(jeune_spec['specialite'], rotation=30, ha='right', fontsize=9)
ax.set_ylabel('Durée moyenne (heures)')
ax.set_title('Durée moyenne de jeûne par spécialité chirurgicale\n'
             '(barres d\'erreur = écart-type | lignes = seuils recommandés)')
ax.legend(fontsize=8)
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout()
savefig(fig, '10_jeune_par_specialite.png')


# ─────────────────────────────────────────────────────────────────────────────
# 5. OBJECTIF 3 — INSTRUCTIONS ET CONNAISSANCE
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("  OBJECTIF 3 — INSTRUCTIONS ET CONNAISSANCE")
print("="*70)

# ── Tableau instructions ──────────────────────────────────────────────────────
items_inst = {
    'Instructions reçues'    : 'instructions_recues',
    'Consigne : no liquide'  : 'consigne_liquide',
    'Consigne : no solide'   : 'consigne_solide',
    'Patient a compris'      : 'patient_compris',
}
rows_inst = []
for label, col in items_inst.items():
    oui = (df[col] == 'OUI').sum()
    non = (df[col] == 'NON').sum()
    nr  = (df[col] == 'Non renseigné').sum()
    rows_inst.append({
        'Item': label, 'OUI': oui, 'NON': non,
        'Non renseigné': nr, '% OUI': round(oui / N * 100, 1)
    })
inst_df = pd.DataFrame(rows_inst)
print(inst_df.to_string(index=False))

fig, ax = plt.subplots(figsize=(11, 5))
x_inst = np.arange(len(inst_df))
w_inst = 0.28
ax.bar(x_inst - w_inst, inst_df['OUI'],            w_inst,
       label='OUI', color=PALETTE_SET2[2], edgecolor='white')
ax.bar(x_inst,          inst_df['NON'],            w_inst,
       label='NON', color=PALETTE_SET2[5], edgecolor='white')
ax.bar(x_inst + w_inst, inst_df['Non renseigné'],  w_inst,
       label='Non renseigné', color='lightgrey', edgecolor='white')
for xi, row in zip(x_inst, inst_df.itertuples()):
    ax.text(xi - w_inst, row.OUI + 0.5,
            f'{row.OUI}\n({row._5}%)',
            ha='center', va='bottom', fontsize=9, fontweight='bold')
ax.set_xticks(x_inst)
ax.set_xticklabels(inst_df['Item'], rotation=15, ha='right', fontsize=9)
ax.set_title('Conformité aux instructions de jeûne préopératoire')
ax.set_ylabel('Effectif')
ax.legend(fontsize=9)
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout()
savefig(fig, '11_instructions.png')

# ── Source des instructions ────────────────────────────────────────────────────
print("\n── Source des instructions ──")
src_tab = df['source_instructions'].value_counts().reset_index()
src_tab.columns = ['Source', 'n']
src_tab['%'] = (src_tab['n'] / N * 100).round(1)
print(src_tab.to_string(index=False))

fig, ax = plt.subplots(figsize=(7, 5))
wedges, texts, autos = ax.pie(
    src_tab['n'],
    labels=src_tab['Source'],
    autopct=lambda p: f'{p:.1f}%\n(n={int(round(p*N/100))})',
    colors=[PALETTE_SET2[i] for i in range(len(src_tab))],
    startangle=90,
    pctdistance=0.73,
    wedgeprops=dict(edgecolor='white', linewidth=2))
for a in autos:
    a.set_fontsize(9)
ax.set_title('Source des instructions de jeûne reçues par les patients')
plt.tight_layout()
savefig(fig, '12_source_instructions.png')

# ── Durée jeûne selon compréhension du patient ────────────────────────────────
print("\n── Durée jeûne solide selon compréhension ──")
compris_grp = df.groupby('patient_compris')['duree_solide_h'].describe().round(2)
print(compris_grp)


# ─────────────────────────────────────────────────────────────────────────────
# 6. OBJECTIF 4 — FACTEURS ASSOCIÉS AU JEÛNE PROLONGÉ
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("  OBJECTIF 4 — FACTEURS ASSOCIÉS AU JEÛNE PROLONGÉ")
print("="*70)

# ── 6.1 Retard chirurgical ────────────────────────────────────────────────────
print("\n── Retard chirurgical ──")
ret_tab = df['retard_chirurgie'].value_counts().reset_index()
ret_tab.columns = ['Retard', 'n']
ret_tab['%'] = (ret_tab['n'] / N * 100).round(1)
print(ret_tab.to_string(index=False))

n_retard  = int((df['retard_chirurgie'] == 'OUI').sum())
pct_retard = round(n_retard / N * 100, 1)
ret_valid  = df[df['retard_chirurgie'] == 'OUI']['duree_retard_h'].dropna()
print(f"\n  Retards : {n_retard}/{N} ({pct_retard}%)")
if len(ret_valid) > 0:
    print(f"  Durée retard — min:{ret_valid.min():.0f}h | max:{ret_valid.max():.0f}h | "
          f"moy:{ret_valid.mean():.1f}h ± {ret_valid.std():.1f}h")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
# Donut retard
colors_r = [PALETTE_SET2[2], PALETTE_SET2[5]]
wedges2, _, autos2 = ax1.pie(
    [n_retard, N - n_retard],
    labels=['Avec retard', 'Sans retard'],
    autopct='%1.1f%%',
    colors=colors_r,
    startangle=90,
    pctdistance=0.72,
    wedgeprops=dict(edgecolor='white', linewidth=2, width=0.55))
ax1.set_title(f'Fréquence des retards chirurgicaux\n(n = {N})')
# Distribution durée retard
if len(ret_valid) > 0:
    bins_r = np.arange(int(ret_valid.min()), int(ret_valid.max()) + 2, 1)
    ax2.hist(ret_valid, bins=bins_r, color=PALETTE_SET2[4],
             edgecolor='white', linewidth=1)
    ax2.axvline(ret_valid.mean(), color='red', ls='--', lw=2,
                label=f'Moy. = {ret_valid.mean():.1f}h')
    ax2.set_title('Distribution des durées de retard')
    ax2.set_xlabel('Durée du retard (heures)')
    ax2.set_ylabel('Effectif')
    ax2.legend(fontsize=9)
    ax2.spines[['top', 'right']].set_visible(False)
plt.tight_layout()
savefig(fig, '13_retard_chirurgical.png')

# ── 6.2 Retard par spécialité ─────────────────────────────────────────────────
print("\n── Retard par spécialité ──")
# Compter retards et calculer % par spécialité
spec_ret = (df[df['retard_chirurgie'] == 'OUI']
            .groupby('specialite')
            .agg(n_ret=('retard_chirurgie', 'count'),
                 ret_moy=('duree_retard_h', lambda x: round(x.mean(), 1)),
                 ret_max=('duree_retard_h', lambda x: x.max()))
            .reset_index())
total_sp = df.groupby('specialite').size().reset_index(name='total')
spec_ret = spec_ret.merge(total_sp, on='specialite')
spec_ret['pct_ret'] = (spec_ret['n_ret'] / spec_ret['total'] * 100).round(1)
spec_ret = spec_ret[spec_ret['specialite'] != 'Non renseigné']
print(spec_ret.to_string(index=False))

fig, ax = plt.subplots(figsize=(11, 6))
palette_r2 = sns.color_palette('husl', len(spec_ret))
bars_sr = ax.bar(spec_ret['specialite'], spec_ret['pct_ret'],
                 color=palette_r2, edgecolor='white', linewidth=1, width=0.6)
for bar, row in zip(bars_sr, spec_ret.itertuples()):
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 0.4,
            f'{row.pct_ret}%\n(n={row.n_ret})',
            ha='center', va='bottom', fontsize=9, fontweight='bold')
ax.set_title('Pourcentage de retards chirurgicaux par spécialité')
ax.set_xlabel('Spécialité chirurgicale')
ax.set_ylabel('% de patients avec retard')
ax.set_ylim(0, spec_ret['pct_ret'].max() * 1.35)
ax.tick_params(axis='x', rotation=30)
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout()
savefig(fig, '14_retard_par_specialite.png')

# ── 6.3 Tests statistiques : facteurs associés au jeûne prolongé ─────────────
print("\n── Tests statistiques (Mann-Whitney U, Kruskal-Wallis, Chi²) ──")

# Préparer groupes jeûne prolongé vs non prolongé
sol_valid = df[['duree_solide_h', 'sexe', 'score_asa',
                'specialite', 'retard_chirurgie',
                'type_anesthesie', 'age']].dropna(subset=['duree_solide_h'])

# Test Mann-Whitney : jeûne solide selon sexe
for sexe_val, label in [('Masculin', 'Hommes'), ('Féminin', 'Femmes')]:
    pass

grp_h = sol_valid[sol_valid['sexe'] == 'Masculin']['duree_solide_h']
grp_f = sol_valid[sol_valid['sexe'] == 'Féminin']['duree_solide_h']
if len(grp_h) > 1 and len(grp_f) > 1:
    u_stat, p_sexe = mannwhitneyu(grp_h, grp_f, alternative='two-sided')
    print(f"  Sexe (H vs F) — Mann-Whitney U={u_stat:.1f}, p={p_sexe:.4f}")
    print(f"    Moy. H={grp_h.mean():.1f}h | Moy. F={grp_f.mean():.1f}h")

# Test Kruskal-Wallis : jeûne solide selon spécialité
spec_groups = [g['duree_solide_h'].values
               for _, g in sol_valid.groupby('specialite')
               if len(g) >= 3 and _ != 'Non renseigné']
if len(spec_groups) >= 2:
    h_stat, p_spec = kruskal(*spec_groups)
    print(f"  Spécialité — Kruskal-Wallis H={h_stat:.2f}, p={p_spec:.4f}")

# Test Mann-Whitney : jeûne selon présence de retard
grp_ret = sol_valid[sol_valid['retard_chirurgie'] == 'OUI']['duree_solide_h']
grp_nor = sol_valid[sol_valid['retard_chirurgie'] == 'NON']['duree_solide_h']
if len(grp_ret) > 1 and len(grp_nor) > 1:
    u2, p2 = mannwhitneyu(grp_ret, grp_nor, alternative='two-sided')
    print(f"  Retard (oui vs non) — Mann-Whitney U={u2:.1f}, p={p2:.4f}")
    print(f"    Moy. retard={grp_ret.mean():.1f}h | Moy. sans retard={grp_nor.mean():.1f}h")

# ── 6.4 Heatmap jeûne solide moyen : spécialité × anesthésie ──────────────────
pivot = (df.groupby(['specialite', 'type_anesthesie'])['duree_solide_h']
          .mean().round(1).unstack())
pivot = pivot.drop(index='Non renseigné', errors='ignore')
pivot = pivot.drop(columns='Non renseigné', errors='ignore')

fig, ax = plt.subplots(figsize=(12, 7))
sns.heatmap(pivot, annot=True, fmt='.1f', cmap='YlOrRd',
            linewidths=0.5, linecolor='white',
            annot_kws={'size': 9, 'weight': 'bold'},
            cbar_kws={'label': 'Durée moy. jeûne solide (h)'},
            ax=ax)
ax.set_title('Durée moyenne de jeûne solide (h)\n'
             'selon spécialité et type d\'anesthésie')
ax.set_xlabel('Type d\'anesthésie')
ax.set_ylabel('Spécialité chirurgicale')
ax.tick_params(axis='x', rotation=30)
ax.tick_params(axis='y', rotation=0)
plt.tight_layout()
savefig(fig, '15_heatmap_specialite_anesthesie.png')

# ── 6.5 Comparaison observé vs recommandé ─────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 6))
categories   = ['Jeûne SOLIDE\n(seuil ≤ 6h)', 'Jeûne LIQUIDE\n(seuil ≤ 2h)']
rec_vals     = [SEUIL_SOLIDE, SEUIL_LIQUIDE]
obs_vals     = [sol.mean(), liq.mean()]
obs_et       = [sol.std(),  liq.std()]
x = np.arange(len(categories))
w2 = 0.32
br = ax.bar(x - w2/2, rec_vals, w2, label='Recommandation max (SFAR/ASA)',
            color='#2ecc71', edgecolor='white', alpha=0.85)
bo = ax.bar(x + w2/2, obs_vals, w2, label='Observé (moyenne ± ET)',
            color='#e74c3c', edgecolor='white', alpha=0.85,
            yerr=obs_et, capsize=6,
            error_kw=dict(ecolor='gray', linewidth=1.5))
for bar, v in zip(br, rec_vals):
    ax.text(bar.get_x() + bar.get_width()/2,
            v + 0.1, f'{v:.0f}h',
            ha='center', va='bottom', fontsize=12, fontweight='bold')
for bar, v in zip(bo, obs_vals):
    ax.text(bar.get_x() + bar.get_width()/2,
            v + 0.1, f'{v:.1f}h',
            ha='center', va='bottom', fontsize=12, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=11)
ax.set_ylabel('Durée (heures)')
ax.set_title('Jeûne observé vs recommandations SFAR / ASA 2017')
ax.legend(fontsize=10)
ax.set_ylim(0, max(obs_vals) + max(obs_et) + 2)
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout()
savefig(fig, '16_comparaison_recommandations.png')


# ─────────────────────────────────────────────────────────────────────────────
# 7. FIGURE DE SYNTHÈSE (dashboard récapitulatif)
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Figure synthèse ──")
fig = plt.figure(figsize=(18, 12))
gs  = gridspec.GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.35)

# Panneau 1 : Sexe
ax_s = fig.add_subplot(gs[0, 0])
valids_s = sexe_tab[~sexe_tab['Sexe'].isna() & (sexe_tab['Sexe'] != 'Non renseigné')]
ax_s.pie(valids_s['n'], labels=valids_s['Sexe'],
         autopct='%1.1f%%',
         colors=[PALETTE_SET2[0], PALETTE_SET2[1]],
         wedgeprops=dict(edgecolor='white', linewidth=2))
ax_s.set_title('Sexe')

# Panneau 2 : Âge
ax_a = fig.add_subplot(gs[0, 1])
ax_a.hist(age, bins=14, color=PALETTE_SET2[2], edgecolor='white')
ax_a.axvline(age.mean(), color='red', ls='--', lw=2,
             label=f'Moy.={age.mean():.0f}ans')
ax_a.set_title(f'Âge (moy.={age.mean():.0f} ans)')
ax_a.set_xlabel('Âge (ans)')
ax_a.legend(fontsize=8)
ax_a.spines[['top', 'right']].set_visible(False)

# Panneau 3 : ASA
ax_asa = fig.add_subplot(gs[0, 2])
ax_asa.pie(asa_tab['n'], labels=asa_tab['score_asa'],
           autopct='%1.1f%%',
           colors=[PALETTE_SET2[i] for i in range(len(asa_tab))],
           wedgeprops=dict(edgecolor='white', linewidth=2))
ax_asa.set_title('Score ASA')

# Panneau 4 : Durée jeûne solide
ax_js = fig.add_subplot(gs[1, 0])
bins_s2 = np.arange(int(sol.min()), int(sol.max()) + 2, 1)
ax_js.hist(sol, bins=bins_s2, color=PALETTE_SET2[0], edgecolor='white', alpha=0.85)
ax_js.axvline(SEUIL_SOLIDE, color='red', ls='--', lw=2,
              label=f'Recom. ≤{int(SEUIL_SOLIDE)}h')
ax_js.axvline(sol.mean(), color='navy', ls=':', lw=2,
              label=f'Moy.={sol.mean():.1f}h')
ax_js.set_title('Jeûne solide')
ax_js.set_xlabel('Heures')
ax_js.legend(fontsize=7.5)
ax_js.spines[['top', 'right']].set_visible(False)

# Panneau 5 : Durée jeûne liquide
ax_jl = fig.add_subplot(gs[1, 1])
bins_l2 = np.arange(int(liq.min()), int(liq.max()) + 2, 1)
ax_jl.hist(liq, bins=bins_l2, color=PALETTE_SET2[3], edgecolor='white', alpha=0.85)
ax_jl.axvline(SEUIL_LIQUIDE, color='red', ls='--', lw=2,
              label=f'Recom. ≤{int(SEUIL_LIQUIDE)}h')
ax_jl.axvline(liq.mean(), color='navy', ls=':', lw=2,
              label=f'Moy.={liq.mean():.1f}h')
ax_jl.set_title('Jeûne liquide')
ax_jl.set_xlabel('Heures')
ax_jl.legend(fontsize=7.5)
ax_jl.spines[['top', 'right']].set_visible(False)

# Panneau 6 : Retard
ax_r = fig.add_subplot(gs[1, 2])
ax_r.pie([n_retard, N - n_retard],
         labels=[f'Retard\n{pct_retard}%', f'Sans retard\n{100-pct_retard}%'],
         colors=[PALETTE_SET2[4], 'lightgrey'],
         wedgeprops=dict(edgecolor='white', linewidth=2, width=0.55),
         startangle=90)
ax_r.set_title('Retard chirurgical')

fig.suptitle('Tableau de bord — Jeûne préopératoire\nHôpital Général de Douala 2026',
             fontsize=16, fontweight='bold', y=1.01)
savefig(fig, '00_dashboard.png')


# ─────────────────────────────────────────────────────────────────────────────
# 8. TABLEAU RÉCAPITULATIF FINAL
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("  TABLEAU RÉCAPITULATIF FINAL")
print("="*70)
summary = [
    ('Effectif total (N)',                          str(N)),
    ('Sexe masculin (%)',                           f"{(df['sexe']=='Masculin').sum()} ({round((df['sexe']=='Masculin').sum()/N*100,1)}%)"),
    ('Âge moyen ± ET (ans)',                        f"{age.mean():.1f} ± {age.std():.1f}"),
    ('Âge médian [Q1–Q3] (ans)',                    f"{age.median():.0f} [{age.quantile(0.25):.0f}–{age.quantile(0.75):.0f}]"),
    ('IMC moyen ± ET (kg/m²)',                      f"{imc.mean():.1f} ± {imc.std():.1f} (n={len(imc)})"),
    ('Surpoids + Obésité (IMC>24,99)',               f"{n_surpoids} ({pct_surpoids}%)"),
    ('ASA I (%)',                                   f"{asa_tab.loc[asa_tab['score_asa']=='ASA I','n'].sum()} ({asa_tab.loc[asa_tab['score_asa']=='ASA I','%'].sum():.1f}%)"),
    ('ASA II (%)',                                  f"{asa_tab.loc[asa_tab['score_asa']=='ASA II','n'].sum() if 'ASA II' in asa_tab['score_asa'].values else 0}"),
    ('Durée jeûne SOLIDE — moyenne ± ET (h)',       f"{sol.mean():.2f} ± {sol.std():.2f}"),
    ('Durée jeûne SOLIDE — médiane [Q1–Q3] (h)',    f"{sol.median():.1f} [{sol.quantile(0.25):.1f}–{sol.quantile(0.75):.1f}]"),
    ('Durée jeûne LIQUIDE — moyenne ± ET (h)',      f"{liq.mean():.2f} ± {liq.std():.2f}"),
    (f'Solide > {SEUIL_SOLIDE}h (recom. max)',       f"{n_sol_sup_rec}/{len(sol)} ({pct_sol_rec}%)"),
    ('Solide > 9h',                                f"{n_sol_prolonge}/{len(sol)} ({pct_sol_pro}%)"),
    (f'Liquide > {SEUIL_LIQUIDE}h (recom. max)',     f"{n_liq_sup_rec}/{len(liq)} ({pct_liq_rec}%)"),
    ('Instructions reçues (OUI)',                  f"{(df['instructions_recues']=='OUI').sum()} ({round((df['instructions_recues']=='OUI').sum()/N*100,1)}%)"),
    ('Patients ayant compris',                     f"{(df['patient_compris']=='OUI').sum()} ({round((df['patient_compris']=='OUI').sum()/N*100,1)}%)"),
    ('Retard chirurgical (OUI)',                   f"{n_retard} ({pct_retard}%)"),
    ('Durée retard : moy. ± ET (h)',               f"{ret_valid.mean():.1f} ± {ret_valid.std():.1f}" if len(ret_valid)>0 else 'N/A'),
]
print(f"\n  {'Indicateur':<50}  {'Valeur':>30}")
print("  " + "-"*82)
for k, v in summary:
    print(f"  {k:<50}  {v:>30}")

print(f"\n  ✓ ANALYSE PYTHON TERMINÉE — {len(os.listdir(OUTPUT_DIR))} figures dans : {OUTPUT_DIR}\n")
