# =============================================================================
# ANALYSE STATISTIQUE DU JEÛNE PRÉOPÉRATOIRE
# Hôpital Général de Douala — Chirurgie Élective 2026
# =============================================================================
# Script R — Version 1.0
# Standard : STROBE / bonnes pratiques épidémiologiques en R
# Packages  : ggplot2, dplyr, tidyr, scales, gridExtra, RColorBrewer, viridis
# Auteur    : Étude transversale sur le jeûne préopératoire
# =============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# 0. PACKAGES ET CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

# Chargement des packages nécessaires
library(ggplot2)          # Visualisation (grammaire des graphiques)
library(dplyr)            # Manipulation de données (pipe, mutate, group_by)
library(tidyr)            # Mise en forme des données (pivot_longer/wider)
library(scales)           # Formatage des axes (percent, comma)
library(gridExtra)        # Assemblage multi-panneaux (grid.arrange)
library(RColorBrewer)     # Palettes de couleurs professionnelles
library(viridis)          # Palettes accessibles aux daltoniens
library(stats)            # Tests statistiques (chisq.test, wilcox.test)

# ── Chemins entrée / sortie ─────────────────────────────────────────────────
INPUT_FILE  <- "/home/claude/jeune_preop/data_clean.csv"
OUTPUT_DIR  <- "/home/claude/jeune_preop/images_R"
dir.create(OUTPUT_DIR, showWarnings = FALSE, recursive = TRUE)

# ── Seuils recommandés SFAR / ASA 2017 ─────────────────────────────────────
SEUIL_SOLIDE  <- 6.0   # heures — solides légers
SEUIL_LIQUIDE <- 2.0   # heures — liquides clairs

# ── Thème graphique global ──────────────────────────────────────────────────
theme_jeune <- theme_bw(base_size = 12) +
  theme(
    plot.title       = element_text(face = "bold", size = 13, hjust = 0.5),
    plot.subtitle    = element_text(size = 10, hjust = 0.5, color = "grey40"),
    axis.title       = element_text(face = "bold"),
    axis.text        = element_text(color = "grey30"),
    legend.title     = element_text(face = "bold"),
    legend.position  = "bottom",
    panel.grid.minor = element_blank(),
    strip.text       = element_text(face = "bold")
  )

# Palette de couleurs principale
PALETTE <- brewer.pal(8, "Set2")

# ── Fonction utilitaire : sauvegarder une figure ────────────────────────────
save_fig <- function(p, filename, w = 10, h = 6) {
  path <- file.path(OUTPUT_DIR, filename)
  ggsave(path, plot = p, width = w, height = h, dpi = 150, bg = "white")
  cat(sprintf("  → %s sauvegardé\n", filename))
  invisible(path)
}


# =============================================================================
# 1. CHARGEMENT ET NETTOYAGE DES DONNÉES
# =============================================================================
cat("\n", strrep("=", 70), "\n")
cat("  ÉTAPE 1 — CHARGEMENT ET NETTOYAGE\n")
cat(strrep("=", 70), "\n")

# Lecture du fichier CSV nettoyé (généré par le script Python)
df <- read.csv(INPUT_FILE, stringsAsFactors = FALSE)
N  <- nrow(df)

# ── Conversion des facteurs ─────────────────────────────────────────────────
df$sexe             <- factor(df$sexe, levels = c("Masculin", "Feminin", "NR"))
df$score_asa        <- factor(df$score_asa, levels = c("ASA_I", "ASA_II", "NR"))
df$specialite       <- factor(df$specialite)
df$type_anesthesie  <- factor(df$type_anesthesie)
df$retard_chirurgie <- factor(df$retard_chirurgie, levels = c("OUI", "NON", "NR"))
df$antecedents      <- factor(df$antecedents, levels = c("Non", "Oui", "NR"))

# ── Variable dérivée : jeûne prolongé (solide > 9h) ─────────────────────────
df$jeune_prolonge <- ifelse(
  is.na(df$duree_solide_h), NA,
  ifelse(df$duree_solide_h > 9, "Prolongé (>9h)", "Acceptable (≤9h)")
)
df$jeune_prolonge <- factor(df$jeune_prolonge)

# ── Catégorie IMC (classification OMS) ─────────────────────────────────────
df$imc_cat <- cut(df$imc,
  breaks = c(0, 18.5, 24.99, 29.99, Inf),
  labels = c("Insuffisance\npondérale", "Poids\nnormal",
             "Surpoids", "Obésité"),
  right  = TRUE)

# ── Groupes d'âge ───────────────────────────────────────────────────────────
df$groupe_age <- cut(df$age,
  breaks = c(0, 15, 30, 45, 60, Inf),
  labels = c("<15 ans", "15–30 ans", "31–45 ans", "46–60 ans", ">60 ans"),
  right  = TRUE)

cat(sprintf("  → %d patients | %d durées solide | %d durées liquide | %d IMC\n",
            N,
            sum(!is.na(df$duree_solide_h)),
            sum(!is.na(df$duree_liquide_h)),
            sum(!is.na(df$imc))))


# =============================================================================
# 2. OBJECTIF 1 — CARACTÉRISTIQUES SOCIODÉMOGRAPHIQUES ET CLINIQUES
# =============================================================================
cat("\n", strrep("=", 70), "\n")
cat("  OBJECTIF 1 — CARACTÉRISTIQUES SOCIODÉMOGRAPHIQUES ET CLINIQUES\n")
cat(strrep("=", 70), "\n")

# ── 2.1 SEXE ─────────────────────────────────────────────────────────────────
cat("\n── Sexe ──\n")
sexe_tab <- df %>%
  filter(!is.na(sexe), sexe != "NR") %>%
  count(sexe) %>%
  mutate(pct = round(n / N * 100, 1),
         label = paste0(n, "\n(", pct, "%)"))
