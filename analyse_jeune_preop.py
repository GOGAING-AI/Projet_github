"""
=============================================================================
ANALYSE STATISTIQUE DU JEÛNE PRÉOPÉRATOIRE
Hôpital Général de Douala — Chirurgie Élective 2026
=============================================================================
Auteur   : Script généré pour l'étude sur le jeûne préopératoire
Standard : Conforme aux recommandations STROBE / bonnes pratiques épidémiologiques
Python   : pandas, numpy, matplotlib, seaborn, scipy
=============================================================================
"""

# ─────────────────────────────────────────────────────────────────────────────
# 0. IMPORTS ET CONFIGURATION GÉNÉRALE
# ─────────────────────────────────────────────────────────────────────────────
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')                        # Mode non-interactif (sauvegarde fichiers)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats
import warnings
import os

warnings.filterwarnings('ignore')

# ── Chemins ──────────────────────────────────────────────────────────────────
INPUT_FILE  = "C:/Users/Foguen Lucas/Downloads/resultat_Courbes_Dora/collecte_de_données_1.xlsx"
OUTPUT_DIR  = "C:/Users/Foguen Lucas/Downloads/resultat_Courbes_Dora/images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Style graphique global ────────────────────────────────────────────────────
sns.set_theme(style='whitegrid', font='DejaVu Sans')
PALETTE     = sns.color_palette('Set2', 12)   # Palette accessible et lisible
plt.rcParams.update({
    'figure.dpi'       : 150,
    'axes.titlesize'   : 13,
    'axes.labelsize'   : 11,
    'xtick.labelsize'  : 9,
    'ytick.labelsize'  : 9,
    'legend.fontsize'  : 9,
    'figure.titlesize' : 15,
})

# ─────────────────────────────────────────────────────────────────────────────
# 1. CHARGEMENT ET NETTOYAGE DES DONNÉES
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print(" ÉTAPE 1 — CHARGEMENT ET NETTOYAGE DES DONNÉES")
print("="*70)

df_raw = pd.read_excel(INPUT_FILE, header=0)

# ── Renommage harmonisé des colonnes ─────────────────────────────────────────
# Les colonnes du fichier original contiennent des doublons (résidu de mise en
# forme Excel). On sélectionne les colonnes utiles par position.
col_map = {
    df_raw.columns[0]  : 'date_inclusion',
    df_raw.columns[2]  : 'nom',
    df_raw.columns[3]  : 'sexe',
    df_raw.columns[4]  : 'age',
    df_raw.columns[5]  : 'antecedent_op',
    df_raw.columns[6]  : 'nb_operations',
    df_raw.columns[7]  : 'score_asa',
    df_raw.columns[8]  : 'imc',
    df_raw.columns[9]  : 'type_chirurgie',
    df_raw.columns[10] : 'specialite',
    df_raw.columns[11] : 'type_anesthesie',
    df_raw.columns[12] : 'instructions_recues',
    df_raw.columns[14] : 'source_instructions',
    df_raw.columns[16] : 'consigne_liquide',
    df_raw.columns[18] : 'consigne_solide',
    df_raw.columns[20] : 'patient_compris',
    df_raw.columns[32] : 'duree_jeune_solide_h',
    df_raw.columns[34] : 'duree_jeune_liquide_h',
    df_raw.columns[36] : 'retard_chirurgie',
    df_raw.columns[38] : 'duree_retard_h',
}
df = df_raw.rename(columns=col_map)[list(col_map.values())].copy()

# ── Nettoyage des valeurs textuelles ─────────────────────────────────────────
def clean_str(s):
    """Normalise une chaîne : minuscule, sans espaces superflus."""
    if pd.isna(s):
        return np.nan
    return str(s).strip().lower()

for col in ['sexe', 'antecedent_op', 'score_asa', 'type_anesthesie',
            'instructions_recues', 'source_instructions',
            'consigne_liquide', 'consigne_solide', 'patient_compris',
            'retard_chirurgie', 'specialite']:
    df[col] = df[col].apply(clean_str)

# ── Nettoyage de la colonne âge ───────────────────────────────────────────────
def parse_age(v):
    """Extrait l'entier numérique d'une valeur d'âge potentiellement mixte."""
    if pd.isna(v):
        return np.nan
    s = str(v).strip()
    # Cherche le premier groupe numérique
    import re
    m = re.search(r'\d+', s)
    return int(m.group()) if m else np.nan

df['age'] = df['age'].apply(parse_age)

# ── Nettoyage de l'IMC ────────────────────────────────────────────────────────
df['imc'] = pd.to_numeric(df['imc'], errors='coerce')

# ── Nettoyage des durées de jeûne ─────────────────────────────────────────────
def parse_heures(v):
    """
    Convertit une durée en heures depuis différents formats :
    '08H', '08h', '8', '8H', etc.
    """
    if pd.isna(v):
        return np.nan
    import re
    s = str(v).strip().upper().replace('H', '').replace(' ', '')
    m = re.search(r'[\d]+', s)
    return float(m.group()) if m else np.nan

df['duree_jeune_solide_h']  = df['duree_jeune_solide_h'].apply(parse_heures)
print("\nDEBUG duree_jeune_solide_h :")
print(df['duree_jeune_solide_h'].head(20))
print(df['duree_jeune_solide_h'].describe())

