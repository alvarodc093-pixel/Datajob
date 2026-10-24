"""
DataJobs Radar - pagina: chat RAG
Chat que responde preguntas sobre las ofertas usando Chroma (recuperacion)
+ un LLM local via Ollama (generacion).

Sin Ollama, el chat sigue funcionando: responde solo con los datos
recuperados de Chroma (modo "datos").
"""

import os
import tomllib
from pathlib import Path

import chromadb
import streamlit as st
from openai import OpenAI

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
def obtener_cliente_llm() -> tuple[OpenAI | None, str]:
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

    try:
        coleccion = obtener_coleccion()
    except Exception:
        st.warning(
            "No hay colección Chroma. Ejecuta primero: "
            "`python preparar_corpus.py`"
        )
        coleccion = None

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
                st.write("No hay datos indexados todavía.")
            else:
                resultados = recuperar(coleccion, prompt, k)
                if not resultados:
                    st.write(
                        "No he encontrado ofertas relacionadas. Prueba a "
                        "preguntar sobre habilidades, salarios, remoto o país.")
                else:
                    contexto = formato_contexto(resultados)
                    respuesta = generar_respuesta(
                        prompt, contexto, st.session_state.messages[:-1])
                    if isinstance(respuesta, str):
                        st.write(respuesta)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": respuesta})
                    else:
                        texto = st.write_stream(respuesta)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": texto})

        st.rerun()
