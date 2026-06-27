"""Utilidades compartidas para entrenamiento y app de los modelos UADY.

Centraliza rutas, nombres de columnas y carga de datos para que los scripts de
entrenamiento (PyCaret) y la app de Streamlit usen exactamente las mismas
convenciones. Esto resuelve la discrepancia historica de nombres de columna
entre los notebooks de Colab y el dataset actual.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

# --- Rutas ---------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
DATASET_CSV = DATA_DIR / "Salida_UADY_ML_26.csv"
LICENCIATURAS_CSV = DATA_DIR / "licenciaturas.csv"

# Nombres canonicos de columna (los REALES del CSV 2026).
COL_FOLIO = "FOLIO CENEVAL"
COL_ESTATUS = "ESTATUS"
COL_ABV = "Abv.1"
COL_CICLO = "Ciclo"
COL_POSICION = "POSICION"
COL_CENEVAL = "indice_Ceneval"
COL_PENSAMIENTO = "indice_Pensamiento_Matematico"  # sin tilde tras normalizar

# Features que usa el usuario en la app productiva.
FEATURES = [COL_ABV, COL_CENEVAL, COL_PENSAMIENTO]

MODEL_CLASIFICACION = MODELS_DIR / "modelo_clasificacion"  # sin .pkl (PyCaret lo agrega)
MODEL_REGRESION = MODELS_DIR / "modelo_regresion"


def load_dataset(path: Path = DATASET_CSV) -> pd.DataFrame:
    """Carga el CSV 2026 y normaliza nombres de columna a los canonicos.

    El CSV viene en UTF-8 con BOM; la columna de pensamiento matematico trae
    tilde en el original. Renombramos a un nombre ASCII estable.
    """
    df = pd.read_csv(path, encoding="utf-8-sig")
    rename = {}
    for c in df.columns:
        cl = c.strip()
        if cl.lower().startswith("indice_pensamiento"):
            rename[c] = COL_PENSAMIENTO
        elif cl.lower().startswith("indice_ceneval"):
            rename[c] = COL_CENEVAL
        elif cl.upper() in ("POSICION", "POSICIÓN"):
            rename[c] = COL_POSICION
    df = df.rename(columns=rename)
    return df


def load_licenciaturas(path: Path = LICENCIATURAS_CSV) -> pd.DataFrame:
    """Diccionario programa <-> abreviatura (ABV) <-> facultad."""
    return pd.read_csv(path, encoding="utf-8-sig")