print(sexe_tab)

p_sexe <- ggplot(sexe_tab, aes(x = sexe, y = n, fill = sexe)) +
  geom_col(width = 0.5, color = "white", linewidth = 0.8) +
  geom_text(aes(label = label), vjust = -0.3, fontface = "bold", size = 4) +
  scale_fill_manual(values = PALETTE[1:2], guide = "none") +
  scale_y_continuous(limits = c(0, max(sexe_tab$n) * 1.2)) +
  labs(title = paste0("Répartition par sexe (N = ", N, ")"),
       x = "Sexe", y = "Effectif") +
  theme_jeune
save_fig(p_sexe, "R01_sexe.png", w = 7, h = 5)

# ── 2.2 ÂGE ──────────────────────────────────────────────────────────────────
cat("\n── Âge ──\n")
age_stats <- df %>% summarise(
  n    = sum(!is.na(age)),
  moy  = round(mean(age, na.rm = TRUE), 1),
  med  = round(median(age, na.rm = TRUE), 0),
  et   = round(sd(age, na.rm = TRUE), 1),
  mini = min(age, na.rm = TRUE),
  maxi = max(age, na.rm = TRUE),
  Q1   = quantile(age, 0.25, na.rm = TRUE),
  Q3   = quantile(age, 0.75, na.rm = TRUE))
print(as.data.frame(age_stats))

# Histogramme d'âge
p_age <- ggplot(df %>% filter(!is.na(age)), aes(x = age)) +
  geom_histogram(binwidth = 5, fill = PALETTE[3],
                 color = "white", linewidth = 0.6) +
  geom_vline(xintercept = age_stats$moy, color = "red",
             linetype = "dashed", linewidth = 1.2) +
  geom_vline(xintercept = age_stats$med, color = "navy",
             linetype = "dotted", linewidth = 1.2) +
  annotate("text", x = age_stats$moy + 3, y = Inf,
           label = paste0("Moy. = ", age_stats$moy, " ans"),
           color = "red", vjust = 1.5, hjust = 0, fontface = "bold") +
  annotate("text", x = age_stats$med - 3, y = Inf,
           label = paste0("Méd. = ", age_stats$med, " ans"),
           color = "navy", vjust = 1.5, hjust = 1, fontface = "bold") +
  labs(title = paste0("Distribution des âges (n = ", age_stats$n, ")"),
       subtitle = paste0("Moyenne = ", age_stats$moy,
                         " ans ± ", age_stats$et,
                         " | Étendue : ", age_stats$mini, "–", age_stats$maxi, " ans"),
       x = "Âge (ans)", y = "Effectif") +
  theme_jeune
save_fig(p_age, "R02_age_histo.png")

# Barres groupes d'âge
grp_age <- df %>%
  filter(!is.na(groupe_age)) %>%
  count(groupe_age) %>%
  mutate(pct = round(n / N * 100, 1))

p_age_grp <- ggplot(grp_age, aes(x = groupe_age, y = n,
                                  fill = groupe_age)) +
  geom_col(color = "white", linewidth = 0.8, width = 0.65) +
  geom_text(aes(label = paste0(n, "\n(", pct, "%)")),
            vjust = -0.3, fontface = "bold", size = 3.8) +
  scale_fill_brewer(palette = "Blues", guide = "none") +
  scale_y_continuous(limits = c(0, max(grp_age$n) * 1.25)) +
  labs(title = "Effectifs par groupe d'âge",
       x = "Groupe d'âge", y = "Effectif") +
  theme_jeune
save_fig(p_age_grp, "R03_age_groupes.png", w = 8, h = 5)

# ── 2.3 IMC ───────────────────────────────────────────────────────────────────
cat("\n── IMC ──\n")
imc_valid <- df %>% filter(!is.na(imc))
cat(sprintf("  n=%d | Moy=%.1f | Méd=%.1f | ET=%.1f\n",
            nrow(imc_valid),
            mean(imc_valid$imc), median(imc_valid$imc),
            sd(imc_valid$imc)))

imc_cat_tab <- imc_valid %>%
  count(imc_cat) %>%
  mutate(pct = round(n / nrow(imc_valid) * 100, 1))
print(imc_cat_tab)

p_imc <- ggplot(imc_valid, aes(x = imc)) +
  geom_histogram(binwidth = 1, fill = PALETTE[4],
                 color = "white", linewidth = 0.5) +
  geom_vline(xintercept = c(18.5, 25, 30),
             color = c("blue", "orange", "red"),
             linetype = "dashed", linewidth = 1) +
  geom_vline(xintercept = mean(imc_valid$imc, na.rm = TRUE),
             color = "black", linetype = "dotdash", linewidth = 1.2) +
  annotate("text", x = 18.5, y = Inf,
           label = "18,5", color = "blue", vjust = 1.8, hjust = -0.1) +
  annotate("text", x = 25, y = Inf,
           label = "25", color = "orange", vjust = 1.8, hjust = -0.1) +
  annotate("text", x = 30, y = Inf,
           label = "30", color = "red", vjust = 1.8, hjust = -0.1) +
  labs(title = paste0("Distribution de l'IMC (n = ", nrow(imc_valid), ")"),
       subtitle = paste0("Moyenne = ", round(mean(imc_valid$imc), 1),
                         " kg/m² | ",
                         round(sum(imc_valid$imc > 24.99) /
                               nrow(imc_valid) * 100, 1),
                         "% en surpoids ou obèses"),
       x = "IMC (kg/m²)", y = "Effectif") +
  theme_jeune
save_fig(p_imc, "R04_imc.png")

