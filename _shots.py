"""Script temporal: recorre el wizard y captura cada paso (solo para validación visual)."""
from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path("_screenshots")
OUT.mkdir(exist_ok=True)
BASE_FILE = str(Path("data/referencia/base 2026.xlsx").resolve())
URL = "http://localhost:8501"


def settle(page, ms: int = 2500) -> None:
    """Espera a que Streamlit termine de re-ejecutar (status 'running' desaparece)."""
    page.wait_for_timeout(ms)
    try:
        page.wait_for_selector("[data-testid='stStatusWidget']", state="detached", timeout=8000)
    except Exception:
        pass
    page.wait_for_timeout(800)


def shot(page, name: str) -> None:
    settle(page)
    page.screenshot(path=str(OUT / name), full_page=True)
    print("saved", name)


def click_text(page, text: str) -> None:
    page.get_by_role("button", name=text).first.click()


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=2)
    page.goto(URL, wait_until="networkidle")
    settle(page, 4000)

    # Paso 1 — Cargar Base 2026
    shot(page, "paso1_base.png")

    # subir Base 2026 para habilitar Siguiente
    page.set_input_files("input[type='file']", BASE_FILE)
    settle(page, 4000)
    shot(page, "paso1_base_cargada.png")

    # Paso 2 — Cargar Contable
    click_text(page, "Siguiente")
    shot(page, "paso2_contable.png")

    # Paso 3 — Configuración: setear fecha pivot a un mes presente en la Base (mayo)
    click_text(page, "Siguiente")
    settle(page, 2000)
    date_in = page.locator("[data-testid='stDateInput'] input").first
    date_in.click()
    date_in.press("Control+a")
    date_in.type("15/05/2026", delay=40)
    date_in.press("Enter")
    page.keyboard.press("Escape")
    settle(page, 3000)
    shot(page, "paso3_config.png")

    # Paso 4 — Resultado
    click_text(page, "Siguiente")
    shot(page, "paso4_resultado.png")

    # Ejecutar proyección para ver metric cards + gráfico
    try:
        page.get_by_role("button", name="Ejecutar").first.click()
        settle(page, 6000)
        shot(page, "paso4_resultado_ejecutado.png")
    except Exception as e:
        print("no se pudo ejecutar:", e)

    browser.close()
print("DONE")
