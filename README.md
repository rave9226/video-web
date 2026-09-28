# 🎬 video-web

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
![Voz: 10 idiomas](https://img.shields.io/badge/voz-10_idiomas-green)
![Local](https://img.shields.io/badge/TTS-100%25_local-orange)
![Claude Code](https://img.shields.io/badge/Claude_Code-skill-black)

### Convierte el material que ya tienes en un video narrado.

video-web es una skill de código abierto (Apache-2.0), sin costo de licencia ni experiencia previa en edición. Tu agente puede partir de una app, su código si tiene acceso, un PDF, otros documentos, una investigación o una idea para crear demos, tutoriales, capacitaciones y explicativos. También permite videos de varios minutos: la skill documenta una producción real de 2:40.

Úsala con un agente que pueda leer y ejecutar skills. Está documentada para Claude Code y OpenCode, incluido OpenCode con DeepSeek V4.1 Flash; otros harnesses requieren adaptar la instalación y comprobar sus herramientas.

<p align="center">
  <img src="docs/demo.gif" alt="Video generado por video-web a partir de la demo pública de OrangeHRM" width="800">
  <br>
  <sub>Fragmento de un video de 30 s generado de punta a punta con la demo pública de OrangeHRM (sin afiliación). <a href="https://github.com/rave9226/video-web/releases/latest">Mira el video completo con audio</a>.</sub>
</p>

> **English:** Turn a web app URL, PDF manual, document or researched topic into a 1920×1080 narrated MP4. video-web is an open-source agent skill for Claude Code and OpenCode: real read-only screenshots, a script, local native voice-over in 10 languages (Qwen3-TTS, each line checked with Whisper), your brand colors and HyperFrames animation synced to each spoken word. Motion graphics included. Docs are in Spanish; videos can use any of the 10 languages below.

Una demo para lanzar. Un tutorial que tu equipo sí puede seguir. Un explicativo sin app que capturar. Pídeselo a Claude Code u OpenCode con el material que ya tienes:

```text
"Haz un video demo de 45 segundos de https://mi-app.com, voz en español latino"
"Convierte este manual.pdf en un video tutorial paso a paso de 2 minutos"
"Investiga cómo migrar de Google Workspace a Microsoft 365 y haz un video de capacitación"
"Make a 30-second motion graphics explainer about our new pricing, English voice-over"
```

**Sin editor de video, locutor ni suscripción de TTS.** Dale acceso autorizado a una app y el agente puede explorarla mediante la captura en solo lectura, preparar el guion, usar sus colores y fuentes, generar la voz, construir las escenas y renderizar el MP4. Si le das solo un tema, puede investigarlo y crear un explicativo sin app que capturar. La voz y el render se ejecutan localmente; el modelo del agente puede ser externo y tener un costo de uso. La música generada con MusicGen no tiene licencia comercial: para publicar comercialmente, usa música propia con licencia o ninguna.

## Dale lo que tienes. Publica lo que necesitas.

| Le das… | Obtienes… |
|---|---|
| 🌐 **La URL de tu app** (con o sin login) | Demo, tour o lanzamiento con capturas reales, zoom y anillos sobre lo que la voz nombra |
| 📄 **Un manual en PDF** | Tutoriales y procedimientos paso a paso; sus imágenes se recortan y se animan |
| 🗂️ **Cualquier documento** (Word, PowerPoint, notas, transcripciones) | Capacitaciones, onboarding y comunicados internos narrados |
| 🔎 **Solo un tema** | El agente investiga, cita sus fuentes, busca imágenes oficiales o con licencia libre y arma un explicativo |
| ✨ **Una idea o un mensaje** | Motion graphics con tipografía cinética, diagramas, números y formas animadas, sin capturas |

También puedes combinar fuentes: la app con su manual, o una investigación con capturas oficiales de documentación. Por ejemplo, un video interno de 3 minutos sobre una **migración de Google Workspace a Microsoft 365**: equivalencias entre herramientas y recorrido por Teams, SharePoint, Planner y Power Automate con capturas oficiales de la documentación de Microsoft. Sin app que capturar.

## Movimiento que sigue cada palabra

Las escenas usan [HyperFrames](https://github.com/heygen-com/hyperframes): HTML + GSAP renderizado cuadro a cuadro. video-web sincroniza los elementos con cada palabra hablada y funciona junto con las skills que instalas con `npx hyperframes skills update`: `/motion-graphics`, `/hyperframes-animation` (blueprints de escenas) y `/hyperframes-creative`. `vl` añade captura en solo lectura, voz verificada, marca y revisión antes del render.

---

## Tu producto real, no una interfaz inventada

Una demo pierde fuerza si dibuja una app distinta, habla sobre un botón que aún no aparece o cambia de estilo entre escenas. video-web ata la imagen, la voz y el movimiento al material original:

| Problema típico | Lo que hace video-web |
|---|---|
| El agente redibuja tu app en HTML | **Capturas reales** a 2x de tu app, con la posición de cada botón medida al píxel |
| Navegar tu app con un agente es riesgoso | **Captura en solo lectura**: bloquea escrituras, GET de acción y WebSockets; permite el login |
| Voz robótica o con acento extranjero | **Voz nativa en 10 idiomas**, local con Qwen3-TTS, y cada línea verificada con Whisper (se regenera sola si falla) |
| Animaciones desfasadas de la voz | Cada elemento aparece **en el segundo exacto** en que la voz lo nombra |
| Cada escena con un estilo distinto | **Colores y fuentes de tu marca** fijados para todo el video |
| Errores que aparecen tras 20 min de render | **`vl check`** detecta antes del render lo que rompe el video |

## Una voz para tu audiencia

🇪🇸 Español (por defecto, latino) · 🇺🇸 Inglés · 🇧🇷 Portugués · 🇫🇷 Francés · 🇩🇪 Alemán ·
🇮🇹 Italiano · 🇷🇺 Ruso · 🇨🇳 Chino · 🇯🇵 Japonés · 🇰🇷 Coreano

Son los 10 idiomas de Qwen3-TTS. **Probados:** español en videos completos; inglés y portugués de Brasil en diseño, clonación y validación de voz. Para cambiar el idioma: `video-web/references/oficio.md` § Otros idiomas.

## Del lanzamiento a la capacitación

- 🚀 **Lanzamientos** de producto o de una función nueva.
- 🧭 **Demos y tours** de tu SaaS, portal o panel de administración (con o sin login).
- 🎓 **Tutoriales y procedimientos** desde tu app o tu manual en PDF.
- 🏢 **Capacitación interna**: migraciones de herramientas, onboarding, políticas y procesos.
- 🔎 **Explicativos investigados** sobre cualquier tema, con fuentes citadas.
- ✨ **Motion graphics**: tipografía cinética, diagramas y datos animados.
- 🌎 **El mismo video en otro idioma**: cambia voz, guion y textos; reusa capturas y estructura.

## Números de videos reales

- **Video de producto de 2:40:** documentado en la skill; el flujo también sirve para presentaciones de varios minutos, no solo clips breves.
- **3 videos completos** de punta a punta con apps públicas (OrangeHRM y books.toscrape.com): **≈ 14 minutos por video** de 20–45 s con GPU, incluido todo el pipeline.
- **Voz comprobada con Whisper:** WER 0 en las líneas medidas y P(idioma) > 0,98 en español, inglés y portugués.
- **Audio nivelado** a ≈ −16 LUFS.
- **También corre sin GPU:** la voz tarda ≈ 10× la duración del audio en una CPU de 16 núcleos. Probado en Linux. macOS y Windows con WSL2 están soportados, pero aún no se han probado en equipos reales.

## Pide el video; revisa lo que importa

`vl` ejecuta el pipeline. Tu agente prepara el video con tu material:

```text
explorar → capturar → marca → guion → voz → música → escenas → revisar → render
```

1. Reúne el material: `vl explorar` y `vl captura` recorren tu app en solo lectura y miden
   cada elemento; `vl init --manual` lee tu PDF y `vl crop` recorta sus imágenes; el agente lee
   tus documentos o investiga el tema.
2. `vl marca`: saca colores y fuentes de tu app.
3. `vl voz`: diseña 3 voces, tú eliges de oído y clona esa voz en cada línea.
4. `vl musica` (opcional): música de fondo mezclada bajo la voz.
5. Escenas HyperFrames escritas en paralelo por varios agentes, una por archivo.
6. `vl snap`: hojas de revisión con inicio, medio y final de cada escena.
7. `vl render`: MP4 final, versión 720p y grilla de revisión.

Tú decides qué datos se muestran, eliges la voz y la música, y revisas el video antes del render.

**Producción local:** las capturas, el guion y la voz no pasan por servicios de TTS o video en la nube. El único modelo externo es el de tu agente.

> **Música para uso comercial:** MusicGen es CC-BY-NC (no comercial). Usa una pista
> propia con licencia (`assets/bgm/track.wav` + `vl musica mezclar`) o ninguna.

Las instrucciones completas para el agente están en [`video-web/SKILL.md`](video-web/SKILL.md).

---

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
   con voz en español", o "... with an English voice-over") o usa `/video-web` en Claude Code.

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

## Contribuir

Issues y pull requests bienvenidos. Antes de un PR: `python3 -m pytest tests -q` en
`video-web/scripts` y, si tocas el pipeline, las evals de `video-web/evals/` (ver
[`MANTENER.md`](MANTENER.md)). Especialmente útil: probar en macOS, WSL2 y en idiomas aún no
verificados.

## Licencia

[Apache-2.0](LICENSE). Los modelos que descarga la skill tienen sus propias licencias (ver
§ Licencias de los modelos); MusicGen no permite uso comercial.
