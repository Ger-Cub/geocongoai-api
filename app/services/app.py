import streamlit as st
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
import requests
import time
import os

# --- Configuration ---
# Vous pourrez remplacer localhost par l'URL de votre API Cloud Run (ex: https://geocongo-api-xyz.a.run.app)
API_URL = os.getenv("API_URL", "http://localhost:8080")
API_KEY = "test_key_geocongo"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

st.set_page_config(page_title="GeoCongo AI", layout="wide", page_icon="🌍")

st.title("🌍 GeoCongo AI - Géo-Intelligence Interactive")
st.markdown("Dessinez une zone sur la carte, choisissez le type d'analyse et laissez l'IA opérer !")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("1. Sélection de la zone")
    # Initialisation de la carte centrée sur l'Est de la RDC
    m = folium.Map(location=[-2.5, 28.8], zoom_start=10)
    
    # Ajout de l'outil de dessin
    draw = Draw(
        export=True,
        position='topleft',
        draw_options={'polyline': False, 'polyline': False, 'circle': False, 'marker': False, 'circlemarker': False, 'polygon': False, 'rectangle': True},
        edit_options={'edit': False}
    )
    m.add_child(draw)

    # Affichage de la carte
    st_data = st_folium(m, width=700, height=500)

with col2:
    st.subheader("2. Paramètres d'Analyse")
    
    analysis_type = st.selectbox(
        "Que souhaitez-vous détecter ?",
        ("failles", "mines", "minéraux", "landcover")
    )
    
    if st.button("🚀 Lancer l'Analyse par IA", type="primary"):
        # Vérifier si un rectangle a été dessiné
        if not st_data.get("last_active_drawing"):
            st.warning("⚠️ Veuillez d'abord dessiner un rectangle sur la carte.")
        else:
            # Extraire les coordonnées BBox du dessin Folium
            geom = st_data["last_active_drawing"]["geometry"]["coordinates"][0]
            lons = [p[0] for p in geom]
            lats = [p[1] for p in geom]
            bbox = [min(lons), min(lats), max(lons), max(lats)]
            
            st.info(f"📍 Zone sélectionnée : {bbox}")
            
            # --- ÉTAPE 1 : ENVOYER LA REQUÊTE ---
            with st.spinner("⏳ Envoi de la requête à l'API..."):
                payload = {"bbox": bbox, "analysis_type": analysis_type}
                try:
                    response = requests.post(f"{API_URL}/analyze", json=payload, headers=HEADERS)
                    response.raise_for_status()
                    task_data = response.json()
                    task_id = task_data.get("task_id")
                    st.success(f"Tâche créée ! ID: `{task_id}`")
                except Exception as e:
                    st.error(f"❌ Erreur de communication avec l'API: {e}")
                    st.stop()

            # --- ÉTAPE 2 : POLLLING (Attendre le résultat asynchrone) ---
            progress_bar = st.progress(0, text="Les modèles IA Vertex traitent l'image...")
            status = "processing"
            while status not in ["completed", "failed"]:
                time.sleep(3) # On interroge l'API toutes les 3 secondes
                try:
                    res_status = requests.get(f"{API_URL}/tasks/status/{task_id}", headers=HEADERS)
                    status = res_status.json().get("status", "unknown")
                except:
                    pass # Ignore les erreurs temporaires de réseau
            
            progress_bar.empty()
            
            if status == "failed":
                st.error("❌ Le traitement a échoué. Vérifiez les logs côté serveur.")
            else:
                # --- ÉTAPE 3 : RÉCUPÉRER ET AFFICHER LE RÉSULTAT ---
                st.success("✅ Analyse terminée avec succès !")
                with st.spinner("Téléchargement des résultats vectorisés..."):
                    bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
                    res_data = requests.get(f"{API_URL}/results", params={"bbox": bbox_str, "analysis_type": analysis_type}, headers=HEADERS)
                    geojson_results = res_data.json()
                
                # Afficher le résultat sur une nouvelle mini-carte
                st.subheader("🗺️ Résultats de la détection")
                res_map = folium.Map(location=[(bbox[1]+bbox[3])/2, (bbox[0]+bbox[2])/2], zoom_start=12)
                folium.GeoJson(geojson_results, style_function=lambda x: {'color': 'red', 'weight': 2, 'fillOpacity': 0.3}).add_to(res_map)
                folium.Rectangle(bounds=[(bbox[1], bbox[0]), (bbox[3], bbox[2])], color='blue', dash_array='5, 5').add_to(res_map)
                st_folium(res_map, width=400, height=300)
                
                st.download_button("💾 Télécharger le GeoJSON", data=str(geojson_results), file_name=f"resultats_{analysis_type}.geojson", mime="application/json")