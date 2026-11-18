"""Narración local con Qwen3-TTS (VoiceDesign → clon con Base) verificada con Whisper.

    voice.py design [--n 3]        voces candidatas por instruct, rankeadas por P(idioma) y WER
    voice.py lines [--frames 3,7]  clona la voz elegida por línea; reintenta semillas si falla
    voice.py finalize              recorta, nivela y agrega pausas a los NN.raw.wav existentes
    voice.py guardar <nombre> [--desde ref.wav] [--texto "..."]
                                   guarda la voz elegida en la biblioteca ($VL_VOCES)

Receta (elegida a ciegas, 2026-11-18): clon con Base y la referencia COMPLETA (ref_audio +
ref_text, modo ICL), una generación por línea, semilla fija por voz. La voz sale de
audio.json → voice.library (carpeta $VL_VOCES/<nombre> con voz.json y ref.wav) o, si no hay
biblioteca, de voice.ref_audio + voice.ref_text.

El clon arrastra al inicio de cada toma la última frase de ref_text: el recorte la detecta y
corta tras ella. Whisper oye una frase repetida una sola vez y deja un hueco, así que el WER no
basta: cada línea pasa también por un detector de habla oculta (huecos con voz y ritmo lento).
Una línea que falla cualquiera de las dos cosas se repite con otra semilla.

Salida: NN.wav mono 48 kHz a −18 LUFS (la mezcla final normaliza a −16), audio_meta.json y
cues.md. Corre con el venv de Qwen3-TTS desde la raíz del proyecto (lo hace `./vl voz`). Cada
fase carga un solo modelo en la GPU (8 GB no alcanzan para Qwen + Whisper).
"""
import argparse
import gc
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from utils import medios, texto  # pylint: disable=import-error

VOICE_DIR, REF_DIR = Path("assets/voice"), Path("assets/voice/ref")
DESIGN_MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
BASE_MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
GEN_KWARGS = {"temperature": 0.8, "top_p": 0.95, "max_new_tokens": 2048}
TARGET_LUFS = -18
SAMPLE_RATE = 48000
VOCES_DEFAULT = "~/.config/video-web/voces"
MARGEN_FUGA_S = 0.1  # tras la frase filtrada: Whisper suele cerrar la última palabra temprano
HUECO_MAX_S = 1.0  # entre palabras: más que esto sin silencio real es habla no transcrita
# Ritmo mínimo por segundo de VOZ (sin silencios ≥ 0,25 s). En español la receta aprobada da
# ≈ 2,8–3,4 pal/s; por debajo de 2,3 hay habla que Whisper no transcribió (p. ej. una frase
# repetida que oye una sola vez).
MIN_PAL_POR_S = 2.3
SILENCIO = "silencedetect=noise=-35dB:d=0.25"
# Perfil de la voz que funcionó (references/oficio.md § La receta que funciona). Se usa para
# ordenar las candidatas: una con buen P(idioma) pero tono o ritmo fuera de rango suena mal.
# Se puede ajustar por proyecto en audio.json → voice.perfil.
PERFIL = {"f0_hz": [230, 275], "words_per_s": [2.0, 2.6]}


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


def f0_mediana(path: Path) -> float:
    """Tono mediano en Hz por autocorrelación de los tramos sonoros (0 si no hay voz)."""
    import numpy as np  # pylint: disable=import-outside-toplevel,import-error
    import soundfile as sf  # pylint: disable=import-outside-toplevel,import-error
    audio, rate = sf.read(str(path), dtype="float32", always_2d=True)
    onda = audio.mean(axis=1)
    paso, ventana = int(rate * 0.01), int(rate * 0.04)
    lo, hi = int(rate / 400), int(rate / 70)  # 70–400 Hz: voz humana
    tonos = []
    for inicio in range(0, max(0, len(onda) - ventana), paso):
        trozo = onda[inicio:inicio + ventana]
        if float(np.sqrt(np.mean(trozo ** 2))) < 0.01:
            continue  # silencio
        trozo = trozo - trozo.mean()
        corr = np.correlate(trozo, trozo, mode="full")[len(trozo) - 1:]
        if corr[0] <= 0 or hi >= len(corr):
            continue
        pico = int(np.argmax(corr[lo:hi])) + lo
        if corr[pico] / corr[0] > 0.3:  # periodicidad suficiente = sonoro
            tonos.append(rate / pico)
    return round(float(np.median(tonos)), 1) if tonos else 0.0


