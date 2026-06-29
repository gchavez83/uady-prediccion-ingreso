"""Modelo Predictivo — predice ESTATUS (Admitido/No admitido) y POSICION.

Carga modelos scikit-learn puros calibrados (models/*_prod.pkl); NO requiere PyCaret.
Migrada a vista del sistema Synapse; el tema y page_config los pone app.py.
"""
from __future__ import annotations

import pickle
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MODELS = ROOT / "models"

COL_ABV = "Abv.1"
COL_CENEVAL = "indice_Ceneval"
COL_PENSAMIENTO = "indice_Pensamiento_Matematico"
POS_LABEL = "Admitido"
PENS_MIN, PENS_MAX = 710, 1350

# Banda de "caso límite" sobre el score CALIBRADO (40-60% = frontera).
BAND_LO, BAND_HI = 40.0, 60.0
V_ADM, V_NO, V_LIM = "Admitido", "No admitido", "Caso límite"


def verdict(score_admitido: float) -> str:
    if score_admitido >= BAND_HI:
        return V_ADM
    if score_admitido <= BAND_LO:
        return V_NO
    return V_LIM


@st.cache_resource
def load_models():
    with open(MODELS / "clf_prod.pkl", "rb") as f:
        clf = pickle.load(f)
    with open(MODELS / "reg_prod.pkl", "rb") as f:
        reg = pickle.load(f)
    return clf, reg


@st.cache_data
def load_reference() -> pd.DataFrame:
    df = pd.read_csv(DATA / "Salida_UADY_ML_26.csv", encoding="utf-8-sig")
    df = df.rename(columns={c: COL_PENSAMIENTO for c in df.columns
                            if c.lower().startswith("indice_pensamiento")})
    df = df.rename(columns={c: COL_CENEVAL for c in df.columns
                            if c.lower().startswith("indice_ceneval")})
    lic = pd.read_csv(DATA / "licenciaturas.csv", encoding="utf-8-sig")
    lic["programa"] = lic["programa"].str.upper().str.strip()
    campus_path = DATA / "campus.csv"
    if campus_path.exists():
        camp = pd.read_csv(campus_path, encoding="utf-8-sig")
        lic = lic.merge(camp, on="abv", how="left")
        lic["campus"] = lic["campus"].fillna(lic["facultad"])
        lic["programa"] = lic["programa_oficial"].fillna(lic["programa"]).str.upper().str.strip()
    else:
        lic["campus"] = lic["facultad"]
    abvs_data = pd.DataFrame({"abv": sorted(df[COL_ABV].dropna().unique())})
    ref = lic.merge(abvs_data, on="abv", how="inner")
    ref["etiqueta"] = ref["programa"] + " - " + ref["abv"]
    return ref.sort_values("programa").reset_index(drop=True)


def predict_all(clf, reg, ref: pd.DataFrame, ceneval: int, pensamiento: int) -> pd.DataFrame:
    X = pd.DataFrame({COL_ABV: ref["abv"], COL_CENEVAL: ceneval, COL_PENSAMIENTO: pensamiento})
    idx_adm = list(clf.classes_).index(POS_LABEL)
    out = ref.copy()
    out["score_admitido"] = (clf.predict_proba(X)[:, idx_adm] * 100).round(2)
    out["pred"] = out["score_admitido"].apply(verdict)
    out["posicion"] = reg.predict(X).round().astype(int)
    return out


clf, reg = load_models()
ref = load_reference()

st.markdown('<div class="syn-eyebrow">Modelo · IA / ML</div>', unsafe_allow_html=True)
st.title("Predicción de Ingreso")
st.caption("Modelos entrenados con resultados públicos de admisión 2022–2026. "
           "Clasificador calibrado (sigmoid).")

col_form, col_res = st.columns([1, 1])
with col_form:
    st.subheader("Formulario de Cálculo")
    ceneval = st.number_input("Índice Ceneval", min_value=600, max_value=1400, value=None,
                              step=1, placeholder="ej. 1030")
    pensamiento = st.number_input(
        f"Pensamiento Matemático · *Introducir valor entre {PENS_MIN} y {PENS_MAX}*",
        min_value=PENS_MIN, max_value=PENS_MAX, value=None, step=10, placeholder="ej. 1040")
    etiqueta = st.selectbox("Especialidad", ref["etiqueta"].tolist(), index=None,
                            placeholder="Selecciona una especialidad (ej. CIRUJANO DENTISTA - ODO)")
    fila = ref[ref["etiqueta"] == etiqueta].iloc[0] if etiqueta else None
    st.text_input("Campus", value=fila["campus"] if fila is not None else "",
                  disabled=True, placeholder="Se autocompleta al elegir la especialidad")
    calcular = st.button("Calcular", type="primary", use_container_width=True)

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
        v = mine["pred"]
        score_adm = mine["score_admitido"]
        box, titulo = {
            V_ADM: (st.success, "✅ Admitido"),
            V_NO: (st.error, "❌ No Admitido"),
            V_LIM: (st.warning, "⚠️ Caso límite"),
        }[v]
        cuerpo = (
            f"**Prediction Score Admitido:** {score_adm:.2f}\n\n"
            f"**Prediction Score No Admitido:** {100 - score_adm:.2f}\n\n"
            f"**Prediction Score Position:** {int(mine['posicion'])}\n\n"
            f"### {titulo}"
        )
        if v == V_LIM:
            cuerpo += ("\n\nTu puntaje cae en la **zona de frontera**: la admisión depende del cupo y "
                       "la competencia de cada año. Un mismo perfil con estos índices ha sido admitido "
                       "en algunos ciclos y rechazado en otros.")
        box(cuerpo)
    else:
        st.info("Completa el formulario y presiona **Calcular**.")

# --- Simulación "Otras Opciones" ---
if "calc" in st.session_state:
    c = st.session_state["calc"]
    sim = predict_all(clf, reg, ref, c["ceneval"], c["pensamiento"])
    mi_campus = ref[ref["abv"] == c["abv"]].iloc[0]["campus"]
    otras = sim[sim["abv"] != c["abv"]].copy()

    st.divider()
    modo = st.radio(f"Otras Opciones ({len(otras)})",
                    ["Mismo campus seleccionado", "Otros campus"], horizontal=True)
    tabla = otras[otras["campus"] == mi_campus] if modo == "Mismo campus seleccionado" \
        else otras[otras["campus"] != mi_campus]
    tabla = tabla.sort_values("posicion")
    vista = tabla[["campus", "programa", "posicion", "pred"]].rename(
        columns={"campus": "Campus", "programa": "Especialidad",
                 "posicion": "Posición", "pred": "Estatus"})

    def resaltar(row):
        fondo = {V_ADM: "#d4edda", V_LIM: "#fff3cd"}.get(row["Estatus"], "")
        return [f"background-color: {fondo}" if fondo else ""] * len(row)

    st.dataframe(vista.style.apply(resaltar, axis=1), use_container_width=True, hide_index=True)
    st.caption("🟩 Verde = serías admitido · 🟨 amarillo = caso límite (depende del cupo) · sin color = no admitido.")
    csv = vista.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Descargar resultados (CSV)", data=csv,
                       file_name=f"simulacion_uady_cen{c['ceneval']}_pm{c['pensamiento']}.csv",
                       mime="text/csv", use_container_width=True)
