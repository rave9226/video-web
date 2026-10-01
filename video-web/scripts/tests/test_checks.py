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


# --- Reglas nacidas de un video entregado con defectos que los checks no vieron ---

def test_raiz_renombrada_se_detecta(tmp_path):
    """Si la raíz no se llama `root`, las reglas #root del CSS no aplican (texto negro)."""
    bad = GOOD_FRAME.replace('id="root"', 'id="f01-hook-root-inner"').replace(
        "<template>", "<template>\n  <style>#root { color:#fff; }</style>")
    issues = " ".join(checks.check_frame(tmp_path, _frame(tmp_path, bad, "5.2s")))
    assert "debe llevar id='root'" in issues
    assert 'id="root"' in issues or "id=\"root\"" in issues  # el aviso de _frame_timing


def test_css_sin_color_en_root(tmp_path):
    """Una regla #root sin `color:` deja que el texto herede el negro del navegador."""
    bad = GOOD_FRAME.replace("<template>", "<template>\n  <style>#root { inset:0; }</style>")
    assert any("no declara `color:`" in i
               for i in checks.check_frame(tmp_path, _frame(tmp_path, bad)))


def test_css_estila_ids_inexistentes(tmp_path):
    """Un selector #id sin elemento suele ser un id renombrado a medias."""
    bad = GOOD_FRAME.replace(
        "<template>", "<template>\n  <style>#f01-hook-viejo { color:#fff; }</style>")
    assert any("ids que no existen" in i
               for i in checks.check_frame(tmp_path, _frame(tmp_path, bad)))


def test_ancho_fijo_con_nowrap(tmp_path):
    """Una caja que no parte línea ni encoge deja el texto por fuera."""
    bad = GOOD_FRAME.replace("<template>", "<template>\n  <style>"
                             "#f01-hook-url { width:400px; white-space:nowrap; }</style>")
    assert any("white-space:nowrap" in i
               for i in checks.check_frame(tmp_path, _frame(tmp_path, bad)))


def _png(path: Path, size: tuple[int, int]) -> None:
    from PIL import Image  # pylint: disable=import-outside-toplevel
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, (200, 40, 40)).save(path)


def test_imagen_estirada(tmp_path):
    """Una captura mostrada con otra relación de aspecto sale deformada."""
    _png(tmp_path / "assets/app.png", (800, 450))          # nativa 1.778
    bad = GOOD_FRAME.replace(
        "<template>", "<template>\n  <style>#f01-hook-img { width:800px; height:500px; }</style>"
    ).replace("<h2", '<img id="f01-hook-img" src="assets/app.png" alt=""><h2')
    assert any("sale estirada" in i for i in checks.check_frame(tmp_path, _frame(tmp_path, bad)))


def test_imagen_con_object_fit_no_avisa(tmp_path):
    """`object-fit` es una decisión explícita: no se avisa."""
    _png(tmp_path / "assets/app.png", (800, 450))
    ok = GOOD_FRAME.replace(
        "<template>", "<template>\n  <style>#f01-hook-img { width:800px; height:500px;"
        " object-fit:contain; }</style>"
    ).replace("<h2", '<img id="f01-hook-img" src="assets/app.png" alt=""><h2')
    assert not any("estirada" in i for i in checks.check_frame(tmp_path, _frame(tmp_path, ok)))


def test_hallazgos_warning_no_se_silencian(tmp_path):
    """LA prueba de regresión: `hf check` da ok=true con warnings dentro y hay que verlos."""
    (tmp_path / ".vl").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".vl/check.json").write_text(json.dumps({
        "ok": True,
        "contrast": {"findings": [{"code": "contrast_below_aa", "severity": "warning",
                                   "selector": "#f01-hook-eb", "message": "4.04:1 (need 4.5:1)",
                                   "time": 60.1, "fixHint": "Try rgb(199,68,68)",
                                   "sourceFile": "compositions/frames/f01-hook.html"}],
                     "errorCount": 0, "warningCount": 1},
    }), encoding="utf-8")
    issues = " ".join(checks.check_findings(tmp_path))
    assert "4.04:1" in issues and "#f01-hook-eb" in issues


def test_solape_en_transicion_no_avisa(tmp_path):
    """Dos escenas cruzándose en un crossfade es lo esperado, no un defecto."""
    (tmp_path / ".vl").mkdir(parents=True, exist_ok=True)
    (tmp_path / "STORYBOARD.md").write_text(
        "## Frame 1 — A\n\n- src: compositions/frames/f01-a.html\n- duration: 10s\n\n"
        "## Frame 2 — B\n\n- src: compositions/frames/f02-b.html\n- duration: 10s\n",
        encoding="utf-8")
    finding = {"code": "content_overlap", "severity": "info", "selector": "#f01-a-w0",
               "message": "Two text blocks overlap", "sourceFile": "compositions/frames/f01-a.html"}
    (tmp_path / ".vl/check.json").write_text(json.dumps({
        "layout": {"findings": [{**finding, "time": 10.0},      # en el corte: esperado
                                {**finding, "time": 4.0}]},     # a mitad de escena: real
    }), encoding="utf-8")
    issues = checks.check_findings(tmp_path)
    assert len(issues) == 1 and "t=4.0s" in issues[0]


def test_perfil_de_voz_en_la_plantilla():
    """La receta de la voz es el comportamiento por defecto, no solo documentación."""
    plantilla = json.loads((Path(checks.__file__).parents[1]
                            / "assets/templates/audio.json").read_text(encoding="utf-8"))
    assert plantilla["gates"]["ref_min_p_lang"] >= 0.99, "0.97 dejaba pasar acento extranjero"
    perfil = plantilla["voice"]["perfil"]
    assert perfil["f0_hz"][0] <= 250 <= perfil["f0_hz"][1], "la voz aprobada medía 250 Hz"
    assert perfil["words_per_s"][0] <= 2.2 <= perfil["words_per_s"][1], "iba a 2.2 palabras/s"