df['duree_jeune_liquide_h'] = df['duree_jeune_liquide_h'].apply(parse_heures)
print("\nDEBUG duree_jeune_liquide_h :")
print(df['duree_jeune_liquide_h'].head(20))
print(df['duree_jeune_liquide_h'].describe())

df['duree_retard_h']        = df['duree_retard_h'].apply(parse_heures)

# ── Normalisation du sexe ─────────────────────────────────────────────────────
def normalize_sexe(v):
    if pd.isna(v):
        return np.nan
    v = str(v).strip().upper()
    if v.startswith('F'):
        return 'Féminin'
    elif v.startswith('M'):
        return 'Masculin'
    return np.nan

df['sexe'] = df['sexe'].apply(normalize_sexe)

# ── Normalisation du score ASA ────────────────────────────────────────────────
def normalize_asa(v):
    if pd.isna(v):
        return np.nan
    import re
    v = str(v).upper()
    m = re.search(r'(I{1,3}|IV)', v)
    if m:
        return 'ASA ' + m.group()
    return np.nan

df['score_asa'] = df['score_asa'].apply(normalize_asa)

# ── Normalisation du type d'anesthésie ───────────────────────────────────────
def normalize_anesthesie(v):
    if pd.isna(v):
        return 'Non renseigné'
    v = str(v).upper().strip()
    if 'AG' in v and 'IOT' in v:
        return 'AG + IOT'
    elif 'AG' in v:
        return 'AG seule'
    elif 'ALR' in v or 'RA' in v:
        return 'ALR/RA'
    elif 'AL' in v:
        return 'AL'
    elif 'APD' in v:
        return 'APD'
    return 'Autre'

df['type_anesthesie_clean'] = df['type_anesthesie'].apply(normalize_anesthesie)

# ── Normalisation de la spécialité chirurgicale ───────────────────────────────
def normalize_specialite(v):
    if pd.isna(v):
        return 'Non renseigné'
    v = str(v).lower().strip()
    if 'orl' in v or 'oph' in v or 'ccf' in v:
        return 'ORL / Ophtalmologie'
    elif 'gynéco' in v or 'gyneco' in v or 'gynécolog' in v:
        return 'Gynécologie'
    elif 'urol' in v:
        return 'Urologie'
    elif 'neurochir' in v or 'neurochi' in v:
        return 'Neurochirurgie'
    elif 'orthop' in v or 'othop' in v:
        return 'Orthopédie'
    elif 'vasc' in v or 'cv' in v:
        return 'Chirurgie vasculaire'
    elif 'viscér' in v or 'visceral' in v or 'visc' in v:
        return 'Chirurgie viscérale'
    return 'Autre'

df['specialite_clean'] = df['specialite'].apply(normalize_specialite)


# ── Gestion globale des valeurs manquantes catégorielles ─────────────
cols_cat = [
    'sexe',
    'score_asa',
    'specialite_clean',
    'type_anesthesie_clean'
]

for col in cols_cat:
    df[col] = df[col].fillna('Non renseigné').astype(str)



# ── Suppression des lignes sans données essentielles ─────────────────────────
df = df.dropna(subset=['nom', 'age']).reset_index(drop=True)

print(f"  → {len(df)} patients retenus après nettoyage")
print(f"  → Variables : {list(df.columns)}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. OBJECTIF 1 — CARACTÉRISTIQUES SOCIODÉMOGRAPHIQUES ET CLINIQUES
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print(" OBJECTIF 1 — CARACTÉRISTIQUES SOCIODÉMOGRAPHIQUES ET CLINIQUES")
print("="*70)

N = len(df)   # Effectif total de l'étude

# ── 2.1 Répartition par sexe ──────────────────────────────────────────────────
print("\n── 2.1 Sexe ──")

"""
sexe_tab = df['sexe'].value_counts(dropna=False).rename_axis('Sexe').reset_index(name='Effectif')
sexe_tab['%'] = (sexe_tab['Effectif'] / N * 100).round(1)
print(sexe_tab.to_string(index=False))

fig, ax = plt.subplots(figsize=(6, 5))
bars = ax.bar(sexe_tab['Sexe'], sexe_tab['Effectif'],
              color=[PALETTE[0], PALETTE[1]], edgecolor='white', linewidth=1.5, width=0.5)
              """

sexe_tab = (
    df['sexe']
    .fillna('Non renseigné')
    .value_counts(dropna=False)
    .rename_axis('Sexe')
    .reset_index(name='Effectif')
)

sexe_tab['%'] = (sexe_tab['Effectif'] / N * 100).round(1)

print(sexe_tab.to_string(index=False))

# Couleurs dynamiques
colors = [PALETTE[i] for i in range(len(sexe_tab))]

fig, ax = plt.subplots(figsize=(6, 5))

bars = ax.bar(
    sexe_tab['Sexe'].astype(str),
    sexe_tab['Effectif'],
    color=colors,
    edgecolor='white',
    linewidth=1.5,
    width=0.5
)


for bar, pct in zip(bars, sexe_tab['%']):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f'{bar.get_height()} ({pct}%)', ha='center', va='bottom', fontsize=10, fontweight='bold')
ax.set_title('Répartition des patients par sexe', fontweight='bold', pad=12)
ax.set_xlabel('Sexe')
ax.set_ylabel('Effectif')
ax.set_ylim(0, sexe_tab['Effectif'].max() * 1.2)
ax.spines[['top','right']].set_visible(False)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/01_repartition_sexe.png', bbox_inches='tight')
plt.close()
print("  → Figure 01 sauvegardée")

