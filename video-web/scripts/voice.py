"""Narración local con Qwen3-TTS (VoiceDesign → clon con Base) verificada con Whisper.

    voice.py design [--n 3]        voces candidatas por instruct, rankeadas por P(idioma) y WER
    voice.py lines [--frames 3,7]  clona la voz elegida por línea; reintenta semillas por WER
    voice.py finalize              recorta, nivela y agrega pausas a los NN.raw.wav existentes

Corre con el venv de Qwen3-TTS desde la raíz del proyecto (lo hace `./vl voz`). Configuración en
audio.json. Cada fase carga un solo modelo en la GPU (8 GB no alcanzan para Qwen + Whisper).
"""
import argparse
import gc
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from utils import medios, texto  # pylint: disable=import-error

VOICE_DIR, REF_DIR = Path("assets/voice"), Path("assets/voice/ref")
DESIGN_MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
BASE_MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
GEN_KWARGS = {"temperature": 0.8, "top_p": 0.95, "max_new_tokens": 2048}
TARGET_LUFS = -18


_LOADED: dict = {"name": None, "model": None}


def device() -> str:
    """cuda, mps o cpu: VL_DEVICE manda; si no, el mejor disponible."""
    import torch  # pylint: disable=import-outside-toplevel,import-error
    if os.environ.get("VL_DEVICE"):
        return os.environ["VL_DEVICE"]
    if torch.cuda.is_available():
        return "cuda"
    return "mps" if torch.backends.mps.is_available() else "cpu"


def load(name: str):
    """Un modelo a la vez en memoria: Qwen (TTS) o "whisper"; libera el anterior.

    Sin GPU NVIDIA corre en CPU (medido: TTS ≈ 6× la duración del audio con 16 núcleos) o en
    MPS (Apple) para el TTS; faster-whisper no soporta MPS y usa CPU int8.
    """
    import torch  # pylint: disable=import-outside-toplevel,import-error
    dev = device()
    if _LOADED["name"] != name:
        _LOADED.update(name=None, model=None)
        gc.collect()
        if dev == "cuda":
            torch.cuda.empty_cache()
        if name == "whisper":
            from faster_whisper import WhisperModel  # pylint: disable=C0415,E0401
            model = (WhisperModel("large-v3", device="cuda", compute_type="float16")
                     if dev == "cuda" else WhisperModel("large-v3", device="cpu",
                                                        compute_type="int8"))
        else:
            from qwen_tts import Qwen3TTSModel  # pylint: disable=C0415,E0401
            extra = {"attn_implementation": "sdpa"} if dev == "cuda" else {}
            model = Qwen3TTSModel.from_pretrained(
                name, device_map="cuda:0" if dev == "cuda" else dev,
                dtype=torch.bfloat16 if dev == "cuda" else torch.float32, **extra)
        _LOADED.update(name=name, model=model)
    return _LOADED["model"]


def save_wav(wav, rate: int, path: Path) -> None:
    """WAV mono float32."""
    import numpy as np  # pylint: disable=import-outside-toplevel,import-error
    import soundfile as sf  # pylint: disable=import-outside-toplevel,import-error
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), np.asarray(wav, dtype=np.float32), rate)


