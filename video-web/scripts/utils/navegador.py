"""Helpers de Playwright para capturar apps en SOLO LECTURA.

- `Guard` bloquea en la red toda escritura (POST/PUT/PATCH/DELETE) salvo las permitidas.
- `run_steps` solo admite acciones de lectura y rechaza botones de acción (lista negra).
- `goto_clean` reintenta mientras la página muestre marcadores de error o throttling.
Sin lógica de negocio: todo lo específico del producto llega en la configuración.
"""
import re
import time
from urllib.parse import quote, urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeout  # pylint: disable=import-error

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SAFE_KEYS = {"Escape", "Tab", "ArrowDown", "ArrowUp", "PageDown", "PageUp"}
# Sube desde el elemento más interno cuyo texto propio (o placeholder) empieza por `text`
# hasta el primer ancestro de al menos minW×minH CSS px: la tarjeta o fila que lo contiene.
CONTAINER_JS = """([text, minW, minH, nth]) => {
  const hits = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
  while (walker.nextNode()) {
    const el = walker.currentNode;
    const own = Array.from(el.childNodes).filter(n => n.nodeType === 3)
      .map(n => n.textContent).join('').trim();
    const label = own || (el.getAttribute('placeholder') || '');
    if (label.startsWith(text) && el.getBoundingClientRect().width > 0) hits.push(el);
  }
  let el = hits[nth || 0];
  if (!el) return null;
  let r = el.getBoundingClientRect();
  while (el.parentElement && (r.width < minW || r.height < minH)) {
    el = el.parentElement; r = el.getBoundingClientRect();
  }
  return [r.x, r.y, r.width, r.height];
}"""
CSS_VARS_JS = """() => {
  const vars = {};
  for (const sheet of Array.from(document.styleSheets)) {
    let rules; try { rules = sheet.cssRules; } catch (e) { continue; }
    for (const r of Array.from(rules || [])) {
      if (r.selectorText && /:root|\\[data-theme/.test(r.selectorText) && r.style) {
        for (let i = 0; i < r.style.length; i++) {
          const p = r.style[i];
          if (p.startsWith('--')) vars[r.selectorText + ' ' + p] = r.style.getPropertyValue(p).trim();
        }
      }
    }
  }
  const cs = s => { const e = document.querySelector(s); return e ? getComputedStyle(e) : null; };
  return { vars, body_font: cs('body') && cs('body').fontFamily,
           heading_font: cs('h1, h2') && cs('h1, h2').fontFamily,
           body_bg: cs('body') && cs('body').backgroundColor,
           // sin variables CSS (sitios viejos) la marca se lee de elementos típicos
           computed: Object.fromEntries([
             ['fondo', 'body', 'backgroundColor'], ['texto', 'body', 'color'],
             ['título', 'h1, h2', 'color'], ['enlace', 'a[href]', 'color'],
             ['botón fondo', 'button, .btn, [role=button]', 'backgroundColor'],
             ['botón texto', 'button, .btn, [role=button]', 'color'],
             ['encabezado', 'header, nav, .navbar', 'backgroundColor']]
             .map(([k, s, p]) => [k, cs(s) && cs(s)[p]]).filter(([, v]) => v)),
           images: Array.from(document.images).map(i => i.currentSrc || i.src) };
}"""


def dotenv(path) -> dict:
    """Variables KEY=valor de un .env (sin comillas ni export); {} si no existe."""
    if not path.exists():
        return {}
    pairs = (line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines()
             if "=" in line and not line.lstrip().startswith("#"))
    return {k.strip().removeprefix("export ").strip(): v.strip().strip("'\"") for k, v in pairs}


def fonts_url(fonts: list[dict]) -> str:
    """URL de Google Fonts CSS2 para las familias y pesos pedidos."""
    fams = "&".join(f"family={quote(f['family'])}:wght@{';'.join(map(str, f['weights']))}"
                    for f in fonts)
    return f"https://fonts.googleapis.com/css2?{fams}&display=swap"


def font_init_script(fonts: list[dict]) -> str:
    """Script de inicio que inyecta las fuentes de marca en cada documento."""
    if not fonts:
        return ""
    return ("document.addEventListener('DOMContentLoaded', () => {"
            " const l = document.createElement('link'); l.rel = 'stylesheet';"
            f" l.href = '{fonts_url(fonts)}'; document.head.appendChild(l); }});")


# GET que en muchas apps cambian estado (enlaces de acción, cierre de sesión)
GET_DENY = (r"/(log-?out|sign-?out|salir|cerrar-?sesion|delete|remove|destroy|eliminar|"
            r"borrar|approve|aprobar|reject|rechazar|cancel|cancelar|unsubscribe|confirm|"
            r"confirmar|activate|activar|deactivate|desactivar)(?=[/?._-]|$)")


def allowed_path(url: str, allow: list[str]) -> bool:
    """Ruta exacta de la lista, o prefijo si el patrón termina en '*'."""
    path = urlparse(url).path
    return any(path.startswith(p[:-1]) if p.endswith("*")
               else path.rstrip("/") == p.rstrip("/") for p in allow)


