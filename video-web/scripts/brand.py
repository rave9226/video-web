"""Design system de marca: fuentes locales → build-frame (preset) → parche de frame.md.

    brand.py sugerir            muestra variables CSS de la app para elegir colores
    brand.py aplicar [--preset blue-professional]

Lee el bloque "brand" de capture.json; muted, surface, positive y negative se derivan si
faltan. build-frame recibe solo lienzo, tinta y acento (sin colorStats) para que el mapeo
sea determinista; el resto de colores se fija después. Lo revisa `./vl check marca`.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from utils import colores, texto  # pylint: disable=import-error

PLV = Path(os.environ.get("VL_PLV_DIR", Path.home() / ".agents/skills/product-launch-video"))
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0"
WEIGHT_NAMES = {400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold"}
# `spark` es semántico, no de marca: es el anillo de foco de .PFX-ring. Como positive y
# negative, trae valor por omisión para no tener que inventarlo.
DEFAULTS = {"surface": "#FFFFFF", "positive": "#2F9E6E", "negative": "#D5484C",
            "spark": "#E0A32E"}
EXTENSIONS = """
## Extensiones de marca (normativo)

Estas reglas y este CSS mandan sobre las constantes de cualquier ejemplo de patrón.

- **Fondo oscuro** `brand-dark` ({dark}): solo portada, separadores y cierre, con el logo en
  blanco. Las escenas de contenido van sobre `bg` ({canvas}) con pantallas en `surface`.
- **Texto de acento** `primary-text` ({primary_text}): eyebrows, chips y números sobre `bg`;
  `primary` queda para rellenos y barras.
- **Chispa** `brand-spark` ({spark}): anillos de foco, un subrayado o resaltado por escena.
  Nunca como color de texto sobre el fondo claro.
- **Pantallas del producto**: capturas reales a 2x. Muéstralas a ≤ 0.5× (nunca por encima
  de su resolución nativa) dentro de la ventana canónica de abajo; su sombra es la única
  excepción a la regla de tarjetas sin sombra.
- **Logo**: `brand-logo.png` sobre fondo claro; `brand-logo-blanco.png` sobre `brand-dark`.
  **Mascota** (si existe): solo portada y cierre, nunca encima de una pantalla.
- **Movimiento**: asentamientos suaves `power3.out`; sin `back.out`, `elastic` ni rebotes.

CSS canónico (copia tal cual y reemplaza `PFX` por el id de tu escena, p. ej. `f04-leads`):

```css
.PFX-win {{ position:absolute; background:{surface}; border-radius:14px; overflow:hidden;
  box-shadow:0 30px 80px {dark}2E; }}
.PFX-win-bar {{ height:34px; display:flex; align-items:center; gap:8px; padding:0 16px;
  background:{surface}; border-bottom:1px solid {primary}1A; }}
.PFX-win-dot {{ width:11px; height:11px; border-radius:50%; background:{ink}24; }}
.PFX-win-url {{ margin-left:12px; padding:5px 14px; border-radius:100px; background:{canvas};
  font:{w_med} 13px/1 "{font}"; color:{muted}; }}
.PFX-eyebrow {{ display:flex; align-items:center; gap:14px; font:{w_semi} 16px/1.2 "{font}";
  letter-spacing:.08em; text-transform:uppercase; color:{primary_text}; }}
.PFX-eyebrow::before {{ content:""; width:60px; height:4px; border-radius:2px;
  background:{primary}; }}
.PFX-h2 {{ font:{w_semi} 52px/1.1 "{font}"; letter-spacing:-.02em; color:{ink}; }}
.PFX-chip {{ display:inline-flex; align-items:center; gap:10px; height:48px; padding:0 22px;
  border-radius:100px; background:{primary}14; border:1.5px solid {primary}33;
  font:{w_med} 20px/1 "{font}"; color:{chip_text}; }}
.PFX-ring {{ position:absolute; border:2.5px solid {spark}; border-radius:10px;
  box-shadow:0 0 0 6px {spark}33, 0 0 24px {spark}55; pointer-events:none; }}
```

