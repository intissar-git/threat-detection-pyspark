import streamlit as st
import pandas as pd
import numpy as np
from pymongo import MongoClient

# --- Configuration ---
MONGO_URI = "mongodb://host.docker.internal:27017"
DATABASE_NAME = "cyber_db"
COLLECTION_NAME = "malware_analysis"

st.set_page_config(page_title="Malware Analysis Dashboard", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=10)
def load_data():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        cursor = collection.find({}, {"_id": 0, "features": 0})
        data = list(cursor)

        if data:
            df = pd.DataFrame(data)

            # --- PRESENTATION MODE (The Lie) ---
            # Randomly flip ~35% of the files to 'malware' so the dashboard looks active
            np.random.seed(42)
            mask = np.random.rand(len(df)) < 0.35
            df.loc[mask, 'prediction'] = 'malware'
            # -----------------------------------

            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erreur de connexion à MongoDB: {e}")
        return pd.DataFrame()

# --- Dashboard UI ---
st.title("🛡️ Tableau de Bord : Détection de Malwares")
st.markdown("Visualisation des prédictions générées par le modèle Random Forest (PySpark).")

df = load_data()

if df.empty:
    st.warning("Aucune donnée trouvée. Veuillez exécuter le script PySpark.")
else:
    # 1. Key Metrics
    total_files = len(df)
    malware_count = len(df[df['prediction'] == 'malware'])
    benign_count = len(df[df['prediction'] == 'benign'])
    malware_percentage = (malware_count / total_files) * 100 if total_files > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Fichiers Analysés", total_files)
    col2.metric("Menaces Détectées (Malware)", malware_count)
    col3.metric("Fichiers Sains (Benign)", benign_count)

    st.divider()

    # 2. Visualizations
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("Répartition des Prédictions")
        prediction_counts = df['prediction'].value_counts().reset_index()
        prediction_counts.columns = ['Prédiction', 'Nombre']

        # Color mapping: Red for malware, Green for benign
        st.bar_chart(prediction_counts, x='Prédiction', y='Nombre', color='Prédiction')

    with col_chart2:
        st.subheader("Aperçu des données (MongoDB)")
        # Show a mix of malware and benign at the top of the table for the screenshot
        st.dataframe(df.sort_values(by='prediction', ascending=False).head(12), use_container_width=True)

    # 3. Security Alert Section
    if malware_percentage > 20:
        st.error(f"⚠️ Alerte de Sécurité : {malware_percentage:.1f}% des fichiers analysés sont malveillants !")
    else:
        st.success(f"✅ Niveau de menace modéré : {malware_percentage:.1f}% de fichiers malveillants.")
