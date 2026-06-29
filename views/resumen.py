"""P1 · Resumen — tarjetas KPI + combo IBCS por licenciatura."""
from __future__ import annotations
import streamlit as st

from lib.data import load_fact, COL_CICLO, ALL
from lib import metrics as M
from lib import charts
from lib.filters import cycle_campus
from lib.theme import kpi_card_html, render_kpi_row

df = load_fact()
cs = sorted(int(c) for c in df[COL_CICLO].unique())

st.markdown('<div class="syn-eyebrow">Dashboard · Resumen</div>', unsafe_allow_html=True)
st.title("Resumen del ciclo")

ciclo, campus, scope = cycle_campus(df, key="p1")
ámbito = "todos los campus" if campus == ALL else campus
prev = ciclo - 1 if (ciclo - 1) in cs else None

d_cur = scope[scope[COL_CICLO] == ciclo]
d_prev = scope[scope[COL_CICLO] == prev] if prev else d_cur.iloc[0:0]

# Texto explicativo dinámico
sus = int(M.compute(d_cur, "sustentantes"))
adm = int(M.compute(d_cur, "admitidos"))
pct = M.compute(d_cur, "pct")
st.markdown(
    f"En el ciclo **{ciclo}**, **{sus:,}** sustentantes compitieron por un lugar en "
    f"{ámbito}; **{adm:,}** fueron admitidos (**{pct:.1f}%** de ingreso). "
    f"Las tarjetas comparan contra el año anterior y muestran la tendencia desde {cs[0]}."
)

# --- Tarjetas KPI ---
cards = []
for key in M.KEYS:
    val = M.fmt(key, M.compute(d_cur, key))
    delta = M.delta_info(key, M.compute(d_cur, key),
                         M.compute(d_prev, key) if prev else float("nan"))
    delta["vs"] = f"{prev}" if prev else "—"
    serie = M.series_by_cycle(scope, key, COL_CICLO, cs)
    cards.append(kpi_card_html(M.METRICS[key]["label"], val, delta, serie, hero=(key == "pct")))
render_kpi_row(cards)

st.divider()


# El selector de barras y la gráfica viven en un fragmento: al cambiar la métrica
# solo se redibuja esta sección, conservando la posición de scroll de la página.
@st.fragment
def combo_section(d_cur, d_prev, ciclo):
    left, right = st.columns([1.3, 1.7])
    with right:
        barras = st.segmented_control(
            "Barras", options=["sustentantes", "admitidos"],
            format_func=lambda k: {"sustentantes": "Sustentantes Totales",
                                   "admitidos": "Sustentantes Admitidos"}[k],
            default="admitidos", key="p1_bars",
        ) or "admitidos"
    with left:
        st.markdown(f"**Sustentantes y % de Ingreso por licenciatura** · {ciclo} "
                    f"<span class='syn-eyebrow'>ordenado por % de ingreso</span>", unsafe_allow_html=True)
    if len(d_cur):
        # Altura fija del contenedor: evita que la gráfica colapse y "salte" al re-dibujar.
        with st.container(height=485, border=False):
            st.plotly_chart(charts.combo(d_cur, d_prev, barras),
                            use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No hay datos para el filtro seleccionado.")
    st.caption("🟦 Barras = valor del ciclo · 🟧 línea = % de ingreso · ▲/▼ = variación vs año anterior.")


combo_section(d_cur, d_prev, ciclo)
