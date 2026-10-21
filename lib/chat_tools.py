"""Herramientas para el chat IA (nodo Synapse) sobre los datos planos UADY.

La precisión la dan estas funciones (cómputo exacto en pandas/DuckDB), no el LLM:
- `consultar_metrica`: una de las 7 métricas oficiales (reusa lib/metrics, validado).
- `consulta_sql`: SQL de solo lectura (DuckDB) sobre la tabla `aspirantes` para
  rankings, comparativos, listados y cualquier pregunta fuera de las 7 métricas.
- `predecir_ingreso`: corre los modelos productivos (models/clf_prod.pkl calibrado y
  models/reg_prod.pkl, sklearn puro) para un perfil Ceneval + Pensamiento + licenciatura;
  el veredicto (Admitido / No admitido / Caso límite) lo decide el código con la banda 40–60.

Claude solo traduce la pregunta en lenguaje natural a una llamada de herramienta;
el número lo calcula el código. No requiere modelo PBI ni túnel.
"""
from __future__ import annotations

import json
import math
import pickle
import unicodedata
from pathlib import Path

import duckdb
import pandas as pd

from . import data as D
from . import metrics as M

# Tabla de hechos enriquecida + copia con nombres limpios para SQL
_FACT = D.build_fact()
_SQLT = _FACT.rename(columns={
    D.COL_FOLIO: "folio", D.COL_EST: "estatus", D.COL_ABV: "abv",
    D.COL_CICLO: "ciclo", D.COL_POS: "posicion",
    D.COL_CEN: "ceneval", D.COL_PM: "pensamiento",
})[["folio", "estatus", "abv", "ciclo", "posicion", "ceneval",
    "pensamiento", "campus", "cluster", "facultad", "programa"]]

_CON = duckdb.connect()
_CON.register("aspirantes", _SQLT)


def consultar_metrica(metrica, ciclo=None, campus=None, abv=None, programa=None) -> dict:
    if metrica not in M.METRICS:
        return {"error": f"métrica desconocida: {metrica}. Válidas: {list(M.METRICS)}"}
    d = _FACT
    if ciclo is not None:
        d = d[d[D.COL_CICLO] == int(ciclo)]
    if campus:
        d = d[d["campus"].str.contains(campus, case=False, na=False)]
    if abv:
        d = d[d[D.COL_ABV] == abv]
    if programa:
        d = d[d["programa"].str.contains(programa, case=False, na=False)]
    if len(d) == 0:
        return {"valor": None, "nota": "Sin datos para ese filtro.", "n_sustentantes": 0}
    val = M.compute(d, metrica)
    return {
        "metrica": M.METRICS[metrica]["label"],
        "valor": None if (isinstance(val, float) and math.isnan(val)) else round(val, 2),
        "valor_formateado": M.fmt(metrica, val),
        "n_sustentantes": int(len(d)),
        "filtros": {k: v for k, v in
                    {"ciclo": ciclo, "campus": campus, "abv": abv, "programa": programa}.items()
                    if v is not None},
    }


def consulta_sql(sql: str) -> dict:
    s = sql.strip().rstrip(";")
    low = s.lower()
    if not (low.startswith("select") or low.startswith("with")):
        return {"error": "Solo se permiten consultas de lectura (SELECT / WITH)."}
    try:
        df = _CON.execute(s).fetch_df()
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}
    if len(df) > 100:
        return {"filas": df.head(100).to_dict("records"),
                "nota": f"Resultado truncado a 100 de {len(df)} filas."}
    return {"filas": df.to_dict("records")}

# ── Modelo predictivo (misma lógica que views/prediccion.py) ─────────────────
_MODELS = Path(__file__).resolve().parents[1] / "models"
POS_LABEL = "Admitido"
BAND_LO, BAND_HI = 40.0, 60.0            # banda de "caso límite" sobre el score CALIBRADO
V_ADM, V_NO, V_LIM = "Admitido", "No admitido", "Caso límite"
CEN_MIN, CEN_MAX = 600, 1400             # mismos límites que el formulario
PENS_MIN, PENS_MAX = 710, 1350

# Catálogo abv -> programa / campus / facultad (solo ABVs presentes en el dataset)
_REF = (_FACT[[D.COL_ABV, "programa", "campus", "facultad"]]
        .drop_duplicates(D.COL_ABV).rename(columns={D.COL_ABV: "abv"})
        .sort_values("programa").reset_index(drop=True))

