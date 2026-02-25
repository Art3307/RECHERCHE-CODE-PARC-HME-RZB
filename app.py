-import streamlit as st
-import pandas as pd
-import re
+import streamlit as st
+import pandas as pd
+import re
+import json
+import streamlit.components.v1 as components
 
 st.set_page_config(
     page_title="Recherche Parc HME ↔ RZB",
     layout="centered",
     initial_sidebar_state="collapsed"  # ✅ options masquées par défaut
 )
 st.title("🔎 Recherche Parc : HME ↔ RZB")
 
 # ----------------------------
 # STYLE (fond noir + liseré orange)
 # ----------------------------
 st.markdown("""
 <style>
 /* Fond global */
 .stApp {
     background: #0b0b0b;
     color: #f2f2f2;
 }
 
 /* Inputs / widgets plus lisibles */
 .stTextInput input, .stTextArea textarea {
     background: #121212 !important;
     color: #f2f2f2 !important;
     border: 1px solid rgba(255,165,0,.35) !important;
 }
@@ -115,54 +117,101 @@ st.markdown("""
 }
 
 /* Dataframe look sombre */
 [data-testid="stDataFrame"] {
     border: 1px solid rgba(255,165,0,.35);
     border-radius: 12px;
     overflow: hidden;
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
     return x in ("", "NAN", "NONE", "NULL")
 
-def clean_serial(v) -> str:
+def clean_serial(v) -> str:
     s = norm_text("" if v is None else str(v))
     s = re.sub(r"\s+", " ", s).strip()
-    return "" if is_blank(s) else s
+    return "" if is_blank(s) else s
+
+
+def render_copy_button(value: str, key: str):
+    """Affiche un bouton de copie (presse-papiers navigateur)."""
+    value = "" if value is None else str(value)
+    button_id = re.sub(r"[^a-zA-Z0-9_-]", "_", key)
+    payload = json.dumps(value)
+
+    components.html(
+        f"""
+        <div style="display:flex;justify-content:flex-end;">
+          <button id="{button_id}" style="
+            background:#141414;
+            color:#f2f2f2;
+            border:1px solid rgba(255,165,0,.55);
+            border-radius:10px;
+            padding:8px 10px;
+            cursor:pointer;
+            width:100%;
+          ">📋 Copier</button>
+        </div>
+        <script>
+          const btn = document.getElementById('{button_id}');
+          btn.addEventListener('click', async () => {{
+            try {{
+              await navigator.clipboard.writeText({payload});
+              const old = btn.innerText;
+              btn.innerText = '✅ Copié';
+              setTimeout(() => btn.innerText = old, 1200);
+            }} catch (e) {{
+              btn.innerText = '❌ Refusé';
+              setTimeout(() => btn.innerText = '📋 Copier', 1200);
+            }}
+          }});
+        </script>
+        """,
+        height=48,
+    )
+
+
+def render_copyable_row(label: str, value: str, key: str):
+    left, right = st.columns([4, 1.2], vertical_alignment="bottom")
+    with left:
+        st.caption(label)
+        st.code(value if value else "—", language=None)
+    with right:
+        render_copy_button(value, key)
 
 SERIAL_COLS = ["N° SERIE", "N° SERIE GRUE"]
 
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
 
     if "AGENCE" in df.columns:
         df["AGENCE"] = df["AGENCE"].ffill()
 
@@ -244,78 +293,92 @@ def render_series_side(row: pd.Series):
         return
 
     html = f"""
     <div class="series-card">
       <div class="series-title">🔧 Numéros de série</div>
 
       <div class="series-row">
         <div class="series-label">N° SERIE :</div>
         <div class="series-value" style="margin-top:6px;">
             {s1 if s1 else "—"}
         </div>
       </div>
 
       <div class="series-row" style="margin-top:18px;">
         <div class="series-label">N° SERIE GRUE :</div>
         <div class="series-value" style="margin-top:6px;">
             {s2 if s2 else "—"}
         </div>
       </div>
 
     </div>
     """
 
     st.markdown(html, unsafe_allow_html=True)
 
-def render_big_card(row: pd.Series, user_query: str):
+def render_big_card(row: pd.Series, user_query: str):
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
 
-    st.markdown(f"""
+    st.markdown(f"""
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
-    </div>
-    """, unsafe_allow_html=True)
+    </div>
+    """, unsafe_allow_html=True)
+
+    st.markdown("#### 📎 Copier un élément")
+    copy_items = [
+        (f"Code affiché ({big_label})", big_value),
+        ("HME", row.get("PARC_HME", "")),
+        ("RZB", row.get("PARC_RZB", "")),
+        ("Immatriculation", immat),
+        ("Agence", row.get("AGENCE", "")),
+        ("Libellé", row.get("LIBELLE", "")),
+        ("N° SERIE", clean_serial(row.get("N° SERIE", ""))),
+        ("N° SERIE GRUE", clean_serial(row.get("N° SERIE GRUE", ""))),
+    ]
+    for idx, (label, value) in enumerate(copy_items):
+        render_copyable_row(label, "" if value is None else str(value), f"copy_{idx}_{row.get('PARC_HME','')}_{row.get('PARC_RZB','')}")
 
 def results_table_with_selection(res: pd.DataFrame, filename: str, key: str):
     cols = ["AGENCE", "PARC_HME", "PARC_RZB", "IMMATRICULATION", "LIBELLE"]
 
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
@@ -358,26 +421,26 @@ with tab2:
     st.code("H01100M\nX001L\nAB-123-CD\npelle bassin", language="text")
 
     raw_list = st.text_area("Liste", height=180, placeholder="1 entrée par ligne…")
     if raw_list.strip():
         items = [norm_text(x) for x in raw_list.splitlines() if norm_text(x)]
         items = list(dict.fromkeys(items))
 
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
             cols = ["RECHERCHE", "AGENCE", "PARC_HME", "PARC_RZB", "IMMATRICULATION", "LIBELLE"]
             st.dataframe(out[cols], use_container_width=True, hide_index=True)
 
             csv = out[cols].to_csv(index=False, sep=";").encode("utf-8")
-            st.download_button("⬇️ Télécharger (CSV)", data=csv, file_name="multi_resultats_parc.csv", mime="text/csv")
\ No newline at end of file
+            st.download_button("⬇️ Télécharger (CSV)", data=csv, file_name="multi_resultats_parc.csv", mime="text/csv")

