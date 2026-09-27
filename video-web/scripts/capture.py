"""Captura de la app web para el video, en SOLO LECTURA, según capture.json.

    capture.py explorar --route /ruta [--auth] [--steps '[{"click": "Texto"}]']
    capture.py run [--only nombre1,nombre2]
    capture.py crop --src ARCHIVO --name NOMBRE --desc "..." [--card | --box x,y,w,h]

`run` produce capturas a 2x en capture/assets/, rectángulos medidos por DOM en
capture/extracted/ui-regions.json, descripciones en asset-descriptions.md, hojas de contacto
en capture/review/ y capture/extracted/capture-report.json (lo revisa `./vl check captura`).
"""
import argparse
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image  # pylint: disable=import-error
from playwright.sync_api import Error as PlaywrightError  # pylint: disable=import-error
from playwright.sync_api import TimeoutError as PlaywrightTimeout  # pylint: disable=import-error
from playwright.sync_api import sync_playwright  # pylint: disable=import-error

from utils import imagenes, navegador as nav  # pylint: disable=import-error

ASSETS = Path("capture/assets")
EXTRACTED = Path("capture/extracted")
REVIEW = Path("capture/review")
INDEX, REGIONS = EXTRACTED / "capture-index.json", EXTRACTED / "ui-regions.json"
DEFAULTS = {
    "viewport": [1440, 900], "scale": 2, "locale": "es-CO", "timezone": "America/Bogota",
    "pause_s": 5, "retry_wait_s": 40, "tries": 5, "fonts": [], "allow_mutations": [],
    "error_markers": ["No fue posible", "throttled", "regulada", "Error 500", "Not Found"],
    # Verbos de acción al inicio de palabra; los ingleses cortos, como palabra completa
    # (si no, "pay" bloquea "Ver payload").
    "deny": (r"\b(guardar|crear|enviar|eliminar|borrar|aprobar|rechazar|pagar|activar|"
             r"desactivar|firmar|confirmar|ejecutar|generar|subir|cancelar|solicitar|"
             r"agregar|convertir|reenviar|aceptar|iniciar|registrar|simular|reintentar|"
             r"cerrar sesión)|\b(save|delete|submit|send|approve|reject|pay|confirm|remove|add|"
             r"create|edit|update|upload|buy|purchase|checkout|basket|cart|log ?out|"
             r"sign ?out|archive|invite|trash)\b"),
}
BLANK_STD = 6.0


def load_json(path: Path, default):
    """Lee JSON o devuelve el valor por defecto si el archivo no existe."""
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def load_cfg() -> dict:
    """capture.json con valores por defecto."""
    cfg = load_json(Path("capture.json"), None)
    if cfg is None:
        sys.exit("✗ falta capture.json en el proyecto (plantilla en assets/templates/)")
    return {**DEFAULTS, **cfg}