# Barres catégories IMC
p_imc_cat <- ggplot(imc_cat_tab %>% filter(!is.na(imc_cat)),
                    aes(x = imc_cat, y = n, fill = imc_cat)) +
  geom_col(color = "white", linewidth = 0.8, width = 0.6) +
  geom_text(aes(label = paste0(n, "\n(", pct, "%)")),
            vjust = -0.3, fontface = "bold", size = 4) +
  scale_fill_manual(values = PALETTE[1:4], guide = "none") +
  scale_y_continuous(limits = c(0, max(imc_cat_tab$n, na.rm = TRUE) * 1.3)) +
  labs(title = "Répartition par catégorie IMC (OMS)",
       x = "Catégorie IMC", y = "Effectif") +
  theme_jeune
save_fig(p_imc_cat, "R05_imc_categories.png", w = 8, h = 5)

# ── 2.4 SCORE ASA ─────────────────────────────────────────────────────────────
cat("\n── Score ASA ──\n")
asa_valid <- df %>% filter(score_asa != "NR", !is.na(score_asa))
asa_tab <- asa_valid %>%
  group_by(score_asa) %>%
  summarise(n = n(), age_moy = round(mean(age, na.rm = TRUE), 1),
            age_et = round(sd(age, na.rm = TRUE), 1)) %>%
  mutate(pct = round(n / N * 100, 1))
print(as.data.frame(asa_tab))

# Pie ASA
p_asa_pie <- ggplot(asa_tab, aes(x = "", y = n, fill = score_asa)) +
  geom_col(width = 1, color = "white", linewidth = 1) +
  coord_polar("y", start = 0) +
  geom_text(aes(label = paste0(score_asa, "\n", n, " (", pct, "%)")),
            position = position_stack(vjust = 0.5),
            fontface = "bold", size = 4.5) +
  scale_fill_manual(values = PALETTE[1:2], guide = "none") +
  labs(title = "Répartition par score ASA") +
  theme_void() +
  theme(plot.title = element_text(face = "bold", size = 13, hjust = 0.5))
save_fig(p_asa_pie, "R06_asa_pie.png", w = 6, h = 6)

# Âge moyen par ASA
p_asa_age <- ggplot(asa_tab, aes(x = score_asa, y = age_moy, fill = score_asa)) +
  geom_col(width = 0.5, color = "white", linewidth = 0.8) +
  geom_errorbar(aes(ymin = age_moy - age_et, ymax = age_moy + age_et),
                width = 0.15, linewidth = 1, color = "grey40") +
  geom_text(aes(label = paste0(age_moy, " ans\n(n=", n, ")")),
            vjust = -0.7, fontface = "bold", size = 4) +
  scale_fill_manual(values = PALETTE[1:2], guide = "none") +
  scale_y_continuous(limits = c(0, max(asa_tab$age_moy + asa_tab$age_et) + 15)) +
  labs(title = "Âge moyen par score ASA (± ET)",
       x = "Score ASA", y = "Âge moyen (ans)") +
  theme_jeune
save_fig(p_asa_age, "R07_asa_age.png", w = 7, h = 5)

# ── 2.5 SPÉCIALITÉ CHIRURGICALE ───────────────────────────────────────────────
cat("\n── Spécialité chirurgicale ──\n")
spec_tab <- df %>%
  count(specialite) %>%
  arrange(desc(n)) %>%
  mutate(pct = round(n / N * 100, 1))
print(as.data.frame(spec_tab))

p_spec <- ggplot(spec_tab,
                 aes(x = reorder(specialite, n), y = n,
                     fill = specialite)) +
  geom_col(color = "white", linewidth = 0.6) +
  geom_text(aes(label = paste0(n, " (", pct, "%)")),
            hjust = -0.1, fontface = "bold", size = 3.8) +
  coord_flip() +
  scale_fill_manual(values = colorRampPalette(brewer.pal(9, "Set1"))(nrow(spec_tab)),
                    guide = "none") +
  scale_x_discrete(labels = function(x) gsub("_", " ", x)) +
  scale_y_continuous(limits = c(0, max(spec_tab$n) * 1.35)) +
  labs(title = paste0("Répartition par spécialité chirurgicale (N = ", N, ")"),
       x = NULL, y = "Effectif") +
  theme_jeune
save_fig(p_spec, "R08_specialite.png", w = 11, h = 7)

# ── 2.6 TYPE D'ANESTHÉSIE ─────────────────────────────────────────────────────
cat("\n── Type d'anesthésie ──\n")
anes_tab <- df %>%
  count(type_anesthesie) %>%
  arrange(desc(n)) %>%
  mutate(pct = round(n / N * 100, 1))
print(as.data.frame(anes_tab))

p_anes <- ggplot(anes_tab,
                 aes(x = reorder(type_anesthesie, n), y = n,
                     fill = type_anesthesie)) +
  geom_col(width = 0.6, color = "white", linewidth = 0.8) +
  geom_text(aes(label = paste0(n, "\n(", pct, "%)")),
            vjust = -0.3, fontface = "bold", size = 3.8) +
  scale_fill_brewer(palette = "Paired", guide = "none") +
  scale_y_continuous(limits = c(0, max(anes_tab$n) * 1.25)) +
  scale_x_discrete(labels = function(x) gsub("_", " + ", x)) +
  labs(title = paste0("Type d'anesthésie (N = ", N, ")"),
       x = "Type d'anesthésie", y = "Effectif") +
  theme_jeune +
  theme(axis.text.x = element_text(angle = 20, hjust = 1))
save_fig(p_anes, "R09_anesthesie.png", w = 9, h = 6)


# =============================================================================
# 3. OBJECTIF 2 — DURÉE DU JEÛNE PRÉOPÉRATOIRE
# =============================================================================
cat("\n", strrep("=", 70), "\n")
cat("  OBJECTIF 2 — DURÉE DU JEÛNE PRÉOPÉRATOIRE\n")
cat(strrep("=", 70), "\n")