def _fuera(valor: float, rango: list) -> bool:
    """¿El valor cae fuera del rango del perfil? (0 = no medible, no penaliza)."""
    return bool(valor) and not rango[0] <= valor <= rango[1]


def rank(cfg: dict, paths: list[Path]) -> list[dict]:
    """Ordena candidatas por P(idioma) y WER contra el texto de referencia."""
    whisper, lang, report = load("whisper"), cfg["voice"]["whisper_lang"], []
    perfil = {**PERFIL, **cfg["voice"].get("perfil", {})}
    for path in paths:
        heard, words = transcribe(whisper, path, lang)
        habla = (words[-1]["end"] - words[0]["start"]) if words else 0.0
        report.append({"file": str(path), "p_lang": p_lang(whisper, path, lang),
                       "wer": round(texto.wer(cfg["voice"]["ref_text"], heard), 3),
                       "f0_hz": f0_mediana(path),
                       "words_per_s": round(len(words) / habla, 2) if habla else 0.0,
                       "heard": heard})
    for row in report:
        row["fuera_de_perfil"] = [
            k for k, rango in perfil.items() if _fuera(row.get(k, 0.0), rango)]
        # La receta pide las cuatro cosas: idioma, fidelidad, tono y ritmo.
        row["ok"] = (row["p_lang"] >= cfg["gates"]["ref_min_p_lang"] and row["wer"] <= 0.1
                     and not row["fuera_de_perfil"])
    # Primero las que cumplen el perfil; dentro de cada grupo, por P(idioma) y WER.
    report.sort(key=lambda r: (bool(r["fuera_de_perfil"]), -r["p_lang"], r["wer"]))
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
        fuera = (" ⚠ fuera de perfil: " + ", ".join(row["fuera_de_perfil"])
                 if row["fuera_de_perfil"] else "")
        print(f"{'✓' if row['ok'] else '✗'} {row['file']}  P={row['p_lang']:.4f}  "
              f"WER={row['wer']:.3f}  f0={row['f0_hz']:.0f}Hz  "
              f"{row['words_per_s']:.1f} pal/s{fuera}")
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
        # semilla fija por voz (la receta aprobada usa la misma en todas las líneas)
        torch.manual_seed(voice.get("seed", 4242) + 1000 * attempt)
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
    """Frames cuyo WAV crudo, ya sin la frase filtrada, supera el WER máximo o esconde habla
    (función aparte: libera Whisper al volver)."""
    whisper, failing, lang = load("whisper"), [], cfg["voice"]["whisper_lang"]
    for frame in frames:
        raw = VOICE_DIR / f"{frame:02d}.raw.wav"
        _, words = transcribe(whisper, raw, lang)
        start = inicio_linea(words, script[frame], cfg["voice"].get("ref_text", ""))
        # Se mide sobre la toma ya recortada y vuelta a transcribir: en la cruda Whisper puede
        # fundir la frase filtrada con el inicio real de la línea y las palabras no alcanzan.
        check = VOICE_DIR / f"{frame:02d}.check.wav"
        medios.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.3f}", "-i", str(raw),
                    str(check)])
        heard, words = transcribe(whisper, check, lang)
        motivos = revisar_habla(words, silencios(check))
        check.unlink()
        score = texto.wer_respell(script[frame], heard, cfg.get("respell", {}))
        if score > cfg["gates"]["max_wer"] or motivos:
            print(f"  ↻ frame {frame}: WER {score:.3f} {'; '.join(motivos)} → otra semilla\n"
                  f"      oído: {heard}", flush=True)
            failing.append(frame)
    return failing


