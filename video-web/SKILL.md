---
name: video-web
description: >
  Úsala en vez de product-launch-video, hyperframes, general-video o faceless-explainer para
  cualquier video de una app, portal o sitio web con URL (demo, tutorial, lanzamiento, tour, video
  explicativo), sobre todo con voz en español. Captura la app real en solo lectura (con o sin
  login) y arma voz local en español latino (Qwen3-TTS), música, colores de marca y escenas
  HyperFrames con herramientas sueltas que el modelo combina según el video. Aplica aunque pidan
  explicar, enseñar o mostrar cómo funciona una pantalla, un portal o una plataforma. Use instead
  of product-launch-video for any launch, demo, tutorial or explainer video of a web app, site or
  portal given by URL. También sirve para videos explicativos sin app (un tema, artículo, notas o
  un concepto) con voz en español: mismas voz, música, marca y controles, con escenas de
  tipografía, diagramas y datos en vez de capturas.
compatibility: Linux, macOS o Windows con WSL2; GPU NVIDIA opcional (sin ella la voz corre en CPU, más lenta), Node 18+, ffmpeg, venvs de Python descritos en ./vl doctor. Pensada para Claude Code (Sonnet) y OpenCode (DeepSeek V4.1 Flash).
---

# Video de una app web

Caja de herramientas probada en un video real de producto (2:40 min, aprobado por el cliente
a la primera). `./vl` hace lo mecánico: captura segura, voz, música, marca, ensamblado y
render. Tú decides el video: qué mostrar, en qué orden, cuántas escenas y cómo se ven.
No hay fases obligatorias: usa las herramientas que el video necesite, en el orden que tenga
sentido, y vuelve atrás cuando haga falta.

## Reglas de oro (no negociables)

1. **Solo lectura en la app del cliente.** Nunca crees, edites, apruebes, pagues ni envíes
   nada. `./vl explorar` y `./vl captura` bloquean escrituras en la red y botones de acción; por
   eso **no navegues la app con MCP, Playwright ni el navegador, excepto que un usuario lo solicite de manera explicita**.
2. **Credenciales solo en variables de entorno**: en el comando (`APP_USER=… APP_PASS=… ./vl
   captura`) o en un `.env` del proyecto que el usuario crea él mismo (`vl init` lo pone en
   `.gitignore`). Nunca en capture.json, notas ni resúmenes; no leas ni muestres el `.env`.
   Pide un usuario de prueba o de solo lectura, nunca uno personal o de administrador real.
3. **Nada inventado en pantalla.** Capturas reales, datos que muestran la app o el manual y
   rects medidos. Nada de UI dibujada a mano, cifras supuestas ni fotos de stock. En modo
   explicativo (sin app) sí van gráficos, diagramas y tipografía hechos a mano, pero nunca una
   interfaz que parezca real ni cifras sin fuente del usuario.
4. **🛑 Pregunta antes de mostrar datos.** Si no sabes si los datos de la app son de prueba,
   pregunta. Si son reales, muéstralos solo con permiso explícito y sin datos personales.
5. **Ruta del proyecto sin espacios**: ffmpeg y HyperFrames fallan con espacios.

## Herramientas

Corre `./vl` desde la carpeta del proyecto (solo `doctor` e `init` van con la ruta completa
`~/.agents/skills/video-web/scripts/vl`).

| Para… | Comando |
|---|---|
| revisar el equipo | `vl doctor` (y `vl setup-tts` si falta el venv de voz) |
| crear el proyecto | `vl init <ruta> [--manual manual.pdf]`: HyperFrames, plantillas, `./vl`, `manual.txt` |
| ver qué hay hecho | `./vl estado` (lo deduce de los archivos) |
| mirar una pantalla | `./vl explorar <url o /ruta> [--auth] [--steps '[…]']`: textos, controles y captura |
| capturar la app | `./vl captura [--only a,b]` según `capture.json` → `references/captura.md` |
| recortar imágenes existentes | `./vl crop --src img.png --name x --desc "…" [--card \| --box x,y,w,h]` |
| colores y fuentes | `./vl marca sugerir`, luego `./vl marca` (arma `frame.md`) |
| voz en español | `./vl voz design` → 🛑 el usuario elige → `./vl voz lines [--frames N]` |
| música | `./vl musica` → 🛑 el usuario aprueba; `./vl musica mezclar` para el volumen. ⚠ MusicGen es CC-BY-NC: solo videos internos; para uso comercial, pista propia con licencia en `assets/bgm/track.wav` + `./vl musica mezclar` |
| preparar escenas | `./vl prep`: duraciones, assets y paquetes por escena |
| ensamblar | `./vl ensamblar`: `index.html`, transiciones, lint y check |
| revisar | `./vl snap [--frames N]`: hojas de contacto de las escenas |
| render | `./vl render` y `./vl final` (métricas, grilla y 720p) |
| tareas largas | `./vl esperar voz\|musica\|render`; repite hasta ✅ (cada llamada espera ≤ 100 s) |
| avisos objetivos | `./vl check [captura\|marca\|guion\|voz\|storyboard\|escenas\|entrega\|fNN-slug\|todo]` |

