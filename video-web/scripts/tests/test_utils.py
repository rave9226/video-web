"""Pruebas de la lógica nueva en utils y capture: contraste, lista negra y detección de vacío."""
import re
import sys
from pathlib import Path

from PIL import Image  # pylint: disable=import-error

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import capture  # pylint: disable=import-error,wrong-import-position
from utils import colores, imagenes, navegador  # pylint: disable=import-error,wrong-import-position


def test_muted_keeps_aa_contrast():
    """El gris derivado queda legible (≥ 4.5) y más claro que la tinta."""
    muted = colores.muted_between("#22254F", "#F1F1F1")
    assert colores.contrast(muted, "#F1F1F1") >= 4.5
    assert muted != "#22254F"


def test_deny_list_blocks_actions_not_reads():
    """Bloquea verbos de acción, pero no 'Ver payload' ni botones de lectura."""
    deny = re.compile(capture.DEFAULTS["deny"], re.IGNORECASE)
    for text in ("Pagar", "Enviar pendientes", "Aprobar documentos", "Cerrar sesión", "Send"):
        assert deny.search(text), text
    for text in ("Ver payload", "Consultar estado", "Nuevo lead", "Tema oscuro"):
        assert not deny.search(text), text


def test_white_logo_on_alpha_is_not_blank(tmp_path):
    """Un logo blanco sobre transparencia no cuenta como imagen vacía; un lienzo liso sí."""
    logo = Image.new("RGBA", (40, 40), (255, 255, 255, 0))
    logo.paste((255, 255, 255, 255), (10, 10, 30, 30))
    logo.save(tmp_path / "logo.png")
    Image.new("RGB", (40, 40), (241, 241, 241)).save(tmp_path / "flat.png")
    assert imagenes.gray_std(tmp_path / "logo.png") > 6
    assert imagenes.gray_std(tmp_path / "flat.png") < 6


def test_stale_clip_duration_is_flagged():
    """Un clip que termina justo antes del final (duración vieja) se marca; uno corto no."""
    import checks  # pylint: disable=import-outside-toplevel,import-error
    html = ('<div id="root" data-duration="12.19">'
            '<div id="f01-x-bg" data-start="0" data-duration="12.09"></div>'
            '<div id="f01-x-chip" data-start="1" data-duration="3"></div>'
            '<div id="f01-x-stage" data-start="0" data-duration="12.69"></div></div>')
    issues = checks._frame_timing(html, "f01-x", 12.19)  # pylint: disable=protected-access
    assert len(issues) == 1 and "f01-x-bg" in issues[0]


def test_readable_oscurece_acento_hasta_contraste_aa():
    """Un naranja claro como texto se oscurece hasta 4.6:1; uno ya legible no cambia."""
    orange = colores.readable("#FF7B1D", "#2E2E3A", "#F6F6F9")
    assert colores.contrast(orange, "#F6F6F9") >= 4.6
    assert colores.readable("#22254F", "#000000", "#FFFFFF") == "#22254F"


def test_guard_ruta_exacta_get_de_accion_y_permitidos(tmp_path: Path):
    """Login exacto sí; subrutas, GET de acción y escrituras ajenas no; prefijo solo con '*'."""
    guard = navegador.Guard(["/api/auth/login", "/public/*"], tmp_path / "log")
    assert guard.verdict("POST", "https://a.co/api/auth/login") == "PERMITIDO"
    assert guard.verdict("POST", "https://a.co/api/auth/change-password") == "BLOQUEADO"
    assert guard.verdict("POST", "https://a.co/public/x") == "PERMITIDO"
    assert guard.verdict("GET", "https://a.co/orders/7/approve?x=1") == "BLOQUEADO"
    assert guard.verdict("GET", "https://a.co/logout") == "BLOQUEADO"
    assert guard.verdict("GET", "https://a.co/approvals") is None
    assert guard.verdict("GET", "https://a.co/api/users") is None


def test_dotenv(tmp_path: Path):
    """KEY=valor con comillas, export y comentarios."""
    env = tmp_path / ".env"
    env.write_text("# c\nexport APP_USER='ana'\nAPP_PASS=\"a=b\"\n", encoding="utf-8")
    assert navegador.dotenv(env) == {"APP_USER": "ana", "APP_PASS": "a=b"}
    assert not navegador.dotenv(tmp_path / "no")
