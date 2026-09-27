"""Música de fondo: MusicGen local (motor de media-use) + volumen calibrado + preview.

    bgm.py generar     lanza el motor (--only bgm), espera la pista y luego mezcla
    bgm.py mezclar     solo calibra y mezcla una pista existente (assets/bgm/track.wav)

La voz queda a −18 LUFS y la música `under_voice_db` por debajo (12.5 dB, calibrado con la
mezcla de un video aprobado): el volumen por defecto del motor (0.12) resultó inaudible.
Escribe bgm en audio_meta.json, renders/narracion.wav y renders/preview-audio.mp3.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from utils import medios  # pylint: disable=import-error

AUDIO_ENGINE = Path(os.environ.get(
    "VL_MEDIA_USE_DIR", Path.home() / ".agents/skills/media-use")) / "audio/scripts"
QWEN_VENV = Path(os.environ.get("VL_QWEN_VENV", str(Path.home() / ".venvs/qwen-tts")))
VOICE_LUFS = -18


def load(path: str) -> dict:
    """JSON del proyecto."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump(path: str, data: dict) -> None:
    """Escribe JSON legible."""
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_generar(cfg: dict, meta: dict) -> int:
    """Pide la pista al motor de media-use (MusicGen) y espera a que termine."""
    track = Path("assets/bgm/track.wav")
    if track.exists():  # wait-bgm da por lista cualquier pista existente: aparta la anterior
        track.replace(track.with_name("track.prev.wav"))
    dump("audio_request.json", {"provider": "auto", "lines": [],
                                "bgm": {"mode": "generate", "prompt": cfg["bgm"]["prompt"]}})
    dump("audio_engine_meta.json", {"bgm": None, "sfx": [], "voices": [
        {"id": f"{v['frame']:02d}", "path": v["path"], "duration_s": v["duration_s"],
         "words": v["words"]} for v in meta["voices"]]})
    # El motor lanza `python3` del PATH para MusicGen: debe ser el del venv con transformers.
    env = {**os.environ, "PATH": f"{QWEN_VENV / 'bin'}:{os.environ['PATH']}"}
    subprocess.run(["node", str(AUDIO_ENGINE / "audio.mjs"), "--request",
                    "./audio_request.json", "--hyperframes", ".", "--out",
                    "./audio_engine_meta.json", "--only", "bgm"], env=env, check=True)
    subprocess.run(["node", str(AUDIO_ENGINE / "wait-bgm.mjs"), "--audio-meta",
                    "./audio_engine_meta.json", "--hyperframes", ".", "--timeout-ms",
                    "1500000", "--out", "./bgm_status.json"], check=True)
    status = load("bgm_status.json")
    if not status.get("ready"):
        sys.exit(f"✗ la música no quedó lista: {status.get('message')} (log: "
                 f"{status.get('log')}). Reintenta `./vl musica`.")
    return cmd_mezclar(cfg, meta, load("audio_engine_meta.json")["bgm"]["path"])


def cmd_mezclar(cfg: dict, meta: dict, track: str) -> int:
    """Calibra el volumen, lo registra en audio_meta.json y arma el preview de audio."""
    if not Path(track).exists():
        sys.exit(f"✗ no existe {track}: corre `./vl musica` (genera la pista)")
    Path("renders").mkdir(exist_ok=True)
    listing = Path(".vl/narracion.txt")
    listing.parent.mkdir(exist_ok=True)
    listing.write_text("".join(f"file '{Path(v['path']).resolve()}'\n" for v in meta["voices"]),
                       encoding="utf-8")
    medios.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i",
                str(listing), "-c:a", "pcm_s16le", "-ar", "44100", "renders/narracion.wav"])
    target = VOICE_LUFS - cfg["bgm"].get("under_voice_db", 12.5)
    volume = min(medios.gain_for(medios.lufs(Path(track)), target), 1.0)
    meta["bgm"] = {"path": track, "volume": volume, "mode": "generate",
                   "query": cfg["bgm"]["prompt"], "duration_s": round(medios.duration(
                       Path("renders/narracion.wav")), 2)}
    meta["bgm_pending"] = False
    dump("audio_meta.json", meta)
    medios.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "renders/narracion.wav", "-i",
                track, "-filter_complex", f"[1:a]volume={volume},aresample=44100[m];"
                "[0:a][m]amix=inputs=2:duration=first:normalize=0[a]", "-map", "[a]",
                "-c:a", "libmp3lame", "-b:a", "192k", "renders/preview-audio.mp3"])
    print(f"✅ música a volumen {volume} (≈ {target} LUFS); preview "
          f"{medios.lufs(Path('renders/preview-audio.mp3')):.1f} LUFS → "
          "renders/preview-audio.mp3")
    print("SIGUIENTE: 🛑 envía renders/preview-audio.mp3 al usuario. Si pide más o menos "
          "música, ajusta bgm.under_voice_db en audio.json y corre `./vl musica mezclar`.")
    return 0


def main() -> int:
    """Punto de entrada."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("cmd", choices=["generar", "mezclar"])
    args = parser.parse_args()
    if not Path("audio_meta.json").exists():
        sys.exit("✗ falta audio_meta.json: primero `./vl voz lines`")
    cfg, meta = load("audio.json"), load("audio_meta.json")
    if args.cmd == "generar":
        return cmd_generar(cfg, meta)
    return cmd_mezclar(cfg, meta, (meta.get("bgm") or {}).get("path", "assets/bgm/track.wav"))


if __name__ == "__main__":
    sys.exit(main())
