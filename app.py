import streamlit as st
import sqlite3
import sys
import os
import plotly.graph_objects as go
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.crear_base_dades import crear_base_dades
from core.motor import MotorSimulacio
from ia.groq_agent import AgentIA

DB_PATH = "simulador.db"

st.set_page_config(
    page_title="EcoSim — Simulador d'Ecosistemes",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #080d1a; color: #c9d4e8; }
section[data-testid="stSidebar"] { background: #0d1424 !important; border-right: 1px solid #1e2d4a; }
section[data-testid="stSidebar"] * { color: #8fa3c4 !important; }
h1 { font-family:'Space Mono',monospace !important; color:#e8f4fd !important; font-size:1.8rem !important; letter-spacing:-1px; }
h2 { font-family:'Space Mono',monospace !important; color:#7dd3fc !important; font-size:1.2rem !important; }
h3 { color:#94b8d8 !important; font-weight:500 !important; }
.sim-card { background:#0d1829; border:1px solid #1e3050; border-radius:12px; padding:20px 24px; margin-bottom:16px; }
.sim-card-green { background:linear-gradient(135deg,#071a10 0%,#0d2218 100%); border:1px solid #1a4a2e; border-radius:12px; padding:20px 24px; margin-bottom:16px; }
.sim-card-amber { background:linear-gradient(135deg,#1a1200 0%,#1f1800 100%); border:1px solid #3d2e00; border-radius:12px; padding:20px 24px; margin-bottom:16px; }
.metric-box { background:#0d1829; border:1px solid #1e3050; border-radius:10px; padding:14px 18px; text-align:center; }
.metric-value { font-family:'Space Mono',monospace; font-size:1.6rem; color:#38bdf8; font-weight:700; line-height:1.2; }
.metric-label { font-size:0.75rem; color:#4a6a8a; text-transform:uppercase; letter-spacing:0.08em; margin-top:4px; }
.metric-unit { font-size:0.75rem; color:#2d7ab0; font-family:'Space Mono',monospace; }
.tag { display:inline-block; padding:2px 10px; border-radius:20px; font-size:0.7rem; font-weight:600; letter-spacing:0.05em; text-transform:uppercase; }
.tag-green { background:#0a2e18; color:#34d399; border:1px solid #0f4a28; }
.tag-blue  { background:#071830; color:#60a5fa; border:1px solid #0f2d5a; }
.tag-amber { background:#1f1000; color:#fbbf24; border:1px solid #3d2200; }
.tag-red   { background:#1f0a0a; color:#f87171; border:1px solid #3d1515; }
.rel-row { display:flex; align-items:center; gap:10px; padding:6px 0; border-bottom:1px solid #111d30; font-size:0.85rem; }
.rel-origen { color:#60a5fa; font-weight:500; }
.rel-desti  { color:#34d399; font-weight:500; }
.rel-pes-pos { color:#34d399; font-family:'Space Mono',monospace; font-size:0.8rem; }
.rel-pes-neg { color:#f87171; font-family:'Space Mono',monospace; font-size:0.8rem; }
.rel-desc   { color:#4a6a8a; font-size:0.8rem; }
.esc-card { background:#0d1829; border:1px solid #1e3050; border-radius:10px; padding:16px 20px; margin-bottom:10px; }
.esc-nom  { font-size:1rem; font-weight:600; color:#c9d4e8; }
.esc-tema { font-size:0.8rem; color:#4a6a8a; margin-top:2px; }
.esc-meta { font-size:0.75rem; color:#2d5a8a; margin-top:6px; font-family:'Space Mono',monospace; }
.sidebar-logo { font-family:'Space Mono',monospace; font-size:1.3rem; color:#38bdf8 !important; font-weight:700; }
.sidebar-sub  { font-size:0.7rem; color:#2d5a8a !important; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:20px; }
.stTextInput input, .stTextArea textarea, .stNumberInput input { background:#0d1829 !important; border:1px solid #1e3050 !important; color:#c9d4e8 !important; border-radius:8px !important; }
.stTextInput label, .stTextArea label, .stNumberInput label, .stSelectbox label, .stSlider label, .stRadio label, .stMultiSelect label { color:#a8c0d8 !important; font-size:0.9rem !important; font-weight:500 !important; }
.stSelectbox > div > div { background:#0d1829 !important; border:1px solid #1e3050 !important; color:#c9d4e8 !important; }
.stButton > button { background:#0f2d50 !important; color:#60a5fa !important; border:1px solid #1e4a7a !important; border-radius:8px !important; font-weight:500 !important; }
.stButton > button:hover { background:#1a4a80 !important; }
.stButton > button[kind="primary"] { background:linear-gradient(135deg,#0f4a2e 0%,#1a6040 100%) !important; color:#34d399 !important; border:1px solid #1a5a38 !important; }
hr { border-color:#1e2d4a !important; margin:20px 0 !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

if not os.path.exists(DB_PATH):
    crear_base_dades(DB_PATH)


# =============================================================================
# FUNCIONS AUXILIARS
# =============================================================================

def _guardar_escenari_ia(nom, descripcio, unitat, num_passos, ei):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON;")
    cur.execute("INSERT INTO escenaris (nom,tema,descripcio,unitat_temps,num_passos) VALUES (?,?,?,?,?)",
                (nom, nom, descripcio, unitat, num_passos))
    eid  = cur.lastrowid
    vids = {}
    for v in ei.get('variables_fixes', []):
        cur.execute("INSERT INTO variables (escenari_id,nom,tipus_var,unitat,valor_inicial,valor_min,valor_max,notes) VALUES (?,?,'fixa',?,?,?,?,?)",
                    (eid,v['nom'],v.get('unitat',''),v['valor_inicial'],v.get('valor_min',0),v.get('valor_max',100),v.get('notes','')))
        vids[v['nom']] = cur.lastrowid
    for v in ei.get('variables_dinamiques', []):
        cur.execute("INSERT INTO variables (escenari_id,nom,tipus_var,unitat,valor_inicial,valor_min,valor_max,notes) VALUES (?,?,'dinamica',?,?,?,?,?)",
                    (eid,v['nom'],v.get('unitat',''),v['valor_inicial'],v.get('valor_min',0),v.get('valor_max',100),v.get('notes','')))
        vids[v['nom']] = cur.lastrowid
    vids_norm = {k.lower().strip(): v for k, v in vids.items()}
    for r in ei.get('relacions', []):
        orig = vids_norm.get(r['origen'].lower().strip())
        dest = vids_norm.get(r['desti'].lower().strip())
        if orig and dest:
            cur.execute("INSERT INTO relacions (escenari_id,variable_origen_id,variable_desti_id,pes,descripcio,generada_per_ia) VALUES (?,?,?,?,?,1)",
                        (eid,orig,dest,r['pes'],r.get('descripcio','')))
    conn.commit()
    conn.close()
    st.success(f"Escenari '{nom}' guardat!")
    st.session_state['escenari_actiu'] = eid
    if 'escenari_ia' in st.session_state:
        del st.session_state['escenari_ia']
    st.rerun()


def _guardar_escenari_assistit(cfg, pm):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON;")
    cur.execute("INSERT INTO escenaris (nom,tema,descripcio,unitat_temps,num_passos) VALUES (?,?,?,?,?)",
                (cfg['nom'], cfg['tema'], cfg['desc'], cfg['unitat'], cfg['passos']))
    eid  = cur.lastrowid
    vids = {}
    for v in pm.get('variables_fixes', []):
        cur.execute("INSERT INTO variables (escenari_id,nom,tipus_var,unitat,valor_inicial,valor_min,valor_max,notes) VALUES (?,?,'fixa',?,?,?,?,?)",
                    (eid,v['nom'],v.get('unitat',''),v['valor_inicial'],v.get('valor_min',0),v.get('valor_max',100),v.get('notes','')))
        vids[v['nom']] = cur.lastrowid
    for v in pm.get('variables_dinamiques', []):
        cur.execute("INSERT INTO variables (escenari_id,nom,tipus_var,unitat,valor_inicial,valor_min,valor_max,notes) VALUES (?,?,'dinamica',?,?,?,?,?)",
                    (eid,v['nom'],v.get('unitat',''),v['valor_inicial'],v.get('valor_min',0),v.get('valor_max',100),v.get('notes','')))
        vids[v['nom']] = cur.lastrowid
    vids_norm = {k.lower().strip(): v for k, v in vids.items()}
    for r in pm.get('relacions', []):
        orig = vids_norm.get(r['origen'].lower().strip())
        dest = vids_norm.get(r['desti'].lower().strip())
        if orig and dest:
            cur.execute("INSERT INTO relacions (escenari_id,variable_origen_id,variable_desti_id,pes,descripcio,generada_per_ia) VALUES (?,?,?,?,?,1)",
                        (eid,orig,dest,r['pes'],r.get('descripcio','')))
    conn.commit()
    conn.close()
    st.session_state['escenari_actiu'] = eid
    for k in ['proposta_manual','config_manual']:
        if k in st.session_state:
            del st.session_state[k]
    st.success("Escenari guardat!")
    st.rerun()


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown('<div class="sidebar-logo">🌍 EcoSim</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Simulador d\'ecosistemes</div>', unsafe_allow_html=True)
    st.markdown("---")
    seccio = st.radio("", [
        "🆕  Nou escenari",
        "📂  Escenaris",
        "✏️  Variables",
        "🎛️  Simulació",
        "📊  Gràfiques"
    ], label_visibility="collapsed")

    if 'escenari_actiu' in st.session_state:
        st.markdown("---")
        conn = sqlite3.connect(DB_PATH)
        cur  = conn.cursor()
        cur.execute("SELECT nom,estat FROM escenaris WHERE id=?", (st.session_state['escenari_actiu'],))
        row  = cur.fetchone()
        conn.close()
        if row:
            ecls = {"actiu":"tag-green","pausat":"tag-amber","finalitzat":"tag-red"}.get(row[1],"tag-blue")
            st.markdown(f"""<div style="padding:12px;background:#0d1829;border-radius:10px;border:1px solid #1e3050;">
                <div style="font-size:0.7rem;color:#2d5a8a;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">Escenari actiu</div>
                <div style="font-size:0.9rem;color:#c9d4e8;font-weight:500;">{row[0]}</div>
                <div style="margin-top:6px;"><span class="tag {ecls}">{row[1]}</span></div>
            </div>""", unsafe_allow_html=True)


# =============================================================================
# NOU ESCENARI
# =============================================================================

if "🆕" in seccio:
    # Netejar NOMÉS quan venim d'una altra secció
    if st.session_state.get('seccio_anterior','') != '🆕':
        for k in ['escenari_ia','tema_ia','proposta_manual','config_manual']:
            if k in st.session_state: del st.session_state[k]
    st.session_state['seccio_anterior'] = '🆕'

    st.markdown("# 🆕 Nou escenari")
    st.markdown("Crea una nova simulació en mode automàtic o assistit.")
    st.markdown("---")
    mode = st.radio("Selecciona el mode de creació", ["🤖  Automàtic (IA genera tot)","🔬  Assistit (tu controles, IA ajuda)"], horizontal=True)

    if "🤖" in mode:
        c1, c2 = st.columns([2,1])
        with c1:
            st.markdown("### Descriu el teu escenari")
            tema    = st.text_input("Tema de la simulació", placeholder="Ex: Bosc pirinenc afectat per la sequera...")
            context = st.text_area("Context addicional (opcional)", placeholder="Zona geogràfica, condicions especials...", height=80)
            gen     = st.button("🤖  Generar amb IA", type="primary", disabled=not tema)
        with c2:
            st.markdown('<div class="sim-card-green"><div style="font-size:0.75rem;color:#1a6040;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">Mode automàtic</div><div style="font-size:0.85rem;color:#5a9a78;line-height:1.6;">La IA genera automàticament variables, relacions i pesos científics.</div></div>', unsafe_allow_html=True)

        if gen:
            with st.spinner("La IA genera l'escenari científic..."):
                agent       = AgentIA()
                escenari_ia = agent.generar_escenari(tema, context)
            if escenari_ia:
                st.session_state['escenari_ia'] = escenari_ia
                st.session_state['tema_ia']     = tema
            else:
                st.error("Error generant l'escenari. Comprova la clau de Groq.")

        if 'escenari_ia' in st.session_state:
            ei = st.session_state['escenari_ia']
            st.markdown("---")
            st.markdown("## Revisa i confirma")
            cc1, cc2, cc3 = st.columns([3,1,1])
            with cc1: nom = st.text_input("Nom de l'escenari", value=st.session_state.get('tema_ia',''))
            with cc2: unitat = st.selectbox("Unitat de temps", ["any","mes","dia","hora"], index=["any","mes","dia","hora"].index(ei.get('unitat_temps','any')))
            with cc3: num_passos = st.number_input("Passos", min_value=1, max_value=200, value=int(ei.get('num_passos',10)))
            descripcio = st.text_area("Descripció", value=ei.get('descripcio',''), height=80)

            cv1, cv2 = st.columns(2)
            with cv1:
                st.markdown('<div style="font-size:0.75rem;color:#2d5a8a;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">📌 Variables fixes</div>', unsafe_allow_html=True)
                for v in ei.get('variables_fixes',[]):
                    st.markdown(f'<div style="display:flex;justify-content:space-between;padding:8px 12px;background:#0d1829;border-radius:8px;margin-bottom:4px;border:1px solid #1e3050;"><span style="color:#94b8d8;font-size:0.85rem;">📌 {v["nom"]}</span><span style="color:#2d5a8a;font-family:monospace;font-size:0.8rem;">{v["valor_inicial"]} {v.get("unitat","")}</span></div>', unsafe_allow_html=True)
            with cv2:
                st.markdown('<div style="font-size:0.75rem;color:#2d5a8a;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">🔄 Variables dinàmiques</div>', unsafe_allow_html=True)
                for v in ei.get('variables_dinamiques',[]):
                    st.markdown(f'<div style="display:flex;justify-content:space-between;padding:8px 12px;background:#0d1829;border-radius:8px;margin-bottom:4px;border:1px solid #1e3050;"><span style="color:#94b8d8;font-size:0.85rem;">🔄 {v["nom"]}</span><span style="color:#38bdf8;font-family:monospace;font-size:0.8rem;">{v["valor_inicial"]} {v.get("unitat","")}</span></div>', unsafe_allow_html=True)

            with st.expander("➕  Afegir variable pròpia"):
                na, nb, nc = st.columns(3)
                with na:
                    nv_nom   = st.text_input("Nom", key="nv_nom")
                    nv_tipus = st.selectbox("Tipus", ["dinamica","fixa"], key="nv_tipus")
                with nb:
                    nv_unit = st.text_input("Unitat", key="nv_unit")
                    nv_val  = st.number_input("Valor inicial", key="nv_val")
                with nc:
                    nv_min = st.number_input("Valor mínim", key="nv_min")
                    nv_max = st.number_input("Valor màxim", value=100.0, key="nv_max")
                nv_notes = st.text_input("Descripció del comportament", key="nv_notes")
                if st.button("➕  Afegir") and nv_nom:
                    nv  = {"nom":nv_nom,"unitat":nv_unit,"valor_inicial":nv_val,"valor_min":nv_min,"valor_max":nv_max,"notes":nv_notes}
                    key = 'variables_dinamiques' if nv_tipus=="dinamica" else 'variables_fixes'
                    st.session_state['escenari_ia'][key].append(nv)
                    st.rerun()

            st.markdown('<div style="font-size:0.75rem;color:#2d5a8a;text-transform:uppercase;letter-spacing:0.08em;margin:16px 0 8px;">⚡ Relacions científiques</div>', unsafe_allow_html=True)
            for r in ei.get('relacions',[]):
                pcls  = "rel-pes-pos" if r['pes']>0 else "rel-pes-neg"
                signe = "▲" if r['pes']>0 else "▼"
                st.markdown(f'<div class="rel-row"><span class="rel-origen">{r["origen"]}</span><span style="color:#1e3050;">→</span><span class="rel-desti">{r["desti"]}</span><span class="{pcls}">{signe} {abs(r["pes"])}</span><span class="rel-desc">{r.get("descripcio","")}</span></div>', unsafe_allow_html=True)

            st.markdown("---")
            if st.button("💾  Guardar i activar escenari", type="primary"):
                _guardar_escenari_ia(nom, descripcio, unitat, num_passos, ei)

    else:
        c1, c2 = st.columns([2,1])
        with c1:
            st.markdown("### Defineix el teu escenari")
            nom_m  = st.text_input("Nom de l'escenari")
            tema_m = st.text_input("Tema", placeholder="Ex: Contaminació a una zona industrial...")
            desc_m = st.text_area("Descripció i objectiu", height=80)
            ma2, mb2 = st.columns(2)
            with ma2: unitat_m = st.selectbox("Unitat de temps", ["any","mes","dia","hora"])
            with mb2: passos_m = st.number_input("Passos", min_value=1, max_value=200, value=10)
            gen_m = st.button("🔬  Proposar variables i relacions amb IA", type="primary", disabled=not (nom_m and tema_m))
        with c2:
            st.markdown('<div class="sim-card-amber"><div style="font-size:0.75rem;color:#7a5a00;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">Mode assistit</div><div style="font-size:0.85rem;color:#a07830;line-height:1.6;">La IA proposa variables i relacions. Tu pots esborrar les que no vols i afegir les teves pròpies.</div></div>', unsafe_allow_html=True)

        if gen_m:
            with st.spinner("La IA proposa variables i relacions..."):
                agent   = AgentIA()
                prop_ia = agent.generar_escenari(tema_m, desc_m)
            if prop_ia:
                st.session_state['proposta_manual'] = prop_ia
                st.session_state['config_manual']   = {'nom':nom_m,'tema':tema_m,'desc':desc_m,'unitat':unitat_m,'passos':passos_m}
            else:
                st.error("Error generant la proposta. Comprova la clau de Groq.")

        if 'proposta_manual' in st.session_state:
            pm  = st.session_state['proposta_manual']
            cfg = st.session_state.get('config_manual',{})
            st.markdown("---")
            st.markdown("## ✏️ Revisa i modifica")
            st.markdown('<div class="sim-card-amber"><div style="font-size:0.8rem;color:#a07830;line-height:1.6;">🔬 Esborra el que no necessites i afegeix les teves pròpies variables abans de guardar.</div></div>', unsafe_allow_html=True)

            # Capçaleres
            hc1, hc2, hc3, hc4, hc5 = st.columns([3,1,1,1,0.4])
            with hc1: st.markdown('<div style="font-size:0.7rem;color:#2d5a8a;text-transform:uppercase;padding:4px 0;">Nom</div>', unsafe_allow_html=True)
            with hc2: st.markdown('<div style="font-size:0.7rem;color:#2d5a8a;text-transform:uppercase;padding:4px 0;">Valor</div>', unsafe_allow_html=True)
            with hc3: st.markdown('<div style="font-size:0.7rem;color:#2d5a8a;text-transform:uppercase;padding:4px 0;">Mínim</div>', unsafe_allow_html=True)
            with hc4: st.markdown('<div style="font-size:0.7rem;color:#2d5a8a;text-transform:uppercase;padding:4px 0;">Màxim</div>', unsafe_allow_html=True)

            fixes_del = []
            st.markdown('<div style="font-size:0.75rem;color:#2d5a8a;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">📌 Variables fixes</div>', unsafe_allow_html=True)
            for i, v in enumerate(pm.get('variables_fixes',[])):
                cf1, cf2, cf3, cf4, cf5 = st.columns([3,1,1,1,0.4])
                with cf1: st.markdown(f'<div style="padding:8px 0;color:#94b8d8;font-size:0.85rem;">📌 {v["nom"]} <span style="color:#2d5a8a;font-size:0.75rem;">({v.get("unitat","")})</span></div>', unsafe_allow_html=True)
                with cf2:
                    nou_val = st.number_input("", value=float(v["valor_inicial"]), key=f"fval_{i}", label_visibility="collapsed")
                    pm['variables_fixes'][i]['valor_inicial'] = nou_val
                with cf3:
                    nou_min = st.number_input("", value=float(v.get("valor_min",0)), key=f"fmin_{i}", label_visibility="collapsed")
                    pm['variables_fixes'][i]['valor_min'] = nou_min
                with cf4:
                    nou_max = st.number_input("", value=float(v.get("valor_max",100)), key=f"fmax_{i}", label_visibility="collapsed")
                    pm['variables_fixes'][i]['valor_max'] = nou_max
                with cf5:
                    if st.button("🗑", key=f"df_{i}"): fixes_del.append(i)
            if fixes_del:
                for i in sorted(fixes_del, reverse=True): st.session_state['proposta_manual']['variables_fixes'].pop(i)
                st.rerun()

            dins_del = []
            st.markdown('<div style="font-size:0.75rem;color:#2d5a8a;text-transform:uppercase;letter-spacing:0.08em;margin:12px 0 8px;">🔄 Variables dinàmiques</div>', unsafe_allow_html=True)
            for i, v in enumerate(pm.get('variables_dinamiques',[])):
                cd1, cd2, cd3, cd4, cd5 = st.columns([3,1,1,1,0.4])
                with cd1: st.markdown(f'<div style="padding:8px 0;color:#94b8d8;font-size:0.85rem;">🔄 {v["nom"]} <span style="color:#2d5a8a;font-size:0.75rem;">({v.get("unitat","")})</span></div>', unsafe_allow_html=True)
                with cd2:
                    nou_val = st.number_input("", value=float(v["valor_inicial"]), key=f"dval_{i}", label_visibility="collapsed")
                    pm['variables_dinamiques'][i]['valor_inicial'] = nou_val
                with cd3:
                    nou_min = st.number_input("", value=float(v.get("valor_min",0)), key=f"dmin_{i}", label_visibility="collapsed")
                    pm['variables_dinamiques'][i]['valor_min'] = nou_min
                with cd4:
                    nou_max = st.number_input("", value=float(v.get("valor_max",100)), key=f"dmax_{i}", label_visibility="collapsed")
                    pm['variables_dinamiques'][i]['valor_max'] = nou_max
                with cd5:
                    if st.button("🗑", key=f"dd_{i}"): dins_del.append(i)
            if dins_del:
                for i in sorted(dins_del, reverse=True): st.session_state['proposta_manual']['variables_dinamiques'].pop(i)
                st.rerun()

            with st.expander("➕  Afegir variable pròpia"):
                ma3, mb3, mc3 = st.columns(3)
                with ma3:
                    mv_nom   = st.text_input("Nom", key="mv_nom")
                    mv_tipus = st.selectbox("Tipus", ["dinamica","fixa"], key="mv_tipus")
                with mb3:
                    mv_unit = st.text_input("Unitat", key="mv_unit")
                    mv_val  = st.number_input("Valor inicial", key="mv_val")
                with mc3:
                    mv_min = st.number_input("Valor mínim", key="mv_min")
                    mv_max = st.number_input("Valor màxim", value=100.0, key="mv_max")
                mv_notes = st.text_input("Descripció", key="mv_notes")
                if st.button("➕  Afegir variable") and mv_nom:
                    nv  = {"nom":mv_nom,"unitat":mv_unit,"valor_inicial":mv_val,"valor_min":mv_min,"valor_max":mv_max,"notes":mv_notes}
                    key = 'variables_dinamiques' if mv_tipus=="dinamica" else 'variables_fixes'
                    st.session_state['proposta_manual'][key].append(nv)
                    st.rerun()

            rels_del = []
            st.markdown('<div style="font-size:0.75rem;color:#2d5a8a;text-transform:uppercase;letter-spacing:0.08em;margin:16px 0 8px;">⚡ Relacions proposades</div>', unsafe_allow_html=True)
            for i, r in enumerate(pm.get('relacions',[])):
                cr1, cr2 = st.columns([5,0.4])
                with cr1:
                    pcls  = "rel-pes-pos" if r['pes']>0 else "rel-pes-neg"
                    signe = "▲" if r['pes']>0 else "▼"
                    st.markdown(f'<div class="rel-row"><span class="rel-origen">{r["origen"]}</span><span style="color:#1e3050;">→</span><span class="rel-desti">{r["desti"]}</span><span class="{pcls}">{signe} {abs(r["pes"])}</span><span class="rel-desc">{r.get("descripcio","")}</span></div>', unsafe_allow_html=True)
                with cr2:
                    if st.button("🗑", key=f"dr_{i}"): rels_del.append(i)
            if rels_del:
                for i in sorted(rels_del, reverse=True): st.session_state['proposta_manual']['relacions'].pop(i)
                st.rerun()

            st.markdown("---")
            if st.button("💾  Guardar i activar escenari", type="primary"):
                _guardar_escenari_assistit(cfg, pm)


# =============================================================================
# ESCENARIS
# =============================================================================

elif "📂" in seccio:
    st.markdown("# 📂 Escenaris guardats")
    st.markdown("---")
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT id,nom,tema,estat,unitat_temps,num_passos,creat_el FROM escenaris ORDER BY creat_el DESC")
    escenaris = cur.fetchall()
    conn.close()

    if not escenaris:
        st.markdown('<div style="text-align:center;padding:60px 20px;color:#2d5a8a;"><div style="font-size:3rem;margin-bottom:16px;">🌱</div><div>Encara no hi ha escenaris.</div></div>', unsafe_allow_html=True)
    else:
        for esc in escenaris:
            eid, nom, tema, estat, unitat, passos, creat = esc
            ecls     = {"actiu":"tag-green","pausat":"tag-amber","finalitzat":"tag-red"}.get(estat,"tag-blue")
            es_actiu = "✦ ACTIU" if st.session_state.get('escenari_actiu')==eid else ""
            ci, cb, cd = st.columns([5,1,1])
            with ci:
                st.markdown(f'<div class="esc-card"><div style="display:flex;align-items:center;gap:10px;"><div class="esc-nom">{nom}</div><span class="tag {ecls}">{estat}</span><span style="font-size:0.7rem;color:#38bdf8;">{es_actiu}</span></div><div class="esc-tema">{tema}</div><div class="esc-meta">{passos} {unitat}s &nbsp;·&nbsp; {creat[:10]}</div></div>', unsafe_allow_html=True)
            with cb:
                st.markdown("<div style='margin-top:14px;'>", unsafe_allow_html=True)
                if st.button("▶ Carregar", key=f"load_{eid}"):
                    st.session_state['escenari_actiu'] = eid
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with cd:
                st.markdown("<div style='margin-top:14px;'>", unsafe_allow_html=True)
                if st.button("🗑", key=f"del_{eid}"):
                    conn_d = sqlite3.connect(DB_PATH)
                    conn_d.execute("PRAGMA foreign_keys=ON;")
                    conn_d.execute("DELETE FROM escenaris WHERE id=?", (eid,))
                    conn_d.commit()
                    conn_d.close()
                    if st.session_state.get('escenari_actiu') == eid:
                        del st.session_state['escenari_actiu']
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# VARIABLES I RELACIONS (editor complet)
# =============================================================================

elif "✏️" in seccio:
    st.markdown("# ✏️ Variables i relacions")

    if 'escenari_actiu' not in st.session_state:
        st.markdown('<div style="text-align:center;padding:60px 20px;color:#2d5a8a;"><div style="font-size:3rem;margin-bottom:16px;">✏️</div><div>Cap escenari actiu.<br>Carrega un escenari primer.</div></div>', unsafe_allow_html=True)
    else:
        eid = st.session_state['escenari_actiu']
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur  = conn.cursor()
        cur.execute("SELECT nom, tema FROM escenaris WHERE id=?", (eid,))
        esc_info = cur.fetchone()
        cur.execute("SELECT id,nom,tipus_var,unitat,valor_inicial,valor_min,valor_max FROM variables WHERE escenari_id=? ORDER BY tipus_var,nom", (eid,))
        variables = [dict(r) for r in cur.fetchall()]
        cur.execute("""SELECT r.id, v1.nom as origen, v2.nom as desti, r.pes, r.descripcio
                       FROM relacions r
                       JOIN variables v1 ON r.variable_origen_id=v1.id
                       JOIN variables v2 ON r.variable_desti_id=v2.id
                       WHERE r.escenari_id=? ORDER BY v1.nom""", (eid,))
        relacions = [dict(r) for r in cur.fetchall()]
        conn.close()

        st.markdown(f'<div class="sim-card"><div style="font-size:1.2rem;font-weight:600;color:#e8f4fd;font-family:\'Space Mono\',monospace;">{esc_info["nom"]}</div><div style="color:#4a6a8a;font-size:0.85rem;margin-top:4px;">{esc_info["tema"]}</div><div style="display:flex;gap:20px;margin-top:12px;"><div><span style="color:#2d5a8a;font-size:0.7rem;text-transform:uppercase;">Variables</span><br><span style="color:#38bdf8;font-family:\'Space Mono\',monospace;">{len(variables)}</span></div><div><span style="color:#2d5a8a;font-size:0.7rem;text-transform:uppercase;">Relacions</span><br><span style="color:#38bdf8;font-family:\'Space Mono\',monospace;">{len(relacions)}</span></div></div></div>', unsafe_allow_html=True)
        st.markdown('<div class="sim-card-amber"><div style="font-size:0.85rem;color:#a07830;line-height:1.6;">🔬 Aquí pots calibrar el teu escenari. Si els resultats de la simulació no van cap a on esperes, ajusta els pesos de les relacions, modifica els valors de les variables o afegeix elements que falten.</div></div>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["📊 Variables", "⚡ Relacions"])

        # --- TAB VARIABLES ---
        with tab1:
            st.markdown("#### Variables actuals")
            for v in variables:
                icona = "📌" if v['tipus_var']=='fixa' else "🔄"
                cv1, cv2, cv3, cv4, cv5 = st.columns([3,1,1,1,0.5])
                with cv1: st.markdown(f'<div style="padding:8px 0;color:#94b8d8;font-size:0.85rem;">{icona} {v["nom"]} <span style="color:#2d5a8a;font-size:0.75rem;">({v.get("unitat","")})</span></div>', unsafe_allow_html=True)
                with cv2: st.markdown(f'<div style="padding:8px 0;color:#38bdf8;font-family:monospace;font-size:0.8rem;">Val: {v["valor_inicial"]}</div>', unsafe_allow_html=True)
                with cv3: st.markdown(f'<div style="padding:8px 0;color:#2d5a8a;font-family:monospace;font-size:0.75rem;">Min: {v["valor_min"] or 0}</div>', unsafe_allow_html=True)
                with cv4: st.markdown(f'<div style="padding:8px 0;color:#2d5a8a;font-family:monospace;font-size:0.75rem;">Max: {v["valor_max"] or 100}</div>', unsafe_allow_html=True)
                with cv5:
                    if st.button("🗑", key=f"dvar_{v['id']}"):
                        conn_dv = sqlite3.connect(DB_PATH)
                        conn_dv.execute("PRAGMA foreign_keys=ON;")
                        conn_dv.execute("DELETE FROM variables WHERE id=?", (v['id'],))
                        conn_dv.commit()
                        conn_dv.close()
                        st.rerun()

            st.markdown("---")
            st.markdown("#### ➕ Afegir nova variable")
            va1, va2, va3 = st.columns(3)
            with va1:
                av_nom   = st.text_input("Nom de la variable", key="av_nom")
                av_tipus = st.selectbox("Tipus", ["dinamica","fixa"], key="av_tipus")
            with va2:
                av_unit = st.text_input("Unitat", key="av_unit", placeholder="°C, mm/any, %...")
                av_val  = st.number_input("Valor inicial", key="av_val")
            with va3:
                av_min = st.number_input("Valor mínim", key="av_min")
                av_max = st.number_input("Valor màxim", value=100.0, key="av_max")
            av_notes = st.text_input("Notes (opcional)", key="av_notes")
            if st.button("➕  Afegir variable", type="primary") and av_nom:
                conn_av = sqlite3.connect(DB_PATH)
                conn_av.execute("INSERT INTO variables (escenari_id,nom,tipus_var,unitat,valor_inicial,valor_min,valor_max,notes) VALUES (?,?,?,?,?,?,?,?)",
                                (eid,av_nom,av_tipus,av_unit,av_val,av_min,av_max,av_notes))
                conn_av.commit()
                conn_av.close()
                st.success(f"Variable '{av_nom}' afegida!")
                st.rerun()

        # --- TAB RELACIONS ---
        with tab2:
            st.markdown("#### Relacions actuals")
            if not relacions:
                st.warning("Aquest escenari no té relacions. Afegeix-ne per que la simulació evolucioni.")
            else:
                for r in relacions:
                    pcls  = "rel-pes-pos" if r['pes']>0 else "rel-pes-neg"
                    signe = "▲" if r['pes']>0 else "▼"
                    cr1, cr2, cr3 = st.columns([4,1,0.5])
                    with cr1:
                        st.markdown(f'<div class="rel-row"><span class="rel-origen">{r["origen"]}</span><span style="color:#1e3050;">→</span><span class="rel-desti">{r["desti"]}</span><span class="{pcls}">{signe} {abs(r["pes"])}</span></div>', unsafe_allow_html=True)
                    with cr2:
                        nou_pes = st.number_input("Pes", min_value=-1.0, max_value=1.0, value=float(r['pes']), step=0.1, key=f"pes_{r['id']}", label_visibility="collapsed")
                        if nou_pes != r['pes']:
                            conn_rp = sqlite3.connect(DB_PATH)
                            conn_rp.execute("UPDATE relacions SET pes=? WHERE id=?", (nou_pes, r['id']))
                            conn_rp.commit()
                            conn_rp.close()
                            st.rerun()
                    with cr3:
                        if st.button("🗑", key=f"drel_{r['id']}"):
                            conn_dr = sqlite3.connect(DB_PATH)
                            conn_dr.execute("DELETE FROM relacions WHERE id=?", (r['id'],))
                            conn_dr.commit()
                            conn_dr.close()
                            st.rerun()

            st.markdown("---")
            st.markdown("#### ➕ Afegir nova relació")
            noms_vars = [v['nom'] for v in variables]
            if len(noms_vars) >= 2:
                ra1, ra2, ra3 = st.columns(3)
                with ra1: ar_orig = st.selectbox("Variable origen", noms_vars, key="ar_orig")
                with ra2: ar_dest = st.selectbox("Variable destí", noms_vars, key="ar_dest")
                with ra3: ar_pes  = st.number_input("Pes (-1 a +1)", min_value=-1.0, max_value=1.0, value=0.5, step=0.1, key="ar_pes")
                ar_desc = st.text_input("Descripció de la relació", key="ar_desc", placeholder="Ex: Temperatura alta redueix la humitat del sòl")
                if st.button("➕  Afegir relació", type="primary"):
                    conn_ar = sqlite3.connect(DB_PATH)
                    cur_ar  = conn_ar.cursor()
                    cur_ar.execute("SELECT id FROM variables WHERE escenari_id=? AND nom=?", (eid, ar_orig))
                    orig_id = cur_ar.fetchone()
                    cur_ar.execute("SELECT id FROM variables WHERE escenari_id=? AND nom=?", (eid, ar_dest))
                    dest_id = cur_ar.fetchone()
                    if orig_id and dest_id and ar_orig != ar_dest:
                        cur_ar.execute("INSERT INTO relacions (escenari_id,variable_origen_id,variable_desti_id,pes,descripcio) VALUES (?,?,?,?,?)",
                                       (eid, orig_id[0], dest_id[0], ar_pes, ar_desc))
                        conn_ar.commit()
                        st.success("Relació afegida!")
                    else:
                        st.error("Selecciona dues variables diferents.")
                    conn_ar.close()
                    st.rerun()
            else:
                st.info("Necessites almenys 2 variables per crear relacions.")


# =============================================================================
# SIMULACIÓ
# =============================================================================

elif "🎛️" in seccio:
    st.markdown("# 🎛️ Panell de simulació")

    if 'escenari_actiu' not in st.session_state:
        st.markdown('<div style="text-align:center;padding:60px 20px;color:#2d5a8a;"><div style="font-size:3rem;margin-bottom:16px;">⚡</div><div>Cap escenari actiu.</div></div>', unsafe_allow_html=True)
    else:
        eid  = st.session_state['escenari_actiu']
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur  = conn.cursor()
        cur.execute("SELECT * FROM escenaris WHERE id=?", (eid,))
        esc  = dict(cur.fetchone())
        cur.execute("SELECT * FROM variables WHERE escenari_id=?", (eid,))
        variables = [dict(r) for r in cur.fetchall()]
        conn.close()

        ecls = {"actiu":"tag-green","pausat":"tag-amber","finalitzat":"tag-red"}.get(esc['estat'],"tag-blue")
        st.markdown(f'<div class="sim-card"><div style="display:flex;align-items:flex-start;justify-content:space-between;"><div><div style="font-size:1.4rem;font-weight:600;color:#e8f4fd;font-family:\'Space Mono\',monospace;">{esc["nom"]}</div><div style="color:#4a6a8a;font-size:0.85rem;margin-top:4px;">{esc["tema"]}</div></div><span class="tag {ecls}">{esc["estat"]}</span></div><div style="display:flex;gap:24px;margin-top:14px;"><div><span style="color:#2d5a8a;font-size:0.7rem;text-transform:uppercase;">Passos</span><br><span style="color:#38bdf8;font-family:\'Space Mono\',monospace;">{esc["num_passos"]}</span></div><div><span style="color:#2d5a8a;font-size:0.7rem;text-transform:uppercase;">Unitat</span><br><span style="color:#38bdf8;font-family:\'Space Mono\',monospace;">{esc["unitat_temps"]}</span></div><div><span style="color:#2d5a8a;font-size:0.7rem;text-transform:uppercase;">Variables</span><br><span style="color:#38bdf8;font-family:\'Space Mono\',monospace;">{len(variables)}</span></div></div></div>', unsafe_allow_html=True)

        if esc.get('descripcio'):
            with st.expander("📋 Descripció"):
                st.write(esc['descripcio'])

        # Relacions guardades
        conn_r = sqlite3.connect(DB_PATH)
        cur_r  = conn_r.cursor()
        cur_r.execute("""SELECT v1.nom, v2.nom, r.pes FROM relacions r
                         JOIN variables v1 ON r.variable_origen_id=v1.id
                         JOIN variables v2 ON r.variable_desti_id=v2.id
                         WHERE r.escenari_id=?""", (eid,))
        relacions_db = cur_r.fetchall()
        conn_r.close()

        if relacions_db:
            with st.expander(f"⚡ Relacions actives ({len(relacions_db)})"):
                for r in relacions_db:
                    pcls  = "rel-pes-pos" if r[2]>0 else "rel-pes-neg"
                    signe = "▲" if r[2]>0 else "▼"
                    st.markdown(f'<div class="rel-row"><span class="rel-origen">{r[0]}</span><span style="color:#1e3050;">→</span><span class="rel-desti">{r[1]}</span><span class="{pcls}">{signe} {abs(r[2])}</span></div>', unsafe_allow_html=True)
        else:
            st.warning("⚠️ No hi ha relacions. Ves a ✏️ Variables per afegir-ne.")

        fixes = [v for v in variables if v['tipus_var']=='fixa']
        if fixes:
            st.markdown('<div style="font-size:0.75rem;color:#2d5a8a;text-transform:uppercase;letter-spacing:0.08em;margin:16px 0 8px;">📌 Variables fixes</div>', unsafe_allow_html=True)
            cfs = st.columns(min(len(fixes), 5))
            for i,v in enumerate(fixes[:5]):
                cfs[i].markdown(f'<div class="metric-box"><div class="metric-value">{v["valor_inicial"]}</div><div class="metric-unit">{v.get("unitat","")}</div><div class="metric-label">{v["nom"]}</div></div>', unsafe_allow_html=True)

        dinamiques = [v for v in variables if v['tipus_var']=='dinamica']
        if dinamiques:
            st.markdown('<div style="font-size:0.75rem;color:#2d5a8a;text-transform:uppercase;letter-spacing:0.08em;margin:20px 0 10px;">🎛️ Variables dinàmiques</div>', unsafe_allow_html=True)
            cds = st.columns(2)
            for i,v in enumerate(dinamiques):
                with cds[i%2]:
                    vmin = float(v['valor_min']) if v['valor_min'] is not None else 0.0
                    vmax = float(v['valor_max']) if v['valor_max'] is not None else 100.0
                    st.slider(f"{v['nom']} ({v.get('unitat','')})", min_value=vmin, max_value=vmax,
                              value=float(v['valor_inicial']), key=f"sl_{v['id']}")

        st.markdown("---")
        ba, bb, bc = st.columns(3)
        with ba:
            if st.button("▶️  Simular tot", type="primary"):
                with st.spinner("Executant simulació..."):
                    m = MotorSimulacio(escenari_id=eid, db_path=DB_PATH)
                    m.carregar()
                    m.simular_tot()
                st.success("✅ Simulació completada! Ves a 📊 Gràfiques.")
        with bb:
            if st.button("⏭️  Avançar un pas"):
                if 'motor_pas' not in st.session_state:
                    st.session_state['motor_pas'] = MotorSimulacio(escenari_id=eid, db_path=DB_PATH)
                    st.session_state['motor_pas'].carregar()
                ok = st.session_state['motor_pas'].calcular_pas()
                if ok: st.rerun()
                else:  st.info("Simulació finalitzada.")
        with bc:
            if st.button("↺  Reiniciar"):
                if 'motor_pas' in st.session_state: del st.session_state['motor_pas']
                conn2 = sqlite3.connect(DB_PATH)
                conn2.execute("DELETE FROM historial_valors WHERE escenari_id=?", (eid,))
                conn2.commit(); conn2.close()
                st.rerun()

        st.markdown("---")
        st.markdown('<div style="font-size:0.75rem;color:#2d5a8a;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">📝 Notes de sessió</div>', unsafe_allow_html=True)
        nova_nota = st.text_area("Afegeix una nota", height=80, placeholder="Què has provat? Què has observat?")
        if st.button("💾  Guardar nota"):
            if nova_nota.strip():
                conn3 = sqlite3.connect(DB_PATH)
                conn3.execute("INSERT INTO notes_escenari (escenari_id,nota) VALUES (?,?)", (eid, nova_nota))
                conn3.commit(); conn3.close()
                st.success("Nota guardada!")

        conn4 = sqlite3.connect(DB_PATH)
        cur4  = conn4.cursor()
        cur4.execute("SELECT registrat_el,nota FROM notes_escenari WHERE escenari_id=? ORDER BY registrat_el DESC LIMIT 5", (eid,))
        notes = cur4.fetchall(); conn4.close()
        if notes:
            with st.expander(f"📖 Notes anteriors ({len(notes)})"):
                for data, nota in notes:
                    st.markdown(f'<div style="padding:8px 12px;background:#0d1829;border-left:3px solid #1e4a7a;border-radius:0 6px 6px 0;margin-bottom:6px;"><div style="font-size:0.7rem;color:#2d5a8a;margin-bottom:2px;font-family:monospace;">{data}</div><div style="font-size:0.85rem;color:#94b8d8;">{nota}</div></div>', unsafe_allow_html=True)


# =============================================================================
# GRÀFIQUES
# =============================================================================

elif "📊" in seccio:
    st.markdown("# 📊 Evolució de la simulació")

    if 'escenari_actiu' not in st.session_state:
        st.markdown('<div style="text-align:center;padding:60px 20px;color:#2d5a8a;"><div style="font-size:3rem;margin-bottom:16px;">📊</div><div>Cap escenari actiu.</div></div>', unsafe_allow_html=True)
    else:
        eid  = st.session_state['escenari_actiu']
        conn = sqlite3.connect(DB_PATH)
        cur  = conn.cursor()
        cur.execute("""SELECT h.pas, v.nom, h.valor, v.unitat
                       FROM historial_valors h JOIN variables v ON h.variable_id=v.id
                       WHERE h.escenari_id=? AND v.tipus_var='dinamica'
                       ORDER BY h.pas ASC""", (eid,))
        dades = cur.fetchall()
        cur.execute("SELECT nom, unitat_temps FROM escenaris WHERE id=?", (eid,))
        info  = cur.fetchone()
        conn.close()

        if not dades:
            st.markdown('<div style="text-align:center;padding:60px 20px;color:#2d5a8a;"><div style="font-size:3rem;margin-bottom:16px;">⏳</div><div>Encara no hi ha dades.<br>Executa la simulació primer!</div></div>', unsafe_allow_html=True)
        else:
            df        = pd.DataFrame(dades, columns=['pas','variable','valor','unitat'])
            vars_disp = df['variable'].unique().tolist()
            cs, ci    = st.columns([3,1])
            with cs: sel = st.multiselect("Variables a mostrar", vars_disp, default=vars_disp[:4])
            with ci: st.markdown(f'<div class="metric-box" style="margin-top:8px;"><div class="metric-value">{df["pas"].max()}</div><div class="metric-unit">{info[1] if info else ""}s</div><div class="metric-label">{info[0] if info else ""}</div></div>', unsafe_allow_html=True)

            if sel:
                colors = ['#38bdf8','#34d399','#fbbf24','#f87171','#a78bfa','#fb923c','#22d3ee','#86efac']
                fig    = go.Figure()
                for i, var in enumerate(sel):
                    dv = df[df['variable']==var]
                    fig.add_trace(go.Scatter(x=dv['pas'], y=dv['valor'], name=var, mode='lines+markers',
                                             line=dict(color=colors[i%len(colors)], width=2), marker=dict(size=5),
                                             hovertemplate=f"<b>{var}</b><br>Pas %{{x}}<br>%{{y:.2f}}<extra></extra>"))
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#080d1a',
                    font=dict(color='#8fa3c4', family='DM Sans'),
                    xaxis=dict(title=f"Pas ({info[1] if info else 'temps'})", gridcolor='#0d1829', linecolor='#1e3050', tickfont=dict(color='#4a6a8a')),
                    yaxis=dict(title="Valor", gridcolor='#0d1829', linecolor='#1e3050', tickfont=dict(color='#4a6a8a')),
                    legend=dict(bgcolor='#0d1829', bordercolor='#1e3050', borderwidth=1, font=dict(color='#8fa3c4')),
                    hovermode='x unified', height=420, margin=dict(l=10,r=10,t=20,b=10)
                )
                st.plotly_chart(fig, use_container_width=True)

                st.markdown('<div style="font-size:0.75rem;color:#2d5a8a;text-transform:uppercase;letter-spacing:0.08em;margin:16px 0 8px;">Valors finals</div>', unsafe_allow_html=True)
                ultim = df['pas'].max()
                df_f  = df[df['pas']==ultim][['variable','valor','unitat']].copy()
                df_f.columns = ['Variable','Valor final','Unitat']
                df_f['Valor final'] = df_f['Valor final'].round(2)
                st.dataframe(df_f, use_container_width=True, hide_index=True)
