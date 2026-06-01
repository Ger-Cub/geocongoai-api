import numpy as np
import os
import asyncio
import sys
from unittest.mock import MagicMock

# Add current directory to path
sys.path.append(os.getcwd())

# Import the analysis module
from app.services.analysis.mineral_detection import run_analysis

async def test_mineral_analysis():
    print("🔬 Simulation d'une analyse de détection minérale en local...")
    
    # 1. Création de fausses caractéristiques Prithvi (H=20, W=20, Dim=128)
    # On simule une zone "anormale" au milieu
    features = np.random.normal(0, 1, (20, 20, 128)).astype(np.float32)
    features[8:12, 8:12, :] += 5.0  # Simulation d'une anomalie spectrale
    
    # 2. Création d'un faux profil rasterio
    from rasterio.transform import from_origin
    profile = {
        'driver': 'GTiff',
        'dtype': 'float32',
        'nodata': None,
        'width': 20,
        'height': 20,
        'count': 6,
        'crs': 'EPSG:4326',
        'transform': from_origin(28.8, -2.4, 0.01, 0.01) # Zone de Bukavu
    }
    
    # 3. Dossier de travail temporaire
    work_dir = "test_results"
    os.makedirs(work_dir, exist_ok=True)
    
    # 4. Exécution de l'analyse
    params = {"threshold": 0.8}
    result = await run_analysis(features, profile, work_dir, params)
    
    print("\n✅ Résultat de l'analyse :")
    print(f"- Nombre d'anomalies détectées : {result['n_anomalies']}")
    print(f"- Z-score maximum : {result['max_z_score']:.2f}")
    print(f"- Fichier généré : {result['files'][0]}")
    
    if os.path.exists(result['files'][0]):
        print("📂 Le fichier GeoJSON a été créé avec succès.")
    else:
        print("❌ Erreur : Le fichier GeoJSON n'a pas été généré.")

if __name__ == "__main__":
    asyncio.run(test_mineral_analysis())
