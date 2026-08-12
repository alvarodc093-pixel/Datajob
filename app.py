"""
DataJobs Radar - app.py
Punto de entrada de la app Streamlit con las pestañas:
- Visión general (KPIs y contexto)
- Habilidades y tecnologías
- Salarios
- Ofertas remotas
- Mercado por país
- Explorar ofertas (tabla con filtros)
- Chat RAG
"""

import streamlit as st
from paginas import chat, habilidades, ofertas, pais, remoto, salarios, vision

st.set_page_config(
    page_title="DataJobs Radar",
    page_icon=":material/radar:",
    layout="wide",
)

paginas = {
    "Visión general": vision.pagina,
    "Habilidades": habilidades.pagina,
    "Salarios": salarios.pagina,
    "Ofertas remotas": remoto.pagina,
    "Mercado por país": pais.pagina,
    "Explorar ofertas": ofertas.pagina,
    "Chat RAG": chat.pagina,
}

with st.sidebar:
    st.title("DataJobs Radar")
    st.caption("¿Qué buscan las empresas al contratar Data Analysts?")
    st.divider()
    seleccion = st.radio(
        "Sección",
        list(paginas.keys()),
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Datos: API de Adzuna · España + Europa · SQLite + Chroma")

paginas[seleccion]()