# ── 2.2 Âge ───────────────────────────────────────────────────────────────────
print("\n── 2.2 Âge ──")
age_valid = df['age'].dropna()
age_stats = {
    'n'        : int(age_valid.count()),
    'moyenne'  : round(float(age_valid.mean()), 1),
    'médiane'  : round(float(age_valid.median()), 1),
    'écart-type': round(float(age_valid.std()), 1),
    'min'      : int(age_valid.min()),
    'max'      : int(age_valid.max()),
    'IQR [Q1-Q3]': f'{int(age_valid.quantile(0.25))} – {int(age_valid.quantile(0.75))}',
}
for k, v in age_stats.items():
    print(f"  {k:20s}: {v}")

# Histogramme + boxplot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
# Histogramme
ax1.hist(age_valid, bins=15, color=PALETTE[2], edgecolor='white', linewidth=1)
ax1.axvline(age_valid.mean(), color='red', linestyle='--', linewidth=1.8,
            label=f'Moyenne = {age_stats["moyenne"]} ans')
ax1.axvline(age_valid.median(), color='navy', linestyle=':', linewidth=1.8,
            label=f'Médiane = {age_stats["médiane"]} ans')
ax1.set_title('Distribution des âges', fontweight='bold')
ax1.set_xlabel('Âge (ans)')
ax1.set_ylabel('Effectif')
ax1.legend()
ax1.spines[['top','right']].set_visible(False)
# Boxplot
bp = ax2.boxplot(age_valid, vert=True, patch_artist=True,
                 boxprops=dict(facecolor=PALETTE[2], alpha=0.6),
                 medianprops=dict(color='navy', linewidth=2))
ax2.set_title('Boîte à moustaches — Âge', fontweight='bold')
ax2.set_ylabel('Âge (ans)')
ax2.set_xticks([])
ax2.spines[['top','right']].set_visible(False)
fig.suptitle(f'Analyse de l\'âge (n = {age_stats["n"]})', fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/02_distribution_age.png', bbox_inches='tight')
plt.close()
print("  → Figure 02 sauvegardée")

# ── 2.3 IMC ───────────────────────────────────────────────────────────────────
print("\n── 2.3 IMC ──")
imc_valid = df['imc'].dropna()

# Catégorisation selon OMS
bins_imc   = [0, 18.5, 24.99, 29.99, 100]
labels_imc = ['Insuffisance pondérale (<18,5)',
               'Poids normal (18,5–24,99)',
               'Surpoids (25–29,99)',
               'Obésité (≥30)']
df['imc_cat'] = pd.cut(df['imc'], bins=bins_imc, labels=labels_imc, right=True)
imc_cat_tab = df['imc_cat'].value_counts().reindex(labels_imc).reset_index()
imc_cat_tab.columns = ['Catégorie IMC', 'Effectif']
imc_cat_tab['%'] = (imc_cat_tab['Effectif'] / imc_valid.count() * 100).round(1)
print(imc_cat_tab.to_string(index=False))

n_surpoids = int(imc_cat_tab.loc[imc_cat_tab['Catégorie IMC'].isin(
    ['Surpoids (25–29,99)', 'Obésité (≥30)']), 'Effectif'].sum())
pct_surpoids = round(n_surpoids / imc_valid.count() * 100, 1)
print(f"\n  Patients en surpoids ou obèses (IMC > 24,99) : {n_surpoids} / {len(imc_valid)} ({pct_surpoids}%)")

fig, ax = plt.subplots(figsize=(7, 5))
colors_imc = [PALETTE[i] for i in range(len(labels_imc))]
bars = ax.barh(imc_cat_tab['Catégorie IMC'], imc_cat_tab['Effectif'],
               color=colors_imc, edgecolor='white', linewidth=1)
for bar, row in zip(bars, imc_cat_tab.itertuples()):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
            f'{row.Effectif} ({row._3}%)', va='center', fontsize=9, fontweight='bold')
ax.set_title('Répartition par catégorie IMC (OMS)', fontweight='bold')
ax.set_xlabel('Effectif')
ax.set_xlim(0, imc_cat_tab['Effectif'].max() * 1.3)
ax.spines[['top','right']].set_visible(False)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/03_repartition_imc.png', bbox_inches='tight')
plt.close()
print("  → Figure 03 sauvegardée")

# ── 2.4 Score ASA ─────────────────────────────────────────────────────────────
print("\n── 2.4 Score ASA ──")
asa_valid = df.dropna(subset=['score_asa'])
asa_tab = asa_valid.groupby('score_asa').agg(
    Effectif=('score_asa', 'count'),
    Age_moyen=('age', lambda x: round(x.mean(), 1)),
    Age_SD=('age', lambda x: round(x.std(), 1))
).reset_index()
asa_tab['%'] = (asa_tab['Effectif'] / len(asa_valid) * 100).round(1)
print(asa_tab.to_string(index=False))

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
# Diagramme en secteurs
wedges, texts, autotexts = axes[0].pie(
    asa_tab['Effectif'],
    labels=asa_tab['score_asa'],
    autopct='%1.1f%%',
    colors=[PALETTE[i] for i in range(len(asa_tab))],
    startangle=90,
    pctdistance=0.75,
    wedgeprops=dict(edgecolor='white', linewidth=2)
)
for at in autotexts:
    at.set_fontsize(10)
    at.set_fontweight('bold')