def _comparables(words: list[dict]) -> list[tuple[str, int]]:
    """(palabra normalizada, índice en words), sin las que no tienen letras ni números."""
    pares = [(" ".join(texto.normalize(w["text"])), i) for i, w in enumerate(words)]
    return [(p, i) for p, i in pares if p]


def _antes_de(words: list[dict], idx: int, borde: float) -> float:
    """Segundo de corte antes de words[idx]: un borde de aire sin meterse en la palabra previa."""
    start = words[idx]["start"]
    if not idx:
        return max(start - borde, 0.0)
    return max(min(words[idx - 1]["end"] + MARGEN_FUGA_S, start), start - borde)


def _tras_fuga(words: list[dict], pares: list[tuple[str, int]], linea: str,
               ref_text: str) -> float | None:
    """Segundo justo después de la frase filtrada, o None si la toma no empieza con ella.

    Si la línea empieza con esa misma frase, solo se corta cuando hay prueba de la segunda
    copia: queda la línea completa detrás, o Whisper fundió las dos copias en una y dejó un
    hueco largo donde está la segunda. Sin esa prueba la toma salió sin filtración y cortar le
    quitaría su comienzo.
    """
    frases = [f for f in re.split(r"[.!?…]+", ref_text) if texto.normalize(f)]
    cola = texto.normalize(frases[-1]) if frases else []
    oidas = [p for p, _ in pares]
    if not cola or len(oidas) <= len(cola) or texto.wer(
            " ".join(cola), " ".join(oidas[:len(cola)])) > 0.2:
        return None
    fin, sig = words[pares[len(cola) - 1][1]]["end"], words[pares[len(cola)][1]]["start"]
    resto = " ".join(w["text"] for w in words[pares[len(cola)][1]:])
    todo = " ".join(w["text"] for w in words)
    if sig - fin > HUECO_MAX_S or texto.wer(linea, resto) <= texto.wer(linea, todo):
        return min(fin + MARGEN_FUGA_S, sig)
    return None


def inicio_linea(words: list[dict], linea: str, ref_text: str, borde: float = 0.12) -> float:
    """Segundo donde cortar la toma cruda para que empiece la línea real.

    1. Si la toma empieza con la última frase de ref_text (la que el clon arrastra), justo
       después de ella (ver _tras_fuga).
    2. Si no, antes de la primera aparición de las tres primeras palabras de la línea.
    3. Si no, antes de la primera palabra.
    """
    if not words:
        return 0.0
    pares = _comparables(words)
    fuga = _tras_fuga(words, pares, linea, ref_text) if pares else None
    if fuga is not None:
        return fuga
    oidas, clave = [p for p, _ in pares], texto.normalize(linea)[:3]
    for pos in range(len(oidas) - len(clave) + 1):
        if clave and oidas[pos:pos + len(clave)] == clave:
            return _antes_de(words, pares[pos][1], borde)
    return _antes_de(words, 0, borde)


def silencios(path: Path) -> list[tuple[float, float]]:
    """Tramos de silencio del archivo según ffmpeg silencedetect."""
    err = medios.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", SILENCIO,
                      "-f", "null", "-"]).stderr
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    if len(ends) < len(starts):  # termina en silencio: ffmpeg no imprime el final
        ends.append(medios.duration(path))
    return list(zip(starts, ends))


def _silencio_en(tramos: list[tuple[float, float]], ini: float, fin: float) -> float:
    """Segundos de silencio dentro de [ini, fin]."""
    return sum(max(0.0, min(fin, b) - max(ini, a)) for a, b in tramos)


