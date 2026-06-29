"""Capa de datos del dashboard Synapse — fact plano enriquecido con dimensiones.

La "base de datos" del dashboard es un DataFrame en memoria: la tabla de hechos
(Salida_UADY_ML_26.csv) unida a las dimensiones planas del repo (campus, clúster,
facultad). No se consulta el modelo semántico de Power BI.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Nombres canónicos de columna
COL_FOLIO = "FOLIO CENEVAL"
COL_EST = "ESTATUS"
COL_ABV = "Abv.1"
COL_CICLO = "Ciclo"
COL_POS = "POSICION"
COL_CEN = "indice_Ceneval"
COL_PM = "indice_Pensamiento_Matematico"
ADM = "Admitido"

ALL = "Todos"  # opción "sin filtro" en los slicers


def build_fact() -> pd.DataFrame:
    """Carga el CSV de hechos y lo enriquece con campus/programa/facultad/clúster."""
    df = pd.read_csv(DATA / "Salida_UADY_ML_26.csv", encoding="utf-8-sig")
    ren = {}
    for c in df.columns:
        cl = c.strip().lower()
        if cl.startswith("indice_pensamiento"):
            ren[c] = COL_PM
        elif cl.startswith("indice_ceneval"):
            ren[c] = COL_CEN
        elif c.strip().upper() in ("POSICION", "POSICIÓN"):
            ren[c] = COL_POS
    df = df.rename(columns=ren)

    campus = pd.read_csv(DATA / "campus.csv", encoding="utf-8-sig")          # abv, programa_oficial, campus
    clusters = pd.read_csv(DATA / "clusters_2026.csv", encoding="utf-8-sig")  # abv, cluster
    lic = pd.read_csv(DATA / "licenciaturas.csv", encoding="utf-8-sig")       # programa, abv, facultad

    df = df.merge(campus, left_on=COL_ABV, right_on="abv", how="left")
    df = df.merge(clusters, on="abv", how="left")
    df = df.merge(lic[["abv", "facultad"]], on="abv", how="left")

    df["programa"] = df["programa_oficial"].fillna(df[COL_ABV])
    df = df.drop(columns=["abv", "programa_oficial"], errors="ignore")
    return df


# Versión cacheada para la app
load_fact = st.cache_data(build_fact)


def cycles(df: pd.DataFrame) -> list[int]:
    return sorted(int(c) for c in df[COL_CICLO].dropna().unique())


def campuses(df: pd.DataFrame) -> list[str]:
    return sorted(df["campus"].dropna().unique())


def programas(df: pd.DataFrame, campus: str | None = None) -> list[str]:
    d = df if not campus or campus == ALL else df[df["campus"] == campus]
    return sorted(d["programa"].dropna().unique())