# Umbrales históricos del último ciclo por programa (del dataset, no del modelo)
_ULT = int(_FACT[D.COL_CICLO].max())
_adm_ult = _FACT[(_FACT[D.COL_CICLO] == _ULT) & (_FACT[D.COL_EST] == POS_LABEL)]
_CORTES = (_adm_ult.groupby(D.COL_ABV)
           .agg(corte_ceneval=(D.COL_CEN, "min"), min_pensamiento=(D.COL_PM, "min"))
           .reset_index().rename(columns={D.COL_ABV: "abv"}))
_REF = _REF.merge(_CORTES, on="abv", how="left")

_CLF = _REG = None


def _models():
    global _CLF, _REG
    if _CLF is None:
        with open(_MODELS / "clf_prod.pkl", "rb") as f:
            _CLF = pickle.load(f)
        with open(_MODELS / "reg_prod.pkl", "rb") as f:
            _REG = pickle.load(f)
    return _CLF, _REG


def verdict(score_admitido: float) -> str:
    if score_admitido >= BAND_HI:
        return V_ADM
    if score_admitido <= BAND_LO:
        return V_NO
    return V_LIM


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t))
    return "".join(c for c in t if not unicodedata.combining(c)).upper().strip()


# Nombres coloquiales -> abv (el programa oficial se llama distinto)
_ALIAS = {"ODONTOLOGIA": "ODO", "DENTISTA": "ODO", "MEDICINA": "MCI", "MEDICO": "MCI",
          "VETERINARIA": "MVZ", "VETERINARIO": "MVZ", "MERCADOTECNIA": "MKT", "MARKETING": "MKT",
          "LEYES": "DER", "ABOGADO": "DER", "PSICOLOGIA": "PSI", "ENFERMERIA": "ENF"}


def resolver_abv(texto: str):
    """Resuelve 'ODO', 'odontología' o 'cirujano dentista' a un abv. -> (abv | None, candidatos)."""
    q = _norm(texto)
    if q in set(_REF["abv"]):
        return q, []
    for alias, abv in _ALIAS.items():
        if alias in q and abv in set(_REF["abv"]):
            return abv, []
    hits = _REF[_REF["programa"].map(_norm).str.contains(q, regex=False)]
    if len(hits) == 1:
        return hits.iloc[0]["abv"], []
    return None, hits[["abv", "programa", "campus"]].to_dict("records")


def predict_all(ceneval: int, pensamiento: int) -> pd.DataFrame:
    clf, reg = _models()
    X = pd.DataFrame({D.COL_ABV: _REF["abv"], D.COL_CEN: ceneval, D.COL_PM: pensamiento})
    idx_adm = list(clf.classes_).index(POS_LABEL)
    out = _REF.copy()
    out["score_admitido"] = (clf.predict_proba(X)[:, idx_adm] * 100).round(2)
    out["veredicto"] = out["score_admitido"].apply(verdict)
    out["posicion"] = reg.predict(X).round().clip(min=1).astype(int)
    return out


def predecir_ingreso(ceneval, pensamiento, licenciatura, otras_opciones=False, top_n=10) -> dict:
    try:
        ceneval, pensamiento = int(ceneval), int(pensamiento)
    except (TypeError, ValueError):
        return {"error": "ceneval y pensamiento deben ser enteros."}
    if not (CEN_MIN <= ceneval <= CEN_MAX):
        return {"error": f"Índice Ceneval fuera de rango ({CEN_MIN}–{CEN_MAX}): {ceneval}."}
    if not (PENS_MIN <= pensamiento <= PENS_MAX):
        return {"error": f"Índice de Pensamiento Matemático fuera de rango ({PENS_MIN}–{PENS_MAX}): {pensamiento}."}
    abv, cand = resolver_abv(licenciatura)
    if abv is None:
        if cand:
            return {"error": f"'{licenciatura}' es ambiguo; pide al usuario elegir una.",
                    "candidatos": cand}
        return {"error": f"No encontré la licenciatura '{licenciatura}'.",
                "licenciaturas_disponibles": _REF[["abv", "programa"]].to_dict("records")}

    sim = predict_all(ceneval, pensamiento)
    mine = sim[sim["abv"] == abv].iloc[0]
    res = {
        "entrada": {"ceneval": ceneval, "pensamiento": pensamiento, "abv": abv,
                    "programa": mine["programa"], "campus": mine["campus"]},
        "score_admitido_pct": float(mine["score_admitido"]),
        "score_no_admitido_pct": round(100 - float(mine["score_admitido"]), 2),
        "posicion_estimada": int(mine["posicion"]),
        "veredicto": mine["veredicto"],
        "umbrales_historicos_ultimo_ciclo": {
            "ciclo": _ULT,
            "corte_ceneval": None if pd.isna(mine["corte_ceneval"]) else int(mine["corte_ceneval"]),
            "min_pensamiento": None if pd.isna(mine["min_pensamiento"]) else int(mine["min_pensamiento"]),
        },
        "nota": (
            "Probabilidad calibrada con datos históricos 2022–2026. El modelo no conoce el cupo ni "
            "la competencia del próximo ciclo, así que no es una garantía."
        ),
    }
    if mine["veredicto"] == V_LIM:
        res["nota"] += (" El perfil cae en la zona de frontera (40–60%): perfiles iguales han sido "
                        "admitidos en unos ciclos y rechazados en otros.")
    if otras_opciones:
        otras = sim[sim["abv"] != abv].copy()
        otras["mismo_campus"] = otras["campus"] == mine["campus"]
        otras = otras.sort_values("score_admitido", ascending=False).head(int(top_n))
        res["otras_opciones"] = [
            {"abv": r["abv"], "programa": r["programa"], "campus": r["campus"],
             "mismo_campus": bool(r["mismo_campus"]),
             "score_admitido_pct": float(r["score_admitido"]), "veredicto": r["veredicto"],
             "posicion_estimada": int(r["posicion"]),
             "corte_ceneval": None if pd.isna(r["corte_ceneval"]) else int(r["corte_ceneval"])}
            for _, r in otras.iterrows()
        ]
        res["n_admitido_en_otras"] = int((sim[sim["abv"] != abv]["veredicto"] == V_ADM).sum())
    return res


