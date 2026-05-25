ANALYSIS_DESCRIPTIONS = {
    "geological_units": {
        "name": "Cartographie des unités géologiques",
        "description": "Segmentation des lithologies par clustering spectral basé sur les caractéristiques profondes de Prithvi.",
        "methodology": "Clustering Hiérarchique (Ward) sur les caractéristiques extraites par l'IA Prithvi pour diviser l'image en ensembles continus.",
        "outputs": ["GeoJSON", "PNG (PCA RGB)", "CSV superficies", "TIFF classifié"]
    },
    "lithology": {
        "name": "Classification lithologique détaillée",
        "description": "Identification des types de roches par signatures spectrales et classification non supervisée (HDBSCAN).",
        "methodology": "Clustering par densité spatiale (HDBSCAN) sur les caractéristiques Prithvi pour isoler des affleurements rocheux spécifiques en ignorant le bruit.",
        "outputs": ["GeoJSON lithologique", "Heatmap de confiance"]
    },
    "hydrothermal_alteration": {
        "name": "Zones d'altération hydrothermale",
        "description": "Détection des argiles, oxydes de fer, carbonates via indices spectraux (SWIR).",
        "methodology": "Ratio mathématique des bandes Infrarouge (SWIR) ciblant l'absorption spécifique des argiles et oxydes de fer.",
        "outputs": ["GeoJSON des zones altérées", "Carte de probabilité", "Indices spectraux bruts"]
    },
    "mineral_detection": {
        "name": "Détection minérale spécifique",
        "description": "Identification de spectres caractéristiques (or, cuivre, coltan, etc.) par matching spectral.",
        "methodology": "Détection d'anomalies statistiques (Z-score) dans l'espace de représentation de Prithvi pour révéler des signatures atypiques.",
        "outputs": ["GeoJSON des anomalies", "Rapports de détection"]
    },
    "structural_lineaments": {
        "name": "Linéaments et failles",
        "description": "Extraction des structures géologiques par gradient PCA et seuillage Otsu.",
        "methodology": "Réduction de dimension (PCA) des caractéristiques Prithvi suivie d'un filtre de contour (Canny/Sobel) pour repérer les failles tectoniques.",
        "outputs": ["GeoJSON des linéaments", "Diagramme polaire (rose des vents)"]
    },
    "mining_sites_monitoring": {
        "name": "Suivi des sites miniers",
        "description": "Détection et suivi des exploitations, rejets et résidus miniers.",
        "methodology": "Clustering (K-Means) focalisé sur le repérage de signatures anthropiques (sols retournés) distinctes de la nature environnante.",
        "outputs": ["GeoJSON des sites", "Analyse multi-temporelle"]
    },
    "mine_reclamation": {
        "name": "Évaluation de restauration minière",
        "description": "Suivi de la réhabilitation après exploitation via indices de végétation (NDVI).",
        "methodology": "Modélisation continue de l'Indice Végétal (NDVI) avec seuillage pour contrôler scientifiquement la repousse sur les anciennes mines.",
        "outputs": ["GeoJSON zones restaurées", "Indice de réhabilitation"]
    },
    "landslides": {
        "name": "Détection des glissements de terrain",
        "description": "Cartographie des zones à risque par texture, NDVI et analyse de pente.",
        "methodology": "Équation croisant la perte végétale brutale (NDVI), la forte rugosité texturale et le modèle numérique de pente (MNT).",
        "outputs": ["GeoJSON des glissements", "Carte de susceptibilité", "Rasters de pente"]
    },
    "flood_mapping": {
        "name": "Cartographie des inondations",
        "description": "Détection des zones inondées en temps réel via NDWI et seuillage adaptatif.",
        "methodology": "Extraction dynamique via l'Indice d'Eau Normalisé (NDWI) qui isole fortement les propriétés d'absorption de l'eau.",
        "outputs": ["GeoJSON zones inondées", "Carte d'extension", "Profondeur estimée"]
    },
    "wildfire_monitoring": {
        "name": "Surveillance des feux de forêt",
        "description": "Détection des zones brûlées et suivi de régénération via dNBR.",
        "methodology": "Ciblage des résidus de carbone calcinés via le Normalized Burn Ratio (NBR) mesuré dans les spectres infrarouges lointains.",
        "outputs": ["GeoJSON des brûlés", "Sévérité des brûlés (dNBR)"]
    },
    "post_disaster_damage": {
        "name": "Évaluation des dégâts post-catastrophe",
        "description": "Analyse des impactes après séisme ou cyclone par détection de changements.",
        "methodology": "Calcul de la variance spatiale locale sur les embeddings Prithvi IA pour détecter le chaos structural laissé par un sinistre.",
        "outputs": ["GeoJSON zones affectées", "Niveau de sévérité"]
    },
    "land_cover": {
        "name": "Classification territoriale (LULC)",
        "description": "Distinction hydrographie, urbain, forêt, agriculture, sols nus via Random Forest sur features Prithvi.",
        "methodology": "Apprentissage non supervisé classant naturellement les descripteurs contextuels Prithvi en macro-catégories (eau, forêt, urbain, etc.).",
        "outputs": ["GeoJSON par classe", "Carte PNG", "Statistiques CSV", "TIFF classifié"]
    },
    "crop_classification": {
        "name": "Classification des cultures",
        "description": "Identification des types de cultures agricoles via indices multi-temporels.",
        "methodology": "Croisement multi-indices (NDVI et EVI) corrigeant les artéfacts atmosphériques pour différencier les typologies de canopées.",
        "outputs": ["GeoJSON par type de culture", "Surfaces cultivées"]
    },
    "water_bodies": {
        "name": "Surveillance des plans d'eau",
        "description": "Détection des lacs, rivières et réservoirs via MNDWI et segmentation par contours actifs.",
        "methodology": "Utilisation du Modified NDWI avec la bande SWIR pour annuler systématiquement les faux positifs liés aux ombres du relief et des bâtiments.",
        "outputs": ["GeoJSON des plans d'eau", "Carte de profondeur estimée"]
    },
    "deforestation": {
        "name": "Suivi de la déforestation",
        "description": "Détection des changements forestiers multi-temporels via différence de NDVI.",
        "methodology": "Co-détection d'une baisse franche de chlorophylle (NDVI) et d'une déviation anormale relevée par le réseau de neurones Prithvi.",
        "outputs": ["GeoJSON des zones déforestées", "Taux de déforestation annuel"]
    },
    "carbon_monitoring": {
        "name": "Mesure des émissions de carbone",
        "description": "Estimation de la biomasse et du carbone stocké par allométrie NDVI.",
        "methodology": "Modélisation allométrique traduisant la densité foliaire (NDVI) en estimations spatialisées de volume de biomasse et tonnage de carbone.",
        "outputs": ["Raster de carbone (t/ha)", "GeoJSON des stocks"]
    }
}
