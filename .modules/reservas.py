import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar

from config.reglas import CANCHAS_MAP, HORARIOS_CLUB, DURACIONES, PRECIOS_PARTICULARES
from utils.database import insertar_folio, insertar_folio_dias, insertar_alumno, get_supabase, refrescar_tabla
from utils.validaciones import obtener_lista_fechas_wonox, verificar_empalme, parse_rango_horas

def aplicar_estilo_premium():
    estilo_css = """
    <style>
    /* Fondo oscuro para las cajas de texto */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {
        background-color: #121212 !important; 
        border-radius: 8px !important; 
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-top: 2px solid #C5A059 !important; /* Dorado Premium */
        transition: all 0.3s ease-in-out;
    }
    /* Efecto al seleccionar (Dorado brillante) */
    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within {
        border-top: 2px solid #FFD700 !important; 
        box-shadow: 0 -4px 15px rgba(212, 175, 55, 0.15) !important;
    }
    /* Texto Blanco */
    div[data-baseweb="input"] input,
    div[data-baseweb="select"],
    div[data-baseweb="select"] div,
    div[data-baseweb="select"] span,
    input { color: #FAFAFA !important; -webkit-text-fill-color: #FAFAFA !important; }
    
    /* Menús desplegables (Dropdowns) */
    ul[data-baseweb="menu"] { background-color: #121212 !important; border-radius: 8px !important; border: 1px solid rgba(255, 255, 255, 0.2) !important; }
    li[data-baseweb="option"] { color: #FAFAFA !important; }
    li[data-baseweb="option"]:hover { background-color: #2a2a2a !important; color: #D4AF37 !important; }
    </style>
    """
    st.markdown(estilo_css, unsafe_allow_html=True)

