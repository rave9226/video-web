"""Genera las escenas de `compositions/frames/` desde `scenes.json`.

Un solo generador para todas las escenas con ventana: así todas comparten geometría,
colores y ritmo. Antes cada escena la escribía un worker distinto y cada uno inventaba su
ventana y su zoom; el resultado eran capturas recortadas y anillos de foco corridos.

Uso: `./vl escenas` (o `./vl escenas --solo f03-menu,f04-tablero`).
"""
import argparse
import json
import re
import sys
from pathlib import Path

from utils import imagenes, texto  # pylint: disable=import-error

FRAMES = Path("compositions/frames")
GSAP = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
# Clases canónicas de frame.md que las escenas reutilizan en vez de recrear.
CANONICAS = ("eyebrow", "h2", "chip", "ring", "win", "win-bar", "win-dot", "win-url")


def leer_marca(proj: Path) -> tuple[dict, dict]:
    """Colores del frontmatter de frame.md y cuerpo de cada clase .PFX-* canónica."""
    md = (proj / "frame.md").read_text(encoding="utf-8")
    colores = dict(re.findall(r'^\s{2}([\w-]+):\s*"([^"]+)"', md, re.MULTILINE))
    reglas = {}
    for clase in CANONICAS:
        hallado = re.search(rf"\.PFX-{re.escape(clase)}\s*\{{([^}}]*)\}}", md)
        if hallado:
            reglas[clase] = " ".join(hallado.group(1).split())
    faltan = [c for c in ("eyebrow", "h2", "chip", "ring") if c not in reglas]
    if faltan:
        sys.exit(f"✗ frame.md no trae las clases .PFX-{{{','.join(faltan)}}}: corre `./vl marca`")
    return colores, reglas


def fuentes(proj: Path) -> str:
    """Los @font-face locales de frame.md, tal cual (nada de fuentes de red)."""
    md = (proj / "frame.md").read_text(encoding="utf-8")
    caras = re.findall(r"@font-face\s*\{[^}]*\}", md)
    if not caras:
        sys.exit("✗ frame.md no trae @font-face local: corre `./vl marca`")
    return "".join(" ".join(c.split()) for c in caras)


def duraciones(proj: Path) -> dict[str, float]:
    """Duración de cada escena según STORYBOARD.md (ya sincronizado por `./vl prep`)."""
    out = {}
    for frame in texto.split_frames((proj / "STORYBOARD.md").read_text(encoding="utf-8")):
        src, dur = frame["fields"].get("src", ""), frame["fields"].get("duration")
        if src and dur:
            out[Path(src).stem] = texto.seconds(dur)
    return out


def _css_comun(slug: str, col: dict, reglas: dict, caras: str) -> str:
    """Base de toda escena: colores explícitos y las clases canónicas con prefijo propio."""
    propias = "".join(f".{slug}-{clase} {{ {cuerpo} }}\n" for clase, cuerpo in reglas.items())
    return f"""{caras}
#root {{ position:relative; width:1920px; height:1080px; overflow:hidden;
  font-family:"{col.get('font-family', 'sans-serif')}",sans-serif; color:{col['text']}; }}
#{slug}-bg {{ position:absolute; inset:0; background:{col['bg']}; }}
#{slug}-stage {{ position:absolute; inset:0; }}
{propias}.{slug}-w {{ display:inline-block; white-space:pre; }}
"""


def _css_columna(slug: str) -> str:
    """Columna de texto a la izquierda. Solo la usan las escenas con ventana."""
    return f"""
#{slug}-col {{ position:absolute; left:92px; width:472px; display:flex;
  flex-direction:column; align-items:flex-start; }}
#{slug}-h2 {{ margin:0 0 34px; }}
#{slug}-chips {{ display:flex; flex-direction:column; align-items:flex-start; gap:11px; }}
.{slug}-chip {{ max-width:472px; height:auto; min-height:44px; padding:7px 20px; }}
"""


