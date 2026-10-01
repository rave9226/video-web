"""Manual de usuario de una app web: captura, armado y PDF.

Independiente: no necesita un proyecto de video. Si existe uno de `video-web`, reutiliza sus
capturas y sus colores en vez de volver a sacarlos (`./ml init --desde <proyecto>`).

Comandos: `init`, `pantalla`, `pdf`, `check`.
"""
import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
IMG = Path("img")
FUENTE = Path("manual.md")
MARCA = Path("marca.json")
# Colores de respaldo: grises neutros. Si el manual no declara marca, sale sobrio, no inventado.
MARCA_BASE = {"primary": "#1F2937", "ink": "#111827", "canvas": "#F9FAFB",
              "muted": "#6B7280", "font": "Helvetica, Arial, sans-serif"}


def _marca() -> dict:
    """Colores y fuente del manual (marca.json), con respaldo neutro."""
    if MARCA.exists():
        return {**MARCA_BASE, **json.loads(MARCA.read_text(encoding="utf-8"))}
    return dict(MARCA_BASE)


def _marca_desde_frame(frame: Path) -> dict | None:
    """Lee los colores de un frame.md de video-web, para no volver a definirlos."""
    if not frame.exists():
        return None
    md = frame.read_text(encoding="utf-8")
    col = dict(re.findall(r'^\s{2}([\w-]+):\s*"(#[0-9A-Fa-f]{6})"', md, re.MULTILINE))
    if not col.get("primary"):
        return None
    fuente = re.search(r'font-family:\s*"([^"]+)"', md)
    return {"primary": col.get("primary-text", col["primary"]), "ink": col.get("text", "#111827"),
            "canvas": col.get("bg", "#F9FAFB"), "muted": col.get("text-muted", "#6B7280"),
            "font": f'{fuente.group(1)}, sans-serif' if fuente else MARCA_BASE["font"]}


