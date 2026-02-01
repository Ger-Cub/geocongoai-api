# 📖 Guide de Recréation et de Déploiement - API GeoCongo AI

Ce document fournit des instructions complètes pour recréer, configurer et déployer l'API GeoCongo AI à partir de zéro. Il est conçu pour être utilisé par un développeur ou un agent d'intelligence artificielle.

## 1. Vue d'ensemble du Projet

L'API GeoCongo AI est un service de géo-intelligence artificielle conçu pour analyser des images satellites et en extraire des informations géologiques pertinentes pour la République Démocratique du Congo (RDC).

**Fonctionnalités Clés :**
- **Analyse Asynchrone :** Les requêtes d'analyse sont gérées via une file d'attente de tâches pour éviter les timeouts HTTP sur les traitements longs.
- **Modèles d'IA Multiples :** Intègre plusieurs modèles pour différentes analyses :
    - **Prithvi-EO-V2 :** Pour la détection de minéraux et de sites miniers.
    - **SAM 2 (Segment Anything Model) :** Pour la détection de failles géologiques.
    - **SegFormer :** Pour la classification de la couverture terrestre (déforestation, zones urbaines, etc.).
- **Traitement Géospatial :** Utilise PyQGIS pour la vectorisation des résultats de l'IA (conversion de raster en polygones).
- **Persistance des Données :** Stocke les résultats vectorisés dans une base de données PostGIS pour des requêtes spatiales futures.
- **Mise en Cache Intelligente :** Met en cache les images satellites téléchargées pour accélérer les analyses répétées sur les mêmes zones.
- **Déploiement Cloud-Native :** Conçu pour être déployé en tant que conteneur sur des services managés comme Google Cloud Run, avec support GPU.

## 2. Prérequis

- **Python** >= 3.9
- **Docker**
- Un compte sur une plateforme Cloud (GCP, AWS, ou Azure) avec les outils CLI correspondants installés et configurés.
- **Modèles d'IA :** Les modèles doivent être téléchargés et placés dans un bucket de stockage cloud.
    - **Prithvi:** `Prithvi_EO_V2_600M_TL.pt` (disponible sur Hugging Face)
    - **SAM 2:** `sam2_l.pt` (disponible via Ultralytics/Meta)
    - **SegFormer:** `segformer-b0-finetuned-ade-512-512` (disponible sur Hugging Face)

## 3. Structure du Projet

Créez la structure de fichiers et de dossiers suivante :

```
/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Point d'entrée de l'API FastAPI
│   ├── core/
│   │   ├── __init__.py
│   │   └── security.py         # Gestion de la clé d'API
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py         # Configuration de la connexion à la base de données
│   │   └── models.py           # Modèles de données SQLAlchemy/GeoAlchemy2
│   └── services/
│       ├── __init__.py
│       ├── ai_service.py       # Logique d'inférence des modèles d'IA
│       ├── geo_service.py      # Logique de traitement géospatial (QGIS)
│       ├── postgis_service.py  # Interaction avec la base de données PostGIS
│       ├── cloud_tasks_service.py # Gestion des tâches asynchrones (spécifique à GCP)
│       └── landcover_colormap.json # Palette de couleurs pour la classification
├── scripts/
│   └── deploy.sh               # Script de déploiement pour GCP
├── Dockerfile
├── requirements.txt
└── RECREATION_GUIDE.md         # Ce fichier
```

## 4. Code Source Complet

Voici le contenu de chaque fichier nécessaire pour construire l'application.

---

### `requirements.txt`

```txt
fastapi
uvicorn[standard]
pydantic
python-dotenv
python-multipart
sqlalchemy
psycopg2-binary
geoalchemy2
transformers
torch
ultralytics
rasterio
odc-stac
pystac-client
matplotlib
Pillow
google-cloud-tasks
google-cloud-storage
```

---

### `Dockerfile`

Ce Dockerfile est optimisé pour installer PyQGIS, ce qui est une étape complexe.