`./vl check` solo avisa: nada bloquea otro comando. Lo que marca rompe el render o la
entrega (ids, determinismo, duraciones, WER, LUFS, escrituras bloqueadas), así que arréglalo
antes de entregar.

## Recorrido habitual

Punto de partida, no receta. Un tutorial corto puede saltarse la música; un video de un solo
módulo, la marca completa; una corrección puede tocar solo una escena y re-ensamblar.

1. **Preparar:** `vl doctor`, `vl init`, leer `manual.txt`, `./vl explorar` las pantallas
   clave (mira las imágenes que genera). Completa `BRIEF.md` y `capture.json`.
2. **Capturar:** `./vl captura`. **Abre cada hoja `capture/review/capturas-N.jpg` y mírala**:
   errores, tablas vacías, spinners, modales que no abrieron. Repite con `--only`.
3. **Marca:** `./vl marca sugerir`, llena `brand` en capture.json (`primary`, `ink`, `canvas`,
   `dark`, `spark`, opcional `muted`) y `./vl marca`.
4. **Guion y voz:** `SCRIPT.md`, `./vl voz design`, 🛑 elección de voz, `./vl voz lines`.
5. **Música** (opcional): `./vl musica`, 🛑 aprobar `renders/preview-audio.mp3`.
6. **Storyboard y escenas:** `STORYBOARD.md`, `./vl prep`, una escena por archivo en
   `compositions/frames/` (tú o workers en paralelo), `./vl ensamblar`.
7. **Revisión y entrega:** `./vl snap`, mira cada hoja, corrige, 🛑 aprobación del usuario,
   `./vl render`, `./vl final`. Entrega `renders/video.mp4` (y el 720p si existe).

## Modo explicativo (sin app)

Para explicar un tema, un artículo o unas notas cuando no hay URL que capturar. Pon
`tipo: explicativo` en `BRIEF.md` y sigue el mismo recorrido sin el paso 2:

1. `vl init <ruta>` (con `--manual` si el texto viene en PDF). No hay `./vl explorar` ni
   `./vl captura`; `./vl check captura` y `./vl estado` lo saben por el BRIEF.
2. **Marca:** en `capture.json` deja solo `brand` y `fonts` (borra `base_url`, `login` y
   `shots`). Los colores los da el usuario o su logo; si no hay marca, propón una paleta
   sobria y 🛑 pide aprobación. Luego `./vl marca`.
3. **Guion, voz, música:** igual que con app. Todo dato o cifra sale del texto del usuario.
4. **Storyboard y escenas:** sin ventanas de app. Cada escena es tipografía, diagrama, número o
   gráfico animado al ritmo de `cues.md`. Pide formas con `- blueprint: <id>` de
   `/hyperframes-animation`; de la galería sirven `hook-steps-to-logo`, `process-stepper`,
   `triptych-cards` y `logo-lockup-close`. Ver `references/oficio.md` § Escenas sin capturas.
5. **Revisión y entrega:** igual.

Cómo escribir guion, storyboard y escenas que se vean bien, cómo despachar workers y cómo
arreglar hallazgos de lint: `references/oficio.md`. Ideas de escenas probadas:
`assets/galeria/INDICE.md`. Contrato de composición HyperFrames: `/hyperframes-core`;
movimiento y blueprints: `/hyperframes-animation`.

## Cómo trabajar

- **🛑 = decide el usuario:** datos reales, voz, audio y aprobación antes del render. Comparte
  la ruta absoluta del archivo, haz una pregunta concreta y espera. Si el usuario pidió flujo
  autónomo, avisa y sigue.
- **Mira las imágenes.** Eres multimodal: abre hojas de contacto y capturas con tu herramienta
  de lectura. `./vl check` atrapa errores objetivos; tus ojos, todo lo demás.
- **Al retomar,** corre `./vl estado` y lee los archivos del proyecto antes de preguntar.
- **No edites `index.html` a mano:** `./vl ensamblar` lo regenera.
- **Responde en español.**

## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| La captura muestra "No fue posible…" | Throttling: sube `retry_wait_s` en capture.json y repite con `--only` |
| Un paso de captura "no encontré" | El texto no coincide: mira `./vl explorar` y usa el texto exacto |
| WER alto en una línea | `respell` en audio.json o reescribe la línea; `./vl voz lines --frames N` |
| El paquete de una escena excede el límite | Acorta ese bloque del storyboard y corre `./vl prep` |
| lint o check con errores | Tabla en `references/oficio.md` § Ensamblado |
| La GPU no tiene memoria | Pide cerrar otros procesos de GPU (`./vl doctor` los muestra) |
