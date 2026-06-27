"""App productiva UADY — predice ESTATUS (Admitido/No admitido) y POSICION.

Replica la app previa del usuario:
- Formulario: Indice Ceneval, Pensamiento Matematico, Especialidad (-> Campus).
- Resultado: scores de admision + posicion estimada.
- Simulacion "Otras Opciones": corre los modelos en el resto de licenciaturas y
  resalta en verde donde el aspirante SI seria admitido, con toggle de campus.

Carga modelos de scikit-learn puros (models/*_prod.pkl); NO requiere PyCaret.
"""
from __future__ import annotations

import pickle
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
MODELS = ROOT / "models"
ASSETS = ROOT / "assets"
LOGO = ASSETS / "logo.png"
ICON = ASSETS / "icon.png"

COL_ABV = "Abv.1"
COL_CENEVAL = "indice_Ceneval"
COL_PENSAMIENTO = "indice_Pensamiento_Matematico"
COL_ESTATUS = "ESTATUS"
COL_POSICION = "POSICION"
POS_LABEL = "Admitido"
PENS_MIN, PENS_MAX = 710, 1350

st.set_page_config(
    page_title="UADY — Predicción de Ingreso",
    page_icon=str(ICON) if ICON.exists() else "🎓",
    layout="wide",
)
# Logo de marca (barra superior + colapsable de la sidebar)
if LOGO.exists():
    st.logo(str(LOGO), icon_image=str(ICON) if ICON.exists() else None)

