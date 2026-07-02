# Dashboard HQVS — Sète Proximités

> Projet Sorbonne × Chaire ETI — Analyse de la Haute Qualité de Vie Sociétale de la ville de Sète (Hérault, France)

---

## Présentation

Ce dashboard Streamlit permet d'explorer et d'analyser l'accessibilité aux équipements urbains pour les **9 910 bâtiments de Sète**, selon la méthode **HQVS (Haute Qualité de Vie Sociétale)**. Il s'appuie sur les données de la **Base Permanente des Équipements INSEE (BPE 2024)** et les isochrones calculées par le serveur de routing Valhalla de la Sorbonne.

L'outil est conçu pour deux publics :
- **Étudiants et chercheurs** : exploration méthodologique, comparaison des modes de transport, analyse de la qualité des données
- **Élus et conseils de quartier** : lecture simple du score HQVS, identification des zones sous-desservies

---

## Les 6 fonctions sociales HQVS

| Fonction | Icône | Exemples d'équipements |
|----------|-------|------------------------|
| **Habiter** | 🏠 | Mairie, services sociaux, déchetterie |
| **Travailler** | 💼 | France Services, pôle emploi, espaces de coworking |
| **S'approvisionner** | 🛒 | Supérette, marché, boulangerie, pharmacie |
| **Être en forme** | 💪 | Centre de santé, salle de sport, piscine |
| **Apprendre** | 📚 | École, collège, bibliothèque, médiathèque |
| **S'épanouir** | 🎭 | Théâtre, musée, espace culturel, association |

Chaque bâtiment reçoit une note de 0 à 1 par fonction (1 = au moins un équipement accessible dans le rayon isochrone). Le **score HQVS** est la moyenne de ces 6 notes × 10.

---

## Score HQVS — deux méthodes

### Score arithmétique (proxy rapide)
```
Score = moyenne(6 fonctions) × 10  →  [0, 10]
```
Résultats observés sur Sète :
- 🚶 Marche 15 min : **1,7 / 10** (beaucoup de bâtiments sans accès piéton)
- 🚴 Vélo 15 min : **10,0 / 10** (tous les bâtiments atteignent les 6 fonctions)
- 🚗 Voiture 15 min : **10,0 / 10**

### Score Monterey (méthode Université de Monterey — pondéré)
Pipeline en 3 étapes :
1. `ln(x + 1)` + normalisation robuste P5/P95 → [0, 100]
2. Même pipeline appliqué aux scores catégorie
3. Moyenne géométrique : `(∏ (cat_i + 0.1))^(1/6)` remise à l'échelle [0, 10]

La moyenne géométrique pénalise les bâtiments ayant **zéro** sur une fonction (un seul manque fait chuter le score), contrairement à la moyenne arithmétique.

---

## Les 8 onglets du dashboard

| # | Onglet | Contenu |
|---|--------|---------|
| 1 | **Vue principale** | Carte interactive, radar HQVS, répartition par niveau de proximité, tableau des équipements |
| 2 | **Analyse fonctions** | Isochrones par fonction sociale, camembert, top 20 types d'équipements |
| 3 | **Score pondéré** | Comparaison score arithmétique vs Monterey, radar comparatif, détail par fonction |
| 4 | **Modes de transport** | Comparaison automatique Marche / Vélo / Voiture, scores côte à côte, import données personnalisées |
| 5 | **Population** | Données Filosofi INSEE 200 m — densité, pyramide des âges, types de logements, revenus médians |
| 6 | **Grille 50 m** | 8 282 carreaux 50×50 m — diagnostic spatial fin intra-quartier |
| 7 | **Qualité données** | Taux de couverture BPE, types non classés, correspondance avec bpe24key_classification.csv |
| 8 | **Documentation** | Glossaire (HQVS, IRIS, carreau, isochrone), méthodologie, calendrier, sources |

---

## Modes de transport

Le dashboard charge automatiquement les données de la Sorbonne si les fichiers sont présents dans `data/`. Sinon, il génère une approximation géométrique (cercles buffer).

| Mode | Rayon (approx.) | Source |
|------|----------------|--------|
| 🚶 Marche 15 min | 1 250 m | Isochrones Valhalla (BDTopo) |
| 🚴 Vélo 15 min | 3 750 m | Isochrones Valhalla (OSM) |
| 🚗 Voiture 15 min | 10 000 m | Isochrones Valhalla (OSM) |

---

## Architecture des fichiers

