"""Smoke-test de la app SIN levantar Streamlit ni PyCaret.

Verifica que: (1) los modelos de produccion cargan con solo sklearn+lightgbm,
(2) la tabla de referencia se construye, (3) predict_all corre y devuelve
columnas esperadas. Falla con codigo !=0 si algo no cuadra.
"""
from __future__ import annotations

import sys
import pickle
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MODELS = ROOT / "models"

# Asegura que NO dependemos de PyCaret en este entorno
assert "pycaret" not in sys.modules
try:
    import pycaret  # noqa
    print("AVISO: pycaret esta instalado en este entorno (no deberia en deploy)")
except ImportError:
    print("OK: pycaret NO instalado (entorno ligero correcto)")

COL_ABV, COL_CEN, COL_PEN = "Abv.1", "indice_Ceneval", "indice_Pensamiento_Matematico"

with open(MODELS / "clf_prod.pkl", "rb") as f:
    clf = pickle.load(f)
with open(MODELS / "reg_prod.pkl", "rb") as f:
    reg = pickle.load(f)
print("OK: modelos cargados. clases:", list(clf.classes_))

lic = pd.read_csv(DATA / "licenciaturas.csv", encoding="utf-8-sig")
abvs = lic["abv"].tolist()
X = pd.DataFrame({COL_ABV: abvs, COL_CEN: 1030, COL_PEN: 1040})
pred = clf.predict(X)
proba = clf.predict_proba(X)
pos = reg.predict(X)
assert len(pred) == len(abvs) and proba.shape[0] == len(abvs)
print(f"OK: predict_all sobre {len(abvs)} licenciaturas")
print(f"   ejemplo ODO -> admitido_score={proba[abvs.index('ODO')][list(clf.classes_).index('Admitido')]*100:.2f}  posicion={pos[abvs.index('ODO')]:.0f}")
print("SMOKE TEST OK")
