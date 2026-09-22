import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

def obtener_lista_fechas_wonox(fecha_inicio, fecha_fin, dias_seleccionados):
    if not dias_seleccionados or fecha_fin < fecha_inicio: 
        return []
    mapa_dias = {"Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3, "Viernes": 4, "Sábado": 5, "Domingo": 6}
    dias_num = [mapa_dias[dia] for dia in dias_seleccionados]
    fechas_generadas = []
    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        if fecha_actual.weekday() in dias_num:
            nombre_dia = ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'][fecha_actual.weekday()]
            fechas_generadas.append(f"{nombre_dia} {fecha_actual.strftime('%d/%m/%Y')}")
        fecha_actual += timedelta(days=1)
    return fechas_generadas

def parse_rango_horas(horario_str):
    if " a " in str(horario_str):
        partes = str(horario_str).split(" a ")
        ini = datetime.strptime(partes[0].strip(), "%H:%M").time()
        fin = datetime.strptime(partes[1].strip(), "%H:%M").time()
        return ini, fin
    else:
        try:
            ini = datetime.strptime(str(horario_str).strip(), "%H:%M")
            fin = (ini + timedelta(hours=1)).time()
            return ini.time(), fin
        except:
            return datetime.strptime("00:00", "%H:%M").time(), datetime.strptime("00:00", "%H:%M").time()

def verificar_empalme(cancha, horario_solicitado, fechas_nuevas_str):
    df_folios = st.session_state.get('db_folios', pd.DataFrame())
    if df_folios.empty: return False, None, []
    
    fechas_n = [f.split(" ")[1] for f in fechas_nuevas_str if " " in f]
    
    estatus_ignorados = ['Cancelado', 'Rechazado', 'Eliminado', 'Inactivo', 'Reagendado/Sustituido']
    activos = df_folios[~df_folios['estatus'].isin(estatus_ignorados)]
    ocupados = activos[activos['cancha'] == cancha]
    
    req_ini, req_fin = parse_rango_horas(horario_solicitado)
    
    for _, row in ocupados.iterrows():
        try:
            # Lógica adaptada para la nueva arquitectura BI
            if 'hora_inicio' in row and 'duracion_minutos' in row:
                hora_i_str = str(row['hora_inicio'])[:5] 
                db_ini = datetime.strptime(hora_i_str, "%H:%M").time()
                db_fin = (datetime.combine(datetime.today(), db_ini) + timedelta(minutes=int(row['duracion_minutos']))).time()
            else:
                db_ini, db_fin = parse_rango_horas(row.get('horario', '00:00 a 00:00'))
                
            if (req_ini < db_fin) and (req_fin > db_ini):
                f_ini = pd.to_datetime(row['fecha_inicio']).date()
                f_fin = pd.to_datetime(row['fecha_fin']).date()
                
                # Consultamos los días exactos en la tabla puente de Supabase
                from utils.database import get_supabase
                res = get_supabase().table("fact_folio_dias").select("dia_semana").eq("id_folio", row['id']).execute()
                
                if res.data:
                    dias_lista = [d['dia_semana'] for d in res.data]
                else:
                    dias_lista = []
                
                fechas_existentes = obtener_lista_fechas_wonox(f_ini, f_fin, dias_lista)
                fechas_e = [f.split(" ")[1] for f in fechas_existentes if " " in f]
                
                empalmes = set(fechas_n).intersection(set(fechas_e))
                if empalmes:
                    return True, row.get('folio', 'Desconocido'), list(empalmes)
        except Exception:
            continue
            
    return False, None, []
