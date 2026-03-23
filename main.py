import streamlit as st
import pandas as pd
from pymongo import MongoClient

# --- Configuration ---
# Connect to the MongoDB container
MONGO_URI = "mongodb://host.docker.internal:27017"
DATABASE_NAME = "cyber_db"
COLLECTION_NAME = "malware_analysis"

st.set_page_config(page_title="Malware Analysis Dashboard", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=10) # Cache data for 10 seconds to avoid spamming the database
def load_data():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        # Fetch all documents, excluding the MongoDB '_id' and the raw features array to save memory
        cursor = collection.find({}, {"_id": 0, "features": 0})
        data = list(cursor)

        if data:
            return pd.DataFrame(data)
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erreur de connexion à MongoDB: {e}")
        return pd.DataFrame()

# --- Dashboard UI ---
st.title("🛡️ Tableau de Bord : Détection de Malwares")
st.markdown("Visualisation des prédictions générées par le modèle Random Forest (PySpark)[cite: 54].")

df = load_data()

if df.empty:
    st.warning("Aucune donnée trouvée. Veuillez d'abord exécuter le script PySpark (main.py) pour peupler la base de données.")
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
        # Count the occurrences of each prediction
        prediction_counts = df['prediction'].value_counts().reset_index()
        prediction_counts.columns = ['Prédiction', 'Nombre']

        # Native Streamlit Bar Chart
        st.bar_chart(prediction_counts, x='Prédiction', y='Nombre', color=["#FF4B4B"])

    with col_chart2:
        st.subheader("Aperçu des données brutes (MongoDB)")
        st.dataframe(df.head(10), use_container_width=True)

    # 3. Security Alert Section
    if malware_percentage > 50:
        st.error(f"⚠️ Alerte de Sécurité : {malware_percentage:.1f}% des fichiers analysés sont malveillants !")
    else:
        st.success(f"✅ Niveau de menace modéré : {malware_percentage:.1f}% de fichiers malveillants.")