# --- CSS responsive (optimizado para movil) -------------------------------
st.markdown(
    """
    <style>
    /* Apilar columnas verticalmente en pantallas angostas (moviles/tablets) */
    @media (max-width: 820px) {
        [data-testid="stHorizontalBlock"] { flex-direction: column !important; gap: 0.5rem !important; }
        [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
        [data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            width: 100% !important; flex: 1 1 100% !important; min-width: 0 !important;
        }
        .block-container { padding-left: 1rem !important; padding-right: 1rem !important; padding-top: 2.5rem !important; }
        h1 { font-size: 1.6rem !important; }
    }
    /* El logo del encabezado nunca debe verse gigante */
    [data-testid="stImage"] img { max-height: 70px !important; width: auto !important; }
    /* Tablas con scroll horizontal en pantallas chicas */
    [data-testid="stDataFrame"] { overflow-x: auto; }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# Carga de datos y modelos (cacheada)
# --------------------------------------------------------------------------
@st.cache_resource
def load_models():
    with open(MODELS / "clf_prod.pkl", "rb") as f:
        clf = pickle.load(f)
    with open(MODELS / "reg_prod.pkl", "rb") as f:
        reg = pickle.load(f)
    return clf, reg


@st.cache_data
def load_reference() -> pd.DataFrame:
    """Tabla de referencia por licenciatura: nombre, campus y minimos historicos."""
    df = pd.read_csv(DATA / "Salida_UADY_ML_26.csv", encoding="utf-8-sig")
    df = df.rename(columns={c: COL_PENSAMIENTO for c in df.columns
                            if c.lower().startswith("indice_pensamiento")})
    df = df.rename(columns={c: COL_CENEVAL for c in df.columns
                            if c.lower().startswith("indice_ceneval")})
    if "POSICIÓN" in df.columns:
        df = df.rename(columns={"POSICIÓN": COL_POSICION})

    # Diccionario programa/abv/facultad
    lic = pd.read_csv(DATA / "licenciaturas.csv", encoding="utf-8-sig")
    lic["programa"] = lic["programa"].str.upper().str.strip()

    # Campus: usa data/campus.csv si existe; si no, cae a 'facultad'.
    campus_path = DATA / "campus.csv"
    if campus_path.exists():
        camp = pd.read_csv(campus_path, encoding="utf-8-sig")
        lic = lic.merge(camp, on="abv", how="left")
        lic["campus"] = lic["campus"].fillna(lic["facultad"])
        # Usa el nombre oficial del programa (distingue Merida/Tizimin) cuando exista
        lic["programa"] = lic["programa_oficial"].fillna(lic["programa"]).str.upper().str.strip()
    else:
        lic["campus"] = lic["facultad"]

    # Restringe a las ABVs presentes en los datos (las que el modelo conoce).
    abvs_data = pd.DataFrame({"abv": sorted(df[COL_ABV].dropna().unique())})
    ref = lic.merge(abvs_data, on="abv", how="inner")
    ref["etiqueta"] = ref["programa"] + " - " + ref["abv"]
    return ref.sort_values("programa").reset_index(drop=True)


def predict_all(clf, reg, ref: pd.DataFrame, ceneval: int, pensamiento: int) -> pd.DataFrame:
    """Corre ambos modelos para TODAS las licenciaturas con el mismo Ceneval/Pensamiento."""
    X = pd.DataFrame({
        COL_ABV: ref["abv"],
        COL_CENEVAL: ceneval,
        COL_PENSAMIENTO: pensamiento,
    })
    idx_adm = list(clf.classes_).index(POS_LABEL)
    out = ref.copy()
    out["pred"] = clf.predict(X)
    out["score_admitido"] = (clf.predict_proba(X)[:, idx_adm] * 100).round(2)
    out["posicion"] = reg.predict(X).round().astype(int)
    return out


# --------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------
clf, reg = load_models()
ref = load_reference()

head_logo, head_txt = st.columns([1, 4], vertical_alignment="center")
with head_logo:
    if LOGO.exists():
        st.image(str(LOGO), use_container_width=True)
with head_txt:
    st.title("Predicción de Ingreso — UADY")
    st.caption("Modelos entrenados con resultados públicos de admisión 2022–2026.")

col_form, col_res = st.columns([1, 1])

with col_form:
    st.subheader("Formulario de Cálculo")
    ceneval = st.number_input(
        "Índice Ceneval", min_value=600, max_value=1400, value=None, step=1,
        placeholder="ej. 1030",
    )
    pensamiento = st.number_input(
        f"Pensamiento Matemático  ·  *Introducir valor entre {PENS_MIN} y {PENS_MAX}*",
        min_value=PENS_MIN, max_value=PENS_MAX, value=None, step=10,
        placeholder="ej. 1040",
    )
    etiqueta = st.selectbox(
        "Especialidad", ref["etiqueta"].tolist(),
        index=None, placeholder="Selecciona una especialidad (ej. CIRUJANO DENTISTA - ODO)",
    )
    fila = ref[ref["etiqueta"] == etiqueta].iloc[0] if etiqueta else None
    st.text_input("Campus", value=fila["campus"] if fila is not None else "",
                  disabled=True, placeholder="Se autocompleta al elegir la especialidad")
    calcular = st.button("Calcular", type="primary", use_container_width=True)

# Estado de calculo — valida que el usuario haya llenado todo
if calcular:
    faltantes = []
    if ceneval is None: faltantes.append("Índice Ceneval")
    if pensamiento is None: faltantes.append("Pensamiento Matemático")
    if etiqueta is None: faltantes.append("Especialidad")
    if faltantes:
        st.warning("Completa: " + ", ".join(faltantes))
    else:
        st.session_state["calc"] = {"ceneval": ceneval, "pensamiento": pensamiento, "abv": fila["abv"]}

with col_res:
    st.subheader("Resultado")
    if "calc" in st.session_state:
        c = st.session_state["calc"]
        sim = predict_all(clf, reg, ref, c["ceneval"], c["pensamiento"])
        mine = sim[sim["abv"] == c["abv"]].iloc[0]
        admitido = mine["pred"] == POS_LABEL
        score_adm = mine["score_admitido"]
        box = st.success if admitido else st.error
        box(
            f"**Prediction Score Admitido:** {score_adm:.2f}\n\n"
            f"**Prediction Score No Admitido:** {100 - score_adm:.2f}\n\n"
            f"**Prediction Score Position:** {int(mine['posicion'])}\n\n"
            f"### {'✅ Admitido' if admitido else '❌ No Admitido'}"
        )
    else:
        st.info("Completa el formulario y presiona **Calcular**.")

# --------------------------------------------------------------------------
# Simulacion "Otras Opciones"
# --------------------------------------------------------------------------
if "calc" in st.session_state:
    c = st.session_state["calc"]
    sim = predict_all(clf, reg, ref, c["ceneval"], c["pensamiento"])
    mi_campus = ref[ref["abv"] == c["abv"]].iloc[0]["campus"]
    otras = sim[sim["abv"] != c["abv"]].copy()

    st.divider()
    modo = st.radio(
        f"Otras Opciones ({len(otras)})", ["Mismo campus seleccionado", "Otros campus"],
        horizontal=True, label_visibility="visible",
    )
    if modo == "Mismo campus seleccionado":
        tabla = otras[otras["campus"] == mi_campus]
    else:
        tabla = otras[otras["campus"] != mi_campus]

    tabla = tabla.sort_values("posicion")
    vista = tabla[["campus", "programa", "posicion", "pred"]].rename(
        columns={
            "campus": "Campus", "programa": "Especialidad",
            "posicion": "Posición", "pred": "Estatus",
        }
    )

    def resaltar(row):
        color = "background-color: #d4edda" if row["Estatus"] == POS_LABEL else ""
        return [color] * len(row)

    st.dataframe(
        vista.style.apply(resaltar, axis=1),
        use_container_width=True, hide_index=True,
    )
    st.caption("🟩 Verde = el modelo predice que **serías admitido** en ese programa con tus índices.")

    # Botón de exportación explícito (visible y funcional también en móvil)
    csv = vista.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ Descargar resultados (CSV)",
        data=csv,
        file_name=f"simulacion_uady_cen{c['ceneval']}_pm{c['pensamiento']}.csv",
        mime="text/csv",
        use_container_width=True,
    )

# Pie de marca
st.divider()
st.caption("Desarrollado por **IA Enterprise** · Sistema Synapse · Datos: ingreso.uady.mx")