def transcribe(whisper, path: Path, lang: str) -> tuple[str, list[dict]]:
    """Texto oído y palabras con tiempos."""
    segments, _ = whisper.transcribe(str(path), language=lang, word_timestamps=True,
                                     vad_filter=False, beam_size=5)
    words = [w for seg in segments for w in seg.words]
    return (" ".join(w.word.strip() for w in words),
            [{"text": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
             for w in words])


def p_lang(whisper, path: Path, lang: str) -> float:
    """P(idioma) de la detección de Whisper: un acento extranjero la baja."""
    _, info = whisper.transcribe(str(path), language=None, beam_size=1)
    return round(float(dict(info.all_language_probs or []).get(lang, 0.0)), 4)


def rank(cfg: dict, paths: list[Path]) -> list[dict]:
    """Ordena candidatas por P(idioma) y WER contra el texto de referencia."""
    whisper, lang, report = load("whisper"), cfg["voice"]["whisper_lang"], []
    for path in paths:
        heard, _ = transcribe(whisper, path, lang)
        report.append({"file": str(path), "p_lang": p_lang(whisper, path, lang),
                       "wer": round(texto.wer(cfg["voice"]["ref_text"], heard), 3),
                       "heard": heard})
    report.sort(key=lambda r: (-r["p_lang"], r["wer"]))
    for row in report:
        row["ok"] = row["p_lang"] >= cfg["gates"]["ref_min_p_lang"] and row["wer"] <= 0.1
    (REF_DIR / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
    return report


def design_candidates(voice: dict, count: int) -> list[Path]:
    """Genera las candidatas. Función aparte: al volver, nada retiene el modelo en la GPU."""
    import torch  # pylint: disable=import-outside-toplevel,import-error
    tts, made = load(DESIGN_MODEL), []
    for variant, instruct in voice["instructs"].items():
        for idx in range(1, count + 1):
            torch.manual_seed(1000 + idx * 17)
            wavs, rate = tts.generate_voice_design(text=voice["ref_text"], instruct=instruct,
                                                   language=voice["language"], **GEN_KWARGS)
            made.append(REF_DIR / f"{variant}-{idx}.wav")
            save_wav(wavs[0], rate, made[-1])
            print(f"  ✓ {made[-1].name}", flush=True)
    return made


def cmd_design(cfg: dict, count: int) -> int:
    """Candidatas de voz por instruct y ranking objetivo."""
    voice = cfg["voice"]
    # un instruct en inglés da acento inglés: escríbelo en el idioma del video
    english = [k for k, v in voice["instructs"].items() if texto.english_ratio(v) > 0.12]
    if english and voice.get("whisper_lang", "es") != "en":
        sys.exit(f"✗ instructs en inglés: {', '.join(english)}. Escríbelos en el idioma del "
                 "video y describe a una hablante NATIVA de una ciudad concreta (si no, suena a "
                 "acento extranjero).")
    report = rank(cfg, design_candidates(voice, count))
    for row in report:
        print(f"{'✓' if row['ok'] else '✗'} {row['file']}  P={row['p_lang']:.4f}  "
              f"WER={row['wer']:.3f}")
    best = [r["file"] for r in report if r["ok"]][:3]
    if not best:
        print("Ninguna candidata pasa. Ajusta los instructs (más detalle de hablante nativa) "
              "y repite `./vl voz design`.")
        return 1
    print(f"SIGUIENTE: 🛑 envía al usuario {', '.join(best)} para que elija; pon su elección "
          "en audio.json → voice.ref_audio y corre `./vl voz lines`")
    return 0


def synth(cfg: dict, ref: Path, jobs: dict[int, int], script: dict) -> None:
    """Genera NN.raw.wav para cada {frame: intento} con semilla distinta por intento."""
    import torch  # pylint: disable=import-outside-toplevel,import-error
    voice = cfg["voice"]
    tts = load(BASE_MODEL)
    prompt = tts.create_voice_clone_prompt(ref_audio=str(ref), ref_text=voice["ref_text"])
    for frame, attempt in sorted(jobs.items()):
        torch.manual_seed(voice.get("seed", 4242) + 1000 * attempt + frame)
        wavs, rate = tts.generate_voice_clone(
            text=texto.respell(script[frame], cfg.get("respell", {})),
            language=voice["language"], voice_clone_prompt=prompt, **GEN_KWARGS)
        save_wav(wavs[0], rate, VOICE_DIR / f"{frame:02d}.raw.wav")
        print(f"  ✓ {frame:02d}.raw.wav (intento {attempt + 1})", flush=True)


def cmd_lines(cfg: dict, ref: Path, frames: set[int]) -> int:
    """Clona todas las líneas (o las pedidas), reintenta las de WER alto y finaliza."""
    script = texto.parse_script(Path("SCRIPT.md").read_text(encoding="utf-8"))
    jobs = {f: 0 for f in (frames or set(script))}
    for attempt in range(cfg["gates"].get("tries", 3)):
        synth(cfg, ref, jobs, script)
        jobs = {frame: attempt + 1 for frame in failing_lines(cfg, sorted(jobs), script)}
        if not jobs:
            break
    return cmd_finalize(cfg)


def failing_lines(cfg: dict, frames: list[int], script: dict) -> list[int]:
    """Frames cuyo WAV crudo supera el WER máximo (función aparte: libera Whisper al volver)."""
    whisper, failing = load("whisper"), []
    for frame in frames:
        heard, _ = transcribe(whisper, VOICE_DIR / f"{frame:02d}.raw.wav",
                              cfg["voice"]["whisper_lang"])
        score = texto.wer_respell(script[frame], heard, cfg.get("respell", {}))
        if score > cfg["gates"]["max_wer"]:
            print(f"  ↻ frame {frame}: WER {score:.3f} → otra semilla\n      oído: {heard}",
                  flush=True)
            failing.append(frame)
    return failing


def trim_and_pad(cfg: dict, frame: int, words: list[dict], meta: dict) -> tuple[float, float]:
    """NN.raw.wav → NN.wav: recorte al habla, −18 LUFS y pausas; devuelve (recorte, pausa)."""
    pads = cfg["pads"]
    raw = VOICE_DIR / f"{frame:02d}.raw.wav"
    edge = pads.get("edge_s", 0.12)
    start = max(words[0]["start"] - edge, 0.0) if words else 0.0
    end = words[-1]["end"] + edge * 2 if words else medios.duration(raw)
    head = pads["first_head_s"] if frame == meta["first"] else 0.0
    tail = pads["last_tail_s"] if frame == meta["last"] else pads["tail_s"]
    chain = (f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11,"
             f"adelay=delays={int(head * 1000)}:all=1,apad=pad_dur={tail}")
    # -ss/-to como opciones de ENTRADA: como opciones de salida también cortarían el relleno.
    medios.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.3f}", "-to",
                f"{end:.3f}", "-i", str(raw), "-af", chain, "-ar", "44100", "-ac", "1",
                str(VOICE_DIR / f"{frame:02d}.wav")])
    return start, head


