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
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; }

.stApp {
    background: #0d0d0d;
    color: #e8e8e0;
    font-family: 'Syne', sans-serif;
}

/* Supprimer les marges superflues */
.block-container { padding-top: 2rem !important; padding-bottom: 3rem !important; }

/* Header */
.app-header {
    display: flex;
    align-items: baseline;
    gap: 18px;
    margin-bottom: 2.5rem;
    border-bottom: 1px solid #2a2a2a;
    padding-bottom: 1.2rem;
}
.app-title {
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: #e8e8e0;
}
.app-subtitle {
    font-size: 0.9rem;
    color: #555;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.5px;
}
.dot-orange { color: #e8601a; }

/* Input */
.stTextInput > div > div > input {
    background: #141414 !important;
    border: 1px solid #252525 !important;
    border-radius: 6px !important;
    color: #e8e8e0 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 1rem !important;
    padding: 0.7rem 1rem !important;
    transition: border-color 0.2s;
}
.stTextInput > div > div > input:focus {
    border-color: #e8601a !important;
    box-shadow: 0 0 0 2px rgba(232,96,26,0.1) !important;
}

/* Bouton */
.stButton > button {
    background: #e8601a !important;
    color: #0d0d0d !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    padding: 0.65rem 1.8rem !important;
    letter-spacing: 0.5px !important;
    transition: opacity 0.15s !important;
    cursor: pointer !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* Carte résultat principal */
.result-card {
    background: #111;
    border: 1px solid #1e1e1e;
    border-radius: 12px;
    padding: 2rem;
    position: relative;
    overflow: hidden;
}
.result-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #e8601a, #f7b500);
}
.result-tag {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #e8601a;
    background: rgba(232,96,26,0.08);
    border: 1px solid rgba(232,96,26,0.3);
    padding: 3px 10px;
    border-radius: 99px;
    margin-bottom: 14px;
}
.result-main-code {
    font-family: 'DM Mono', monospace;
    font-size: 3.2rem;
    font-weight: 500;
    color: #f7b500;
    letter-spacing: 1px;
    line-height: 1;
    margin-bottom: 1.5rem;
}
.result-row {
    display: flex;
    gap: 12px;
    margin-bottom: 10px;
    align-items: baseline;
}
.result-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #444;
    min-width: 120px;
    flex-shrink: 0;
}
.result-value {
    font-size: 0.95rem;
    color: #c8c8c0;
}
.result-value.mono {
    font-family: 'DM Mono', monospace;
    color: #e8e8e0;
}
.result-comment {
    margin-top: 1rem;
    padding: 0.8rem 1rem;
    background: rgba(255,255,255,0.025);
    border-left: 2px solid rgba(232,96,26,0.5);
    border-radius: 0 4px 4px 0;
    font-size: 0.9rem;
    color: #999;
    font-style: italic;
}

/* Carte série */
.serie-card {
    background: #111;
    border: 1px solid #1e1e1e;
    border-radius: 12px;
    padding: 1.6rem;
    height: 100%;
}
.serie-card-title {
    font-size: 0.7rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #444;
    margin-bottom: 1.2rem;
    font-family: 'DM Mono', monospace;
}
.serie-block { margin-bottom: 1.2rem; }
.serie-block-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #444;
    margin-bottom: 5px;
}
.serie-block-value {
    font-family: 'DM Mono', monospace;
    font-size: 0.92rem;
    color: #e8e8e0;
    word-break: break-all;
}
.serie-empty {
    color: #333;
    font-size: 0.88rem;
    font-style: italic;
}
.serie-divider {
    height: 1px;
    background: #1e1e1e;
    margin: 1rem 0;
}

/* Stats bar */
.stats-bar {
    display: flex;
    gap: 24px;
    margin-bottom: 1.5rem;
    padding: 1rem 1.2rem;
    background: #111;
    border: 1px solid #1e1e1e;
    border-radius: 8px;
    align-items: center;
    flex-wrap: wrap;
}
.stat-item { text-align: center; }
.stat-value {
    font-family: 'DM Mono', monospace;
    font-size: 1.3rem;
    font-weight: 500;
    color: #f7b500;
}
.stat-label {
    font-size: 0.68rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #444;
    margin-top: 2px;
}
.stat-sep { color: #222; font-size: 1.5rem; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #1e1e1e !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #555 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    letter-spacing: 1px !important;
    padding: 0.7rem 1.5rem !important;
    border-radius: 0 !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.15s !important;
}
.stTabs [aria-selected="true"] {
    color: #e8601a !important;
    border-bottom: 2px solid #e8601a !important;
}

/* Tableau */
[data-testid="stDataFrame"] {
    border: 1px solid #1e1e1e !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* Hint chips */
.hint-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 1.2rem;
}
.hint-chip {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: #555;
    background: #141414;
    border: 1px solid #252525;
    padding: 3px 10px;
    border-radius: 99px;
}

/* Error / success */
.stAlert { border-radius: 8px !important; }

/* Section label */
.section-label {
    font-size: 0.68rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #444;
    margin-bottom: 0.8rem;
    font-family: 'DM Mono', monospace;
}

