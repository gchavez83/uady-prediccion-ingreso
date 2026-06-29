"""P5 · Consulta por Folio — ubica a un aspirante (2026) frente a su programa."""
from __future__ import annotations
import streamlit as st

from lib.data import load_fact, COL_CICLO, COL_FOLIO, COL_ABV, COL_CEN, COL_PM, COL_POS, COL_EST, ADM
from lib import charts
from lib.theme import stat_card, render_grid, comparison_panel, render_panels

df = load_fact()
d = df[df[COL_CICLO] == 2026].copy()
d["_folio"] = d[COL_FOLIO].astype(str)

st.markdown('<div class="syn-eyebrow">Dashboard · Consulta por Folio · 2026</div>', unsafe_allow_html=True)
st.title("Resultado del aspirante")

folio = st.text_input(
    "Folio Ceneval", value="",
    placeholder="Escribe un folio del ciclo 2026 (ej. 624258078)",
    help="Captura el folio Ceneval del aspirante para ver su resultado.",
).strip()

if not folio:
    st.info("Escribe un **folio Ceneval** del ciclo 2026 para consultar su resultado.")
    st.stop()

match = d[d["_folio"] == folio]
if match.empty:
    st.warning(f"No se encontró el folio **{folio}** en el ciclo 2026. Verifica el número.")
    st.stop()

row = match.iloc[0]
abv, prog = row[COL_ABV], row["programa"]
cen, pm, pos = float(row[COL_CEN]), float(row[COL_PM]), int(row[COL_POS])
admit = row[COL_EST] == ADM

pdf = d[d[COL_ABV] == abv]
adm = pdf[pdf[COL_EST] == ADM]
corte_cen = float(adm[COL_CEN].min())
min_pm = float(adm[COL_PM].min())
pos_corte = int(adm[COL_POS].max())

# --- Tarjetas superiores ---
tono_est = "success" if admit else "danger"
render_grid([
    stat_card("Nombre Licenciatura", prog, "azure", vsize="1.05rem"),
    stat_card("Estatus", "Admitido" if admit else "No admitido", tono_est, vsize="1.5rem"),
    stat_card("Posición", f"{pos:,}", "ink"),
    stat_card("Índice Ceneval", f"{cen:,.0f}", "ink"),
    stat_card("Índice Pensamiento Mat.", f"{pm:,.0f}", "ink"),
], cols=5)

st.divider()
izq, der = st.columns([1.6, 1])

with izq:
    st.markdown("**Resultado del folio en el programa** "
                "<span class='syn-eyebrow'>4 cuadrantes según punto de corte y P. Mat. mínimo</span>",
                unsafe_allow_html=True)
    st.plotly_chart(charts.quadrant(pdf, cen, pm, corte_cen, min_pm),
                    use_container_width=True, config={"displayModeBar": False})

with der:
    falt_cen = corte_cen - cen           # >0: le faltan puntos
    lugares = pos - pos_corte            # >0: fuera del corte
    exced_pm = pm - min_pm               # >0: por encima del mínimo
    pos_max = int(pdf[COL_POS].max())

    panel_cen = comparison_panel(
        "Índice Ceneval", cen, corte_cen, "Tu índice", "Punto de corte",
        f"▼ Te faltan {falt_cen:,.0f} pts" if falt_cen > 0 else f"▲ Superas el corte por {-falt_cen:,.0f}",
        "bad" if falt_cen > 0 else "good", 700, 1350)
    panel_pm = comparison_panel(
        "Pensamiento Matemático", pm, min_pm, "Tu índice", "Mínimo admitido",
        f"▲ Excedes por {exced_pm:,.0f} pts" if exced_pm >= 0 else f"▼ Te faltan {-exced_pm:,.0f} pts",
        "good" if exced_pm >= 0 else "bad", 700, 1350)
    panel_pos = comparison_panel(
        "Posición / Ranking", pos, pos_corte, "Tu posición", "Posición de corte",
        f"▼ Te faltan {lugares:,} lugares" if lugares > 0 else "▲ Dentro del corte",
        "bad" if lugares > 0 else "good", 1, pos_max)
    render_panels([panel_cen, panel_pm, panel_pos])

veredicto = ("**admitido**" if admit else "**no admitido**")
st.caption(
    f"El folio {folio} ({prog}) quedó en la **posición {pos:,}** y fue {veredicto}. "
    f"La 🟠 marca tu posición; las líneas punteadas son el punto de corte Ceneval ({corte_cen:.0f}) "
    f"y el Pensamiento Matemático mínimo admitido ({min_pm:.0f}) del programa."
)
