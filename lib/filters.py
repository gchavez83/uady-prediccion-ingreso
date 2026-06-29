"""Slicers compartidos del dashboard (Ciclo, Campus/Facultad, Programa)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .data import COL_CICLO, ALL, cycles, campuses, programas


def cycle_campus(df: pd.DataFrame, key: str, default_cycle: int | None = None):
    """Barra de filtros Ciclo + Campus. Devuelve (ciclo, campus, df_scope)."""
    cs = cycles(df)
    default_cycle = default_cycle or cs[-1]
    c1, c2 = st.columns([1.4, 1])
    with c1:
        ciclo = st.radio("Ciclo", cs, index=cs.index(default_cycle),
                         horizontal=True, key=f"{key}_ciclo")
    with c2:
        campus = st.selectbox("Campus", [ALL] + campuses(df), key=f"{key}_campus")
    scope = df if campus == ALL else df[df["campus"] == campus]
    return ciclo, campus, scope
