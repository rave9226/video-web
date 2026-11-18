# 🎬 video-web

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
![Voz: 10 idiomas](https://img.shields.io/badge/voz-10_idiomas-green)
![Local](https://img.shields.io/badge/TTS-100%25_local-orange)
![Claude Code](https://img.shields.io/badge/Claude_Code-skill-black)

### Convierte el material que ya tienes en un video narrado, o en el manual escrito.

video-web es una skill de código abierto (Apache-2.0), sin costo de licencia ni experiencia previa en edición. Tu agente puede partir de una app, su código si tiene acceso, un PDF, otros documentos, una investigación o una idea para crear demos, tutoriales, capacitaciones, explicativos y **cápsulas de cursos de pago** (listas para plataformas como Hotmart). También permite videos de varios minutos.

**El repo trae dos skills, una instalación:** `video-web` hace el video; **`manual-app` hace el manual de usuario en PDF** de la misma app. Ninguna depende de la otra: puedes pedir solo el manual.

Úsala con un agente que pueda leer y ejecutar skills. Está documentada para Claude Code y OpenCode, incluido OpenCode con DeepSeek V4.1 Flash; otros harnesses requieren adaptar la instalación y comprobar sus herramientas.

<p align="center">
  <img src="docs/demo.gif" alt="Video generado por video-web a partir de la demo pública de OrangeHRM" width="800">
  <br>
  <sub>Fragmento de un video de 30 s generado de punta a punta con la demo pública de OrangeHRM (sin afiliación), con la versión 1.x. <a href="https://github.com/rave9226/video-web/releases/latest">Mira el video completo con audio</a>.</sub>
</p>

> **English:** Turn a web app URL, PDF manual, document or researched topic into a 1920×1080 narrated MP4. video-web is an open-source agent skill for Claude Code and OpenCode: real read-only screenshots, a script, local native voice-over in 10 languages (Qwen3-TTS, each line checked with Whisper), your brand colors and givemotion scenes (HTML + CSS) synced to each spoken word, plus subtitles and a thumbnail for course platforms. Motion graphics included. Docs are in Spanish; videos can use any of the 10 languages below.

Una demo para lanzar. Un tutorial que tu equipo sí puede seguir. Un explicativo sin app que capturar. Pídeselo a Claude Code u OpenCode con el material que ya tienes:

```text
"Haz un video demo de 45 segundos de https://mi-app.com, voz en español latino"
"Convierte este manual.pdf en un video tutorial paso a paso de 2 minutos"
"Haz la cápsula de 3 minutos de mi curso sobre cómo verificar un informe hecho con IA"
"Investiga cómo migrar de Google Workspace a Microsoft 365 y haz un video de capacitación"
"Make a 30-second motion graphics explainer about our new pricing, English voice-over"
"Hazme el manual de usuario de https://mi-app.com para la gente nueva"
```

**Sin editor de video, locutor ni suscripción de TTS.** Dale acceso autorizado a una app y el agente puede explorarla mediante la captura en solo lectura, preparar el guion, usar sus colores y fuentes, generar la voz, construir las escenas y renderizar el MP4. Si le das solo un tema, puede investigarlo y crear un explicativo sin app que capturar. La voz y el render se ejecutan localmente; el modelo del agente puede ser externo y tener un costo de uso. La música solo entra con licencia comercial (CC0 o comprada) y queda anotada en `CREDITOS.md`.

## Dale lo que tienes. Publica lo que necesitas.

| Le das… | Obtienes… |
|---|---|
| 🌐 **La URL de tu app** (con o sin login) | Demo, tour o lanzamiento con capturas reales, zoom y anillos sobre lo que la voz nombra |
| 📄 **Un manual en PDF** | Tutoriales y procedimientos paso a paso; cada página queda como imagen y sus capturas se recortan y se animan |
| 🗂️ **Cualquier documento** (Word, PowerPoint, notas, transcripciones) | Capacitaciones, onboarding y comunicados internos narrados |
| 🔎 **Solo un tema** | El agente investiga, cita sus fuentes, busca imágenes oficiales o con licencia libre y arma un explicativo |
| ✨ **Una idea o un mensaje** | Motion graphics con tipografía cinética, diagramas, números y formas animadas, sin capturas |
| 🎓 **El contenido de un curso** | Cápsulas con un caso concreto de principio a fin, pasos numerados, subtítulos y miniatura para la plataforma |
| 📘 **La URL de tu app, otra vez** | El **manual de usuario** en PDF: una sección por pantalla, para qué sirve cada una y en qué orden se usan |

También puedes combinar fuentes: la app con su manual, o una investigación con capturas oficiales de documentación. Por ejemplo, un video interno de 3 minutos sobre una **migración de Google Workspace a Microsoft 365**: equivalencias entre herramientas y recorrido por Teams, SharePoint, Planner y Power Automate con capturas oficiales de la documentación de Microsoft. Sin app que capturar.

## Movimiento que sigue cada palabra

Las escenas usan givemotion (MIT): HTML + CSS + `gm.timeline`, renderizado cuadro a cuadro. video-web sincroniza los elementos con cada palabra hablada y parte de un sistema visual de curso profesional: encabezado con la sección y «Paso N de M», barra de progreso, tarjetas, estados en verde y rojo, y una cámara que se acerca a lo que nombra la voz. Ese sistema ganó una comparación a ciegas contra la versión anterior. `vl` añade captura en solo lectura, voz verificada, marca, revisión antes del render y la entrega final.

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
| Errores que aparecen tras 20 min de render | **`vl revisar`** y **`vl check`** detectan antes del render lo que rompe el video |
| Una frase repetida que Whisper no ve | **Detector de habla oculta**: Whisper transcribe una frase doble una sola vez, así que `vl voz` mide los huecos y reintenta |
| Tarjetas con barras grises, letra diminuta, pantalla medio vacía | **Un caso concreto** rotulado «Ejemplo ficticio», letra de 24 px como mínimo, composición que llena el cuadro y nada quieto más de 1,5 s: lo revisa `vl revisar` |
| Colores de otro video que se cuelan | Las escenas solo usan los tokens de `marca.css`; `vl check` avisa de cualquier color escrito a mano |

## Una voz para tu audiencia

🇪🇸 Español (por defecto, latino) · 🇺🇸 Inglés · 🇧🇷 Portugués · 🇫🇷 Francés · 🇩🇪 Alemán ·
🇮🇹 Italiano · 🇷🇺 Ruso · 🇨🇳 Chino · 🇯🇵 Japonés · 🇰🇷 Coreano

Son los 10 idiomas de Qwen3-TTS. **Probados:** español en videos completos; inglés y portugués de Brasil en diseño, clonación y validación de voz. Para cambiar el idioma: `video-web/references/oficio.md` § Otros idiomas.

**Una voz lista para usar:** la skill trae `instructora-2026`, una narradora colombiana de curso, cálida y segura, elegida en una prueba a ciegas. Es la voz por omisión: todo el equipo narra con el mismo tono sin configurar nada.

## Del lanzamiento a la capacitación

- 🚀 **Lanzamientos** de producto o de una función nueva.
- 🧭 **Demos y tours** de tu SaaS, portal o panel de administración (con o sin login).
- 🎓 **Tutoriales y procedimientos** desde tu app o tu manual en PDF.
- 💳 **Cursos de pago**: cápsulas para Hotmart y plataformas similares, con subtítulos, miniatura y música con licencia comercial.
- 🏢 **Capacitación interna**: migraciones de herramientas, onboarding, políticas y procesos.
- 🔎 **Explicativos investigados** sobre cualquier tema, con fuentes citadas.
- ✨ **Motion graphics**: tipografía cinética, diagramas y datos animados.
- 🌎 **El mismo video en otro idioma**: cambia voz, guion y textos; reusa capturas y estructura.
- 📘 **Manuales de usuario** en PDF de la misma app, con `manual-app`.

### Elige el formato desde el principio

`BRIEF.md → formato` decide el arco, la duración y qué dice cada línea. Si no lo declaras, la
skill lo pregunta antes de escribir el guion.

| | `lanzamiento` | `capacitacion` | `explicativo` (tema o cápsula de curso) |
|---|---|---|---|
| Para qué | que quieran el producto | que sepan usarlo | que entiendan una idea y la apliquen |
| Duración | 30–120 s | 3–10 min | 1–4 min |
| Cada línea | nombra lo que se verá | dice **para qué sirve**, no solo qué es | una idea con su ejemplo |
| Lleva | gancho y cierre de marca | el modelo primero, el vocabulario del negocio y el orden de trabajo | un caso concreto, pasos numerados y la acción de la semana |

## 📘 Manuales de usuario con `manual-app`

La otra mitad del repo. Un manual se usa distinto que un video: la gente llega buscando **una**
cosa, con la app abierta al lado. `manual-app` escribe el manual de una app con capturas reales y
lo entrega en PDF con los colores de la marca.

**Funciona sola.** No necesita video, ni GPU, ni Node, ni ffmpeg: Python con `markdown` y
`playwright`, y nada más.

```text
"Hazme el manual de usuario de https://mi-app.com"
"Documenta este portal para los usuarios nuevos"
```

```bash
~/.agents/skills/manual-app/scripts/ml init ~/manuales/mi-app --titulo "Mi App"
cd ~/manuales/mi-app
./ml pantalla --url https://mi-app.com --ruta /facturas --nombre app-facturas
./ml check && ./ml pdf
```

Si ya hiciste el video, `ml init --desde <proyecto-de-video>` reutiliza sus capturas y su marca
(los colores de `marca.css`, o del `frame.md` de un proyecto 1.x).
Lo que hace útil al manual —y lo que la plantilla obliga a llenar— es decir **para qué sirve**
cada pantalla, explicar los verbos del negocio y dejar claro **en qué orden** se usan las cosas.

## Probado con videos reales

- **Cápsula de un curso de pago** (3:09 min): voz, motor de escenas y estilo elegidos en
  pruebas a ciegas contra la versión anterior; entregada a −16 LUFS con subtítulos y miniatura.
- **Versión 2.x de punta a punta** con la skill instalada: un sitio web público (exploración
  en solo lectura, captura con medidas y escena de ventana con anillos), un manual en PDF
  (texto, páginas y captura recortada) y un explicativo con caso ficticio. Los tres pasan
  `vl check entrega` sin avisos.
- **Versión 1.x:** 3 videos completos con apps públicas (OrangeHRM y books.toscrape.com),
  ≈ 14 minutos por video de 20–45 s con GPU.
- **Voz comprobada con Whisper:** WER 0 en las líneas medidas y P(idioma) > 0,98 en español,
  inglés y portugués; el detector de habla oculta revisa además lo que Whisper no transcribe.
- **También corre sin GPU:** la voz tarda ≈ 10× la duración del audio en una CPU de 16 núcleos.
  Probado en Linux. macOS y Windows con WSL2 están soportados, pero aún no se han probado en
  equipos reales.

## Pide el video; revisa lo que importa

`vl` ejecuta el pipeline. Tu agente prepara el video con tu material:

```text
explorar → capturar → marca → guion → voz → música → escenas → revisar → render → final
```

1. Reúne el material: `vl explorar` y `vl captura` recorren tu app en solo lectura y miden
   cada elemento; `vl init --manual` lee tu PDF y deja cada página como imagen para que
   `vl crop` recorte sus capturas; el agente lee tus documentos o investiga el tema.
2. `vl marca`: saca colores y fuentes de tu app y escribe `marca.css` (tokens, fuentes locales y
   componentes).
3. `vl voz lines`: narra cada línea con la voz del curso (`instructora-2026`, viene con la
   skill) u otra de tu biblioteca, clonada en modo referencia completa. ¿Voz nueva?
   `vl voz design` propone candidatas, tú eliges de oído y `vl voz guardar <nombre>` la deja en
   la biblioteca para todos tus videos.
4. `vl musica <pista> --licencia "…"` (opcional): música con licencia comercial, anotada en
   `CREDITOS.md`.
5. Escenas givemotion, una por archivo (`scenes/sNN.html`), a partir de las plantillas de la
   skill: `escena-ventana.html` para una pantalla capturada (anillos con las medidas reales) y
   `escena-ejemplo.html` para tarjetas, comparaciones y el caso concreto.
6. `vl revisar`: `givemotion check`, hojas de cuadros y avisos de las escenas; `vl gm still`
   para un cuadro exacto.
7. `vl render` y `vl final`: MP4 1080p (CRF 16) mezclado a −16 LUFS, subtítulos
   `renders/video.vtt`, miniatura `renders/miniatura.png` y una copia 720p si pesa más de 25 MB.
   Listo para plataformas de cursos como Hotmart.

Tú decides qué datos se muestran, eliges la voz y la música, y revisas el video antes del render.

**Producción local:** las capturas, el guion y la voz no pasan por servicios de TTS o video en la nube. El único modelo externo es el de tu agente.

> **Música para uso comercial:** solo pistas con licencia que lo permita (CC0 o compradas),
> registradas con `vl musica <pista> --licencia "…"`, o ninguna. Si tienes instalada la skill
> `media-use`, `vl init` copia al proyecto su librería de efectos de sonido (licencia Pixabay,
> apta para uso comercial).

Las instrucciones completas para el agente están en [`video-web/SKILL.md`](video-web/SKILL.md).

---

## Requisitos

> Esto es lo que pide `video-web` para hacer **videos**. Para **manuales** con `manual-app`
> basta Python con `markdown` y `playwright`: ni GPU, ni Node, ni ffmpeg.

### Sistema

| Qué | Para qué | Cómo instalar (Debian/Ubuntu) |
|---|---|---|
| Linux, macOS 12.3+ o Windows con WSL2 | los scripts usan bash | — |
| GPU NVIDIA con ≥ 8 GB de VRAM (opcional) | voz rápida | driver de tu distribución (`nvidia-smi` debe funcionar) |
| Sin GPU: ≥ 16 GB de RAM | la voz corre en CPU (o MPS en Apple Silicon) | — |
| Node.js ≥ 20 con `npx` | givemotion (check, still, render) | `nvm install 20` o el paquete `nodejs` |
| Chrome o Chromium | render de givemotion (lo encuentra o descarga uno; compruébalo con `npx givemotion doctor`) | — |
| ffmpeg y ffprobe | cortes de audio, sonoridad (LUFS), mezcla y video final | `sudo apt install ffmpeg` |
| [uv](https://docs.astral.sh/uv/) | crear el venv de voz | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| pdftotext y pdftoppm (opcional) | leer un manual en PDF y sacar sus páginas como imagen con `vl init --manual` | `sudo apt install poppler-utils` |
| ≈ 15 GB libres en disco | venv de voz (≈ 6 GB) y modelos de Hugging Face | — |

### Python general (`VL_PY`)

Python 3.10 o superior con:

```bash
pip install playwright pillow numpy
python3 -m playwright install chromium
# opcional, para correr los tests de la skill:
pip install pytest
```

Por defecto la skill busca un `python3` con esos paquetes. Si están en otro venv, define
`VL_PY=/ruta/al/venv/bin/python3` en `~/.config/video-web/entorno.sh`.

### Python de voz (`VL_QWEN_VENV`)

Un venv aparte, porque trae PyTorch con CUDA. Por defecto está en `~/.venvs/qwen-tts`:

```bash
uv venv ~/.venvs/qwen-tts --python 3.12
uv pip install --python ~/.venvs/qwen-tts/bin/python \
  torch qwen-tts faster-whisper librosa soundfile transformers
```

Si lo creas en otra ruta, define `VL_QWEN_VENV=/ruta/al/venv` en `~/.config/video-web/entorno.sh`.
`vl setup-tts` muestra estos mismos pasos.

Los modelos se descargan solos en el primer uso (en `~/.cache/huggingface`):
`Qwen/Qwen3-TTS-12Hz-1.7B-Base`, `Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign` y
`Systran/faster-whisper-large-v3`.

### Biblioteca de voces y entorno de la máquina

La skill trae una voz lista: **`instructora-2026`** (`video-web/assets/voces/`), una
narradora colombiana de curso, cálida y segura, elegida en una prueba a ciegas. Es la voz por
omisión de todo proyecto nuevo: cualquiera del equipo narra con el mismo tono sin configurar
nada. Es sintética (Qwen3-TTS, pesos Apache-2.0), apta para uso comercial.

Tus voces propias van fuera del repo, en `~/.config/video-web/voces/<nombre>/` (`ref.wav` +
`voz.json`; otra carpeta con `VL_VOCES`); una propia con el mismo nombre manda sobre la de la
skill. Así un curso suena al mismo narrador en todas sus cápsulas. Las rutas propias de la máquina van en `~/.config/video-web/entorno.sh`,
que `vl` carga solo:

```bash
export VL_PY=/ruta/al/venv/bin/python3
export VL_QWEN_VENV=~/.venvs/qwen-tts
export VL_VOZ=mi-voz              # otra voz por omisión (sin esto: instructora-2026)
export GIVEMOTION_NO_SANDBOX=1    # solo si vl doctor lo pide
```

### givemotion

givemotion es el motor de las escenas: HTML + CSS +
`gm.timeline`, licencia MIT. `vl` lo corre con `npx` en la versión fijada en
`video-web/compat.json`, así que no hay que instalarlo aparte. `vl init` instala su skill en el
proyecto (`.claude/skills/givemotion/`) para que el agente lea su manual antes de escribir
escenas.

En Linux sin user namespaces, Chrome sale con SIGTRAP: agrega
`export GIVEMOTION_NO_SANDBOX=1` a `~/.config/video-web/entorno.sh` (`vl doctor` lo avisa).

## Licencias de los modelos

| Modelo | Licencia | Uso comercial |
|---|---|---|
| Qwen3-TTS (Base y VoiceDesign) | Apache-2.0 | sí |
| faster-whisper-large-v3 | MIT | sí |

## Datos y credenciales

- Datos reales solo con permiso explícito del dueño de la app, y sin datos personales.
- Usa usuarios de prueba o de solo lectura; nunca tu usuario personal ni uno de administrador real.
  El bloqueo de la captura (escrituras, GET de acción y WebSockets) es una red de seguridad,
  no un permiso: un GET con efectos y nombre inocente no se puede detectar.
- Las capturas y el guion los lee el modelo de tu agente: aplica la política de proveedores de tu empresa.

## Instalación

1. Copia las dos carpetas, `video-web/` y `manual-app/`, en `~/.agents/skills/`. Son
   independientes: si solo quieres manuales, copia `manual-app/`. Desde un clon del repo (así
   actualizar es repetir el comando):
   ```bash
   git clone https://github.com/rave9226/video-web.git && cd video-web
   rsync -a --delete video-web/ ~/.agents/skills/video-web/
   rsync -a --delete manual-app/ ~/.agents/skills/manual-app/
   ```
   O descomprime el paquete de una versión: `tar -xzf video-web-skill.tar.gz -C ~/.agents/skills/`.
2. Enlázalas en tu agente:
   ```bash
   ln -s ~/.agents/skills/video-web  ~/.claude/skills/video-web             # Claude Code
   ln -s ~/.agents/skills/manual-app ~/.claude/skills/manual-app
   ln -s ~/.agents/skills/video-web  ~/.config/opencode/skills/video-web    # OpenCode
   ln -s ~/.agents/skills/manual-app ~/.config/opencode/skills/manual-app
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
el doble con 8 núcleos. El render ya corría en CPU.
Fuerza el dispositivo con `VL_DEVICE=cpu|mps|cuda`.

## Variables de entorno

| Variable | Por defecto | Qué es |
|---|---|---|
| `VL_PY` | el primer `python3` con las dependencias | Python con playwright, Pillow y numpy |
| `VL_QWEN_VENV` | `~/.venvs/qwen-tts` | venv de voz |
| `VL_VOCES` | `~/.config/video-web/voces` | biblioteca de voces aprobadas |
| `VL_VOZ` | `instructora-2026` (de la plantilla) | voz que `vl init` pone en el proyecto |
| `VL_DEVICE` | el mejor disponible | `cuda`, `mps` o `cpu` para la voz |
| `GIVEMOTION_NO_SANDBOX` | — | `1` en Linux sin user namespaces (Chrome sale con SIGTRAP) |
| `APP_USER`, `APP_PASS` | — | credenciales de la app: en el comando de captura o en `.env` del proyecto (ignorado por git) |

## Estructura

```
video-web/
├── SKILL.md            instrucciones para el agente
├── references/         guía de captura y de oficio (guion, voz, escenas, revisión)
├── compat.json         versión fijada de givemotion
├── scripts/            vl y los scripts de Python (captura, voz, marca, checks, entrega final)
├── assets/templates/   plantillas del proyecto, marca.css y un ejemplo (app ficticia)
│   └── givemotion/     video.html (encabezado, progreso, cámara), escena-ventana.html
│                       (pantalla capturada) y escena-ejemplo.html (tarjetas y caso concreto)
├── assets/voces/       voz del curso incluida (instructora-2026: ref.wav + voz.json)
└── evals/              casos de prueba de la skill
manual-app/             skill de manuales de usuario en PDF (independiente)
```

## Versiones

La versión está en `video-web/VERSION` y los cambios en [`CHANGELOG.md`](CHANGELOG.md).
La versión probada de givemotion está fijada en `video-web/compat.json` y `vl doctor` la muestra
junto con `givemotion doctor`. Cómo publicar una versión: [`MANTENER.md`](MANTENER.md).

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
§ Licencias de los modelos); givemotion es MIT.