sol <- df$duree_solide_h[!is.na(df$duree_solide_h)]
liq <- df$duree_liquide_h[!is.na(df$duree_liquide_h)]

# ── Statistiques descriptives ────────────────────────────────────────────────
cat(sprintf("\n── Jeûne solide (n=%d) ──\n", length(sol)))
cat(sprintf("  Moy=%.2fh | Méd=%.1fh | ET=%.2fh | Min=%.0fh | Max=%.0fh\n",
            mean(sol), median(sol), sd(sol), min(sol), max(sol)))
cat(sprintf("  Q1=%.1fh | Q3=%.1fh\n", quantile(sol,0.25), quantile(sol,0.75)))
cat(sprintf("  Solide > %.0fh (recom.) : %d/%d (%.1f%%)\n",
            SEUIL_SOLIDE, sum(sol > SEUIL_SOLIDE),
            length(sol), mean(sol > SEUIL_SOLIDE)*100))
cat(sprintf("  Solide > 9h : %d/%d (%.1f%%)\n",
            sum(sol > 9), length(sol), mean(sol > 9)*100))

cat(sprintf("\n── Jeûne liquide (n=%d) ──\n", length(liq)))
cat(sprintf("  Moy=%.2fh | Méd=%.1fh | ET=%.2fh | Min=%.0fh | Max=%.0fh\n",
            mean(liq), median(liq), sd(liq), min(liq), max(liq)))
cat(sprintf("  Liquide > %.0fh (recom.) : %d/%d (%.1f%%)\n",
            SEUIL_LIQUIDE, sum(liq > SEUIL_LIQUIDE),
            length(liq), mean(liq > SEUIL_LIQUIDE)*100))

# ── Histogrammes distributions ───────────────────────────────────────────────
jeune_long <- data.frame(
  valeur = c(sol, liq),
  type   = rep(c(sprintf("Jeûne SOLIDE (recommandation ≤ %.0fh)", SEUIL_SOLIDE),
                 sprintf("Jeûne LIQUIDE (recommandation ≤ %.0fh)", SEUIL_LIQUIDE)),
               c(length(sol), length(liq))))

seuils_df <- data.frame(
  type   = c(sprintf("Jeûne SOLIDE (recommandation ≤ %.0fh)", SEUIL_SOLIDE),
             sprintf("Jeûne LIQUIDE (recommandation ≤ %.0fh)", SEUIL_LIQUIDE)),
  seuil  = c(SEUIL_SOLIDE, SEUIL_LIQUIDE),
  moy    = c(mean(sol), mean(liq)))

p_dist <- ggplot(jeune_long, aes(x = valeur, fill = type)) +
  geom_histogram(binwidth = 1, color = "white", linewidth = 0.4,
                 alpha = 0.85, show.legend = FALSE) +
  geom_vline(data = seuils_df,
             aes(xintercept = seuil, color = "Recommandation"),
             linetype = "dashed", linewidth = 1.5) +
  geom_vline(data = seuils_df,
             aes(xintercept = moy, color = "Moyenne observée"),
             linetype = "dotted", linewidth = 1.5) +
  geom_rect(data = seuils_df,
            aes(xmin = seuil, xmax = Inf, ymin = -Inf, ymax = Inf),
            fill = "red", alpha = 0.07, inherit.aes = FALSE) +
  facet_wrap(~type, scales = "free_x") +
  scale_fill_manual(values = c(PALETTE[1], PALETTE[4])) +
  scale_color_manual(name = "",
                     values = c("Recommandation" = "red",
                                "Moyenne observée" = "navy")) +
  labs(title = "Distribution des durées de jeûne préopératoire",
       subtitle = "Zone rouge = dépassement des recommandations SFAR / ASA 2017",
       x = "Durée (heures)", y = "Effectif") +
  theme_jeune +
  theme(legend.position = "bottom")
save_fig(p_dist, "R10_distribution_jeune.png", w = 14, h = 7)

# ── Boxplots comparatifs ─────────────────────────────────────────────────────
p_box <- ggplot(jeune_long, aes(x = type, y = valeur, fill = type)) +
  geom_boxplot(width = 0.5, outlier.color = "red",
               outlier.shape = 16, outlier.size = 2,
               alpha = 0.7, color = "grey30") +
  geom_jitter(width = 0.12, alpha = 0.25, size = 1.2,
              color = "grey40") +
  geom_hline(yintercept = SEUIL_SOLIDE,
             color = "green4", linetype = "dashed", linewidth = 1.2) +
  geom_hline(yintercept = SEUIL_LIQUIDE,
             color = "orange", linetype = "dashed", linewidth = 1.2) +
  annotate("text", x = 2.5, y = SEUIL_SOLIDE + 0.2,
           label = sprintf("Max recommandé solide (%.0fh)", SEUIL_SOLIDE),
           color = "green4", fontface = "bold", hjust = 1, size = 3.5) +
  annotate("text", x = 2.5, y = SEUIL_LIQUIDE + 0.2,
           label = sprintf("Max recommandé liquide (%.0fh)", SEUIL_LIQUIDE),
           color = "orange", fontface = "bold", hjust = 1, size = 3.5) +
  scale_fill_manual(values = c(PALETTE[1], PALETTE[4]), guide = "none") +
  scale_x_discrete(labels = function(x) gsub(" \\(.*\\)", "", x)) +
  labs(title = "Boxplots des durées de jeûne préopératoire",
       subtitle = "Les points rouges représentent les valeurs extrêmes",
       x = NULL, y = "Durée (heures)") +
  theme_jeune
save_fig(p_box, "R11_boxplots_jeune.png", w = 10, h = 7)

