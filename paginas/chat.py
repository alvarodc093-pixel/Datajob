"""
DataJobs Radar - pagina: chat RAG
Chat que responde preguntas sobre las ofertas usando Chroma (recuperacion)
+ un LLM local via Ollama (generacion).

Sin Ollama, el chat sigue funcionando: responde solo con los datos
recuperados de Chroma (modo "datos"). Sin Chroma (demo web con stlite),
responde con cifras calculadas sobre las ofertas.
"""

import os
import tomllib
from pathlib import Path

from collections import Counter

import streamlit as st

from consultas import PAISES, cargar_ofertas
from skills import detectar_rol, detectar_skills

try:
    import chromadb
    from openai import OpenAI
except ImportError:  # demo web (stlite): sin Chroma ni cliente de LLM
    chromadb = None
    OpenAI = None

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
COLLECTION = "ofertas"


def _config_ollama() -> dict:
    """Config de Ollama desde st.secrets o el secrets.toml del proyecto."""
    cfg = st.secrets.get("ollama") or {}
    if not cfg.get("base_url"):
        ruta = Path(__file__).resolve().parent.parent / "secrets.toml"
        try:
            with ruta.open("rb") as f:
                cfg = tomllib.load(f).get("ollama") or {}
        except (OSError, tomllib.TOMLDecodeError):
            cfg = {}
    return cfg

SUGERENCIAS = {
    ":blue[:material/query_stats:] ¿Qué habilidades piden más?": (
        "¿Qué habilidades piden más las empresas para data analyst?"),
    ":green[:material/euro:] ¿Cuánto se paga en Alemania?": (
        "¿Cuánto se ofrece de salario en Alemania para data analyst?"),
    ":orange[:material/home_work:] ¿Hay ofertas remotas?": (
        "¿Qué porcentaje de ofertas son remotas y para qué roles?"),
    ":violet[:material/school:] ¿Qué debería aprender?": (
        "¿Qué skills debería aprender alguien que quiere ser data analyst?"),
}


@st.cache_resource
def obtener_coleccion():
    client = chromadb.PersistentClient(path=DB_DIR)
    return client.get_collection(COLLECTION)


@st.cache_resource
def obtener_cliente_llm():
    if OpenAI is None:
        return None, ""
    cfg = _config_ollama()
    base_url = cfg.get("base_url")
    model = cfg.get("model")
    if not base_url or not model:
        return None, ""
    try:
        cliente = OpenAI(base_url=base_url, api_key="ollama")
        return cliente, model
    except Exception:
        return None, ""


def recuperar(coleccion, pregunta: str, k: int) -> list[dict]:
    """Busca las k ofertas mas relevantes en Chroma."""
    try:
        resultados = coleccion.query(
            query_texts=[pregunta], n_results=k, include=["documents", "metadatas"]
        )
    except Exception:
        return []
    docs = (resultados.get("documents") or [[]])[0]
    metas = (resultados.get("metadatas") or [[]])[0]
    return [{"documento": d, "metadatos": m}
            for d, m in zip(docs, metas) if d]


def respuesta_con_datos(pregunta: str, k: int) -> str:
    """Modo sin Chroma: responde a las preguntas típicas con cifras de las ofertas."""
    p = pregunta.lower()
    df = cargar_ofertas()
    pais = next((c for c, n in PAISES.items() if n.lower() in p), None)
    if pais:
        df = df[df["country"] == pais]
    ambito = f" en {PAISES[pais]}" if pais else ""
    if df.empty:
        return "No hay ofertas para ese país."

    if any(w in p for w in ("salario", "sueldo", "paga", "cobra")):
        sal = df.dropna(subset=["salary_min", "salary_max"])
        sal = sal[sal["salary_currency"] == "EUR"]
        if sal.empty:
            return f"Ninguna oferta{ambito} publica salario en euros."
        medio = (sal["salary_min"] + sal["salary_max"]) / 2
        por_rol = medio.groupby(sal["title"].map(detectar_rol)).median().dropna()
        lineas = [f"- {rol}: {v:,.0f} €".replace(",", ".") for rol, v in por_rol.sort_values(ascending=False).items()]
        return (f"Mediana salarial{ambito}: **{medio.median():,.0f} €/año**".replace(",", ".")
                + f" ({len(sal)} ofertas con salario en euros).\n\n" + "\n".join(lineas))

    if any(w in p for w in ("remot", "teletrabajo", "casa")):
        roles = df["title"].map(detectar_rol)
        pct = df.groupby(roles)["remote"].mean().mul(100).sort_values(ascending=False)
        lineas = [f"- {rol}: {v:.1f} %" for rol, v in pct.items()]
        return (f"**{df['remote'].mean() * 100:.1f} %** de las ofertas{ambito} son remotas "
                f"({int(df['remote'].sum())} de {len(df)}).\n\n" + "\n".join(lineas))

    if any(w in p for w in ("habilidad", "skill", "aprender", "tecnolog", "piden")):
        analistas = df[df["title"].map(detectar_rol).isin(["Data Analyst", "BI Analyst"])]
        base = analistas if not analistas.empty else df
        conteo = Counter(s for t, d in zip(base["title"], base["description"].fillna(""))
                         for s in detectar_skills(f"{t} {d}"))
        lineas = [f"{i}. {s}: {n} ofertas" for i, (s, n) in enumerate(conteo.most_common(8), 1)]
        return (f"Habilidades más pedidas en {len(base)} ofertas de Data/BI Analyst{ambito}:\n\n"
                + "\n".join(lineas))

    palabras = [w for w in p.replace("?", " ").replace("¿", " ").split() if len(w) > 3]
    texto = (df["title"] + " " + df["description"].fillna("")).str.lower()
    mascara = texto.apply(lambda t: all(w in t for w in palabras)) if palabras else texto.astype(bool)
    encontradas = df[mascara].head(k)
    if encontradas.empty:
        return "No he encontrado ofertas relacionadas. Prueba con habilidades, salarios, remoto o un país."
    lineas = [f"- {r.title} · {r.company} · {r.location_display}" for r in encontradas.itertuples()]
    return f"Ofertas relacionadas{ambito}:\n\n" + "\n".join(lineas)


