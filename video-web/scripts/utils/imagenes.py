"""Helpers de imagen (PIL + numpy): vacías, variante blanca, recorte de tarjetas y hojas.

Sin estado ni lógica de negocio. Requiere el venv general (Pillow y numpy).
"""
from pathlib import Path

import numpy as np  # pylint: disable=import-error
from PIL import Image, ImageDraw, ImageFont  # pylint: disable=import-error

FONT_PATHS = ("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")


def gray_std(path: Path) -> float:
    """Variación de grises (o de alfa, para logos sobre transparencia): < 6 = vacía."""
    with Image.open(path) as img:
        bands = [img.convert("L")] + ([img.getchannel("A")] if "A" in img.getbands() else [])
        return max(float(np.asarray(band, dtype=np.float32).std()) for band in bands)


def mean_abs_diff(path_a: Path, path_b: Path) -> float:
    """Diferencia media absoluta (0–1) entre dos imágenes del mismo tamaño."""
    with Image.open(path_a) as img_a, Image.open(path_b) as img_b:
        arr_a = np.asarray(img_a.convert("L").resize((480, 270)), dtype=np.float32)
        arr_b = np.asarray(img_b.convert("L").resize((480, 270)), dtype=np.float32)
    return float(np.abs(arr_a - arr_b).mean() / 255)


def white_variant(src: Path, dst: Path) -> None:
    """Misma silueta en blanco (para logos sobre fondo oscuro); conserva el alfa."""
    with Image.open(src) as img:
        rgba = img.convert("RGBA")
    white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    white.putalpha(rgba.getchannel("A"))
    white.save(dst)


def card_box(path: Path, pad_ratio: float = 0.012) -> tuple[int, int, int, int]:
    """Caja (x0, y0, x1, y1) de la tarjeta blanca centrada de una página pública."""
    with Image.open(path) as img:
        arr = np.asarray(img.convert("RGB")).astype(int)
    white = arr.min(axis=2) >= 253
    height, width = white.shape
    xs = np.where(white.sum(axis=0) > height * 0.25)[0]
    ys = np.where(white.sum(axis=1) > width * 0.12)[0]
    if xs.size == 0 or ys.size == 0:
        raise ValueError(f"no se detectó una tarjeta blanca en {path}")
    pad = int(pad_ratio * width)
    return (max(int(xs.min()) - pad, 0), max(int(ys.min()) - pad, 0),
            min(int(xs.max()) + pad, width), min(int(ys.max()) + pad, height))


def _font(size: int):
    for candidate in FONT_PATHS:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


THUMB, COLS, LABEL_H = (576, 360), 4, 30


def _sheet(chunk: list[Path], font) -> Image.Image:
    """Una hoja de 4 columnas con nombre y tamaño de cada imagen."""
    rows = (len(chunk) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * THUMB[0], rows * (THUMB[1] + LABEL_H)), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, path in enumerate(chunk):
        with Image.open(path) as img:
            size = img.size
            rgba = img.convert("RGBA")
        # Gris neutro bajo la transparencia: logos blancos y oscuros quedan visibles.
        small = Image.new("RGBA", rgba.size, (128, 128, 128, 255))
        small.alpha_composite(rgba)
        small = small.convert("RGB")
        small.thumbnail(THUMB)
        x, y = (idx % COLS) * THUMB[0], (idx // COLS) * (THUMB[1] + LABEL_H)
        sheet.paste(small, (x, y + LABEL_H))
        draw.text((x + 6, y + 4), f"{path.name} {size[0]}x{size[1]}", fill="black", font=font)
    return sheet


def contact_sheets(paths: list[Path], out_prefix: Path, per_sheet: int = 12) -> list[Path]:
    """Hojas de contacto (12 por hoja) para revisar capturas o fotogramas de un vistazo."""
    font = _font(20)
    sheets = []
    for start in range(0, len(paths), per_sheet):
        out = out_prefix.with_name(f"{out_prefix.name}-{start // per_sheet + 1}.jpg")
        out.parent.mkdir(parents=True, exist_ok=True)
        _sheet(paths[start:start + per_sheet], font).save(out, quality=85)
        sheets.append(out)
    return sheets