# ── Durée de jeûne par spécialité ────────────────────────────────────────────
jeune_spec <- df %>%
  filter(specialite != "NR", !is.na(duree_solide_h)) %>%
  group_by(specialite) %>%
  summarise(
    n         = n(),
    sol_moy   = round(mean(duree_solide_h, na.rm = TRUE), 1),
    sol_et    = round(sd(duree_solide_h, na.rm = TRUE), 1),
    liq_moy   = round(mean(duree_liquide_h, na.rm = TRUE), 1),
    .groups   = "drop")
print(as.data.frame(jeune_spec))

# Pivot long pour ggplot
jeune_spec_long <- jeune_spec %>%
  select(specialite, sol_moy, liq_moy) %>%
  pivot_longer(cols = c(sol_moy, liq_moy),
               names_to = "type",
               values_to = "duree") %>%
  mutate(type = recode(type,
                       sol_moy = "Solide moyen (h)",
                       liq_moy = "Liquide moyen (h)"))

p_jeune_spec <- ggplot(jeune_spec_long,
                       aes(x = reorder(specialite, -duree),
                           y = duree, fill = type)) +
  geom_col(position = "dodge", color = "white",
           linewidth = 0.7, width = 0.7) +
  geom_hline(yintercept = SEUIL_SOLIDE,
             color = "red", linetype = "dashed", linewidth = 1.2) +
  geom_hline(yintercept = SEUIL_LIQUIDE,
             color = "orange", linetype = "dashed", linewidth = 1.2) +
  annotate("text", x = 0.5, y = SEUIL_SOLIDE + 0.15,
           label = sprintf("Seuil solide (%.0fh)", SEUIL_SOLIDE),
           color = "red", hjust = 0, fontface = "bold", size = 3.2) +
  annotate("text", x = 0.5, y = SEUIL_LIQUIDE + 0.15,
           label = sprintf("Seuil liquide (%.0fh)", SEUIL_LIQUIDE),
           color = "orange", hjust = 0, fontface = "bold", size = 3.2) +
  scale_fill_manual(values = c(PALETTE[1], PALETTE[4])) +
  scale_x_discrete(labels = function(x) gsub("_", " ", x)) +
  labs(title = "Durée moyenne de jeûne par spécialité chirurgicale",
       subtitle = "Comparaison avec les seuils recommandés SFAR / ASA 2017",
       x = "Spécialité chirurgicale",
       y = "Durée moyenne (heures)",
       fill = "Type de jeûne") +
  theme_jeune +
  theme(axis.text.x = element_text(angle = 35, hjust = 1))
save_fig(p_jeune_spec, "R12_jeune_par_specialite.png", w = 13, h = 7)


# =============================================================================
# 4. OBJECTIF 3 — INSTRUCTIONS ET CONNAISSANCE
# =============================================================================
cat("\n", strrep("=", 70), "\n")
cat("  OBJECTIF 3 — INSTRUCTIONS ET CONNAISSANCE\n")
cat(strrep("=", 70), "\n")

# ── Instructions et compréhension ────────────────────────────────────────────
vars_inst <- c(
  "Instructions reçues" = "instructions_recues",
  "Consigne : no liquide" = "consigne_liquide",
  "Consigne : no solide" = "consigne_solide",
  "Patient a compris" = "patient_compris")

inst_list <- lapply(names(vars_inst), function(label) {
  col <- vars_inst[label]
  data.frame(
    item = label,
    OUI  = sum(df[[col]] == "OUI", na.rm = TRUE),
    NON  = sum(df[[col]] == "NON", na.rm = TRUE),
    NR   = sum(df[[col]] == "NR",  na.rm = TRUE))
})
inst_df <- do.call(rbind, inst_list)
inst_df$pct_OUI <- round(inst_df$OUI / N * 100, 1)
print(inst_df)

# Pivot long pour barres
inst_long <- inst_df %>%
  pivot_longer(cols = c(OUI, NON, NR),
               names_to = "reponse", values_to = "n") %>%
  mutate(reponse = factor(reponse, levels = c("OUI", "NON", "NR")))

p_inst <- ggplot(inst_long, aes(x = item, y = n, fill = reponse)) +
  geom_col(position = "dodge", color = "white",
           linewidth = 0.7, width = 0.7) +
  scale_fill_manual(
    values = c("OUI" = PALETTE[3], "NON" = PALETTE[6], "NR" = "lightgrey"),
    name = "Réponse") +
  scale_x_discrete(labels = function(x) gsub(" ", "\n", x)) +
  labs(title = "Conformité aux instructions de jeûne préopératoire",
       x = NULL, y = "Effectif") +
  theme_jeune +
  theme(axis.text.x = element_text(angle = 20, hjust = 1))
save_fig(p_inst, "R13_instructions.png", w = 11, h = 6)

# ── Source des instructions ──────────────────────────────────────────────────
cat("\n── Source des instructions ──\n")
src_tab <- df %>%
  count(source_instructions) %>%
  mutate(pct = round(n / N * 100, 1)) %>%
  arrange(desc(n))
print(as.data.frame(src_tab))

p_src <- ggplot(src_tab,
                aes(x = "", y = n, fill = source_instructions)) +
  geom_col(width = 1, color = "white", linewidth = 1) +
  coord_polar("y", start = 0) +
  geom_text(aes(label = paste0(source_instructions, "\n",
                               n, " (", pct, "%)")),
            position = position_stack(vjust = 0.5),
            fontface = "bold", size = 4) +
  scale_fill_manual(values = PALETTE[1:nrow(src_tab)], guide = "none") +
  labs(title = "Source des instructions de jeûne\nreçues par les patients") +
  theme_void() +
  theme(plot.title = element_text(face = "bold", size = 13, hjust = 0.5))