def formato_contexto(resultados: list[dict]) -> str:
    # Cada documento ya es la ficha completa de preparar_corpus.py: titulo,
    # empresa, ubicacion, salario, remoto y descripcion.
    return "\n\n".join(f"[{i}] {r['documento']}"
                       for i, r in enumerate(resultados, 1))


def generar_respuesta(pregunta: str, contexto: str,
                      historial: list[dict]) -> str:
    cliente, model = obtener_cliente_llm()
    if not cliente:
        return (
            "Solo tengo datos (Ollama no está conectado). Respuesta basada en "
            f"las ofertas recuperadas:\n\n{contexto[:2000]}"
        )

    system = (
        "Eres DataJobs Radar, un asistente que responde preguntas sobre "
        "ofertas de empleo de data analyst, bi analyst y data scientist en "
        "España y Europa. Responde usando SOLO la información de las ofertas "
        "recuperadas (contexto). Si no hay datos suficientes, dilo. "
        "Sé concreto, usa números y porcentajes cuando puedas. Responde en "
        "el idioma de la pregunta.\n\nContexto de ofertas recuperadas:\n"
        f"{contexto}"
    )
    mensajes = [{"role": "system", "content": system}]
    for m in historial[-6:]:
        mensajes.append({"role": m["role"], "content": m["content"]})
    mensajes.append({"role": "user", "content": pregunta})

    respuesta = cliente.chat.completions.create(
        model=model,
        messages=mensajes,
        stream=True,
        temperature=0.2,
    )
    return respuesta  # objeto stream, lo consume st.write_stream


def pagina() -> None:
    st.title("Chat con tus datos")

    st.caption(
        "Pregunta sobre las ofertas descargadas. El chat recupera las más "
        "relevantes de Chroma y las usa como contexto. "
        "Conecta Ollama para respuestas generadas por IA; sin él, responde "
        "con los datos recuperados directamente."
    )

    with st.sidebar:
        k = st.slider("Nº de ofertas recuperadas (k)", 1, 10, 5)
        if st.button("Borrar conversación"):
            st.session_state.messages = []
            st.rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    coleccion = None
    if chromadb is None:
        st.info("Versión web: el chat responde con cifras calculadas sobre las "
                "ofertas (sin búsqueda semántica ni LLM).")
    else:
        try:
            coleccion = obtener_coleccion()
        except Exception:
            st.info("No hay colección Chroma (`python preparar_corpus.py`); "
                    "el chat responde con cifras calculadas sobre las ofertas.")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    sugerencia = None
    if not st.session_state.messages:
        seleccion = st.pills(
            "Prueba a preguntar:",
            list(SUGERENCIAS.keys()),
            label_visibility="collapsed",
        )
        if seleccion:
            sugerencia = SUGERENCIAS[seleccion]

    # Una sugerencia pulsada sigue el mismo camino que una pregunta escrita.
    prompt = st.chat_input(
        "Pregunta sobre las ofertas...", submit_mode="disable") or sugerencia

    if prompt:
        st.session_state.messages.append(
            {"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            if coleccion is None:
                respuesta = respuesta_con_datos(prompt, k)
            else:
                resultados = recuperar(coleccion, prompt, k)
                if not resultados:
                    respuesta = ("No he encontrado ofertas relacionadas. Prueba a "
                                 "preguntar sobre habilidades, salarios, remoto o país.")
                else:
                    respuesta = generar_respuesta(
                        prompt, formato_contexto(resultados), st.session_state.messages[:-1])
            if isinstance(respuesta, str):
                st.write(respuesta)
            else:
                respuesta = st.write_stream(respuesta)
            st.session_state.messages.append(
                {"role": "assistant", "content": respuesta})

        st.rerun()
