ANALYSIS_DESCRIPTIONS = {
    "geological_units": {
        "name": "Cartographie des unités géologiques",
        "category": "Exploration Minière et Géologie",
        "description": "Segmentation globale et continue des terrains géologiques par intelligence artificielle.",
        "methodology": {
            "method": "Clustering Hiérarchique (Méthode de Ward) sur les caractéristiques (embeddings) extraites par l'IA Prithvi.",
            "principle": "On force l'algorithme à diviser TOUTE l'image satellite en grands ensembles cohérents (ex: 8 clusters). L'IA regroupe les pixels ayant une texture et une signature spatiale similaire en forçant une continuité territoriale.",
            "objective": "Créer une carte géomorphologique ou structurale de base (bassin sédimentaire vs socle granitique)."
        },
        "outputs": ["GeoJSON (Polygones 벡터isés)", "PNG (Carte PCA RGB)", "CSV (Superficies)", "TIFF (Raster classifié)"]
    },
    "lithology": {
        "name": "Classification lithologique détaillée",
        "category": "Exploration Minière et Géologie",
        "description": "Identification des affleurements de types de roches spécifiques avec exclusion du bruit.",
        "methodology": {
            "method": "Clustering par densité spatiale (HDBSCAN) sur les caractéristiques Prithvi.",
            "principle": "Contrairement aux unités géologiques, HDBSCAN ne force pas tous les pixels dans une classe. Il cherche des noyaux ultra-denses qui ont exactement la même signature, et considère les zones mixtes comme du bruit.",
            "objective": "Identifier avec une haute certitude des affleurements de roches spécifiques (ex: basalte pur), tout en ignorant la végétation ou l'eau."
        },
        "outputs": ["GeoJSON lithologique", "Heatmap de confiance (Raster)"]
    },
    "hydrothermal_alteration": {
        "name": "Zones d'altération hydrothermale",
        "category": "Exploration Minière et Géologie",
        "description": "Cartographie des zones où la chaleur souterraine a altéré la roche (argiles, fer).",
        "methodology": {
            "method": "Ratio mathématique des bandes Infrarouge à ondes courtes (SWIR).",
            "principle": "Les fluides géothermiques cuisent la roche en argiles et oxydes de fer qui absorbent spécifiquement l'infrarouge SWIR. L'algorithme calcule un indice combiné de ces anomalies d'absorption.",
            "objective": "Détecter la surface altérée permettant de cibler les gisements minéralisés sous-jacents (or, cuivre)."
        },
        "outputs": ["GeoJSON des zones altérées", "Carte de probabilité", "Indices spectraux bruts"]
    },
    "mineral_detection": {
        "name": "Détection minérale (Anomalies Statistique)",
        "category": "Exploration Minière et Géologie",
        "description": "Recherche algorithmique de signatures rocheuses statistiquement anormales.",
        "methodology": {
            "method": "Détection d'anomalies statistiques (Z-score) dans l'espace de représentation géologique de Prithvi.",
            "principle": "Le système scanne le relief et isole les pixels qui s'éloignent considérablement de la norme géologique locale (statistiquement aberrants).",
            "objective": "Dénicher des gisements minéraux atypiques affleurants sans avoir besoin de connaître a priori leur signature spectrale spécifique."
        },
        "outputs": ["GeoJSON des anomalies spectales", "Rapport CSV de détection"]
    },
    "structural_lineaments": {
        "name": "Cartographie des Linéaments et failles",
        "category": "Exploration Minière et Géologie",
        "description": "Repérage des macro-structures géologiques (plis et réseaux de failles).",
        "methodology": {
            "method": "Réduction de dimension (PCA) suivie d'un filtre de détection de contours (Algorithmes de Canny et Sobel).",
            "principle": "L'image est d'abord compressée par l'IA. Les algorithmes géométriques repèrent ensuite des changements brusques, fins et rectilignes (ex: limite abrupte d'humidité de part et d'autre d'une ligne).",
            "objective": "Cartographier les failles tectoniques agissant comme des couloirs de circulation pour les fluides chargés de minerais (coltan, or)."
        },
        "outputs": ["GeoJSON (Lignes vectorielles des failles)", "Diagramme polaire (Rose des vents)"]
    },
    "mining_sites_monitoring": {
        "name": "Suivi et détection des sites miniers",
        "category": "Exploration Minière et Géologie",
        "description": "Identification des sols perturbés par l'activité d'extraction artificielle.",
        "methodology": {
            "method": "Machine Learning (K-Means) focalisé sur le repérage de signatures anthropiques.",
            "principle": "L'extraction minière détruit la structure géologique naturelle et expose sa sous-couche en créant un chaos. L'IA sépare radicalement ce chaos minéral de la zone naturelle.",
            "objective": "Surveiller l'évolution (expansion spatiale) des carrières gérées et détecter l'exploitation minière illégale naissante."
        },
        "outputs": ["GeoJSON (Polygones des sites actifs)", "Analyse Raster multi-temporelle"]
    },
    "mine_reclamation": {
        "name": "Évaluation de la restauration minière",
        "category": "Exploration Minière et Environnement",
        "description": "Mesure du retour au vert des anciennes carrières et mines désaffectées.",
        "methodology": {
            "method": "Calcul continu de l'Indice de Végétation Normalisé (NDVI) combiné à un seuillage de tolérance.",
            "principle": "Mesure la densité de chlorophylle sur une zone historiquement connue (et géographée) comme étant un ancien site d'extraction.",
            "objective": "Contrôler sur le long terme si les obligations de reboisement et de réparation des écosystèmes sont respectées pour valider la fermeture d'une mine."
        },
        "outputs": ["GeoJSON des zones restaurées correctement", "Indice global de réhabilitation (0 à 100%)"]
    },
    "landslides": {
        "name": "Détection des glissements de terrain",
        "category": "Catastrophes Naturelles",
        "description": "Cartographie rapide des effondrements de terrain (landslides/mudslides).",
        "methodology": {
            "method": "Équation hybride : Chute du NDVI + Extraction de Texture (rugosité) + Modèle Numérique de Terrain (SRTM Pente).",
            "principle": "Un glissement = sol mis à nu soudainement (baisse chlorophylle), combiné à une texture visuelle très rugueuse (débris), systématiquement localisée sur (ou sous) une pente inclinée.",
            "objective": "Assister les secours en repérant automatiquement les effondrements de collines suite aux violentes intempéries."
        },
        "outputs": ["GeoJSON des glissements confirmés", "Carte Raster de susceptibilité géologique", "Couche SRTM des pentes"]
    },
    "flood_mapping": {
        "name": "Cartographie des inondations (Crues)",
        "category": "Catastrophes Naturelles",
        "description": "Délimitation de l'étendue des eaux de crues en débordement.",
        "methodology": {
            "method": "Indice d'Eau Normalisé (NDWI) avec seuillage dynamique.",
            "principle": "Propriété physique stricte : les surfaces recouvertes d'eau absorbent massivement l'énergie Proche-Infrarouge (NIR) mais reflètent le vert. Ce ratio isole infailliblement les fluides liquides.",
            "objective": "Délimiter en temps quasi réel l'étendue spatiale des crues (ex: Fleuve Congo ou rivières du Kivu)."
        },
        "outputs": ["GeoJSON (Polygones de l'eau)", "Carte spatiale d'extension", "Estimation volumétrique/profondeur"]
    },
    "wildfire_monitoring": {
        "name": "Surveillance des feux de forêt",
        "category": "Catastrophes Naturelles",
        "description": "Détection des zones forestières brûlées et de la sévérité du feu.",
        "methodology": {
            "method": "Formule NBR (Normalized Burn Ratio) dédiée au ciblage du carbone brûlé.",
            "principle": "Le sol et la biomasse calcinés présentent une réflectance unique (pic d'absorption) dans les ondes infrarouges lointaines (SWIR2).",
            "objective": "Cartographier avec une haute précision les cicatrices d'incendies et orienter les équipes de garde forestière."
        },
        "outputs": ["GeoJSON des cicatrices brûlées", "Carte dNBR (Sévérité des dommages)"]
    },
    "post_disaster_damage": {
        "name": "Évaluation des dégâts post-catastrophe",
        "category": "Catastrophes Naturelles",
        "description": "Estimation du niveau de destruction massif (Volcans, Séismes, Cyclones).",
        "methodology": {
            "method": "Analyse de la Variance spatiale sur les embeddings du transformeur IA (Prithvi).",
            "principle": "Un séisme ou une coulée de lave détruit l'organisation microscopique naturelle ou urbaine d'un paysage. L'IA repère cette désorganisation géométrique soudaine via un pic de variance locale.",
            "objective": "Aider l'État et l'aide humanitaire internationale à orienter les fonds là où les dégâts matériels mesurés sont les plus absolus."
        },
        "outputs": ["GeoJSON zones sévèrement affectées", "Carte de chaleur des dommages"]
    },
    "land_cover": {
        "name": "Classification territoriale (LULC)",
        "category": "Occupation des Sols",
        "description": "Zonage global de l'hydrologie, tissu urbain, forestier, agricole et minéral.",
        "methodology": {
            "method": "Intelligence Artificielle non supervisée (Algorithme K-Means) configurée pour 6 ou plus macro-clusters.",
            "principle": "Le réseau neuronal regroupe naturellement les pixels qui se ressemblent sémantiquement, non seulement par leur couleur, mais aussi par leur macro-texture et leur contexte de voisinage immédiat.",
            "objective": "Créer des cartes de Base Map (Fonds de carte) fiables et monitorer la croissance ou l'étalement urbain (ex: cartographie de Goma)."
        },
        "outputs": ["GeoJSON classifié multi-catégories", "TIFF RGB", "Tableau CSV (Pourcentage couvert par classe)"]
    },
    "crop_classification": {
        "name": "Classification des cultures agricoles",
        "category": "Occupation des Sols",
        "description": "Isolement des parcelles végétales domestiquées vs végétation sauvage.",
        "methodology": {
            "method": "Intersection multi-indices : NDVI (quantité végétale) + EVI (Indice de Végétation Amélioré).",
            "principle": "Le couvert atmosphérique sature souvent les indices classiques (NDVI). L'EVI corrige le bruit aérosol et révèle la micro-géométrie des plants, permettant de distinguer la canopée d'une forêt primaire d'un champ agricole symétrique.",
            "objective": "Garantir le suivi de la sécurité alimentaire et estimer l'état des sols agricoles face à la sécheresse."
        },
        "outputs": ["GeoJSON par polygone cultivé", "Calcul des Surfaces Net cultivées (Hectares)"]
    },
    "water_bodies": {
        "name": "Surveillance pérenne des plans d'eau",
        "category": "Occupation des Sols",
        "description": "Suivi des rivières pacifiques, réservoirs et lacs de la région.",
        "methodology": {
            "method": "Indice MNDWI (Modified Normalized Difference Water Index) limitant les faux positifs.",
            "principle": "Le MNDWI remplace la bande Proche Infrarouge (NIR) par la bande SWIR. Cela permet d'isoler l'eau sans la confondre avec les grandes ombres noires portées par des gratte-ciels, falaises ou nuages volcaniques.",
            "objective": "Surveiller de près les variations de volume des grands lacs (Lac Kivu, Tanganyika) et alerter sur le tarissement des ressources hydriques."
        },
        "outputs": ["GeoJSON de contour de lac/fleuve", "Estimation de l'évolution des berges"]
    },
    "deforestation": {
        "name": "Suivi granulaire de la déforestation",
        "category": "Forêts et Climat",
        "description": "Alerte de coupe de bois et altération des aires protégées.",
        "methodology": {
            "method": "Détection d'anomalies bidimensionnelles (Perte physique de biomasse croisée avec alerte de structure IA).",
            "principle": "Déboiser engendre obligatoirement la rencontre de deux phénomènes spatiaux : une chute brutale de chlorophylle active ET un signal de forte déviation structurelle remontée par le réseau de neurones par rapport à un dôme forestier classique.",
            "objective": "Combattre l'exploitation de charbon de bois illégale (braconnage sylvicole) profondément à l'intérieur du gigantesque bassin du Congo."
        },
        "outputs": ["GeoJSON d'Alerte Déforestation (Localisation GPS)", "Taux annuel de dégradation"]
    },
    "carbon_monitoring": {
        "name": "Mesure des Stocks de Carbone (Projets REDD+)",
        "category": "Forêts et Climat",
        "description": "Calcul du tonnage de carbone piégé dans la forêt primaire ou secondaire.",
        "methodology": {
            "method": "Formules d'allométrie forestière dérivées de la corrélation foliaire.",
            "principle": "Il existe une loi naturelle validant que la forte densité de la canopée (indice NDVI haut très resserré) est proportionnelle au très large volume de biomasse épigée des troncs d'arbres. Le bois étant constitué à de ~50% de carbone brut, on extrapole quantitativement ce volume en puit de carbone.",
            "objective": "Appuyer la mise en place de zones REDD+ certifiées et faciliter l'accès souverain au marché de la finance/comptabilité carbone internationale."
        },
        "outputs": ["Raster de densité du Carbone (t/ha)", "Bilan total comptabilisé en Tonnes via GeoJSON"]
    }
}