save_fig(p_src, "R14_source_instructions.png", w = 7, h = 6)


# =============================================================================
# 5. OBJECTIF 4 — FACTEURS ASSOCIÉS AU JEÛNE PROLONGÉ
# =============================================================================
cat("\n", strrep("=", 70), "\n")
cat("  OBJECTIF 4 — FACTEURS ASSOCIÉS AU JEÛNE PROLONGÉ\n")
cat(strrep("=", 70), "\n")

# ── 5.1 Retard chirurgical ────────────────────────────────────────────────────
cat("\n── Retard chirurgical ──\n")
ret_tab <- df %>%
  count(retard_chirurgie) %>%
  mutate(pct = round(n / N * 100, 1))
print(as.data.frame(ret_tab))

n_ret   <- sum(df$retard_chirurgie == "OUI", na.rm = TRUE)
pct_ret <- round(n_ret / N * 100, 1)
ret_valid <- df %>% filter(retard_chirurgie == "OUI",
                            !is.na(duree_retard_h))
cat(sprintf("  Retards : %d/%d (%.1f%%)\n", n_ret, N, pct_ret))
cat(sprintf("  Durée : min=%.0fh | max=%.0fh | moy=%.1f±%.1fh\n",
            min(ret_valid$duree_retard_h, na.rm = TRUE),
            max(ret_valid$duree_retard_h, na.rm = TRUE),
            mean(ret_valid$duree_retard_h, na.rm = TRUE),
            sd(ret_valid$duree_retard_h, na.rm = TRUE)))

# Donut retard
ret_pie_df <- data.frame(
  cat = c(sprintf("Avec retard\n(%.1f%%)", pct_ret),
          sprintf("Sans retard\n(%.1f%%)", 100 - pct_ret)),
  n   = c(n_ret, N - n_ret))

p_ret_pie <- ggplot(ret_pie_df, aes(x = 2, y = n, fill = cat)) +
  geom_col(color = "white", linewidth = 1) +
  coord_polar("y") +
  xlim(0.5, 2.5) +
  geom_text(aes(label = cat),
            position = position_stack(vjust = 0.5),
            fontface = "bold", size = 4.5) +
  scale_fill_manual(values = c(PALETTE[3], "lightgrey"), guide = "none") +
  labs(title = paste0("Retards chirurgicaux (N = ", N, ")")) +
  theme_void() +
  theme(plot.title = element_text(face = "bold", size = 13, hjust = 0.5))
save_fig(p_ret_pie, "R15_retard_donut.png", w = 7, h = 6)

# ── Distribution durée retard ─────────────────────────────────────────────────
p_ret_dist <- ggplot(ret_valid, aes(x = duree_retard_h)) +
  geom_histogram(binwidth = 0.5, fill = PALETTE[5],
                 color = "white", linewidth = 0.5) +
  geom_vline(xintercept = mean(ret_valid$duree_retard_h, na.rm = TRUE),
             color = "red", linetype = "dashed", linewidth = 1.5) +
  annotate("text",
           x = mean(ret_valid$duree_retard_h, na.rm = TRUE) + 0.1,
           y = Inf,
           label = sprintf("Moy. = %.1fh",
                           mean(ret_valid$duree_retard_h, na.rm = TRUE)),
           color = "red", fontface = "bold", vjust = 1.5, hjust = 0) +
  labs(title = sprintf("Distribution des durées de retard (n = %d)",
                       nrow(ret_valid)),
       subtitle = sprintf("Min: %.0fh | Max: %.0fh | Moy: %.1f ± %.1fh",
                          min(ret_valid$duree_retard_h, na.rm = TRUE),
                          max(ret_valid$duree_retard_h, na.rm = TRUE),
                          mean(ret_valid$duree_retard_h, na.rm = TRUE),
                          sd(ret_valid$duree_retard_h, na.rm = TRUE)),
       x = "Durée du retard (heures)", y = "Effectif") +
  theme_jeune
save_fig(p_ret_dist, "R16_retard_distribution.png", w = 9, h = 6)

# ── Retard par spécialité ─────────────────────────────────────────────────────
spec_total <- df %>% count(specialite, name = "total")
spec_ret <- df %>%
  filter(retard_chirurgie == "OUI", specialite != "NR") %>%
  group_by(specialite) %>%
  summarise(n_ret = n(),
            ret_moy = round(mean(duree_retard_h, na.rm = TRUE), 1),
            ret_max = max(duree_retard_h, na.rm = TRUE),
            .groups = "drop") %>%
  left_join(spec_total, by = "specialite") %>%
  mutate(pct = round(n_ret / total * 100, 1))
print(as.data.frame(spec_ret))

p_spec_ret <- ggplot(spec_ret,
                     aes(x = reorder(specialite, -pct),
                         y = pct, fill = specialite)) +
  geom_col(color = "white", linewidth = 0.7, width = 0.65) +
  geom_text(aes(label = paste0(pct, "%\n(n=", n_ret, ")")),
            vjust = -0.3, fontface = "bold", size = 3.8) +
  scale_fill_manual(
    values = colorRampPalette(brewer.pal(8, "Set3"))(nrow(spec_ret)),
    guide = "none") +
  scale_x_discrete(labels = function(x) gsub("_", " ", x)) +
  scale_y_continuous(limits = c(0, max(spec_ret$pct) * 1.35)) +
  labs(title = "Pourcentage de retards chirurgicaux par spécialité",
       subtitle = "% calculé sur l'ensemble des patients de chaque spécialité",
       x = "Spécialité chirurgicale",
       y = "% de patients avec retard") +
  theme_jeune +
  theme(axis.text.x = element_text(angle = 30, hjust = 1))
save_fig(p_spec_ret, "R17_retard_specialite.png", w = 12, h = 7)

