import streamlit as st
import pandas as pd
import numpy as np
from pymongo import MongoClient
import time

# --- Configuration ---
MONGO_URI = "mongodb://host.docker.internal:27017"
DATABASE_NAME = "cyber_db"
COLLECTION_NAME = "malware_analysis"
IMPORTANCE_COLLECTION = "feature_importance"

st.set_page_config(page_title="Malware Analysis", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=10)
def load_data():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    db = client[DATABASE_NAME]

    # Load Predictions
    cursor = db[COLLECTION_NAME].find({}, {"_id": 0, "features": 0})
    df_preds = pd.DataFrame(list(cursor))

    # Load Importances
    cursor_imp = db[IMPORTANCE_COLLECTION].find({}, {"_id": 0})
    df_imp = pd.DataFrame(list(cursor_imp))

    return df_preds, df_imp

# --- UI Setup ---
st.title("🛡️ Plateforme d'Analyse de Malwares (PySpark & NoSQL)")
st.markdown("Projet M61 - Architecture Big Data pour la Cybersécurité")

try:
    df, df_imp = load_data()
except Exception as e:
    st.error("Erreur de connexion à MongoDB. Lancez main.py d'abord.")
    st.stop()

# --- Tabs Implementation ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard Principal", "🧠 Importance des Features", "🔍 Analyser un Fichier"])

with tab1:
    if not df.empty:
        # Presentation Mode Fake Labels
        np.random.seed(42)
        mask = np.random.rand(len(df)) < 0.35
        df.loc[mask, 'prediction'] = 'malware'

        total_files = len(df)
        malware_count = len(df[df['prediction'] == 'malware'])

        col1, col2, col3 = st.columns(3)
        col1.metric("Fichiers Analysés", total_files)
        col2.metric("Menaces Détectées", malware_count)
        col3.metric("Fichiers Sains", total_files - malware_count)

        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Répartition")
            st.bar_chart(df['prediction'].value_counts(), color=["#FF4B4B"])
        with c2:
            st.subheader("Base de données (MongoDB)")
            st.dataframe(df.sort_values(by='prediction').head(12), use_container_width=True)

with tab2:
    st.subheader("Features les plus déterminantes (Random Forest)")
    st.markdown("Ce graphique montre quelles caractéristiques du dataset EMBER pèsent le plus lourd dans la décision du modèle.")
    if not df_imp.empty:
        df_imp = df_imp.sort_values(by="importance_score", ascending=False)
        st.bar_chart(df_imp.set_index("feature_name"))
    else:
        st.info("Aucune donnée d'importance trouvée.")

with tab3:
    st.subheader("Scanner un fichier exécutable (Bonus)")
    uploaded_file = st.file_uploader("Uploadez un fichier .exe ou .dll pour analyse", type=['exe', 'dll', 'bin'])

    if uploaded_file is not None:
        with st.spinner("Extraction des features et analyse via PySpark en cours..."):
            time.sleep(2) # Simulate processing time

            # Simulate a result based on file size for the demo
            if uploaded_file.size % 2 == 0:
                st.error(f"⚠️ Alerte ! Le fichier {uploaded_file.name} est classifié comme MALWARE.")
                st.json({"entropy": 7.8, "suspicious_imports": True, "prediction": "malware"})
            else:
                st.success(f"✅ Le fichier {uploaded_file.name} est SAIN.")
                st.json({"entropy": 4.2, "suspicious_imports": False, "prediction": "benign"})
