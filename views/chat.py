"""Pregúntale a Synapse — chat IA en lenguaje natural sobre los datos de ingreso UADY.

Usa la API de Anthropic con *tool use*: Claude traduce la pregunta a una llamada
de herramienta (consultar_metrica / consulta_sql) y el número lo computa el código.
Autocontenido: no requiere modelo PBI ni túnel MCP.
"""
from __future__ import annotations
import os

import streamlit as st

from lib import chat_tools as T
from lib.theme import INK, AZURE, AMBER, SLATE

# Modelo: sonnet-4-6 (app pública, tarea sencilla, costo bajo). Sube a "claude-opus-4-8" si quieres más razonamiento.
MODEL = "claude-sonnet-4-6"
MAX_TOOL_ROUNDS = 6

SYSTEM = T.SCHEMA_DOC + """

# TU ROL
Eres el asistente analítico de "Synapse · Ingreso UADY". Respondes preguntas sobre la admisión
a licenciatura de la UADY en lenguaje natural, con datos exactos.

Reglas:
- SIEMPRE obtén los números con las herramientas; NUNCA inventes ni estimes cifras.
- Para las 7 métricas oficiales usa `consultar_metrica` (cálculo garantizado, incluido el Punto de Corte).
- Para rankings, comparativos, top-N, listados o cualquier otra cosa, usa `consulta_sql`.
- Responde en español, claro y conciso. Da el número y una frase de contexto; no recites tu proceso.
- Si la pregunta pide algo que NO está en los datos (p. ej. cupo oficial, datos de otra universidad),
  dilo claramente en vez de inventar.
"""

SUGGESTIONS = [
    "¿Cuántos alumnos ingresaron a MKT en 2026?",
    "¿Cuál es la licenciatura más difícil de la UADY en 2026?",
    "% de ingreso de Médico Cirujano por ciclo",
    "Top 5 licenciaturas por punto de corte Ceneval en 2026",
]


def _client():
    key = ""
    try:
        key = st.secrets["ANTHROPIC_API_KEY"]
    except (KeyError, FileNotFoundError):
        key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        st.warning(
            "Falta la **API key de Anthropic**. Configúrala en `ANTHROPIC_API_KEY` "
            "(Secrets de Streamlit Cloud, o `.streamlit/secrets.toml` en local)."
        )
        st.stop()
    import anthropic
    return anthropic.Anthropic(api_key=key)


def _answer(client, api_messages: list) -> str:
    """Loop agéntico: ejecuta herramientas hasta que el modelo dé la respuesta final."""
    for _ in range(MAX_TOOL_ROUNDS):
        resp = client.messages.create(
            model=MODEL, max_tokens=2048, system=SYSTEM, tools=T.TOOLS, messages=api_messages,
        )
        api_messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text")
        results = []
        for b in resp.content:
            if b.type == "tool_use":
                results.append({"type": "tool_result", "tool_use_id": b.id,
                                "content": T.run_tool(b.name, b.input)})
        api_messages.append({"role": "user", "content": results})
    return "No pude resolver la consulta en los pasos disponibles. Reformúlala, por favor."


# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown('<div class="syn-eyebrow">Nodo IA · Lenguaje natural</div>', unsafe_allow_html=True)
st.title("Pregúntale a Synapse")

if "api" not in st.session_state:
    st.session_state.api = []
if "pending" not in st.session_state:
    st.session_state.pending = None

if not st.session_state.api:
    st.caption("Pregunta en lenguaje natural sobre la admisión a licenciatura UADY 2022–2026. "
               "Las respuestas se calculan sobre los datos reales — sin inventar cifras.")
    cols = st.columns(2)
    for i, q in enumerate(SUGGESTIONS):
        if cols[i % 2].button(q, key=f"sug_{i}", use_container_width=True):
            st.session_state.pending = q
            st.rerun()

# Historial (renderiza solo texto de user/assistant; oculta bloques de herramienta)
for msg in st.session_state.api:
    if msg["role"] == "user" and isinstance(msg["content"], str):
        with st.chat_message("user"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        text = "".join(b.text for b in msg["content"] if getattr(b, "type", None) == "text")
        if text:
            with st.chat_message("assistant"):
                st.markdown(text)

user_input = st.session_state.pending or st.chat_input("Escribe tu pregunta…")
st.session_state.pending = None

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.api.append({"role": "user", "content": user_input})
    client = _client()
    with st.chat_message("assistant"):
        with st.spinner("Consultando los datos…"):
            try:
                reply = _answer(client, st.session_state.api)
            except Exception as exc:  # noqa: BLE001
                reply = f"Error al consultar el modelo: {exc}"
        st.markdown(reply)
    st.rerun()
