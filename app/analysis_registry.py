ANALYSIS_TYPES = [
    # Exploration Minière
    {"id": "geological_units", "name": "Cartographie des unités géologiques", "category": "mining", "description": "Segmentation des lithologies par clustering spectral", "methodology": "Clustering Hiérarchique (Ward) sur les caractéristiques extraites par l'IA Prithvi pour diviser l'image en ensembles continus."},
    {"id": "lithology", "name": "Classification lithologique détaillée", "category": "mining", "description": "Identification des types de roches par signatures spectrales", "methodology": "Clustering par densité spatiale (HDBSCAN) sur les caractéristiques Prithvi pour isoler des affleurements rocheux spécifiques en ignorant le bruit."},
    {"id": "hydrothermal_alteration", "name": "Zones d'altération hydrothermale", "category": "mining", "description": "Détection des argiles, oxydes de fer, carbonates (SWIR)", "methodology": "Ratio mathématique des bandes Infrarouge (SWIR) ciblant l'absorption spécifique des argiles et oxydes de fer."},
    {"id": "mineral_detection", "name": "Détection minérale spécifique", "category": "mining", "description": "Identification de spectres caractéristiques", "methodology": "Détection d'anomalies statistiques (Z-score) dans l'espace de représentation de Prithvi pour révéler des signatures atypiques."},
    {"id": "structural_lineaments", "name": "Linéaments et failles", "category": "mining", "description": "Extraction des structures géologiques par gradient PCA", "methodology": "Réduction de dimension (PCA) des caractéristiques Prithvi suivie d'un filtre de contour (Canny/Sobel) pour repérer les failles tectoniques."},
    {"id": "mining_sites_monitoring", "name": "Suivi des sites miniers", "category": "mining", "description": "Détection et suivi des exploitations", "methodology": "Clustering (K-Means) focalisé sur le repérage de signatures anthropiques (sols retournés) distinctes de la nature environnante."},
    {"id": "mine_reclamation", "name": "Évaluation de restauration minière", "category": "mining", "description": "Suivi de la réhabilitation après exploitation", "methodology": "Modélisation continue de l'Indice Végétal (NDVI) avec seuillage pour contrôler scientifiquement la repousse sur les anciennes mines."},
    
    # Environnement et Catastrophes
    {"id": "landslides", "name": "Détection des glissements de terrain", "category": "disasters", "description": "Cartographie des zones à risque et événements récents", "methodology": "Équation croisant la perte végétale brutale (NDVI), la forte rugosité texturale et le modèle numérique de pente (MNT)."},
    {"id": "flood_mapping", "name": "Cartographie des inondations", "category": "disasters", "description": "Détection des zones inondées en temps réel", "methodology": "Extraction dynamique via l'Indice d'Eau Normalisé (NDWI) qui isole fortement les propriétés d'absorption de l'eau."},
    {"id": "wildfire_monitoring", "name": "Surveillance des feux de forêt", "category": "disasters", "description": "Détection des brûlés, suivi de régénération", "methodology": "Ciblage des résidus de carbone calcinés via le Normalized Burn Ratio (NBR) mesuré dans les spectres infrarouges lointains."},
    {"id": "post_disaster_damage", "name": "Évaluation des dégâts post-catastrophe", "category": "disasters", "description": "Analyse des impacts après séisme/cyclone", "methodology": "Calcul de la variance spatiale locale sur les embeddings Prithvi IA pour détecter le chaos structural laissé par un sinistre."},
    
    # Occupation des Sols
    {"id": "land_cover", "name": "Classification territoriale", "category": "land_use", "description": "Distinction hydrographie, urbain, forêt, agriculture, sols nus", "methodology": "Apprentissage non supervisé classant naturellement les descripteurs contextuels Prithvi en macro-catégories (eau, forêt, urbain, etc.)."},
    {"id": "crop_classification", "name": "Classification des cultures", "category": "land_use", "description": "Identification des types de cultures agricoles", "methodology": "Croisement multi-indices (NDVI et EVI) corrigeant les artéfacts atmosphériques pour différencier les typologies de canopées."},
    {"id": "water_bodies", "name": "Surveillance des plans d'eau", "category": "land_use", "description": "Détection des lacs, rivières, réservoirs", "methodology": "Utilisation du Modified NDWI avec la bande SWIR pour annuler systématiquement les faux positifs liés aux ombres du relief et des bâtiments."},
    
    # Forêts et Climat
    {"id": "deforestation", "name": "Suivi de la déforestation", "category": "climate", "description": "Détection des changements forestiers multi-temporels", "methodology": "Co-détection d'une baisse franche de chlorophylle (NDVI) et d'une déviation anormale relevée par le réseau de neurones Prithvi."},
    {"id": "carbon_monitoring", "name": "Mesure des émissions de carbone", "category": "climate", "description": "Estimation de la biomasse et du carbone stocké", "methodology": "Modélisation allométrique traduisant la densité foliaire (NDVI) en estimations spatialisées de volume de biomasse et tonnage de carbone."}
]

def get_analysis_config(analysis_id: str):
    return next((a for a in ANALYSIS_TYPES if a["id"] == analysis_id), None)