"""
DataJobs Radar - pagina: salarios
Comparativa de salarios por pais, rol y tipo.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from paginas.comunes import barra_h, filtros_basicos
from skills import detectar_rol


def pagina() -> None:
    st.title("Salarios")
    df, _ = filtros_basicos()

    if df.empty:
        st.warning("No hay ofertas para los filtros seleccionados.")
        return

    df = df.copy()
    df["salario_medio"] = (df["salary_min"] + df["salary_max"]) / 2
    df["rol"] = df["title"].apply(detectar_rol)
    con_salario = df.dropna(subset=["salario_medio"])

    if con_salario.empty:
        st.info("Ninguna oferta de los filtros actuales incluye salario "
                "(Adzuna solo publica salario en una parte de las ofertas).")
        return

    st.caption(
        f"{len(con_salario)} ofertas con salario publicado "
        f"({len(con_salario) / len(df):.0%} del total filtrado). "
        "Adzuna solo publica salario en una parte de las ofertas."
    )

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Salario por país (EUR)")
            euro = con_salario[con_salario["salary_currency"] == "EUR"]
            if not euro.empty:
                fig = px.box(euro, x="pais_nombre", y="salario_medio",
                             labels={"pais_nombre": "País",
                                     "salario_medio": "Salario medio (EUR/año)"})
                fig.update_layout(height=420,
                                  margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Sin datos en EUR.")

    with col2:
        with st.container(border=True):
            st.subheader("Salario por rol (EUR)")
            roles = euro.dropna(subset=["rol"])
            if not roles.empty:
                mediana = (roles.groupby("rol")["salario_medio"]
                           .median().sort_values(ascending=True))
                fig = barra_h(mediana, "Mediana salarial (EUR)", "Rol")
                fig.update_layout(height=420,
                                  margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Sin datos.")

    st.divider()
    with st.container(border=True):
        st.subheader("Detalle de salarios")
        columnas = ["title", "company", "pais_nombre", "salary_min",
                    "salary_max", "salary_currency", "rol", "remote"]
        vista = con_salario[columnas].rename(columns={
            "title": "Título", "company": "Empresa", "pais_nombre": "País",
            "salary_min": "Mínimo", "salary_max": "Máximo",
            "salary_currency": "Moneda", "rol": "Rol",
            "remote": "Remoto"})
        vista["Remoto"] = vista["Remoto"].map({1: "Sí", 0: "No"})
        st.dataframe(vista, hide_index=True, width="stretch")
