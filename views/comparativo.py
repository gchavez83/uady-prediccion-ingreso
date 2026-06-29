"""P2 · Comparativo — tabla de varianza por programa vs año anterior (Zebra BI)."""
from __future__ import annotations
import streamlit as st

from lib.data import load_fact, COL_CICLO, ALL
from lib import metrics as M
from lib import tables
from lib.filters import cycle_campus

df = load_fact()
cs = sorted(int(c) for c in df[COL_CICLO].unique())

st.markdown('<div class="syn-eyebrow">Dashboard · Comparativo</div>', unsafe_allow_html=True)
st.title("Comparativo por ciclo")

# Selector de métrica (una a la vez)
key = st.segmented_control(
    "Métrica a analizar", options=M.KEYS,
    format_func=lambda k: M.METRICS[k]["label"], default="sustentantes", key="p2_metric",
) or "sustentantes"

ciclo, campus, scope = cycle_campus(df, key="p2")
prev = ciclo - 1 if (ciclo - 1) in cs else None
ámbito = "todos los campus" if campus == ALL else campus

st.markdown(
    f"**{M.METRICS[key]['label']}** por licenciatura en **{ámbito}**, ciclo **{ciclo}** "
    f"comparado contra {prev if prev else '—'}. Las barras muestran la variación "
    f"**absoluta (ΔPY)** y **relativa (ΔPY %)**; los subtotales por campus y el total "
    f"se **recalculan** (no se suman) según la métrica."
)

rows = tables.build_rows(scope, key, ciclo, prev)
st.markdown(tables.variance_table_html(rows, key), unsafe_allow_html=True)
st.caption("🟦 Navy = variación positiva · 🟥 Rojo = variación negativa vs año anterior.")