axes[0].set_title('Répartition par score ASA', fontweight='bold')
# Âge moyen par score ASA
#bars = axes[1].bar(asa_tab['score_asa'], asa_tab['Age_moyen'],
bars = axes[1].bar(
    asa_tab['score_asa'].astype(str),
    asa_tab['Age_moyen'],
                   color=[PALETTE[i] for i in range(len(asa_tab))],
                   edgecolor='white', linewidth=1.5, width=0.5,
                   yerr=asa_tab['Age_SD'], capsize=5,
                   error_kw=dict(ecolor='gray', linewidth=1))
for bar, row in zip(bars, asa_tab.itertuples()):
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + row.Age_SD + 0.5,
                 f'{row.Age_moyen} ans\n(n={row.Effectif})',
                 ha='center', va='bottom', fontsize=9, fontweight='bold')
axes[1].set_title('Âge moyen par score ASA (± ET)', fontweight='bold')
axes[1].set_xlabel('Score ASA')
axes[1].set_ylabel('Âge moyen (ans)')
axes[1].set_ylim(0, asa_tab['Age_moyen'].max() + asa_tab['Age_SD'].max() + 15)
axes[1].spines[['top','right']].set_visible(False)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/04_score_asa.png', bbox_inches='tight')
plt.close()
print("  → Figure 04 sauvegardée")

# ── 2.5 Type de chirurgie par spécialité ──────────────────────────────────────
print("\n── 2.5 Spécialité chirurgicale ──")
spec_tab = df['specialite_clean'].value_counts().reset_index()
spec_tab.columns = ['Spécialité', 'Effectif']
spec_tab['%'] = (spec_tab['Effectif'] / N * 100).round(1)
print(spec_tab.to_string(index=False))

fig, ax = plt.subplots(figsize=(9, 6))
palette_spec = sns.color_palette('tab10', len(spec_tab))

#bars = ax.barh(spec_tab['Spécialité'], spec_tab['Effectif'],
bars = ax.barh(
    spec_tab['Spécialité'].astype(str),
    spec_tab['Effectif'],
               color=palette_spec, edgecolor='white', linewidth=1)
for bar, row in zip(bars, spec_tab.itertuples()):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
            f'{row.Effectif} ({row._3}%)', va='center', fontsize=9, fontweight='bold')
ax.set_title('Répartition par spécialité chirurgicale', fontweight='bold', pad=12)
ax.set_xlabel('Effectif')
ax.set_xlim(0, spec_tab['Effectif'].max() * 1.35)
ax.spines[['top','right']].set_visible(False)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/05_specialite_chirurgicale.png', bbox_inches='tight')
plt.close()
print("  → Figure 05 sauvegardée")

# ── 2.6 Type d'anesthésie ─────────────────────────────────────────────────────
print("\n── 2.6 Type d'anesthésie ──")
anes_tab = df['type_anesthesie_clean'].value_counts().reset_index()
anes_tab.columns = ['Type anesthésie', 'Effectif']
anes_tab['%'] = (anes_tab['Effectif'] / N * 100).round(1)
print(anes_tab.to_string(index=False))

fig, ax = plt.subplots(figsize=(7, 5))

#bars = ax.bar(anes_tab['Type anesthésie'], anes_tab['Effectif'],

bars = ax.bar(
    anes_tab['Type anesthésie'].astype(str),
    anes_tab['Effectif'],
              color=sns.color_palette('Paired', len(anes_tab)),
              edgecolor='white', linewidth=1.5, width=0.6)
for bar, row in zip(bars, anes_tab.itertuples()):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f'{row.Effectif}\n({row._3}%)', ha='center', va='bottom',
            fontsize=9, fontweight='bold')
ax.set_title('Répartition par type d\'anesthésie', fontweight='bold')
ax.set_xlabel('Type d\'anesthésie')
ax.set_ylabel('Effectif')
ax.set_ylim(0, anes_tab['Effectif'].max() * 1.25)
ax.tick_params(axis='x', rotation=20)
ax.spines[['top','right']].set_visible(False)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/06_type_anesthesie.png', bbox_inches='tight')
plt.close()
print("  → Figure 06 sauvegardée")

# ─────────────────────────────────────────────────────────────────────────────
# 3. OBJECTIF 2 — DURÉE MOYENNE DU JEÛNE PRÉOPÉRATOIRE
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print(" OBJECTIF 2 — DURÉE MOYENNE DU JEÛNE PRÉOPÉRATOIRE")
print("="*70)

# ── Recommandations internationales (SFAR / ASA 2017) ────────────────────────
SEUIL_SOLIDE  = 6.0   # heures — recommandation maximale pour solides
SEUIL_LIQUIDE = 2.0   # heures — recommandation maximale pour liquides clairs

