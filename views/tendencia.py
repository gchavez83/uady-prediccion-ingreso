"""P3 · Tendencia — small multiples por programa a lo largo de los ciclos."""
from __future__ import annotations
import streamlit as st

from lib.data import load_fact, COL_CICLO, campuses, programas
from lib import metrics as M
from lib import charts

df = load_fact()
cs = sorted(int(c) for c in df[COL_CICLO].unique())

st.markdown('<div class="syn-eyebrow">Dashboard · Tendencia</div>', unsafe_allow_html=True)
st.title("Tendencia por ciclo")

key = st.segmented_control(
    "Métrica a analizar", options=M.KEYS,
    format_func=lambda k: M.METRICS[k]["label"], default="admitidos", key="p3_metric",
) or "admitidos"

c1, c2 = st.columns([1, 2])
with c1:
    campus = st.selectbox("Campus", campuses(df), index=None,
                          placeholder="Selecciona un campus", key="p3_campus")
with c2:
    progs_all = programas(df, campus) if campus else []
    sel = st.multiselect("Programa de licenciatura", progs_all, default=progs_all,
                         key="p3_prog", disabled=not campus)

if not campus:
    st.info("Selecciona un **campus** para ver la tendencia de sus programas de licenciatura.")
    st.stop()

scope = df[df["campus"] == campus]
st.markdown(
    f"Evolución de **{M.METRICS[key]['label']}** {cs[0]}–{cs[-1]} por programa en **{campus}**. "
    f"Las barras muestran el valor de cada ciclo; **▲/▼** la variación vs año anterior (ΔPY) y, "
    f"junto al título, el cambio del último ciclo."
)

if not sel:
    st.info("Selecciona al menos un programa.")
else:
    ncols = 3
    cols = st.columns(ncols)
    for i, prog in enumerate(sel):
        pdf = scope[scope["programa"] == prog]
        series = [M.compute(pdf[pdf[COL_CICLO] == y], key) for y in cs]
        fig = charts.small_multiple(prog, series, cs, key)
        cols[i % ncols].plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
