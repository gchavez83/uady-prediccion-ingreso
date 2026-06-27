"""Captura la app en 3 viewports (movil/tablet/escritorio) para validar responsive.

Requiere que la app este corriendo en http://localhost:8501 y playwright instalado.
Simula el clic en Calcular para capturar tambien la tabla de simulacion.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[1] / "scratch_shots"
OUT.mkdir(exist_ok=True)
URL = "http://localhost:8501"
VIEWPORTS = {"movil": (390, 844), "tablet": (768, 1024), "escritorio": (1280, 900)}


def shoot(page, name):
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(2500)
    # Clic en Calcular para mostrar resultado + simulacion
    try:
        page.get_by_role("button", name="Calcular").click(timeout=10000)
        page.wait_for_timeout(2500)
    except Exception as e:
        print(f"  (aviso {name}: no se pudo clickear Calcular: {e})")
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
    print(f"  guardada {name}.png")


with sync_playwright() as p:
    browser = p.chromium.launch()
    for name, (w, h) in VIEWPORTS.items():
        ctx = browser.new_context(viewport={"width": w, "height": h},
                                  device_scale_factor=2, is_mobile=(name == "movil"))
        page = ctx.new_page()
        print(f"Capturando {name} ({w}x{h})...")
        shoot(page, name)
        ctx.close()
    browser.close()
print("OK screenshots en scratch_shots/")
