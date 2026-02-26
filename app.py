import streamlit as st
import pandas as pd
import re

st.set_page_config(
    page_title="Parc HME ↔ RZB",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── STYLES ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .result-card {
        background: #181818;
        border: 1px solid #333;
        border-radius: 6px;
        padding: 0;
        margin: 16px 0;
        overflow: hidden;
        box-shadow: 0 2px 12px rgba(0,0,0,0.5);
    }
    .result-header {
        background: #2a2a2a;
        border-bottom: 3px solid #ff9800;
        padding: 10px 16px;
        color: #ffcc80;
        font-size: 1.05em;
        font-weight: 600;
        display: flex;
        align-items: center;
    }
    .result-header::before {
        content: "→";
        margin-right: 8px;
        font-size: 1.2em;
    }
    .big-code {
        font-size: 3.1rem;
        font-weight: 800;
        color: #ffc107;
        text-align: center;
        padding: 16px 0 20px 0;
        letter-spacing: 1px;
        line-height: 0.95;
        background: linear-gradient(to bottom, #2a2a2a, #181818);
    }
    .main-content {
        padding: 0 20px 16px 20px;
    }
    .result-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        padding: 9px 0;
        border-bottom: 1px solid #2a2a2a;
    }
    .result-row:last-child {
        border-bottom: none;
    }
    .result-label {
        color: #9e9e9e;
        font-weight: 500;
        min-width: 130px;
        flex-shrink: 0;
    }
    .result-value {
        color: #e8e8e8;
        text-align: right;
        flex: 1;
        word-break: break-all;
    }
    .mono {
        font-family: 'Courier New', Courier, monospace;
        font-size: 1.05em;
    }
    .comment-row {
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid #333;
        color: #bdbdbd;
        font-style: italic;
    }
    .serial-panel {
        background: #202020;
        border-left: 1px solid #333;
        padding: 16px 12px;
        min-width: 260px;
        flex-shrink: 0;
    }
    .serial-title {
        color: #ffca28;
        font-size: 1.1em;
        font-weight: 600;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .serial-value {
        color: #e0e0e0;
        font-family: 'Courier New', monospace;
        font-size: 1.05em;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)

# ─── HELPERS ───────────────────────────────────────────────────────────────────
def norm_text(s):
    return (s or "").strip().upper()

def norm_immat(s):
    return re.sub(r"[^A-Z0-9]", "", norm_text(s))

def is_blank(x):
    return norm_text(str(x)) in ("", "NAN", "NONE", "NULL", "(VIDE)")

def clean_serial(v):
    s = ("" if v is None else str(v)).strip()
    s = re.sub(r"\s+", " ", s).strip()
    return "" if is_blank(s) else s

def clean_comment(v):
    s = ("" if v is None else str(v)).strip()
    return "" if is_blank(s) else s

SERIAL_COLS = ["N° SERIE", "N° SERIE GRUE"]

# ─── DATA ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_excel("PARC RZB (version 1).xlsx", sheet_name="Feuil2", header=2)
    df.columns = [str(c).strip() for c in df.columns]

    rename_map = {
        "N° DE PARC HME": "PARC_HME",
        "N° PARC RZB": "PARC_RZB",
        "Libellé": "LIBELLE",
        "LIBELLE": "LIBELLE",
        "COMMENTAIRE": "COMMENTAIRE",
        "Commentaire": "COMMENTAIRE",
        "Commentaires": "COMMENTAIRE",
        "COMMENTAIRES": "COMMENTAIRE",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

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
        df["LIBELLE"] = df["LIBELLE"].astype(str).str.strip()
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
    df = df[~df["PARC_HME"].map(is_blank)].copy()
    return df

df = load_data()

# ─── SEARCH ────────────────────────────────────────────────────────────────────
def search(df_, query):
    q_raw = norm_text(query)
    if not q_raw:
        return df_.iloc[0:0].copy()

    q_immat = norm_immat(q_raw)
    tokens = [t for t in re.split(r"\s+", q_raw) if t]
    mask = pd.Series(True, index=df_.index)

    for tok in tokens:
        tok_i = norm_immat(tok)
        one = (
            df_["PARC_HME"].str.contains(tok, na=False, regex=False) |
            df_["PARC_RZB"].str.contains(tok, na=False, regex=False) |
            df_["IMMATRICULATION"].str.contains(tok, na=False, regex=False) |
            df_["AGENCE"].astype(str).str.upper().str.contains(tok, na=False, regex=False) |
            df_["LIBELLE"].astype(str).str.upper().str.contains(tok, na=False, regex=False) |
            df_["COMMENTAIRE"].astype(str).str.upper().str.contains(tok, na=False, regex=False)
        )
        if tok_i:
            one = one | df_["IMM_NORM"].str.contains(tok_i, na=False, regex=False)
        mask = mask & one

    return df_[mask].copy()

# ─── RENDER HELPERS ────────────────────────────────────────────────────────────
def render_result(row, query):
    # ... (la logique de matched_hme / matched_rzb / big_code / big_tag reste identique)

    immat   = row.get("IMMATRICULATION", "").strip() or ""
    com     = clean_comment(row.get("COMMENTAIRE", "")).strip()
    libelle = (row.get("LIBELLE", "") or "").strip()
    agence  = (row.get("AGENCE", "") or "").strip()
    hme_val = row.get("PARC_HME", "").strip()
    rzb_val = row.get("PARC_RZB", "").strip()

    html = f'''
<div class="result-card">
    <div class="result-header">{big_tag}</div>
    <div class="big-code">{big_code}</div>
    
    <div style="display: flex;">
        <div class="main-content" style="flex: 1;">
            <div class="result-row">
                <span class="result-label">HME</span>
                <span class="result-value mono">{hme_val}</span>
            </div>
            <div class="result-row">
                <span class="result-label">RZB</span>
                <span class="result-value mono">{rzb_val}</span>
            </div>
            {f'<div class="result-row"><span class="result-label">IMMATRICULATION</span><span class="result-value">{immat}</span></div>' if immat else ''}
            {f'<div class="result-row"><span class="result-label">AGENCE</span><span class="result-value">{agence}</span></div>' if agence else ''}
            {f'<div class="result-row"><span class="result-label">LIBELLÉ</span><span class="result-value">{libelle}</span></div>' if libelle else ''}
            {f'<div class="comment-row">💬 {com}</div>' if com else ''}
        </div>
        
        <div class="serial-panel">
            {render_serial_content(row)}
        </div>
    </div>
</div>
    '''
    st.markdown(html, unsafe_allow_html=True)


def render_serial_content(row):
    s1 = clean_serial(row.get("N° SERIE", ""))
    s2 = clean_serial(row.get("N° SERIE GRUE", ""))

    if not s1 and not s2:
        return '<div class="serial-value" style="color:#888;">Aucun numéro enregistré</div>'

    lines = []
    if s1:
        lines.append(f'<div class="serial-value">{s1}</div>')
    if s2:
        lines.append(f'<div class="serial-value">{s2}</div>')

    return f'''
<div class="serial-title">NUMÉROS DE SÉRIE</div>
{''.join(lines)}
    '''


# Dans le code principal, quand tu appelles :
c1, c2 = st.columns([3.8, 1.4], gap=20)
with c1:
    render_result(chosen, query)
# Pas besoin d'appeler render_serial séparément → intégré dans render_result



def show_table_with_select(res, filename, key):
    cols = ["AGENCE","PARC_HME","PARC_RZB","IMMATRICULATION","LIBELLE","COMMENTAIRE"]
    cols = [c for c in cols if c in res.columns]
    st.markdown('Cliquez une ligne pour la détailler', unsafe_allow_html=True)
    event = st.dataframe(
        res[cols],
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun",
        key=key
    )
    csv = res[cols].to_csv(index=False, sep=";").encode("utf-8")
    st.download_button("⬇ Exporter CSV", data=csv, file_name=filename, mime="text/csv", key=f"dl_{key}")
    selected_pos = None
    try:
        if event and hasattr(event, "selection") and event.selection:
            rows = getattr(event.selection, "rows", None)
            if rows:
                selected_pos = rows[0]
    except Exception:
        pass
    return selected_pos

# ─── HEADER ────────────────────────────────────────────────────────────────────
n_agences = df["AGENCE"].nunique()
n_engins  = len(df)

st.markdown(f"""
<div class="app-header">
    <div class="app-title">Parc <span class="dot-orange">HME</span> ↔ RZB</div>
    <div class="app-subtitle">{n_engins} engins · {n_agences} agences</div>
</div>
""", unsafe_allow_html=True)

# ─── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["RECHERCHE", "MULTI-RECHERCHE"])

# ══════════════════════════════════════════════════════════════
with tab1:
    if "last_query" not in st.session_state:
        st.session_state["last_query"] = ""

    with st.form("search_form", clear_on_submit=True):
        col_inp, col_btn = st.columns([6, 1])
        with col_inp:
            q_input = st.text_input(
                " ",
                placeholder="Ex : H01100M · X001L · AB-123-CD · pelle bassin",
                label_visibility="collapsed",
                key="q_simple"
            )
        with col_btn:
            go = st.form_submit_button("Chercher", use_container_width=True)

    st.markdown("""
    <div class="hint-row">
        <span class="hint-chip">HME → commence par H</span>
        <span class="hint-chip">RZB → commence par X ou P</span>
        <span class="hint-chip">Immatriculation</span>
        <span class="hint-chip">Mots-clés libres</span>
    </div>
    """, unsafe_allow_html=True)

    if go and q_input.strip():
        st.session_state["last_query"] = q_input.strip()

    query = st.session_state["last_query"]

    if query:
        res = search(df, query)
        if res.empty:
            st.markdown(f"""
            <div class="no-result">
                Aucun résultat pour <span>«&nbsp;{query}&nbsp;»</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            if len(res) == 1:
                chosen = res.iloc[0]
                c1, c2 = st.columns([2.5, 1.2], gap="large")
                with c1:
                    render_result(chosen, query)
                with c2:
                    render_serial(chosen)
            else:
                st.markdown(f'<div class="section-label">{len(res)} résultats trouvés</div>', unsafe_allow_html=True)
                sel = show_table_with_select(res, "resultats.csv", key="tbl_simple")
                chosen = res.iloc[sel] if sel is not None else None

                if chosen is not None:
                    st.markdown("---")
                    c1, c2 = st.columns([2.5, 1.2], gap="large")
                    with c1:
                        render_result(chosen, query)
                    with c2:
                        render_serial(chosen)

# ══════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-label">Une entrée par ligne (code HME, RZB, immat ou mots-clés)</div>', unsafe_allow_html=True)

    raw = st.text_area(" ", height=180,
        placeholder="H01100M\nX001L\nAB-123-CD\npelle bassin",
        label_visibility="collapsed",
        key="multi_input"
    )

    if raw.strip():
        items = list(dict.fromkeys([x.strip() for x in raw.splitlines() if x.strip()]))
        all_res = []
        for it in items:
            r = search(df, it)
            if not r.empty:
                rr = r.copy()
                rr.insert(0, "RECHERCHE", it)
                all_res.append(rr)

        if not all_res:
            st.markdown('Aucun résultat pour la liste fournie', unsafe_allow_html=True)
        else:
            out = pd.concat(all_res, ignore_index=True)
            not_found = [it for it in items if it not in out["RECHERCHE"].values]
            cols_show = ["RECHERCHE","AGENCE","PARC_HME","PARC_RZB","IMMATRICULATION","LIBELLE","COMMENTAIRE"]
            cols_show = [c for c in cols_show if c in out.columns]
            # Stats
            st.markdown(f"""{len(items)}Recherches·{len(items)-len(not_found)}Trouvées·{len(out)}Lignes{"·" + str(len(not_found)) + "Non trouvées" if not_found else ""}            """, unsafe_allow_html=True)
            if not_found:
                with st.expander(f"⚠ {len(not_found)} entrée(s) sans résultat"):
                    for x in not_found:
                        st.markdown(f"`{x}`")
            st.dataframe(out[cols_show], use_container_width=True, hide_index=True)

            csv = out[cols_show].to_csv(index=False, sep=";").encode("utf-8")
            st.download_button("⬇ Exporter CSV", data=csv, file_name="multi_resultats.csv", mime="text/csv")