def run_tool(name: str, tool_input: dict) -> str:
    if name == "consultar_metrica":
        res = consultar_metrica(**tool_input)
    elif name == "consulta_sql":
        res = consulta_sql(**tool_input)
    elif name == "predecir_ingreso":
        res = predecir_ingreso(**tool_input)
    else:
        res = {"error": f"Herramienta desconocida: {name}"}
    return json.dumps(res, ensure_ascii=False, default=str)


TOOLS = [
    {
        "name": "consultar_metrica",
        "description": (
            "Calcula UNA de las 7 métricas oficiales con filtros opcionales. Úsala para valores "
            "escalares exactos. Es la forma correcta de obtener el Punto de Corte (promedio de los "
            "mínimos de Ceneval admitido por programa) y el % de Ingreso (admitidos/sustentantes). "
            "Filtra por ciclo, campus, abv y/o programa."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "metrica": {"type": "string", "enum": list(M.METRICS),
                            "description": "clave de la métrica"},
                "ciclo": {"type": "integer", "description": "año 2022–2026"},
                "campus": {"type": "string", "description": "subcadena del nombre del campus"},
                "abv": {"type": "string", "description": "abreviatura exacta, p. ej. MKT"},
                "programa": {"type": "string", "description": "subcadena del programa, p. ej. Mercadotecnia"},
            },
            "required": ["metrica"],
        },
    },
    {
        "name": "consulta_sql",
        "description": (
            "Ejecuta SQL de solo lectura (DuckDB) sobre la tabla `aspirantes`. Úsala para rankings, "
            "comparativos vs años, listados, top-N, agregados por grupo o cualquier pregunta fuera de "
            "las 7 métricas. Solo SELECT/WITH."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"sql": {"type": "string", "description": "consulta SELECT sobre `aspirantes`"}},
            "required": ["sql"],
        },
    },
    {
        "name": "predecir_ingreso",
        "description": (
            "Corre los modelos predictivos (clasificación calibrada + regresión de posición) para un "
            "aspirante con cierto Índice Ceneval e Índice de Pensamiento Matemático en una licenciatura. "
            "Devuelve el score de admisión (%), la posición estimada, el veredicto ya decidido por el "
            "código (Admitido / No admitido / Caso límite) y los umbrales históricos del programa. "
            "Con otras_opciones=true agrega las licenciaturas donde el mismo perfil tendría mayor "
            "probabilidad. Úsala SIEMPRE que el usuario dé sus puntajes y pregunte si entra, "
            "qué probabilidad tiene o a qué otras carreras podría entrar."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ceneval": {"type": "integer", "description": "Índice Ceneval (600–1400)"},
                "pensamiento": {"type": "integer",
                                "description": "Índice de Pensamiento Matemático (710–1350)"},
                "licenciatura": {"type": "string",
                                 "description": "abreviatura (ODO, MKT, QFB...) o nombre/parte del "
                                                "programa tal como lo dijo el usuario (p. ej. 'odontología')"},
                "otras_opciones": {"type": "boolean",
                                   "description": "true para listar otras licenciaturas donde sí entraría"},
                "top_n": {"type": "integer", "description": "cuántas otras opciones devolver (default 10)"},
            },
            "required": ["ceneval", "pensamiento", "licenciatura"],
        },
    },
]


