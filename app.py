import streamlit as st
import pandas as pd
import re

st.set_page_config(
    page_title="Recherche Parc HME ↔ RZB",
    layout="centered",
    initial_sidebar_state="collapsed"
)
st.title("🔎 Recherche Parc : HME ↔ RZB")

# ----------------------------
# STYLE (fond noir + liseré orange)
# ----------------------------
st.markdown("""
<style>
.stApp { background:#0b0b0b; color:#f2f2f2; }

.stTextInput input, .stTextArea textarea {
    background:#121212 !important;
    color:#f2f2f2 !important;
    border:1px solid rgba(255,165,0,.35) !important;
}

.stButton button {
    background:#141414 !important;
    color:#f2f2f2 !important;
    border:1px solid rgba(255,165,0,.55) !important;
}
.stButton button:hover { border:1px solid rgba(255,165,0,.9) !important; }

.big-result{
    padding:22px; border-radius:16px;
    border:2px solid rgba(255,165,0,.85);
    background:rgba(255,255,255,0.03);
    margin-top:18px; text-align:center;
}
.big-code{
    font-size:56px; font-weight:900; margin-bottom:10px; letter-spacing:1px;
    color:#ffa500;
}
.meta{
    font-size:18px; opacity:0.95; text-align:left; max-width:650px;
    margin:0 auto; line-height:1.55;
}
.small{ font-size:13px; opacity:0.75; margin-bottom:8px; }
.badge{
    display:inline-block; padding:6px 10px; border-radius:999px;
    border:1px solid rgba(255,165,0,.75);
    background:rgba(255,165,0,.08);
    color:#ffd18a;
}

/* Carte séries à droite */
.series-card{
    padding:22px; border-radius:16px;
    border:2px solid rgba(255,165,0,.85);
    background:rgba(255,255,255,0.03);
    margin-top:18px;
}
.series-title{
    font-size:16px; font-weight:800; margin-bottom:10px; color:#ffd18a;
}
.series-row{ margin:12px 0; font-size:15px; line-height:1.45; }
.series-label{ display:block; font-weight:800; opacity:0.9; margin-bottom:6px; }
.series-value{
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    font-size:14px;
    white-space: pre-wrap;       /* garde les retours à la ligne si tu en mets dans Excel */
    word-break: break-word;
}
.series-empty{ opacity:0.8; font-style:italic; margin-top:8px; }

/* Tableau */
[data-testid="stDataFrame"]{
    border:1px solid rgba(255,165,0,.35);
    border-radius:12px;
    overflow:hidden;
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
    s = ("" if v is None else str(v)).strip()
    s = re.sub(r"\s+", " ", s).strip()
    return "" if is_blank(s) else s

def clean_comment(v) -> str:
    s = ("" if v is None else str(v)).strip()
    return "" if is_blank(s) else s

SERIAL_COLS = ["N° SERIE", "N° SERIE GRUE"]

# ----------------------------
# Chargement data
# ----------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("PARC RZB (version 1).xlsx", sheet_name="Feuil2", header=2)
    df.columns = [str(c).strip() for c in df.columns]

    # Renommage tolérant
    rename_map = {
        "AGENCE": "AGENCE",
        "N° DE PARC HME": "PARC_HME",
        "N° PARC RZB": "PARC_RZB",
        "Libellé": "LIBELLE",
        "LIBELLE": "LIBELLE",
        "IMMATRICULATION": "IMMATRICULATION",
        "N° SERIE": "N° SERIE",
        "N° SERIE GRUE": "N° SERIE GRUE",
        "COMMENTAIRE": "COMMENTAIRE",
        "Commentaire": "COMMENTAIRE",
        "Commentaires": "COMMENTAIRE",
        "COMMENTAIRES": "COMMENTAIRE",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Normalisation
    if "AGENCE" in df.columns:
        df["AGENCE"] = df["AGENCE"].ffill()
    else:
        df["AGENCE"] = ""

    for col in ["PARC_HME", "PARC_RZB", "IMMATRICULATION"]:
        if col in df.columns:
            df[col] = df[col].astype(str).map(norm_text)
        else:
            df[col] = ""

    if "LIBELLE" in df.columns:
        df["LIBELLE"] = df["LIBELLE"].astype(str).map(lambda x: (x or "").strip())
    else:
        df["LIBELLE"] = ""

    if "COMMENTAIRE" in df.columns:
        df["COMMENTAIRE"] = df["COMMENTAIRE"].apply(clean_comment)
    else:
        df["COMMENTAIRE"] = ""

    for col in SERIAL_COLS:
        if col in df.columns:
            df[col] = df[col].apply(clean_serial)
        else:
            df[col] = ""

    df["IMM_NORM"] = df["IMMATRICULATION"].map(norm_immat) if "IMMATRICULATION" in df.columns else ""

    # Filtrer lignes vides (parc HME vide)
    df = df[~df["PARC_HME"].map(is_blank)].copy()

    return df

df = load_data()

# ----------------------------
# Recherche (CONTIENT uniquement)
# ----------------------------
def search_df_contains(df_: pd.DataFrame, query: str) -> pd.DataFrame:
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
    commentaire = df_["COMMENTAIRE"].astype(str).map(norm_text)

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
            libelle.str.contains(tok, na=False, regex=False) |
            commentaire.str.contains(tok, na=False, regex=False)
        )

        if tok_immat:
            one_tok_mask = one_tok_mask | imm_norm.str.contains(tok_immat, na=False, regex=False)

        mask = mask & one_tok_mask

    return df_[mask].copy()

# ----------------------------
# Affichage
# ----------------------------
def render_series_side(row: pd.Series):
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
        <div class="series-label">N° SERIE :</div>
        <div class="series-value">{s1 if s1 else "—"}</div>
      </div>

      <div class="series-row" style="margin-top:18px;">
        <div class="series-label">N° SERIE GRUE :</div>
        <div class="series-value">{s2 if s2 else "—"}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_big_card(row: pd.Series, user_query: str):
    q = norm_text(user_query)

    typed_is_hme = bool(re.match(r"^H[0-9A-Z]", q))
    typed_is_rzb = bool(re.match(r"^X[0-9A-Z]", q))

    if typed_is_hme:
        big_value, big_label = row.get("PARC_RZB", ""), "RZB"
    elif typed_is_rzb:
        big_value, big_label = row.get("PARC_HME", ""), "HME"
    else:
        big_value, big_label = row.get("PARC_RZB", ""), "RZB"

    immat = "" if is_blank(row.get("IMMATRICULATION", "")) else row.get("IMMATRICULATION", "")
    com = clean_comment(row.get("COMMENTAIRE", ""))

    # Sécurisation : pas d'injection HTML accidentelle
    com = com.replace("<", "&lt;").replace(">", "&gt;")

    # Si commentaire vide → rien du tout
    com_block = ""
    if com:
        com_block = f"<br><b>Commentaire :</b> {com}"

    st.markdown(f"""
    <div class="big-result">
        <div class="small"><span class="badge">{big_label}</span></div>
        <div class="big-code">{big_value}</div>
        <div class="meta">
            <b>HME :</b> {row.get('PARC_HME','')}<br>
            <b>RZB :</b> {row.get('PARC_RZB','')}<br>
            <b>Immat :</b> {immat}<br>
            <b>Agence :</b> {row.get('AGENCE','')}<br>
            <b>Libellé :</b> {row.get('LIBELLE','')}
            {com_block}
        </div>
    </div>
    """, unsafe_allow_html=True)
def results_table_with_selection(res: pd.DataFrame, filename: str, key: str):
    cols = ["AGENCE", "PARC_HME", "PARC_RZB", "IMMATRICULATION", "LIBELLE", "COMMENTAIRE"]
    cols = [c for c in cols if c in res.columns]

    st.caption("Clique une ligne pour afficher le résultat 👇")

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
                selected_pos = rows[0]
    except Exception:
        selected_pos = None

    return selected_pos

# ----------------------------
# UI
# ----------------------------
tab1, tab2 = st.tabs(["Recherche simple", "Multi-recherche (liste)"])

with tab1:
    # On garde la dernière recherche affichée même si le champ se vide
    if "last_query" not in st.session_state:
        st.session_state["last_query"] = ""

    with st.form("search_form", clear_on_submit=True):
        query_input = st.text_input(
            "Tape un code HME (H0…), RZB (X…), une immatriculation, ou des mots-clés (ex: pelle bassin)",
            placeholder="Ex: H01100M / X001L / AB-123-CD / pelle bassin",
            key="query_input"
        )
        submitted = st.form_submit_button("🔎 Rechercher")

    if submitted:
        st.session_state["last_query"] = query_input.strip()

    query = st.session_state["last_query"]

    if query:
        res = search_df_contains(df, query)

        if res.empty:
            st.error("❌ Aucun résultat trouvé")
        else:
            if len(res) == 1:
                chosen = res.iloc[0]
            else:
                st.info(f"✅ {len(res)} résultats trouvés.")
                selected_pos = results_table_with_selection(res, "resultats_parc.csv", key="table_simple")
                chosen = res.iloc[selected_pos] if selected_pos is not None else res.iloc[0]

            left, right = st.columns([2.2, 1.3], gap="large")
            with left:
                render_big_card(chosen, query)
            with right:
                render_series_side(chosen)

with tab2:
    st.write("Colle une liste (1 entrée par ligne). Tu peux aussi mettre des mots-clés :")
    st.code("H01100M\nX001L\nAB-123-CD\npelle bassin", language="text")

    raw_list = st.text_area("Liste", height=180, placeholder="1 entrée par ligne…")
    if raw_list.strip():
        items = [x.strip() for x in raw_list.splitlines() if x.strip()]
        items = list(dict.fromkeys(items))  # unique en gardant l'ordre

        all_results = []
        for it in items:
            r = search_df_contains(df, it)
            if not r.empty:
                rr = r.copy()
                rr.insert(0, "RECHERCHE", it)
                all_results.append(rr)

        if not all_results:
            st.error("❌ Aucun résultat trouvé pour la liste.")
        else:
            out = pd.concat(all_results, ignore_index=True)
            st.success(f"✅ {len(out)} ligne(s) trouvée(s) (pour {len(items)} recherche(s)).")

            cols = ["RECHERCHE", "AGENCE", "PARC_HME", "PARC_RZB", "IMMATRICULATION", "LIBELLE", "COMMENTAIRE"]
            cols = [c for c in cols if c in out.columns]
            st.dataframe(out[cols], use_container_width=True, hide_index=True)

            csv = out[cols].to_csv(index=False, sep=";").encode("utf-8")
            st.download_button("⬇️ Télécharger (CSV)", data=csv, file_name="multi_resultats_parc.csv", mime="text/csv")