def _plantilla(slug: str, dur: float, css: str, cuerpo: str, js: str) -> str:
    """Envoltura que cumple el contrato de sub-composición (id root, timeline pausado)."""
    return f"""<template>
  <style>{css}</style>
  <div id="root" data-composition-id="{slug}" data-width="1920" data-height="1080"
       data-duration="{dur}">
    <div id="{slug}-bg" class="clip" data-start="0" data-duration="{dur}"
         data-track-index="0"></div>
    <div id="{slug}-stage" class="clip" data-start="0" data-duration="{dur}"
         data-track-index="1">
{cuerpo}
    </div>
  </div>
  <script src="{GSAP}"></script>
  <script>
    (function () {{
      var P = "{slug}-", el = function (k) {{ return document.getElementById(P + k); }};
      var tl = gsap.timeline({{ paused: true }});
{js}
      window.__timelines = window.__timelines || {{}};
      window.__timelines["{slug}"] = tl;
    }})();
  </script>
</template>
"""


def _js_entradas(items: list, prefijo: str, dy: int = 18) -> str:
    """Un fromTo por elemento, cada uno en el segundo de su palabra."""
    return "".join(
        f'      tl.fromTo(el("{prefijo}{i}"), {{ opacity: 0, y: {dy} }}, '
        f'{{ opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }}, '
        f"{max(0.1, float(t) - 0.06):.2f});\n"
        for i, t in enumerate(items))


def escena_ventana(spec: dict, dur: float, col: dict, reglas: dict, caras: str,
                   proj: Path, ventana: dict) -> str:
    # pylint: disable=too-many-locals,too-many-arguments,too-many-positional-arguments
    """Captura completa en una ventana, con anillos de foco sobre lo que nombra la voz.

    Sin zoom de cámara: el foco se logra atenuando el resto. Un zoom sobre una captura a
    1x recorta los bordes y desalinea los anillos.
    """
    slug = spec["slug"]
    ancho, izq, barra = ventana["width"], ventana["left"], ventana["bar"]
    primera = proj / spec["imgs"][0][0]
    if not primera.exists():
        sys.exit(f"✗ {slug}: no existe {spec['imgs'][0][0]}")
    nativo_w, nativo_h = imagenes.dimensiones(primera)
    alto_vista = round(ancho * nativo_h / nativo_w)
    top = round((1080 - (alto_vista + barra)) / 2)
    escala = ancho / nativo_w
    css = _css_comun(slug, col, reglas, caras) + _css_columna(slug) + f"""
#{slug}-col {{ top:{max(top - 6, 86)}px; }}
#{slug}-win {{ position:absolute; left:{izq}px; top:{top}px; width:{ancho}px;
  height:{alto_vista + barra}px; }}
#{slug}-view {{ position:absolute; left:0; top:{barra}px; width:{ancho}px;
  height:{alto_vista}px; overflow:hidden; background:{col['bg']}; }}
.{slug}-shot {{ position:absolute; left:0; top:0; width:{ancho}px; height:{alto_vista}px;
  display:block; max-width:none; }}
.{slug}-ring {{ opacity:0; box-sizing:border-box;
  box-shadow:0 0 0 4000px {col['text']}17, 0 0 22px {col.get('brand-spark', '#E0A32E')}88; }}
"""
    palabras = "".join(f'<span id="{slug}-w{i}" class="{slug}-w">{t}</span> '
                       for i, (t, _) in enumerate(spec.get("h2", [])))
    chips = "".join(f'<div id="{slug}-chip{i}" class="{slug}-chip">{c[0]}</div>'
                    for i, c in enumerate(spec.get("chips", [])))
    imgs = "".join(f'<img id="{slug}-shot{i}" class="{slug}-shot" src="{s}" alt="" />'
                   for i, (s, _) in enumerate(spec["imgs"]))
    anillos = "".join(f'<div id="{slug}-ring{i}" class="{slug}-ring {slug}-ring"></div>'
                      for i in range(len(spec.get("rings", []))))
    cuerpo = f"""      <div id="{slug}-col">
        <div id="{slug}-eb" class="{slug}-eyebrow">{spec.get('eyebrow', '')}</div>
        <h2 id="{slug}-h2" class="{slug}-h2">{palabras}</h2>
        <div id="{slug}-chips">{chips}</div>
      </div>
      <div id="{slug}-win" class="{slug}-win">
        <div id="{slug}-bar" class="{slug}-win-bar"><span class="{slug}-win-dot"></span>\
<span class="{slug}-win-dot"></span><span class="{slug}-win-dot"></span>\
<span id="{slug}-url" class="{slug}-win-url">{spec.get('url', '')}</span></div>
        <div id="{slug}-view">{imgs}{anillos}</div>
      </div>"""
    js = ('      tl.fromTo(el("win"), { x: 110, opacity: 0 }, { x: 0, opacity: 1, '
          'duration: 1.0, ease: "power3.out" }, 0);\n'
          '      tl.fromTo(el("eb"), { opacity: 0, x: -12 }, { opacity: 1, x: 0, '
          'duration: 0.5, ease: "power3.out" }, 0.05);\n')
    js += _js_entradas([t for _, t in spec.get("h2", [])], "w", 24)
    js += _js_entradas([c[1] for c in spec.get("chips", [])], "chip")
    for i, (_, t) in enumerate(spec["imgs"]):
        if i == 0:
            js += '      gsap.set(el("shot0"), { opacity: 1 });\n'
        else:
            js += (f'      gsap.set(el("shot{i}"), {{ opacity: 0 }});\n'
                   f'      tl.to(el("shot{i}"), {{ opacity: 1, duration: 0.4, '
                   f'ease: "power1.inOut" }}, {float(t) - 0.1:.2f});\n')
    for i, (caja, entra, sale) in enumerate(spec.get("rings", [])):
        x, y, w, h = caja
        pad = 6
        js += (f'      Object.assign(el("ring{i}").style, {{ '
               f'left: "{(x - pad) * escala:.1f}px", top: "{(y - pad) * escala:.1f}px", '
               f'width: "{(w + 2 * pad) * escala:.1f}px", '
               f'height: "{(h + 2 * pad) * escala:.1f}px" }});\n'
               f'      tl.fromTo(el("ring{i}"), {{ opacity: 0 }}, {{ opacity: 1, '
               f'duration: 0.32, ease: "power2.out" }}, {float(entra):.2f});\n'
               f'      tl.to(el("ring{i}"), {{ opacity: 0, duration: 0.25, '
               f'ease: "power1.in" }}, {max(float(entra) + 0.4, float(sale) - 0.05):.2f});\n')
    return _plantilla(slug, dur, css, cuerpo, js)


