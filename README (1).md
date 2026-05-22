# 📋 ÉVALUATION DU JEÛNE PRÉOPÉRATOIRE EN CHIRURGIE ÉLECTIVE
## Hôpital Général de Douala — 2026



---

## 📌 Résumé du projet

Cette recherche constitue une **étude transversale descriptive** menée au bloc opératoire de l'**Hôpital Général de Douala (HGD)** entre février et mars 2026. Elle évalue les pratiques réelles de jeûne préopératoire auprès de **195 patients** consécutivement inclus en chirurgie élective, et les compare aux recommandations internationales de la **SFAR (2015)** et de l'**ASA (2017)**.

### 🎯 Question de recherche
> *Les durées de jeûne préopératoire pratiquées à l'HGD sont-elles conformes aux recommandations internationales, et quels facteurs sont associés à un jeûne prolongé ?*

---

## 📊 Résultats clés

| Indicateur | Valeur observée | Recommandation |
|---|---|---|
| **Effectif total** | N = 195 patients | — |
| **Sexe masculin** | 117 (60,0 %) | — |
| **Âge moyen ± ET** | 40,6 ± 21,5 ans | — |
| **Âge médian [Q1–Q3]** | 43 [24–57] ans | — |
| **IMC moyen ± ET** | 25,0 ± 2,1 kg/m² (n=149) | Normal : 18,5–24,99 |
| **ASA I** | 152 patients (77,9 %) | — |
| **Durée jeûne SOLIDE** | **9,38 ± 1,57 h** | ≤ 6 h (SFAR/ASA) |
| **Durée jeûne LIQUIDE** | **9,23 ± 1,65 h** | ≤ 2 h (SFAR/ASA) |
| **Solide > 6h (seuil recom.)** | **97,4 %** des patients | 0 % idéal |
| **Liquide > 2h (seuil recom.)** | **100 %** des patients | 0 % idéal |
| **Retard chirurgical** | 95/195 (48,7 %) | — |
| **Durée retard moy. ± ET** | 2,1 ± 1,0 h | — |
| **Association retard × jeûne prolongé** | **p < 0,001 \*\*\*** | Test Mann-Whitney |

### 💡 Conclusion principale
Les durées de jeûne préopératoire à l'HGD dépassent **quasi-systématiquement** les recommandations SFAR/ASA. Le facteur le plus fortement associé au jeûne prolongé est la **présence d'un retard chirurgical** (p < 0,001). Les instructions sont délivrées à 97,9 % par des infirmiers, sur la base de la règle historique NPO après minuit, sans référence aux guidelines actualisés.

---

## 🗂️ Structure du dépôt / du dossier ZIP

```
Resultats_Complets_These_DORA_HGD_2026.zip
│
├── 📄 README.txt                          ← Guide rapide intégré au ZIP
│

│   
│
├── 01_Scripts_Python/
│   └── analyse_jeune_preop_v2.py          ← Script Python (975 lignes)
│
├── 02_Scripts_R/
│   └── analyse_jeune_preop.R              ← Script R (815 lignes)
│
├── 03_Images_Python/                      ← 17 figures (matplotlib/seaborn)
│   ├── 00_dashboard.png
│   ├── 01_sexe.png
│   ├── 02_age.png
│   ├── 03_imc.png
│   ├── 04_asa.png
│   ├── 05_specialite.png
│   ├── 06_anesthesie.png
│   ├── 07_antecedents.png
│   ├── 08_distribution_jeune.png
│   ├── 09_boxplots_jeune.png
│   ├── 10_jeune_par_specialite.png
│   ├── 11_instructions.png
│   ├── 12_source_instructions.png
│   ├── 13_retard_chirurgical.png
│   ├── 14_retard_par_specialite.png
│   ├── 15_heatmap_specialite_anesthesie.png
│   └── 16_comparaison_recommandations.png
│
├── 04_Images_R/                           ← 20 figures (ggplot2/tidyverse)
│   ├── R01_sexe.png
│   ├── R02_age_histo.png
│   ├── R03_age_groupes.png
│   ├── R04_imc.png
│   ├── R05_imc_categories.png
│   ├── R06_asa_pie.png
│   ├── R07_asa_age.png
│   ├── R08_specialite.png
│   ├── R09_anesthesie.png
│   ├── R10_distribution_jeune.png
│   ├── R11_boxplots_jeune.png
│   ├── R12_jeune_par_specialite.png
│   ├── R13_instructions.png
│   ├── R14_source_instructions.png
│   ├── R15_retard_donut.png
│   ├── R16_retard_distribution.png
│   ├── R17_retard_specialite.png
│   ├── R18_violin_jeune_retard.png
│   ├── R19_comparaison_recommandations.png
│   └── R20_heatmap.png
│
└── 05_Donnees/
    └── data_clean.csv                     ← 195 patients, données nettoyées
```

