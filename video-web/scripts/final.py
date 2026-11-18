"""Entrega final: música automatizada, sonoridad, subtítulos, miniatura y métricas.

    final.py    renders/imagen-voz.mp4 (givemotion: imagen + voces + efectos) →
                renders/video.mp4, renders/video.vtt, renders/miniatura.png,
                renders/review/final.json, renders/review/final-grilla.jpg
                (y renders/video-720p.mp4 si el MP4 pesa más de 25 MB)

La música va fuera de givemotion porque su data-duck es una sola proporción fija y su mezcla
solo limita picos: aquí sube en la portada, en las pausas y en los cambios de sección, baja
`under_voice_db` bajo la voz mientras se habla y todo queda a −16 LUFS / pico ≤ −1.5 dBTP.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np  # pylint: disable=import-error

from utils import medios, texto  # pylint: disable=import-error

GM = ["npx", "--yes", "givemotion@0.1.6"]
ENTRADA = Path("renders/imagen-voz.mp4")
SALIDA = Path("renders/video.mp4")
REVIEW = Path("renders/review")
# 25 y no 30 MB: con el límite justo, un render de 30.7 MB no se pudo enviar.
SHARE_LIMIT = 25 * 2**20

TARGET_LUFS, MAX_TP, TOLERANCIA_LU = -16.0, -1.5, 0.5
TP_LOUDNORM = -2.0  # medio dB de margen: el AAC sube un poco el pico verdadero
SR = 48000

# Envolvente de la música (dB relativos al nivel «bajo la voz»)
UNIR_PAUSA = 0.9      # palabras separadas por menos de esto forman un solo tramo hablado
SUBE_PAUSA, SUBE_SECCION, SUBE_PORTADA = 6.0, 9.0, 12.0
RAMPA, FUNDIDO = 0.35, 2.0
RATE = 1000           # muestras/s de la envolvente; ffmpeg la lleva a 48 kHz

# Subtítulos
MAX_LINEA = 42
FIN_FRASE = ".?!…"
PAUSA_CORTE = 0.6     # una pausa más larga también cierra el subtítulo


# ---------------------------------------------------------------- tiempos de escena y voces

def atributos(tag: str) -> dict:
    """Atributos de una etiqueta HTML como dict (sin valor = '')."""
    return {k: v for k, v in re.findall(r'([\w-]+)="([^"]*)"', tag)}


def escenas(video_html: str) -> list[str]:
    """Rutas de las escenas incluidas en la secuencia, en orden."""
    return re.findall(r'<gm-include[^>]*\bsrc="([^"]+)"', video_html)


def inicios_inspect() -> list[float] | None:
    """Inicio de cada escena según `givemotion inspect` (None si falla)."""
    # inspect solo lee video.html local; sin sandbox porque en algunas máquinas Chrome muere
    # con SIGTRAP. Si el entorno ya define la variable, manda el entorno.
    env = {"GIVEMOTION_NO_SANDBOX": "1", **os.environ}
    try:
        out = subprocess.run(GM + ["inspect", "video.html"], capture_output=True,
                             text=True, check=True, env=env, timeout=600)
        clips = json.loads(out.stdout)["clips"]
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        return None
    return sorted(c["start"] for c in clips if c.get("scene"))


def inicios_duracion(video_html: str, htmls: list[str]) -> list[float]:
    """Respaldo: suma data-duration de cada escena y resta el solape de la transición."""
    trans = re.search(r'data-transition="\S+\s+([\d.]+)', video_html)
    solape = float(trans.group(1)) if trans else 0.0
    starts, t = [], 0.0
    for html in htmls:
        starts.append(round(t, 3))
        dur = re.search(r'<section[^>]*data-duration="([\d.]+)"', html)
        t += (float(dur.group(1)) if dur else 0.0) - solape
    return starts


def desfase_voz(html: str, ruta_voz: str) -> float | None:
    """data-start del <audio> de esa voz dentro de la escena (0 si no tiene; None si no está)."""
    for tag in re.findall(r"<audio\b[^>]*>", html):
        attr = atributos(tag)
        src = attr.get("src", "")
        if src == ruta_voz or Path(src).name == Path(ruta_voz).name:
            return float(attr.get("data-start", 0) or 0)
    return None


def ubicar_voces(voces: list[dict], htmls: list[str], starts: list[float]) -> list[dict]:
    """Cada voz con t0 = inicio de su escena + desfase de su <audio> en esa escena."""
    out = []
    for voz in voces:
        for idx, html in enumerate(htmls):
            off = desfase_voz(html, voz["path"])
            if off is not None:
                out.append({**voz, "escena": idx + 1, "t0": starts[idx] + off})
                break
        else:
            sys.exit(f"✗ ninguna escena tiene <audio src=\"{voz['path']}\"> (voz {voz['frame']})")
    return out


# ---------------------------------------------------------------- envolvente de la música

def tramos(palabras: list[tuple[float, float]], unir: float = UNIR_PAUSA) -> list[list[float]]:
    """Tramos hablados [inicio, fin]: palabras separadas por menos de `unir` s se juntan."""
    spans: list[list[float]] = []
    for ini, fin in sorted(palabras):
        if spans and ini - spans[-1][1] < unir:
            spans[-1][1] = max(spans[-1][1], fin)
        else:
            spans.append([ini, fin])
    return spans


def envolvente(dur: float, spans: list[list[float]], secciones: list[float],
               bajo_db: float, rate: int = RATE) -> np.ndarray:
    """Ganancia lineal de la música, `rate` muestras por segundo.

    Plena (+12 dB) antes de la primera palabra, `bajo_db` mientras se habla, +6 dB en las
    pausas, +9 dB en las pausas con cambio de sección y tras la última palabra; rampas de
    RAMPA s y fundido de FUNDIDO s al final.
    """
    t = np.arange(int(dur * rate)) / rate
    db = np.full(t.shape, bajo_db + SUBE_PAUSA)
    if spans:
        db[t < spans[0][0]] = bajo_db + SUBE_PORTADA
        for (_, a), (b, _) in zip(spans[:-1], spans[1:]):
            if any(a - 1.5 < x < b + 0.5 for x in secciones):
                db[(t >= a) & (t < b)] = bajo_db + SUBE_SECCION
        db[t >= spans[-1][1]] = bajo_db + SUBE_SECCION
        for ini, fin in spans:
            db[(t >= ini - 0.15) & (t < fin + 0.1)] = bajo_db
    # rampas: media móvil con sumas acumuladas (lineal en la longitud, no O(n·k))
    k = max(1, int(RAMPA * rate))
    pad = np.pad(db, (k // 2, k - k // 2), mode="edge")
    acc = np.concatenate([[0.0], np.cumsum(pad)])
    db = (acc[k:] - acc[:-k])[:len(t)] / k
    gain = 10 ** (db / 20)
    fade = t > dur - FUNDIDO
    gain[fade] *= np.cos((t[fade] - (dur - FUNDIDO)) / FUNDIDO * np.pi / 2) ** 2
    return gain


# ---------------------------------------------------------------- subtítulos

def lineas(palabras: list[str], maximo: int = MAX_LINEA) -> list[str] | None:
    """1 o 2 líneas de ≤ maximo caracteres, lo más parejas posible (None si no caben)."""
    todo = " ".join(palabras)
    if len(todo) <= maximo or len(palabras) == 1:
        return [todo]
    mejor = None
    for i in range(1, len(palabras)):
        a, b = " ".join(palabras[:i]), " ".join(palabras[i:])
        if len(a) <= maximo and len(b) <= maximo and (mejor is None
                                                      or abs(len(a) - len(b)) < mejor[0]):
            mejor = (abs(len(a) - len(b)), [a, b])
    return mejor[1] if mejor else None


def partir(seg: list[dict], k: int) -> list[list[dict]]:
    """Divide un tramo en k trozos contiguos de largo parecido (por caracteres)."""
    total = sum(len(w["t"]) + 1 for w in seg)
    trozos: list[list[dict]] = [[] for _ in range(k)]
    pos = 0
    for w in seg:
        centro = pos + (len(w["t"]) + 1) / 2
        trozos[min(k - 1, int(centro * k / total))].append(w)
        pos += len(w["t"]) + 1
    return [t for t in trozos if t]


def frases(palabras: list[dict]) -> list[list[dict]]:
    """Agrupa palabras {t, s, e} en subtítulos. Cada oración (o tramo tras una pausa larga)
    cierra su subtítulo; si no cabe en 2 líneas se reparte en el mínimo de subtítulos
    parejos, así no quedan palabras sueltas como «aprendido.» en pantalla 0.7 s."""
    segmentos, cur = [], []
    for i, w in enumerate(palabras):
        cur.append(w)
        sig = palabras[i + 1] if i + 1 < len(palabras) else None
        if sig is None or w["t"][-1] in FIN_FRASE or sig["s"] - w["e"] > PAUSA_CORTE:
            segmentos.append(cur)
            cur = []
    grupos = []
    for seg in segmentos:
        for k in range(1, len(seg) + 1):
            trozos = partir(seg, k)
            if all(lineas([w["t"] for w in t]) for t in trozos):
                grupos += trozos
                break
    return grupos


def marca(t: float) -> str:
    """Segundos → HH:MM:SS.mmm de WebVTT."""
    h, rem = divmod(max(t, 0.0), 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


def vtt(grupos: list[list[dict]]) -> str:
    """Texto WebVTT; cada subtítulo dura hasta 0.25 s tras su última palabra sin pisar el
    siguiente."""
    out = ["WEBVTT", ""]
    for n, g in enumerate(grupos):
        fin = g[-1]["e"] + 0.25
        if n + 1 < len(grupos):
            fin = min(fin, grupos[n + 1][0]["s"] - 0.05)
        out += [str(n + 1), f"{marca(g[0]['s'])} --> {marca(fin)}",
                *lineas([w["t"] for w in g]), ""]
    return "\n".join(out)


def palabras_video(voces: list[dict], guion: dict[int, str]) -> tuple[list[dict], list[int]]:
    """Palabras con tiempo de video. Ortografía del guion («cero», no «0») alineada por
    índice con los tiempos de Whisper; si el número de palabras no coincide, texto de Whisper.
    Devuelve también las líneas que usaron el texto de Whisper."""
    out, whisper = [], []
    for voz in voces:
        tokens = guion.get(voz["frame"], "").split()
        if len(tokens) != len(voz["words"]):
            tokens = [w["text"] for w in voz["words"]]
            whisper.append(voz["frame"])
        out += [{"t": tok, "s": voz["t0"] + w["start"], "e": voz["t0"] + w["end"]}
                for tok, w in zip(tokens, voz["words"])]
    return sorted(out, key=lambda w: w["s"]), whisper


# ---------------------------------------------------------------- audio

def ff(*args: str) -> None:
    """ffmpeg silencioso que falla con su mensaje."""
    medios.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", *args])


def normalizar(src: Path, dst: Path) -> None:
    """loudnorm en dos pasadas (lineal) a TARGET_LUFS y TP_LOUDNORM, 48 kHz estéreo."""
    base = f"loudnorm=I={TARGET_LUFS}:TP={TP_LOUDNORM}:LRA=11"
    out = medios.run(["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-i", str(src), "-af",
                      base + ":print_format=json", "-f", "null", "-"], check=False)
    m = json.loads(re.findall(r"\{[^{}]*\}", out.stderr)[-1])
    ff("-i", str(src), "-af",
       f"{base}:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
       f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
       f":offset={m['target_offset']}:linear=true,aresample={SR}",
       "-ar", str(SR), "-ac", "2", "-c:a", "pcm_f32le", str(dst))


def mezclar(tmp: Path, dur: float, voces: list[dict], starts: list[float], bgm: dict) -> Path:
    """Voz/efectos de givemotion + música por su envolvente → WAV sin normalizar."""
    voz_wav = tmp / "voz.wav"
    ff("-i", str(ENTRADA), "-vn", "-ac", "2", "-ar", str(SR), "-c:a", "pcm_f32le", str(voz_wav))
    if not (bgm or {}).get("path"):
        print("Sin música (audio.json → bgm.path vacío)")
        return voz_wav
    musica = Path(bgm["path"])
    if not musica.exists():
        sys.exit(f"✗ no existe la música {musica} (audio.json → bgm.path)")
    voz_i, mus_i = medios.lufs(voz_wav), medios.lufs(musica)
    bajo = (voz_i - float(bgm.get("under_voice_db", 18))) - mus_i
    spans = tramos([(v["t0"] + w["start"], v["t0"] + w["end"])
                    for v in voces for w in v["words"]])
    secciones = [starts[n - 1] for n in bgm.get("secciones", []) if 0 < n <= len(starts)]
    envolvente(dur, spans, secciones, bajo).astype("<f4").tofile(tmp / "env.raw")
    print(f"voz+efectos {voz_i:.1f} LUFS · música {mus_i:.1f} LUFS · música bajo la voz "
          f"{bajo:+.1f} dB (pausa {bajo + SUBE_PAUSA:+.1f}, sección {bajo + SUBE_SECCION:+.1f},"
          f" portada {bajo + SUBE_PORTADA:+.1f})")
    fmt = f"aresample={SR},aformat=sample_fmts=flt:channel_layouts=stereo"
    mezcla = tmp / "mezcla.wav"
    ff("-i", str(voz_wav), "-stream_loop", "-1", "-i", str(musica),
       "-f", "f32le", "-ar", str(RATE), "-ac", "1", "-i", str(tmp / "env.raw"),
       "-filter_complex",
       f"[0:a]{fmt}[v];[1:a]{fmt},atrim=0:{dur:.3f}[m];[2:a]{fmt}[e];[m][e]amultiply[mb];"
       "[v][mb]amix=inputs=2:normalize=0:duration=first[mix]",
       "-map", "[mix]", "-c:a", "pcm_f32le", str(mezcla))
    return mezcla


def empaquetar(master: Path) -> dict:
    """Video copiado sin recodificar + audio AAC 48 kHz; devuelve la sonoridad medida."""
    ff("-i", str(ENTRADA), "-i", str(master), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
       "-c:a", "aac", "-b:a", "256k", "-ar", str(SR), "-ac", "2", "-movflags", "+faststart",
       str(SALIDA))
    return medios.loudness(SALIDA)


# ---------------------------------------------------------------- comando

def leer(path: str) -> dict:
    """JSON del proyecto ({} si no existe)."""
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    """Punto de entrada."""
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    if not ENTRADA.exists():
        sys.exit(f"✗ falta {ENTRADA}: corre `./vl render` primero")
    video_html = Path("video.html").read_text(encoding="utf-8")
    htmls = [Path(src).read_text(encoding="utf-8") for src in escenas(video_html)]
    starts = inicios_inspect()
    fuente = "givemotion inspect"
    if not starts or len(starts) != len(htmls):
        starts, fuente = inicios_duracion(video_html, htmls), "data-duration (inspect falló)"
        print("⚠ givemotion inspect falló: inicios calculados con data-duration y la transición")
    voces = ubicar_voces(leer("audio_meta.json").get("voices", []), htmls, starts)
    bgm = leer("audio.json").get("bgm")
    dur = medios.duration(ENTRADA)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        normalizar(mezclar(tmp, dur, voces, starts, bgm), tmp / "master.wav")
        medida = empaquetar(tmp / "master.wav")
        if abs(medida["lufs"] - TARGET_LUFS) > TOLERANCIA_LU:
            print(f"Segunda pasada: {medida['lufs']:.1f} LUFS fuera de ±{TOLERANCIA_LU} LU")
            normalizar(tmp / "master.wav", tmp / "master2.wav")
            medida = empaquetar(tmp / "master2.wav")

    guion = texto.parse_script(Path("SCRIPT.md").read_text(encoding="utf-8")) \
        if Path("SCRIPT.md").exists() else {}
    palabras, whisper = palabras_video(voces, guion)
    grupos = frases(palabras)
    SALIDA.with_suffix(".vtt").write_text(vtt(grupos), encoding="utf-8")
    ff("-i", str(ENTRADA), "-frames:v", "1", "-vf", "scale=1920:1080", "renders/miniatura.png")

    info = {**medios.video_summary(SALIDA), **medida, "inicios": fuente,
            "subtitulos": len(grupos), "subtitulos_whisper": whisper,
            "musica": bgm.get("path") if bgm else None}
    REVIEW.mkdir(parents=True, exist_ok=True)
    medios.grilla(SALIDA, REVIEW / "final-grilla.jpg", info["duration"])
    if info["bytes"] > SHARE_LIMIT:
        medios.preview_720p(SALIDA, Path("renders/video-720p.mp4"))
        info["preview_720p"] = "renders/video-720p.mp4"
    (REVIEW / "final.json").write_text(json.dumps(info, indent=2, ensure_ascii=False),
                                       encoding="utf-8")

    ok = abs(medida["lufs"] - TARGET_LUFS) <= TOLERANCIA_LU and medida["true_peak"] <= MAX_TP
    print(f"{'✓' if ok else '✗'} {SALIDA}: {info['width']}x{info['height']} · "
          f"{info['duration']:.2f} s · {info['bytes'] / 2**20:.1f} MB · {medida['lufs']:.1f} LUFS"
          f" · pico {medida['true_peak']:.1f} dBTP · LRA {medida['lra']:.1f} LU")
    print(f"Inicios de escena: {fuente} · subtítulos: {len(grupos)} en {SALIDA.with_suffix('.vtt')}"
          + (f" (texto de Whisper en líneas {whisper})" if whisper else ""))
    print("Grilla: renders/review/final-grilla.jpg · miniatura: renders/miniatura.png"
          + (" · 720p: renders/video-720p.mp4" if "preview_720p" in info else ""))
    print("SIGUIENTE: revisa la grilla y escucha el inicio, un cambio de sección y el cierre;"
          " entrega renders/video.mp4 con renders/video.vtt")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
