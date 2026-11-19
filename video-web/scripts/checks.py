"""Revisiones objetivas del proyecto y estado inferido de los archivos. Solo avisan.

Se ejecuta con el directorio del proyecto como cwd (lo hace `vl`):
    checks.py estado                 qué hay hecho y una sugerencia de siguiente paso
    checks.py captura|marca|guion|voz|escenas|entrega|todo

Nada bloquea otros comandos: la lista de avisos dice qué arreglar y el código de salida es 1
si hay alguno (útil para que un worker repita hasta ✅). Los mensajes van en español porque
los lee el modelo que usa la skill.
"""
import json
import re
import sys
from pathlib import Path

from utils import colores, medios, texto  # pylint: disable=import-error

MAX_WORDS_LINE = 45  # más largo degrada el TTS; mejor dividir la línea
WORDS_PER_S = 2.4


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
    """marca.css con los tokens básicos, contraste AA de cada texto sobre SU fondo y fuentes."""
    css = _read(proj / "marca.css")
    if not css:
        return ["no hay marca.css: corre `./vl marca`"]
    colors = dict(re.findall(r"--([\w-]+):\s*(#[0-9A-Fa-f]{6})\b", css))
    issues = [f"marca.css: falta el token --{k}" for k in ("bg", "ink", "muted", "accent")
              if k not in colors]
    # Cada texto se mide sobre el fondo donde va: el chip de acento está sobre su propio
    # tinte, no sobre bg, y ahí el contraste baja (pasó en un video entregado).
    # Portada y cierre llevan texto sobre --campo, y los chips sólidos sobre --accent: con un
    # blanco fijo, un campo claro quedaba ilegible y nadie lo medía.
    pares = [("ink", "bg"), ("muted", "bg"), ("muted", "surface"), ("accent-text", "bg"),
             ("accent-text", "accent-bg"), ("ok", "ok-bg"), ("bad", "bad-bg"),
             ("on-campo", "campo"), ("on-accent", "accent")]
    for texto_k, fondo_k in pares:
        if texto_k in colors and fondo_k in colors:
            ratio = colores.contrast(colors[texto_k], colors[fondo_k])
            if ratio < 4.5:
                issues.append(f"contraste --{texto_k} sobre --{fondo_k} = {ratio:.2f} (< 4.5): "
                              "ajusta capture.json → brand y corre `./vl marca`")
    issues += _tokens_fuera_de_marca(colors)
    issues += [f"fuente declarada sin archivo: {font}" for font in
               re.findall(r"url\((assets/fonts/[^)]+)\)", css) if not (proj / font).exists()]
    return issues


