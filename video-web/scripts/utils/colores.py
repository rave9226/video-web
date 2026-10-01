"""Helpers de color hex: contraste WCAG y mezcla lineal. Sin estado ni lógica de negocio."""


def _rgb(hexcol: str) -> list[int]:
    return [int(hexcol.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]


def rgb(hexcol: str) -> list[int]:
    """Componentes 0-255 de un #RRGGBB."""
    return _rgb(hexcol)


def contrast(fg: str, bg: str) -> float:
    """Razón de contraste WCAG 2.x entre dos colores #RRGGBB (1–21)."""
    def lum(hexcol: str) -> float:
        lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
               for c in (v / 255 for v in _rgb(hexcol))]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    high, low = sorted((lum(fg), lum(bg)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def mix(hex_a: str, hex_b: str, weight: float) -> str:
    """Mezcla lineal de dos colores (weight = proporción de hex_b)."""
    return "#" + "".join(f"{round(a + (b - a) * weight):02X}"
                         for a, b in zip(_rgb(hex_a), _rgb(hex_b)))


def readable(color: str, ink: str, canvas: str, minimum: float = 4.6) -> str:
    """`color` oscurecido hacia `ink` lo justo para leerse como texto sobre `canvas`."""
    for step in range(0, 21):
        candidate = mix(color, ink, step / 20)
        if contrast(candidate, canvas) >= minimum:
            return candidate
    return ink


def muted_between(ink: str, canvas: str, minimum: float = 4.6) -> str:
    """El gris más claro entre tinta y lienzo que aún cumple `minimum` de contraste."""
    best = ink
    for step in range(1, 20):
        candidate = mix(ink, canvas, step / 20)
        if contrast(candidate, canvas) < minimum:
            break
        best = candidate
    return best
