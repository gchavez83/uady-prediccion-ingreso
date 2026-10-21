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

# Modelo: Haiku 5.5 (app pública, tarea sencilla de tool use, costo mínimo: $0.10/$0.50 por MTok).
# Sube a "claude-sonnet-5-5" si quieres más razonamiento. Haiku 5.5 piensa de forma adaptativa
# por defecto; effort "low" basta para traducir la pregunta a una llamada de herramienta.
MODEL = "claude-haiku-5-5"
EFFORT = "low"
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


def _text_of(content) -> str:
    """Concatena los bloques de texto de un mensaje (objetos del SDK o dicts)."""
    if isinstance(content, str):
        return content
    out = []
    for b in content:
        btype = b.get("type") if isinstance(b, dict) else getattr(b, "type", None)
        if btype == "text":
            out.append(b["text"] if isinstance(b, dict) else b.text)
    return "".join(out)


def _answer(client, api_messages: list) -> str:
    """Loop agéntico: ejecuta herramientas hasta que el modelo dé la respuesta final.

    Los bloques `thinking` que devuelve el modelo se reenvían intactos (van dentro de
    resp.content); nunca se editan turnos anteriores, solo se agrega al final.
    """
    for _ in range(MAX_TOOL_ROUNDS):
        resp = client.messages.create(
            model=MODEL, max_tokens=4096, output_config={"effort": EFFORT},
            system=SYSTEM, tools=T.TOOLS, messages=api_messages,
        )
        api_messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason == "refusal":
            return "No puedo responder esa pregunta. Intenta reformularla."
        if resp.stop_reason != "tool_use":
            return _text_of(resp.content)
        results = []
        for b in resp.content:
            if b.type == "tool_use":
                results.append({"type": "tool_result", "tool_use_id": b.id,
                                "content": T.run_tool(b.name, b.input)})
        api_messages.append({"role": "user", "content": results})
    fallback = "No pude resolver la consulta en los pasos disponibles. Reformúlala, por favor."
    api_messages.append({"role": "assistant", "content": [{"type": "text", "text": fallback}]})
    return fallback


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
        text = _text_of(msg["content"])
        if text:
            with st.chat_message("assistant"):
                st.markdown(text)

user_input = st.session_state.pending or st.chat_input("Escribe tu pregunta…")
st.session_state.pending = None

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    n_before = len(st.session_state.api)
    st.session_state.api.append({"role": "user", "content": user_input})
    client = _client()
    with st.chat_message("assistant"):
        with st.spinner("Consultando los datos…"):
            try:
                reply = _answer(client, st.session_state.api)
            except Exception as exc:  # noqa: BLE001
                # Deshacer este intento (solo se recorta el final del historial) y dejar
                # el error visible: sin rerun, para que no desaparezca de la pantalla.
                del st.session_state.api[n_before:]
                st.error(
                    "No pude obtener respuesta del modelo. Intenta de nuevo en unos segundos.\n\n"
                    f"Detalle técnico: `{type(exc).__name__}: {str(exc)[:300]}`"
                )
                st.stop()
        st.markdown(reply)
    st.rerun()
