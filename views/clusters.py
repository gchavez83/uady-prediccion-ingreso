"""P4 · Clústers — dispersión de programas (2026) + tabla jerárquica de clústers."""
from __future__ import annotations
import streamlit as st

from lib.data import load_fact, COL_CICLO
from lib import charts, tables

df = load_fact()
d = df[df[COL_CICLO] == 2026]

st.markdown('<div class="syn-eyebrow">Dashboard · Modelo de Clústers 2026</div>', unsafe_allow_html=True)
st.title("Clústers de licenciaturas")

st.markdown(
    "Cada **burbuja** es un programa de licenciatura, ubicado por:\n"
    "- **Eje X — Punto de corte Ceneval**: más a la derecha, más exigente.\n"
    "- **Eje Y — % de ingreso**: más abajo, entra una menor proporción de aspirantes.\n"
    "- **Tamaño de la burbuja — total de admitidos**: a mayor tamaño, más lugares otorgados.\n"
    "- **Color — clúster** (modelo de 5 grupos del ciclo 2026).\n\n"
    "La **dificultad de ingreso aumenta con el número de clúster**: el **Clúster 5** reúne a los "
    "programas más difíciles (punto de corte más alto y menor % de ingreso, p. ej. *Médico Cirujano*) "
    "y desciende hasta el **Clúster 1**, los de acceso más holgado (corte bajo y ~100% de ingreso)."
)

st.plotly_chart(charts.cluster_scatter(d), use_container_width=True, config={"displayModeBar": False})

st.divider()
st.markdown("**Tabla de contenido de clústers** "
            "<span class='syn-eyebrow'>los clústers contienen en su jerarquía a los programas</span>",
            unsafe_allow_html=True)

labels = {k: v[0] for k, v in tables.CLUSTER_COLS.items()}
fc, ft = st.columns([3, 1])
with fc:
    sel = st.multiselect(
        "Columnas de la tabla", options=list(tables.CLUSTER_COLS),
        default=["corte", "pct", "sust", "adm"], format_func=lambda k: labels[k], key="p4_cols",
    )
with ft:
    expand = st.toggle("Ver programas", value=True, key="p4_expand",
                       help="Abre o cierra los programas dentro de cada clúster.")
st.markdown(tables.cluster_table_html(d, sel, expand=expand), unsafe_allow_html=True)
st.caption("Avg % Ingreso y promedios se **recalculan** en cada nivel (no se suman).")
