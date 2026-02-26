import streamlit as st
import pandas as pd
import re

st.set_page_config(
    page_title="Parc HME ↔ RZB",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── STYLES ────────────────────────────────────────────────────────────────────
# (on garde exactement le même style que dans ta version originale)
st.markdown("""
<style>
    .result-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
    }
    .result-label {
        font-weight: bold;
        color: #888;
    }
    .result-value {
        text-align: right;
    }
    .result-comment {
        color: #555;
        font-style: italic;
        margin-top: 10px;
    }
    .big-code {
        font-size: 2em;
        font-weight: bold;
    }
    .big-tag {
        color: #666;
        font-size: 1.2em;
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
        "COMMENTAIRE": "COMMENTAIRE",
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
    matched_hme = q in hme or (q_immat and q_immat in norm_immat(hme))
    matched_rzb = q in rzb or (q_immat and q_immat in norm_immat(rzb))
    
    if matched_hme:
        big_code, big_tag = row.get("PARC_RZB", ""), "→ N° PARC RZB"
    elif matched_rzb:
        big_code, big_tag = row.get("PARC_HME", ""), "→ N° PARC HME"
    else:
        big_code, big_tag = row.get("PARC_RZB", ""), "→ N° PARC RZB"
    
    immat = "" if is_blank(row.get("IMMATRICULATION", "")) else row.get("IMMATRICULATION", "")
    com = clean_comment(row.get("COMMENTAIRE", "")).replace("<","<").replace(">","")
    libelle = (row.get("LIBELLE","") or "").replace("<","<").replace(">","")
    agence = (row.get("AGENCE","") or "").replace("<","<").replace(">","")
    parc_hme = norm_text(row.get("PARC_HME",""))
    parc_rzb = norm_text(row.get("PARC_RZB",""))
    
    immat_html = f'''
<div class="result-row">
    <span class="result-label">Immatriculation</span>
    <span class="result-value">{immat}</span>
</div>
''' if immat else ""
    
    com_html = f'''
<div class="result-comment"> 💬 {com}</div>
''' if com else ""
    
    html = f'''
<div class="big-tag">{big_tag}</div>
<div class="big-code">{big_code}</div>
<div class="result-row">
    <span class="result-label">HME</span>
    <span class="result-value">{parc_hme}</span>
</div>
<div class="result-row">
    <span class="result-label">RZB</span>
    <span class="result-value">{parc_rzb}</span>
</div>
{immat_html}
<div class="result-row">
    <span class="result-label">Agence</span>
    <span class="result-value">{agence}</span>
</div>
<div class="result-row">
    <span class="result-label">Libellé</span>
    <span class="result-value">{libelle}</span>
</div>
{com_html}
    '''
    st.markdown(html, unsafe_allow_html=True)

def render_serial(row):
    s1 = clean_serial(row.get("N° SERIE", ""))
    s2 = clean_serial(row.get("N° SERIE GRUE", ""))
    if not s1 and not s2:
        st.markdown("""<div class="result-row">    <span class="result-label">Numéros de série</span>    <span class="result-value">Aucun numéro enregistré</span></div>        """, unsafe_allow_html=True)
        return
    
    html = ""
    if s1:
        html += f'''
<div class="result-row">
    <span class="result-label">N° Série</span>
    <span class="result-value">{s1}</span>
</div>
'''
    if s2:
        html += f'''
<div class="result-row">
    <span class="result-label">N° Série Grue</span>
    <span class="result-value">{s2}</span>
</div>
'''
    st.markdown(f'''<div class="result-row">    <span class="result-label">Numéros de série</span></div>{html}    ''', unsafe_allow_html=True)

def show_table_with_select(res, filename, key):
    cols = ["AGENCE","PARC_HME","PARC_RZB","IMMATRICULATION","LIBELLE","COMMENTAIRE"]
    cols = [c for c in cols if c in res.columns]
    
    st.markdown('''Cliquez une ligne pour la détailler    ''', unsafe_allow_html=True)
    
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
n_engins = len(df)
st.markdown(f"""**Parc HME ↔ RZB**  {n_engins} engins · {n_agences} agences""", unsafe_allow_html=True)

# ─── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["RECHERCHE", "MULTI-RECHERCHE"])

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
    
    st.markdown("""HME → commence par H  RZB → commence par X ou P  Immatriculation  Mots-clés libres    """)
    
    if go and q_input.strip():
        st.session_state["last_query"] = q_input.strip()
    
    query = st.session_state["last_query"]
    if query:
        res = search(df, query)
        if res.empty:
            st.markdown(f"""**Aucun résultat pour « {query} »**            """)
        else:
            if len(res) == 1:
                chosen = res.iloc[0]
                c1, c2 = st.columns([2.5, 1.2], gap="large")
                with c1:
                    render_result(chosen, query)
                with c2:
                    render_serial(chosen)
            else:
                st.markdown(f"**{len(res)} résultats trouvés**")
                sel = show_table_with_select(res, "resultats.csv", key="tbl_simple")
                if sel is not None:
                    chosen = res.iloc[sel]
                    st.markdown("---")
                    c1, c2 = st.columns([2.5, 1.2], gap="large")
                    with c1:
                        render_result(chosen, query)
                    with c2:
                        render_serial(chosen)

with tab2:
    st.markdown("""Une entrée par ligne (code HME, RZB, immat ou mots-clés)    """)
    
    raw = st.text_area(" ", height=180, placeholder="H01100M\nX001L\nAB-123-CD\npelle bassin", label_visibility="collapsed", key="multi_input")
    
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
            st.markdown("**Aucun résultat pour la liste fournie**")
        else:
            out = pd.concat(all_res, ignore_index=True)
            not_found = [it for it in items if it not in out["RECHERCHE"].values]
            cols_show = ["RECHERCHE","AGENCE","PARC_HME","PARC_RZB","IMMATRICULATION","LIBELLE","COMMENTAIRE"]
            cols_show = [c for c in cols_show if c in out.columns]
            
            st.markdown(f"""**{len(items)}** Recherches  **{len(items)-len(not_found)}** Trouvées  **{len(out)}** Lignes  {"**" + str(len(not_found)) + "** Non trouvées" if not_found else ""}            """)
            
            if not_found:
                with st.expander(f"⚠ {len(not_found)} entrée(s) sans résultat"):
                    for x in not_found:
                        st.markdown(f"`{x}`")
            
            st.dataframe(out[cols_show], use_container_width=True, hide_index=True)
            
            csv = out[cols_show].to_csv(index=False, sep=";").encode("utf-8")
            st.download_button("⬇ Exporter CSV", data=csv, file_name="multi_resultats.csv", mime="text/csv")
