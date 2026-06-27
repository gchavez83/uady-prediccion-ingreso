"""Entrena el modelo de CLASIFICACION (target = ESTATUS: Admitido / No admitido).

Modernizacion del notebook uady_clasificacion.ipynb de Colab:
- lee el dataset local 2026 (no la URL de GitHub),
- nombres de columna reconciliados via common.py,
- sin magics de shell / ngrok,
- agrega validacion temporal (entrenar <=2025, validar 2026) ademas del
  split aleatorio, y guarda un reporte de metricas en JSON.

Uso:  .venv\\Scripts\\python.exe src\\train_clasificacion.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from pycaret.classification import (
    setup, compare_models, create_model, predict_model,
    finalize_model, pull, save_model, plot_model,
)

import common as C


def main() -> None:
    C.MODELS_DIR.mkdir(exist_ok=True)
    df = C.load_dataset()
    print(f"Dataset: {df.shape}  ciclos: {sorted(df[C.COL_CICLO].unique())}")
    print(df[C.COL_ESTATUS].value_counts())

    ignore = [C.COL_CICLO, C.COL_FOLIO, C.COL_POSICION]
    report: dict = {"target": C.COL_ESTATUS, "n_rows": int(len(df))}

    # --- Split aleatorio 75/25 (reproduce la linea base del notebook) -----
    datos = df.sample(frac=0.75, random_state=0).reset_index(drop=True)
    no_vistos = df.drop(df.sample(frac=0.75, random_state=0).index).reset_index(drop=True)

    setup(
        data=datos, target=C.COL_ESTATUS, session_id=123,
        ignore_features=ignore, fix_imbalance=True,
        categorical_features=[C.COL_ABV], max_encoding_ohe=49, verbose=False,
    )

    print("\n== compare_models (sort=Recall) ==")
    best = compare_models(sort="Recall")
    leaderboard = pull()
    print(leaderboard)
    report["leaderboard"] = leaderboard.reset_index().to_dict(orient="records")

    print("\n== create_model(lightgbm) ==")
    modelo = create_model("lightgbm")
    cv = pull()
    report["lightgbm_cv_mean"] = cv.loc["Mean"].to_dict()

    # Metricas en holdout aleatorio
    pred_holdout = predict_model(modelo, data=no_vistos)
    report["holdout_aleatorio"] = pull().iloc[0].to_dict()

    # --- Validacion temporal: entrenar <=2025, validar 2026 ---------------
    if 2026 in df[C.COL_CICLO].unique():
        print("\n== Validacion temporal: train<=2025 -> test 2026 ==")
        train_t = df[df[C.COL_CICLO] <= 2025].reset_index(drop=True)
        test_t = df[df[C.COL_CICLO] == 2026].reset_index(drop=True)
        setup(
            data=train_t, target=C.COL_ESTATUS, session_id=123,
            ignore_features=ignore, fix_imbalance=True,
            categorical_features=[C.COL_ABV], max_encoding_ohe=49, verbose=False,
        )
        modelo_t = create_model("lightgbm")
        predict_model(modelo_t, data=test_t)
        temporal = pull().iloc[0].to_dict()
        print(temporal)
        report["validacion_temporal_2026"] = temporal

    # --- Modelo FINAL: entrenado con TODOS los datos para produccion ------
    print("\n== Modelo final (todos los datos) ==")
    setup(
        data=df, target=C.COL_ESTATUS, session_id=123,
        ignore_features=ignore, fix_imbalance=True,
        categorical_features=[C.COL_ABV], max_encoding_ohe=49, verbose=False,
    )
    modelo_full = create_model("lightgbm")
    final = finalize_model(modelo_full)
    save_model(final, str(C.MODEL_CLASIFICACION))
    print(f"Guardado: {C.MODEL_CLASIFICACION}.pkl")

    (C.MODELS_DIR / "metrics_clasificacion.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    print("Reporte de metricas: models/metrics_clasificacion.json")


if __name__ == "__main__":
    main()
