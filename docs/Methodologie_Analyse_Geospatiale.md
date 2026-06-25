# Méthodologie d'Analyse de GeoCongo AI

Ce document explique les fondements scientifiques et algorithmiques derrière les 16 types d'analyse proposés par l'API GeoCongo AI regroupée en quatre catégories (Exploration Minière et analyse géologique, Environnement et Catastrophes, Occupation des Sols, Forêts et Climat).

L'objectif de GeoCongo AI est de faciliter l'accès, le traitement et l'interprétation des données géospatiales et géoscientifiques de la République Démocratique du Congo (RDC) grâce à la combinaison de la télédétection, l'intelligence artificielle et des bases de données collaboratives. Pour ce faire, nous exploitons la puissance des **fondations models d'Intelligence Artificielle (Prithvi EO v2 de NASA-IBM)** ainsi que des **indices mathématiques spectraux éprouvés** pour faire des analyses géospatiales. Ces résultats sont ensuite discutés et confrontés aux travaux de recherches existants et aux données de terrain grâce à une architecture d'intelligence artificielle **RAG (Retrieval Augmented Generation)** qui permet d'interroger par recherche sémantique des milliers de thèses, rapports, cartes, collections d'échantillons des roches, données de terrain, et autres archives géo-scientifiques. Pour rendre ces fonctionnalités accessibles à tous les utilisateurs, GeoCongo AI met en place des **Agents IA (ChatBots)** capables d'exécuter ces requêtes géospatiales, interroger ces bases de données et générer des rapports à travers  des conversations en langage vocal ou textuel et disponibles sur le site web [www.geocongoai.com/chat](https://www.geocongoai.com/chat), WhatsApp et Telegram.

Voici la méthodologie approfondie pour chaque type d'analyse.

---

## 🪨 Exploration Minière et Géologie

### 1. Cartographie des Unités Géologiques (`geological_units`)

* **La Méthode :** Clustering Hiérarchique (Méthode de Ward) sur les caractéristiques (embeddings) extraites par l'IA Prithvi.
* **Le Principe :** On force l'algorithme à diviser *toute* l'image satellite en grands ensembles cohérents (ex: 8 clusters). L'IA regroupe les pixels ayant une texture et une signature spatiale similaire en forçant une continuité territoriale.
* **L'Objectif :** Créer une carte géomorphologique ou structurale de base (bassin sédimentaire vs socle granitique).

### 2. Classification Lithologique (`lithology`)

* **La Méthode :** Clustering par densité spatiale (HDBSCAN) sur les caractéristiques Prithvi.
* **Le Principe :** Contrairement aux unités géologiques, HDBSCAN ne force pas tous les pixels dans une classe. Il cherche des "noyaux ultra-denses" qui ont exactement la même signature, et considère le reste comme du "bruit" (valeur -1).
* **L'Objectif :** Identifier avec une haute certitude des affleurements de roches spécifiques (ex: basalte pur, granite nu), tout en ignorant la végétation, l'eau ou les sols trop mixtes.

### 3. Altération Hydrothermale (`hydrothermal_alteration`)

* **La Méthode :** Ratio mathématique des bandes Infrarouge (SWIR).
* **Le Principe :** Les fluides géothermiques remontant à la surface "cuisent" la roche, favorisant l'apparition d'**argiles** et d'**oxydes de fer**. Ces minéraux d'altération absorbent de manière spécifique l'infrarouge à ondes courtes (SWIR). L'algorithme calcule un indice combiné d'argile et de fer.
* **L'Objectif :** Détecter la surface altérée permettant de cibler les gisements minéralisés sous-jacents (or, cuivre).

### 4. Détection Minérale Spécifique (`mineral_detection`)

* **La Méthode :** Détection d'anomalies statistiques (Z-score) dans l'espace de représentation géologique de Prithvi.
* **Le Principe :** Le système cherche les pixels qui s'éloignent considérablement de la norme géologique locale (statistiquement aberrants).
* **L'Objectif :** Dénicher des gisements minéraux atypiques affleurants sans avoir besoin de connaître a priori leur signature spectrale spécifique.

### 5. Linéaments et Failles (`structural_lineaments`)

