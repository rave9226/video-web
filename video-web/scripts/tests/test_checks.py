"""Pruebas de checks.py: guion, storyboard, revisión estática de escenas y estado."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import checks  # pylint: disable=import-error,wrong-import-position

GOOD_FRAME = """<template>
  <div id="root" data-composition-id="f01-hook" data-duration="5.2">
    <div id="f01-hook-bg" class="clip" data-start="0" data-duration="5.2"
         data-track-index="0"></div>
    <h2 id="f01-hook-title">Un solo lugar</h2>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <script>
    var tl = gsap.timeline({ paused: true });
    window.__timelines = window.__timelines || {};
    window.__timelines["f01-hook"] = tl;
  </script>
</template>
"""


def _frame(tmp_path: Path, frame_html: str, duration: str = "") -> dict:
    (tmp_path / "compositions/frames").mkdir(parents=True, exist_ok=True)
    (tmp_path / "compositions/frames/f01-hook.html").write_text(frame_html, encoding="utf-8")
    fields = {"src": "compositions/frames/f01-hook.html"}
    if duration:
        fields["duration"] = duration
    return {"number": 1, "fields": fields, "block": ""}


def test_good_frame_passes(tmp_path):
    """Una escena que cumple el contrato no tiene avisos."""
    assert not checks.check_frame(tmp_path, _frame(tmp_path, GOOD_FRAME, "5.2s"))


def test_frame_render_problems_are_reported(tmp_path):
    """Ids sin prefijo, fuentes de red y yoyo se detectan."""
    bad = (GOOD_FRAME.replace('id="f01-hook-title"', 'id="title"')
           .replace("<h2", '<link href="https://fonts.googleapis.com/x"><h2')
           .replace("paused: true", "paused: true, yoyo: true"))
    issues = " ".join(checks.check_frame(tmp_path, _frame(tmp_path, bad)))
    assert "ids sin prefijo" in issues
    assert "fuentes de red" in issues
    assert "yoyo" in issues


def test_clip_ending_just_before_frame_end(tmp_path):
    """Un clip que termina justo antes del final deja la transición en blanco."""
    issues = " ".join(checks.check_frame(tmp_path, _frame(tmp_path, GOOD_FRAME, "5.6s")))
    assert "f01-hook-bg termina en 5.20s" in issues


def test_guion_only_flags_long_lines(tmp_path):
    """Línea larga avisa; la duración total ya no es un error."""
    long_line = " ".join(["palabra"] * 50)
    body = "".join(f"## Line {i} — x (Frame {i})\n\n    {long_line}\n\n" for i in (1, 2, 3))
    (tmp_path / "SCRIPT.md").write_text(body, encoding="utf-8")
    issues = checks.check_guion(tmp_path)
    assert len(issues) == 3 and "(> 45)" in issues[0]


def test_storyboard_needs_src_and_real_assets_only(tmp_path):
    """Sin pattern ni rects obligatorios: solo src fNN-slug, duración y assets."""
    (tmp_path / "capture/assets").mkdir(parents=True)
    (tmp_path / "capture/assets/app-a.png").write_bytes(b"x")
    (tmp_path / "audio_meta.json").write_text(json.dumps(
        {"voices": [{"frame": 1, "duration_s": 5.0, "path": "a.wav"}]}))
    (tmp_path / "STORYBOARD.md").write_text(
        "## Frame 1 — X\n\n- src: compositions/frames/01-x.html\n- duration: 4.0s\n"
        "- asset_candidates: assets/app-a.png — a; assets/falta.png — b\n", encoding="utf-8")
    issues = " ".join(checks.check_storyboard(tmp_path))
    assert "src debe ser compositions/frames/f01-" in issues
    assert "duration 4.0s ≠ voz 5.0s" in issues
    assert "falta.png" in issues and "app-a.png" not in issues


def test_estado_suggests_first_missing(tmp_path, capsys):
    """El estado sale de los archivos y sugiere lo primero que falta."""
    (tmp_path / "BRIEF.md").write_text("---\n---\n", encoding="utf-8")
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
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


def test_compat_detecta_dependencia_cambiada(tmp_path: Path, monkeypatch):
    """Graba huellas, cambia un archivo y compat lo reporta (exit 1)."""
    monkeypatch.setattr(checks, "COMPAT", tmp_path / "compat.json")
    skills = tmp_path / "skills"
    for rel in checks.DEPENDENCIAS:
        (skills / rel).parent.mkdir(parents=True, exist_ok=True)
        (skills / rel).write_text("v1", encoding="utf-8")
    assert checks.compat(skills, grabar=True) == 0
    assert checks.compat(skills, grabar=False) == 0
    (skills / checks.DEPENDENCIAS[0]).write_text("v2", encoding="utf-8")
    assert checks.compat(skills, grabar=False) == 1
