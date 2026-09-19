import streamlit as st
from utils.database import inicializar_cache

# Importamos los submódulos que irán en la carpeta Modules/
import Modules.reservas as reservas
import Modules.asistencias as asistencias
import Modules.edicion_rapida as edicion_rapida
import Modules.nomina as nomina

# Configuración base de la app
st.set_page_config(page_title="Marca Padel | POS (BI Ready)", page_icon="🎾", layout="wide")

def main():
    # Carga los catálogos limpios de Power BI a la memoria
    inicializar_cache()

    # Menú Lateral
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/8/8a/Transparent_background.png", width=50) # Tu logo aquí
    st.sidebar.title("🎾 Menú Principal")
    st.sidebar.caption("v2.0 - Arquitectura BI")
    
    opcion = st.sidebar.radio(
        "Navegación",
        ["🛒 Ventas y Reservas", "📋 Asistencias del Día", "⚡ Edición Rápida", "💸 Nómina y Comisiones"]
    )

    st.sidebar.divider()
    st.sidebar.success("🟢 Conexión Segura (Supabase)")

    # Ruteo de módulos
    if opcion == "🛒 Ventas y Reservas":
        reservas.render()
    elif opcion == "📋 Asistencias del Día":
        asistencias.render()
    elif opcion == "⚡ Edición Rápida":
        edicion_rapida.render()
    elif opcion == "💸 Nómina y Comisiones":
        nomina.render()

if __name__ == "__main__":
    main()