---
---

### 2️⃣ `analyse_jeune_preop_v2.py` — Script Python (975 lignes)

Script d'analyse statistique complet, entièrement **commenté en français**, conforme aux bonnes pratiques épidémiologiques (STROBE).

**Environnement requis :**
```bash
pip install pandas numpy matplotlib seaborn scipy openpyxl
```

**Packages utilisés :**

| Package | Version testée | Rôle |
|---|---|---|
| `pandas` | ≥ 2.0 | Manipulation des données |
| `numpy` | ≥ 1.24 | Calculs numériques |
| `matplotlib` | ≥ 3.7 | Génération des figures |
| `seaborn` | ≥ 0.12 | Visualisations statistiques |
| `scipy` | ≥ 1.10 | Tests statistiques (Mann-Whitney, Kruskal-Wallis) |
| `openpyxl` | ≥ 3.1 | Lecture du fichier Excel source |

**Structure du script :**

```
0. Imports et configuration (thème graphique, seuils recommandés)
1. Chargement et nettoyage des données
   ├── Parsing des colonnes (heures au format NNh00, âge, sexe, ASA...)
   ├── Normalisation des modalités textuelles
   └── Création de variables dérivées (IMC_cat, jeune_prolonge, groupe_age)
2. Objectif 1 — Caractéristiques sociodémographiques et cliniques
   ├── Fig 01 : Répartition par sexe
   ├── Fig 02 : Distribution des âges + groupes d'âge
   ├── Fig 03 : IMC (histogramme + catégories OMS)
   ├── Fig 04 : Score ASA + âge moyen par score
   ├── Fig 05 : Spécialité chirurgicale
   ├── Fig 06 : Type d'anesthésie
   └── Fig 07 : Antécédents opératoires
3. Objectif 2 — Durée du jeûne préopératoire
   ├── Statistiques descriptives (n, moy, méd, ET, min, max, Q1, Q3)
   ├── % dépassant les seuils SFAR/ASA
   ├── Fig 08 : Histogrammes distributions vs recommandations
   ├── Fig 09 : Boxplots jeûne solide et liquide
   └── Fig 10 : Durée de jeûne par spécialité chirurgicale
4. Objectif 3 — Instructions et connaissance
   ├── Fig 11 : Conformité aux instructions de jeûne
   └── Fig 12 : Source des instructions
5. Objectif 4 — Facteurs associés au jeûne prolongé
   ├── Fig 13 : Fréquence et durée des retards chirurgicaux
   ├── Fig 14 : Retards par spécialité
   ├── Tests Mann-Whitney (sexe, retard) et Kruskal-Wallis (spécialité)
   ├── Fig 15 : Heatmap spécialité × anesthésie
   └── Fig 16 : Comparaison observé vs recommandé (bilan synthétique)
6. Tableau récapitulatif final (console)
```

**Exécution :**
```bash
# Modifier le chemin INPUT_FILE ligne 47 si nécessaire
python3 analyse_jeune_preop_v2.py
# → 17 figures sauvegardées dans ./images/
```

