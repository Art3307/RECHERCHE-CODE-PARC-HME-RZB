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
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Helpers
# ----------------------------
def norm_text(s: str) -> str:
    return (s or "").strip().upper()

def norm_immat(s: str) -> str:
    """
    Normalise une immatriculation pour matcher:
    AB-123-CD / AB 123 CD / AB123CD -> AB123CD
    """
    s = norm_text(s)
    # garde lettres/chiffres uniquement
    return re.sub(r"[^A-Z0-9]", "", s)

def is_blank(x: str) -> bool:
    x = norm_text(x)
    return x in ("", "NAN", "NONE")

# ----------------------------
# Chargement data
# ----------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("PARC RZB (version 1).xlsx", header=1)

    # AGENCE | HME | RZB | Libellé | IMMATRICULATION
    df = df.rename(columns={
        df.columns[0]: "AGENCE",
        df.columns[1]: "PARC_HME",
        df.columns[2]: "PARC_RZB",
        df.columns[3]: "LIBELLE",
        df.columns[4]: "IMMATRICULATION",
    })

    df["AGENCE"] = df["AGENCE"].ffill()

    df["PARC_HME"] = df["PARC_HME"].astype(str).map(norm_text)
    df["PARC_RZB"] = df["PARC_RZB"].astype(str).map(norm_text)
    df["LIBELLE"] = df["LIBELLE"].astype(str).map(lambda x: (x or "").strip())
    df["IMMATRICULATION"] = df["IMMATRICULATION"].astype(str).map(norm_text)

    # colonne normalisée pour immat
    df["IMM_NORM"] = df["IMMATRICULATION"].map(norm_immat)

    # Retirer lignes vides
    df = df[~df["PARC_HME"].map(is_blank)].copy()

    return df

df = load_data()

# ----------------------------
# Options
# ----------------------------
with st.sidebar:
    st.header("⚙️ Options")
    mode = st.radio("Mode de recherche", ["Exact", "Contient (partiel)"], index=1)
    st.caption("Recherche sur HME, RZB, Immat, Agence, Libellé.")
    show_table_on_single = st.checkbox("Afficher le tableau si plusieurs résultats", value=True)

# ----------------------------
# Recherche (fonction commune)
# ----------------------------
def search_df(df_: pd.DataFrame, query: str, mode_: str) -> pd.DataFrame:
    q_raw = norm_text(query)
    if not q_raw:
        return df_.iloc[0:0].copy()

    # Pour les immats, on compare aussi une version normalisée
    q_immat = norm_immat(q_raw)

    if mode_ == "Exact":
        # Exact: HME/RZB exact, Immat exact (normalisé aussi)
        return df_[
            (df_["PARC_HME"] == q_raw) |
            (df_["PARC_RZB"] == q_raw) |
            (df_["IMMATRICULATION"] == q_raw) |
            ((df_["IMM_NORM"] == q_immat) & (q_immat != ""))
        ].copy()

    # Contient: recherche "mots-clés" sur toutes les colonnes utiles
    # IMPORTANT: regex=False pour éviter les soucis si la recherche contient des caractères spéciaux
    return df_[
        df_["PARC_HME"].str.contains(q_raw, na=False, regex=False) |
        df_["PARC_RZB"].str.contains(q_raw, na=False, regex=False) |
        df_["IMMATRICULATION"].str.contains(q_raw, na=False, regex=False) |
        df_["IMM_NORM"].str.contains(q_immat, na=False, regex=False) |
        df_["AGENCE"].astype(str).map(norm_text).str.contains(q_raw, na=False, regex=False) |
        df_["LIBELLE"].astype(str).map(norm_text).str.contains(q_raw, na=False, regex=False)
    ].copy()

def render_big_card(row: pd.Series, user_query: str):
    q = norm_text(user_query)
    typed_is_hme = q.startswith("H")
    typed_is_rzb = q.startswith("X")
    typed_immat_like = (not typed_is_hme and not typed_is_rzb and norm_immat(q) != "")

    # En gros : le "code opposé" si on a tapé HME ou RZB, sinon RZB par défaut
    if typed_is_hme:
        big_value, big_label = row["PARC_RZB"], "RZB"
    elif typed_is_rzb:
        big_value, big_label = row["PARC_HME"], "HME"
    else:
        big_value, big_label = row["PARC_RZB"], ("RZB" if typed_immat_like else "Résultat")

    immat = "" if is_blank(row.get("IMMATRICULATION", "")) else row.get("IMMATRICULATION", "")

    st.markdown(f"""
    <div class="big-result">
        <div class="small"><span class="badge">{big_label}</span></div>
        <div class="big-code">{big_value}</div>
        <div class="meta">
            <b>HME :</b> {row['PARC_HME']}<br>
            <b>RZB :</b> {row['PARC_RZB']}<br>
            <b>Immat :</b> {immat}<br>
            <b>Agence :</b> {row['AGENCE']}<br>
            <b>Libellé :</b> {row['LIBELLE']}
        </div>
    </div>
    """, unsafe_allow_html=True)

def results_table(res: pd.DataFrame):
    cols = ["AGENCE", "PARC_HME", "PARC_RZB", "IMMATRICULATION", "LIBELLE"]
    st.dataframe(res[cols], use_container_width=True)

    csv = res[cols].to_csv(index=False, sep=";").encode("utf-8")
    st.download_button("⬇️ Télécharger les résultats (CSV)", data=csv, file_name="resultats_parc.csv", mime="text/csv")

# ----------------------------
# UI : onglets (Simple / Multi)
# ----------------------------
tab1, tab2 = st.tabs(["Recherche simple", "Multi-recherche (liste)"])

with tab1:
    query = st.text_input(
        "Tape un code HME (H0…), RZB (X…), une immatriculation, ou un mot-clé (ex: BASSIN)",
        placeholder="Ex: H01100M / X001L / AB-123-CD / BASSIN"
    )

    if query:
        res = search_df(df, query, mode)

        if res.empty:
            st.error("❌ Aucun résultat trouvé")
        else:
            # carte du premier résultat
            render_big_card(res.iloc[0], query)

            # si plusieurs résultats (ex: BASSIN), on affiche le tableau complet
            if len(res) > 1 and show_table_on_single:
                st.info(f"✅ {len(res)} résultats trouvés.")
                results_table(res)

with tab2:
    st.write("Colle une liste de codes / mots-clés (1 par ligne). Exemple :")
    st.code("H01100M\nX001L\nAB-123-CD\nBASSIN", language="text")

    raw_list = st.text_area("Liste", height=180, placeholder="1 entrée par ligne…")
    if raw_list.strip():
        items = [norm_text(x) for x in raw_list.splitlines() if norm_text(x)]
        items = list(dict.fromkeys(items))  # unique en gardant l'ordre

        all_results = []
        for it in items:
            r = search_df(df, it, mode)
            if not r.empty:
                rr = r.copy()
                rr.insert(0, "RECHERCHE", it)
                all_results.append(rr)

        if not all_results:
            st.error("❌ Aucun résultat trouvé pour la liste.")
        else:
            out = pd.concat(all_results, ignore_index=True)

            st.success(f"✅ {len(out)} ligne(s) trouvée(s) (pour {len(items)} recherche(s)).")
            cols = ["RECHERCHE", "AGENCE", "PARC_HME", "PARC_RZB", "IMMATRICULATION", "LIBELLE"]
            st.dataframe(out[cols], use_container_width=True)

            csv = out[cols].to_csv(index=False, sep=";").encode("utf-8")
            st.download_button("⬇️ Télécharger (CSV)", data=csv, file_name="multi_resultats_parc.csv", mime="text/csv")
