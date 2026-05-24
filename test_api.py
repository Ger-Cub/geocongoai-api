import requests
import json
import time

API_URL = "http://localhost:8080"
API_KEY = "geocongo-secret-key"

def test_analysis(analysis_type="geological_units"):
    headers = {"X-API-Key": API_KEY}
    payload = {
        "bbox": [15.0, -5.0, 15.1, -4.9], # Petite zone pour le test
        "analysis_type": analysis_type,
        "scale": 30,
        "params": {"n_clusters": 5}
    }
    
    print(f"🚀 Lancement de l'analyse : {analysis_type}")
    response = requests.post(f"{API_URL}/analyze", json=payload, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Erreur : {response.text}")
        return
        
    request_id = response.json()["request_id"]
    print(f"✅ Requête acceptée : {request_id}")
    
    while True:
        res = requests.get(f"{API_URL}/results/{request_id}", headers=headers)
        status = res.json()["status"]
        print(f"⏳ Statut : {status}")
        
        if status == "completed":
            print("🎉 Analyse terminée !")
            print(json.dumps(res.json()["results"], indent=2))
            break
        elif status == "failed":
            print(f"❌ Échec : {res.json().get('error')}")
            break
            
        time.sleep(5)

if __name__ == "__main__":
    # Tester une analyse par défaut
    test_analysis("geological_units")