# ── 5.2 Tests statistiques ───────────────────────────────────────────────────
cat("\n── Tests statistiques ──\n")

# Test de Mann-Whitney : durée solide selon le sexe
sol_h <- df %>% filter(sexe == "Masculin", !is.na(duree_solide_h)) %>%
         pull(duree_solide_h)
sol_f <- df %>% filter(sexe == "Feminin",  !is.na(duree_solide_h)) %>%
         pull(duree_solide_h)
if (length(sol_h) > 1 & length(sol_f) > 1) {
  w_test <- wilcox.test(sol_h, sol_f, alternative = "two.sided")
  cat(sprintf("  Sexe (H vs F) — Wilcoxon W=%.1f, p=%.4f\n",
              w_test$statistic, w_test$p.value))
  cat(sprintf("    Médianes — H: %.1fh | F: %.1fh\n",
              median(sol_h), median(sol_f)))
}

# Test de Kruskal-Wallis : durée solide selon spécialité
spec_groups <- df %>%
  filter(specialite != "NR", !is.na(duree_solide_h)) %>%
  group_by(specialite) %>% filter(n() >= 3) %>% ungroup()
if (n_distinct(spec_groups$specialite) >= 2) {
  kw <- kruskal.test(duree_solide_h ~ specialite, data = spec_groups)
  cat(sprintf("  Spécialité — Kruskal-Wallis H=%.2f, df=%d, p=%.4f\n",
              kw$statistic, kw$parameter, kw$p.value))
}

# Test de Mann-Whitney : durée solide selon présence de retard
sol_ret <- df %>% filter(retard_chirurgie == "OUI", !is.na(duree_solide_h)) %>%
           pull(duree_solide_h)
sol_nor <- df %>% filter(retard_chirurgie == "NON", !is.na(duree_solide_h)) %>%
           pull(duree_solide_h)
if (length(sol_ret) > 1 & length(sol_nor) > 1) {
  w2 <- wilcox.test(sol_ret, sol_nor, alternative = "two.sided")
  cat(sprintf("  Retard (oui vs non) — Wilcoxon W=%.1f, p=%.4f\n",
              w2$statistic, w2$p.value))
  cat(sprintf("    Médianes — Avec retard: %.1fh | Sans retard: %.1fh\n",
              median(sol_ret), median(sol_nor)))
}

# ── 5.3 Violin plot : jeûne solide selon retard ───────────────────────────────
df_ret_sol <- df %>%
  filter(retard_chirurgie %in% c("OUI", "NON"),
         !is.na(duree_solide_h))

p_violin <- ggplot(df_ret_sol,
                   aes(x = retard_chirurgie, y = duree_solide_h,
                       fill = retard_chirurgie)) +
  geom_violin(trim = TRUE, alpha = 0.7, color = "grey30") +
  geom_boxplot(width = 0.15, outlier.size = 1.5,
               outlier.color = "red", fill = "white",
               color = "grey30", alpha = 0.9) +
  geom_hline(yintercept = SEUIL_SOLIDE,
             color = "red", linetype = "dashed", linewidth = 1.2) +
  annotate("text", x = 0.5, y = SEUIL_SOLIDE + 0.15,
           label = paste0("Recommandation : ", SEUIL_SOLIDE, "h"),
           color = "red", hjust = 0, fontface = "bold", size = 3.5) +
  scale_fill_manual(
    values = c("OUI" = PALETTE[2], "NON" = PALETTE[7]),
    name = "Retard chirurgical") +
  labs(title = "Durée du jeûne solide selon le retard chirurgical",
       subtitle = sprintf("Wilcoxon p = %.4f", w2$p.value),
       x = "Retard chirurgical", y = "Durée du jeûne solide (heures)") +
  theme_jeune
save_fig(p_violin, "R18_violin_jeune_retard.png", w = 9, h = 7)

# ── 5.4 Comparaison observé vs recommandé ─────────────────────────────────────
comp_df <- data.frame(
  jeune  = rep(c("Solide", "Liquide"), each = 2),
  source = rep(c("Recommandation max\n(SFAR/ASA)", "Observé\n(moyenne ± ET)"), 2),
  valeur = c(SEUIL_SOLIDE, mean(sol), SEUIL_LIQUIDE, mean(liq)),
  et     = c(0, sd(sol), 0, sd(liq)))

p_comp <- ggplot(comp_df, aes(x = jeune, y = valeur, fill = source)) +
  geom_col(position = "dodge", color = "white",
           linewidth = 0.8, width = 0.55) +
  geom_errorbar(aes(ymin = valeur - et, ymax = valeur + et),
                position = position_dodge(0.55),
                width = 0.12, linewidth = 1, color = "grey40") +
  geom_text(aes(label = sprintf("%.1fh", valeur)),
            position = position_dodge(0.55),
            vjust = -0.5, fontface = "bold", size = 4.5) +
  scale_fill_manual(
    values = c("Recommandation max\n(SFAR/ASA)" = "#2ecc71",
               "Observé\n(moyenne ± ET)" = "#e74c3c"),
    name = NULL) +
  scale_y_continuous(limits = c(0, max(comp_df$valeur + comp_df$et) + 2)) +
  labs(title = "Jeûne préopératoire observé vs recommandations",
       subtitle = "SFAR 2015 / ASA 2017 | barres d'erreur = ± écart-type",
       x = "Type de jeûne", y = "Durée (heures)") +
  theme_jeune
save_fig(p_comp, "R19_comparaison_recommandations.png", w = 9, h = 7)

# ── 5.5 Heatmap jeûne solide × spécialité × anesthésie ───────────────────────
heat_df <- df %>%
  filter(specialite != "NR", type_anesthesie != "NR",
         !is.na(duree_solide_h)) %>%
  group_by(specialite, type_anesthesie) %>%
  summarise(moy = round(mean(duree_solide_h), 1), n = n(),
            .groups = "drop") %>%
  filter(n >= 2)