def revisar_habla(words: list[dict], tramos: list[tuple[float, float]]) -> list[str]:
    """Habla que Whisper no transcribió: motivos para revisar la línea (vacío = bien).

    Marca cada hueco > HUECO_MAX_S entre palabras que no es mayormente silencio, y un ritmo por
    segundo de voz menor que MIN_PAL_POR_S. Ambos delatan una frase repetida que Whisper oyó una
    sola vez (el WER queda en 0).
    """
    motivos = []
    for prev, cur in zip(words, words[1:]):
        hueco = cur["start"] - prev["end"]
        if hueco > HUECO_MAX_S and _silencio_en(tramos, prev["end"], cur["start"]) < hueco / 2:
            motivos.append(f"hueco de {hueco:.1f} s con voz sin transcribir "
                           f"({prev['end']:.1f}–{cur['start']:.1f} s)")
    if words:
        ini, fin = words[0]["start"], words[-1]["end"]
        voz = fin - ini - _silencio_en(tramos, ini, fin)
        ritmo = len(words) / voz if voz > 0 else 0.0
        if ritmo < MIN_PAL_POR_S:
            motivos.append(f"ritmo {ritmo:.1f} pal/s de voz (< {MIN_PAL_POR_S}): "
                           "habla sin transcribir")
    return motivos


def trim_and_pad(cfg: dict, frame: int, words: list[dict], meta: dict) -> tuple[float, float]:
    """NN.raw.wav → NN.wav: recorte al habla real (sin la frase filtrada de la referencia),
    −18 LUFS, 48 kHz y pausas; devuelve (recorte, pausa)."""
    pads = cfg["pads"]
    raw = VOICE_DIR / f"{frame:02d}.raw.wav"
    edge = pads.get("edge_s", 0.12)
    start = inicio_linea(words, meta["script"][frame], cfg["voice"].get("ref_text", ""), edge)
    end = words[-1]["end"] + edge * 2 if words else medios.duration(raw)
    head = pads["first_head_s"] if frame == meta["first"] else 0.0
    tail = pads["last_tail_s"] if frame == meta["last"] else pads["tail_s"]
    chain = (f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11,"
             f"adelay=delays={int(head * 1000)}:all=1,apad=pad_dur={tail}")
    # -ss/-to como opciones de ENTRADA: como opciones de salida también cortarían el relleno.
    medios.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.3f}", "-to",
                f"{end:.3f}", "-i", str(raw), "-af", chain, "-ar", str(SAMPLE_RATE), "-ac", "1",
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
            "revisar": revisar_habla(words, silencios(final)),
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
        passed = (line["wer"] <= gates["max_wer"] and line["p_lang"] >= gates["min_p_lang"]
                  and not line["revisar"])
        print(f"  {'OK ' if passed else 'REV'} {frame:02d} {line['duration_s']:6.2f}s "
              f"WER={line['wer']:.3f} P={line['p_lang']:.4f}", flush=True)
        if not passed:
            bad.append(frame)
            print(f"      esperado: {script[frame]}\n      oído:     {heard}")
            for motivo in line["revisar"]:
                print(f"      revisar:  {motivo}")
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
                           "respell en audio.json)" if bad else "`./vl musica <pista> --licencia \"…\"` (opcional) y las escenas"))
    return 1 if bad else 0


def chosen_voice(cfg: dict) -> Path:
    """Voz de referencia elegida por el usuario (biblioteca o audio.json → voice.ref_audio)."""
    choice = cfg["voice"].get("ref_audio")
    if not choice or not Path(choice).exists():
        sys.exit("✗ 🛑 falta la voz elegida: pon audio.json → voice.library con una voz de "
                 f"{voces_dir()}, o el usuario escucha las candidatas de `./vl voz design` y "
                 "pones su ruta en voice.ref_audio")
    return Path(choice)


def voces_dir() -> Path:
    """Carpeta de la biblioteca de voces ($VL_VOCES o ~/.config/video-web/voces)."""
    return Path(os.environ.get("VL_VOCES", VOCES_DEFAULT)).expanduser()


