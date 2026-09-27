"""Pruebas de utils/texto.py: guion, WER, storyboard y duraciones."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils import texto  # pylint: disable=import-error,wrong-import-position

SCRIPT = """# SCRIPT — demo

## Line 1 — Hook (Frame 1)

**Time:** 0.0 – 5.0s

    Una afiliación tiene muchos pasos.

## Line 2 — Cierre (Frame 2)

    Todo en un solo lugar.
"""

STORY = """---
format: 1920x1080
length: 45s
---

## Frame 1 — Hook

- blueprint: compose
- src: compositions/frames/f01-hook.html
- duration: 5.2s

Scene 1 (0.0–2.0s): título. Ring on [608,260,2176,416].
Scene 2 (2.0–5.2s): logo.

## Frame 2 — Cierre

- src: compositions/frames/f02-cierre.html
"""


def test_parse_script_reads_indented_lines_only():
    """Solo el bloque indentado es texto hablado; las líneas ** se ignoran."""
    assert texto.parse_script(SCRIPT) == {1: "Una afiliación tiene muchos pasos.",
                                          2: "Todo en un solo lugar."}


def test_wer_ignores_accents_and_punctuation():
    """'Acmé' y 'Acme' cuentan igual; una palabra distinta suma error."""
    assert texto.wer("La Plataforma de Acmé.", "la plataforma de acme") == 0
    assert texto.wer("pagos con Wompi", "pagos con Wampi") == 1 / 3


def test_respell_only_changes_mapped_words():
    """El respelling cambia la marca y deja el resto intacto."""
    assert texto.respell("pagos con Wompi", {"Wompi": "Uómpi"}) == "pagos con Uómpi"


def test_english_ratio_flags_english_instruct():
    """Un instruct en inglés supera el umbral; uno en español no."""
    assert texto.english_ratio("Female narrator with a warm voice and clear accent") > 0.3
    assert texto.english_ratio("Mujer colombiana, hablante nativa, voz cálida") < 0.1


def test_split_frames_fields():
    """Campos '- clave: valor' se leen por frame; el texto libre queda en el bloque."""
    frames = texto.split_frames(STORY)
    assert [f["number"] for f in frames] == [1, 2]
    assert frames[0]["fields"]["blueprint"] == "compose"
    assert "Scene 2 (2.0–5.2s)" in frames[0]["block"]
    assert frames[1]["fields"] == {"src": "compositions/frames/f02-cierre.html"}


def test_frontmatter_and_seconds():
    """Frontmatter plano y duraciones en varios formatos."""
    assert texto.parse_frontmatter(STORY)["length"] == "45s"
    assert texto.seconds("2:40") == 160
    assert texto.seconds("2-3 min") == 150
    assert texto.seconds("150s") == 150


def test_asset_names_strip_paths_and_descriptions():
    """asset_candidates → nombres de archivo."""
    value = "assets/app-a.png — pantalla A; assets/brand-logo.png — logo"
    assert texto.asset_names(value) == ["app-a.png", "brand-logo.png"]


def test_wer_respell_acepta_ortografia_real_o_fonetica():
    """Whisper puede oír 'Books' o 'Buks': ninguna de las dos formas debe fallar."""
    spell = {"Books": "Buks"}
    assert texto.wer_respell("Explora Books", "explora books", spell) == 0
    assert texto.wer_respell("Explora Books", "explora buks", spell) == 0
    assert not texto.asset_names("ninguno")


def test_wer_otros_alfabetos():
    """Cirílico y chino cuentan de verdad (antes quedaban vacíos y todo daba WER 0)."""
    assert texto.wer("Привет мир", "привет мир") == 0
    assert texto.wer("Привет мир", "пока мир") == 0.5
    assert texto.wer("你好世界", "你好世界") == 0
    assert texto.wer("你好世界", "你好地界") == 0.25
    assert texto.wer("Über Straße", "uber strasse") == 0.5  # ß no se translitera
