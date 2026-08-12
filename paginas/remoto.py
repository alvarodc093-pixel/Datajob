"""
DataJobs Radar - pagina: ofertas remotas
Analisis del teletrabajo por pais y rol.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from paginas.comunes import filtros_basicos
from skills import detectar_rol


def pagina() -> None:
    st.title("Ofertas remotas")
    df, _ = filtros_basicos()

    if df.empty:
        st.warning("No hay ofertas para los filtros seleccionados.")
        return

    df = df.copy()
    df["rol"] = df["title"].apply(detectar_rol)

    pct_global = df["remote"].mean() * 100
    with st.container(horizontal=True):
        st.metric("Ofertas remotas", f"{int(df['remote'].sum())}", border=True)
        st.metric("% remoto del total filtrado", f"{pct_global:.1f}%", border=True)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Remoto por país")
            por_pais = (df.groupby("pais_nombre")["remote"]
                        .agg(["sum", "count"]).reset_index())
            por_pais["% remoto"] = por_pais["sum"] / por_pais["count"] * 100
            por_pais = por_pais.sort_values("% remoto", ascending=True)
            if not por_pais.empty:
                fig = px.bar(por_pais, x="% remoto", y="pais_nombre",
                             orientation="h",
                             labels={"% remoto": "% remoto",
                                     "pais_nombre": "País"},
                             hover_data=["count"])
                fig.update_layout(height=420,
                                  margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Sin datos.")

    with col2:
        with st.container(border=True):
            st.subheader("Remoto por rol")
            por_rol = (df.dropna(subset=["rol"]).groupby("rol")["remote"]
                       .agg(["sum", "count"]).reset_index())
            por_rol["% remoto"] = por_rol["sum"] / por_rol["count"] * 100
            por_rol = por_rol.sort_values("% remoto", ascending=True)
            if not por_rol.empty:
                fig = px.bar(por_rol, x="% remoto", y="rol",
                             orientation="h",
                             labels={"% remoto": "% remoto", "rol": "Rol"},
                             hover_data=["count"])
                fig.update_layout(height=420,
                                  margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Sin datos.")

    st.divider()
    with st.container(border=True):
        st.subheader("¿Cómo detectamos el remoto?")
        st.markdown(
            "Adzuna no tiene filtro de remoto en su API. Marcamos una oferta "
            "como remota cuando el título, la ubicación o la descripción "
            "contienen palabras como *remote*, *work from home*, *teletrabajo*, "
            "*home office*, *100% remoto*, etc."
        )