def resolve_voice(voice: dict) -> dict:
    """Con voice.library, toma ref_audio, ref_text y semilla de la biblioteca."""
    name = voice.get("library")
    if not name:
        return voice
    folder = voces_dir() / name
    if not (folder / "voz.json").exists():
        sys.exit(f"✗ no existe la voz «{name}» en {voces_dir()} (falta voz.json). Disponibles: "
                 f"{', '.join(sorted(p.parent.name for p in voces_dir().glob('*/voz.json')))}")
    entry = json.loads((folder / "voz.json").read_text(encoding="utf-8"))
    resolved = dict(voice, ref_audio=str(folder / entry.get("ref_wav", "ref.wav")),
                    ref_text=entry["ref_text"])
    if "semilla" in entry:
        resolved["seed"] = entry["semilla"]
    return resolved


def cmd_guardar(voice: dict, nombre: str, desde: str, texto_ref: str) -> int:
    """Guarda la voz (ref.wav + voz.json) en la biblioteca para reusarla en otros videos."""
    ref, ref_text = Path(desde or voice.get("ref_audio") or ""), texto_ref or voice.get("ref_text")
    if not ref.is_file() or not ref_text:
        sys.exit("✗ falta la voz: pasa --desde ruta.wav y --texto, o completa voice.ref_audio y "
                 "voice.ref_text en audio.json")
    folder = voces_dir() / nombre
    if folder.exists():  # no pisar una voz aprobada
        sys.exit(f"✗ ya existe {folder}: elige otro nombre o bórrala a mano")
    folder.mkdir(parents=True)
    shutil.copyfile(ref, folder / "ref.wav")
    entry = {"nombre": nombre, "ref_wav": "ref.wav", "ref_text": ref_text,
             "semilla": voice.get("seed", 4242), "procedencia": str(ref.resolve())}
    (folder / "voz.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
    print(f"✓ voz guardada en {folder}. Úsala con audio.json → voice.library: \"{nombre}\"")
    return 0


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


def claves_usadas(cfg: dict, cmd: str) -> dict:
    """La parte de audio.json que el subcomando usa: con voice.library (salvo en design) la
    referencia sale de la biblioteca, así que ref_text e instructs pueden seguir con marcadores."""
    if not cfg["voice"].get("library") or cmd == "design":
        return cfg
    voz = {k: v for k, v in cfg["voice"].items() if k not in ("ref_text", "instructs")}
    return dict(cfg, voice=voz)


def run() -> int:
    """Interpreta argumentos y despacha el subcomando."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("design").add_argument("--n", type=int, default=3)
    sub.add_parser("lines").add_argument("--frames", default="")
    sub.add_parser("finalize")
    guardar = sub.add_parser("guardar")
    guardar.add_argument("nombre")
    guardar.add_argument("--desde", default="")
    guardar.add_argument("--texto", default="")
    args = parser.parse_args()
    cfg = json.loads(Path("audio.json").read_text(encoding="utf-8"))
    if re.search(r"<[A-ZÁÉÍÓÚÑ_ ]{3,}>", json.dumps(claves_usadas(cfg, args.cmd),
                                                    ensure_ascii=False)):
        sys.exit("✗ audio.json aún tiene marcadores <...>: complétalo (references/oficio.md § Voz)")
    if args.cmd == "guardar":
        return cmd_guardar(cfg["voice"], args.nombre, args.desde, args.texto)
    if args.cmd == "design":
        return cmd_design(cfg, args.n)
    cfg["voice"] = resolve_voice(cfg["voice"])
    if args.cmd == "lines":
        return cmd_lines(cfg, chosen_voice(cfg), {int(f) for f in args.frames.split(",") if f})
    return cmd_finalize(cfg)


if __name__ == "__main__":
    sys.exit(main())
