"""
DataJobs Radar - preparar_corpus.py
Construye el corpus de fichas (ofertas de empleo) y lo indexa en Chroma.

Cada ficha contiene: titulo, empresa, ubicacion, pais, salario, remoto y
descripcion. Con ellas se responde el chat RAG.

Ejecucion:
    python preparar_corpus.py            # indexa (o actualiza) el corpus
    python preparar_corpus.py --borrar   # borra la coleccion y reindexa
"""

from __future__ import annotations

import argparse
from pathlib import Path

import chromadb
import pandas as pd

from consultas import cargar_ofertas, PAISES

DB_DIR = Path(__file__).parent / "chroma_db"
COLLECTION = "ofertas"


def construir_fichas(df: pd.DataFrame) -> list[dict]:
    fichas = []
    for _, r in df.iterrows():
        salario = ""
        if pd.notna(r["salary_min"]) or pd.notna(r["salary_max"]):
            smin = r["salary_min"] if pd.notna(r["salary_min"]) else "?"
            smax = r["salary_max"] if pd.notna(r["salary_max"]) else "?"
            salario = f" Salario: {smin} - {smax} {r['salary_currency']}."
        remoto = " Remoto: sí." if r["remote"] == 1 else ""
        ubicacion = (r["location_display"] or "") + " " + \
                     PAISES.get(r["country"], r["country"])
        fichas.append({
            "id": f"oferta_{r['id']}",
            "texto": (
                f"Oferta: {r['title']}. Empresa: {r['company']}."
                f" Ubicación: {ubicacion}.{salario}{remoto}"
                f" Descripción: {r['description']}"
            ),
            "metadatos": {
                "id_original": str(r["id"]),
                "titulo": r["title"],
                "empresa": r["company"],
                "ubicacion": ubicacion,
                "pais": r["country"],
                "pais_nombre": PAISES.get(r["country"], r["country"]),
                "remoto": int(r["remote"]),
                "salario_min": None if pd.isna(r["salary_min"]) else float(r["salary_min"]),
                "salario_max": None if pd.isna(r["salary_max"]) else float(r["salary_max"]),
                "moneda": r["salary_currency"],
                "url": r["redirect_url"],
            },
        })
    return fichas


def main() -> None:
    parser = argparse.ArgumentParser(description="Indexa ofertas en Chroma")
    parser.add_argument("--borrar", action="store_true",
                        help="Borra la coleccion y vuelve a indexar todo")
    args = parser.parse_args()

    client = chromadb.PersistentClient(path=str(DB_DIR))
    if args.borrar:
        try:
            client.delete_collection(COLLECTION)
        except Exception:
            pass

    coleccion = client.get_or_create_collection(COLLECTION)

    df = cargar_ofertas()
    fichas = construir_fichas(df)
    ids = [f["id"] for f in fichas]
    textos = [f["texto"] for f in fichas]
    metas = [f["metadatos"] for f in fichas]

    if ids:
        coleccion.upsert(ids=ids, documents=textos, metadatas=metas)

    print(f"Indexadas {len(ids)} ofertas en la coleccion '{COLLECTION}' "
          f"({client.get_collection(COLLECTION).count()} fichas).")


if __name__ == "__main__":
    main()
