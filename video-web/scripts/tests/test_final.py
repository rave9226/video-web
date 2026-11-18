"""Pruebas de final.py: envolvente de la música, subtítulos y tiempos de escena."""
import sys
from pathlib import Path

import numpy as np  # pylint: disable=import-error

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import final  # noqa: E402  # pylint: disable=import-error,wrong-import-position


def db_en(gain: np.ndarray, t: float) -> float:
    """Nivel en dB de la envolvente en el segundo t."""
    return 20 * np.log10(gain[int(t * final.RATE)])


def test_tramos_une_pausas_cortas():
    """Pausas < 0.9 s se unen; más largas abren otro tramo."""
    assert final.tramos([(0, 1), (1.5, 2), (3.0, 4)]) == [[0, 2], [3.0, 4]]


def test_envolvente_niveles():
    """Portada plena, baja bajo la voz, +6 en pausa, +9 en cambio de sección, fundido final."""
    spans = [[3, 6], [10, 13], [20, 23]]
    gain = final.envolvente(30, spans, secciones=[18], bajo_db=-20)
    assert abs(db_en(gain, 1) - (-8)) < 0.1      # antes de la primera palabra: +12
    assert abs(db_en(gain, 4.5) - (-20)) < 0.1   # hablando
    assert abs(db_en(gain, 8) - (-14)) < 0.1     # pausa ordinaria: +6
    assert abs(db_en(gain, 16.5) - (-11)) < 0.1  # pausa con cambio de sección: +9
    assert abs(db_en(gain, 26) - (-11)) < 0.1    # cierre tras la última palabra
    assert gain[-1] < 1e-3                        # fundido a silencio
    # rampas: no hay saltos bruscos entre muestras vecinas
    assert np.max(np.abs(np.diff(20 * np.log10(gain[: 27 * final.RATE])))) < 0.1


def test_lineas_max_dos_de_42():
    """Corta en dos líneas parejas de ≤ 42 caracteres; None si no cabe en dos."""
    assert final.lineas(["hola"]) == ["hola"]
    dos = final.lineas(("palabra " * 9).split())
    assert len(dos) == 2 and all(len(x) <= 42 for x in dos)
    assert final.lineas(("palabra " * 12).split()) is None


def palabras(texto: str, paso: float = 0.3) -> list[dict]:
    """Palabras seguidas con tiempos regulares."""
    return [{"t": w, "s": i * paso, "e": i * paso + 0.25} for i, w in enumerate(texto.split())]


def test_frases_cierran_en_oracion_y_respetan_limites():
    """Cada oración cierra su subtítulo y ninguno pasa de 2 líneas de 42."""
    words = palabras("Hola mundo. " + "una frase bastante larga que no cabe " * 3 + "fin.")
    grupos = final.frases(words)
    assert [w["t"] for w in grupos[0]] == ["Hola", "mundo."]
    assert grupos[-1][-1]["t"] == "fin."
    for g in grupos:
        lineas = final.lineas([w["t"] for w in g])
        assert lineas and len(lineas) <= 2 and all(len(x) <= 42 for x in lineas)
    # una oración larga se reparte pareja: sin una palabra suelta al final
    largo = final.frases(palabras("Imagina un redactor que propone cómo continuar una frase "
                                  "a partir de lo aprendido."))
    assert len(largo) == 2 and min(len(g) for g in largo) >= 4


def test_palabras_video_usa_ortografia_del_guion():
    """«cero» del guion reemplaza el «0.» de Whisper; si no cuadra, queda Whisper."""
    linea1 = [{"text": "Módulo", "start": 0, "end": 0.5}, {"text": "0.", "start": 0.5, "end": 0.8}]
    voces = [{"frame": 1, "t0": 10.0, "words": linea1},
             {"frame": 2, "t0": 20.0, "words": [{"text": "Hola", "start": 0, "end": 0.4}]}]
    out, whisper = final.palabras_video(voces, {1: "Módulo cero.", 2: "Hola de nuevo"})
    assert [w["t"] for w in out] == ["Módulo", "cero.", "Hola"]
    assert out[1]["s"] == 10.5 and whisper == [2]


def test_vtt_formato():
    """Cabecera WEBVTT y marcas HH:MM:SS.mmm sin solaparse."""
    grupos = final.frases(palabras("Uno dos. Tres cuatro."))
    txt = final.vtt(grupos)
    assert txt.startswith("WEBVTT\n\n1\n00:00:00.000 --> ")
    assert final.marca(3725.5) == "01:02:05.500"


def test_desfase_y_respaldo_de_inicios():
    """data-start de la voz (0 si falta) y inicios por duración menos la transición."""
    s1 = ('<section id="s1" data-duration="14.43"><audio src="assets/voz/01.wav" '
          'data-start="0.8"></audio><audio src="assets/sfx/pop.mp3" data-start="8"></audio>')
    s2 = '<section id="s2" data-duration="10"><audio src="assets/voz/02.wav"></audio>'
    assert final.desfase_voz(s1, "assets/voz/01.wav") == 0.8
    assert final.desfase_voz(s2, "assets/voz/02.wav") == 0
    assert final.desfase_voz(s2, "assets/voz/09.wav") is None
    video = ('<main data-sequence data-transition="push-left 0.6 in-out-cubic">'
             '<gm-include src="scenes/s01.html"></gm-include>'
             '<gm-include src="scenes/s02.html"></gm-include></main>')
    assert final.escenas(video) == ["scenes/s01.html", "scenes/s02.html"]
    assert final.inicios_duracion(video, [s1, s2]) == [0.0, 13.83]
    voces = final.ubicar_voces([{"frame": 2, "path": "assets/voz/02.wav", "words": []}],
                               [s1, s2], [0.0, 13.83])
    assert voces[0]["escena"] == 2 and voces[0]["t0"] == 13.83