class Capturer:
    """Sesiones de navegador (pública y autenticada) con bloqueo de escrituras."""

    def __init__(self, cfg: dict, playwright):
        self.cfg = cfg
        self.browser = playwright.chromium.launch()
        self.guard = nav.Guard(cfg["allow_mutations"], EXTRACTED / "requests.log",
                               cfg.get("deny_get", nav.GET_DENY))
        self.pages: dict[bool, object] = {}
        self.css_dumped = False

    def page(self, auth: bool):
        """Página de la sesión pedida (se crea y, si hace falta, inicia sesión)."""
        if auth not in self.pages:
            width, height = self.cfg["viewport"]
            ctx = self.browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=self.cfg["scale"], locale=self.cfg["locale"],
                timezone_id=self.cfg["timezone"])
            ctx.route("**/*", self.guard.handle)
            if not self.cfg.get("websocket"):
                ctx.route_web_socket("**/*", self.guard.handle_ws)
            if self.cfg["fonts"]:
                ctx.add_init_script(nav.font_init_script(self.cfg["fonts"]))
            self.pages[auth] = ctx.new_page()
            if auth:
                self._login(self.pages[auth])
        return self.pages[auth]

    def _login(self, page) -> None:
        login = self.cfg.get("login")
        if not login:
            sys.exit("✗ una captura pide auth pero capture.json no tiene 'login'")
        env = {**nav.dotenv(Path(".env")), **os.environ}  # la variable del comando manda
        user, password = env.get(login["user_env"]), env.get(login["pass_env"])
        if not user or not password:
            sys.exit(f"✗ define {login['user_env']} y {login['pass_env']} en el comando o en "
                     "un .env del proyecto (ignorado por git); nunca en capture.json ni notas")
        page.goto(self.cfg["base_url"] + login.get("route", "/"))
        self.settle(page, 2)
        for label, value in zip(login["fields"], (user, password)):
            field = page.get_by_role("textbox", name=label)
            (field if field.count() else page.get_by_label(label)).first.fill(value)
        page.get_by_role("button", name=login["submit"]).first.click()
        page.wait_for_url(login["wait_url"], timeout=30000)
        self.settle(page)

    def settle(self, page, pause: float | None = None) -> None:
        """Red inactiva + fuentes + pausa."""
        nav.settle(page, self.cfg["fonts"], self.cfg["pause_s"] if pause is None else pause)

    def open_state(self, page, shot: dict) -> None:
        """Navega y ejecuta los pasos; reintenta mientras haya errores o throttling."""
        route = shot.get("route", "/")
        url = route if route.startswith(("http://", "https://")) else self.cfg["base_url"] + route
        if "<" in url:
            sys.exit("✗ llena base_url en capture.json, o pasa la URL completa "
                     "(./vl explorar https://…)")
        width, height = self.cfg["viewport"]
        page.set_viewport_size({"width": width, "height": height})
        for attempt in range(1, self.cfg["tries"] + 1):
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
            except PlaywrightTimeout:
                print(f"  ! {shot['name']}: la página no respondió (intento {attempt})")
                time.sleep(10)
                continue
            self.settle(page)
            try:
                nav.run_steps(page, shot.get("steps", []), self.cfg["deny"])
                self.settle(page, 2)
                problem = nav.error_text(page, self.cfg["error_markers"])
            except PlaywrightTimeout as exc:
                # Un paso sin control suele ser un selector equivocado (no throttling): no
                # insistas 5×40s. Reintenta un par de veces por si el SPA cargó tarde, luego falla
                # con el texto del paso para que se corrija capture.json.
                step_fail = str(exc).splitlines()[0]
                if attempt >= 2:
                    raise RuntimeError(f"{shot['name']}: un paso no encontró su control tras "
                                       f"{attempt} intentos ({step_fail}). Revisa 'steps' con "
                                       "`./vl explorar` — el texto o la ruta no coinciden.") \
                        from exc
                print(f"  ! {shot['name']}: paso sin respuesta ({step_fail}); reintento…",
                      flush=True)
                time.sleep(6)
                continue
            if not problem:
                return
            print(f"  ! {shot['name']}: '{problem}' (intento {attempt}); espero…", flush=True)
            time.sleep(self.cfg["retry_wait_s"])
        raise RuntimeError(f"{shot['name']} sigue mostrando error tras {self.cfg['tries']} "
                           "intentos")

    def dump_css(self, page) -> None:
        """Variables CSS, fuentes e imágenes de la app (insumo de `./vl marca`)."""
        if not self.css_dumped:
            data = page.evaluate(nav.CSS_VARS_JS)
            (EXTRACTED / "css-vars.json").write_text(json.dumps(data, ensure_ascii=False,
                                                                indent=2), encoding="utf-8")
            self.css_dumped = True


