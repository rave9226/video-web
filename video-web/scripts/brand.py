"""Marca del video: colores y fuentes de capture.json → marca.css (tokens + componentes).

    brand.py sugerir            muestra variables CSS de la app para elegir colores
    brand.py aplicar            escribe marca.css y descarga las fuentes a assets/fonts/

Lee el bloque "brand" de capture.json; muted, superficies, estados y el campo de portada se
derivan si faltan, y el que la marca declare (cualquier token de TOKENS_MARCA) se usa tal cual.
marca.css es la única fuente de color y tipografía de las escenas givemotion (video.html la
enlaza). Lo revisa `./vl check marca`.
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
# Tokens que una marca con manual puede fijar en capture.json → brand: se usan tal cual. Antes
# solo `campo` y `muted` se respetaban y el resto se derivaba: un curso con su manual de marca
# salió con tintes aproximados y hubo que parchar marca.css desde fuera.
TOKENS_MARCA = ("muted", "accent-text", "accent-bg", "line", "surface", "campo",
                "ok", "ok-bg", "bad", "bad-bg")
# Claves de video-web 1.x. `dark` era el fondo de portada: ignorarla en silencio dio una
# portada azul oscuro (el primario oscurecido) en vez del azul de la marca.
CLAVES_1X = {"dark": "campo", "spark": None}


def migrar_1x(brand: dict) -> dict:
    """Pasa las claves de video-web 1.x a las de 2.x (o las quita) y avisa de cada una."""
    brand = dict(brand)
    for vieja, nueva in CLAVES_1X.items():
        if vieja not in brand:
            continue
        valor = brand.pop(vieja)
        if nueva and nueva not in brand:
            brand[nueva] = valor
            print(f"⚠ capture.json → brand.{vieja} es de video-web 1.x: se usa como `{nueva}` "
                  f"({valor}). Renómbrala a `{nueva}`.")
        else:
            print(f"⚠ capture.json → brand.{vieja} es de video-web 1.x y ya no se usa: bórrala.")
    conocidas = {"primary", "ink", "canvas", *DEFAULTS, *TOKENS_MARCA}
    for clave in sorted(set(brand) - conocidas):
        print(f"⚠ capture.json → brand.{clave} no es un token de marca.css: se ignora "
              f"(válidos: primary, ink, canvas, {', '.join(TOKENS_MARCA)})")
    return brand


def resolve_brand(cfg: dict) -> dict:
    """Completa el bloque brand con valores por defecto y derivados."""
    brand = {**DEFAULTS, **{k: v.upper() for k, v in
                            migrar_1x(cfg.get("brand", {})).items() if v}}
    # Solo se piden los tres que cualquier app publica. Pedir también `dark` y `spark`
    # llevaba a inventarlos copiándolos de un ejemplo: así un video de una app roja salió
    # con portada azul.
    missing = [k for k in ("primary", "ink", "canvas") if not brand.get(k)]
    if missing:
        sys.exit(f"✗ capture.json → brand: faltan {', '.join(missing)} "
                 "(usa `./vl marca sugerir` para ver los colores de la app)")
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
    """Variables CSS de marca.css: las que fija la marca, tal cual; el resto se deriva.

    Fondos teñidos y líneas salen de mezclar con el lienzo; cada texto se ajusta contra el fondo
    donde va (el que fijó la marca, si lo fijó)."""
    canvas, ink, primary = brand["canvas"], brand["ink"], brand["primary"]
    fijo = {k: brand[k] for k in TOKENS_MARCA if brand.get(k)}
    # El texto de estado va sobre su propio fondo teñido, no sobre el lienzo: ajustarlo contra
    # el lienzo dejaba el verde en 4.1:1 sobre su fondo (lo detectó `./vl check marca`).
    ok_bg = fijo.get("ok-bg", colores.mix(canvas, brand["positive"], 0.14))
    bad_bg = fijo.get("bad-bg", colores.mix(canvas, brand["negative"], 0.07))
    accent_bg = fijo.get("accent-bg", colores.mix(canvas, primary, 0.08))
    # campo de portada y cierre: el que pida la marca (p. ej. su primario) o el primario
    # oscurecido, nunca un color ajeno
    campo = fijo.get("campo", colores.mix(primary, "#000000", 0.72))
    return {
        "bg": canvas, "ink": ink,
        "muted": fijo.get("muted", colores.muted_between(ink, canvas)),
        "accent": primary,
        # el acento como texto va sobre el lienzo y sobre su tinte (chips): legible en el peor
        "accent-text": fijo.get("accent-text",
                                colores.readable(brand["primary_text"], ink, accent_bg)),
        "accent-bg": accent_bg,
        "line": fijo.get("line", colores.mix(canvas, ink, 0.10)),
        "surface": fijo.get("surface", colores.mix(canvas, ink, 0.03)),
        "campo": campo,
        # texto sobre el campo y sobre un relleno de acento: blanco o tinta, el que contraste.
        # Un blanco fijo fallaba con marcas de primario claro (amarillo, celeste).
        "on-campo": colores.sobre(campo, ink), "on-accent": colores.sobre(primary, ink),
        "ok": fijo.get("ok", colores.readable(brand["positive"], ink, ok_bg)), "ok-bg": ok_bg,
        "bad": fijo.get("bad", colores.readable(brand["negative"], ink, bad_bg)),
        "bad-bg": bad_bg}


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
        # se muestra como `campo` (el nombre 2.x): sugerir `dark`, clave de 1.x, llevaba a
        # escribirla en capture.json, donde 2.x la ignoraba
        derivado["campo"] = colores.mix(derivado["primary"], "#000000", 0.72)
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
    tok = tokens(brand)
    print(f"✅ marca.css (fuente {brand['font']}, acento {tok['accent']}, campo "
          f"{tok['campo']}, muted {tok['muted']}).\nSIGUIENTE: `./vl check marca`")
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