def escena_marca(spec: dict, dur: float, col: dict, reglas: dict, caras: str) -> str:
    # pylint: disable=too-many-locals
    """Portada y cierre: el campo de marca (`brand-dark`) con tipografía blanca.

    Las dos con el mismo tratamiento. Una portada clara con un cierre oscuro, o un título
    que hereda el negro del navegador, se lee como un error de montaje.
    """
    slug = spec["slug"]
    campo = col.get("brand-dark", col["text"])
    chispa = col.get("brand-spark", "#E0A32E")
    # La píldora de la URL se dimensiona por su contenido (inline-flex + padding): con un
    # ancho fijo el texto se sale, y eso llegó a un video entregado.
    css_url = f"""#{slug}-urlwrap {{ position:absolute; left:0; top:684px; width:1920px;
  text-align:center; }}
#{slug}-url2 {{ display:inline-flex; align-items:center; height:84px; padding:0 48px;
  border-radius:100px; border:2px solid #FFFFFF5C; background:#FFFFFF1A;
  font:500 38px/1 inherit; letter-spacing:.02em; color:#FFFFFF; }}
""" if spec.get("url") else ""
    css = _css_comun(slug, col, reglas, caras) + f"""
#root {{ color:#FFFFFF; }}
#{slug}-bg {{ background:radial-gradient(ellipse 78% 66% at 50% 40%,
  {campo} 0%, {col['text']} 78%); }}
#{slug}-rule {{ position:absolute; left:50%; margin-left:-110px; top:348px; width:220px;
  height:6px; border-radius:3px; background:{chispa}; }}
#{slug}-title {{ position:absolute; left:0; top:392px; width:1920px; text-align:center;
  font:700 158px/1.04 inherit; letter-spacing:-.025em; color:#FFFFFF; }}
#{slug}-sub {{ position:absolute; left:0; top:596px; width:1920px; text-align:center;
  font:500 34px/1.3 inherit; letter-spacing:.09em; text-transform:uppercase;
  color:#FFFFFFD9; }}
{css_url}.{slug}-pill {{ position:absolute; display:inline-flex; align-items:center;
  justify-content:center; height:78px; padding:0 34px; border-radius:100px;
  border:2px solid #FFFFFF59; background:#FFFFFF1F; font:500 33px/1 inherit;
  color:#FFFFFF; white-space:nowrap; }}
.{slug}-stat {{ position:absolute; text-align:center; color:#FFFFFF; }}
.{slug}-stat b {{ display:block; font:700 92px/1 inherit; letter-spacing:-.02em; }}
.{slug}-stat span {{ display:block; margin-top:10px; font:500 26px/1.2 inherit;
  letter-spacing:.07em; text-transform:uppercase; color:#FFFFFFC7; }}
"""
    pills = spec.get("chips", []) + [(f"{n} {t}", s) for n, t, s in
                                     (x for x in spec.get("steps", []) if len(x) == 3)]
    cuerpo = "".join(
        f'      <div class="{slug}-pill" id="{slug}-k{i}">{p[0]}</div>\n'
        for i, p in enumerate(pills))
    cuerpo += "".join(
        f'      <div class="{slug}-stat" id="{slug}-s{i}"><b>{v}</b><span>{lab}</span></div>\n'
        for i, (v, lab, _) in enumerate(spec.get("stats", [])))
    cuerpo += f"""      <div id="{slug}-rule"></div>
      <div id="{slug}-title">{spec['title']}</div>
      <div id="{slug}-sub">{spec.get('sub', '')}</div>"""
    if spec.get("url"):
        cuerpo += (f'\n      <div id="{slug}-urlwrap">'
                   f'<span id="{slug}-url2">{spec["url"]}</span></div>')
    revela = float(spec.get("reveal", max(0.0, dur - 4.0)))
    xs = [460, 960, 1460, 760, 1160]
    js = ""
    for i, pill in enumerate(pills):
        js += (f'      gsap.set(el("k{i}"), {{ left: {xs[i % len(xs)]}, top: 480, '
               'xPercent: -50, yPercent: -50 });\n'
               f'      tl.fromTo(el("k{i}"), {{ opacity: 0, y: 26, scale: 0.94 }}, '
               '{ opacity: 1, y: 0, scale: 1, duration: 0.6, ease: "power3.out" }, '
               f'{max(0.1, float(pill[1]) - 0.06):.2f});\n'
               f'      tl.to(el("k{i}"), {{ opacity: 0, y: -22, duration: 0.6, '
               f'ease: "power2.inOut" }}, {revela - 0.3:.2f});\n')
    for i, (_, _, cuando) in enumerate(spec.get("stats", [])):
        js += (f'      gsap.set(el("s{i}"), {{ left: {560 + i * 800}, top: 530, '
               'xPercent: -50, yPercent: -50 });\n'
               f'      tl.fromTo(el("s{i}"), {{ opacity: 0, y: 26 }}, {{ opacity: 1, y: 0, '
               f'duration: 0.7, ease: "power3.out" }}, {float(cuando):.2f});\n'
               f'      tl.to(el("s{i}"), {{ opacity: 0, y: -18, duration: 0.6, '
               f'ease: "power2.inOut" }}, {revela - 0.3:.2f});\n')
    js += (f'      tl.fromTo(el("rule"), {{ scaleX: 0, opacity: 0 }}, {{ scaleX: 1, '
           f'opacity: 1, duration: 0.7, ease: "power3.out" }}, {revela:.2f});\n'
           f'      tl.fromTo(el("title"), {{ opacity: 0, y: 42, scale: 0.94 }}, '
           f'{{ opacity: 1, y: 0, scale: 1, duration: 0.9, ease: "power3.out" }}, '
           f'{revela + 0.1:.2f});\n'
           f'      tl.fromTo(el("sub"), {{ opacity: 0, y: 22 }}, {{ opacity: 1, y: 0, '
           f'duration: 0.8, ease: "power3.out" }}, {revela + 1.5:.2f});\n')
    if spec.get("url"):
        js += (f'      tl.fromTo(el("urlwrap"), {{ opacity: 0, y: 22 }}, {{ opacity: 1, '
               f'y: 0, duration: 0.7, ease: "power3.out" }}, {revela + 2.1:.2f});\n')
    return _plantilla(slug, dur, css, cuerpo, js)


