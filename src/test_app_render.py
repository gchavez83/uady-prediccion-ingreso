"""Test de renderizado de la app con el framework AppTest de Streamlit.

Ejecuta app.py de principio a fin (sin navegador), simula el clic en Calcular
y el toggle de campus, y verifica que no haya excepciones ni en el render
inicial ni tras interactuar. Falla con codigo !=0 si algo truena.
"""
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def main() -> None:
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception, f"Excepcion en render inicial: {at.exception}"
    print("OK: render inicial sin excepciones")
    print("   titulos:", [h.value for h in at.subheader])

    # Simula Calcular
    at.number_input[0].set_value(1030)
    at.number_input[1].set_value(1040)
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
    print("TEST RENDER OK")


if __name__ == "__main__":
    main()
