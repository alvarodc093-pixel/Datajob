"""
DataJobs Radar - pagina: explorar ofertas
Tabla navegable de ofertas con filtros por texto y rol.
"""

import streamlit as st

from paginas.comunes import filtros_basicos
from skills import detectar_rol


def pagina() -> None:
    st.title("Explorar ofertas")
    df, _ = filtros_basicos()

    if df.empty:
        st.warning("No hay ofertas para los filtros seleccionados.")
        return

    df = df.copy()
    df["rol"] = df["title"].apply(detectar_rol)
    df["remoto_txt"] = df["remote"].map({1: "Sí", 0: "No"})

    col1, col2 = st.columns([2, 1])
    with col1:
        busqueda = st.text_input(
            "Buscar por palabra clave (título, empresa, descripción)",
            placeholder="p.ej. python, sql, remoto...",
        )
    with col2:
        roles = sorted(df["rol"].dropna().unique())
        rol_sel = st.selectbox("Rol", ["Todos"] + roles)

    vista = df.copy()
    if busqueda:
        mascara = (
            vista["title"].str.contains(busqueda, case=False, na=False, regex=False)
            | vista["company"].str.contains(busqueda, case=False, na=False, regex=False)
            | vista["description"].str.contains(busqueda, case=False, na=False, regex=False)
        )
        vista = vista[mascara]
    if rol_sel != "Todos":
        vista = vista[vista["rol"] == rol_sel]

    st.caption(f"{len(vista)} ofertas en la vista actual.")

    columnas = ["title", "company", "pais_nombre", "location_display",
                "salary_min", "salary_max", "salary_currency",
                "contract_type", "remoto_txt", "rol", "redirect_url"]
    vista = vista[columnas].rename(columns={
        "title": "Título", "company": "Empresa", "pais_nombre": "País",
        "location_display": "Ubicación", "salary_min": "Mínimo",
        "salary_max": "Máximo", "salary_currency": "Moneda",
        "contract_type": "Contrato", "remoto_txt": "Remoto", "rol": "Rol",
        "redirect_url": "Enlace"})
    vista["Enlace"] = vista["Enlace"].fillna("").map(
        lambda u: f"[Abrir]({u})" if u else "")

    st.dataframe(
        vista,
        hide_index=True,
        width="stretch",
        column_config={
            "Enlace": st.column_config.LinkColumn("Enlace"),
            "Mínimo": st.column_config.NumberColumn(format="%d"),
            "Máximo": st.column_config.NumberColumn(format="%d"),
        },
    )