solide  = df['duree_jeune_solide_h'].dropna()
liquide = df['duree_jeune_liquide_h'].dropna()

# ── Statistiques descriptives jeûne solide ───────────────────────────────────
print("\n── Jeûne solide ──")
sol_stats = {
    'n'           : int(solide.count()),
    'Moyenne (h)' : round(float(solide.mean()), 2),
    'Médiane (h)' : round(float(solide.median()), 2),
    'Écart-type'  : round(float(solide.std()), 2),
    'Min (h)'     : float(solide.min()),
    'Max (h)'     : float(solide.max()),
}
for k, v in sol_stats.items():
    print(f"  {k:20s}: {v}")

n_sol_9h = int((solide > 9).sum())
pct_sol_9h = round(n_sol_9h / len(solide) * 100, 1)
n_sol_sup_rec = int((solide > SEUIL_SOLIDE).sum())
pct_sol_sup_rec = round(n_sol_sup_rec / len(solide) * 100, 1)
print(f"\n  Jeûne solide > 9h     : {n_sol_9h}/{len(solide)} ({pct_sol_9h}%)")
print(f"  Jeûne solide > {SEUIL_SOLIDE}h (recom.): {n_sol_sup_rec}/{len(solide)} ({pct_sol_sup_rec}%)")

# ── Statistiques descriptives jeûne liquide ──────────────────────────────────
print("\n── Jeûne liquide ──")
liq_stats = {
    'n'           : int(liquide.count()),
    'Moyenne (h)' : round(float(liquide.mean()), 2),
    'Médiane (h)' : round(float(liquide.median()), 2),
    'Écart-type'  : round(float(liquide.std()), 2),
    'Min (h)'     : float(liquide.min()),
    'Max (h)'     : float(liquide.max()),
}
for k, v in liq_stats.items():
    print(f"  {k:20s}: {v}")

n_liq_sup2  = int((liquide > SEUIL_LIQUIDE).sum())
pct_liq_sup2 = round(n_liq_sup2 / len(liquide) * 100, 1)
n_liq_sup6  = int((liquide > 6).sum())
pct_liq_sup6 = round(n_liq_sup6 / len(liquide) * 100, 1)
print(f"\n  Jeûne liquide > {SEUIL_LIQUIDE}h (recom.) : {n_liq_sup2}/{len(liquide)} ({pct_liq_sup2}%)")
print(f"  Jeûne liquide > 6h              : {n_liq_sup6}/{len(liquide)} ({pct_liq_sup6}%)")

# ── Visualisation comparée ────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for ax, data, seuil, titre, couleur, rec_label in [
    (axes[0], solide,  SEUIL_SOLIDE,  'Durée jeûne SOLIDE',  PALETTE[0],
     f'Recommandation : ≤ {int(SEUIL_SOLIDE)}h'),
    (axes[1], liquide, SEUIL_LIQUIDE, 'Durée jeûne LIQUIDE', PALETTE[3],
     f'Recommandation : ≤ {int(SEUIL_LIQUIDE)}h'),
]:
    ax.hist(data, bins=range(int(data.min()), int(data.max())+2),
            color=couleur, edgecolor='white', linewidth=1, alpha=0.85)
    ax.axvline(seuil, color='red', linestyle='--', linewidth=2,
               label=rec_label)
    ax.axvline(data.mean(), color='navy', linestyle=':', linewidth=2,
               label=f'Moyenne obs. = {data.mean():.1f}h')
    ax.set_title(titre, fontweight='bold')
    ax.set_xlabel('Durée (heures)')
    ax.set_ylabel('Nombre de patients')
    ax.legend(fontsize=8)
    ax.spines[['top','right']].set_visible(False)

fig.suptitle('Distribution des durées de jeûne préopératoire\nvs recommandations SFAR/ASA 2017',
             fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/07_distribution_jeune.png', bbox_inches='tight')
plt.close()
print("  → Figure 07 sauvegardée")

# ── Durée de jeûne par spécialité ─────────────────────────────────────────────
print("\n── Jeûne par spécialité chirurgicale ──")
jeune_spec = df.groupby('specialite_clean').agg(
    n=('duree_jeune_solide_h', 'count'),
    moy_solide=('duree_jeune_solide_h', lambda x: round(x.mean(), 1)),
    moy_liquide=('duree_jeune_liquide_h', lambda x: round(x.mean(), 1))
).reset_index()
jeune_spec['%_sol>6h'] = df.groupby('specialite_clean')['duree_jeune_solide_h'].apply(
    lambda x: round((x > SEUIL_SOLIDE).mean() * 100, 1)
).values
print(jeune_spec.to_string(index=False))

fig, ax = plt.subplots(figsize=(11, 6))
x = np.arange(len(jeune_spec))
width = 0.38
bars1 = ax.bar(x - width/2, jeune_spec['moy_solide'],  width,
               label='Jeûne solide moyen (h)',  color=PALETTE[0], edgecolor='white')
bars2 = ax.bar(x + width/2, jeune_spec['moy_liquide'], width,
               label='Jeûne liquide moyen (h)', color=PALETTE[3], edgecolor='white')
# Annotations
for bar in bars1:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
            f'{bar.get_height():.1f}h', ha='center', va='bottom', fontsize=7.5, fontweight='bold')
