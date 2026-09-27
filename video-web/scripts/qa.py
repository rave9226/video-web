"""QA visual (snapshots del ensamblado) y revisión del MP4 final.

    qa.py snap [--frames 4,6]   3 fotogramas por escena + cortes → renders/review/ + qa-report
    qa.py final                 renders/video.mp4: resolución, duración, LUFS, grilla y 720p

Las hojas llevan el id de escena en cada miniatura para que el modelo las revise y cite.
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

from utils import imagenes, medios  # pylint: disable=import-error

REVIEW = Path("renders/review")
SNAPS = REVIEW / "snaps"
STATIC_DIFF = 0.004  # diferencia media < 0.4 % entre inicio, medio y final = escena quieta
SHARE_LIMIT = 30 * 2**20


def hyperframes() -> str:
    """Versión fijada del CLI en package.json (la misma que usan lint/check/render)."""
    pkg = Path("package.json").read_text(encoding="utf-8") if Path("package.json").exists() else ""
    pin = re.search(r"hyperframes@([\d.]+)", pkg)
    return f"hyperframes@{pin.group(1)}" if pin else "hyperframes"


def clips() -> list[dict]:
    """Escenas del index.html ensamblado: id, inicio y duración."""
    html = Path("index.html").read_text(encoding="utf-8")
    found = []
    for tag in re.findall(r"<div[^>]*data-composition-src=[^>]*>", html):
        attr = dict(re.findall(r'data-([\w-]+)="([^"]*)"', tag))
        found.append({"id": attr["composition-id"], "start": float(attr["start"]),
                      "dur": float(attr["duration"])})
    if not found:
        sys.exit("✗ index.html sin escenas: corre `./vl ensamblar`")
    return sorted(found, key=lambda c: c["start"])


def plan(scenes: list[dict], wanted: set[str]) -> list[tuple[str, float]]:
    """(nombre, segundo) de cada fotograma: inicio, medio y final de escena, y cada corte."""
    shots = []
    for idx, clip in enumerate(scenes):
        if wanted and clip["id"].split("-")[0] not in wanted:
            continue
        edge = min(0.9, clip["dur"] * 0.15)
        shots += [(f"{clip['id']}-a", clip["start"] + edge),
                  (f"{clip['id']}-m", clip["start"] + clip["dur"] / 2),
                  (f"{clip['id']}-z", clip["start"] + clip["dur"] - edge)]
        if idx and not wanted:
            shots.append((f"corte-{scenes[idx - 1]['id']}-{clip['id']}", clip["start"] + 0.2))
    return [(name, round(t, 2)) for name, t in shots]


def cmd_snap(wanted: set[str]) -> int:
    """Snapshots deterministas, hojas de contacto y heurísticas de vacío/quietud."""
    scenes = clips()
    shots = plan(scenes, wanted)
    raw = Path(".vl/snaps")
    medios.run(["npx", "--yes", hyperframes(), "snapshot", ".", "--at",
                ",".join(str(t) for _, t in shots), "--no-end", "--no-browser-gpu",
                "--describe", "false", "-o", str(raw)])
    SNAPS.mkdir(parents=True, exist_ok=True)
    named = []
    for idx, (name, sec) in enumerate(shots):
        src = raw / f"frame-{idx:02d}-at-{sec:g}s.png"
        if not src.exists():
            src = next(raw.glob(f"frame-{idx:02d}-at-*.png"))
        named.append(SNAPS / f"{name}.png")
        shutil.copyfile(src, named[-1])
    by_name = dict(zip((n for n, _ in shots), named))
    # Solo medio y final: el inicio de escena puede estar casi vacío a propósito (revelado
    # al ritmo de la voz); una escena rota sigue vacía a la mitad.
    blank = [sec for (name, sec), path in zip(shots, named)
             if name.endswith(("-m", "-z")) and imagenes.gray_std(path) < 6]
    static = [c["id"] for c in scenes if f"{c['id']}-a" in by_name
              and imagenes.mean_abs_diff(by_name[f"{c['id']}-a"], by_name[f"{c['id']}-m"])
              < STATIC_DIFF
              and imagenes.mean_abs_diff(by_name[f"{c['id']}-m"], by_name[f"{c['id']}-z"])
              < STATIC_DIFF]
    sheets = imagenes.contact_sheets(named, REVIEW / "escenas", per_sheet=12)
    report = {"shots": dict(shots), "blank": blank, "static": static,
              "sheets": [str(s) for s in sheets]}
    (REVIEW / "qa-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                           encoding="utf-8")
    print(f"Hojas: {', '.join(report['sheets'])}")
    print(f"Vacíos: {blank or 'ninguno'} · escenas sin movimiento: {static or 'ninguna'}")
    print("SIGUIENTE: mira TÚ cada hoja (lista en references/oficio.md § Revisión) y corrige "
          "lo que falle (`./vl snap --frames N` para re-ver una escena). Luego 🛑 envía las "
          "hojas al usuario.")
    return 1 if blank else 0


def cmd_final() -> int:
    """Métricas del MP4, grilla de 12 fotogramas y versión 720p si pesa mucho."""
    video = Path("renders/video.mp4")
    if not video.exists():
        sys.exit("✗ falta renders/video.mp4: corre `./vl render`")
    info = medios.video_summary(video)
    info["lufs"] = medios.lufs(video) if info["audio"] else None
    REVIEW.mkdir(parents=True, exist_ok=True)
    medios.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-vf",
                f"fps=12/{info['duration']:.2f},scale=480:-1,tile=4x3", "-frames:v", "1",
                str(REVIEW / "final-grilla.jpg")])
    if info["bytes"] > SHARE_LIMIT:
        medios.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-vf",
                    "scale=-2:720", "-c:v", "libx264", "-crf", "26", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
                    "renders/video-720p.mp4"])
        info["preview_720p"] = "renders/video-720p.mp4"
    (REVIEW / "final.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(f"{info['width']}x{info['height']} · {info['duration']:.2f} s · "
          f"{info['bytes'] / 2**20:.1f} MB · audio {info['lufs']} LUFS")
    print("Grilla: renders/review/final-grilla.jpg"
          + (" · 720p: renders/video-720p.mp4" if "preview_720p" in info else ""))
    return 0


def main() -> int:
    """Punto de entrada."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("cmd", choices=["snap", "final"])
    parser.add_argument("--frames", default="", help="números de escena, p. ej. 4,6")
    args = parser.parse_args()
    if args.cmd == "final":
        return cmd_final()
    return cmd_snap({f"f{int(n):02d}" for n in args.frames.split(",") if n})


if __name__ == "__main__":
    sys.exit(main())