class Collector:
    """Acumula imágenes, regiones y descripciones producidas en la corrida."""

    def __init__(self):
        self.index = load_json(INDEX, {})
        self.regions = load_json(REGIONS, {})
        self.files: list[str] = []
        self.region_issues: list[str] = []

    def add(self, name: str, desc: str, rects: dict | None = None) -> None:
        """Registra una imagen con su tamaño, descripción y rectángulos."""
        with Image.open(ASSETS / name) as img:
            size = list(img.size)
        self.index[name] = {"desc": desc, "size": size}
        if rects:
            self.regions[name] = {"size": size, "rects": {k: v for k, v in rects.items() if v}}
            missing = [k for k, v in rects.items() if not v]
            # un ancestro que desborda la imagen o la cubre casi entera no marca nada útil:
            # baja `min` o usa `css`
            huge = [k for k, v in rects.items() if v and (
                v[0] < 0 or v[1] < 0 or v[0] + v[2] > size[0] + 2 or v[1] + v[3] > size[1] + 2
                or v[2] * v[3] > 0.6 * size[0] * size[1])]
            issues = [f"{name}: región no encontrada '{k}'" for k in missing]
            issues += [f"{name}: región '{k}' {rects[k]} desborda o cubre casi toda la imagen "
                       "(baja min o usa css)" for k in huge]
            for issue in issues:
                print(f"  ! {issue}")
            self.region_issues += issues
        self.files.append(name)
        print(f"  ✓ {name} {size[0]}x{size[1]}", flush=True)

    def save(self) -> None:
        """Escribe índice, regiones, tabla legible y sección de asset-descriptions.md."""
        INDEX.write_text(json.dumps(self.index, ensure_ascii=False, indent=2), encoding="utf-8")
        REGIONS.write_text(json.dumps(self.regions, ensure_ascii=False, indent=2),
                           encoding="utf-8")
        rows = ["| imagen | región | [x,y,w,h] |", "|---|---|---|"]
        rows += [f"| {img} | {k} | {v} |" for img, info in sorted(self.regions.items())
                 for k, v in info["rects"].items()]
        (EXTRACTED / "regions.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
        lines = [f"- {n} — {i['desc']} ({i['size'][0]}x{i['size'][1]})"
                 for n, i in sorted(self.index.items())]
        section = ("<!-- vl:capturas:inicio -->\n## Capturas (generado por `./vl captura`)\n\n"
                   + "\n".join(lines) + "\n<!-- vl:capturas:fin -->")
        desc_path = EXTRACTED / "asset-descriptions.md"
        text = desc_path.read_text(encoding="utf-8") if desc_path.exists() else ""
        pattern = re.compile(r"<!-- vl:capturas:inicio -->.*<!-- vl:capturas:fin -->", re.DOTALL)
        text = pattern.sub(section, text) if pattern.search(text) else text + "\n\n" + section
        desc_path.write_text(text.strip() + "\n", encoding="utf-8")


def measure(page, specs: dict, origin, scale) -> dict:
    """Rectángulos de un conjunto de specs {clave: {text|css, min, nth}}."""
    return {key: nav.rect(page, spec, origin, scale) for key, spec in specs.items()}


def take_crops(page, shot: dict, cap: Capturer, col: Collector) -> None:
    """Recortes de elementos (tarjetas, secciones) con sus propias regiones."""
    scale = cap.cfg["scale"]
    for spec in shot.get("crops", []):
        if spec.get("container"):
            box = page.locator(spec["container"]).filter(has_text=spec["text"]).nth(
                spec.get("nth", 0)).bounding_box()
            found = [box["x"], box["y"], box["width"], box["height"]] if box else None
        else:
            size = spec.get("min", [0, 0])
            found = page.evaluate(nav.CONTAINER_JS, [spec["text"], size[0], size[1],
                                                     spec.get("nth", 0)])
        if not found:
            raise RuntimeError(f"recorte {spec['name']}: no encontré '{spec['text']}'")
        pad = spec.get("pad", 0)
        clip = {"x": max(found[0] - pad, 0), "y": max(found[1] - pad, 0),
                "width": found[2] + 2 * pad, "height": found[3] + 2 * pad}
        name = f"{spec['name']}.png"
        page.screenshot(path=str(ASSETS / name), clip=clip)
        rects = measure(page, spec.get("regions", {}), (clip["x"], clip["y"]), scale)
        col.add(name, spec.get("desc", f"recorte de {shot['name']}: {spec['text']}"), rects)


def shoot_modal(page, shot: dict, cap: Capturer, col: Collector) -> None:
    """Modal: vista en contexto + contenido completo sin scroll + recortes internos."""
    modal = page.locator(cap.cfg["modal"]).first
    modal.wait_for(state="visible", timeout=20000)
    cap.settle(page, 2)
    page.screenshot(path=str(ASSETS / f"{shot['name']}-vista.png"))
    col.add(f"{shot['name']}-vista.png", f"{shot.get('desc', '')} (en contexto)")
    width, height = cap.cfg["viewport"]
    extra = 400
    for _ in range(4):
        need = modal.evaluate("el => el.scrollHeight")
        page.set_viewport_size({"width": width, "height": need + extra})
        cap.settle(page, 1.5)
        if modal.evaluate("el => el.scrollHeight <= el.clientHeight + 2"):
            break
        extra *= 2
    modal.screenshot(path=str(ASSETS / f"{shot['name']}.png"))
    box = modal.bounding_box()
    rects = measure(page, shot.get("regions", {}), (box["x"], box["y"]), cap.cfg["scale"])
    col.add(f"{shot['name']}.png", f"{shot.get('desc', '')} (contenido completo)", rects)
    take_crops(page, shot, cap, col)
    page.set_viewport_size({"width": width, "height": height})


def shoot(shot: dict, cap: Capturer, col: Collector) -> None:
    """Una captura completa: estado, imagen principal, regiones, recortes y pasos 'after'."""
    page = cap.page(shot.get("auth", "login" in cap.cfg))  # sin login → sin sesión
    cap.open_state(page, shot)
    cap.dump_css(page)
    target = shot.get("target", "viewport")
    if target == "modal":
        shoot_modal(page, shot, cap, col)
    else:
        name = f"{shot['name']}.png"
        page.screenshot(path=str(ASSETS / name), full_page=target == "full")
        rects = measure(page, shot.get("regions", {}), (0, 0), cap.cfg["scale"])
        col.add(name, shot.get("desc", shot["name"]), rects)
        take_crops(page, shot, cap, col)
    nav.run_steps(page, shot.get("after", []), cap.cfg["deny"])


def fetch_brand(cap: Capturer, col: Collector) -> None:
    """Descarga logos/mascota de la app y crea variantes blancas si se piden."""
    page = cap.page(False)
    for item in cap.cfg.get("brand_assets", []):
        resp = page.request.get(cap.cfg["base_url"] + item["url"])
        ctype = resp.headers.get("content-type", "")
        # Una SPA responde su index.html a rutas desconocidas (200 pero HTML), no un 404:
        # confía en el content-type, no en resp.ok, o el logo baja como página web.
        if not resp.ok or not ctype.startswith(("image/", "application/octet-stream")):
            raise RuntimeError(f"{item['url']} no devolvió una imagen ({resp.status}, "
                               f"{ctype or 'sin tipo'}): revisa la URL del brand_asset")
        name = f"{item['name']}{Path(item['url']).suffix}"
        (ASSETS / name).write_bytes(resp.body())
        col.add(name, item.get("desc", item["name"]))
        if item.get("white"):
            white = f"{item['name']}-blanco.png"
            imagenes.white_variant(ASSETS / name, ASSETS / white)
            col.add(white, f"{item.get('desc', item['name'])} en blanco (fondos oscuros)")


def cmd_run(only: set[str]) -> int:
    """Corre las capturas de capture.json (o solo las indicadas)."""
    cfg = load_cfg()
    for folder in (ASSETS, EXTRACTED, REVIEW):
        folder.mkdir(parents=True, exist_ok=True)
    col, failed = Collector(), []
    with sync_playwright() as playwright:
        cap = Capturer(cfg, playwright)
        if not only:
            fetch_brand(cap, col)
        for shot in cfg["shots"]:
            if only and shot["name"] not in only:
                continue
            print(f"[{shot['name']}]", flush=True)
            try:
                shoot(shot, cap, col)
            except (RuntimeError, ValueError, PlaywrightError) as exc:
                print(f"  ✗ {exc}", flush=True)
                failed.append(f"{shot['name']}: {exc}")
            col.save()  # índice al día aunque la corrida se interrumpa
        cap.browser.close()
    col.save()
    # Una corrida parcial (--only) conserva los fallos de las tomas que no volvió a correr.
    previous = load_json(EXTRACTED / "capture-report.json", {}).get("failed", [])
    failed += [f for f in previous if only and f.split(":")[0] not in only]
    files = sorted(col.index)
    blank = [n for n in files if imagenes.gray_std(ASSETS / n) < BLANK_STD]
    report = {"files": files, "run": col.files, "failed": failed,
              "blocked": cap.guard.report()["blocked"], "blank": blank,
              "regions": col.region_issues}
    (EXTRACTED / "capture-report.json").write_text(json.dumps(report, ensure_ascii=False,
                                                             indent=2), encoding="utf-8")
    sheets = imagenes.contact_sheets([ASSETS / n for n in files], REVIEW / "capturas")
    print(f"\nHojas de contacto: {', '.join(str(s) for s in sheets)}")
    print(f"Fallidas: {len(failed)} · escrituras bloqueadas: {len(report['blocked'])} · "
          f"vacías: {len(blank)}")
    print("SIGUIENTE: abre y mira cada hoja de contacto; repite con `--only` las tomas que "
          "fallen")
    return 1 if failed or report["blocked"] or blank else 0


EXPLORE_JS = """() => {
  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  // botones de solo icono (papelera, lápiz): la clase del icono es su único "texto"
  const icon = el => { const i = el.querySelector('i,svg'); if (!i) return '';
    const c = i.getAttribute('class') || ''; return c ? 'icono ' + c : ''; };
  const txt = el => (el.innerText || el.value || el.getAttribute('aria-label')
    || el.getAttribute('title') || el.getAttribute('placeholder') || icon(el) || '')
    .trim().replace(/\\s+/g, ' ').slice(0, 80);
  const q = s => Array.from(document.querySelectorAll(s)).filter(vis);
  return { title: document.title, headings: q('h1,h2,h3').map(txt).slice(0, 30),
    controls: q('button,[role=button],[role=tab],a[href],input[type=submit],input[type=button]').map(el => ({
      tag: el.tagName.toLowerCase(), role: el.getAttribute('role') || '', text: txt(el)
    })).filter(c => c.text).slice(0, 150),
    inputs: q('input,select,textarea').map(el => ({ type: el.type || el.tagName.toLowerCase(),
      placeholder: el.placeholder || '', text: txt(el) })).slice(0, 60) };
}"""


def explore_error(route: str, first: str, blocked: list[str]) -> str:
    """Mensaje corto de por qué falló explorar (ruta bloqueada o paso sin control)."""
    hint = ("la ruta está bloqueada por solo lectura (GET de acción)"
            if any(b.split(" ", 1)[1] in first for b in blocked) else
            "revisa el texto exacto de cada paso (sin --steps, explorar lista los controles "
            "de la pantalla)")
    return f"✗ explorar {route}: {first}\n  {hint}."


def cmd_explorar(route: str, auth: bool, steps: list[dict]) -> int:
    """Lista controles y textos de una pantalla (solo lectura) para escribir capture.json."""
    cfg = load_cfg()
    for folder in (EXTRACTED, REVIEW):
        folder.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", urlparse(route).path.lower()).strip("-") or "inicio"
    with sync_playwright() as playwright:
        cap = Capturer(cfg, playwright)
        page = cap.page(auth)
        try:
            cap.open_state(page, {"name": slug, "route": route, "steps": steps})
        except (PlaywrightError, ValueError, RuntimeError) as exc:
            cap.browser.close()
            sys.exit(explore_error(route, str(exc).splitlines()[0], cap.guard.blocked))
        data = page.evaluate(EXPLORE_JS)
        page.screenshot(path=str(REVIEW / f"explorar-{slug}.png"))
        cap.browser.close()
    deny = re.compile(cfg["deny"], re.IGNORECASE)
    lines = [f"# Explorar {route} — {data['title']}", "", "## Títulos",
             *[f"- {h}" for h in data["headings"]], "", "## Controles (⛔ = bloqueado)"]
    lines += [f"- {'⛔ ' if deny.search(c['text']) else ''}{c['role'] or c['tag']}: "
              f"\"{c['text']}\"" for c in data["controls"]]
    lines += ["", "## Campos"] + [f"- {i['type']}: \"{i['placeholder'] or i['text']}\""
                                   for i in data["inputs"]]
    text = "\n".join(lines)
    (EXTRACTED / f"explorar-{slug}.md").write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nCaptura de referencia: {REVIEW / f'explorar-{slug}.png'}")
    return 0


def cmd_crop(src: Path, name: str, desc: str, card: bool, box: str | None) -> int:
    """Copia o recorta una imagen estática (p. ej. capturas del manual) a capture/assets."""
    ASSETS.mkdir(parents=True, exist_ok=True)
    EXTRACTED.mkdir(parents=True, exist_ok=True)
    out = ASSETS / f"{name}.png"
    if card or box:
        bounds = imagenes.card_box(src) if card else tuple(int(v) for v in box.split(","))
        if box:
            bounds = (bounds[0], bounds[1], bounds[0] + bounds[2], bounds[1] + bounds[3])
        with Image.open(src) as img:
            img.crop(bounds).save(out)
    else:
        shutil.copyfile(src, out)
    col = Collector()
    col.add(out.name, desc)
    col.save()
    return 0


def main() -> int:
    """Punto de entrada."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    exp = sub.add_parser("explorar")
    exp.add_argument("--route", required=True)
    exp.add_argument("--auth", action="store_true")
    exp.add_argument("--steps", default="[]")
    run = sub.add_parser("run")
    run.add_argument("--only", default="")
    crop = sub.add_parser("crop")
    crop.add_argument("--src", type=Path, required=True)
    crop.add_argument("--name", required=True)
    crop.add_argument("--desc", required=True)
    crop.add_argument("--card", action="store_true")
    crop.add_argument("--box", default=None)
    args = parser.parse_args()
    if args.cmd == "explorar":
        return cmd_explorar(args.route, args.auth, json.loads(args.steps))
    if args.cmd == "run":
        return cmd_run({n for n in args.only.split(",") if n})
    return cmd_crop(args.src, args.name, args.desc, args.card, args.box)


if __name__ == "__main__":
    sys.exit(main())
