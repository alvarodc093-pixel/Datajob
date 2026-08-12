"""
DataJobs Radar - consultas.py
Funciones de acceso a datos (SQLite) para la app y el EDA.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).parent / "datos.db"

PAISES = {
    "es": "España", "de": "Alemania", "fr": "Francia", "nl": "Países Bajos",
    "pl": "Polonia", "it": "Italia", "at": "Austria", "be": "Bélgica",
    "ch": "Suiza",
}


def conectar() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def cargar_ofertas(filtro_pais: list[str] | None = None,
                   solo_remotas: bool = False) -> pd.DataFrame:
    """Carga las ofertas de la base. Acepta filtros opcionales."""
    conn = conectar()
    sql = "SELECT * FROM ofertas WHERE 1=1"
    params: list = []
    if filtro_pais:
        marcadores = ", ".join("?" for _ in filtro_pais)
        sql += f" AND country IN ({marcadores})"
        params += filtro_pais
    if solo_remotas:
        sql += " AND remote = 1"
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    if "country" in df:
        df["pais_nombre"] = df["country"].map(PAISES).fillna(df["country"])
    return df


def resumen(df: pd.DataFrame) -> dict:
    """KPIs basicos del dataset (puede estar filtrado)."""
    con_salario = df.dropna(subset=["salary_min"]).copy()
    con_salario_eur = (
        con_salario[con_salario["salary_currency"] == "EUR"]
        if not con_salario.empty else con_salario
    )
    sal_medio = (
        ((con_salario_eur["salary_min"] + con_salario_eur["salary_max"]) / 2)
        if not con_salario_eur.empty else pd.Series(dtype=float)
    )
    return {
        "ofertas": len(df),
        "remotas": int(df["remote"].sum()) if not df.empty else 0,
        "con_salario": len(con_salario),
        "salario_mediana": round(float(sal_medio.median()), 0)
        if not sal_medio.empty else None,
        "paises": df["pais_nombre"].nunique() if not df.empty else 0,
    }