for bar in bars2:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
            f'{bar.get_height():.1f}h', ha='center', va='bottom', fontsize=7.5, fontweight='bold')
ax.axhline(SEUIL_SOLIDE,  color='red',    linestyle='--', linewidth=1.5,
           label=f'Seuil solide ({int(SEUIL_SOLIDE)}h)')
ax.axhline(SEUIL_LIQUIDE, color='orange', linestyle='--', linewidth=1.5,
           label=f'Seuil liquide ({int(SEUIL_LIQUIDE)}h)')
ax.set_xticks(x)

#ax.set_xticklabels(jeune_spec['specialite_clean'], rotation=30, ha='right', fontsize=8.5)
ax.set_xticklabels(
    jeune_spec['specialite_clean'].astype(str),
    rotation=30,
    ha='right',
    fontsize=8.5
)
ax.set_ylabel('Durée moyenne (heures)')
ax.set_title('Durée moyenne de jeûne par spécialité chirurgicale\n(avec seuils recommandés)',
             fontweight='bold')
ax.legend(fontsize=8, loc='upper right')
ax.spines[['top','right']].set_visible(False)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/08_jeune_par_specialite.png', bbox_inches='tight')
plt.close()
print("  → Figure 08 sauvegardée")

# ─────────────────────────────────────────────────────────────────────────────
# 4. OBJECTIF 3 — CONNAISSANCE DES PATIENTS SUR LE JEÛNE
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print(" OBJECTIF 3 — CONNAISSANCE ET INSTRUCTIONS")
print("="*70)

# ── Instructions de jeûne reçues ──────────────────────────────────────────────
def norm_oui_non(v):
    if pd.isna(v):
        return 'Non renseigné'
    v = str(v).strip().lower()
    if v in ['oui', 'o', 'yes']:
        return 'OUI'
    elif v in ['non', 'n', 'no']:
        return 'NON'
    return 'Non renseigné'

for col in ['instructions_recues', 'consigne_liquide', 'consigne_solide', 'patient_compris']:
    df[col] = df[col].apply(norm_oui_non)

# ── Tableau synthétique connaissance ─────────────────────────────────────────
items = {
    'Instructions reçues'          : 'instructions_recues',
    'Consigne : ne pas prendre de liquide' : 'consigne_liquide',
    'Consigne : ne pas prendre de solide'  : 'consigne_solide',
    'Patient a compris'            : 'patient_compris',
}
rows = []
for label, col in items.items():
    oui = (df[col] == 'OUI').sum()
    non = (df[col] == 'NON').sum()
    nr  = (df[col] == 'Non renseigné').sum()
    rows.append({'Item': label, 'OUI': oui, 'NON': non,
                 'Non renseigné': nr,
                 '% OUI': round(oui / N * 100, 1)})
connaissance_df = pd.DataFrame(rows)
print(connaissance_df.to_string(index=False))

fig, ax = plt.subplots(figsize=(10, 5))
x = np.arange(len(connaissance_df))
w = 0.28
ax.bar(x - w, connaissance_df['OUI'],            width=w, label='OUI',
       color=PALETTE[2], edgecolor='white')
ax.bar(x,     connaissance_df['NON'],            width=w, label='NON',
       color=PALETTE[5], edgecolor='white')
ax.bar(x + w, connaissance_df['Non renseigné'], width=w, label='Non renseigné',
       color='lightgrey', edgecolor='white')
