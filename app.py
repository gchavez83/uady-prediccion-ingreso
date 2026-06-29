"""Synapse · Analítica de Ingreso UADY — entrypoint multipágina (IA Enterprise).

Portada → Modelo Predictivo (ML) · Dashboard Analítico (BI).
El tema y la configuración global se aplican aquí; cada vista vive en views/.
"""
from __future__ import annotations
from pathlib import Path
import streamlit as st

from lib.theme import inject_theme

ROOT = Path(__file__).resolve().parent
ICON = ROOT / "assets" / "icon.png"

st.set_page_config(
    page_title="Synapse · Ingreso UADY",
    page_icon=str(ICON) if ICON.exists() else "🔷",
    layout="wide",
)
inject_theme()

landing = st.Page("views/landing.py", title="Inicio", icon="🔷", default=True)
modelo = st.Page("views/prediccion.py", title="Modelo Predictivo", icon="🎯", url_path="modelo")
resumen = st.Page("views/resumen.py", title="Resumen", icon="📊", url_path="resumen")
comparativo = st.Page("views/comparativo.py", title="Comparativo", icon="📋", url_path="comparativo")
tendencia = st.Page("views/tendencia.py", title="Tendencia", icon="📈", url_path="tendencia")
clusters = st.Page("views/clusters.py", title="Clústers", icon="🔵", url_path="clusters")
folio = st.Page("views/folio.py", title="Consulta por Folio", icon="🔎", url_path="folio")

pg = st.navigation({
    "Synapse": [landing],
    "Modelo": [modelo],
    "Dashboard": [resumen, comparativo, tendencia, clusters, folio],
})
pg.run()
