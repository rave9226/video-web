"""Pruebas de brand.py: tokens que fija la marca, claves de 1.x y texto sobre fondos de marca."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import brand  # pylint: disable=import-error,wrong-import-position
from utils import colores  # pylint: disable=import-error,wrong-import-position

MANUAL = {"primary": "#1d4ed8", "ink": "#111827", "canvas": "#ffffff", "campo": "#1d4ed8",
          "accent-bg": "#eef2ff", "line": "#e5e7eb", "surface": "#f8fafc", "ok": "#15803d",
          "ok-bg": "#dcfce7", "bad": "#b91c1c", "bad-bg": "#fef2f2", "muted": "#6b7280"}


def test_tokens_del_manual_se_usan_tal_cual():
    """Los colores del manual de marca no se aproximan: un curso tuvo que parchar marca.css."""
    tok = brand.tokens(brand.resolve_brand({"brand": MANUAL}))
    for clave, valor in MANUAL.items():
        if clave not in ("primary", "ink", "canvas"):
            assert tok[clave] == valor.upper(), clave


def test_dark_de_1x_es_el_campo(capsys):
    """`dark` (1.x) ignorado en silencio dio una portada azul oscuro: ahora es `campo`."""
    viejo = {"primary": "#1d4ed8", "ink": "#111827", "canvas": "#ffffff", "dark": "#1d4ed8",
             "spark": "#1d4ed8"}
    tok = brand.tokens(brand.resolve_brand({"brand": viejo}))
    assert tok["campo"] == "#1D4ED8"
    out = capsys.readouterr().out
    assert "brand.dark es de video-web 1.x" in out and "brand.spark" in out


def test_texto_legible_sobre_campo_y_acento_claros():
    """Con un primario claro, el texto sobre campo y acento pasa a tinta (blanco no se lee)."""
    tok = brand.tokens(brand.resolve_brand({"brand": {
        "primary": "#FACC15", "ink": "#111827", "canvas": "#FFFFFF", "campo": "#FACC15"}}))
    assert tok["on-campo"] == tok["on-accent"] == "#111827"
    assert colores.contrast(tok["on-campo"], tok["campo"]) >= 4.5
    azul = brand.tokens(brand.resolve_brand({"brand": MANUAL}))
    assert azul["on-campo"] == "#FFFFFF"