def finalize_line(cfg: dict, whisper, frame: int, meta: dict) -> dict:
    """Finaliza una línea y la vuelve a transcribir para medir WER, P(idioma) y tiempos."""
    lang = cfg["voice"]["whisper_lang"]
    _, words = transcribe(whisper, VOICE_DIR / f"{frame:02d}.raw.wav", lang)
    start, head = trim_and_pad(cfg, frame, words, meta)
    final = VOICE_DIR / f"{frame:02d}.wav"
    heard, words = transcribe(whisper, final, lang)
    for word in words:  # Whisper pega a 0.0 la primera palabra tras un silencio inicial
        word["start"] = max(word["start"], head)
        word["end"] = max(word["end"], word["start"])
    return {"frame": frame, "path": str(final), "duration_s": round(medios.duration(final), 3),
            "wer": round(texto.wer_respell(meta["script"][frame], heard,
                                           cfg.get("respell", {})), 3),
            "p_lang": p_lang(whisper, final, lang), "trim_s": round(start, 3), "heard": heard,
            "words": [dict(w, id=f"w{i}") for i, w in enumerate(words)]}


def cmd_finalize(cfg: dict) -> int:
    """NN.wav finales + audio_meta.json + cues.md; exit 1 si alguna línea no pasa."""
    script = texto.parse_script(Path("SCRIPT.md").read_text(encoding="utf-8"))
    missing = [f for f in script if not (VOICE_DIR / f"{f:02d}.raw.wav").exists()]
    if missing:
        sys.exit(f"✗ faltan WAV crudos de los frames {missing}: corre `./vl voz lines`")
    whisper, gates = load("whisper"), cfg["gates"]
    meta = {"first": min(script), "last": max(script), "script": script}
    voices, bad, cues = [], [], ["# Cues de voz (generado por `./vl voz`)", "",
                                  "Segundos desde el inicio de cada frame.", ""]
    for frame in sorted(script):
        line = finalize_line(cfg, whisper, frame, meta)
        heard = line.pop("heard")
        passed = line["wer"] <= gates["max_wer"] and line["p_lang"] >= gates["min_p_lang"]
        print(f"  {'OK ' if passed else 'REV'} {frame:02d} {line['duration_s']:6.2f}s "
              f"WER={line['wer']:.3f} P={line['p_lang']:.4f}", flush=True)
        if not passed:
            bad.append(frame)
            print(f"      esperado: {script[frame]}\n      oído:     {heard}")
        voices.append(line)
        cues += [f"## Frame {frame} · {line['duration_s']:.2f} s",
                 " · ".join(f"{w['start']:.2f} {w['text']}" for w in line["words"]), ""]
    old = json.loads(Path("audio_meta.json").read_text(encoding="utf-8")) \
        if Path("audio_meta.json").exists() else {}
    Path("audio_meta.json").write_text(json.dumps(
        {"bgm": old.get("bgm"), "bgm_pending": False, "voices": voices, "sfx": []},
        ensure_ascii=False, indent=2), encoding="utf-8")
    Path("cues.md").write_text("\n".join(cues), encoding="utf-8")
    print(f"Total narración: {sum(v['duration_s'] for v in voices):.1f} s · "
          f"a revisar: {bad or 'ninguna'}")
    print("SIGUIENTE: " + (f"`./vl voz lines --frames {','.join(map(str, bad))}` (o ajusta "
                           "respell en audio.json)" if bad else "`./vl musica` (opcional)"))
    return 1 if bad else 0


