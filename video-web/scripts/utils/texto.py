"""Utilidades de texto: guion, storyboard, WER y respelling.

Solo stdlib, sin estado: las usan tanto el venv general como el de Qwen3-TTS.
"""
import hashlib
import re
import unicodedata

FRAME_HEAD = re.compile(r"^#{2,3}\s+.*?\(frame\s+(\d+)\)", re.IGNORECASE)
SPOKEN = re.compile(r"^(?: {4,}|\t)(.+)$")
STORY_FRAME = re.compile(r"^## Frame\s+(\d+)\s*[—–-]?\s*(.*)$", re.MULTILINE)
FIELD = re.compile(r"^-\s+([\w-]+):\s*(.*)$")
EN_STOPWORDS = {"the", "and", "with", "voice", "she", "her", "speaks", "narrator", "female",
                "male", "warm", "clear", "accent", "pace", "tone", "of", "in", "a", "is"}


def parse_script(md: str) -> dict[int, str]:
    """SCRIPT.md → {frame: texto hablado}. Mismo criterio que product-launch-video."""
    lines: dict[int, str] = {}
    current = None
    for raw in md.splitlines():
        head = FRAME_HEAD.match(raw)
        if head:
            current = int(head.group(1))
            lines[current] = ""
            continue
        spoken = SPOKEN.match(raw)
        if current is not None and spoken and not raw.lstrip().startswith("**"):
            lines[current] = (lines[current] + " " + spoken.group(1).strip()).strip()
    return {frame: text for frame, text in lines.items() if text}


CJK = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")


def normalize(text: str) -> list[str]:
    """Minúsculas, sin tildes ni puntuación: lista de unidades comparables.

    Sirve para cualquier alfabeto; en chino y japonés (sin espacios) cada carácter cuenta como
    una unidad, así que el "WER" es en realidad CER.
    """
    plain = unicodedata.normalize("NFKD", text.lower())
    plain = unicodedata.normalize("NFC", "".join(c for c in plain
                                                 if not unicodedata.combining(c)))
    units = []
    for word in re.findall(r"[^\W_]+", plain):
        units += list(word) if CJK.search(word) else [word]
    return units


UNIDADES = {"cero": 0, "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4,
            "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11,
            "doce": 12, "trece": 13, "catorce": 14, "quince": 15, "dieciseis": 16,
            "diecisiete": 17, "dieciocho": 18, "diecinueve": 19, "veinte": 20, "veintiun": 21,
            "veintiuno": 21, "veintiuna": 21, "veintidos": 22, "veintitres": 23,
            "veinticuatro": 24, "veinticinco": 25, "veintiseis": 26, "veintisiete": 27,
            "veintiocho": 28, "veintinueve": 29}
DECENAS = {"treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70,
           "ochenta": 80, "noventa": 90}
CENTENAS = {"cien": 100, "ciento": 100, **{f"{p}{g}": v for p, v in (
    ("doscient", 200), ("trescient", 300), ("cuatrocient", 400), ("quinient", 500),
    ("seiscient", 600), ("setecient", 700), ("ochocient", 800), ("novecient", 900))
    for g in ("os", "as")}}


def _un_numero(palabras: list[str], i: int) -> tuple[int, int]:
    """(valor, palabras usadas) del número en letras que empieza en palabras[i]; (0, 0) si no.

    Cardinales en español hasta los millones: «ciento cuarenta y ocho», «dos mil veinticinco».
    """
    total, grupo, nivel, j = 0, 0, 0, i  # nivel: 0 inicio, 1 centena, 2 decena, 3 unidad
    while j < len(palabras):
        pal = palabras[j]
        sig = palabras[j + 1] if j + 1 < len(palabras) else ""
        if pal in CENTENAS and nivel == 0 and grupo == 0 and \
                not (pal == "ciento" and i and palabras[i - 1] == "por"):  # «por ciento»
            grupo, nivel = CENTENAS[pal], 1
        elif pal in DECENAS and nivel < 2:
            grupo, nivel = grupo + DECENAS[pal], 2
        elif pal == "y" and nivel == 2 and 1 <= UNIDADES.get(sig, 0) <= 9:
            grupo, nivel, j = grupo + UNIDADES[sig], 3, j + 1
        elif pal in UNIDADES and nivel < 2:
            grupo, nivel = grupo + UNIDADES[pal], 3
        elif pal == "mil" and total % 1_000_000 == 0:
            total, grupo, nivel = total + (grupo or 1) * 1000, 0, 0
        elif pal in ("millon", "millones"):
            total, grupo, nivel = (total + (grupo or 1)) * 1_000_000, 0, 0
        else:
            break
        j += 1
    return total + grupo, j - i


