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
