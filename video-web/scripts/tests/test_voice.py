"""Pruebas de voice.py: recorte de la frase filtrada y detector de habla oculta (sin GPU)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import voice  # pylint: disable=import-error,wrong-import-position

REF_TEXT = ("Define el alcance. Ese archivo será la única referencia durante todo el ejercicio. "
            "Pide un resumen que use exclusivamente el archivo adjunto.")
COLA = "Pide un resumen que use exclusivamente el archivo adjunto."
LINEA_6 = (COLA + " Solicita el fragmento que respalda cada afirmación importante. Separa los "
           "datos confirmados de los supuestos y la información ausente.")
LINEA_5 = ("En Claude, abre una conversación y adjunta un informe breve de práctica. Define el "
           "alcance: ese archivo será la única referencia durante todo el ejercicio.")


def palabras(texto: str, inicio: float = 0.0, paso: float = 0.35) -> list[dict]:
    """Palabras con tiempos regulares a partir de un segundo dado."""
    return [{"text": w, "start": round(inicio + i * paso, 3),
             "end": round(inicio + i * paso + paso - 0.05, 3)}
            for i, w in enumerate(texto.split())]


def test_fuga_y_linea_con_la_misma_frase_corta_tras_la_primera_copia():
    """La falla real: la línea empieza con la frase filtrada y Whisper oyó las dos copias."""
    fuga = palabras(COLA)
    linea = palabras(LINEA_6, inicio=fuga[-1]["end"] + 0.4)
    corte = voice.inicio_linea(fuga + linea, LINEA_6, REF_TEXT)
    assert fuga[-1]["end"] < corte <= linea[0]["start"]


def test_fuga_fundida_por_whisper_corta_tras_la_frase():
    """Whisper oyó una sola copia y dejó un hueco de 3,7 s: el corte deja la segunda copia."""
    words = palabras(COLA) + palabras(LINEA_6.replace(COLA, ""), inicio=6.96)
    corte = voice.inicio_linea(words, LINEA_6, REF_TEXT)
    assert words[8]["end"] < corte < 3.5


def test_sin_fuga_no_le_quita_el_comienzo_a_la_linea():
    """Toma limpia de una línea que empieza con la frase de la referencia: no se recorta."""
    words = palabras(LINEA_6, inicio=0.3)
    assert voice.inicio_linea(words, LINEA_6, REF_TEXT) == 0.3 - 0.12


def test_fuga_ante_otra_linea_corta_tras_la_frase():
    """Caso común (línea 5): fuga con puntuación y mayúsculas distintas, línea diferente."""
    fuga = palabras("pide un resumen que use exclusivamente el archivo adjunto,")
    linea = palabras(LINEA_5, inicio=fuga[-1]["end"] + 0.06)
    corte = voice.inicio_linea(fuga + linea, LINEA_5, REF_TEXT)
    assert fuga[-1]["end"] <= corte <= linea[0]["start"]


def test_sin_frase_filtrada_busca_las_tres_primeras_palabras():
    """Basura al inicio que no es la frase filtrada: corta antes de la línea."""
    basura = palabras("bueno este")
    linea = palabras(LINEA_5, inicio=2.0)
    corte = voice.inicio_linea(basura + linea, LINEA_5, REF_TEXT)
    assert basura[-1]["end"] <= corte < linea[0]["start"]


def test_sin_coincidencia_usa_la_primera_palabra():
    """Nada coincide: borde antes de la primera palabra, nunca negativo."""
    assert voice.inicio_linea(palabras("algo distinto", 0.05), LINEA_5, REF_TEXT) == 0.0
    assert voice.inicio_linea([], LINEA_5, REF_TEXT) == 0.0


def test_hueco_con_voz_sin_transcribir_se_marca():
    """La falla real: 3,7 s sin palabras que silencedetect muestra como voz."""
    words = palabras(COLA) + palabras(LINEA_6.replace(COLA, ""), inicio=3.1 + 3.7)
    hueco = (words[8]["end"], words[9]["start"])
    motivos = voice.revisar_habla(words, [(hueco[0], hueco[0] + 0.3)])
    assert any("hueco de 3.7 s" in m for m in motivos)


def test_hueco_de_silencio_real_no_se_marca():
    """Una pausa larga que sí es silencio no es habla oculta."""
    words = palabras(COLA, paso=0.3) + palabras("Solicita el fragmento", inicio=4.2, paso=0.3)
    assert voice.revisar_habla(words, [(2.65, 4.2)]) == []


def test_ritmo_lento_por_segundo_de_voz_se_marca():
    """Pocas palabras para el tiempo con voz delatan habla sin transcribir."""
    lentas = palabras("una dos tres cuatro", paso=0.9)
    assert any("ritmo" in m for m in voice.revisar_habla(lentas, []))
    assert voice.revisar_habla(palabras(LINEA_6), []) == []


def test_biblioteca_de_voces(tmp_path, monkeypatch):
    """voice.library toma ref.wav, ref_text y semilla de $VL_VOCES/<nombre>/voz.json."""
    carpeta = tmp_path / "instructora"
    carpeta.mkdir()
    (carpeta / "voz.json").write_text(json.dumps(
        {"ref_wav": "ref.wav", "ref_text": REF_TEXT, "semilla": 7242}), encoding="utf-8")
    monkeypatch.setenv("VL_VOCES", str(tmp_path))
    voz = voice.resolve_voice({"library": "instructora", "ref_text": "<X>", "seed": 4242})
    assert voz["ref_audio"] == str(carpeta / "ref.wav")
    assert (voz["ref_text"], voz["seed"]) == (REF_TEXT, 7242)
    assert voice.resolve_voice({"ref_audio": "a.wav"}) == {"ref_audio": "a.wav"}


def test_guardar_y_reusar(tmp_path, monkeypatch):
    """guardar copia la voz elegida a la biblioteca y luego se carga por nombre."""
    ref = tmp_path / "elegida.wav"
    ref.write_bytes(b"RIFF")
    monkeypatch.setenv("VL_VOCES", str(tmp_path / "voces"))
    assert voice.cmd_guardar({"ref_audio": str(ref), "ref_text": REF_TEXT, "seed": 7}, "nueva",
                             "", "") == 0
    voz = voice.resolve_voice({"library": "nueva"})
    assert Path(voz["ref_audio"]).read_bytes() == b"RIFF"
    assert (voz["ref_text"], voz["seed"]) == (REF_TEXT, 7)


def test_marcadores_ignorados_con_biblioteca():
    """Con voice.library, el ref_text de plantilla no bloquea lines/finalize; sin ella, sí."""
    cfg = {"voice": {"library": "x", "ref_text": "<FRASE DE REFERENCIA>", "instructs": {}}}
    assert "ref_text" not in voice.claves_usadas(cfg, "lines")["voice"]
    assert voice.claves_usadas(cfg, "design") is cfg
    assert voice.claves_usadas({"voice": {"ref_text": "<X>"}}, "lines")["voice"]["ref_text"]