def chosen_voice(cfg: dict) -> Path:
    """Voz de referencia elegida por el usuario (audio.json → voice.ref_audio)."""
    choice = cfg["voice"].get("ref_audio")
    if not choice or not Path(choice).exists():
        sys.exit("✗ 🛑 falta la voz elegida: el usuario escucha las candidatas de "
                 "`./vl voz design` y pones su ruta en audio.json → voice.ref_audio")
    return Path(choice)


def gpu_users() -> str:
    """Procesos que ocupan la GPU según nvidia-smi (pid, memoria, comando)."""
    try:
        out = medios.run(["nvidia-smi", "--query-compute-apps=pid,used_memory",
                          "--format=csv,noheader"]).stdout
    except (OSError, subprocess.CalledProcessError):
        return "  (no pude consultar nvidia-smi)"
    lines = []
    for row in filter(None, out.splitlines()):
        pid, mem = [x.strip() for x in row.split(",")[:2]]
        cmd = Path(f"/proc/{pid}/cmdline")
        name = cmd.read_bytes().replace(b"\0", b" ").decode()[:120] if cmd.exists() else "?"
        lines.append(f"  pid {pid} · {mem} · {name}")
    return "\n".join(lines) or "  (ninguno visible)"


def main() -> int:
    """Punto de entrada; si la GPU se queda sin memoria, dice quién la usa."""
    import torch  # pylint: disable=import-outside-toplevel,import-error
    try:
        return run()
    except torch.cuda.OutOfMemoryError:
        sys.exit("✗ la GPU se quedó sin memoria. Procesos que la usan:\n" + gpu_users() +
                 "\nCierra alguno y repite, o corre sin GPU con VL_DEVICE=cpu (más lento).")


def run() -> int:
    """Interpreta argumentos y despacha el subcomando."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("design").add_argument("--n", type=int, default=3)
    sub.add_parser("lines").add_argument("--frames", default="")
    sub.add_parser("finalize")
    args = parser.parse_args()
    raw = Path("audio.json").read_text(encoding="utf-8")
    if re.search(r"<[A-ZÁÉÍÓÚÑ_ ]{3,}>", raw):
        sys.exit("✗ audio.json aún tiene marcadores <...>: complétalo (references/oficio.md § Voz)")
    cfg = json.loads(raw)
    if args.cmd == "design":
        return cmd_design(cfg, args.n)
    if args.cmd == "lines":
        return cmd_lines(cfg, chosen_voice(cfg), {int(f) for f in args.frames.split(",") if f})
    return cmd_finalize(cfg)


if __name__ == "__main__":
    sys.exit(main())