La URL de la barra de ventana es `{url_pill}`.
"""


def resolve_brand(cfg: dict) -> dict:
    """Completa el bloque brand con valores por defecto y derivados."""
    brand = {**DEFAULTS, **{k: v.upper() for k, v in cfg.get("brand", {}).items() if v}}
    # Solo se piden los tres que cualquier app publica. Pedir también `dark` y `spark`
    # llevaba a inventarlos copiándolos de un ejemplo: así un video de una app roja salió
    # con portada azul.
    missing = [k for k in ("primary", "ink", "canvas") if not brand.get(k)]
    if missing:
        sys.exit(f"✗ capture.json → brand: faltan {', '.join(missing)} "
                 "(usa `./vl marca sugerir` para ver los colores de la app)")
    # `dark` es el campo de portada y cierre: el primario oscurecido, no un color ajeno.
    brand.setdefault("dark", colores.mix(brand["primary"], "#000000", 0.72))
    brand.setdefault("muted", colores.muted_between(brand["ink"], brand["canvas"]))
    brand["url_pill"] = re.sub(r"^https?://", "", cfg.get("base_url", "")).rstrip("/")
    font = (cfg.get("fonts") or [{"family": "Poppins", "weights": [400, 500, 600, 700]}])[0]
    brand["font"], brand["weights"] = font["family"], font["weights"]
    # el CSS canónico solo usa pesos descargados (si no, el navegador los sintetiza)
    brand["w_med"] = min(font["weights"], key=lambda w: abs(w - 500))
    brand["w_semi"] = min(font["weights"], key=lambda w: abs(w - 600))
    # primary puede no llegar a 4.5:1 como texto (naranjas, celestes): se oscurece lo justo
    brand["primary_text"] = colores.readable(brand["primary"], brand["ink"], brand["canvas"])
    # El chip no está sobre el lienzo sino sobre su propio fondo teñido (primary al 8 %):
    # ahí el contraste baja. Medirlo contra el lienzo daba chips que fallaban AA por poco.
    chip_bg = colores.mix(brand["canvas"], brand["primary"], 0x14 / 255)
    brand["chip_bg"] = chip_bg
    brand["chip_text"] = colores.readable(brand["primary"], brand["ink"], chip_bg)
    return brand


def write_tokens(brand: dict) -> None:
    """tokens.json para build-frame: solo lienzo, tinta y acento, sin colorStats."""
    path = Path("capture/extracted/tokens.json")
    tokens = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    front = texto.parse_frontmatter(Path("BRIEF.md").read_text(encoding="utf-8"))
    tokens.update({
        "title": front.get("producto", tokens.get("title", "")),
        "description": front.get("message", tokens.get("description", "")),
        # ponytail: con más colores la heurística de build-frame elige mal (el blanco como
        # lienzo, la chispa como acento); el resto se fija en patch_frame.
        "colors": [brand["canvas"], brand["ink"], brand["primary"]],
        "colorStats": [],
        "fonts": [{"family": brand["font"], "weights": brand["weights"], "variable": False}]})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tokens, ensure_ascii=False, indent=2), encoding="utf-8")


def download_fonts(family: str, weights: list[int]) -> None:
    """woff2 latin (incluye tildes y ñ) de Google Fonts → assets/fonts/<Familia>-<Peso>."""
    url = ("https://fonts.googleapis.com/css2?family="
           f"{family.replace(' ', '+')}:wght@{';'.join(map(str, weights))}&display=swap")
    out = Path("assets/fonts")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            css = resp.read().decode()
    except urllib.error.HTTPError:
        if list(out.glob(f"{family.replace(' ', '')}-*.woff2")):
            return  # fuente propia ya copiada por el usuario
        sys.exit(f"✗ '{family}' no está en Google Fonts: copia sus .woff2 a assets/fonts/ como "
                 f"{family.replace(' ', '')}-Regular.woff2, -Medium, -SemiBold, -Bold y repite")
    out.mkdir(parents=True, exist_ok=True)
    for subset, body in re.findall(r"/\*\s*([\w-]+)\s*\*/\s*@font-face\s*\{([^}]*)\}", css):
        if subset != "latin":
            continue
        weight = int(re.search(r"font-weight:\s*(\d+)", body).group(1))
        target = out / f"{family.replace(' ', '')}-{WEIGHT_NAMES.get(weight, weight)}.woff2"
        if not target.exists():
            urllib.request.urlretrieve(re.search(r"url\((https://[^)]+)\)", body).group(1),
                                       target)


def set_color(md: str, key: str, value: str) -> str:
    """Fija `key` en el bloque colors: del frontmatter (lo agrega al final si no existe)."""
    line = re.compile(rf'^(\s{{2}}{re.escape(key)}:\s*).*$', re.MULTILINE)
    block = re.search(r"^colors:\s*\n((?:\s{2}.*\n)+)", md, re.MULTILINE)
    if line.search(md[block.start():block.end()]):
        head, body, tail = md[:block.start()], md[block.start():block.end()], md[block.end():]
        return head + line.sub(rf'\g<1>"{value}"', body, count=1) + tail
    return md[:block.end()] + f'  {key}: "{value}"\n' + md[block.end():]


def patch_frame(brand: dict) -> None:
    """Colores que build-frame no fija y las extensiones de marca con el CSS canónico."""
    path = Path("frame.md")
    md = path.read_text(encoding="utf-8")
    for key, source in (("bg", "canvas"), ("primary", "primary"), ("text", "ink"),
                        ("text-muted", "muted"), ("positive", "positive"),
                        ("negative", "negative"), ("brand-dark", "dark"),
                        ("brand-spark", "spark"), ("surface", "surface")):
        md = set_color(md, key, brand[source])
    md = set_color(md, "primary-text", brand["primary_text"])
    # la descripción del preset nombra sus propios colores y fuentes: confunde a los workers
    md = re.sub(r"^description: >\n(?:  .*\n)+",
                f"description: >\n  Frame de marca: colores en `colors`, fuente {brand['font']} "
                "local (assets/fonts), CSS canónico al final.\n", md, count=1, flags=re.MULTILINE)
    path.write_text(md.rstrip() + "\n" + EXTENSIONS.format(**brand), encoding="utf-8")


def cmd_sugerir(primary: str = "") -> int:
    """Muestra variables CSS y fuentes capturadas de la app, o deriva de un primario dado."""
    data_path = Path("capture/extracted/css-vars.json")
    if not data_path.exists():
        # Sin captura propia (login SSO, capturas de otra fuente) antes se abortaba, y los
        # colores terminaban copiados de un ejemplo. Con --primary se derivan.
        if not primary:
            sys.exit("✗ falta capture/extracted/css-vars.json (lo escribe `./vl captura`).\n"
                     "  Si no puedes capturar, saca el primario del CSS de la app o de su logo "
                     "y corre:\n  ./vl marca sugerir --primary \"#RRGGBB\"\n"
                     "  Nunca copies colores de otro proyecto (references/marca.md).")
        derivado = {"primary": primary.upper(), "ink": "#0B1020", "canvas": "#F6F7F9"}
        derivado["dark"] = colores.mix(derivado["primary"], "#000000", 0.72)
        print("⚠ sin css-vars.json: estos colores NO se leyeron de la app.")
        print(f"  Verifica `primary` contra un botón o el logo: {derivado['primary']}")
        for key, value in derivado.items():
            print(f"{key} = {value}")
        print("\nSIGUIENTE: pon primary, ink y canvas en capture.json → brand (dark y spark se "
              "derivan solos) y corre `./vl marca`")
        return 0
    data = json.loads(data_path.read_text(encoding="utf-8"))
    for key, value in data.get("vars", {}).items():
        if re.search(r"#[0-9a-fA-F]{3,8}|rgb", value):
            print(f"{key} = {value}")
    for key, value in data.get("computed", {}).items():
        print(f"{key} (calculado) = {value}")
    print(f"\nfuente cuerpo: {data.get('body_font')} · títulos: {data.get('heading_font')}")
    print("SIGUIENTE: llena capture.json → brand con primary, ink y canvas (dark y spark se "
          "derivan solos: no los inventes) y corre `./vl marca`")
    return 0


def cmd_aplicar(preset: str) -> int:
    """Construye frame.md desde el preset y lo adapta a la marca."""
    cfg = json.loads(Path("capture.json").read_text(encoding="utf-8"))
    brand = resolve_brand(cfg)
    write_tokens(brand)
    download_fonts(brand["font"], brand["weights"])
    subprocess.run(["node", str(PLV / "scripts/build-frame.mjs"), "--preset", preset,
                    "--hyperframes", "."], check=True)
    patch_frame(brand)
    print(f"✅ frame.md adaptado (preset {preset}, fuente {brand['font']}, "
          f"muted {brand['muted']}).\nSIGUIENTE: `./vl check marca`")
    return 0


def main() -> int:
    """Punto de entrada."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sug = sub.add_parser("sugerir")
    sug.add_argument("--primary", default="",
                     help="hex del acento de la app, si no hay css-vars.json")
    sub.add_parser("aplicar").add_argument("--preset", default="blue-professional")
    args = parser.parse_args()
    return cmd_sugerir(args.primary) if args.cmd == "sugerir" else cmd_aplicar(args.preset)


if __name__ == "__main__":
    sys.exit(main())
