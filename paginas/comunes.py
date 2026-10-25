"""
DataJobs Radar - paginas/comunes.py
Widgets y helpers compartidos por las pestañas de la app.
"""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from consultas import PAISES, cargar_ofertas, resumen


@st.cache_data(ttl="10m")
def datos_cargados(paises: tuple[str, ...], solo_remotas: bool) -> object:
    """Carga las ofertas (cacheada; los filtros se aplican fuera)."""
    return cargar_ofertas(list(paises) if paises else None, solo_remotas)


def selector_paises(default_todos: bool = True) -> list[str]:
    """Selector multiselect de paises en el sidebar."""
    opciones = sorted(PAISES.keys())
    default = opciones if default_todos else ["es"]
    etiquetas = {c: PAISES[c] for c in opciones}
    seleccion = st.sidebar.multiselect(
        "Países",
        options=opciones,
        default=default,
        format_func=lambda c: etiquetas[c],
        placeholder="Todos los países",
    )
    return seleccion


def filtros_basicos(default_todos: bool = True):
    """Filtros comunes: paises + solo remotas. Devuelve (df, kpis)."""
    with st.sidebar:
        paises = selector_paises(default_todos)
        solo_remotas = st.toggle("Solo ofertas remotas", value=False)
    df = datos_cargados(tuple(paises), solo_remotas)
    return df, resumen(df)


def barra_h(serie, eje_valor: str, eje_categoria: str):
    """Barras horizontales desde una Serie {categoría: valor}, con ejes con nombre y sin leyenda."""
    datos = serie.rename_axis(eje_categoria).reset_index(name=eje_valor)
    fig = px.bar(datos, x=eje_valor, y=eje_categoria, orientation="h")
    fig.update_layout(showlegend=False)
    return fig