def render():
    aplicar_estilo_premium()
    
    st.title("🛒 Registro de Ventas y Reservas")
    
    # 1. Cargamos catálogos limpios
    df_alumnos = st.session_state.get('db_alumnos', pd.DataFrame())
    df_coaches = st.session_state.get('db_coaches', pd.DataFrame())
    
    if df_coaches.empty:
        st.warning("⚠️ No hay coaches dados de alta en Supabase. Ve a la tabla 'dim_coaches' y agrega al menos uno para continuar.")
        return

    # Diccionario de coaches para el selectbox {Nombre: ID}
    mapa_coaches = dict(zip(df_coaches['nombre'], df_coaches['id']))
    
    tab_particulares, tab_academias = st.tabs(["🎾 Clases Particulares", "🏆 Academias"])

    # ==========================================
    # PESTAÑA: CLASES PARTICULARES
    # ==========================================
    with tab_particulares:
        st.markdown("### 1. Datos Generales")
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            coach_seleccionado = st.selectbox("Coach Asignado", list(mapa_coaches.keys()), key="coach_part")
            id_coach = mapa_coaches[coach_seleccionado]
            cantidad_alumnos = st.selectbox("Cantidad de Alumnos", [1, 2, 3, 4], key="cant_alum")
            
        with col_g2:
            st.markdown("**Nombres de los Alumnos:**")
            alumnos_data = []
            
            # Selector Dinámico de Alumnos
            opciones_alumnos = ["➕ Crear Nuevo Alumno..."] + (df_alumnos['nombre_completo'].tolist() if not df_alumnos.empty else [])
            
            for i in range(cantidad_alumnos):
                seleccion_alumno = st.selectbox(f"Alumno {i+1}", opciones_alumnos, key=f"sel_alum_{i}")
                
                # Si eligen crear nuevo, mostramos los campos
                if seleccion_alumno == "➕ Crear Nuevo Alumno...":
                    with st.container(border=True):
                        nuevo_nombre = st.text_input(f"Nombre Completo (Alumno {i+1})", key=f"nuevo_nom_{i}")
                        es_menor = st.checkbox("Es Menor de Edad", key=f"menor_{i}")
                        nombre_tutor = st.text_input("Nombre del Tutor", key=f"tutor_{i}") if es_menor else ""
                        tel_tutor = st.text_input("Teléfono (WhatsApp)", key=f"tel_{i}") if es_menor else st.text_input("Teléfono del Alumno (WhatsApp)", key=f"tel_adulto_{i}")
                        
                        alumnos_data.append({
                            "es_nuevo": True,
                            "nombre_completo": nuevo_nombre.strip().upper(),
                            "es_menor": es_menor,
                            "nombre_tutor": nombre_tutor.strip().upper(),
                            "telefono_contacto": tel_tutor.strip()
                        })
                else:
                    # Alumno existente
                    id_alumno_existente = df_alumnos[df_alumnos['nombre_completo'] == seleccion_alumno].iloc[0]['id']
                    alumnos_data.append({
                        "es_nuevo": False,
                        "id": id_alumno_existente,
                        "nombre_completo": seleccion_alumno
                    })

        st.divider()
        st.markdown("### 2. Diseñador del Paquete")
        
        c1, c2 = st.columns(2)
        with c1:
            tipo_c = st.selectbox("Tipo de Cancha", list(CANCHAS_MAP.keys()), key="tp_c_p")
            nombre_c = st.selectbox("Cancha", CANCHAS_MAP[tipo_c], key="n_c_p")
            hora_p = st.selectbox("Hora Inicio", HORARIOS_CLUB, key="h_p")
            duracion_p = st.selectbox("Duración", list(DURACIONES.keys()), key="dur_p")
            
        with c2:
            import datetime
            hoy = datetime.date.today()
            fi_p = st.date_input("Fecha Inicio", value=hoy, key="fi_p")
            ff_p = st.date_input("Fecha Fin (Límite)", value=hoy + timedelta(days=30), key="ff_p")
            dias_p = st.multiselect("Días de Clase", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"], default=["Lunes", "Miércoles"])

        # Generador de Fechas
        fechas_pre = [] if ff_p < fi_p else obtener_lista_fechas_wonox(fi_p, ff_p, dias_p)
        fechas_f = st.multiselect("Días exactos a cobrar:", options=fechas_pre, default=fechas_pre)

        if st.button("✅ Procesar y Agendar Grupo", type="primary", use_container_width=True):
            if not fechas_f:
                st.error("Debes seleccionar al menos una fecha.")
            else:
                # 1. Calculamos horario fin
                hora_fin_obj = datetime.datetime.strptime(hora_p, "%H:%M") + timedelta(hours=DURACIONES[duracion_p])
                hora_fin_str = hora_fin_obj.strftime("%H:%M")
                horario_str = f"{hora_p} a {hora_fin_str}"
                
                # 2. Radar Anti-empalme
                hay_colision, folio_estorbo, _ = verificar_empalme(nombre_c, horario_str, fechas_f)
                
                if hay_colision:
                    st.error(f"🚨 EMPALME: La cancha {nombre_c} está ocupada por el folio {folio_estorbo}.")
                else:
                    with st.spinner("Procesando en Supabase..."):
                        import uuid
                        grupo_id = f"PART-{str(uuid.uuid4())[:6].upper()}"
                        
                        # Cálculo de costo
                        tarifa = PRECIOS_PARTICULARES[tipo_c]["1-2"] if cantidad_alumnos <= 2 else PRECIOS_PARTICULARES[tipo_c]["3-4"]
                        costo_total_clase = (tarifa if cantidad_alumnos <= 4 else (tarifa / 4) * cantidad_alumnos) * len(fechas_f) * DURACIONES[duracion_p]
                        costo_por_alumno = costo_total_clase / cantidad_alumnos

                        for idx, alum in enumerate(alumnos_data):
                            # Si es nuevo, lo creamos en Supabase
                            if alum["es_nuevo"]:
                                if not alum["nombre_completo"]: continue # Ignorar vacíos
                                res_alum = insertar_alumno({
                                    "nombre_completo": alum["nombre_completo"],
                                    "es_menor": alum["es_menor"],
                                    "nombre_tutor": alum["nombre_tutor"],
                                    "telefono_contacto": alum["telefono_contacto"]
                                })
                                id_alum_final = res_alum["id"]
                            else:
                                id_alum_final = alum["id"]

                            # Insertamos Folio (Tabla de Hechos principal)
                            folio_individual = f"{grupo_id}-{idx+1}"
                            insertar_folio({
                                "folio": folio_individual,
                                "grupo_id": grupo_id,
                                "id_alumno": id_alum_final,
                                "id_coach": id_coach,
                                "tipo_clase": "Particular",
                                "cancha": nombre_c,
                                "hora_inicio": hora_p,
                                "duracion_minutos": int(DURACIONES[duracion_p] * 60),
                                "fecha_inicio": str(fi_p),
                                "fecha_fin": str(ff_p),
                                "total_base": costo_por_alumno,
                                "pagado": 0,
                                "estatus": "Pendiente"
                            })
                            
                        # Insertamos los Días para el Mapa de Calor (Power BI)
                        # Buscamos el ID interno (UUID) del folio recién creado
                        import time
                        time.sleep(1) # Pequeña pausa para asegurar la escritura
                        refrescar_tabla("fact_folios")
                        df_f = st.session_state['db_folios']
                        ids_folios = df_f[df_f['grupo_id'] == grupo_id]['id'].tolist()
                        
                        dias_mapa_calor = []
                        for id_f in ids_folios:
                            for d in dias_p:
                                dias_mapa_calor.append({"id_folio": id_f, "dia_semana": d})
                        
                        insertar_folio_dias(dias_mapa_calor)

                    st.success(f"¡Grupo {grupo_id} agendado correctamente! Deuda lista en Caja.")
                    st.balloons()
