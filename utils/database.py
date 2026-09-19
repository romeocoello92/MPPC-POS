import streamlit as st
from supabase import create_client, Client
import pandas as pd

@st.cache_resource
def get_supabase() -> Client:
    """Conexión a la nueva instancia de Supabase"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

# ─────────────────────────────────────────────
# TABLAS DE DIMENSIÓN (Catálogos)
# ─────────────────────────────────────────────
def cargar_alumnos() -> pd.DataFrame:
    res = get_supabase().table("dim_alumnos").select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

def insertar_alumno(datos: dict) -> dict:
    res = get_supabase().table("dim_alumnos").insert(datos).execute()
    return res.data[0] if res.data else None

def cargar_coaches() -> pd.DataFrame:
    res = get_supabase().table("dim_coaches").select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

# ─────────────────────────────────────────────
# TABLAS DE HECHOS (Operación Diaria)
# ─────────────────────────────────────────────
def cargar_folios() -> pd.DataFrame:
    res = get_supabase().table("fact_folios").select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

def insertar_folio(datos: dict) -> dict:
    res = get_supabase().table("fact_folios").insert(datos).execute()
    return res.data[0] if res.data else None

def actualizar_folio(id_folio: str, campos: dict) -> None:
    get_supabase().table("fact_folios").update(campos).eq("id", id_folio).execute()

def insertar_folio_dias(datos: list) -> None:
    """Inserta los días separados para el Mapa de Calor de Power BI"""
    if datos:
        get_supabase().table("fact_folio_dias").insert(datos).execute()

def cargar_pagos() -> pd.DataFrame:
    res = get_supabase().table("fact_pagos").select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

def insertar_pago(datos: dict) -> None:
    get_supabase().table("fact_pagos").insert(datos).execute()

def cargar_asistencias() -> pd.DataFrame:
    res = get_supabase().table("fact_asistencias").select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

def insertar_asistencia(datos: dict) -> None:
    get_supabase().table("fact_asistencias").insert(datos).execute()

# ─────────────────────────────────────────────
# CACHÉ LOCAL OPTIMIZADO
# ─────────────────────────────────────────────
def inicializar_cache() -> None:
    if "cache_listo" not in st.session_state:
        with st.spinner("Sincronizando con el servidor BI..."):
            st.session_state["db_alumnos"] = cargar_alumnos()
            st.session_state["db_coaches"] = cargar_coaches()
            st.session_state["db_folios"] = cargar_folios()
            st.session_state["db_pagos"] = cargar_pagos()
            st.session_state["db_asistencias"] = cargar_asistencias()
            st.session_state["cache_listo"] = True

def refrescar_tabla(tabla: str) -> None:
    mapa = {
        "dim_alumnos": ("db_alumnos", cargar_alumnos),
        "dim_coaches": ("db_coaches", cargar_coaches),
        "fact_folios": ("db_folios", cargar_folios),
        "fact_pagos": ("db_pagos", cargar_pagos),
        "fact_asistencias": ("db_asistencias", cargar_asistencias)
    }
    if tabla in mapa:
        key, fn = mapa[tabla]
        st.session_state[key] = fn()
