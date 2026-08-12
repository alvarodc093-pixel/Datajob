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

from pathlib import Path

import streamlit as st
from paginas import chat, habilidades, ofertas, pais, remoto, salarios, vision

RAIZ = Path(__file__).resolve().parent
HEADER = RAIZ / "assets" / "header.png"
LOGO = RAIZ / "assets" / "logo.png"

st.set_page_config(
    page_title="DataJobs Radar",
    page_icon=":material/radar:",
    layout="wide",
)

st.logo(str(LOGO))

paginas = {
    ":material/space_dashboard: Visión general": vision.pagina,
    ":material/troubleshoot: Habilidades": habilidades.pagina,
    ":material/paid: Salarios": salarios.pagina,
    ":material/laptop_mac: Ofertas remotas": remoto.pagina,
    ":material/public: Mercado por país": pais.pagina,
    ":material/table_chart: Explorar ofertas": ofertas.pagina,
    ":material/chat: Chat RAG": chat.pagina,
}

with st.sidebar:
    st.caption("¿Qué buscan las empresas al contratar Data Analysts?")
    st.divider()
    seleccion = st.radio(
        "Sección",
        list(paginas.keys()),
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Datos: API de Adzuna · España + Europa · SQLite + Chroma")

if HEADER.exists():
    st.image(str(HEADER), width="stretch")

paginas[seleccion]()
