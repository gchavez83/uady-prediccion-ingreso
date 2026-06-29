"""Las 7 métricas del dashboard, con su regla de agregación (roll-up).

Cada métrica es una función `f(df) -> float` que recibe el subconjunto de filas en
alcance (un ciclo, un campus/programa) y devuelve el escalar. Las no aditivas se
recalculan sobre las filas; el Punto de Corte agrega como PROMEDIO de los cortes
por programa (no el mínimo global).
"""
from __future__ import annotations

import math
import pandas as pd

from .data import COL_ABV, COL_CEN, COL_PM, COL_EST, ADM


def _adm(d: pd.DataFrame) -> pd.DataFrame:
    return d[d[COL_EST] == ADM]


def m_sustentantes(d):
    return float(len(d))


def m_admitidos(d):
    return float(len(_adm(d)))


def m_pct(d):
    return len(_adm(d)) / len(d) * 100 if len(d) else math.nan


def m_punto_corte(d):
    a = _adm(d)
    if a.empty:
        return math.nan
    return float(a.groupby(COL_ABV)[COL_CEN].min().mean())


def m_min_pm(d):
    a = _adm(d)
    return float(a[COL_PM].min()) if len(a) else math.nan


def m_avg_cen(d):
    a = _adm(d)
    return float(a[COL_CEN].mean()) if len(a) else math.nan


def m_avg_pm(d):
    a = _adm(d)
    return float(a[COL_PM].mean()) if len(a) else math.nan


# key -> definición. `good` indica el sentido semántico del delta:
#   up = subir es bueno (verde), neutral = umbral/promedio (sin color de bondad)
# `dfmt` formatea la variación absoluta vs año anterior.
METRICS: dict[str, dict] = {
    "sustentantes": {"label": "Sustentantes Total",        "fn": m_sustentantes, "fmt": "{:,.0f}", "dfmt": "{:+,.0f}",   "good": "up"},
    "admitidos":    {"label": "Sustentantes Admitidos",    "fn": m_admitidos,    "fmt": "{:,.0f}", "dfmt": "{:+,.0f}",   "good": "up"},
    "pct":          {"label": "% de Ingreso",              "fn": m_pct,          "fmt": "{:.1f}%", "dfmt": "{:+.1f} pp", "good": "up"},
    "punto_corte":  {"label": "Punto de Corte Ceneval",    "fn": m_punto_corte,  "fmt": "{:,.0f}", "dfmt": "{:+,.0f}",   "good": "neutral"},
    "min_pm":       {"label": "Mín. Pensamiento Mat.",     "fn": m_min_pm,       "fmt": "{:,.0f}", "dfmt": "{:+,.0f}",   "good": "neutral"},
    "avg_cen":      {"label": "Prom. Ceneval Admitido",    "fn": m_avg_cen,      "fmt": "{:,.1f}", "dfmt": "{:+,.1f}",   "good": "neutral"},
    "avg_pm":       {"label": "Prom. Pensamiento Adm.",    "fn": m_avg_pm,       "fmt": "{:,.1f}", "dfmt": "{:+,.1f}",   "good": "neutral"},
}

KEYS = list(METRICS)


def compute(d: pd.DataFrame, key: str) -> float:
    return METRICS[key]["fn"](d)


def fmt(key: str, value: float) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    return METRICS[key]["fmt"].format(value)


def series_by_cycle(df: pd.DataFrame, key: str, cycle_col: str, cycles: list[int]) -> list[float]:
    """Valor de la métrica por cada ciclo (para sparklines)."""
    return [compute(df[df[cycle_col] == y], key) for y in cycles]


def delta_info(key: str, cur: float, prev: float) -> dict:
    """Texto + sentido (good/bad/neutral/flat) y flecha de la variación vs año anterior."""
    if prev is None or cur is None or math.isnan(cur) or math.isnan(prev):
        return {"text": "s/ comparativo", "kind": "flat", "arrow": ""}
    d = cur - prev
    text = METRICS[key]["dfmt"].format(d)
    if abs(d) < 1e-9:
        return {"text": "sin cambio", "kind": "flat", "arrow": "■"}
    arrow = "▲" if d > 0 else "▼"
    if METRICS[key]["good"] == "up":
        kind = "good" if d > 0 else "bad"
    else:
        kind = "neutral"
    return {"text": text, "kind": kind, "arrow": arrow}