# Tokens que no comparten el tono del primario a propósito: neutros y semánticos.
TOKENS_LIBRES = {"bg", "ink", "muted", "line", "surface", "ok", "ok-bg", "bad", "bad-bg",
                 "on-campo", "on-accent"}
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
    base = _tono(colors["accent"]) if colors.get("accent") else None
    if base is None:
        return []
    issues = []
    for key, value in colors.items():
        if key in TOKENS_LIBRES or key == "accent":
            continue
        tono = _tono(value)
        if tono is None:
            continue
        dif = min(abs(tono - base), 360 - abs(tono - base))
        if dif > TONO_MAX:
            issues.append(f"{key} {value} tiene un tono {dif:.0f}° lejos del acento "
                          f"{colors['accent']}: ¿es de la marca o quedó de otro proyecto? "
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
    cfg = _json(proj / "audio.json") or {}
    gates = cfg.get("gates", {})
    lines = texto.parse_script(_read(proj / "SCRIPT.md"))
    voices = meta.get("voices", [])
    issues = [] if len(voices) == len(lines) else [
        f"voces {len(voices)} ≠ líneas del guion {len(lines)}: `./vl voz lines`"]
    from voice import avisos_1x  # pylint: disable=import-outside-toplevel,import-error
    issues += [f"audio.json de video-web 1.x: {a}" for a in avisos_1x(cfg)]
    voz_actual = cfg.get("voice", {}).get("library") or cfg.get("voice", {}).get("ref_audio")
    for voice in voices:
        # la voz guarda la huella del texto con que se generó (voice.py → firmas.json)
        linea = lines.get(voice["frame"])
        if voice.get("texto") and linea and voice["texto"] != texto.huella(linea):
            issues.append(f"frame {voice['frame']}: SCRIPT.md cambió después de generar su voz "
                          "→ `./vl voz lines` (regenera solo las que cambiaron)")
        if voice.get("voz") and voz_actual and voice["voz"] != voz_actual:
            issues.append(f"frame {voice['frame']}: narrada con «{voice['voz']}» y audio.json "
                          f"pide «{voz_actual}» → `./vl voz lines`")
        if not (proj / voice["path"]).exists():
            issues.append(f"no existe {voice['path']}")
        if voice.get("wer", 1) > gates.get("max_wer", 0.08):
            issues.append(f"frame {voice['frame']}: WER {voice.get('wer')} alto → respell o "
                          f"`./vl voz lines --frames {voice['frame']}`")
        if voice.get("p_lang", 0) < gates.get("min_p_lang", 0.97):
            issues.append(f"frame {voice['frame']}: P(idioma) {voice.get('p_lang')} bajo")
        # Whisper transcribe una frase repetida una sola vez (WER 0): el detector de habla
        # oculta de voice.py lo deja en `revisar`. Así llegó una frase doble a un video.
        for motivo in voice.get("revisar", []):
            issues.append(f"frame {voice['frame']}: {motivo} → escúchala y "
                          f"`./vl voz lines --frames {voice['frame']}`")
    return issues


def _escenas(proj: Path) -> list[Path]:
    return sorted((proj / "scenes").glob("s[0-9]*.html"))


def check_escenas(proj: Path) -> list[str]:
    """Una escena por línea, con su voz y su duración, y el resultado de `givemotion check`."""
    voces = {v["frame"]: v for v in (_json(proj / "audio_meta.json") or {}).get("voices", [])}
    escenas = _escenas(proj)
    if not escenas:
        return ["no hay scenes/sNN.html: escribe las escenas (plantilla escena-ejemplo.html)"]
    issues = [] if not voces or len(escenas) == len(voces) else [
        f"{len(escenas)} escenas ≠ {len(voces)} líneas de voz"]
    video = _read(proj / "video.html")
    incluidas = re.findall(r'<gm-include\s+src="(scenes/s\d+\.html)"', video)
    # el encabezado de video.html también carga archivos (el símbolo de la marca)
    issues += [f"video.html: no existe {rel}" for rel in
               sorted(set(re.findall(r'src="(assets/[^"]+)"', re.sub(r"<!--.*?-->", "", video,
                                                                       flags=re.S))))
               if not (proj / rel).exists()]
    for escena in escenas:
        html, num = _read(escena), int(re.sub(r"\D", "", escena.stem))
        if f"scenes/{escena.name}" not in incluidas:
            issues.append(f"{escena.name} no está incluida en video.html")
        voz = voces.get(num)
        if voz and Path(voz["path"]).name not in html:
            issues.append(f"{escena.name}: no reproduce su voz {voz['path']}")
        dur = re.search(r'class="scene"[^>]*data-duration="([\d.]+)"', html)
        if voz and dur and float(dur.group(1)) < voz["duration_s"]:
            issues.append(f"{escena.name}: data-duration {dur.group(1)} < voz "
                          f"{voz['duration_s']} s (la voz se cortaría)")
        # un archivo que falta no rompe el render: givemotion lo omite en silencio (404)
        for rel in sorted(set(re.findall(r'src="(assets/[^"]+)"', html))):
            if not (proj / rel).exists():
                issues.append(f"{escena.name}: no existe {rel}")
        if re.search(r"#[0-9A-Fa-f]{6}\b", re.sub(r"<!--.*?-->", "", html, flags=re.S)):
            issues.append(f"{escena.name}: colores en hexadecimal; usa var(--token) o C('token') "
                          "de marca.css (si no, una marca nueva hereda los de este video)")
        issues += [f"{escena.name}: {i}" for i in _legibilidad(html)]
        if _es_campo(html):
            issues += [f"{escena.name}: {i}" for i in _sobre_campo(proj, html, video)]
    issues += [f"video.html: {i}" for i in _legibilidad(video)]
    issues += _densidad(proj, escenas)
    reporte = _json(proj / ".vl/check.json")
    if reporte is None:
        return issues + ["sin revisión de givemotion: corre `./vl revisar`"]
    # ✖ errores y ⚠ avisos de givemotion son fallas reales salvo que sean a propósito;
    # ℹ son sugerencias de estilo y no se listan.
    for item in reporte.get("issues", []):
        if item.get("severity") in ("error", "warning") and not _still_calmo(item):
            momento = f" ({item['time']:.1f}–{item.get('until', item['time']):.1f} s)" \
                if "time" in item else ""
            issues.append(f"givemotion {item.get('code')}{momento}: {item.get('message')}")
    return issues


# `still` de givemotion = «poco cambia en pantalla». En el estilo calma una escena puede tener
# pasos pequeños y sincronizados con la voz (una palabra que cambia de color, un hilo que avanza)
# que givemotion mide como quietud. Un tramo así de corto, con la voz narrando, no es falla; uno
# más largo sí (la voz sola no sostiene el interés).
STILL_MAX_S = 6.0


def _still_calmo(item: dict) -> bool:
    """True si es un aviso `still` cuyos tramos duran todos <= STILL_MAX_S."""
    if item.get("code") != "still":
        return False
    tramos = item.get("ranges") or [[item.get("time", 0), item.get("until", item.get("time", 0))]]
    return all(fin - ini <= STILL_MAX_S for ini, fin in tramos)


TEXTO_MIN_PX = 24  # etiquetas 24, contenido 30, títulos 60 (oficio.md § Escenas)
OPACIDAD_MIN_CAMPO = 0.85
ANCHO_MIN = 0.6  # fracción del ancho que debe ocupar el contenido de una escena
ALTO_MIN = 0.4  # fracción de la franja y 228–900
# píxeles con contenido en esa franja: las escenas aprobadas del piloto miden 0,05–0,2; un
# inicio de escena con un rótulo suelto, 0,003–0,015
RELLENO_MIN = 0.03


def _sin_comentarios(html: str) -> str:
    return re.sub(r"<!--.*?-->|/\*.*?\*/", "", html, flags=re.S)


def _es_campo(html: str) -> bool:
    """La escena va sobre el campo (portada, separador o cierre)."""
    return bool(re.search(r'<section[^>]*class="[^"]*\bcampo\b', html))


def _legibilidad(html: str) -> list[str]:
    """Texto menor que el mínimo y texto pintado con el color del fondo.

    givemotion solo avisa bajo 22 px; los videos se ven en el celular y el piloto tuvo que
    agrandar tarjetas enteras. `color: var(--bg)` se lee solo si el fondo es oscuro por
    casualidad: en una portada de campo claro, o al cambiar de marca, desaparece."""
    limpio, issues = _sin_comentarios(html), []
    chicos = sorted({float(n) for n in re.findall(r"font-size:\s*(\d+(?:\.\d+)?)px", limpio)
                     if float(n) < TEXTO_MIN_PX})
    if chicos:
        issues.append(f"texto de {', '.join(f'{n:g}' for n in chicos)} px (< {TEXTO_MIN_PX}): "
                      "etiquetas ≥ 24, contenido ≥ 30, títulos ≥ 60")
    if re.search(r"(?<![\w-])color:\s*var\(--bg\)", limpio):
        issues.append("texto con color var(--bg): sobre el campo usa var(--on-campo); sobre un "
                      "relleno de acento, var(--on-accent)")
    return issues


def _clases_rellenas_de_acento(css: str) -> list[set[str]]:
    """Conjuntos de clases (último tramo del selector) con fondo var(--accent)."""
    out = []
    for selectores, cuerpo in re.findall(r"([^{}]+)\{([^{}]*)\}", _sin_comentarios(css)):
        if re.search(r"background(?:-color)?:\s*var\(--accent\)", cuerpo):
            for sel in selectores.split(","):
                clases = set(re.findall(r"\.([\w-]+)", sel.split()[-1] if sel.split() else ""))
                if clases:
                    out.append(clases)
    return out


def _sobre_campo(proj: Path, html: str, video: str) -> list[str]:
    """Portada y cierre: rellenos de acento invisibles y texto atenuado.

    Con una marca que usa su primario de campo, la burbuja «Tú» (fondo de acento) desapareció
    sobre la portada; y un título de cierre atenuado a 0,55 pasó givemotion (3:1 por ser
    grande) pero el dueño no lo leía."""
    issues = []
    colors = dict(re.findall(r"--([\w-]+):\s*(#[0-9A-Fa-f]{6})\b", _read(proj / "marca.css")))
    if "accent" in colors and "campo" in colors and \
            (ratio := colores.contrast(colors["accent"], colors["campo"])) < 3:
        estilos = "".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S))
        propias = [c for sel, cuerpo in re.findall(r"([^{}]+)\{([^{}]*)\}", estilos)
                   if re.search(r"background", cuerpo) and
                   not re.search(r"background(?:-color)?:\s*var\(--accent\)", cuerpo)
                   for c in [set(re.findall(r"\.([\w-]+)", sel.split()[-1]))] if c]
        css = _read(proj / "marca.css") + "".join(
            re.findall(r"<style[^>]*>(.*?)</style>", video + html, re.S))
        usadas = [set(c.split()) for c in re.findall(r'class="([^"]+)"', html)]
        for rellena in _clases_rellenas_de_acento(css):
            if any(rellena <= u for u in usadas) and not any(rellena == p for p in propias):
                issues.append(f"{'.' + '.'.join(sorted(rellena))} va relleno de acento sobre el "
                              f"campo ({ratio:.1f}:1, se pierde): ahí usa fondo var(--bg) y texto "
                              "var(--accent-text)")
    for valor in re.findall(r"\.to\([^)]*?opacity:\s*(0?\.\d+)", _sin_comentarios(html)):
        if 0.05 < float(valor) < OPACIDAD_MIN_CAMPO:
            issues.append(f"en portada y cierre algo se atenúa a {valor}: el mensaje que queda "
                          f"se lee completo (opacidad ≥ {OPACIDAD_MIN_CAMPO})")
    return issues


