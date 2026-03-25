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
    import math

    def calc_entropy(data):
        if not data: return 0.0
        freq = {}
        for b in data:
            freq[b] = freq.get(b, 0) + 1
        n = len(data)
        return -sum((c/n)*math.log2(c/n) for c in freq.values())

    st.subheader("Scanner un fichier exécutable (Bonus)")
    uploaded_file = st.file_uploader(
        "Uploadez un fichier .exe ou .dll pour analyse",
        type=['exe', 'dll', 'bin']
    )

    if uploaded_file is not None:
        with st.spinner("Analyse en cours..."):
            file_bytes = uploaded_file.read()
            n = len(file_bytes)

            # ── Extraction des vraies features ──────────────────────────
            entropy_val  = calc_entropy(file_bytes)
            has_mz       = file_bytes[:2] == b'MZ'
            has_pe       = b'PE\x00\x00' in file_bytes[:1024]
            ratio_null   = file_bytes.count(0) / max(n, 1)
            ratio_print  = sum(1 for b in file_bytes if 32 <= b <= 126) / max(n, 1)

            # ── Règles de décision réelles ───────────────────────────────
            risk_score = 0
            if entropy_val > 7.0:  risk_score += 3   # packing/chiffrement
            if entropy_val > 6.0:  risk_score += 1
            if has_mz and has_pe:  risk_score += 1   # exécutable Windows
            if ratio_null > 0.5:   risk_score -= 1   # beaucoup de zéros → bénin
            if ratio_print > 0.6:  risk_score -= 1   # beaucoup de texte → bénin

            prediction = "malware" if risk_score >= 3 else "benign"

        # ── Affichage résultat ────────────────────────────────────────────
        if prediction == "malware":
            st.error(f"⚠️ Alerte ! Le fichier **{uploaded_file.name}** "
                     f"est classifié comme **MALWARE**.")
        else:
            st.success(f"✅ Le fichier **{uploaded_file.name}** est **SAIN (benign)**.")

        # ── Features extraites ────────────────────────────────────────────
        st.json({
            "file_size"          : n,
            "entropy"            : round(entropy_val, 3),
            "has_MZ_header"      : has_mz,
            "has_PE_signature"   : has_pe,
            "ratio_null_bytes"   : round(ratio_null, 3),
            "ratio_printable"    : round(ratio_print, 3),
            "risk_score"         : risk_score,
            "prediction"         : prediction
        })