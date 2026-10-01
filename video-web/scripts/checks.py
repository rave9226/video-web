"""Revisiones objetivas del proyecto y estado inferido de los archivos. Solo avisan.

Se ejecuta con el directorio del proyecto como cwd (lo hace `vl`):
    checks.py estado                 qué hay hecho y una sugerencia de siguiente paso
    checks.py captura|marca|guion|voz|storyboard|escenas|entrega|todo
    checks.py fNN-slug | NN          revisión estática de una escena

Nada bloquea otros comandos: la lista de avisos dice qué arreglar y el código de salida es 1
si hay alguno (útil para que un worker repita hasta ✅). Los mensajes van en español porque
los lee el modelo que usa la skill.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from utils import colores, imagenes, medios, texto  # pylint: disable=import-error

MAX_WORDS_LINE = 45  # más largo degrada el TTS; mejor dividir la línea
WORDS_PER_S = 2.4
FORBIDDEN_JS = re.compile(r"Math\.random|Date\.now|repeat\s*:\s*-1|yoyo")


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def es_explicativo(proj: Path) -> bool:
    """True si BRIEF.md declara `tipo: explicativo` (video sin app que capturar)."""
    return bool(re.search(r"^tipo:\s*explicativo\b", _read(proj / "BRIEF.md"), re.MULTILINE))


def check_captura(proj: Path) -> list[str]:
    """Reporte de captura sin fallas, sin escrituras bloqueadas ni imágenes en blanco."""
    if es_explicativo(proj):
        return []
    report = _json(proj / "capture/extracted/capture-report.json")
    if report is None:
        return ["no hay capture/extracted/capture-report.json: corre `./vl captura`"]
    issues = [f"captura fallida: {f}" for f in report.get("failed", [])]
    issues += [f"escritura bloqueada (quita el paso que la disparó): {b}"
               for b in report.get("blocked", [])]
    issues += [f"región: {r}" for r in report.get("regions", [])]
    issues += [f"imagen casi vacía (¿pantalla en blanco?): {b}" for b in report.get("blank", [])]
    issues += [f"no existe capture/assets/{n}" for n in report.get("files", [])
               if not (proj / "capture/assets" / n).exists()]
    return issues


def check_marca(proj: Path) -> list[str]:
    """frame.md con los colores básicos, contraste AA del texto y fuentes locales."""
    md = _read(proj / "frame.md")
    if not md:
        return ["no hay frame.md: corre `./vl marca`"]
    colors = dict(re.findall(r'^\s{2}([\w-]+):\s*"(#[0-9A-Fa-f]{6})"', md, re.MULTILINE))
    issues = [f"frame.md: falta el color {k}" for k in ("bg", "text", "text-muted")
              if k not in colors]
    if not issues:
        for key in ("text", "text-muted"):
            ratio = colores.contrast(colors[key], colors["bg"])
            if ratio < 4.5:
                issues.append(f"contraste {key}/bg = {ratio:.2f} (< 4.5): oscurece {key}")
    # Cada clase se mide sobre SU fondo: el chip está sobre su propio tinte, no sobre bg,
    # y ahí el contraste baja. Medirlo contra bg dejaba pasar chips que fallaban AA.
    for clase in ("eyebrow", "chip"):
        regla = re.search(rf"\.PFX-{clase} \{{([^}}]*)\}}", md)
        if not (regla and colors.get("bg")):
            continue
        color = re.search(r"[; ]color:(#[0-9A-Fa-f]{6})", regla.group(1))
        tinte = re.search(r"background:(#[0-9A-Fa-f]{6})([0-9A-Fa-f]{2})", regla.group(1))
        if not color:
            continue
        fondo = (colores.mix(colors["bg"], tinte.group(1), int(tinte.group(2), 16) / 255)
                 if tinte else colors["bg"])
        ratio = colores.contrast(color.group(1), fondo)
        if ratio < 4.5:
            issues.append(f"{clase} {color.group(1)} sobre {fondo} = {ratio:.2f} (< 4.5): "
                          "corre `./vl marca`")
    issues += _tokens_fuera_de_marca(colors)
    issues += [f"fuente declarada sin archivo: {font}" for font in
               re.findall(r'src:url\("(assets/fonts/[^"]+)"\)', md) if not (proj / font).exists()]
    return issues


# Tokens que no comparten el tono del primario a propósito: neutros y semánticos.
TOKENS_LIBRES = {"bg", "text", "text-muted", "text-light", "surface", "positive", "negative",
                 "brand-spark", "border"}
TONO_MAX = 40  # grados de diferencia en el círculo de color antes de avisar


def _tono(hexcol: str) -> float | None:
    """Tono en grados (0-360); None si el color es un gris (sin tono)."""
    r, g, b = (c / 255 for c in colores.rgb(hexcol))
    alto, bajo = max(r, g, b), min(r, g, b)
    if alto - bajo < 0.08:
        return None
    if alto == r:
        return (60 * ((g - b) / (alto - bajo)) + 360) % 360
    if alto == g:
        return 60 * ((b - r) / (alto - bajo)) + 120
    return 60 * ((r - g) / (alto - bajo)) + 240


def _tokens_fuera_de_marca(colors: dict) -> list[str]:
    """Colores con tono ajeno al primario: casi siempre copiados de otro proyecto."""
    base = _tono(colors["primary"]) if colors.get("primary") else None
    if base is None:
        return []
    issues = []
    for key, value in colors.items():
        if key in TOKENS_LIBRES or key == "primary":
            continue
        tono = _tono(value)
        if tono is None:
            continue
        dif = min(abs(tono - base), 360 - abs(tono - base))
        if dif > TONO_MAX:
            issues.append(f"{key} {value} tiene un tono {dif:.0f}° lejos del primario "
                          f"{colors['primary']}: ¿es de la marca o quedó de otro proyecto? "
                          "(references/marca.md)")
    return issues


def check_guion(proj: Path) -> list[str]:
    """Numeración consecutiva y líneas que el TTS pueda leer de un tirón."""
    lines = texto.parse_script(_read(proj / "SCRIPT.md"))
    if not lines:
        return ["SCRIPT.md vacío o sin líneas: el texto hablado va indentado con 4 espacios "
                "bajo cada '## Line N — … (Frame N)'"]
    issues = []
    if sorted(lines) != list(range(1, len(lines) + 1)):
        issues.append(f"frames no consecutivos en SCRIPT.md: {sorted(lines)}")
    for frame, text in lines.items():
        count = len(texto.normalize(text))
        if count > MAX_WORDS_LINE:
            issues.append(f"frame {frame}: {count} palabras (> {MAX_WORDS_LINE}); el TTS "
                          "rinde peor, conviene dividirla")
    words = sum(len(texto.normalize(t)) for t in lines.values())
    segundos = words / WORDS_PER_S
    print(f"ℹ {len(lines)} líneas, {words} palabras ≈ {segundos:.0f} s de voz (más pausas)")
    return issues + _formato(proj, len(lines), segundos)


# Cada formato tiene su arco y su duración (references/oficio.md § Guion).
FORMATOS = {"lanzamiento": (30, 120), "capacitacion": (150, 600), "explicativo": (45, 600)}


def _formato(proj: Path, n_lineas: int, segundos: float) -> list[str]:
    """El guion debe corresponder al formato declarado en el BRIEF."""
    formato = texto.parse_frontmatter(_read(proj / "BRIEF.md")).get("formato", "").strip()
    if not formato:
        return ["BRIEF.md no declara `formato`: capacitacion | lanzamiento | explicativo. "
                "🛑 pregúntaselo al usuario antes de escribir el guion (SKILL.md § Formato)"]
    if formato not in FORMATOS:
        return [f"BRIEF.md → formato '{formato}' no es {' | '.join(FORMATOS)}"]
    minimo, maximo = FORMATOS[formato]
    issues = []
    if segundos < minimo:
        issues.append(f"formato {formato}: {segundos:.0f} s de narración es poco (mínimo "
                      f"~{minimo} s); con menos no alcanza a explicar lo que promete el arco")
    if segundos > maximo:
        issues.append(f"formato {formato}: {segundos:.0f} s es mucho (máximo ~{maximo} s)")
    if formato == "capacitacion" and n_lineas < 10:
        issues.append(f"formato capacitacion: {n_lineas} líneas es poco (mínimo 10); una "
                      "pantalla por función más el modelo y el orden de trabajo")
    return issues


def check_voz(proj: Path) -> list[str]:
    """Cada línea del guion con su voz, WER y P(idioma) dentro de umbral."""
    meta = _json(proj / "audio_meta.json")
    if meta is None:
        return ["no hay audio_meta.json: corre `./vl voz lines`"]
    gates = (_json(proj / "audio.json") or {}).get("gates", {})
    lines = texto.parse_script(_read(proj / "SCRIPT.md"))
    voices = meta.get("voices", [])
    issues = [] if len(voices) == len(lines) else [
        f"voces {len(voices)} ≠ líneas del guion {len(lines)}: `./vl voz lines`"]
    for voice in voices:
        if not (proj / voice["path"]).exists():
            issues.append(f"no existe {voice['path']}")
        if voice.get("wer", 1) > gates.get("max_wer", 0.08):
            issues.append(f"frame {voice['frame']}: WER {voice.get('wer')} alto → respell o "
                          f"`./vl voz lines --frames {voice['frame']}`")
        if voice.get("p_lang", 0) < gates.get("min_p_lang", 0.97):
            issues.append(f"frame {voice['frame']}: P(idioma) {voice.get('p_lang')} bajo")
    return issues


def check_storyboard(proj: Path) -> list[str]:
    """Lo que necesitan los scripts de ensamblado: src fNN-slug, duración y assets reales."""
    text = _read(proj / "STORYBOARD.md")
    if not text:
        return ["no hay STORYBOARD.md (ejemplo en assets/templates/STORYBOARD.md)"]
    durs = {v["frame"]: v["duration_s"]
            for v in (_json(proj / "audio_meta.json") or {}).get("voices", [])}
    issues = []
    for frame in texto.split_frames(text):
        num, fields = frame["number"], frame["fields"]
        src = fields.get("src", "")
        if not re.fullmatch(rf"compositions/frames/f{num:02d}-[a-z0-9-]+\.html", src):
            issues.append(f"frame {num}: src debe ser compositions/frames/f{num:02d}-<slug>.html "
                          f"(hay '{src}')")
        dur = durs.get(num)
        if dur is not None and abs(texto.seconds(fields.get("duration", "0")) - dur) > 0.02:
            issues.append(f"frame {num}: duration {fields.get('duration')} ≠ voz {dur}s "
                          "(corre `./vl prep`)")
        for name in texto.asset_names(fields.get("asset_candidates", "")):
            if not any((proj / d / name).exists() for d in ("assets", "capture/assets")):
                issues.append(f"frame {num}: asset inexistente {name}")
    return issues


def _frame_structure(html: str, fid: str) -> list[str]:
    """Contrato de sub-composición: template, id, timeline pausado y registrado."""
    issues = []
    body = html.strip()
    if not (body.startswith("<template") and body.endswith("</template>")):
        issues.append(f"{fid}: el archivo debe ser un único <template>…</template>")
    for needle, why in ((f'data-composition-id="{fid}"', "id de composición"),
                        ("paused: true", "timeline pausado")):
        if needle not in html.replace("paused:true", "paused: true"):
            issues.append(f"{fid}: falta {why} ({needle})")
    if not re.search(rf"__timelines\[\s*['\"]{re.escape(fid)}['\"]\s*\]\s*=", html):
        issues.append(f'{fid}: registra window.__timelines["{fid}"] = tl')
    if "fonts.googleapis" in html or "@import" in html:
        issues.append(f"{fid}: fuentes de red prohibidas; usa @font-face local de frame.md")
    if "<audio" in html:
        issues.append(f"{fid}: sin <audio> en escenas (el audio lo monta el ensamblador)")
    if FORBIDDEN_JS.search(html):
        issues.append(f"{fid}: prohibido Math.random/Date.now/repeat:-1/yoyo (no determinista)")
    prefix = fid.split("-")[0] + "-"  # fNN-: único entre escenas, que es lo que importa
    ids = re.findall(r'\bid="([^"]+)"', html)
    bad_ids = [i for i in ids if i != "root" and not i.startswith(prefix)]
    if bad_ids:
        issues.append(f"{fid}: ids sin prefijo '{prefix}': {', '.join(sorted(set(bad_ids))[:6])}")
    return issues + _frame_css(html, fid, set(ids))


def _frame_css(html: str, fid: str, ids: set[str]) -> list[str]:
    """Reglas del <style> que no corresponden al HTML: la clase de fallo más silenciosa.

    Un `#root { color:#fff }` sobre un contenedor llamado de otra forma no aplica, y el
    texto hereda el negro del navegador. Pasó en un video entregado: título negro sobre
    fondo oscuro, con todos los checks en verde.
    """
    issues = []
    estilos = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S))
    if not estilos:
        return issues
    # El div con data-composition-id es la raíz: el resto del contrato (data-duration,
    # las reglas de #root) lo supone así.
    raiz = re.search(rf'<[^>]*data-composition-id="{re.escape(fid)}"[^>]*>', html)
    if raiz and 'id="root"' not in raiz.group(0):
        nombre = re.search(r'id="([^"]+)"', raiz.group(0))
        hoy = f" (hoy es id={nombre.group(1)!r})" if nombre else ""
        issues.append(f"{fid}: el contenedor con data-composition-id debe llevar id='root'"
                      f"{hoy}; si no, las reglas #root del CSS no aplican")
    # Selectores #id del CSS sin elemento que los reciba (ids renombrados, typos).
    # Los cuerpos de las reglas se quitan primero: ahí viven los colores hex (#C04346),
    # que si no se cuelan como "ids".
    selectores = re.sub(r"\{[^}]*\}", " ", estilos)
    huerfanos = {i for i in re.findall(r"#([A-Za-z][\w-]*)", selectores) if i not in ids}
    if huerfanos:
        issues.append(f"{fid}: el CSS estila ids que no existen: "
                      f"{', '.join('#' + i for i in sorted(huerfanos)[:6])}")
    if re.search(r"#root\s*\{[^}]*\}", estilos) and not re.search(
            r"#root\s*\{[^}]*[;{\s]color\s*:", estilos):
        issues.append(f"{fid}: la regla #root no declara `color:`; el texto hereda el negro "
                      "del navegador (usa el color de texto de frame.md)")
    # Caja de texto que no puede partir línea ni encoger: el texto se sale al cambiar de
    # idioma, de fuente o de contenido, aunque hoy quepa.
    for selector, cuerpo in re.findall(r"([^{}]+)\{([^}]*)\}", estilos):
        if (re.search(r"[;{\s]width\s*:\s*\d+px", cuerpo)
                and re.search(r"white-space\s*:\s*nowrap", cuerpo)):
            issues.append(f"{fid}: {selector.strip()} mezcla ancho fijo en px con "
                          "white-space:nowrap; dimensiónalo con padding + inline-flex")
    return issues


def _frame_timing(html: str, fid: str, dur: float) -> list[str]:
    """Raíz y clips largos deben llegar al final del frame, o la transición queda en blanco."""
    issues = []
    root = re.search(r'id="root"[^>]*data-duration="([\d.]+)"', html)
    if not root:
        # Sin esto el check se saltaba en silencio cuando la raíz se llamaba de otra forma.
        issues.append(f"{fid}: no encuentro id=\"root\" con data-duration; la raíz debe "
                      f"llevar id=\"root\" y data-duration=\"{dur}\"")
    elif float(root.group(1)) < dur - 0.02:
        issues.append(f"{fid}: root data-duration {root.group(1)} < duración del frame {dur}")
    for tag in re.findall(r"<[^>]*\bdata-start=[^>]*>", html):
        attr = dict(re.findall(r'data-([\w-]+)="([^"]*)"', tag))
        end = float(attr.get("start", 0)) + float(attr.get("duration", 0))
        # Un clip que termina justo antes del final quedó con una duración vieja: el
        # ensamblador solo extiende (para la transición) los que terminan en la duración.
        if dur - 1.0 < end < dur - 0.02:
            name = re.search(r'id="([^"]+)"', tag)
            issues.append(f"{fid}: el clip {name.group(1) if name else '?'} termina en "
                          f"{end:.2f}s pero el frame dura {dur}s: usa data-duration={dur}")
    return issues


ASPECT_TOL = 0.01  # 1 %: por debajo el estiramiento no se nota; por encima sí


def _caja_css(estilos: str, ident: str) -> tuple[float, float] | None:
    """Ancho y alto en px que el CSS le da a ese id, si fija los dos y no usa object-fit."""
    regla = re.search(rf"#{re.escape(ident)}\s*\{{([^}}]*)\}}", estilos)
    if not regla or re.search(r"object-fit\s*:\s*(cover|contain)", regla.group(1)):
        return None  # recortar o encajar es una decisión explícita
    ancho = re.search(r"[;{\s]width\s*:\s*([\d.]+)px", regla.group(1))
    alto = re.search(r"[;{\s]height\s*:\s*([\d.]+)px", regla.group(1))
    return (float(ancho.group(1)), float(alto.group(1))) if ancho and alto else None


def _frame_images(proj: Path, html: str, fid: str) -> list[str]:
    """Imágenes de assets/ mostradas con una relación de aspecto distinta a la nativa."""
    estilos = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S))
    issues = []
    for tag in re.findall(r"<img\b[^>]*>", html):
        src = re.search(r'src="(assets/[^"]+)"', tag)
        ident = re.search(r'id="([^"]+)"', tag)
        if not (src and ident) or src.group(1).endswith(".svg"):
            continue
        archivo = proj / src.group(1)
        caja = _caja_css(estilos, ident.group(1)) if archivo.exists() else None
        if not caja:
            continue
        mostrada, nativa = caja[0] / caja[1], imagenes.aspect(archivo)
        if abs(mostrada / nativa - 1) > ASPECT_TOL:
            issues.append(f"{fid}: {src.group(1)} se muestra {caja[0]:g}x{caja[1]:g} "
                          f"({mostrada:.3f}) pero su relación nativa es {nativa:.3f}: sale "
                          f"estirada. Usa height:{round(caja[0] / nativa)}px o "
                          "object-fit:contain")
    return issues


def check_frame(proj: Path, frame: dict) -> list[str]:
    """Revisión estática del HTML de una escena (errores que rompen el render)."""
    src = frame["fields"].get("src", "")
    fid = Path(src).stem
    html = _read(proj / src)
    if not html:
        return [f"{fid}: no existe {src}"]
    issues = _frame_structure(html, fid)
    issues += [f"{fid}: referencia inexistente {a}" for a in
               sorted(set(re.findall(r'(assets/[\w./-]+\.(?:png|jpe?g|webp|svg|woff2))', html)))
               if not (proj / a).exists()]
    issues += _frame_images(proj, html, fid)
    if frame["fields"].get("duration"):
        issues += _frame_timing(html, fid, texto.seconds(frame["fields"]["duration"]))
    return issues


def lint_findings(proj: Path, stem: str) -> list[str]:
    """Errores y avisos de `hyperframes lint` en compositions/frames/<stem>.html."""
    pin = re.search(r"hyperframes@[0-9.]+", _read(proj / "package.json"))
    try:
        out = subprocess.run(["npx", "--yes", pin.group(0) if pin else "hyperframes", "lint",
                              "--json"], cwd=proj, capture_output=True, text=True,
                             timeout=120, check=False).stdout
        findings = json.loads(out).get("findings", [])
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return [f"no pude correr hyperframes lint: {exc}"]
    return [f"lint {f['severity']}: {f['code']} — {f.get('fixHint') or f['message']}"
            for f in findings if f.get("severity") in ("error", "warning")
            and Path(f.get("file", "")).stem == stem]


# Códigos de `hf check` que en un crossfade son falsos positivos: dos escenas se cruzan
# a propósito. Solo se descartan si el instante cae dentro de una transición.
EN_TRANSICION_OK = {"content_overlap"}
# Margen alrededor del corte: la transición más larga de `transitions.mjs` dura 0.6 s.
MARGEN_TRANSICION_S = 0.75


def _cortes(proj: Path) -> list[float]:
    """Segundo en que empieza cada frame del video ensamblado (los cortes)."""
    cortes, t = [], 0.0
    for frame in texto.split_frames(_read(proj / "STORYBOARD.md")):
        dur = frame["fields"].get("duration")
        if not dur:
            return cortes
        cortes.append(t)
        t += texto.seconds(dur)
    return cortes


def _en_transicion(tiempo: float, cortes: list[float]) -> bool:
    """¿Ese instante cae en un cruce entre dos escenas?"""
    return any(abs(tiempo - c) <= MARGEN_TRANSICION_S for c in cortes)


def check_findings(proj: Path, stem: str = "") -> list[str]:
    """Hallazgos del navegador (`hf check --json`): contraste AA real, desbordes y solapes.

    Incluye severidad `warning` e `info` a propósito: `hf check` las deja fuera de su `ok`
    y por eso llegaron a un video entregado ocho fallos de contraste AA que sí detectó.
    """
    reporte = _json(proj / ".vl/check.json")
    if not reporte:
        return ["no hay .vl/check.json: corre `./vl ensamblar`"]
    cortes = _cortes(proj)
    issues = []
    for seccion, datos in reporte.items():
        if not isinstance(datos, dict) or not isinstance(datos.get("findings"), list):
            continue
        for f in datos["findings"]:
            archivo = Path(f.get("sourceFile") or f.get("file") or "").stem
            if stem and archivo != stem:
                continue
            tiempo = f.get("time")
            if (f.get("code") in EN_TRANSICION_OK and isinstance(tiempo, (int, float))
                    and _en_transicion(float(tiempo), cortes)):
                continue  # dos escenas cruzándose en una transición: esperado
            donde = f"{archivo}: " if archivo and not stem else ""
            cuando = f" en t={tiempo:.1f}s" if isinstance(tiempo, (int, float)) else ""
            pista = f" — {f['fixHint']}" if f.get("fixHint") else ""
            issues.append(f"{donde}{seccion}/{f.get('code', '?')} en "
                          f"{f.get('selector', '?')}{cuando}: {f.get('message', '')}{pista}")
    return issues


def check_escenas(proj: Path) -> list[str]:
    """Todas las escenas y el resultado de lint/check del ensamblado."""
    issues = []
    for frame in texto.split_frames(_read(proj / "STORYBOARD.md")):
        issues += check_frame(proj, frame)
    if not re.search(r"\b0 errors?(?:\(s\))?\b", _read(proj / ".vl/lint.txt")):
        issues.append("lint con errores o sin correr: `./vl ensamblar` y lee .vl/lint.txt")
    return issues + check_findings(proj)


def check_entrega(proj: Path) -> list[str]:
    """MP4 final con resolución, duración, audio y sonoridad correctos."""
    video = proj / "renders/video.mp4"
    if not video.exists():
        return ["no hay renders/video.mp4: `./vl render`"]
    info = medios.video_summary(video)
    total = sum(v["duration_s"] for v in (_json(proj / "audio_meta.json") or {}).get("voices", []))
    aspect = texto.parse_frontmatter(_read(proj / "BRIEF.md")).get("aspect", "1920x1080")
    width, height = (int(n) for n in aspect.split("x"))
    issues = []
    if (info["width"], info["height"]) != (width, height):
        issues.append(f"resolución {info['width']}x{info['height']} ≠ {width}x{height}")
    if total and abs(info["duration"] - total) > 1.5:
        issues.append(f"duración {info['duration']:.1f}s ≠ narración {total:.1f}s")
    if not info["audio"]:
        issues.append("el MP4 no tiene audio")
    elif not -20 <= (loud := medios.lufs(video)) <= -14:
        issues.append(f"sonoridad {loud:.1f} LUFS fuera de [-20, -14]")
    return issues


CHECKS = {"captura": check_captura, "marca": check_marca, "guion": check_guion,
          "voz": check_voz, "storyboard": check_storyboard, "escenas": check_escenas,
          "entrega": check_entrega}

# (qué existe, descripción, sugerencia si falta). Orden = flujo habitual, no obligatorio.
ARTIFACTS = [
    ("BRIEF.md", "brief", "completa BRIEF.md y capture.json (references/captura.md)"),
    ("capture/extracted/capture-report.json", "capturas", "`./vl captura` y revisa las hojas"),
    ("frame.md", "marca", "`./vl marca sugerir` y `./vl marca`"),
    ("SCRIPT.md", "guion", "escribe SCRIPT.md (references/oficio.md § Guion)"),
    ("audio_meta.json", "voz", "`./vl voz design` 🛑 el usuario elige, luego `./vl voz lines`"),
    ("renders/preview-audio.mp3", "música", "`./vl musica` 🛑 aprobar audio (o sin música)"),
    ("STORYBOARD.md", "storyboard", "escribe STORYBOARD.md y corre `./vl prep`"),
    ("index.html", "escenas", "escenas en compositions/frames/ y `./vl ensamblar`"),
    ("renders/review/qa-report.json", "revisión", "`./vl snap` 🛑 aprobar hojas"),
    ("renders/video.mp4", "video", "`./vl render` y `./vl final`"),
]


def estado(proj: Path) -> int:
    """Qué hay hecho (según los archivos) y una sugerencia; el orden lo decides tú."""
    frames = list((proj / "compositions/frames").glob("f*.html"))
    pending = None
    for rel, label, hint in ARTIFACTS:
        if label == "capturas" and es_explicativo(proj):
            continue
        # init deja un index.html vacío: cuenta como hecho solo si ya hay escenas
        done = (proj / rel).exists() and (rel != "index.html" or bool(frames))
        print(f"{'✓' if done else '·'} {label:<11} {rel}")
        pending = pending or (None if done else hint)
    print(f"\nSugerencia: {pending or 'entrega renders/video.mp4'}")
    return 0


def show(issues: list[str]) -> int:
    """Imprime avisos; 0 si no hay ninguno."""
    for issue in issues:
        print(f"  ⚠ {issue}")
    print("✅ sin avisos" if not issues else f"✗ {len(issues)} aviso(s)")
    return 1 if issues else 0


# Archivos de otras skills de HyperFrames que usa `vl` (API interna: puede cambiar sin aviso)
DEPENDENCIAS = [f"product-launch-video/scripts/{f}" for f in (
    "build-frame.mjs", "stage-assets.mjs", "audio.mjs", "assemble-index.mjs",
    "transitions.mjs", "frame-packets.mjs")] + [
    "media-use/audio/scripts/audio.mjs", "media-use/audio/scripts/wait-bgm.mjs",
    "hyperframes/references/frame-worker-core.md"]
COMPAT = Path(__file__).resolve().parents[1] / "compat.json"


def huellas(skills: Path) -> dict:
    """sha256 (12 caracteres) de cada dependencia instalada; None si falta."""
    return {rel: (hashlib.sha256((skills / rel).read_bytes()).hexdigest()[:12]
                  if (skills / rel).exists() else None) for rel in DEPENDENCIAS}


def compat(skills: Path, grabar: bool) -> int:
    """Compara las dependencias instaladas con las probadas (compat.json) o las graba."""
    actual = huellas(skills)
    if grabar:
        data = json.loads(COMPAT.read_text(encoding="utf-8")) if COMPAT.exists() else {}
        data["dependencias"] = actual
        COMPAT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"✓ compat.json grabado ({len(actual)} archivos)")
        return 0
    probado = json.loads(COMPAT.read_text(encoding="utf-8")).get("dependencias", {})
    distintos = [rel for rel, h in actual.items() if h and probado.get(rel) != h]
    for rel in distintos:
        print(f"⚠ {rel} cambió desde la versión probada de video-web")
    if distintos:
        print("  Corre las evals antes de usarla en videos reales, o reinstala la versión "
              "probada: `vl doctor` muestra cuál es.")
    return 1 if distintos else 0


def main() -> int:
    """Punto de entrada."""
    what = sys.argv[1] if len(sys.argv) > 1 else "estado"
    proj = Path.cwd()
    if what == "estado":
        return estado(proj)
    if what == "compat":
        return compat(Path(sys.argv[2]), "--grabar" in sys.argv)
    if what == "todo":
        issues = []
        for name, check in CHECKS.items():
            issues += [f"{name}: {i}" for i in check(proj)]
        return show(issues)
    if what in CHECKS:
        return show(CHECKS[what](proj))
    for frame in texto.split_frames(_read(proj / "STORYBOARD.md")):
        if what in (Path(frame["fields"].get("src", "")).stem, str(frame["number"]),
                    f"{frame['number']:02d}"):
            stem = Path(frame["fields"].get("src", "")).stem
            hallazgos = check_findings(proj, stem) if (proj / ".vl/check.json").exists() else []
            return show(check_frame(proj, frame) + lint_findings(proj, stem) + hallazgos)
    print(f"✗ '{what}' no es una revisión ({', '.join(CHECKS)}, todo) ni un frame de "
          "STORYBOARD.md")
    return 2


if __name__ == "__main__":
    sys.exit(main())