/* No result */
.no-result {
    text-align: center;
    padding: 3rem 1rem;
    color: #333;
    font-size: 1.2rem;
}
.no-result span { color: #e8601a; }

/* Download button */
.stDownloadButton > button {
    background: transparent !important;
    color: #e8601a !important;
    border: 1px solid rgba(232,96,26,0.4) !important;
    border-radius: 6px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.8rem !important;
    padding: 0.5rem 1.2rem !important;
}
.stDownloadButton > button:hover {
    border-color: #e8601a !important;
    background: rgba(232,96,26,0.05) !important;
}

/* Text area */
.stTextArea textarea {
    background: #141414 !important;
    border: 1px solid #252525 !important;
    border-radius: 6px !important;
    color: #e8e8e0 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.9rem !important;
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
    q = norm_text(query)
    q_immat = norm_immat(q)
    hme = norm_text(row.get("PARC_HME", ""))
    rzb = norm_text(row.get("PARC_RZB", ""))
    # La query matche-t-elle le champ HME ?
    matched_hme = q in hme or (q_immat and q_immat in norm_immat(hme))
    # La query matche-t-elle le champ RZB ?
    matched_rzb = q in rzb or (q_immat and q_immat in norm_immat(rzb))
    if matched_hme:
        # On a cherché par HME → on affiche le RZB en gros
        big_code, big_tag = row.get("PARC_RZB", ""), "→ N° PARC RZB"
    elif matched_rzb:
        # On a cherché par RZB → on affiche le HME en gros
        big_code, big_tag = row.get("PARC_HME", ""), "→ N° PARC HME"
    else:
        # Recherche par mot-clé (libellé, agence…) → on affiche le RZB par défaut
        big_code, big_tag = row.get("PARC_RZB", ""), "→ N° PARC RZB"
    immat = "" if is_blank(row.get("IMMATRICULATION", "")) else row.get("IMMATRICULATION", "")
    com = clean_comment(row.get("COMMENTAIRE", "")).replace("<", "&lt;").replace(">", "&gt;")
    libelle = (row.get("LIBELLE", "") or "").replace("<", "&lt;").replace(">", "&gt;")
    agence = (row.get("AGENCE", "") or "").replace("<", "&lt;").replace(">", "&gt;")
    parc_hme = norm_text(row.get("PARC_HME", ""))
    parc_rzb = norm_text(row.get("PARC_RZB", ""))
    
    html_parts = []
    html_parts.append(f'<div class="big-tag">{big_tag}</div>')
    html_parts.append(f'<div class="big-code">{big_code}</div>')
    
    if parc_hme:
        html_parts.append('<div class="result-row">')
        html_parts.append('<span class="result-label">HME</span>')
        html_parts.append(f'<span class="result-value">{parc_hme}</span>')
        html_parts.append('</div>')
    
    if parc_rzb:
        html_parts.append('<div class="result-row">')
        html_parts.append('<span class="result-label">RZB</span>')
        html_parts.append(f'<span class="result-value">{parc_rzb}</span>')
        html_parts.append('</div>')
    
    if immat:
        html_parts.append('<div class="result-row">')
        html_parts.append('<span class="result-label">Immatriculation</span>')
        html_parts.append(f'<span class="result-value">{immat}</span>')
        html_parts.append('</div>')
    
    if agence:
        html_parts.append('<div class="result-row">')
        html_parts.append('<span class="result-label">Agence</span>')
        html_parts.append(f'<span class="result-value">{agence}</span>')
        html_parts.append('</div>')
    
    if libelle:
        html_parts.append('<div class="result-row">')
        html_parts.append('<span class="result-label">Libellé</span>')
        html_parts.append(f'<span class="result-value">{libelle}</span>')
        html_parts.append('</div>')
    
    if com:
        html_parts.append(f'<div class="result-comment">💬 {com}</div>')
    
    html = ''.join(html_parts)
    st.markdown(html, unsafe_allow_html=True)

def render_serial(row):
    s1 = clean_serial(row.get("N° SERIE", ""))
    s2 = clean_serial(row.get("N° SERIE GRUE", ""))
    if not s1 and not s2:
        st.markdown("""
Numéros de série
Aucun numéro enregistré
        """, unsafe_allow_html=True)
        return
    
    html_parts = ['<div class="result-row"><span class="result-label">Numéros de série</span></div>']
    
    if s1:
        html_parts.append('<div class="result-row">')
        html_parts.append('<span class="result-label">N° Série</span>')
        html_parts.append(f'<span class="result-value">{s1}</span>')
        html_parts.append('</div>')
    
    if s2:
        html_parts.append('<div class="result-row">')
        html_parts.append('<span class="result-label">N° Série Grue</span>')
        html_parts.append(f'<span class="result-value">{s2}</span>')
        html_parts.append('</div>')
    
    html = ''.join(html_parts)
    st.markdown(html, unsafe_allow_html=True)

def show_table_with_select(res, filename, key):
    cols = ["AGENCE","PARC_HME","PARC_RZB","IMMATRICULATION","LIBELLE","COMMENTAIRE"]
    cols = [c for c in cols if c in res.columns]
    st.markdown('Cliquez une ligne pour la détailler', unsafe_allow_html=True)
    event = st.dataframe(a        res[cols],        use_container_width=True,        hide_index=True,        selection_mode="single-row",        on_select="rerun",        key=key    )
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
