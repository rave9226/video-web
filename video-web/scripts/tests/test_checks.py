"""Pruebas de checks.py: guion, voz, marca, escenas givemotion y estado."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import checks  # pylint: disable=import-error,wrong-import-position


def test_guion_only_flags_long_lines(tmp_path):
    """Línea larga avisa; la duración total ya no es un error."""
    long_line = " ".join(["palabra"] * 50)
    body = "".join(f"## Line {i} — x (Frame {i})\n\n    {long_line}\n\n" for i in (1, 2, 3))
    (tmp_path / "SCRIPT.md").write_text(body, encoding="utf-8")
    (tmp_path / "BRIEF.md").write_text("---\nformato: lanzamiento\n---\n", encoding="utf-8")
    issues = checks.check_guion(tmp_path)
    assert len(issues) == 3 and "(> 45)" in issues[0]


def test_guion_exige_formato(tmp_path):
    """Sin `formato` en el BRIEF no se sabe qué arco debe tener el guion."""
    (tmp_path / "SCRIPT.md").write_text(
        "## Line 1 — x (Frame 1)\n\n    Hola mundo.\n", encoding="utf-8")
    assert any("no declara `formato`" in i for i in checks.check_guion(tmp_path))


def test_capacitacion_necesita_cuerpo(tmp_path):
    """Un guion de 60 s no alcanza para capacitar: avisa por duración y por líneas."""
    (tmp_path / "SCRIPT.md").write_text(
        "## Line 1 — x (Frame 1)\n\n    " + " ".join(["palabra"] * 40) + "\n", encoding="utf-8")
    (tmp_path / "BRIEF.md").write_text("---\nformato: capacitacion\n---\n", encoding="utf-8")
    issues = " ".join(checks.check_guion(tmp_path))
    assert "es poco" in issues and "líneas es poco" in issues


def test_estado_suggests_first_missing(tmp_path, capsys):
    """El estado sale de los archivos y sugiere lo primero que falta."""
    (tmp_path / "BRIEF.md").write_text("---\n---\n", encoding="utf-8")
    checks.estado(tmp_path)
    out = capsys.readouterr().out
    assert "✓ brief" in out and "· escenas" in out
    assert "Sugerencia: `./vl captura`" in out


def test_modo_explicativo_omite_captura(tmp_path: Path, capsys):
    """Con `tipo: explicativo` en BRIEF.md no se exige captura ni se sugiere en estado."""
    assert checks.check_captura(tmp_path)  # sin BRIEF: pide captura
    (tmp_path / "BRIEF.md").write_text("---\ntipo: explicativo\n---\n", encoding="utf-8")
    assert checks.check_captura(tmp_path) == []
    checks.estado(tmp_path)
    assert "capturas" not in capsys.readouterr().out


MARCA = """@font-face { font-family: 'Geist'; src: url(assets/fonts/Geist-Bold.woff2); }
:root {
  --bg: #FFFFFF; --ink: #111827; --muted: #6B7280; --accent: #1D4ED8;
  --accent-text: #1D4ED8; --accent-bg: #EEF2FF; --ok: #15803D; --ok-bg: #DCFCE7;
  --bad: #B91C1C; --bad-bg: #FEF2F2; --campo: #1D4ED8;
}"""


def test_marca_css_valida(tmp_path):
    """La marca del curso pasa: contraste AA de cada texto sobre su fondo y fuente local."""
    (tmp_path / "assets/fonts").mkdir(parents=True)
    (tmp_path / "assets/fonts/Geist-Bold.woff2").write_bytes(b"x")
    (tmp_path / "marca.css").write_text(MARCA, encoding="utf-8")
    assert checks.check_marca(tmp_path) == []


def test_marca_detecta_contraste_y_color_ajeno(tmp_path):
    """Un acento claro sobre su tinte falla AA; un campo de otro tono es un color copiado."""
    css = MARCA.replace("--accent-text: #1D4ED8", "--accent-text: #93C5FD").replace(
        "--campo: #1D4ED8", "--campo: #C2410C")
    (tmp_path / "marca.css").write_text(css, encoding="utf-8")
    issues = " ".join(checks.check_marca(tmp_path))
    assert "--accent-text sobre --accent-bg" in issues
    assert "campo #C2410C" in issues and "fuente declarada sin archivo" in issues


def _voz(tmp_path: Path, **extra) -> None:
    voz = {"frame": 1, "path": "assets/voice/01.wav", "duration_s": 10.0, "wer": 0.0,
           "p_lang": 1.0, **extra}
    (tmp_path / "audio_meta.json").write_text(json.dumps({"voices": [voz]}), encoding="utf-8")


def test_voz_con_habla_oculta_avisa(tmp_path):
    """WER 0 no basta: el detector de voice.py deja `revisar` y el check lo muestra."""
    (tmp_path / "SCRIPT.md").write_text("## Line 1 — x (Frame 1)\n\n    Hola.\n",
                                        encoding="utf-8")
    _voz(tmp_path, revisar=["hueco de 3.7 s con habla sin transcribir"])
    (tmp_path / "assets/voice").mkdir(parents=True)
    (tmp_path / "assets/voice/01.wav").write_bytes(b"x")
    issues = checks.check_voz(tmp_path)
    assert len(issues) == 1 and "habla sin transcribir" in issues[0]


def test_escenas_givemotion(tmp_path):
    """Escena sin su voz, corta, con hex o sin incluir; avisos de givemotion sí, notas no."""
    _voz(tmp_path)
    (tmp_path / "scenes").mkdir()
    (tmp_path / "scenes/s01.html").write_text(
        '<section class="scene" id="s1" data-duration="8.0"><p style="color:#FF0000">x</p>'
        '<audio src="assets/sfx/pop.mp3"></audio></section>', encoding="utf-8")
    (tmp_path / "video.html").write_text("<main data-sequence></main>", encoding="utf-8")
    (tmp_path / ".vl").mkdir()
    (tmp_path / ".vl/check.json").write_text(json.dumps({"issues": [
        {"severity": "warning", "code": "still", "time": 0, "until": 13.3, "message": "quieto"},
        {"severity": "info", "code": "fast-no-blur", "message": "estilo"}]}), encoding="utf-8")
    issues = " ".join(checks.check_escenas(tmp_path))
    assert "no está incluida" in issues and "no reproduce su voz" in issues
    assert "data-duration 8.0 < voz 10.0" in issues and "hexadecimal" in issues
    assert "no existe assets/sfx/pop.mp3" in issues
    assert "givemotion still (0.0–13.3 s)" in issues and "fast-no-blur" not in issues


def test_perfil_de_voz_en_la_plantilla():
    """La receta de la voz es el comportamiento por defecto, no solo documentación."""
    plantilla = json.loads((Path(checks.__file__).parents[1]
                            / "assets/templates/audio.json").read_text(encoding="utf-8"))
    assert plantilla["gates"]["ref_min_p_lang"] >= 0.99, "0.97 dejaba pasar acento extranjero"
    perfil = plantilla["voice"]["perfil"]
    # voz de casa (250 Hz) y voz instructora del curso (≈ 170 Hz), ambas aprobadas de oído
    assert perfil["f0_hz"][0] <= 170 and 250 <= perfil["f0_hz"][1]
    assert perfil["words_per_s"][0] <= 2.2 <= perfil["words_per_s"][1], "iba a 2.2 palabras/s"
    assert "prompt" not in (plantilla.get("bgm") or {}), "MusicGen es no comercial"
