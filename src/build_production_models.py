"""Construye los modelos de PRODUCCION como pipelines de scikit-learn PUROS.

Por que: los .pkl de PyCaret contienen clases internas de PyCaret, asi que
cargarlos en Streamlit obligaria a instalar PyCaret (pesado). Aqui reconstruimos
pipelines equivalentes usando solo scikit-learn + lightgbm, de modo que la app
solo dependa de `requirements.txt` (ligero).

Equivalencia con la configuracion PyCaret original:
- Features: Abv.1 (categorica, one-hot) + indice_Ceneval + indice_Pensamiento.
- Imputacion: numerica (media) y categorica (mas frecuente).
- Clasificacion: LightGBM con manejo de desbalance via class_weight='balanced'
  (sustituto sin dependencias del fix_imbalance/SMOTE de PyCaret).
- Regresion: LightGBM por defecto.

Salida: models/clf_prod.pkl, models/reg_prod.pkl (+ metricas de validacion).

Uso:  .venv\\Scripts\\python.exe src\\build_production_models.py
"""
from __future__ import annotations

import json
import pickle

import numpy as np
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, roc_auc_score, recall_score, f1_score,
    mean_absolute_error, r2_score, mean_squared_error,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

import common as C

NUM = [C.COL_CENEVAL, C.COL_PENSAMIENTO]
CAT = [C.COL_ABV]
POS_LABEL = "Admitido"


def make_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="mean"), NUM),
            ("cat", Pipeline([
                ("imp", SimpleImputer(strategy="most_frequent")),
                ("ohe", OneHotEncoder(handle_unknown="ignore")),
            ]), CAT),
        ]
    )


def build_classifier() -> Pipeline:
    return Pipeline([
        ("prep", make_preprocessor()),
        ("model", LGBMClassifier(random_state=123, class_weight="balanced", n_jobs=-1)),
    ])


def build_regressor() -> Pipeline:
    return Pipeline([
        ("prep", make_preprocessor()),
        ("model", LGBMRegressor(random_state=123, n_jobs=-1)),
    ])


def main() -> None:
    C.MODELS_DIR.mkdir(exist_ok=True)
    df = C.load_dataset()
    report: dict = {}

    # ---- Clasificacion ----
    Xc = df[NUM + CAT]
    yc = df[C.COL_ESTATUS]
    # Validacion temporal honesta: train <=2025, test 2026
    tr = df[C.COL_CICLO] <= 2025
    te = df[C.COL_CICLO] == 2026
    clf = build_classifier()
    clf.fit(Xc[tr], yc[tr])
    pred = clf.predict(Xc[te])
    proba = clf.predict_proba(Xc[te])[:, list(clf.classes_).index(POS_LABEL)]
    y_te_bin = (yc[te] == POS_LABEL).astype(int)
    report["clasificacion_temporal_2026"] = {
        "accuracy": accuracy_score(yc[te], pred),
        "auc": roc_auc_score(y_te_bin, proba),
        "recall": recall_score(yc[te], pred, pos_label=POS_LABEL),
        "f1": f1_score(yc[te], pred, pos_label=POS_LABEL),
    }
    # Modelo final con TODOS los datos
    clf_final = build_classifier()
    clf_final.fit(Xc, yc)
    with open(C.MODELS_DIR / "clf_prod.pkl", "wb") as f:
        pickle.dump(clf_final, f)

    # ---- Regresion ----
    Xr = df[NUM + CAT]
    yr = df[C.COL_POSICION]
    reg = build_regressor()
    reg.fit(Xr[tr], yr[tr])
    rp = reg.predict(Xr[te])
    report["regresion_temporal_2026"] = {
        "mae": mean_absolute_error(yr[te], rp),
        "rmse": float(np.sqrt(mean_squared_error(yr[te], rp))),
        "r2": r2_score(yr[te], rp),
    }
    reg_final = build_regressor()
    reg_final.fit(Xr, yr)
    with open(C.MODELS_DIR / "reg_prod.pkl", "wb") as f:
        pickle.dump(reg_final, f)

    report["classes_"] = list(clf_final.classes_)
    (C.MODELS_DIR / "metrics_produccion.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=float), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False, default=float))
    print("\nGuardados: models/clf_prod.pkl, models/reg_prod.pkl")


if __name__ == "__main__":
    main()
