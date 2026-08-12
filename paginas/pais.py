"""
DataJobs Radar - pagina: mercado por pais
Volumen, ciudades y sectores por pais.
"""

import json

import pandas as pd
import plotly.express as px
import streamlit as st

from paginas.comunes import filtros_basicos


def _ciudad(area_json: str, display: str) -> str:
    """Devuelve la ciudad/region mas concreta razonable de la oferta."""
    if display:
        partes = [p.strip() for p in display.split(",") if p.strip()]
        if partes:
            return partes[0]
    try:
        area = json.loads(area_json or "[]")
        if area:
            return str(area[-1])
    except Exception:
        pass
    return "Desconocida"


def pagina() -> None:
    st.title("Mercado por país")
    df, _ = filtros_basicos(default_todos=False)

    if df.empty:
        st.warning("No hay ofertas para los filtros seleccionados.")
        return

    df = df.copy()
    df["ciudad"] = df.apply(
        lambda r: _ciudad(r["location_area"], r["location_display"]), axis=1)

    with st.container(border=True):
        st.subheader("Volumen de ofertas por país")
        conteo = (df["pais_nombre"].value_counts().sort_values(ascending=True))
        fig = px.bar(conteo, orientation="h",
                     labels={"value": "Ofertas", "index": "País"})
        fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, width="stretch")

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Ciudades con más ofertas")
            top_ciudades = df["ciudad"].value_counts().head(15)
            if not top_ciudades.empty:
                fig = px.bar(top_ciudades.sort_values(), orientation="h",
                             labels={"value": "Ofertas", "index": "Ciudad"})
                fig.update_layout(height=500,
                                  margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Sin datos.")

    with col2:
        with st.container(border=True):
            st.subheader("Sectores que más contratan")
            sectores = (df["category_label"].fillna("No especificado")
                        .value_counts().head(12))
            if not sectores.empty:
                fig = px.bar(sectores.sort_values(), orientation="h",
                             labels={"value": "Ofertas", "index": "Sector"})
                fig.update_layout(height=500,
                                  margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Sin datos.")

    st.divider()
    with st.container(border=True):
        st.subheader("Top empresas contratantes")
        top_empresas = (df["company"].fillna("No especificada")
                        .value_counts().head(15))
        if not top_empresas.empty:
            fig = px.bar(top_empresas.sort_values(), orientation="h",
                         labels={"value": "Ofertas", "index": "Empresa"})
            fig.update_layout(height=500, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, width="stretch")