def numeros_a_cifras(palabras: list[str]) -> list[str]:
    """Números en letras → cifras, y «coma» entre dos cifras fuera, para comparar guion y oído.

    El guion dice los números en letras (así los lee bien el TTS) y Whisper los escribe en
    cifras: «ciento cuarenta y ocho» frente a «148» daba WER alto en líneas sanas."""
    out, i = [], 0
    while i < len(palabras):
        valor, usadas = _un_numero(palabras, i)
        out.append(str(valor) if usadas else palabras[i])
        i += usadas or 1
    return [p for k, p in enumerate(out) if not (
        p in ("coma", "punto") and 0 < k < len(out) - 1
        and out[k - 1].isdigit() and out[k + 1].isdigit())]


def comparables(text: str) -> list[str]:
    """Unidades para el WER: normalize() con los números en cifras.

    «1.500» se une en «1500» y «%» se lee «por ciento», como lo dice el guion."""
    text = re.sub(r"(?<=\d)[.,](?=\d{3}\b)", "", text).replace("%", " por ciento")
    return numeros_a_cifras(normalize(text))


def huella(text: str) -> str:
    """Huella corta del texto de una línea: si cambia, su voz quedó vieja."""
    return hashlib.sha1(" ".join(text.split()).encode("utf-8")).hexdigest()[:12]


def wer(expected: str, heard: str) -> float:
    """Tasa de error por palabra (distancia de edición / palabras esperadas)."""
    ref, hyp = comparables(expected), comparables(heard)
    row = list(range(len(hyp) + 1))
    for i, word in enumerate(ref, 1):
        prev, row[0] = row[0], i
        for j, cand in enumerate(hyp, 1):
            prev, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, prev + (word != cand))
    return row[-1] / max(len(ref), 1)


def respell(text: str, mapping: dict[str, str]) -> str:
    """Aplica la pronunciación forzada (solo para la entrada del TTS)."""
    for written, spoken in mapping.items():
        text = text.replace(written, spoken)
    return text


def english_ratio(text: str) -> float:
    """Proporción de palabras funcionales inglesas: detecta instructs escritos en inglés."""
    words = normalize(text)
    return sum(w in EN_STOPWORDS for w in words) / max(len(words), 1)


def parse_frontmatter(md: str) -> dict[str, str]:
    """Frontmatter YAML plano (clave: valor) de BRIEF.md, sin los comentarios ` # …`."""
    match = re.match(r"^---\n(.*?)\n---", md, re.DOTALL)
    if not match:
        return {}
    out = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            # la plantilla de BRIEF.md explica cada campo con un comentario en la misma línea:
            # sin quitarlo, `formato: explicativo # para qué…` no era un formato válido
            value = value.strip()
            if not value.startswith('"'):
                value = re.sub(r"\s+#.*$", "", value)
            out[key.strip()] = value.strip('"')
    return out


def split_frames(storyboard: str) -> list[dict]:
    """STORYBOARD.md → [{number, title, block, fields}]."""
    heads = list(STORY_FRAME.finditer(storyboard))
    frames = []
    for idx, head in enumerate(heads):
        end = heads[idx + 1].start() if idx + 1 < len(heads) else len(storyboard)
        block = storyboard[head.start():end]
        fields = {}
        for line in block.splitlines()[1:]:
            match = FIELD.match(line)
            if match:
                fields.setdefault(match.group(1), match.group(2).strip())
        frames.append({"number": int(head.group(1)), "title": head.group(2).strip(),
                       "block": block, "fields": fields})
    return frames


def seconds(value: str) -> float:
    """'2:40', '160s', '2-3 min', '150' → segundos (rango → punto medio)."""
    text = value.strip().lower()
    clock = re.match(r"^(\d+):(\d{2})$", text)
    if clock:
        return int(clock.group(1)) * 60 + int(clock.group(2))
    nums = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", text)]
    if not nums:
        raise ValueError(f"duración no reconocida: {value!r}")
    mid = sum(nums) / len(nums)
    return mid * 60 if "min" in text else mid


def wer_respell(expected: str, heard: str, spell: dict) -> float:
    """WER contra el texto original o el respelleado, el menor: Whisper suele oír la ortografía
    real ("Books"), pero a veces transcribe la forma fonética ("Uómpi")."""
    return min(wer(expected, heard), wer(respell(expected, spell), heard))


def asset_names(value: str) -> list[str]:
    """asset_candidates 'assets/a.png — desc; assets/b.png — desc' → ['a.png', 'b.png']."""
    names = []
    for seg in value.split(";"):
        path = re.split(r"\s+[—–-]\s+", seg.strip())[0].strip()
        if path and "." in path:  # "ninguno" u otra nota no es un archivo
            names.append(path.split("/")[-1])
    return names