def tiempos(proj: Path) -> list[tuple[str, float]]:
    """(id de la escena, segundo del 65 % de ella), según `givemotion inspect` (.vl/inspect.json).

    Las hojas de givemotion muestran momentos automáticos, a veces el inicio de una escena,
    cuando aún no ha aparecido nada: así no se puede juzgar si quedó pobre. Al 65 % ya está
    armada. Sumar los data-duration no sirve: las transiciones solapan las escenas."""
    clips = (_json(proj / ".vl/inspect.json") or {}).get("clips", [])
    escenas = sorted((c for c in clips if c.get("scene")), key=lambda c: c["start"])
    return [(c["selector"].lstrip("#"), round(c["start"] + 0.65 * (c["end"] - c["start"]), 2))
            for c in escenas]


def _uso_del_lienzo(cuadro: Path) -> tuple[float, float, float] | None:
    """(ancho, alto, área) que ocupa el contenido en la franja y 228–900; None si no hay nada."""
    import numpy as np  # pylint: disable=import-outside-toplevel,import-error
    from PIL import Image  # pylint: disable=import-outside-toplevel,import-error
    img = np.asarray(Image.open(cuadro).convert("RGB"), dtype=np.int16)
    alto, ancho = img.shape[:2]
    franja = img[int(alto * 228 / 1080):int(alto * 900 / 1080)]
    fondo = np.median(franja.reshape(-1, 3), axis=0)
    # la retícula de puntos del fondo difiere ~16 del lienzo: no cuenta como contenido
    marca = np.abs(franja - fondo).max(axis=2) > 40
    cols = np.flatnonzero(marca.sum(axis=0) >= 3)
    filas = np.flatnonzero(marca.sum(axis=1) >= 3)
    if cols.size == 0:
        return None
    return ((cols[-1] - cols[0]) / ancho, (filas[-1] - filas[0]) / len(franja),
            float(marca.mean()))