# Annotations pourcentages
for xi, row in zip(x, connaissance_df.itertuples()):
    ax.text(xi - w, row.OUI + 0.3, f'{row.OUI}\n({row._5}%)',
            ha='center', va='bottom', fontsize=8, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(connaissance_df['Item'], rotation=20, ha='right', fontsize=8.5)
ax.set_title('Connaissance et conformité aux instructions de jeûne', fontweight='bold')
ax.set_ylabel('Effectif')
ax.legend(fontsize=9)
ax.spines[['top','right']].set_visible(False)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/09_connaissance_instructions.png', bbox_inches='tight')
plt.close()
print("  → Figure 09 sauvegardée")

# ── Source des instructions ───────────────────────────────────────────────────
def norm_source(v):
    if pd.isna(v):
        return 'Non renseigné'
    v = str(v).lower()
    if 'sage' in v:
        return 'Sage-femme'
    elif 'infirm' in v:
        return 'Infirmier(ère)'
    elif 'médecin' in v or 'anesth' in v:
        return 'Médecin/Anesthésiste'
    return 'Autre'

df['source_clean'] = df['source_instructions'].apply(norm_source)
source_tab = df['source_clean'].value_counts().reset_index()
source_tab.columns = ['Source', 'Effectif']
source_tab['%'] = (source_tab['Effectif'] / N * 100).round(1)
print("\nSource des instructions de jeûne :")
print(source_tab.to_string(index=False))

fig, ax = plt.subplots(figsize=(6, 5))
wedges, texts, autotexts = ax.pie(
    source_tab['Effectif'],
    labels=source_tab['Source'],
    autopct=lambda p: f'{p:.1f}%\n(n={int(p*N/100)})',
    colors=[PALETTE[i] for i in range(len(source_tab))],
    startangle=90,
    wedgeprops=dict(edgecolor='white', linewidth=2),
    pctdistance=0.75
)
for at in autotexts:
    at.set_fontsize(9)
ax.set_title('Source des instructions de jeûne préopératoire', fontweight='bold')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/10_source_instructions.png', bbox_inches='tight')
plt.close()
print("  → Figure 10 sauvegardée")

# ─────────────────────────────────────────────────────────────────────────────
# 5. OBJECTIF 4 — FACTEURS ASSOCIÉS AU JEÛNE PROLONGÉ
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print(" OBJECTIF 4 — FACTEURS ASSOCIÉS AU JEÛNE PROLONGÉ")
print("="*70)

# ── 5.1 Retard chirurgical ────────────────────────────────────────────────────
df['retard_bin'] = df['retard_chirurgie'].apply(norm_oui_non)
n_retard     = (df['retard_bin'] == 'OUI').sum()
pct_retard   = round(n_retard / N * 100, 1)
retard_valid = df[df['retard_bin'] == 'OUI']['duree_retard_h'].dropna()
print(f"\n  Patients avec retard chirurgical : {n_retard}/{N} ({pct_retard}%)")
if len(retard_valid) > 0:
    print(f"  Durée retard — min : {retard_valid.min():.0f}h | max : {retard_valid.max():.0f}h | "
          f"moyenne : {retard_valid.mean():.1f}h")

# ── Retard par spécialité ──────────────────────────────────────────────────────
retard_spec = df[df['retard_bin'] == 'OUI'].groupby('specialite_clean').agg(
    n_retard=('retard_bin', 'count'),
    retard_moy=('duree_retard_h', lambda x: round(x.mean(), 1)),
    retard_max=('duree_retard_h', lambda x: round(x.max(), 1))
).reset_index()
# Pourcentage parmi l'ensemble des patients de chaque spécialité
total_spec = df.groupby('specialite_clean').size().reset_index(name='total')
retard_spec = retard_spec.merge(total_spec, on='specialite_clean')
retard_spec['%_retard'] = (retard_spec['n_retard'] / retard_spec['total'] * 100).round(1)
print("\nRetards par spécialité :")
print(retard_spec.to_string(index=False))

fig, ax = plt.subplots(figsize=(11, 6))
palette_ret = sns.color_palette('husl', len(retard_spec))

#bars = ax.bar(retard_spec['specialite_clean'], retard_spec['n_retard'],
bars = ax.bar(
    retard_spec['specialite_clean'].astype(str),
    retard_spec['n_retard'],
              color=palette_ret, edgecolor='white', linewidth=1, width=0.6)
for bar, row in zip(bars, retard_spec.itertuples()):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
            f'{row.n_retard}\n({row._6}%)', ha='center', va='bottom',
            fontsize=9, fontweight='bold')
ax.set_title('Nombre de retards chirurgicaux par spécialité\n(% = part des patients de la spécialité)',
             fontweight='bold')
ax.set_xlabel('Spécialité chirurgicale')
ax.set_ylabel('Nombre de retards')
ax.tick_params(axis='x', rotation=30)
ax.spines[['top','right']].set_visible(False)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/11_retard_par_specialite.png', bbox_inches='tight')
plt.close()
print("  → Figure 11 sauvegardée")

# ── 5.2 Durée de retard par spécialité ───────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 6))
palette_dur = sns.color_palette('coolwarm', len(retard_spec))

#bars = ax.bar(retard_spec['specialite_clean'], retard_spec['retard_moy'],
bars = ax.bar(
    retard_spec['specialite_clean'].astype(str),
    retard_spec['retard_moy'],
              color=palette_dur, edgecolor='white', linewidth=1, width=0.6,
              yerr=df[df['retard_bin']=='OUI'].groupby('specialite_clean')['duree_retard_h'].std().reindex(
                  retard_spec['specialite_clean']).fillna(0).values,
              capsize=4, error_kw=dict(ecolor='gray', linewidth=1))
for bar, row in zip(bars, retard_spec.itertuples()):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
            f'{row.retard_moy}h\n(max:{row.retard_max}h)',
            ha='center', va='bottom', fontsize=8, fontweight='bold')
ax.set_title('Durée moyenne de retard chirurgical par spécialité (± ET)',
             fontweight='bold')
ax.set_xlabel('Spécialité chirurgicale')
ax.set_ylabel('Durée du retard (heures)')
ax.tick_params(axis='x', rotation=30)
ax.spines[['top','right']].set_visible(False)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/12_duree_retard_specialite.png', bbox_inches='tight')
plt.close()
print("  → Figure 12 sauvegardée")

# ── 5.3 Analyse du jeûne prolongé : facteurs associés (test du Chi-2) ────────
print("\n── 5.3 Facteurs associés au jeûne solide prolongé (> 9h) ──")
# Création de la variable dépendante binaire
df['jeune_prolonge'] = (df['duree_jeune_solide_h'] > 9).map({True: 'Prolongé (>9h)', False: 'Normal (≤9h)'})

# Chi2 : sexe × jeûne prolongé
for var_label, var_col in [('Sexe', 'sexe'), ('Score ASA', 'score_asa'), ('Retard', 'retard_bin')]:
    ct = pd.crosstab(df[var_col], df['jeune_prolonge'])
    if ct.shape[0] >= 2 and ct.shape[1] >= 2:
        chi2, p, dof, _ = stats.chi2_contingency(ct)
        print(f"\n  {var_label} × jeûne prolongé — χ²({dof}) = {chi2:.2f}, p = {p:.4f}")
        print(ct.to_string())