```dockerfile
# Étape 1: Builder avec l'environnement QGIS
FROM ubuntu:22.04 as builder

ENV DEBIAN_FRONTEND=noninteractive

# Installation des dépendances de base et de QGIS
RUN apt-get update && \
    apt-get install -y gnupg software-properties-common wget && \
    wget -qO - https://qgis.org/downloads/qgis-2024.gpg.key | gpg --no-default-keyring --keyring gnupg-ring:/etc/apt/trusted.gpg.d/qgis-archive.gpg --import && \
    chmod 644 /etc/apt/trusted.gpg.d/qgis-archive.gpg && \
    add-apt-repository "deb https://qgis.org/ubuntu $(lsb_release -cs) main" && \
    apt-get update && \
    apt-get install -y \
    qgis-server \
    python3-qgis \
    python3-pip \
    git

# Copier les fichiers de l'application
WORKDIR /app
COPY ./app /app/app
COPY ./requirements.txt /app/

# Installer les dépendances Python
RUN pip3 install --no-cache-dir -r requirements.txt

# Étape 2: Image finale optimisée
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Installation des dépendances d'exécution (beaucoup moins que le builder)
RUN apt-get update && apt-get install -y \
    python3-pip \
    libgdal-dev \
    gdal-bin \
    # Dépendances minimales pour QGIS et PyTorch
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier l'environnement QGIS et les dépendances Python depuis le builder
COPY --from=builder /usr/lib/python3/dist-packages /usr/lib/python3/dist-packages
COPY --from=builder /usr/share/qgis /usr/share/qgis
COPY --from=builder /etc/qgis /etc/qgis
COPY --from=builder /app /app

# Définir les variables d'environnement pour que Python trouve QGIS
ENV PYTHONPATH=/usr/share/qgis/python:/usr/lib/python3/dist-packages:$PYTHONPATH
ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
ENV QGIS_PREFIX_PATH=/usr

# Point d'entrée de l'application
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### Contenu des fichiers `app/**/*.py`

Utilisez le code fourni dans le contexte de la requête originale pour remplir les fichiers suivants :
- `app/main.py`
- `app/core/security.py`
- `app/db/database.py`
- `app/db/models.py`
- `app/services/ai_service.py`
- `app/services/geo_service.py`
- `app/services/postgis_service.py`
- `app/services/cloud_tasks_service.py`
- `app/services/landcover_colormap.json`

*(Note pour l'agent IA : Le code source de ces fichiers est disponible dans le contexte initial de la conversation. Il suffit de les recréer avec le contenu fourni.)*

## 5. Instructions de Déploiement

Cette section détaille comment déployer l'application sur différentes plateformes cloud. Le principe est toujours le même :
1.  **Stocker les modèles d'IA** dans un service de stockage (S3, GCS, Blob Storage).
2.  **Créer une base de données** PostgreSQL avec l'extension PostGIS.
3.  **Construire et pousser l'image Docker** vers un registre de conteneurs (ECR, GCR, ACR).
4.  **Déployer le conteneur** sur un service de calcul (App Runner, Cloud Run, Container Apps), en le connectant au stockage et à la base de données.
5.  **Configurer un système de tâches asynchrones** (SQS/Lambda, Cloud Tasks, Queue Storage/Functions).

### A. Déploiement sur Google Cloud Platform (GCP) - Implémentation de référence

C'est la plateforme pour laquelle le projet est initialement configuré.

1.  **Configuration du Projet :**
    - Créez un projet GCP.
    - Activez les APIs : `Cloud Build`, `Cloud Run`, `Cloud Tasks`, `Cloud Storage`, `Cloud SQL Admin`.

2.  **Stockage des Modèles :**
    - Créez un bucket Cloud Storage (ex: `geocongo-models-bucket`).
    - Uploadez vos modèles (`.pt`, etc.) dans ce bucket, en respectant la structure attendue par `ai_service.py` (`prithvi/`, `sam2/`, `landcover/`).

3.  **Base de Données PostGIS :**
    - Créez une instance Cloud SQL pour PostgreSQL.
    - Connectez-vous à l'instance et exécutez `CREATE EXTENSION postgis;` dans votre base de données.
    - Créez un utilisateur et notez le mot de passe.

4.  **File d'attente de Tâches :**
    - Créez une file d'attente Cloud Tasks (ex: `geocongo-results-queue`).

5.  **Compte de Service pour le Worker :**
    - Créez un compte de service (ex: `geocongo-worker-sa`).
    - Donnez-lui le rôle "Invocateur Cloud Run" (`run.invoker`) pour qu'il puisse appeler l'endpoint de la tâche.

6.  **Script de Déploiement (`scripts/deploy.sh`) :**
    - Créez le fichier `scripts/deploy.sh` avec le contenu fourni dans le contexte.
    - **Adaptez les variables** en haut du script (`PROJECT_ID`, `MODELS_BUCKET`, `WORKER_SA_EMAIL`).
    - Rendez le script exécutable : `chmod +x scripts/deploy.sh`.
    - Exécutez le script : `./scripts/deploy.sh`.

    **Ce que fait le script :**
    - Il construit l'image Docker via Cloud Build.
    - Il déploie une première version sur Cloud Run avec toutes les configurations (GPU, CPU, mémoire, timeout).
    - Il monte le bucket de modèles en tant que volume dans le conteneur (`--add-volume`).
    - Il configure les variables d'environnement, y compris la clé API et les informations de la file d'attente.
    - Il récupère l'URL du service déployé et la réinjecte dans une nouvelle révision pour que le worker de tâches connaisse sa propre adresse.
    - Il effectue une vérification de santé (`/health`) pour s'assurer que les modèles sont bien chargés avant de terminer.

### B. Déploiement sur AWS (Guide Conceptuel)

1.  **Stockage :** Créez un bucket S3 et uploadez les modèles.
2.  **Base de Données :** Lancez une instance Amazon RDS pour PostgreSQL et activez l'extension PostGIS.
3.  **Conteneur :**
    - Créez un référentiel sur Amazon ECR.
    - Construisez et poussez votre image Docker vers cet ECR.
4.  **Calcul :**
    - **Option 1 (Simple) : AWS App Runner.** Créez un service App Runner à partir de votre image ECR. Vous devrez configurer les variables d'environnement et les secrets. Le montage direct de S3 est moins direct qu'avec GCP ; vous pourriez avoir besoin de télécharger les modèles au démarrage du conteneur.
    - **Option 2 (Avancé) : AWS Fargate sur ECS.** Définissez une "Task Definition" avec les ressources nécessaires (CPU, mémoire, image ECR). Créez un service ECS pour exécuter cette tâche. Pour le GPU, vous devrez utiliser ECS sur des instances EC2 de type `g4dn`, `p3`, etc.
5.  **Tâches Asynchrones :**
    - Créez une file d'attente Amazon SQS.
    - L'endpoint `/analyze` enverra un message à cette file SQS.
    - Créez une fonction AWS Lambda qui est déclenchée par les messages SQS. Cette fonction Lambda fera un appel HTTP POST à l'endpoint `/tasks/execute-analysis` de votre service sur App Runner/ECS. Vous devrez adapter le `CloudTasksService` pour qu'il utilise le SDK Boto3 pour SQS.

### C. Déploiement sur Azure (Guide Conceptuel)

1.  **Stockage :** Créez un compte de stockage Azure et un conteneur Blob. Uploadez les modèles.
2.  **Base de Données :** Lancez une instance "Azure Database for PostgreSQL" et activez l'extension PostGIS.
3.  **Conteneur :**
    - Créez un "Azure Container Registry" (ACR).
    - Construisez et poussez votre image Docker vers cet ACR.
4.  **Calcul :**
    - **Option 1 (Simple) : Azure Container Apps.** Créez une "Container App" à partir de votre image ACR. Configurez les variables d'environnement et les secrets. Pour monter le stockage de blobs, utilisez la fonctionnalité de montage de volume d'Azure Files.
    - **Option 2 (Avancé) : Azure Kubernetes Service (AKS).** Déployez votre conteneur sur un cluster AKS, ce qui vous donne un contrôle total, notamment pour l'attribution de nœuds GPU.
5.  **Tâches Asynchrones :**
    - Créez une file d'attente "Azure Queue Storage".
    - L'endpoint `/analyze` enverra un message à cette file d'attente.
    - Créez une "Azure Function" avec un déclencheur de file d'attente ("Queue Trigger"). Cette fonction appellera l'endpoint `/tasks/execute-analysis` de votre Container App. Vous devrez adapter le `CloudTasksService` pour qu'il utilise le SDK Azure pour les files d'attente.

---

Ce guide fournit une base solide pour la recréation et le déploiement de l'API. L'adaptation aux spécificités de chaque cloud (notamment pour les services de tâches asynchrones et le montage de volumes) nécessitera d'écrire des implémentations de service spécifiques à chaque plateforme.