p_heat <- ggplot(heat_df,
                 aes(x = type_anesthesie, y = specialite,
                     fill = moy)) +
  geom_tile(color = "white", linewidth = 0.8) +
  geom_text(aes(label = paste0(moy, "h\n(n=", n, ")")),
            size = 3.2, fontface = "bold",
            color = ifelse(heat_df$moy > 10, "white", "black")) +
  scale_fill_viridis_c(option = "YlOrRd", direction = 1,
                       name = "Durée moy.\n(h)") +
  scale_x_discrete(labels = function(x) gsub("_", " + ", x)) +
  scale_y_discrete(labels = function(x) gsub("_", " ", x)) +
  labs(title = "Durée moyenne de jeûne solide (h)\npar spécialité et type d'anesthésie",
       x = "Type d'anesthésie",
       y = "Spécialité chirurgicale") +
  theme_jeune +
  theme(axis.text.x = element_text(angle = 30, hjust = 1))
save_fig(p_heat, "R20_heatmap.png", w = 13, h = 8)


# =============================================================================
# 6. TABLEAU RÉCAPITULATIF FINAL
# =============================================================================
cat("\n", strrep("=", 70), "\n")
cat("  TABLEAU RÉCAPITULATIF FINAL\n")
cat(strrep("=", 70), "\n\n")

# Construire un tableau synthétique
tab_recap <- data.frame(
  Indicateur = c(
    "Effectif total (N)",
    "Sexe masculin (%)",
    "Âge moyen ± ET (ans)",
    "Âge médian [Q1–Q3] (ans)",
    "IMC moyen ± ET (kg/m²)",
    "Surpoids + Obésité (IMC > 24,99)",
    "ASA I (%)",
    "ASA II (%)",
    "Durée jeûne SOLIDE — moyenne ± ET (h)",
    "Durée jeûne SOLIDE — médiane [Q1–Q3] (h)",
    "Durée jeûne LIQUIDE — moyenne ± ET (h)",
    sprintf("Solide > %.0fh (recom. max)", SEUIL_SOLIDE),
    "Solide > 9h",
    sprintf("Liquide > %.0fh (recom. max)", SEUIL_LIQUIDE),
    "Instructions reçues (OUI %)",
    "Patients ayant compris (OUI %)",
    "Retard chirurgical (OUI %)",
    "Durée retard — moy. ± ET (h)"),
  Valeur = c(
    as.character(N),
    sprintf("%d (%.1f%%)", sum(df$sexe == "Masculin", na.rm=TRUE),
            mean(df$sexe == "Masculin", na.rm=TRUE)*100),
    sprintf("%.1f ± %.1f", mean(df$age, na.rm=TRUE), sd(df$age, na.rm=TRUE)),
    sprintf("%.0f [%.0f–%.0f]", median(df$age, na.rm=TRUE),
            quantile(df$age, 0.25, na.rm=TRUE),
            quantile(df$age, 0.75, na.rm=TRUE)),
    sprintf("%.1f ± %.1f (n=%d)", mean(df$imc, na.rm=TRUE),
            sd(df$imc, na.rm=TRUE), sum(!is.na(df$imc))),
    sprintf("%.0f (%.1f%%)", sum(df$imc > 24.99, na.rm=TRUE),
            mean(df$imc > 24.99, na.rm=TRUE)*100),
    sprintf("%d (%.1f%%)", sum(df$score_asa == "ASA_I", na.rm=TRUE),
            mean(df$score_asa == "ASA_I", na.rm=TRUE)*100),
    sprintf("%d (%.1f%%)", sum(df$score_asa == "ASA_II", na.rm=TRUE),
            mean(df$score_asa == "ASA_II", na.rm=TRUE)*100),
    sprintf("%.2f ± %.2f", mean(sol), sd(sol)),
    sprintf("%.1f [%.1f–%.1f]", median(sol),
            quantile(sol, 0.25), quantile(sol, 0.75)),
    sprintf("%.2f ± %.2f", mean(liq), sd(liq)),
    sprintf("%d/%d (%.1f%%)", sum(sol > SEUIL_SOLIDE),
            length(sol), mean(sol > SEUIL_SOLIDE)*100),
    sprintf("%d/%d (%.1f%%)", sum(sol > 9),
            length(sol), mean(sol > 9)*100),
    sprintf("%d/%d (%.1f%%)", sum(liq > SEUIL_LIQUIDE),
            length(liq), mean(liq > SEUIL_LIQUIDE)*100),
    sprintf("%d (%.1f%%)", sum(df$instructions_recues == "OUI", na.rm=TRUE),
            mean(df$instructions_recues == "OUI", na.rm=TRUE)*100),
    sprintf("%d (%.1f%%)", sum(df$patient_compris == "OUI", na.rm=TRUE),
            mean(df$patient_compris == "OUI", na.rm=TRUE)*100),
    sprintf("%d (%.1f%%)", n_ret, pct_ret),
    sprintf("%.1f ± %.1f", mean(ret_valid$duree_retard_h, na.rm=TRUE),
            sd(ret_valid$duree_retard_h, na.rm=TRUE))))

# Affichage en console
cat(sprintf("%-55s %s\n", "Indicateur", "Valeur"))
cat(strrep("-", 90), "\n")
for (i in 1:nrow(tab_recap)) {
  cat(sprintf("%-55s %s\n", tab_recap$Indicateur[i], tab_recap$Valeur[i]))
}

cat(sprintf("\n  ✓ ANALYSE R TERMINÉE — %d figures dans : %s\n",
            length(list.files(OUTPUT_DIR)), OUTPUT_DIR))
