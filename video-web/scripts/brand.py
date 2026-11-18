"""Marca del video: colores y fuentes de capture.json → marca.css (tokens + componentes).

    brand.py sugerir            muestra variables CSS de la app para elegir colores
    brand.py aplicar            escribe marca.css y descarga las fuentes a assets/fonts/

Lee el bloque "brand" de capture.json; muted, superficies, estados y el campo de portada se
derivan si faltan. marca.css es la única fuente de color y tipografía de las escenas
givemotion (video.html la enlaza). Lo revisa `./vl check marca`.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from utils import colores  # pylint: disable=import-error

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0"
WEIGHT_NAMES = {400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold"}
# Estados semánticos (no de marca): verde = respaldado, rojo = no aparece. Traen valor por
# omisión para no tener que inventarlos.
DEFAULTS = {"positive": "#15803D", "negative": "#B91C1C"}
TEMPLATE = Path(__file__).resolve().parents[1] / "assets/templates/marca.css"


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
    # El campo de portada y cierre sale de la marca: `campo` si se pide (p. ej. el primario,
    # cuando la marca usa su primario de fondo) o el primario oscurecido, nunca un color ajeno.
    brand.setdefault("campo", colores.mix(brand["primary"], "#000000", 0.72))
    brand.setdefault("muted", colores.muted_between(brand["ink"], brand["canvas"]))
    font = (cfg.get("fonts") or [{"family": "Poppins", "weights": [400, 500, 600, 700]}])[0]
    brand["font"], brand["weights"] = font["family"], font["weights"]
    # primary puede no llegar a 4.5:1 como texto (naranjas, celestes): se oscurece lo justo
    brand["primary_text"] = colores.readable(brand["primary"], brand["ink"], brand["canvas"])
    return brand


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


def tokens(brand: dict) -> dict:
    """Variables CSS de marca.css. Fondos teñidos y líneas salen de mezclar con el lienzo."""
    canvas, ink = brand["canvas"], brand["ink"]
    # El texto de estado va sobre su propio fondo teñido, no sobre el lienzo: ajustarlo contra
    # el lienzo dejaba el verde en 4.1:1 sobre su fondo (lo detectó `./vl check marca`).
    ok_bg = colores.mix(canvas, brand["positive"], 0.14)
    bad_bg = colores.mix(canvas, brand["negative"], 0.07)
    ok = colores.readable(brand["positive"], ink, ok_bg)
    bad = colores.readable(brand["negative"], ink, bad_bg)
    accent_bg = colores.mix(canvas, brand["primary"], 0.08)
    return {
        "bg": canvas, "ink": ink, "muted": brand["muted"],
        "accent": brand["primary"],
        # el acento como texto va sobre el lienzo y sobre su tinte (chips): legible en el peor
        "accent-text": colores.readable(brand["primary_text"], ink, accent_bg),
        "accent-bg": accent_bg,
        "line": colores.mix(canvas, ink, 0.10), "surface": colores.mix(canvas, ink, 0.03),
        # campo de portada y cierre: el que pida la marca o el primario oscurecido
        "campo": brand["campo"],
        "ok": ok, "ok-bg": ok_bg, "bad": bad, "bad-bg": bad_bg}


def font_faces(family: str) -> str:
    """@font-face de cada .woff2 local de la familia (nada de fuentes de red en el render)."""
    caras = []
    pesos = {v: k for k, v in WEIGHT_NAMES.items()}
    for woff in sorted(Path("assets/fonts").glob(f"{family.replace(' ', '')}-*.woff2")):
        peso = pesos.get(woff.stem.split("-")[-1])
        if peso:
            caras.append(f"@font-face {{ font-family: '{family}'; src: url({woff.as_posix()}) "
                         f"format('woff2'); font-weight: {peso}; font-display: block; }}")
    if not caras:
        sys.exit(f"✗ no hay .woff2 de '{family}' en assets/fonts/")
    return "\n".join(caras)


def write_css(brand: dict) -> None:
    """marca.css = @font-face + :root con los tokens + componentes de la plantilla."""
    raiz = "\n".join(f"  --{k}: {v};" for k, v in tokens(brand).items())
    css = (f"/* Generado por `./vl marca` desde capture.json → brand. No lo edites: "
           f"cambia capture.json y repite. */\n{font_faces(brand['font'])}\n"
           f":root {{\n{raiz}\n  --font: '{brand['font']}', sans-serif;\n}}\n\n"
           + TEMPLATE.read_text(encoding="utf-8"))
    Path("marca.css").write_text(css, encoding="utf-8")


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
        print("\nSIGUIENTE: pon primary, ink y canvas en capture.json → brand (el campo de portada "
              "se deriva solo) y corre `./vl marca`")
        return 0
    data = json.loads(data_path.read_text(encoding="utf-8"))
    for key, value in data.get("vars", {}).items():
        if re.search(r"#[0-9a-fA-F]{3,8}|rgb", value):
            print(f"{key} = {value}")
    for key, value in data.get("computed", {}).items():
        print(f"{key} (calculado) = {value}")
    print(f"\nfuente cuerpo: {data.get('body_font')} · títulos: {data.get('heading_font')}")
    print("SIGUIENTE: llena capture.json → brand con primary, ink y canvas (el resto se deriva: "
          "no lo inventes) y corre `./vl marca`")
    return 0


def cmd_aplicar() -> int:
    """Descarga las fuentes y escribe marca.css."""
    cfg = json.loads(Path("capture.json").read_text(encoding="utf-8"))
    brand = resolve_brand(cfg)
    download_fonts(brand["font"], brand["weights"])
    write_css(brand)
    print(f"✅ marca.css (fuente {brand['font']}, acento {brand['primary']}, campo "
          f"{brand['campo']}, muted {brand['muted']}).\nSIGUIENTE: `./vl check marca`")
    return 0


def main() -> int:
    """Punto de entrada."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sug = sub.add_parser("sugerir")
    sug.add_argument("--primary", default="",
                     help="hex del acento de la app, si no hay css-vars.json")
    sub.add_parser("aplicar")
    args = parser.parse_args()
    return cmd_sugerir(args.primary) if args.cmd == "sugerir" else cmd_aplicar()


if __name__ == "__main__":
    sys.exit(main())
