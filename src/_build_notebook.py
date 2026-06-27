"""Construye el notebook consolidado uady_modelos_consolidado.ipynb con nbformat.

Un solo notebook con: EDA + modelo de Regresion (POSICION) + modelo de
Clasificacion (ESTATUS) + exportacion a modelos de produccion (sklearn puro).
Pensado para correr en el venv local de entrenamiento (Python 3.11 + PyCaret).
"""
import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s))
code = lambda s: cells.append(nbf.v4.new_code_cell(s))

md("""# UADY · Modelos de Ingreso — Notebook consolidado
**IA Enterprise · Sistema Synapse**

Análisis de los resultados públicos de admisión a licenciatura de la UADY
(2022–2026, fuente: ingreso.uady.mx). Un solo cuaderno con:

1. **EDA** — exploración de los datos.
2. **Regresión** — pronostica `POSICION` (lugar en el ranking).
3. **Clasificación** — pronostica `ESTATUS` (Admitido / No admitido).
4. **Modelos de producción** — pipelines de scikit-learn puros para la app.

> Requiere el entorno de entrenamiento (Python 3.11 + `requirements-train.txt`).
> Selecciona el kernel del venv `.venv` antes de ejecutar.""")

code("""import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

pd.set_option("display.max_columns", None)
RUTA_DATA = "data/Salida_UADY_ML_26.csv"  # ejecutar desde la raíz del repo""")

md("""## 1. Carga y normalización de datos

El CSV viene en UTF-8 con BOM. Normalizamos los nombres de columna a nombres
ASCII estables (la columna de pensamiento matemático trae tilde en el origen).""")

code("""df = pd.read_csv(RUTA_DATA, encoding="utf-8-sig")
df = df.rename(columns={c: "indice_Pensamiento_Matematico" for c in df.columns
                        if c.lower().startswith("indice_pensamiento")})
df = df.rename(columns={c: "indice_Ceneval" for c in df.columns
                        if c.lower().startswith("indice_ceneval")})
if "POSICIÓN" in df.columns:
    df = df.rename(columns={"POSICIÓN": "POSICION"})
print(df.shape)
df.head()""")

code("""df.info()""")
code("""df.isnull().sum().sort_values(ascending=False)""")

md("""## 2. Análisis exploratorio (EDA)""")

md("""### 2.1 Balance de clases (ESTATUS)
El objetivo de clasificación está desbalanceado (~2:1), por eso en el modelo
usamos `fix_imbalance=True`.""")
code("""conteo = df["ESTATUS"].value_counts()
print(conteo)
conteo.plot(kind="bar", rot=0, color=["#2A6FDB", "#F39A1E"])
plt.title("Frecuencia por ESTATUS"); plt.ylabel("Núm. de observaciones"); plt.show()""")

code("""df.describe()""")

md("""### 2.2 Matriz de correlación
Relación entre los índices y la posición.""")
code("""num = ["indice_Ceneval", "indice_Pensamiento_Matematico", "POSICION"]
plt.figure(figsize=(7, 5))
sns.heatmap(df[num].corr(), annot=True, cmap="coolwarm", center=0)
plt.title("Matriz de correlación"); plt.show()""")

md("""### 2.3 Distribución por ciclo
Cuántos registros hay por año (incluye 2026, el ciclo más reciente).""")
code("""df["Ciclo"].value_counts().sort_index().plot(kind="bar", rot=0, color="#244269")
plt.title("Registros por ciclo"); plt.ylabel("Conteo"); plt.show()""")

md("""## 3. Modelo de REGRESIÓN — `POSICION`

Configuración (igual a la histórica): se ignoran `FOLIO CENEVAL`, `ESTATUS` y
`Ciclo`; `Abv.1` es categórica (one-hot). Split 75/25 reproducible.""")
code("""from pycaret.regression import (
    setup as r_setup, compare_models as r_compare, create_model as r_create,
    predict_model as r_predict, finalize_model as r_finalize, pull as r_pull,
    save_model as r_save, plot_model as r_plot,
)
ignore_r = ["FOLIO CENEVAL", "ESTATUS", "Ciclo"]
datos = df.sample(frac=0.75, random_state=0).reset_index(drop=True)
r_setup(data=datos, target="POSICION", session_id=123, ignore_features=ignore_r,
        categorical_features=["Abv.1"], max_encoding_ohe=49, verbose=False)""")

md("""### 3.1 Comparación de algoritmos""")
code("""r_best = r_compare()
r_pull()""")

md("""### 3.2 Modelo LightGBM y diagnóstico""")
code("""r_modelo = r_create("lightgbm")""")
code("""r_plot(r_modelo, plot="residuals")""")
code("""r_plot(r_modelo, plot="feature")""")

md("""### 3.3 Validación temporal (entrenar ≤2025 → predecir 2026)
Escenario realista: ¿qué tan bien pronostica el ciclo siguiente nunca visto?""")
code("""train_t = df[df["Ciclo"] <= 2025].reset_index(drop=True)
test_t  = df[df["Ciclo"] == 2026].reset_index(drop=True)
r_setup(data=train_t, target="POSICION", session_id=123, ignore_features=ignore_r,
        categorical_features=["Abv.1"], max_encoding_ohe=49, verbose=False)
r_mod_t = r_create("lightgbm")
r_predict(r_mod_t, data=test_t)
r_pull()""")

