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
    s = norm_text(s)
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
    df["IMM_NORM"] = df["IMMATRICULATION"].map(norm_immat)

    df = df[~df["PARC_HME"].map(is_blank)].copy()
    return df

df = load_data()

# ----------------------------
# Options
# ----------------------------
with st.sidebar:
    st.header("⚙️ Options")
    mode = st.radio("Mode de recherche", ["Exact", "Contient (partiel)"], index=1)
    st.caption("En mode 'Contient', la recherche multi-mots est en ET (AND). Ex: 'pelle bassin'.")

# ----------------------------
# Recherche
# ----------------------------
def search_df(df_: pd.DataFrame, query: str, mode_: str) -> pd.DataFrame:
    q_raw = norm_text(query)
    if not q_raw:
        return df_.iloc[0:0].copy()

    q_immat = norm_immat(q_raw)

    hme = df_["PARC_HME"]
    rzb = df_["PARC_RZB"]
    imm = df_["IMMATRICULATION"]
    imm_norm = df_["IMM_NORM"]
    agence = df_["AGENCE"].astype(str).map(norm_text)
    libelle = df_["LIBELLE"].astype(str).map(norm_text)

    if mode_ == "Exact":
        return df_[
            (hme == q_raw) |
            (rzb == q_raw) |
            (imm == q_raw) |
            ((imm_norm == q_immat) & (q_immat != ""))
        ].copy()

    tokens = [t for t in re.split(r"\s+", q_raw) if t]

    mask = pd.Series(True, index=df_.index)
    for tok in tokens:
        tok = norm_text(tok)
        tok_immat = norm_immat(tok)

        one_tok_mask = (
            hme.str.contains(tok, na=False, regex=False) |
            rzb.str.contains(tok, na=False, regex=False) |
            imm.str.contains(tok, na=False, regex=False) |
            agence.str.contains(tok, na=False, regex=False) |
            libelle.str.contains(tok, na=False, regex=False)
        )

        if tok_immat:
            one_tok_mask = one_tok_mask | imm_norm.str.contains(tok_immat, na=False, regex=False)

        mask = mask & one_tok_mask

    return df_[mask].copy()

def render_big_card(row: pd.Series, user_query: str):
    q = norm_text(user_query)
    typed_is_hme = q.startswith("H")
    typed_is_rzb = q.startswith("X")
    typed_immat_like = (not typed_is_hme and not typed_is_rzb and norm_immat(q) != "")

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

def results_table_with_selection(res: pd.DataFrame, filename: str, key: str):
    """
    Affiche le tableau + export CSV + renvoie l'index (position) de la ligne sélectionnée dans 'res'
    """
    cols = ["AGENCE", "PARC_HME", "PARC_RZB", "IMMATRICULATION", "LIBELLE"]

    st.caption("Clique une ligne pour afficher le détail en dessous 👇")

    # ⚠️ Nécessite une version Streamlit qui supporte la sélection dans st.dataframe.
    event = st.dataframe(
        res[cols],
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun",
        key=key
    )

    csv = res[cols].to_csv(index=False, sep=";").encode("utf-8")
    st.download_button("⬇️ Télécharger les résultats (CSV)", data=csv, file_name=filename, mime="text/csv")

    selected_pos = None
    try:
        if event is not None and hasattr(event, "selection") and event.selection is not None:
            rows = getattr(event.selection, "rows", None)
            if rows:
                selected_pos = rows[0]  # position dans le dataframe affiché
    except Exception:
        selected_pos = None

    return selected_pos

# ----------------------------
# UI : onglets
# ----------------------------
tab1, tab2 = st.tabs(["Recherche simple", "Multi-recherche (liste)"])

with tab1:
    query = st.text_input(
        "Tape un code HME (H0…), RZB (X…), une immatriculation, ou des mots-clés (ex: pelle bassin)",
        placeholder="Ex: H01100M / X001L / AB-123-CD / pelle bassin"
    )

    if query:
        res = search_df(df, query, mode)

        if res.empty:
            st.error("❌ Aucun résultat trouvé")
        else:
            if len(res) == 1:
                # 1 seul résultat : carte (inchangé)
                render_big_card(res.iloc[0], query)
            else:
                # Plusieurs résultats : tableau en premier
                st.info(f"✅ {len(res)} résultats trouvés.")
                selected_pos = results_table_with_selection(res, "resultats_parc.csv", key="table_simple")

                # Carte basée sur la ligne sélectionnée (sinon 1ère)
                chosen = res.iloc[selected_pos] if selected_pos is not None else res.iloc[0]
                render_big_card(chosen, query)

with tab2:
    st.write("Colle une liste (1 entrée par ligne). Tu peux aussi mettre des mots-clés :")
    st.code("H01100M\nX001L\nAB-123-CD\npelle bassin", language="text")

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

            st.dataframe(out[cols], use_container_width=True, hide_index=True)

            csv = out[cols].to_csv(index=False, sep=";").encode("utf-8")
            st.download_button("⬇️ Télécharger (CSV)", data=csv, file_name="multi_resultats_parc.csv", mime="text/csv")