---

### 3️⃣ `analyse_jeune_preop.R` — Script R (815 lignes)

Script R **équivalent** au script Python, utilisant l'écosystème `tidyverse` et `ggplot2`. Produit 20 figures avec une esthétique ggplot2 professionnelle.

**Environnement requis :**
```r
install.packages(c("ggplot2","dplyr","tidyr","scales",
                   "gridExtra","RColorBrewer","viridis"))
# readxl disponible via : install.packages("readxl")
# ou sous Ubuntu/Debian : sudo apt install r-cran-readxl
```

**Packages utilisés :**

| Package | Rôle |
|---|---|
| `ggplot2` | Grammaire des graphiques — toutes les figures |
| `dplyr` | Manipulation des données (pipe, group_by, summarise) |
| `tidyr` | Mise en forme longue/large (pivot_longer) |
| `scales` | Formatage des axes (percent, comma) |
| `gridExtra` | Assemblage multi-panneaux |
| `RColorBrewer` | Palettes de couleurs professionnelles |
| `viridis` | Palette accessible aux daltoniens (heatmap) |

**Figures produites en plus du script Python :**

| Figure | Description |
|---|---|
| `R15_retard_donut.png` | Donut chart pour les retards chirurgicaux |
| `R16_retard_distribution.png` | Distribution des durées de retard |
| `R18_violin_jeune_retard.png` | Violin plot : jeûne solide selon présence de retard |
| `R20_heatmap.png` | Heatmap avec palette viridis (meilleure lisibilité) |

**Exécution :**
```bash
# Lire le CSV nettoyé généré par le script Python
Rscript analyse_jeune_preop.R
# → 20 figures sauvegardées dans ./images_R/
```

> ⚠️ **Note :** Le script R lit `data_clean.csv` (fourni dans `06_Donnees/`). Le fichier Excel source ne peut pas être lu directement sous Linux si le nom contient des accents.

---

### 4️⃣ `04_Images_Python/` — 17 figures matplotlib/seaborn

Toutes les figures sont produites en **150 dpi**, format PNG, avec un thème `whitegrid` (seaborn) et la palette `Set2`.

| Figure | Titre | Objectif |
|---|---|---|
| `00_dashboard.png` | Tableau de bord général (6 panneaux) | Synthèse |
| `01_sexe.png` | Répartition par sexe | Obj. 1 |
| `02_age.png` | Distribution des âges + groupes d'âge | Obj. 1 |
| `03_imc.png` | IMC : histogramme + catégories OMS | Obj. 1 |
| `04_asa.png` | Score ASA : pie + âge moyen ± ET | Obj. 1 |
| `05_specialite.png` | Spécialité chirurgicale (barres horizontales) | Obj. 1 |
| `06_anesthesie.png` | Type d'anesthésie | Obj. 1 |
| `07_antecedents.png` | Antécédents opératoires | Obj. 1 |
| `08_distribution_jeune.png` | Histogrammes jeûne vs seuils SFAR/ASA | Obj. 2 |
| `09_boxplots_jeune.png` | Boxplots jeûne solide et liquide | Obj. 2 |
| `10_jeune_par_specialite.png` | Durée de jeûne par spécialité | Obj. 2 |
| `11_instructions.png` | Conformité aux instructions | Obj. 3 |
| `12_source_instructions.png` | Source des instructions (pie) | Obj. 3 |
| `13_retard_chirurgical.png` | Fréquence + distribution retards | Obj. 4 |
| `14_retard_par_specialite.png` | % retards par spécialité | Obj. 4 |
| `15_heatmap_specialite_anesthesie.png` | Heatmap (YlOrRd) | Obj. 4 |
| `16_comparaison_recommandations.png` | Observé vs recommandé | Obj. 4 |

---

### 5️⃣ `05_Images_R/` — 20 figures ggplot2/tidyverse

