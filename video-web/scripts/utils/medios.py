"""Utilidades de medios sobre ffmpeg/ffprobe: duración, sonoridad y metadatos.

Solo stdlib + binarios del sistema, sin estado.
"""
import json
import re
import subprocess
from pathlib import Path


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Ejecuta un comando capturando salida de texto."""
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def probe(path: Path) -> dict:
    """Metadatos de ffprobe (formato y streams) como dict."""
    out = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format",
               "-show_streams", str(path)])
    return json.loads(out.stdout)


def duration(path: Path) -> float:
    """Duración en segundos según ffprobe."""
    return float(probe(path)["format"]["duration"])


def lufs(path: Path) -> float:
    """Sonoridad integrada (EBU R128) en LUFS."""
    out = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
               "ebur128=framelog=quiet", "-f", "null", "-"], check=False)
    matches = re.findall(r"I:\s+(-?[\d.]+) LUFS", out.stderr)
    if not matches:
        raise RuntimeError(f"no se pudo medir LUFS de {path}")
    return float(matches[-1])


def loudness(path: Path) -> dict:
    """Sonoridad integrada (LUFS), pico verdadero (dBTP) y rango (LU) según EBU R128."""
    out = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0", "-af",
               "ebur128=peak=true:framelog=quiet", "-f", "null", "-"], check=False)
    summary = out.stderr[out.stderr.rfind("Summary:"):]
    found = {key: re.search(rf"{label}:\s+(-?[\d.]+|-inf)", summary)
             for key, label in (("lufs", "I"), ("true_peak", "Peak"), ("lra", "LRA"))}
    if not found["lufs"]:
        raise RuntimeError(f"no se pudo medir la sonoridad de {path}")
    return {key: float(m.group(1)) if m else None for key, m in found.items()}


def grilla(video: Path, out: Path, dur: float) -> None:
    """Hoja 4×3 con 12 fotogramas repartidos en todo el video."""
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-vf",
         f"fps=12/{dur:.2f},scale=480:-1,tile=4x3", "-frames:v", "1", str(out)])


def preview_720p(video: Path, out: Path) -> None:
    """Copia liviana en 720p para compartir por chat o correo."""
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-vf", "scale=-2:720",
         "-c:v", "libx264", "-crf", "26", "-preset", "medium", "-c:a", "aac", "-b:a", "128k",
         "-movflags", "+faststart", str(out)])


def gain_for(current_lufs: float, target_lufs: float) -> float:
    """Factor lineal de volumen para llevar current_lufs a target_lufs."""
    return round(10 ** ((target_lufs - current_lufs) / 20), 3)


def video_summary(path: Path) -> dict:
    """Resumen del MP4: tamaño, duración, resolución, fps y si tiene audio."""
    info = probe(path)
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), {})
    audio = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    return {"bytes": int(info["format"]["size"]), "duration": float(info["format"]["duration"]),
            "width": video.get("width"), "height": video.get("height"),
            "fps": video.get("r_frame_rate"), "audio": audio is not None}