def _densidad(proj: Path, escenas: list[Path]) -> list[str]:
    """Escenas de contenido que usan poco lienzo, medidas en el cuadro de `./vl revisar`.

    En el piloto de un curso las primeras escenas dejaron media pantalla vacía con tarjetas
    chicas y pasaron todas las revisiones; hubo que rehacerlas."""
    cuadros = sorted((proj / "renders/review/escenas").glob("t*.png"),
                     key=lambda p: float(p.stem[1:-1].replace("_", ".")))
    orden = [ident for ident, _ in tiempos(proj)]
    if not cuadros or len(cuadros) != len(orden):
        return []
    por_id = {}
    for escena in escenas:
        ident = re.search(r'<section[^>]*\bid="([^"]+)"', _read(escena))
        if ident:
            por_id[ident.group(1)] = escena
    issues = []
    for ident, cuadro in zip(orden, cuadros):
        if ident not in por_id or _es_campo(_read(por_id[ident])):
            continue
        uso = _uso_del_lienzo(cuadro)
        if uso is None:
            issues.append(f"{por_id[ident].name}: sin contenido visible al 65 % de la escena "
                          f"({cuadro.name})")
        elif uso[0] < ANCHO_MIN or uso[1] < ALTO_MIN or uso[2] < RELLENO_MIN:
            issues.append(f"{por_id[ident].name}: escena pobre, el contenido ocupa {uso[0]:.0%} "
                          f"del ancho, {uso[1]:.0%} del alto útil y {uso[2]:.1%} del área (mín. "
                          f"{ANCHO_MIN:.0%}, {ALTO_MIN:.0%} y {RELLENO_MIN:.0%}; {cuadro.name}): "
                          "tarjetas que llenen el lienzo y texto real del caso")
    return issues


