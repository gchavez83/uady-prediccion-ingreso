# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Idioma

El usuario trabaja en español. Responde en español salvo que se indique lo contrario.

## What this project is

Análisis de los resultados públicos de admisión a licenciatura de la **UADY** (Universidad Autónoma de Yucatán), recopilados desde 2022 del sitio oficial `https://ingreso.uady.mx/licenciatura/resultados.php`. El proyecto tiene dos componentes:

1. **Modelos de Machine Learning** (entrenados con PyCaret en Google Colab) — un modelo de **regresión** que pronostica `POSICION` y un modelo de **clasificación** que pronostica `ESTATUS` (Admitido / No admitido).
2. **Reporte de Power BI** (`UADY Estadística Ingreso.pbip`, formato PBIP/PBIR + TMDL) que visualiza los datos de ingreso.

### Objetivos de trabajo en curso
- Actualizar y reentrenar ambos modelos resolviendo los problemas de compatibilidad de versión de Python (los scripts asumen Python 3.10).
- Llevar los modelos a **producción en Streamlit**, con deploy desde **GitHub**.
- **Emular el reporte de Power BI como aplicación web** (segunda fase).

## Especificación de la app Streamlit (basada en la app previa del usuario)

- **Formulario "Cálculo":** inputs = `Índice Ceneval`, `Índice Pensamiento Matemático` (rango válido ~710–1350), `Especialidad` (selector con formato `NOMBRE - ABV`, p. ej. "CIRUJANO DENTISTA - ODO"). El `Campus` se autocompleta a partir de la especialidad mediante el diccionario.
- **Resultado:** `Prediction Score Admitido` / `No Admitido` (%), `Prediction Score Position` (regresión), y veredicto Admitido/No Admitido con color (verde/rojo).
- **Simulación "Otras Opciones":** correr ambos modelos para el mismo Ceneval+Pensamiento en TODAS las demás licenciaturas; tabla Campus | Especialidad | Ceneval (Mínimo) | Pensamiento Matemático (Mínimo) | Posición, ordenable, **resaltando en verde** donde el aspirante SÍ sería admitido. Toggle "Mismo campus seleccionado" / "Otros campus".
- **Diccionario de licenciaturas:** `data/licenciaturas.csv` (programa, abv, facultad) extraído de la tabla embebida `Cat_Licenciaturas_Abv` del modelo PBI (51 programas; el dataset usa 49 ABVs). El mapeo a Campus proviene del Excel externo `Licenciaturas UADY campus.xlsx` (SharePoint) — **pendiente de obtener**.
- "Ceneval (Mínimo)" / "Pensamiento Matemático (Mínimo)" = umbrales históricos mínimos de admisión por programa (derivar del dataset, no del modelo).

## Comandos

Dos entornos separados (PyCaret necesita Python 3.9–3.11; la app NO usa PyCaret):

```powershell
# Entrenamiento (pesado)
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-train.txt
.\.venv\Scripts\python.exe src\train_clasificacion.py     # -> models/modelo_clasificacion.pkl + metrics
.\.venv\Scripts\python.exe src\train_regresion.py         # -> models/modelo_regresion.pkl + metrics
.\.venv\Scripts\python.exe src\build_production_models.py  # -> models/{clf,reg}_prod.pkl (sklearn puro, ligeros)

# App (ligero) — entorno de produccion/deploy
py -3.11 -m venv .venv-app
.\.venv-app\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-app\Scripts\python.exe -m streamlit run app.py
.\.venv-app\Scripts\python.exe src\smoke_test_app.py      # valida carga de modelos sin PyCaret
.\.venv-app\Scripts\python.exe src\test_app_render.py     # AppTest: render + Calcular + toggle, sin navegador
```

Nota: PowerShell trata el stderr de los nativos (barras de progreso de PyCaret/LightGBM)
como `NativeCommandError`; es ruido, no fallo. Verificar el exit code y los archivos generados.
Definir `$env:PYTHONIOENCODING="utf-8"` antes de correr scripts con salida acentuada.

## Datos

- `Salida_UADY_ML_26.csv` / `Salida_UADY_ML_26.xlsx` — dataset principal, ~67,094 filas. Mismo contenido en ambos formatos.
- Columnas: `FOLIO CENEVAL`, `ESTATUS` (Admitido/No admitido), `Abv.1` (abreviatura de la licenciatura, categórica ~49 valores), `Ciclo` (año, 2022–2026), `POSICION` (ranking), `indice_Ceneval`, `indice_Pensamiento_Matemático`.
- El CSV está en **UTF-8 con BOM** y usa coma como separador.

⚠️ **Discrepancia importante de nombres de columnas** entre los scripts y los datos actuales — debe reconciliarse al reentrenar:
- Los scripts referencian `POSICIÓN` (con tilde), `Avg__indice_Ceneval`, `Avg__indice_Pensamiento_Matemático`.
- El CSV/XLSX actual tiene `POSICION` (sin tilde), `indice_Ceneval`, `indice_Pensamiento_Matemático`.
- El script de clasificación carga `Salida_UADY_ML_25.xlsx` (versión vieja) desde una URL de GitHub; el de regresión carga `Salida_UADY_ML_26.xlsx`. Al modernizar, ambos deben leer el dataset local `Salida_UADY_ML_26`.

## Modelos de ML

