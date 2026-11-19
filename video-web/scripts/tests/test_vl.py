"""Pruebas del candado y la comprobación de memoria de GPU en `vl` (bash)."""
import fcntl
import os
import subprocess
from pathlib import Path

VL = Path(__file__).resolve().parents[1] / "vl"


def _entorno(tmp_path, libre_mib):
    """PATH con un nvidia-smi falso que informa `libre_mib` MiB libres."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    smi = bin_dir / "nvidia-smi"
    smi.write_text(f"#!/bin/sh\n[ \"$1\" = --query-gpu=memory.free ] && echo {libre_mib}\nexit 0\n")
    smi.chmod(0o755)
    return {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}", "HOME": str(tmp_path),
            "VL_GPU_LOCK": str(tmp_path / "gpu.lock"), "VL_PY": "/usr/bin/python3",
            "XDG_CONFIG_HOME": str(tmp_path / "cfg")}


def _vl(args, env, cwd):
    return subprocess.run([str(VL), *args], env=env, cwd=cwd, capture_output=True, text=True,
                          check=False)


def test_gpu_sin_memoria_falla_con_mensaje_claro(tmp_path):
    """Con menos memoria libre que el mínimo, `vl gpu` se niega y dice cuánta hay."""
    r = _vl(["gpu"], _entorno(tmp_path, 500), tmp_path)
    assert r.returncode == 1 and "500 MiB libres" in r.stderr


def test_gpu_con_memoria_pasa(tmp_path):
    """Con memoria suficiente sigue."""
    assert _vl(["gpu"], _entorno(tmp_path, 9000), tmp_path).returncode == 0


def test_tarea_de_gpu_espera_el_candado_y_falla_si_no_llega_el_turno(tmp_path):
    """Si otro video tiene el candado y se agota la espera, la tarea termina con error."""
    env = {**_entorno(tmp_path, 9000), "VL_GPU": "1", "VL_GPU_ESPERA_S": "1"}
    (tmp_path / ".vl/tareas").mkdir(parents=True)
    with open(env["VL_GPU_LOCK"], "w", encoding="utf-8") as ocupado:
        fcntl.flock(ocupado, fcntl.LOCK_EX)
        r = _vl(["_run", "voz", "true"], env, tmp_path)
    assert "sigue ocupada" in r.stderr
    assert (tmp_path / ".vl/tareas/voz.estado").read_text().strip() == "1"
    # libre el candado, la misma tarea corre
    assert _vl(["_run", "voz", "true"], env, tmp_path).returncode == 0
    assert (tmp_path / ".vl/tareas/voz.estado").read_text().strip() == "0"
