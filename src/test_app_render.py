"""Test de renderizado de la app con el framework AppTest de Streamlit.

Ejecuta app.py de principio a fin (sin navegador), simula el clic en Calcular
y el toggle de campus, y verifica que no haya excepciones ni en el render
inicial ni tras interactuar. Falla con codigo !=0 si algo truena.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # la pagina importa lib.* y data desde la raiz

from streamlit.testing.v1 import AppTest

# app.py es multipagina (st.navigation): su render inicial es la portada, sin
# formulario. Apuntamos a la pagina "Modelo Predictivo", que dibuja el form,
# el boton Calcular y el toggle de campus que este test ejercita.
APP = str(ROOT / "views" / "prediccion.py")


def main() -> None:
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception, f"Excepcion en render inicial: {at.exception}"
    print("OK: render inicial sin excepciones")
    print("   titulos:", [h.value for h in at.subheader])

    # Simula llenar el formulario (ahora los campos inician vacios) y Calcular
    at.number_input[0].set_value(1030)
    at.number_input[1].set_value(1040)
    at.selectbox[0].set_value("CIRUJANO DENTISTA - ODO")
    at.button[0].click().run()
    assert not at.exception, f"Excepcion tras Calcular: {at.exception}"
    print("OK: clic Calcular sin excepciones")

    # Verifica que hay tabla de simulacion y radio de campus
    assert len(at.radio) >= 1, "No se encontro el toggle de campus"
    print("   toggle campus:", at.radio[0].options)

    # Cambia al otro modo de campus
    at.radio[0].set_value("Otros campus").run()
    assert not at.exception, f"Excepcion tras cambiar campus: {at.exception}"
    print("OK: toggle 'Otros campus' sin excepciones")

    # La posicion es un ranking (1 = primer lugar): la regresion nunca debe
    # mostrar valores < 1, aun con aspirantes muy fuertes que extrapolan a
    # negativos. Validamos el clip(min=1) con un caso extremo.
    from views.prediccion import clf, reg, ref, predict_all
    sim = predict_all(clf, reg, ref, ceneval=1226, pensamiento=1300)
    assert (sim["posicion"] >= 1).all(), \
        f"Posiciones < 1 detectadas: {sorted(sim['posicion'].unique())[:5]}"
    print(f"OK: posicion minima = {int(sim['posicion'].min())} (>= 1)")
    print("TEST RENDER OK")


if __name__ == "__main__":
    main()
