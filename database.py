import streamlit as st
from supabase import create_client

@st.cache_resource
def get_db():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


# =============================================================================
# ESCENARIS
# =============================================================================

def get_escenaris():
    sb = get_db()
    res = sb.table('escenaris').select('*').order('creat_el', desc=True).execute()
    return res.data or []

def get_escenari(eid):
    sb = get_db()
    res = sb.table('escenaris').select('*').eq('id', eid).single().execute()
    return res.data

def crear_escenari(nom, tema, descripcio, unitat_temps, num_passos):
    sb = get_db()
    res = sb.table('escenaris').insert({
        'nom': nom, 'tema': tema, 'descripcio': descripcio,
        'unitat_temps': unitat_temps, 'num_passos': num_passos
    }).execute()
    return res.data[0]['id']

def esborrar_escenari(eid):
    sb = get_db()
    sb.table('escenaris').delete().eq('id', eid).execute()

def actualitzar_estat_escenari(eid, estat):
    sb = get_db()
    sb.table('escenaris').update({'estat': estat}).eq('id', eid).execute()


# =============================================================================
# VARIABLES
# =============================================================================

def get_variables(eid):
    sb = get_db()
    res = sb.table('variables').select('*').eq('escenari_id', eid).order('tipus_var').execute()
    return res.data or []

def crear_variable(eid, nom, tipus_var, unitat, valor_inicial, valor_min, valor_max, notes=''):
    sb = get_db()
    res = sb.table('variables').insert({
        'escenari_id': eid, 'nom': nom, 'tipus_var': tipus_var,
        'unitat': unitat, 'valor_inicial': valor_inicial,
        'valor_min': valor_min, 'valor_max': valor_max, 'notes': notes
    }).execute()
    return res.data[0]['id']

def actualitzar_variable(vid, unitat, valor_inicial, valor_min, valor_max, tipus_var):
    sb = get_db()
    sb.table('variables').update({
        'unitat': unitat, 'valor_inicial': valor_inicial,
        'valor_min': valor_min, 'valor_max': valor_max, 'tipus_var': tipus_var
    }).eq('id', vid).execute()

def esborrar_variable(vid):
    sb = get_db()
    sb.table('variables').delete().eq('id', vid).execute()


# =============================================================================
# RELACIONS
# =============================================================================

def get_relacions(eid):
    sb = get_db()
    res = sb.table('relacions').select(
        '*, variable_origen:variable_origen_id(nom), variable_desti:variable_desti_id(nom)'
    ).eq('escenari_id', eid).execute()
    relacions = []
    for r in (res.data or []):
        relacions.append({
            'id': r['id'],
            'origen': r['variable_origen']['nom'],
            'desti': r['variable_desti']['nom'],
            'origen_id': r['variable_origen_id'],
            'desti_id': r['variable_desti_id'],
            'pes': r['pes'],
            'descripcio': r.get('descripcio', ''),
            'generada_per_ia': r.get('generada_per_ia', False),
            'tipus_relacio': r.get('tipus_relacio', 'proporcional'),
            'equacio': r.get('equacio', ''),
            'alpha': r.get('alpha', 0),
            'beta': r.get('beta', 0),
        })
    return relacions

def crear_relacio(eid, origen_id, desti_id, pes, descripcio='', generada_per_ia=False, tipus_relacio='proporcional', equacio='', alpha=0, beta=0):
    sb = get_db()
    sb.table('relacions').insert({
        'escenari_id': eid, 'variable_origen_id': origen_id,
        'variable_desti_id': desti_id, 'pes': pes,
        'descripcio': descripcio, 'generada_per_ia': generada_per_ia,
        'tipus_relacio': tipus_relacio, 'equacio': equacio,
        'alpha': alpha, 'beta': beta
    }).execute()

def actualitzar_pes_relacio(rid, pes):
    sb = get_db()
    sb.table('relacions').update({'pes': pes}).eq('id', rid).execute()

def esborrar_relacio(rid):
    sb = get_db()
    sb.table('relacions').delete().eq('id', rid).execute()


# =============================================================================
# HISTORIAL
# =============================================================================

def get_historial(eid):
    sb = get_db()
    res = sb.table('historial_valors').select(
        'pas, valor, variable_id, variables(nom, unitat, tipus_var)'
    ).eq('escenari_id', eid).order('pas').execute()
    return res.data or []

def guardar_historial_bulk(registres):
    """registres = llista de dicts amb escenari_id, variable_id, pas, valor"""
    sb = get_db()
    sb.table('historial_valors').insert(registres).execute()

def esborrar_historial(eid):
    sb = get_db()
    sb.table('historial_valors').delete().eq('escenari_id', eid).execute()

def get_ultim_pas(eid):
    sb = get_db()
    res = sb.table('historial_valors').select('pas').eq('escenari_id', eid).order('pas', desc=True).limit(1).execute()
    if res.data:
        return res.data[0]['pas']
    return 0

def get_valors_ultim_pas(eid):
    ultim = get_ultim_pas(eid)
    if ultim == 0:
        return {}
    sb = get_db()
    res = sb.table('historial_valors').select('variable_id, valor').eq('escenari_id', eid).eq('pas', ultim).execute()
    return {r['variable_id']: r['valor'] for r in (res.data or [])}


# =============================================================================
# NOTES
# =============================================================================

def get_notes(eid, limit=5):
    sb = get_db()
    res = sb.table('notes_escenari').select('*').eq('escenari_id', eid).order('registrat_el', desc=True).limit(limit).execute()
    return res.data or []

def crear_nota(eid, nota):
    sb = get_db()
    sb.table('notes_escenari').insert({'escenari_id': eid, 'nota': nota}).execute()
