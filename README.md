# video-web

Skill para agentes de código (Claude Code, OpenCode) que convierte una app, portal o sitio
web con URL en un video de producto (demo, tutorial, lanzamiento o explicativo) con voz en
español latino.

- Captura la app real en **solo lectura**, con o sin login. Bloquea en la red cualquier
  escritura que no sea el login.
- Genera la voz en local con Qwen3-TTS y la valida con Whisper (WER e idioma).
- Genera música de fondo en local con MusicGen y la mezcla por debajo de la voz.
  **MusicGen es CC-BY-NC (no comercial):** en videos comerciales usa una pista propia con
  licencia (`assets/bgm/track.wav` + `vl musica mezclar`) o ninguna.
- Toma los colores y las fuentes de la marca y arma las escenas con
  HyperFrames.

Todo corre con un solo comando, `vl`. El agente decide qué mostrar y en qué orden. Las
instrucciones para el agente están en [`video-web/SKILL.md`](video-web/SKILL.md).

## Requisitos

### Sistema

| Qué | Para qué | Cómo instalar (Debian/Ubuntu) |
|---|---|---|
| Linux, macOS 12.3+ o Windows con WSL2 | los scripts usan bash | — |
| GPU NVIDIA con ≥ 8 GB de VRAM (opcional) | voz rápida | driver de tu distribución (`nvidia-smi` debe funcionar) |
| Sin GPU: ≥ 16 GB de RAM | la voz corre en CPU (o MPS en Apple Silicon) | — |
| Node.js ≥ 18 con `npx` | HyperFrames (init, lint, snapshot, render) | `nvm install 20` o el paquete `nodejs` |
| ffmpeg y ffprobe | cortes de audio, sonoridad (LUFS), mezcla y video final | `sudo apt install ffmpeg` |
| [uv](https://docs.astral.sh/uv/) | crear el venv de voz | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| pdftotext (opcional) | leer un manual en PDF con `vl init --manual` | `sudo apt install poppler-utils` |
| ≈ 15 GB libres en disco | venv de voz (≈ 6 GB) y modelos de Hugging Face | — |

### Python general (`VL_PY`)

Python 3.10 o superior con:

```bash
pip install playwright pillow numpy
python3 -m playwright install chromium
# opcional, para correr los tests de la skill:
pip install pytest
```

Por defecto la skill usa el `python3` del PATH. Si instalaste esos paquetes en otro venv,
exporta `VL_PY=/ruta/al/venv/bin/python3`.

### Python de voz y música (`VL_QWEN_VENV`)

Un venv aparte, porque trae PyTorch con CUDA. Por defecto está en `~/.venvs/qwen-tts`:

```bash
uv venv ~/.venvs/qwen-tts --python 3.12
uv pip install --python ~/.venvs/qwen-tts/bin/python \
  torch qwen-tts faster-whisper librosa soundfile transformers
```

Si lo creas en otra ruta, exporta `VL_QWEN_VENV=/ruta/al/venv`.

Los modelos se descargan solos en el primer uso (en `~/.cache/huggingface`):
`Qwen/Qwen3-TTS-12Hz-1.7B-Base`, `Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign`,
`Systran/faster-whisper-large-v3` y `facebook/musicgen-small`.

### Skills de HyperFrames

La skill usa scripts de otras skills de HyperFrames: `product-launch-video` (ensamblado),
`media-use` (música) y `hyperframes` (contrato de escenas). No van en este paquete; se
instalan con la CLI en `~/.agents/skills/`:

```bash
npx hyperframes skills update
```

Si están en otra carpeta, exporta `VL_AGENTS_SKILLS=/ruta/a/skills`.

## Licencias de los modelos

| Modelo | Licencia | Uso comercial |
|---|---|---|
| Qwen3-TTS (Base y VoiceDesign) | Apache-2.0 | sí |
| faster-whisper-large-v3 | MIT | sí |
| facebook/musicgen-small | CC-BY-NC-4.0 | **no** |

## Datos y credenciales

- Datos reales solo con permiso explícito del dueño de la app, y sin datos personales.
- Usa usuarios de prueba o de solo lectura; nunca tu usuario personal ni uno de administrador real.
  El bloqueo de la captura (escrituras, GET de acción y WebSockets) es una red de seguridad,
  no un permiso: un GET con efectos y nombre inocente no se puede detectar.
- Las capturas y el guion los lee el modelo de tu agente: aplica la política de proveedores de tu empresa.

## Instalación

1. Copia la carpeta `video-web/` en `~/.agents/skills/` (o descomprime el paquete):
   ```bash
   tar -xzf video-web-skill.tar.gz -C ~/.agents/skills/
   ```
2. Enlázala en tu agente:
   ```bash
   ln -s ~/.agents/skills/video-web ~/.claude/skills/video-web              # Claude Code
   ln -s ~/.agents/skills/video-web ~/.config/opencode/skills/video-web     # OpenCode
   ```
3. Instala los requisitos de arriba y revisa el equipo:
   ```bash
   ~/.agents/skills/video-web/scripts/vl doctor
   ```
   Cada línea con ✗ dice qué falta. Repite hasta que no quede ninguna.
4. En tu agente, pide el video (por ejemplo, "haz un video demo de 60 s de https://mi-app.com
   con voz en español") o usa `/video-web` en Claude Code.

## Tiempos sin GPU

Medidos en CPU de 16 núcleos: una narración de 22 s tardó 3 min 44 s (generación, validación
con Whisper y nivelado), con WER 0 en todas las líneas. Calcula ≈ 10× la duración del audio,
el doble con 8 núcleos. La música (MusicGen) y el render ya corrían en CPU.
Fuerza el dispositivo con `VL_DEVICE=cpu|mps|cuda`.

## Variables de entorno

| Variable | Por defecto | Qué es |
|---|---|---|
| `VL_PY` | `python3` del PATH | Python con playwright, Pillow y numpy |
| `VL_QWEN_VENV` | `~/.venvs/qwen-tts` | venv de voz y música |
| `VL_DEVICE` | el mejor disponible | `cuda`, `mps` o `cpu` para la voz |
| `VL_AGENTS_SKILLS` | `~/.agents/skills` | carpeta de las skills de HyperFrames |
| `APP_USER`, `APP_PASS` | — | credenciales de la app: en el comando de captura o en `.env` del proyecto (ignorado por git) |

## Estructura

```
video-web/
├── SKILL.md            instrucciones para el agente
├── references/         guía de captura y de oficio (guion, voz, escenas, revisión)
├── scripts/            vl y los scripts de Python (captura, voz, música, marca, checks)
├── assets/templates/   plantillas del proyecto y un ejemplo completo (app ficticia)
├── assets/galeria/     12 escenas HyperFrames reales para usar como punto de partida
└── evals/              casos de prueba de la skill
```

## Versiones

La versión está en `video-web/VERSION` y los cambios en [`CHANGELOG.md`](CHANGELOG.md).
`vl doctor` avisa si las skills de HyperFrames instaladas no son las probadas
(`video-web/compat.json`). Cómo publicar una versión: [`MANTENER.md`](MANTENER.md).

## Tests

```bash
cd ~/.agents/skills/video-web/scripts && python3 -m pytest tests -q
```
