"""
DataJobs Radar - pagina: vision general
KPIs del dataset y contexto del problema.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from paginas.comunes import filtros_basicos


def pagina() -> None:
    st.title("Visión general")
    st.markdown(
        "¿Qué buscan realmente las empresas cuando contratan **Data Analysts**? "
        "Este proyecto analiza ofertas reales de España y Europa descargadas de "
        "la API de Adzuna."
    )

    df, kpi = filtros_basicos()

    with st.container(horizontal=True):
        st.metric("Ofertas analizadas", f"{kpi['ofertas']:,}", border=True)
        st.metric("Países", kpi["paises"], border=True)
        st.metric("Ofertas remotas", f"{kpi['remotas']}", border=True)
        st.metric(
            "Mediana salarial (EUR)",
            f"{kpi['salario_mediana']:,.0f} €" if kpi["salario_mediana"] else "n/d",
            border=True,
        )

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Ofertas por país")
            conteo = (df["pais_nombre"].value_counts()
                      .sort_values(ascending=True))
            if not conteo.empty:
                fig = px.bar(conteo, orientation="h",
                             labels={"value": "Ofertas", "index": "País"})
                fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Sin datos para los filtros seleccionados.")

    with col2:
        with st.container(border=True):
            st.subheader("Distribución por tipo de contrato")
            contratos = df["contract_type"].fillna("No especificado").value_counts()
            if not contratos.empty:
                fig = px.pie(contratos, names=contratos.index,
                             hole=0.4)
                fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Sin datos.")

    with st.expander("¿Qué preguntas responde el proyecto?"):
        st.markdown(
            """
            - ¿Qué habilidades piden más para Data Analyst?
            - ¿Cuánto se ofrece de salario?
            - ¿Qué diferencia hay entre Data Analyst, BI Analyst y Data Scientist?
            - ¿Qué tecnologías aparecen más (SQL, Python, Power BI, Excel...)?
            - ¿Qué porcentaje de ofertas son remotas?
            - ¿Qué países y ciudades tienen más oportunidades?
            - ¿Qué experiencia se solicita?
            - ¿Qué debería aprender alguien que quiere ser Data Analyst?
            """
        )
