import streamlit as st
import pandas as pd

st.set_page_config(page_title="Recherche Parc HME ↔ RZB", layout="centered")

st.title("🔎 Recherche Parc : HME ↔ RZB")

# ----------------------------
# STYLE (résultat en gros)
# ----------------------------
st.markdown("""
<style>
.big-result {
    padding: 25px;
    border-radius: 15px;
    border: 1px solid rgba(255,255,255,0.15);
    background: rgba(255,255,255,0.05);
    margin-top: 20px;
    text-align: center;
}
.big-code {
    font-size: 56px;
    font-weight: 900;
    margin-bottom: 15px;
}
.meta {
    font-size: 18px;
    opacity: 0.9;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Chargement du fichier (silencieux)
# ----------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("PARC RZB (version 1).xlsx", header=1)

    df = df.rename(columns={
        df.columns[0]: "AGENCE",
        df.columns[1]: "PARC_HME",
        df.columns[2]: "PARC_RZB",
        df.columns[3]: "LIBELLE",
    })

    df["AGENCE"] = df["AGENCE"].ffill()
    df["PARC_HME"] = df["PARC_HME"].astype(str).str.strip().str.upper()
    df["PARC_RZB"] = df["PARC_RZB"].astype(str).str.strip().str.upper()
    df["LIBELLE"] = df["LIBELLE"].astype(str).str.strip()

    df = df[df["PARC_HME"].notna() & (df["PARC_HME"] != "")]
    return df

df = load_data()

# ----------------------------
# Sidebar (réglages discrets)
# ----------------------------
with st.sidebar:
    st.header("⚙️ Options")
    direction = st.selectbox("Sens", ["HME ➜ RZB", "RZB ➜ HME"])
    mode = st.radio("Mode", ["Contient (partiel)"])

# ----------------------------
# Définition des colonnes selon sens
# ----------------------------
if direction == "HME ➜ RZB":
    input_col = "PARC_HME"
    output_col = "PARC_RZB"
    placeholder = "Ex: H01100M"
else:
    input_col = "PARC_RZB"
    output_col = "PARC_HME"
    placeholder = "Ex: X001L"

# ----------------------------
# Champ de recherche
# ----------------------------
query = st.text_input("Entre ton code :", placeholder=placeholder).strip().upper()

# ----------------------------
# Recherche
# ----------------------------
if query:

    if mode == "Exact":
        result = df[df[input_col] == query]
    else:
        result = df[df[input_col].str.contains(query, na=False)]

    if result.empty:
        st.error("❌ Aucun résultat trouvé")
    else:
        row = result.iloc[0]

        st.markdown(f"""
        <div class="big-result">
            <div class="big-code">{row[output_col]}</div>
            <div class="meta">
                <b>Agence :</b> {row['AGENCE']}<br>
                <b>Libellé :</b> {row['LIBELLE']}<br>
                <b>{input_col} :</b> {row[input_col]}
            </div>
        </div>
        """, unsafe_allow_html=True)