# ── 5.4 Heatmap : durée de jeûne solide vs spécialité & anesthésie ────────────
pivot_heat = df.groupby(['specialite_clean', 'type_anesthesie_clean'])['duree_jeune_solide_h'].mean().unstack()
fig, ax = plt.subplots(figsize=(11, 6))
sns.heatmap(pivot_heat, annot=True, fmt='.1f', cmap='YlOrRd',
            linewidths=0.5, linecolor='white',
            cbar_kws={'label': 'Durée jeûne solide moyen (h)'},
            ax=ax)
ax.set_title('Durée moyenne de jeûne solide (h)\npar spécialité et type d\'anesthésie',
             fontweight='bold')
ax.set_xlabel('Type d\'anesthésie')
ax.set_ylabel('Spécialité chirurgicale')
plt.xticks(rotation=30, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/13_heatmap_jeune.png', bbox_inches='tight')
plt.close()
print("  → Figure 13 sauvegardée")

# ── 5.5 Figure récapitulative : comparaison jeûne observé vs recommandé ────────
fig, ax = plt.subplots(figsize=(9, 5))
categories = ['Jeûne solide\n(recommandation : ≤ 6h)', 'Jeûne liquide\n(recommandation : ≤ 2h)']
moyennes_obs = [solide.mean(), liquide.mean()]
recommandes  = [SEUIL_SOLIDE, SEUIL_LIQUIDE]
x = np.arange(len(categories))
w = 0.35
b1 = ax.bar(x - w/2, recommandes,   w, label='Recommandation max (SFAR/ASA)',
            color='#2ecc71', edgecolor='white', alpha=0.85)
b2 = ax.bar(x + w/2, moyennes_obs,  w, label='Observé (moyenne ± ET)',
            color='#e74c3c', edgecolor='white', alpha=0.85,
            yerr=[solide.std(), liquide.std()], capsize=5,
            error_kw=dict(ecolor='gray', linewidth=1.5))
for bar, val in zip(b1, recommandes):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
            f'{val}h', ha='center', va='bottom', fontsize=11, fontweight='bold')
for bar, val in zip(b2, moyennes_obs):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
            f'{val:.1f}h', ha='center', va='bottom', fontsize=11, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=10)
ax.set_ylabel('Durée (heures)')
ax.set_title('Comparaison jeûne observé vs recommandations\nSFAR / ASA 2017',
             fontweight='bold', pad=12)
ax.legend(fontsize=9)
ax.set_ylim(0, max(moyennes_obs) + 3)
ax.spines[['top','right']].set_visible(False)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/14_comparaison_recommandations.png', bbox_inches='tight')
plt.close()
print("  → Figure 14 sauvegardée")

# ─────────────────────────────────────────────────────────────────────────────
# 6. TABLEAU RÉCAPITULATIF FINAL (console)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print(" TABLEAU RÉCAPITULATIF FINAL")
print("="*70)
summary = {
    'Effectif total (N)'                             : N,
    'Âge moyen (ans)'                               : f"{age_stats['moyenne']} ± {age_stats['écart-type']}",
    'Sex-ratio H/F'                                 : f"{(df['sexe']=='Masculin').sum()} / {(df['sexe']=='Féminin').sum()}",
    'IMC moyen (n renseignés)'                      : f"{round(float(imc_valid.mean()), 1)} ± {round(float(imc_valid.std()), 1)} (n={len(imc_valid)})",
    '% surpoids + obésité (IMC > 24,99)'            : f"{pct_surpoids}%",
    'ASA I (%)'                                     : f"{asa_tab.loc[asa_tab['score_asa']=='ASA I','%'].values[0] if 'ASA I' in asa_tab['score_asa'].values else 'N/A'}%",
    'Durée jeûne solide — moyenne (h)'              : f"{sol_stats['Moyenne (h)']} ± {sol_stats['Écart-type']}",
    'Durée jeûne liquide — moyenne (h)'             : f"{liq_stats['Moyenne (h)']} ± {liq_stats['Écart-type']}",
    f'Jeûne solide > 9h'                            : f"{n_sol_9h}/{len(solide)} ({pct_sol_9h}%)",
    f'Jeûne solide > {SEUIL_SOLIDE}h (recom.)'      : f"{n_sol_sup_rec}/{len(solide)} ({pct_sol_sup_rec}%)",
    f'Jeûne liquide > {SEUIL_LIQUIDE}h (recom.)'    : f"{n_liq_sup2}/{len(liquide)} ({pct_liq_sup2}%)",
    '% patients avec retard chirurgical'            : f"{pct_retard}%",
    '% instructions reçues'                        : f"{round((df['instructions_recues']=='OUI').sum()/N*100, 1)}%",
    'Source principale instructions'                : source_tab.iloc[0]['Source'] if len(source_tab) > 0 else 'N/A',
}
for k, v in summary.items():
    print(f"  {k:<55}: {v}")

print(f"\n  Figures sauvegardées dans : {OUTPUT_DIR}")
print("\n  ✓ Analyse Python terminée avec succès.\n")