LUFS_META = -16  # plataformas de cursos y video: −16 integrados, pico ≤ −1.5 dBTP


def check_entrega(proj: Path) -> list[str]:
    """MP4 final con resolución, duración, audio, sonoridad, subtítulos y miniatura."""
    video = proj / "renders/video.mp4"
    if not video.exists():
        return ["no hay renders/video.mp4: `./vl render` y `./vl final`"]
    info = medios.video_summary(video)
    total = sum(v["duration_s"] for v in (_json(proj / "audio_meta.json") or {}).get("voices", []))
    aspect = texto.parse_frontmatter(_read(proj / "BRIEF.md")).get("aspect", "1920x1080")
    width, height = (int(n) for n in aspect.split("x"))
    issues = []
    if (info["width"], info["height"]) != (width, height):
        issues.append(f"resolución {info['width']}x{info['height']} ≠ {width}x{height}")
    # cada escena dura su voz más un respiro (≤ 1.5 s) y la transición la solapa
    if total and not total - 1 <= info["duration"] <= total * 1.15 + 3:
        issues.append(f"duración {info['duration']:.1f}s no corresponde a la narración "
                      f"({total:.1f}s)")
    if not info["audio"]:
        issues.append("el MP4 no tiene audio")
    elif abs((loud := medios.lufs(video)) - LUFS_META) > 1:
        issues.append(f"sonoridad {loud:.1f} LUFS ≠ {LUFS_META}: `./vl final`")
    issues += [f"falta renders/{n}: `./vl final`" for n in ("video.vtt", "miniatura.png")
               if not (proj / "renders" / n).exists()]
    return issues


CHECKS = {"captura": check_captura, "marca": check_marca, "guion": check_guion,
          "voz": check_voz, "escenas": check_escenas, "entrega": check_entrega}

# (qué existe, descripción, sugerencia si falta). Orden = flujo habitual, no obligatorio.
ARTIFACTS = [
    ("BRIEF.md", "brief", "completa BRIEF.md y capture.json (references/captura.md)"),
    ("capture/extracted/capture-report.json", "capturas", "`./vl captura` y revisa las hojas"),
    ("marca.css", "marca", "`./vl marca sugerir` y `./vl marca`"),
    ("SCRIPT.md", "guion", "escribe SCRIPT.md (references/oficio.md § Guion)"),
    ("audio_meta.json", "voz", "`./vl voz lines` (voz de la biblioteca o 🛑 `./vl voz design`)"),
    ("scenes/s01.html", "escenas", "escribe video.html y scenes/ (references/oficio.md § Escenas)"),
    (".vl/check.json", "revisión", "`./vl revisar` y mira las hojas 🛑 aprobar"),
    ("renders/imagen-voz.mp4", "render", "`./vl render`"),
    ("renders/video.mp4", "video", "`./vl final` (mezcla, subtítulos y miniatura)"),
]


def estado(proj: Path) -> int:
    """Qué hay hecho (según los archivos) y una sugerencia; el orden lo decides tú."""
    pending = None
    for rel, label, hint in ARTIFACTS:
        if label == "capturas" and es_explicativo(proj):
            continue
        done = (proj / rel).exists()
        print(f"{'✓' if done else '·'} {label:<11} {rel}")
        pending = pending or (None if done else hint)
    print(f"\nSugerencia: {pending or 'entrega renders/video.mp4, video.vtt y miniatura.png'}")
    return 0


def show(issues: list[str]) -> int:
    """Imprime avisos; 0 si no hay ninguno."""
    for issue in issues:
        print(f"  ⚠ {issue}")
    print("✅ sin avisos" if not issues else f"✗ {len(issues)} aviso(s)")
    return 1 if issues else 0


def main() -> int:
    """Punto de entrada."""
    what = sys.argv[1] if len(sys.argv) > 1 else "estado"
    proj = Path.cwd()
    if what == "estado":
        return estado(proj)
    if what == "tiempos":  # lo usa `./vl revisar` para los cuadros de cada escena
        print(",".join(f"{t:g}" for _, t in tiempos(proj)))
        return 0
    if what == "todo":
        issues = []
        for name, check in CHECKS.items():
            issues += [f"{name}: {i}" for i in check(proj)]
        return show(issues)
    if what in CHECKS:
        return show(CHECKS[what](proj))
    print(f"✗ '{what}' no es una revisión ({', '.join(CHECKS)}, todo)")
    return 2


if __name__ == "__main__":
    sys.exit(main())