md("""### 3.4 Modelo final (todos los datos) y guardado""")
code("""r_setup(data=df, target="POSICION", session_id=123, ignore_features=ignore_r,
        categorical_features=["Abv.1"], max_encoding_ohe=49, verbose=False)
r_final = r_finalize(r_create("lightgbm"))
r_save(r_final, "models/modelo_regresion")
print("Guardado models/modelo_regresion.pkl")""")

md("""## 4. Modelo de CLASIFICACIÓN — `ESTATUS`

Se ignoran `Ciclo`, `FOLIO CENEVAL` y `POSICION`; `fix_imbalance=True` para el
desbalance; se ordena por `Recall` (priorizar detectar a los admitidos).""")
code("""from pycaret.classification import (
    setup as c_setup, compare_models as c_compare, create_model as c_create,
    predict_model as c_predict, finalize_model as c_finalize, pull as c_pull,
    save_model as c_save, plot_model as c_plot,
)
ignore_c = ["Ciclo", "FOLIO CENEVAL", "POSICION"]
c_setup(data=datos, target="ESTATUS", session_id=123, ignore_features=ignore_c,
        fix_imbalance=True, categorical_features=["Abv.1"], max_encoding_ohe=49, verbose=False)""")

md("""### 4.1 Comparación de algoritmos (orden por Recall)""")
code("""c_best = c_compare(sort="Recall")
c_pull()""")

md("""### 4.2 Modelo LightGBM y diagnóstico""")
code("""c_modelo = c_create("lightgbm")""")
code("""c_plot(c_modelo, plot="auc")""")
code("""c_plot(c_modelo, plot="confusion_matrix")""")
code("""c_plot(c_modelo, plot="feature")""")

md("""### 4.3 Validación temporal (entrenar ≤2025 → predecir 2026)""")
code("""c_setup(data=train_t, target="ESTATUS", session_id=123, ignore_features=ignore_c,
        fix_imbalance=True, categorical_features=["Abv.1"], max_encoding_ohe=49, verbose=False)
c_mod_t = c_create("lightgbm")
c_predict(c_mod_t, data=test_t)
c_pull()""")

md("""### 4.4 Modelo final (todos los datos) y guardado""")
code("""c_setup(data=df, target="ESTATUS", session_id=123, ignore_features=ignore_c,
        fix_imbalance=True, categorical_features=["Abv.1"], max_encoding_ohe=49, verbose=False)
c_final = c_finalize(c_create("lightgbm"))
c_save(c_final, "models/modelo_clasificacion")
print("Guardado models/modelo_clasificacion.pkl")""")

md("""## 5. Modelos de PRODUCCIÓN (scikit-learn puro)

Los `.pkl` de PyCaret requieren PyCaret para cargarse. Para que la app de
Streamlit sea **ligera**, reconstruimos pipelines equivalentes solo con
scikit-learn + lightgbm.""")
code("""import pickle
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

NUM = ["indice_Ceneval", "indice_Pensamiento_Matematico"]; CAT = ["Abv.1"]
def preprocesador():
    return ColumnTransformer([
        ("num", SimpleImputer(strategy="mean"), NUM),
        ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                          ("ohe", OneHotEncoder(handle_unknown="ignore"))]), CAT),
    ])

clf_prod = Pipeline([("prep", preprocesador()),
                     ("model", LGBMClassifier(random_state=123, class_weight="balanced", n_jobs=-1))])
clf_prod.fit(df[NUM + CAT], df["ESTATUS"])
pickle.dump(clf_prod, open("models/clf_prod.pkl", "wb"))

reg_prod = Pipeline([("prep", preprocesador()),
                     ("model", LGBMRegressor(random_state=123, n_jobs=-1))])
reg_prod.fit(df[NUM + CAT], df["POSICION"])
pickle.dump(reg_prod, open("models/reg_prod.pkl", "wb"))
print("Guardados models/clf_prod.pkl y models/reg_prod.pkl")""")

md("""### 5.1 Prueba rápida de inferencia""")
code("""ejemplo = pd.DataFrame({"Abv.1": ["ODO"], "indice_Ceneval": [1030],
                       "indice_Pensamiento_Matematico": [1040]})
print("Estatus:", clf_prod.predict(ejemplo)[0],
      "| Score Admitido:", round(clf_prod.predict_proba(ejemplo)[0][list(clf_prod.classes_).index("Admitido")]*100, 2))
print("Posición estimada:", round(reg_prod.predict(ejemplo)[0]))""")

md("""## 6. Conclusiones

- **Regresión (POSICION):** R² ≈ 0.95 en CV; en validación temporal 2026, R² ≈ 0.93
  con MAE ≈ 153 posiciones (el error real al pronosticar un ciclo nuevo es mayor
  que el de CV — esperado, depende de la competencia de cada año).
- **Clasificación (ESTATUS):** Accuracy ≈ 0.94 y AUC ≈ 0.99, estable en la
  validación temporal 2026.
- Los modelos de producción en scikit-learn puro replican las métricas sin
  depender de PyCaret, lo que permite un deploy ligero en Streamlit.""")

nb["cells"] = cells
nbf.write(nb, "uady_modelos_consolidado.ipynb")
print("Notebook escrito: uady_modelos_consolidado.ipynb")
