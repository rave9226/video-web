"""Utilidades de texto: guion, storyboard, WER y respelling.

Solo stdlib, sin estado: las usan tanto el venv general como el de Qwen3-TTS.
"""
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


def wer(expected: str, heard: str) -> float:
    """Tasa de error por palabra (distancia de edición / palabras esperadas)."""
    ref, hyp = normalize(expected), normalize(heard)
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
    """Frontmatter YAML plano (clave: valor) de BRIEF.md / STORYBOARD.md."""
    match = re.match(r"^---\n(.*?)\n---", md, re.DOTALL)
    if not match:
        return {}
    out = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip().strip('"')
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