SCHEMA_DOC = """\
# DATOS DISPONIBLES — admisión a licenciatura UADY 2022–2026

Tabla `aspirantes` (una fila = un folio en un ciclo). Columnas:
- folio (texto) — FOLIO CENEVAL del aspirante
- estatus (texto) — 'Admitido' o 'No admitido'  (¡"ingresó/admitido" = estatus='Admitido'!)
- abv (texto) — abreviatura de la licenciatura (49 valores: MKT, MCI, ODO, QFB, DER, PSI, ENF, ...)
- ciclo (entero) — año 2022, 2023, 2024, 2025 o 2026
- posicion (entero) — ranking del aspirante dentro de su programa-ciclo (menor = mejor)
- ceneval (entero) — Índice Ceneval
- pensamiento (entero) — Índice de Pensamiento Matemático
- campus (texto) — campus al que pertenece el programa
- cluster (texto) — 'Cluster1'..'Cluster5' (modelo de clústers 2026)
- facultad (texto)
- programa (texto) — nombre completo (p. ej. 'MERCADOTECNIA Y NEGOCIOS INTERNACIONALES' = MKT,
  'MÉDICO CIRUJANO' = MCI, 'QUÍMICO FARMACÉUTICO BIÓLOGO' = QFB)

## Las 7 métricas (clave -> definición)
- sustentantes  = total de aspirantes (COUNT)
- admitidos     = aspirantes con estatus='Admitido'
- pct           = % de ingreso = admitidos / sustentantes
- punto_corte   = Punto de Corte Ceneval = MIN(ceneval) entre admitidos por programa; a nivel
                  agregado, el PROMEDIO de esos mínimos por programa (NO el mínimo global)
- min_pm        = mínimo de pensamiento matemático entre admitidos
- avg_cen       = promedio de Ceneval entre admitidos
- avg_pm        = promedio de Pensamiento Matemático entre admitidos

## Dificultad de ingreso
Más difícil = punto de corte más alto + menor % de ingreso. El Clúster 5 agrupa a las más difíciles
(p. ej. Médico Cirujano); el Clúster 1, las de acceso más holgado (~100% de ingreso).

## Catálogo de licenciaturas (abv = programa | campus)
""" + chr(10).join(f"- {r.abv} = {r.programa} | {r.campus}" for r in _REF.itertuples()) + """
Usa el abv del catálogo en `predecir_ingreso` cuando el usuario diga un nombre coloquial
(p. ej. "odontología" -> ODO Cirujano Dentista, "medicina" -> MCI Médico Cirujano).

## Modelo predictivo (herramienta predecir_ingreso)
- Entradas: Índice Ceneval, Índice de Pensamiento Matemático y licenciatura. El campus se deduce del programa.
- El veredicto viene decidido por el código con el score calibrado: ≥60% Admitido, ≤40% No admitido,
  40–60% "Caso límite". NUNCA cambies ese veredicto ni lo conviertas en un sí/no si es Caso límite.
- Preséntalo como probabilidad histórica, no como garantía: el modelo no conoce el cupo ni la
  competencia del próximo ciclo. Menciona el corte histórico del último ciclo como contexto.
- Si el usuario no da alguno de los tres datos, pídeselo; no inventes valores.
- "Otras opciones" = otras licenciaturas donde el mismo perfil tendría veredicto Admitido.

## Recetas SQL útiles
- Admitidos de MKT en 2026:
  SELECT COUNT(*) FROM aspirantes WHERE abv='MKT' AND ciclo=2026 AND estatus='Admitido'
- % de ingreso por programa en 2026:
  SELECT programa, 100.0*SUM(estatus='Admitido')/COUNT(*) AS pct_ingreso
  FROM aspirantes WHERE ciclo=2026 GROUP BY programa ORDER BY pct_ingreso
- Licenciatura más difícil (corte alto, % bajo) en 2026:
  SELECT programa, MIN(CASE WHEN estatus='Admitido' THEN ceneval END) AS punto_corte,
         100.0*SUM(estatus='Admitido')/COUNT(*) AS pct_ingreso
  FROM aspirantes WHERE ciclo=2026 GROUP BY programa
  ORDER BY pct_ingreso ASC, punto_corte DESC LIMIT 5
"""
