# UADY — Predicción de Ingreso a Licenciatura

Modelos de Machine Learning y app web sobre los resultados públicos de admisión
a licenciatura de la **UADY** (2022–2026), recopilados de
[ingreso.uady.mx](https://ingreso.uady.mx/licenciatura/resultados.php).

- **Clasificación** → predice `ESTATUS` (Admitido / No admitido).
- **Regresión** → predice `POSICION` (lugar en el ranking de admisión).

La app permite, además, **simular** el resultado del aspirante en el resto de
las licenciaturas con sus mismos índices.

## Estructura

```
data/        Salida_UADY_ML_26.csv  ·  licenciaturas.csv  ·  (campus.csv opcional)
src/         common.py  ·  train_*.py  ·  build_production_models.py  ·  smoke_test_app.py
models/      modelo_*.pkl (PyCaret)  ·  *_prod.pkl (sklearn, producción)  ·  metrics_*.json
app.py       Aplicación Streamlit
```

## Dos entornos (importante)

PyCaret necesita Python 3.9–3.11. La app de producción NO usa PyCaret (es ligera).

| | Entrenamiento | App / Producción |
|---|---|---|
| requirements | `requirements-train.txt` | `requirements.txt` |
| incluye | PyCaret 3.3.2 (pesado) | solo sklearn + lightgbm + streamlit |
| Python | 3.11 | 3.11 (`runtime.txt`) |

### Reentrenar los modelos
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-train.txt
.\.venv\Scripts\python.exe src\train_clasificacion.py
.\.venv\Scripts\python.exe src\train_regresion.py
.\.venv\Scripts\python.exe src\build_production_models.py   # genera los *_prod.pkl ligeros
```

### Correr la app en local
```powershell
py -3.11 -m venv .venv-app
.\.venv-app\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-app\Scripts\python.exe -m streamlit run app.py
```

## Deploy (GitHub → Streamlit Community Cloud)

1. Subir el repo a GitHub (incluyendo `models/*_prod.pkl`, `data/`, `app.py`,
   `requirements.txt`, `runtime.txt`).
2. En [share.streamlit.io](https://share.streamlit.io) conectar el repo y apuntar a `app.py`.
3. Streamlit Cloud usa `requirements.txt` y `runtime.txt` (Python 3.11) automáticamente.

## Desempeño de los modelos (validación temporal: entrenar ≤2025, predecir 2026)

- **Clasificación:** Accuracy ≈ 0.94, AUC ≈ 0.99.
- **Regresión:** R² ≈ 0.93, MAE ≈ 153 posiciones.
