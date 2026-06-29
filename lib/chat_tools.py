"""Herramientas para el chat IA (nodo Synapse) sobre los datos planos UADY.

La precisión la dan estas funciones (cómputo exacto en pandas/DuckDB), no el LLM:
- `consultar_metrica`: una de las 7 métricas oficiales (reusa lib/metrics, validado).
- `consulta_sql`: SQL de solo lectura (DuckDB) sobre la tabla `aspirantes` para
  rankings, comparativos, listados y cualquier pregunta fuera de las 7 métricas.

Claude solo traduce la pregunta en lenguaje natural a una llamada de herramienta;
el número lo calcula el código. No requiere modelo PBI ni túnel.
"""
from __future__ import annotations

import json
import math

import duckdb

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


def run_tool(name: str, tool_input: dict) -> str:
    if name == "consultar_metrica":
        res = consultar_metrica(**tool_input)
    elif name == "consulta_sql":
        res = consulta_sql(**tool_input)
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
