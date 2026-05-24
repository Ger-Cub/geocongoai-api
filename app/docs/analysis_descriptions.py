ANALYSIS_DESCRIPTIONS = {
    "geological_units": {
        "name": "Cartographie des unités géologiques",
        "description": "Segmentation des lithologies par clustering spectral basé sur les caractéristiques profondes de Prithvi.",
        "outputs": ["GeoJSON", "PNG (PCA RGB)", "CSV superficies", "TIFF classifié"]
    },
    "lithology": {
        "name": "Classification lithologique détaillée",
        "description": "Identification des types de roches par signatures spectrales et classification non supervisée (HDBSCAN).",
        "outputs": ["GeoJSON lithologique", "Heatmap de confiance"]
    },
    "hydrothermal_alteration": {
        "name": "Zones d'altération hydrothermale",
        "description": "Détection des argiles, oxydes de fer, carbonates via indices spectraux (SWIR).",
        "outputs": ["GeoJSON des zones altérées", "Carte de probabilité", "Indices spectraux bruts"]
    },
    "mineral_detection": {
        "name": "Détection minérale spécifique",
        "description": "Identification de spectres caractéristiques (or, cuivre, coltan, etc.) par matching spectral.",
        "outputs": ["GeoJSON des anomalies", "Rapports de détection"]
    },
    "structural_lineaments": {
        "name": "Linéaments et failles",
        "description": "Extraction des structures géologiques par gradient PCA et seuillage Otsu.",
        "outputs": ["GeoJSON des linéaments", "Diagramme polaire (rose des vents)"]
    },
    "mining_sites_monitoring": {
        "name": "Suivi des sites miniers",
        "description": "Détection et suivi des exploitations, rejets et résidus miniers.",
        "outputs": ["GeoJSON des sites", "Analyse multi-temporelle"]
    },
    "mine_reclamation": {
        "name": "Évaluation de restauration minière",
        "description": "Suivi de la réhabilitation après exploitation via indices de végétation (NDVI).",
        "outputs": ["GeoJSON zones restaurées", "Indice de réhabilitation"]
    },
    "landslides": {
        "name": "Détection des glissements de terrain",
        "description": "Cartographie des zones à risque par texture, NDVI et analyse de pente.",
        "outputs": ["GeoJSON des glissements", "Carte de susceptibilité", "Rasters de pente"]
    },
    "flood_mapping": {
        "name": "Cartographie des inondations",
        "description": "Détection des zones inondées en temps réel via NDWI et seuillage adaptatif.",
        "outputs": ["GeoJSON zones inondées", "Carte d'extension", "Profondeur estimée"]
    },
    "wildfire_monitoring": {
        "name": "Surveillance des feux de forêt",
        "description": "Détection des zones brûlées et suivi de régénération via dNBR.",
        "outputs": ["GeoJSON des brûlés", "Sévérité des brûlés (dNBR)"]
    },
    "post_disaster_damage": {
        "name": "Évaluation des dégâts post-catastrophe",
        "description": "Analyse des impactes après séisme ou cyclone par détection de changements.",
        "outputs": ["GeoJSON zones affectées", "Niveau de sévérité"]
    },
    "land_cover": {
        "name": "Classification territoriale (LULC)",
        "description": "Distinction hydrographie, urbain, forêt, agriculture, sols nus via Random Forest sur features Prithvi.",
        "outputs": ["GeoJSON par classe", "Carte PNG", "Statistiques CSV", "TIFF classifié"]
    },
    "crop_classification": {
        "name": "Classification des cultures",
        "description": "Identification des types de cultures agricoles via indices multi-temporels.",
        "outputs": ["GeoJSON par type de culture", "Surfaces cultivées"]
    },
    "water_bodies": {
        "name": "Surveillance des plans d'eau",
        "description": "Détection des lacs, rivières et réservoirs via MNDWI et segmentation par contours actifs.",
        "outputs": ["GeoJSON des plans d'eau", "Carte de profondeur estimée"]
    },
    "deforestation": {
        "name": "Suivi de la déforestation",
        "description": "Détection des changements forestiers multi-temporels via différence de NDVI.",
        "outputs": ["GeoJSON des zones déforestées", "Taux de déforestation annuel"]
    },
    "carbon_monitoring": {
        "name": "Mesure des émissions de carbone",
        "description": "Estimation de la biomasse et du carbone stocké par allométrie NDVI.",
        "outputs": ["Raster de carbone (t/ha)", "GeoJSON des stocks"]
    }
}