`uady_regression.py` y `uady_clasificacion.py` son **exportaciones de notebooks de Colab** (contienen magics `!pip`, `!wget`, `!python` y `ngrok`); **no se ejecutan localmente tal cual**. Sírvete de ellos como referencia de la lógica de entrenamiento, no como scripts ejecutables.

Configuración de PyCaret usada (a preservar al reentrenar):
- **Regresión** — `target = "POSICIÓN"`, `ignore_features = ['FOLIO CENEVAL', 'ESTATUS', 'Ciclo']`, `categorical_features = ['Abv.1']`, `max_encoding_ohe = 49`. Split 75/25 (`random_state=0`). Mejores modelos probados: lightgbm, catboost, xgboost. Se guardaba como `modelo_regresion_lightgbm_Uady_25`.
- **Clasificación** — `target = "ESTATUS"`, `ignore_features = ['Ciclo', 'FOLIO CENEVAL', 'POSICIÓN']`, `fix_imbalance = True`, `categorical_features = ['Abv.1']`, `max_encoding_ohe = 49`, `compare_models(sort="Recall")`. Se guardaba como `modelo_lightgbm_Uady_25`.

Al reentrenar para producción: fijar versiones en un `requirements.txt`, usar rutas locales al dataset, eliminar los magics de shell, y exportar el pipeline con `save_model` para cargarlo desde la app de Streamlit con `load_model`.

### Línea base (de los notebooks de Colab, entrenados con datos 2022–2025)
Conservar o superar estos números al reentrenar con datos 2022–2026:
- **Regresión (POSICIÓN)** — mejor modelo `lightgbm`: R²=0.9546, MAE=97.5, RMSE=181.9, MAPE=0.40. (catboost y xgboost prácticamente empatados: R²≈0.954.)
- **Clasificación (ESTATUS)** — mejor modelo `lightgbm` (orden por Recall): Accuracy=0.9435, AUC=0.9904, Recall=0.9435, Precision=0.9435, F1=0.9435.
- `tune_model` NO mejoró al modelo base en ninguno de los dos casos (PyCaret devolvió el original).
- Versiones del entorno Colab: Python 3.10.8, pycaret 3.3.2, scikit-learn 1.4.2, pandas 2.1.4, numpy 1.26.4, lightgbm 4.6.0.
- **Desbalance de clases** (ESTATUS): No admitido 35,528 vs Admitido 17,347 (~67/33) → por eso `fix_imbalance=True`.

### Calibración del clasificador de producción (IMPORTANTE — preservar al reentrenar)
El clasificador productivo (`models/clf_prod.pkl`, generado por `src/build_production_models.py`) **va calibrado** con `CalibratedClassifierCV(method="sigmoid", cv=5)` envolviendo el `LGBMClassifier(class_weight="balanced")`. **No quitar la calibración al reentrenar.**
- **Por qué:** `class_weight="balanced"` (sustituto de `fix_imbalance`) resuelve el desbalance pero **infla las probabilidades en la franja fronteriza** (scores crudos de 40–70% correspondían a una admisión real de solo ~25–35%). La calibración corrige ese sesgo para que el score sea una probabilidad confiable.
- **Efecto medido** (validación temporal honesta: entrena ≤2025, prueba 2026): Brier 0.0411→0.0369, accuracy@0.5 0.9394→0.9504, F1 0.9224→0.9342, AUC sin cambio (~0.991). El recall baja un poco (0.952→0.930) a propósito: deja de inflar admisiones dudosas.
- **Caso testigo:** QFB con Ceneval 1048 (admitido 2 de 5 ciclos; en 2026 NO) pasaba de ~51–57% (falso Admitido) a **~33%** (No admitido, correcto). Es error irreducible: la admisión depende del cupo/competencia del año, señal que las features (`Abv.1`+Ceneval+Pensamiento) no contienen porque `Ciclo` se ignora.
- **Banda de "caso límite" en `app.py`:** con el score ya calibrado, `BAND_LO=40`, `BAND_HI=60` → ≥60% Admitido (verde), ≤40% No admitido (rojo), 40–60% "⚠️ Caso límite" (ámbar) en el resultado y en la tabla "Otras Opciones". No forzar un veredicto binario en la zona fronteriza.

## Power BI (`UADY Estadística Ingreso.pbip`)

Proyecto PBIP con dos artefactos:
- `UADY Estadística Ingreso.Report/` — reporte en formato **PBIR** (carpetas `definition/pages/<id>/visuals/<id>/visual.json`), 21 páginas.
- `UADY Estadística Ingreso.SemanticModel/` — modelo semántico en **TMDL** (`definition/tables/*.tmdl`, `relationships.tmdl`, `model.tmdl`).

La tabla de hechos principal es `Contenido`; los datos se ingieren desde **PDFs en SharePoint** vía Power Query (M). `Cat_Licenciaturas_Abv` mapea `Abv.1`/`ABV` a nombre de programa y facultad.

Para trabajar el modelo o el reporte, usa las **skills de pbi-cli** (power-bi-dax, power-bi-modeling, power-bi-report, power-bi-visuals, etc.) descritas en el CLAUDE.md global del usuario. Las operaciones sobre el modelo semántico requieren `pbi connect`; la capa de reporte no.

## Entorno

- Windows 11, shell primario **PowerShell** (también disponible Bash POSIX). No hay sistema de build, tests ni `requirements.txt` todavía — se crearán como parte del trabajo de productivización.
- `.gitignore` solo excluye archivos de caché locales de pbi (`.pbi/localSettings.json`, `.pbi/cache.abf`).