```
hqvs_dashboard_final/
├── app.py                                      # Application Streamlit principale (~1 500 lignes)
├── requirements.txt                            # Dépendances Python
├── audit_HQVS.pdf                              # Audit interne du dashboard
├── comparaison_dashboard_vs_sorbonne.pdf       # Comparaison avec l'ancien site Sorbonne
├── data_audit.py                               # Script d'audit des données
└── data/                                       # Données GeoJSON (non versionnées)
    ├── isochrones_walking_15min.geojson          # 16 785 équipements · marche · 116 Mo
    ├── isochrones_cycling_15min.geojson          # 9 888 bâtiments · vélo · 11 Mo
    ├── isochrones_car_15min.geojson              # 9 888 bâtiments · voiture · 11 Mo
    ├── filosofi_200m.geojson                     # 701 carreaux Filosofi INSEE 200 m
    ├── filosofi_50m.geojson                      # Grille Filosofi 50 m
    ├── grille_50m.geojson                        # 8 282 carreaux 50×50 m
    └── bpe24key_classification.csv               # 241 types d'équipements classifiés
```

> **Note :** Les fichiers `data/` ne sont pas versionnés (trop lourds pour GitHub). Ils sont disponibles via le serveur Martin de la Sorbonne : `https://martin-sete-etudiants.cartosphere.app`

---

## Installation et lancement

### Prérequis
- Python 3.11+
- pip

### Installation
```bash
git clone https://github.com/Ethan941/Prototype_Sorbonne-_Chaire_ETI.git
cd Prototype_Sorbonne-_Chaire_ETI

python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### Lancement
```bash
streamlit run app.py
```

Ouvre automatiquement `http://localhost:8501` dans le navigateur.

### Données
Placer les fichiers GeoJSON dans le dossier `data/` avant de lancer. Sans ces fichiers, le dashboard fonctionne en mode dégradé (approximations géométriques pour vélo/voiture, onglets Population et Grille 50 m désactivés).

---

## Fonctions Python principales

| Fonction | Rôle |
|----------|------|
| `load_gdf()` | Charge les isochrones marche (cache Streamlit) |
| `adapt_od_gdf(gdf)` | Convertit le format OD (comptages `nb_xxx`) vers le format booléen du dashboard |
| `approx_isochrones(gdf, mode)` | Génère des buffers circulaires si les données OD sont absentes |
| `apply_filters(gdf, fonction, niveau, prioritaire)` | Filtre le GeoDataFrame selon les paramètres de la sidebar |
| `compute_score(df)` | Score arithmétique HQVS (moyenne × 10) |
| `compute_weighted_score(df)` | Score Monterey (géométrique pondéré) |
| `fig_radar(df)` | Radar hexagonal avec valeurs affichées sur chaque point |
| `fig_map(df)` | Carte Plotly Mapbox colorée par fonction sociale |
| `_load_od_mode(mode)` | Charge les isochrones vélo ou voiture (cache Streamlit) |
| `load_filosofi()` | Charge les données Filosofi INSEE 200 m |
| `load_grille_50m()` | Charge la grille 50×50 m |

---

## Sources des données

| Source | Contenu |
|--------|---------|
| **INSEE BPE 2024** | 16 724 équipements (base permanente des équipements) |
| **INSEE Filosofi** | Carreaux 200 m et 50 m — revenus, population, logements |
| **BDTopo IGN** | Réseau routier piéton pour routing isochrone |
| **OpenStreetMap** | Réseau routier vélo/voiture pour routing isochrone |
| **Valhalla (Sorbonne)** | Serveur de routing pour calcul des isochrones |
| **Martin tile server** | Exposition des tables PostGIS en tuiles vectorielles MVT |

---

## Comparaison avec l'ancien site Sorbonne

Une analyse complète est disponible dans `comparaison_dashboard_vs_sorbonne.pdf`.

**Ce que ce dashboard apporte en plus :**
- Comparaison automatique des 3 modes de transport (marche / vélo / voiture) avec scores côte à côte
- Score Monterey (géométrique pondéré) en plus du score arithmétique
- Données Filosofi INSEE intégrées (pyramide des âges, revenus médians)
- Grille 50 m pour le diagnostic spatial fin intra-quartier
- Onglet qualité des données BPE (couverture, types non classés)
- Documentation et glossaire intégrés en français
- Navigation simplifiée : 8 onglets vs 15 pages dans l'ancien site

**Bugs de l'ancien site évités ici :**
- Cache Streamlit correctement invalidé (plus de tableau figé sur le 1er quartier sélectionné)
- Zéro message de débogage visible à l'utilisateur final
- Labels en français dans le radar HQVS (pas de fuite de variables internes anglaises)

---

## Contexte académique

Ce projet s'inscrit dans le cadre de la **Chaire ETI (Entreprises, Territoires et Inclusion)** de la Sorbonne. L'objectif est de développer un outil d'aide à la décision pour les collectivités territoriales, permettant d'évaluer l'accessibilité aux équipements urbains et d'identifier les zones de tension en termes de qualité de vie sociétale.

La ville de **Sète** (34 200 habitants, Hérault, France) sert de terrain d'expérimentation.

---

*Projet Sorbonne × Chaire ETI · 2 juillet 2026*
