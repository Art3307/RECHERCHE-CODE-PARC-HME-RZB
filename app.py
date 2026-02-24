import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Recherche Parc HME ↔ RZB", layout="centered")
st.title("🔎 Recherche Parc : HME ↔ RZB")

# ----------------------------
# STYLE
# ----------------------------
st.markdown("""
<style>
.big-result {
    padding: 25px;
    border-radius: 15px;
    border: 1px solid rgba(255,255,255,0.15);
    background: rgba(255,255,255,0.05);
    margin-top: 18px;
    text-align: center;
}
.big-code {
    font-size: 56px;
    font-weight: 900;
    margin-bottom: 10px;
    letter-spacing: 1px;
}
.meta {
    font-size: 18px;
    opacity: 0.92;
    text-align: left;
    max-width: 620px;
    margin: 0 auto;
    line-height: 1.55;
}
.small {
    font-size: 13px;
    opacity: 0.75;
    margin-bottom: 8px;
}
.badge {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,.15);
    background: rgba(255,255,255,.06);
}

/* Colonne série */
.series-card {
    padding: 25px;
    border-radius: 15px;
    border: 1px solid rgba(255,255,255,0.15);
    background: rgba(255,255,255,0.05);
    margin-top: 18px;
}
.series-title {
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 10px;
}
.series-row {
    margin: 10px 0;
    font-size: 15px;
}
.series-label {
    display: inline-block;
    min-width: 140px;
    font-weight: 600;
}
.series-value {
    font-family: monospace;
}
.series-empty {
    opacity: 0.8;
    font-style: italic;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Helpers
# ----------------------------
def norm_text(s: str) -> str:
    return (s or "").strip().upper()

def norm_immat(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", norm_text(s))

def is_blank(x: str) -> bool:
    return norm_text(x) in ("", "NAN", "NONE", "NULL")

def clean_serial(v) -> str:
    s = norm_text("" if v is None else str(v))
    s = re.sub(r"\s+", " ", s).strip()
    return "" if is_blank(s) else s

# ----------------------------
# Chargement data
# ----------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("PARC RZB (version 1).xlsx", sheet_name="Feuil2", header=2)
    df.columns = [str(c).strip() for c in df.columns]

    rename_map = {
        "AGENCE": "AGENCE",
        "N° DE PARC HME": "PARC_HME",
        "N° PARC RZB": "PARC_RZB",
        "Libellé": "LIBELLE",
        "IMMATRICULATION": "IMMATRICULATION",
        "N° SERIE": "N° SERIE",
        "N° SERIE GRUE": "N° SERIE GRUE",
    }

    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    df["AGENCE"] = df["AGENCE"].ffill()
    df["PARC_HME"] = df["PARC_HME"].astype(str).map(norm_text)
    df["PARC_RZB"] = df["PARC_RZB"].astype(str).map(norm_text)
    df["IMMATRICULATION"] = df["IMMATRICULATION"].astype(str).map(norm_text)
    df["LIBELLE"] = df["LIBELLE"].astype(str).str.strip()

    if "N° SERIE" in df.columns:
        df["N° SERIE"] = df["N° SERIE"].apply(clean_serial)
    if "N° SERIE GRUE" in df.columns:
        df["N° SERIE GRUE"] = df["N° SERIE GRUE"].apply(clean_serial)

    df["IMM_NORM"] = df["IMMATRICULATION"].map(norm_immat)
    df = df[~df["PARC_HME"].map(is_blank)].copy()

    return df

df = load_data()

# ----------------------------
# Recherche (Contient uniquement)
# ----------------------------
def search_df(df_, query):
    q_raw = norm_text(query)
    if not q_raw:
        return df_.iloc[0:0]

    tokens = [t for t in re.split(r"\s+", q_raw) if t]

    mask = pd.Series(True, index=df_.index)

    for tok in tokens:
        mask = mask & (
            df_["PARC_HME"].str.contains(tok, na=False) |
            df_["PARC_RZB"].str.contains(tok, na=False) |
            df_["IMMATRICULATION"].str.contains(tok, na=False) |
            df_["AGENCE"].str.contains(tok, na=False) |
            df_["LIBELLE"].str.contains(tok, na=False)
        )

    return df_[mask]

# ----------------------------
# Affichage
# ----------------------------
def render_big_card(row, query):
    big_value = row["PARC_RZB"]

    st.markdown(f"""
    <div class="big-result">
        <div class="big-code">{big_value}</div>
        <div class="meta">
            <b>HME :</b> {row['PARC_HME']}<br>
            <b>RZB :</b> {row['PARC_RZB']}<br>
            <b>Immat :</b> {row['IMMATRICULATION']}<br>
            <b>Agence :</b> {row['AGENCE']}<br>
            <b>Libellé :</b> {row['LIBELLE']}
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_series_side(row):
    s1 = clean_serial(row.get("N° SERIE", ""))
    s2 = clean_serial(row.get("N° SERIE GRUE", ""))

    if not (s1 or s2):
        st.markdown("""
        <div class="series-card">
            <div class="series-title">🔧 Numéros de série</div>
            <div class="series-empty">Pas de numéro de série enregistré</div>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(f"""
    <div class="series-card">
        <div class="series-title">🔧 Numéros de série</div>
        <div class="series-row">
            <span class="series-label">N° SERIE :</span>
            <span class="series-value">{s1 if s1 else "—"}</span>
        </div>
        <div class="series-row">
            <span class="series-label">N° SERIE GRUE :</span>
            <span class="series-value">{s2 if s2 else "—"}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------
# Interface
# ----------------------------
query = st.text_input(
    "Tape un code HME (H0…), RZB (X…), une immatriculation, ou des mots-clés",
)

if query:
    res = search_df(df, query)

    if res.empty:
        st.error("❌ Aucun résultat trouvé")
    else:
        chosen = res.iloc[0]

        left, right = st.columns([2.2, 1.3], gap="large")
        with left:
            render_big_card(chosen, query)
        with right:
            render_series_side(chosen)