* **La Méthode :** Réduction de dimension (PCA) suivie d'un filtre de détection de contours (Sobel/Canny).
* **Le Principe :** L'image est d'abord compressée. Les algorithmes de vision par ordinateur repèrent ensuite des changements brusques, fins et rectilignes (ex: limite abrupte d'humidité de part et d'autre d'une ligne).
* **L'Objectif :** Cartographier les failles tectoniques, qui agissent souvent comme des couloirs de circulation pour les fluides chargés de minerais (coltan, cassitérite).

### 6. Suivi des Sites Miniers (`mining_sites_monitoring`)

* **La Méthode :** Clustering (K-Means) focalisé sur le repérage de signatures anthropiques artificielles.
* **Le Principe :** L'extraction minière détruit la structure "naturelle" du sol et expose sa sous-couche. L'IA sépare radicalement ce chaos minéral de la forêt ou de la savane environnante.
* **L'Objectif :** Surveiller l'évolution (expansion spatiale) des carrières gérées et détecter l'exploitation minière artisanale illégale naissante.

### 7. Évaluation de Restauration Minière (`mine_reclamation`)

* **La Méthode :** Calcul continu de l'Indice de Végétation par Différence Normalisée (NDVI) combiné à un seuillage de tolérance.
* **Le Principe :** Mesure la densité de chlorophylle (capacité de la plante à absorber le rouge et réfléchir le proche infrarouge) sur une zone historiquement connue comme étant une mine.
* **L'Objectif :** Contrôler, sur le long terme, si les obligations de reboisement et de réparation des écosystèmes sont respectées lors de la fermeture d'une mine.

---

## 🌪️ Catastrophes Naturelles

### 8. Glissements de Terrain (`landslides`)

* **La Méthode :** Équation hybride : NDVI (perte végétale) + Extraction de Texture (rugosité) + Modèle Numérique de Terrain (Pente forte).
* **Le Principe :** Un glissement est caractérisé par un sol mis à nu soudainement, combiné à une texture visuelle très "rugueuse" (débris et roches chaotiques) localisée sur - ou en bas d' - une pente inclinée.
* **L'Objectif :** Assister les secouristes en repérant automatiquement les effondrements de collines suite aux événements de précipitations intenses (fréquent et dramatique au Kivu).

### 9. Cartographie des Inondations (`flood_mapping`)

* **La Méthode :** Indice d'Eau Normalisé (NDWI) avec seuillage dynamique.
* **Le Principe :** Propriété purement physique : les surfaces recouvertes d'eau absorbent fortement l'énergie Proche-Infrarouge (NIR) mais reflètent les longueurs d'onde se situant dans le "vert".
* **L'Objectif :** Délimiter rapidement depuis l'espace la véritable étendue spatiale des crues qui frappent régulièrement le bassin du fleuve Congo.

### 10. Surveillance des Feux de Forêt (`wildfire_monitoring`)

* **La Méthode :** Formule NBR (Normalized Burn Ratio) ciblant les restes des feux.
* **Le Principe :** Le carbone résiduel (les cendres froides et le sol calciné) présente une réflectance unique dans les ondes infrarouges lointaines (SWIR2).
* **L'Objectif :** Cartographier avec précision la superficie des cicatrices d'incendies à travers la forêt primaire ou l'est du Congo.

### 11. Dégâts Post-Catastrophe (`post_disaster_damage`)

* **La Méthode :** Analyse de la Variance spatiale sur les embeddings de l'IA (Prithvi).
* **Le Principe :** Un séisme puissant ou la coulée de lave (ex: Nyiragongo) détruit l'organisation microscopique naturelle ou urbaine d'un paysage. L'IA détecte ce "chaos structural" en calculant la variance mathématique et le désordre spatial local.
* **L'Objectif :** Aider les ONG et l'état à orienter les fonds humanitaires là où les dégâts matériels semblent structurellement les plus prononcés.

---

## 🌿 Occupation des Sols et Environnement

### 12. Classification Territoriale (LULC - `land_cover`)

* **La Méthode :** Intelligence Artificielle non supervisée (K-Means/Random Forest) paramétrée sur l'extraction d'au moins 6 clusters (Urbain, Végétation, Eau, Nucléaire/Sols nus...).
* **Le Principe :** L'algorithme regroupe naturellement les pixels qui "se ressemblent" non seulement en termes de couleur mais aussi de texture et de contexte.
* **L'Objectif :** Créer des cartes de Base Map et monitorer la croissance spectaculaire de l'étalement urbain informel (comme à Kinshasa ou Goma).

### 13. Classification des Cultures Agricoles (`crop_classification`)

* **La Méthode :** Intersection multi-indices : NDVI (quantité) et EVI (qualité de la canopée).
* **Le Principe :** Parfois le NDVI n'est pas suffisant car l'atmosphère de la RDC est très humide et la canopée dense sature vite. L'EVI (Enhanced Vegetation Index) parvient à corriger le bruit atmosphérique et révèle la "géométrie" des cultures qui différencie un champ de maïs d'une plantation de palmiers.
* **L'Objectif :** Assurer la sécurité alimentaire par des projections d'état des futures récoltes ou pour évaluer la santé des sols agricoles.

### 14. Surveillance des Plans d'Eau (`water_bodies`)

* **La Méthode :** L'Indice MNDWI (Modified Normalized Difference Water Index).
* **Le Principe :** C'est une version améliorée du NDWI qui remplace judicieusement la bande NIR par la bande SWIR. Cela permet d'exclure les redoutables erreurs créées par les ombres portées des volcans, nuages ou bâtiments massifs car le SWIR gère bien mieux le bâti.
* **L'Objectif :** Surveiller les variations de niveau des lacs (Lac Kivu, Tanganyika) et le cours de fleuves plus modérés, prévenir le tarissement.

---

## 🌳 Forêts et Climat

### 15. Suivi de la Déforestation (`deforestation`)

* **La Méthode :** Détection d'anomalies bidimensionnelles (Baisse chlorophylle + Forte déviation structurelle par IA).
* **Le Principe :** Déboiser une parcelle engendre fatalement deux changements simultanés dans les données satellites : une chute de NDVI (plus de chlorophylle) couplée à un signal d'alarme de forte déviation remontée par le réseau de neurones. L'association des deux alerte d'une perte forcée par rapport au comportement d'une "normale tropicale".
* **L'Objectif :** Alerter sur les coupes de bois illégales (braconnage sylvicole et charbonniers) au fin fond du bassin du Kivu.

### 16. Mesure des Émissions et Stocks de Carbone (`carbon_monitoring`)

* **La Méthode :** Formules (modèles) allométriques dérivées des indices de densité végétale.
* **Le Principe :** La densité de la canopée captée d'en haut (NDVI élevé constant) est corrélée indirectement au grand volume de biomasse épigée des troncs (quantité de bois en mètres cubes sous le feuillage). Sachant mathématiquement que la masse ligneuse retient 50 % de carbone, on peut spatialiser l'estimation des stocks en les traduisant en T/Carbon/Ha.
* **L'Objectif :** Permettre le montage de projets certifiés d'une initiative REDD+ (Réduction des Émissions issues de la Déforestation et Dégradation des Forêts) et appuyer la souveraineté de la RDC sur le marché international des crédits carbones.