class Guard:
    """Bloqueo de escrituras en la red con registro de todo lo que intentó escribir.

    Bloquea POST/PUT/PATCH/DELETE fuera de `allow`, GET a rutas de acción (GET_DENY) y, salvo
    que se permitan, los WebSockets (pueden enviar comandos que la red no ve como escrituras).
    """

    def __init__(self, allow: list[str], log_path, get_deny: str = GET_DENY):
        self.allow = allow
        self.log_path = log_path
        self.get_deny = re.compile(get_deny, re.IGNORECASE) if get_deny else None
        self.blocked: list[str] = []

    def _log(self, verdict: str, what: str) -> None:
        with open(self.log_path, "a", encoding="utf-8") as log:
            log.write(f"{time.strftime('%H:%M:%S')} {verdict} {what}\n")

    def verdict(self, method: str, url: str) -> str | None:
        """'PERMITIDO', 'BLOQUEADO' o None (lectura normal que no se registra)."""
        if method in WRITE_METHODS:
            return "PERMITIDO" if allowed_path(url, self.allow) else "BLOQUEADO"
        if self.get_deny and self.get_deny.search(urlparse(url).path):
            return "BLOQUEADO"
        return None

    def handle(self, route, request) -> None:
        """Handler de context.route: aborta escrituras y GET de acción no permitidos."""
        verdict = self.verdict(request.method, request.url)
        if verdict:
            self._log(verdict, f"{request.method} {request.url}")
        if verdict == "BLOQUEADO":
            self.blocked.append(f"{request.method} {request.url}")
            route.abort()
            return
        route.continue_()

    def handle_ws(self, ws) -> None:
        """Handler de context.route_web_socket: no conecta al servidor (el socket queda mudo)."""
        self._log("BLOQUEADO", f"WS {ws.url}")
        self.blocked.append(f"WS {ws.url}")

    def report(self) -> dict:
        """Escrituras bloqueadas durante la sesión."""
        return {"blocked": list(self.blocked)}


def settle(page, fonts: list[dict], pause_s: float) -> None:
    """Espera red inactiva, carga de fuentes y un margen para animaciones de entrada."""
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except PlaywrightTimeout:
        pass
    loads = ", ".join(f"document.fonts.load('{max(f['weights'])} 20px \"{f['family']}\"')"
                      for f in fonts)
    page.evaluate(f"Promise.all([{loads}]).then(() => document.fonts.ready)")
    time.sleep(pause_s)


def error_text(page, markers: list[str]) -> str | None:
    """Primer marcador de error visible en la página, o None."""
    body = page.inner_text("body")
    return next((m for m in markers if m in body), None)


def check_denied(text: str, deny: str) -> None:
    """Rechaza (ValueError) un control cuyo texto parece una acción que modifica datos."""
    if deny and re.search(deny, text or "", re.IGNORECASE):
        raise ValueError(f"acción bloqueada por la lista negra: '{text}'")


def _locate(page, text: str, timeout_s: float = 15):
    """Control con ese nombre accesible; espera a que aparezca (listas que cargan tarde)."""
    by_role = page.get_by_role("button", name=text)
    for role in ("tab", "link", "menuitem"):
        by_role = by_role.or_(page.get_by_role(role, name=text))
    try:
        by_role.first.wait_for(state="visible", timeout=timeout_s * 1000)
        return by_role.first
    except PlaywrightTimeout:
        return page.get_by_text(text).first


CLICK_TIMEOUT_MS = 8000  # un selector inexistente falla en 8s, no en los 30s por defecto


def run_steps(page, steps: list[dict], deny: str) -> None:
    """Ejecuta pasos de solo lectura: click, click_css, fill, type, hover, key, wait."""
    for step in steps:
        if "click" in step:
            check_denied(step["click"], deny)
            _locate(page, step["click"]).click(timeout=CLICK_TIMEOUT_MS)
        elif "click_css" in step:
            loc = page.locator(step["click_css"]).first
            check_denied(loc.inner_text(), deny)
            loc.click(timeout=CLICK_TIMEOUT_MS)
        elif "fill" in step:
            label = step["fill"]
            loc = page.get_by_placeholder(label)
            if not loc.count():
                loc = page.get_by_role("searchbox", name=label)
            if not loc.count():
                loc = page.get_by_role("textbox", name=label)
            loc.first.fill(str(step["value"]))
        elif "type" in step:
            page.keyboard.type(str(step["type"]), delay=60)
        elif "hover" in step:
            _locate(page, step["hover"]).hover()
        elif "key" in step:
            if step["key"] not in SAFE_KEYS:
                raise ValueError(f"tecla no permitida en captura: {step['key']}")
            page.keyboard.press(step["key"])
        elif "wait" in step:
            time.sleep(float(step["wait"]))
        else:
            raise ValueError(f"paso no reconocido: {step}")
        time.sleep(float(step.get("pause", 1.5)))


def rect(page, spec: dict, origin=(0.0, 0.0), scale: float = 2.0) -> list[int] | None:
    """[x, y, w, h] en px de imagen del contenedor de `spec['text']`, relativo a origin."""
    if "css" in spec:
        box = page.locator(spec["css"]).first.bounding_box()
        found = [box["x"], box["y"], box["width"], box["height"]] if box else None
    else:
        size = spec.get("min", [0, 0])
        found = page.evaluate(CONTAINER_JS, [spec["text"], size[0], size[1], spec.get("nth", 0)])
    if not found:
        return None
    x, y, w, h = found
    return [round((x - origin[0]) * scale), round((y - origin[1]) * scale),
            round(w * scale), round(h * scale)]