def cmd_init(desde: str, titulo: str) -> int:
    """Crea manual.md desde la plantilla y, si se indica, trae capturas y marca."""
    IMG.mkdir(exist_ok=True)
    if not FUENTE.exists():
        plantilla = (SKILL / "assets/templates/MANUAL.md").read_text(encoding="utf-8")
        FUENTE.write_text(plantilla.replace("<PRODUCTO>", titulo or "<PRODUCTO>"),
                          encoding="utf-8")
        print(f"  ✓ {FUENTE} (desde la plantilla)")
    if desde:
        proy = Path(desde).expanduser()
        if not proy.exists():
            sys.exit(f"✗ no existe {proy}")
        copiadas = 0
        for origen in ("capture/assets", "assets"):
            carpeta = proy / origen
            if not carpeta.is_dir():
                continue
            for img in sorted(carpeta.glob("app-*.*")):
                destino = IMG / img.name
                if not destino.exists():
                    shutil.copy2(img, destino)
                    copiadas += 1
            if copiadas:
                break
        print(f"  ✓ {copiadas} captura(s) en {IMG}/")
        marca = _marca_desde_frame(proy / "frame.md")
        if marca and not MARCA.exists():
            MARCA.write_text(json.dumps(marca, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")
            print(f"  ✓ {MARCA} con los colores de {proy / 'frame.md'}")
    if not MARCA.exists():
        print(f"  · sin {MARCA}: el PDF saldrá en grises neutros. Para usar la marca, escribe "
              f'{MARCA} con primary, ink, canvas y font (los colores salen de la app, '
              "no de un ejemplo).")
    print("SIGUIENTE: escribe manual.md (una sección por pantalla, cada una con PARA QUÉ "
          "sirve) y corre `./ml pdf`")
    return 0


def cmd_pantalla(url: str, ruta: str, nombre: str, perfil: str, esperar: float) -> int:
    """Captura una pantalla en solo lectura, para ilustrar una sección del manual.

    Solo lectura: no hay pasos de envío ni de guardado. Si la app pide login, se usa un
    perfil de Chrome con la sesión ya abierta (igual que video-web con SSO).
    """
    try:
        from playwright.sync_api import sync_playwright  # pylint: disable=import-outside-toplevel
    except ImportError:
        sys.exit("✗ falta playwright: pip install playwright && playwright install chromium")
    IMG.mkdir(exist_ok=True)
    destino = IMG / f"{nombre}.png"
    perfil = perfil or os.environ.get("BROWSER_PROFILE", "")
    with sync_playwright() as play:
        if perfil:
            ctx = play.chromium.launch_persistent_context(
                perfil, viewport={"width": 1440, "height": 900}, device_scale_factor=2)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
        else:
            nav = play.chromium.launch()
            ctx = nav.new_context(viewport={"width": 1440, "height": 900},
                                  device_scale_factor=2)
            page = ctx.new_page()
        ctx.route("**/*", _solo_lectura)
        page.goto(url.rstrip("/") + ruta)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(int(esperar * 1000))
        page.screenshot(path=str(destino))
        ctx.close()
    print(f"✓ {destino}\nSIGUIENTE: refiérela en manual.md con ![descripción](img/{nombre}.png)")
    return 0


ESCRITURA = {"POST", "PUT", "PATCH", "DELETE"}


def _solo_lectura(route) -> None:
    """Bloquea cualquier petición que modifique datos del cliente."""
    if route.request.method.upper() in ESCRITURA:
        print(f"  ⛔ bloqueado {route.request.method} {route.request.url}")
        route.abort()
    else:
        route.continue_()


def _css(marca: dict) -> str:
    """Hoja de estilo del PDF, con los colores de la marca."""
    return f"""
@page {{ margin: 16mm 14mm; }}
body {{ font-family:{marca['font']}; color:{marca['ink']}; line-height:1.55;
  max-width:820px; margin:auto; font-size:11.5pt; }}
h1 {{ color:{marca['primary']}; font-size:26pt; margin:0 0 4pt; }}
h1 + p {{ color:{marca['muted']}; margin-top:0; }}
h2 {{ color:{marca['ink']}; font-size:17pt; margin:26pt 0 8pt;
  border-bottom:2px solid {marca['primary']}; padding-bottom:4pt; page-break-after:avoid; }}
h3 {{ color:{marca['primary']}; font-size:13pt; margin:16pt 0 6pt; page-break-after:avoid; }}
img {{ max-width:100%; border:1px solid {marca['muted']}40; border-radius:6px;
  margin:8pt 0; page-break-inside:avoid; }}
table {{ border-collapse:collapse; width:100%; margin:8pt 0; font-size:10.5pt;
  page-break-inside:avoid; }}
th {{ background:{marca['canvas']}; text-align:left; }}
td, th {{ border:1px solid {marca['muted']}55; padding:5pt 7pt; vertical-align:top; }}
blockquote {{ background:{marca['primary']}0F; border-left:4px solid {marca['primary']};
  margin:10pt 0; padding:7pt 12pt; page-break-inside:avoid; }}
blockquote p {{ margin:0; }}
code {{ background:{marca['canvas']}; padding:1pt 4pt; border-radius:3px; font-size:10pt; }}
ol, ul {{ padding-left:20pt; }}
li {{ margin:3pt 0; }}
"""


def cmd_pdf(salida: str) -> int:
    """manual.md → HTML con la marca → PDF A4."""
    try:
        import markdown  # pylint: disable=import-outside-toplevel
        from playwright.sync_api import sync_playwright  # pylint: disable=import-outside-toplevel
    except ImportError as exc:
        sys.exit(f"✗ falta una dependencia ({exc.name}): pip install markdown playwright")
    if not FUENTE.exists():
        sys.exit(f"✗ no existe {FUENTE}: corre `./ml init`")
    cuerpo = markdown.markdown(FUENTE.read_text(encoding="utf-8"),
                               extensions=["tables", "fenced_code", "attr_list"])
    html = Path(salida).with_suffix(".html")
    html.write_text(f"<!doctype html><html lang='es'><head><meta charset='utf-8'>"
                    f"<style>{_css(_marca())}</style></head><body>{cuerpo}</body></html>",
                    encoding="utf-8")
    with sync_playwright() as play:
        nav = play.chromium.launch()
        page = nav.new_page()
        page.goto(html.resolve().as_uri())
        page.wait_for_load_state("networkidle")
        page.pdf(path=salida, format="A4", print_background=True)
        nav.close()
    tam = Path(salida).stat().st_size / 2**20
    print(f"✓ {salida} ({tam:.1f} MB) · HTML intermedio: {html}")
    return 0


MARCADORES = re.compile(r"<[A-ZÁÉÍÓÚÑ][^>]{2,}>|TODO|FIXME")


def cmd_check() -> int:
    """Avisos objetivos: imágenes que faltan, marcadores sin llenar y el propósito ausente."""
    if not FUENTE.exists():
        sys.exit(f"✗ no existe {FUENTE}: corre `./ml init`")
    md = FUENTE.read_text(encoding="utf-8")
    issues = [f"imagen referenciada que no existe: {rel}"
              for rel in sorted(set(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", md)))
              if not Path(rel).exists()]
    pendientes = sorted(set(MARCADORES.findall(md)))
    if pendientes:
        issues.append(f"marcadores sin llenar: {', '.join(pendientes[:6])}")
    titulos = re.findall(r"^## (\d+)\.", md, re.MULTILINE)
    if titulos and [int(n) for n in titulos] != list(range(1, len(titulos) + 1)):
        issues.append(f"secciones numeradas fuera de orden: {', '.join(titulos)}")
    # El manual tiene que decir para qué sirve cada cosa, no solo qué es: es su razón de ser.
    cabeceras = re.findall(r"^\|(.+)\|\s*$", md, re.MULTILINE)
    conceptos = [h for h in cabeceras if re.search(r"concepto|catálogo|campo", h, re.I)]
    sin_proposito = [h.strip() for h in conceptos
                     if not re.search(r"para qué|por qué|sirve|importa", h, re.I)]
    if sin_proposito:
        issues.append("tabla de conceptos sin columna de propósito (\"Para qué sirve\" / "
                      f"\"Por qué importa\"): |{sin_proposito[0]}|")
    if not re.search(r"^## .*(organiza|orden de trabajo|cómo funciona)", md,
                     re.MULTILINE | re.IGNORECASE):
        issues.append("falta la sección que explica cómo está organizado el sistema y en qué "
                      "orden se usan las pantallas (es la que evita la mayoría de los errores)")
    for issue in issues:
        print(f"  ⚠ {issue}")
    print("✅ sin avisos" if not issues else f"✗ {len(issues)} aviso(s)")
    return 1 if issues else 0


def main() -> int:
    """Punto de entrada."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    ini = sub.add_parser("init")
    ini.add_argument("--desde", default="", help="proyecto de video-web del que copiar")
    ini.add_argument("--titulo", default="")
    pan = sub.add_parser("pantalla")
    pan.add_argument("--url", required=True)
    pan.add_argument("--ruta", default="/")
    pan.add_argument("--nombre", required=True)
    pan.add_argument("--perfil", default="", help="perfil de Chrome con la sesión abierta")
    pan.add_argument("--esperar", type=float, default=2.0)
    pdf = sub.add_parser("pdf")
    pdf.add_argument("--salida", default="manual.pdf")
    sub.add_parser("check")
    args = parser.parse_args()
    if args.cmd == "init":
        return cmd_init(args.desde, args.titulo)
    if args.cmd == "pantalla":
        return cmd_pantalla(args.url, args.ruta, args.nombre, args.perfil, args.esperar)
    if args.cmd == "pdf":
        return cmd_pdf(args.salida)
    return cmd_check()


if __name__ == "__main__":
    sys.exit(main())
