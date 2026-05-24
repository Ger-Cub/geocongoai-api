ANALYSIS_TYPES = [
    # Exploration Minière
    {"id": "geological_units", "name": "Cartographie des unités géologiques", "category": "mining", "description": "Segmentation des lithologies par clustering spectral"},
    {"id": "lithology", "name": "Classification lithologique détaillée", "category": "mining", "description": "Identification des types de roches par signatures spectrales"},
    {"id": "hydrothermal_alteration", "name": "Zones d'altération hydrothermale", "category": "mining", "description": "Détection des argiles, oxydes de fer, carbonates (SWIR)"},
    {"id": "mineral_detection", "name": "Détection minérale spécifique", "category": "mining", "description": "Identification de spectres caractéristiques"},
    {"id": "structural_lineaments", "name": "Linéaments et failles", "category": "mining", "description": "Extraction des structures géologiques par gradient PCA"},
    {"id": "mining_sites_monitoring", "name": "Suivi des sites miniers", "category": "mining", "description": "Détection et suivi des exploitations"},
    {"id": "mine_reclamation", "name": "Évaluation de restauration minière", "category": "mining", "description": "Suivi de la réhabilitation après exploitation"},
    
    # Environnement et Catastrophes
    {"id": "landslides", "name": "Détection des glissements de terrain", "category": "disasters", "description": "Cartographie des zones à risque et événements récents"},
    {"id": "flood_mapping", "name": "Cartographie des inondations", "category": "disasters", "description": "Détection des zones inondées en temps réel"},
    {"id": "wildfire_monitoring", "name": "Surveillance des feux de forêt", "category": "disasters", "description": "Détection des brûlés, suivi de régénération"},
    {"id": "post_disaster_damage", "name": "Évaluation des dégâts post-catastrophe", "category": "disasters", "description": "Analyse des impacts après séisme/cyclone"},
    
    # Occupation des Sols
    {"id": "land_cover", "name": "Classification territoriale", "category": "land_use", "description": "Distinction hydrographie, urbain, forêt, agriculture, sols nus"},
    {"id": "crop_classification", "name": "Classification des cultures", "category": "land_use", "description": "Identification des types de cultures agricoles"},
    {"id": "water_bodies", "name": "Surveillance des plans d'eau", "category": "land_use", "description": "Détection des lacs, rivières, réservoirs"},
    
    # Forêts et Climat
    {"id": "deforestation", "name": "Suivi de la déforestation", "category": "climate", "description": "Détection des changements forestiers multi-temporels"},
    {"id": "carbon_monitoring", "name": "Mesure des émissions de carbone", "category": "climate", "description": "Estimation de la biomasse et du carbone stocké"}
]

def get_analysis_config(analysis_id: str):
    return next((a for a in ANALYSIS_TYPES if a["id"] == analysis_id), None)