Figures équivalentes au script Python, avec en plus :

| Figure | Spécificité R |
|---|---|
| `R15_retard_donut.png` | Donut chart (geom_col + coord_polar) |
| `R16_retard_distribution.png` | Histogramme durée retard avec annotation |
| `R18_violin_jeune_retard.png` | Violin plot + boxplot superposés + p-value |
| `R20_heatmap.png` | Heatmap palette `viridis` (meilleure perception chromatique) |

---

### 6️⃣ `data_clean.csv` — Données nettoyées (195 lignes × 16 variables)

Fichier CSV UTF-8 prêt à l'analyse, généré par le script Python à partir du fichier Excel source.

**Variables disponibles :**

| Variable | Type | Description |
|---|---|---|
| `sexe` | Catégorielle | Masculin / Feminin / NR |
| `age` | Numérique | Âge en années |
| `antecedents` | Catégorielle | Oui / Non / NR |
| `score_asa` | Catégorielle | ASA_I / ASA_II / NR |
| `imc` | Numérique | Indice de Masse Corporelle (kg/m²) |
| `specialite` | Catégorielle | Spécialité chirurgicale harmonisée |
| `type_anesthesie` | Catégorielle | AG_IOT / AG_seule / ALR_RA / AL / APD / Autre |
| `instructions_recues` | Catégorielle | OUI / NON / NR |
| `source_instructions` | Catégorielle | Infirmier / Medecin / Sage_femme / Autre / NR |
| `consigne_liquide` | Catégorielle | OUI / NON / NR |
| `consigne_solide` | Catégorielle | OUI / NON / NR |
| `patient_compris` | Catégorielle | OUI / NON / NR |
| `duree_solide_h` | Numérique | Durée du jeûne solide (heures décimales) |
| `duree_liquide_h` | Numérique | Durée du jeûne liquide (heures décimales) |
| `retard_chirurgie` | Catégorielle | OUI / NON / NR |
| `duree_retard_h` | Numérique | Durée du retard chirurgical (heures décimales) |

> **Codage des valeurs manquantes :** `NR` = Non Renseigné (dans les colonnes catégorielles) ; `NaN` (dans les colonnes numériques).

---

## 🔬 Méthodologie statistique

### Tests utilisés

| Test | Variable dépendante | Variable indépendante | Logiciel |
|---|---|---|---|
| **Mann-Whitney U** | Durée jeûne solide | Sexe (H vs F) | Python + R |
| **Mann-Whitney U** | Durée jeûne solide | Retard (OUI vs NON) | Python + R |
| **Kruskal-Wallis** | Durée jeûne solide | Spécialité chirurgicale | Python + R |

> Tests non paramétriques retenus après vérification de la non-normalité des distributions (Shapiro-Wilk). Seuil de significativité : **α = 0,05**.

### Références des recommandations utilisées comme seuils comparateurs

| Recommandation | Jeûne solide | Jeûne liquide | Source |
|---|---|---|---|
| SFAR 2015 | ≤ 6h | ≤ 2h | Société Française d'Anesthésie-Réanimation |
| ASA 2017 | ≤ 6h | ≤ 2h | American Society of Anesthesiologists |

---

## ⚙️ Environnements techniques

### Python
```
Python  : 3.12
pandas  : 2.2
numpy   : 1.26
matplotlib : 3.8
seaborn : 0.13
scipy   : 1.12
openpyxl: 3.1
```

### R
```
R       : 4.3.3
ggplot2 : 3.5
dplyr   : 1.1
tidyr   : 1.3
RColorBrewer : 1.1
viridis : 0.6
scales  : 1.3
gridExtra: 2.3
```

### Système
```
OS      : Ubuntu 24.04 LTS
Résolution figures : 150 dpi
Format figures : PNG (RGB)
Format document : DOCX (Office Open XML)
```


 ## le 15 mai 2026 — Analyse statistique réalisée avec Python 3.12 et R 4.3.3*