def escena_pasos(spec: dict, dur: float, col: dict, reglas: dict, caras: str) -> str:
    """Diagrama de pasos numerados: el modelo del sistema antes de la primera pantalla.

    En un video de capacitación esta escena es la que da el marco; sin ella cada pantalla
    se ve como un formulario suelto.
    """
    slug = spec["slug"]
    css = _css_comun(slug, col, reglas, caras) + f"""
#{slug}-eb {{ position:absolute; left:0; top:132px; width:1920px;
  display:flex; justify-content:center; }}
#{slug}-h2 {{ position:absolute; left:0; top:178px; width:1920px; text-align:center;
  margin:0; }}
.{slug}-card {{ position:absolute; left:460px; width:1000px; height:146px; display:flex;
  align-items:center; gap:34px; padding:0 44px; box-sizing:border-box;
  background:{col.get('surface', '#FFFFFF')}; border:1.5px solid {col['primary']}26;
  border-radius:18px; }}
.{slug}-num {{ flex:0 0 auto; width:76px; height:76px; border-radius:50%;
  background:{col['primary']}; color:{col.get('surface', '#FFFFFF')}; display:flex;
  align-items:center; justify-content:center; font:700 38px/1 inherit; }}
.{slug}-txt b {{ display:block; font:700 46px/1.1 inherit; color:{col['text']}; }}
.{slug}-txt span {{ display:block; margin-top:7px; font:400 28px/1.25 inherit;
  color:{col['text-muted']}; }}
"""
    palabras = "".join(f'<span id="{slug}-w{i}" class="{slug}-w">{t}</span> '
                       for i, (t, _) in enumerate(spec.get("h2", [])))
    pasos = spec["steps"]
    cuerpo = f"""      <div id="{slug}-eb"><span class="{slug}-eyebrow">\
{spec.get('eyebrow', '')}</span></div>
      <h2 id="{slug}-h2" class="{slug}-h2">{palabras}</h2>
"""
    cuerpo += "".join(
        f'      <div class="{slug}-card" id="{slug}-card{i}">'
        f'<div class="{slug}-num">{p[0]}</div>'
        f'<div class="{slug}-txt"><b>{p[1]}</b><span>{p[2]}</span></div></div>\n'
        for i, p in enumerate(pasos))
    tops = [330, 520, 710, 900]
    js = ('      tl.fromTo(el("eb"), { opacity: 0, y: -12 }, { opacity: 1, y: 0, '
          'duration: 0.6, ease: "power3.out" }, 0.2);\n')
    js += _js_entradas([t for _, t in spec.get("h2", [])], "w", 28)
    for i, paso in enumerate(pasos):
        js += (f'      gsap.set(el("card{i}"), {{ top: {tops[i % len(tops)]} }});\n'
               f'      tl.fromTo(el("card{i}"), {{ opacity: 0, y: 30 }}, {{ opacity: 1, '
               f'y: 0, duration: 0.7, ease: "power3.out" }}, '
               f'{max(0.1, float(paso[3]) - 0.06):.2f});\n')
    return _plantilla(slug, dur, css, cuerpo, js)


