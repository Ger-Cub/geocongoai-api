# 🌍 GeoCongo AI API - Documentation

API de pointe pour l'analyse géologique de la RDC utilisant l'IA (Prithvi-EO-2.0, SAM 2) et PyQGIS.

## 🚀 Utilisation Rapide

L'API est accessible via l'URL fournie par Cloud Run.

### 🔐 Authentification

Toutes les requêtes doivent inclure la clé API dans le header :
`X-API-Key: test_key_geocongo`

### 📍 Points d'entrée (Endpoints)

#### 1. Analyse Géologique

**POST** `/analyze`

**Exemple de corps de requête :**

```json
{
  "bbox": [28.8, -2.5, 28.9, -2.4],
  "analysis_type": "failles",
  "crs": "EPSG:4326"
}
```

* **analysis_type** possible : `failles`, `mines`, `minéraux`.

#### 2. État du système

**GET** `/health` : Vérifie l'état des modèles et de QGIS.

#### 3. Consulter les Résultats

**GET** `/results`

Permet de récupérer les résultats d'analyses déjà stockés en base de données.

**Paramètres de requête (optionnels) :**
* `analysis_type`: Filtre par type d'analyse (ex: `failles`).
* `bbox`: Filtre par zone géographique au format `minx,miny,maxx,maxy` (ex: `28.8,-2.5,28.9,-2.4`).

## 🛠️ Exemples de commandes Client

### Lancer une analyse

```bash
curl -X POST https://[YOUR-CLOUD-RUN-URL]/analyze \
     -H "Content-Type: application/json" \
     -H "X-API-Key: test_key_geocongo" \
     -d '{
           "bbox": [28.8, -2.5, 28.9, -2.4],
           "analysis_type": "failles"
         }'
```

---

## 🏗️ Architecture Technique

- **Backend** : FastAPI / Python 3.10
* **IA** : Segment Anything Model 2 (SAM 2) & Prithvi-EO-V2
* **GIS** : Rasterio, Geopandas & Shapely (Vectorisation pure Python)
* **Infra** : Docker sur Google Cloud Run (GPU support)

## 📁 Structure du Projet

- `/app` : Code source de l'API.
* `/models` : Poids des modèles IA (SAM 2, Prithvi).
* `/scripts` : Outils de déploiement et de configuration.
