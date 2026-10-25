"""
DataJobs Radar - pagina: habilidades
Top skills, comparativa por rol y por tecnología.
"""

from collections import Counter

import pandas as pd
import plotly.express as px
import streamlit as st

from paginas.comunes import barra_h, filtros_basicos
from skills import detectar_rol, detectar_skills


def _skills_por_fila(df: pd.DataFrame) -> pd.Series:
    return df.apply(
        lambda r: detectar_skills(str(r["title"]) + " " + str(r["description"])),
        axis=1,
    )


def pagina() -> None:
    st.title("Habilidades y tecnologías")
    df, _ = filtros_basicos()

    if df.empty:
        st.warning("No hay ofertas para los filtros seleccionados.")
        return

    df = df.copy()
    df["skills"] = _skills_por_fila(df)
    conteo = Counter(s for lista in df["skills"] for s in lista)
    if not conteo:
        st.info("No se detectaron skills en estas ofertas.")
        return

    top = pd.Series(conteo).sort_values(ascending=False).head(20)

    with st.container(border=True):
        st.subheader("Top 20 habilidades más demandadas")
        fig = barra_h(top.sort_values(), "Ofertas", "Skill")
        fig.update_layout(height=600, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, width="stretch")

    df["rol"] = df["title"].apply(detectar_rol)
    df_rol = df[df["rol"].notna()].copy()

    if not df_rol.empty:
        st.divider()
        st.subheader("Habilidades por rol")
        roles = df_rol["rol"].unique()
        habilidades = sorted(set(conteo.keys()))
        matriz = pd.DataFrame(0, index=roles, columns=habilidades)
        for rol, grupo in df_rol.groupby("rol"):
            for lista in grupo["skills"]:
                for s in lista:
                    if s in matriz.columns:
                        matriz.loc[rol, s] += 1

        top_skills = matriz.sum().sort_values(ascending=False).head(12).index
        with st.container(border=True):
            fig = px.imshow(
                matriz[top_skills].T, color_continuous_scale="Blues",
                labels=dict(color="Ofertas"),
                title="Frecuencia de habilidades por rol",
            )
            fig.update_yaxes(title="Skill")
            fig.update_layout(height=550, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, width="stretch")

    st.divider()
    st.subheader("¿Qué deberías aprender?")
    cols = st.columns(3)
    sugerencias = [
        ("SQL + Python", "Aparecen en la mayoría de ofertas de análisis de datos. "
         "Son la base no negociable."),
        ("Power BI / Tableau", "La visualización y el reporting son el día a día "
         "del Data Analyst; Power BI domina en Europa."),
        ("Estadística + negocio", "Tests de hipótesis, métricas y entender el "
         "negocio distinguen al analista senior."),
    ]
    for col, (titulo, texto) in zip(cols, sugerencias):
        with col:
            with st.container(border=True):
                st.markdown(f"**{titulo}**")
                st.write(texto)