TIPOS = {"window": escena_ventana, "cover": escena_marca, "close": escena_marca,
         "steps": escena_pasos}


def main() -> int:
    # pylint: disable=too-many-locals
    """Punto de entrada."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--solo", default="", help="slugs separados por coma")
    args = parser.parse_args()
    proj = Path.cwd()
    cfg_path = proj / "scenes.json"
    if not cfg_path.exists():
        sys.exit("✗ falta scenes.json (plantilla: assets/templates/scenes.json de la skill)")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    col, reglas = leer_marca(proj)
    caras = fuentes(proj)
    durs = duraciones(proj)
    ventana = {"left": 620, "width": 1240, "bar": 34, **cfg.get("window", {})}
    pedidos = {s for s in args.solo.split(",") if s}
    FRAMES.mkdir(parents=True, exist_ok=True)
    hechas = 0
    for spec in cfg["frames"]:
        slug = spec["slug"]
        if pedidos and slug not in pedidos:
            continue
        if slug not in durs:
            sys.exit(f"✗ {slug} no está en STORYBOARD.md (o le falta duration): corre "
                     "`./vl prep`")
        constructor = TIPOS.get(spec.get("kind", "window"))
        if not constructor:
            sys.exit(f"✗ {slug}: kind '{spec.get('kind')}' no es {' | '.join(TIPOS)}")
        html = (constructor(spec, durs[slug], col, reglas, caras, proj, ventana)
                if spec.get("kind", "window") == "window"
                else constructor(spec, durs[slug], col, reglas, caras))
        (FRAMES / f"{slug}.html").write_text(html, encoding="utf-8")
        print(f"  ✓ {slug} ({durs[slug]}s, {spec.get('kind', 'window')})")
        hechas += 1
    print(f"✅ {hechas} escena(s) en {FRAMES}\nSIGUIENTE: `./vl ensamblar` y `./vl snap`")
    return 0


if __name__ == "__main__":
    sys.exit(main())
