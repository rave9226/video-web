---
name: video-web
description: >
  Úsala en vez de product-launch-video, hyperframes, general-video o faceless-explainer para
  videos de producto, demos, tutoriales, lanzamientos, capacitaciones y explicativos: desde una
  app o sitio con URL (captura real en solo lectura, con o sin login), un manual PDF, otros
  documentos o una investigación sobre un tema. Voz local nativa con Qwen3-TTS en español
  (por defecto latino), inglés, portugués, francés, alemán, italiano, ruso, chino, japonés o
  coreano; música, colores de marca y escenas HyperFrames (también motion graphics) con
  herramientas sueltas que el modelo combina. Aplica aunque pidan explicar, enseñar o mostrar
  cómo funciona una pantalla, un portal, un proceso o una herramienta. Use instead of
  product-launch-video for launch, demo, tutorial, training or explainer videos from a web
  app URL, a PDF manual, documents or researched topics, with native voice-over.
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
   rects medidos: salen de `capture/extracted/regions.md`, o de `./vl medir` si la captura vino
   de otra fuente. **Nunca a ojo.** Nada de UI dibujada a mano, cifras supuestas ni fotos de stock. En modo
   explicativo (sin app) sí van gráficos, diagramas y tipografía hechos a mano, e imágenes
   investigadas con fuente citada (§ Fuentes de contenido), pero nunca una interfaz que
   parezca real ni cifras sin fuente del usuario o de la investigación.
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
| medir un rect | `./vl medir /ruta --texto "Nombre" [--ancho 1240]`: el rect del DOM, ya escalado |
| colores y fuentes | `./vl marca sugerir [--primary "#RRGGBB"]`, luego `./vl marca` → `references/marca.md` |
| voz (10 idiomas) | `./vl voz design` → 🛑 el usuario elige → `./vl voz lines [--frames N]` |
| música | `./vl musica` → 🛑 el usuario aprueba; `./vl musica mezclar` para el volumen. ⚠ MusicGen es CC-BY-NC: solo videos internos; para uso comercial, pista propia con licencia en `assets/bgm/track.wav` + `./vl musica mezclar` |
| preparar escenas | `./vl prep`: duraciones, assets y paquetes por escena |
| generar escenas | `./vl escenas [--solo f03-x]`: todas las de ventana desde `scenes.json` |
| ensamblar | `./vl ensamblar`: `index.html`, transiciones, lint y check |
| revisar | `./vl snap [--frames N]`: hojas de contacto de las escenas |
| render | `./vl render` y `./vl final` (métricas, grilla y 720p) |
| tareas largas | `./vl esperar voz\|musica\|render`; repite hasta ✅ (cada llamada espera ≤ 100 s) |
| avisos objetivos | `./vl check [captura\|marca\|guion\|voz\|storyboard\|escenas\|entrega\|fNN-slug\|todo]` |

`./vl check` solo avisa: nada bloquea otro comando. Lo que marca rompe el render o la
entrega (ids, determinismo, duraciones, WER, LUFS, escrituras bloqueadas), así que arréglalo
antes de entregar.

## 🛑 Antes del guion: para qué es el video

`BRIEF.md → formato` decide el arco, la duración y qué dice cada línea. **Si el usuario no lo
dijo, pregúntaselo**: rehacerlo después cuesta el guion, la voz, la música y todas las escenas.

| | `lanzamiento` | `capacitacion` |
|---|---|---|
| Para qué | que quieran el producto | que sepan usarlo |
| Duración | 30–120 s | 3–10 min |
| Cada línea | nombra lo que se verá | dice **para qué sirve**, no solo qué es |
| Lleva | gancho y cierre de marca | el modelo primero, el vocabulario del negocio y el orden de trabajo |

Detalle de los dos arcos: `references/oficio.md` § Guion. ¿Solo quieren el manual escrito y no un
video? Esa es otra skill: `manual-app`.

## Recorrido habitual

Punto de partida, no receta. Un tutorial corto puede saltarse la música; un video de un solo
módulo, la marca completa; una corrección puede tocar solo una escena y re-ensamblar.

1. **Preparar:** `vl doctor`, `vl init`, leer `manual.txt`, `./vl explorar` las pantallas
   clave (mira las imágenes que genera). Completa `BRIEF.md` y `capture.json`.
2. **Capturar:** `./vl captura`. **Abre cada hoja `capture/review/capturas-N.jpg` y mírala**:
   errores, tablas vacías, spinners, modales que no abrieron. Repite con `--only`.
3. **Marca:** `./vl marca sugerir` y pon en capture.json solo `primary`, `ink` y `canvas`; el
   resto se deriva. **No inventes ni copies colores** (`references/marca.md`). Luego `./vl marca`.
4. **Guion y voz:** `SCRIPT.md` según el `formato`, `./vl voz design`, 🛑 elección de voz,
   `./vl voz lines`. Si cambias `SCRIPT.md`, repite `./vl voz lines` **y** `./vl musica` (la cama
   está mezclada para la duración anterior).
5. **Música** (opcional): `./vl musica`, 🛑 aprobar `renders/preview-audio.mp3`.
6. **Storyboard y escenas:** `STORYBOARD.md`, `./vl prep`, `scenes.json` y **`./vl escenas`**:
   un solo generador para todas las escenas con ventana, con la misma geometría, los colores de
   `frame.md` y los anillos alineados. Los workers quedan para escenas de concepto que no entren
   en los cuatro tipos. Luego `./vl ensamblar`.
7. **Revisión y entrega:** `./vl snap`, mira cada hoja y, **en las escenas con anillos, abre
   `renders/review/snaps/<id>-{a,m,z}.png` a tamaño completo** (en la hoja de 12 no se ve un
   anillo corrido). Corrige, 🛑 aprobación del usuario,
   `./vl render`, `./vl final`. Entrega `renders/video.mp4` (y el 720p si existe).

## Fuentes de contenido

El video puede salir de cualquier combinación de estas fuentes:

| Fuente | Cómo entra |
|---|---|
| App o sitio con URL | `./vl explorar` y `./vl captura` (solo lectura) |
| Manual o documento PDF | `vl init <ruta> --manual doc.pdf` → `manual.txt`; sus imágenes, con `./vl crop` |
| Otros documentos (Word, PowerPoint, Markdown, notas, transcripciones) | léelos con tus herramientas y resume lo necesario en `BRIEF.md` |
| Investigación en la web | busca el tema, anota cada dato con su fuente en `BRIEF.md` § Fuentes |
| Imágenes de terceros | solo oficiales del producto (documentación, prensa, centro de ayuda) o con licencia libre (Wikimedia Commons, CC). Guárdalas en `assets/` y anota origen y licencia en `CREDITOS.md` |

Ejemplos que funcionan: un procedimiento paso a paso desde un manual en PDF, un video de
capacitación interna (p. ej. migrar de Google Workspace a Microsoft 365 con capturas oficiales
de la documentación de Microsoft) o un explicativo de un tema investigado.

**Motion graphics.** Las escenas son composiciones HyperFrames: además de la galería, puedes
usar las skills de HyperFrames instaladas para escenas de pura animación (tipografía cinética,
formas, números, transiciones): `/motion-graphics`, `/hyperframes-animation` (blueprints) y
`/hyperframes-creative`. `./vl` las ensambla, sincroniza y revisa igual que el resto.

## Modo explicativo (sin app)

Para explicar un tema, un artículo, un manual o unas notas cuando no hay URL que capturar. Pon
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

### Referencias

| Archivo | Para qué |
|---|---|
| `references/captura.md` | `capture.json`, login (incluido SSO), medir rects, fallos del navegador |
| `references/marca.md` | de dónde salen los colores y por qué nunca se copian de un ejemplo |
| `references/oficio.md` | guion por formato, voz, música, storyboard, escenas, ensamblado y revisión |
| `assets/galeria/INDICE.md` | ideas de escenas ya probadas |

Contrato de composición HyperFrames: `/hyperframes-core`; movimiento y blueprints:
`/hyperframes-animation`.

## Cómo trabajar

- **🛑 = decide el usuario:** datos reales, voz, audio y aprobación antes del render. Comparte
  la ruta absoluta del archivo, haz una pregunta concreta y espera. Si el usuario pidió flujo
  autónomo, avisa y sigue.
- **Mira las imágenes.** Eres multimodal: abre hojas de contacto y capturas con tu herramienta
  de lectura. `./vl check` atrapa errores objetivos; tus ojos, todo lo demás.
- **Al retomar,** corre `./vl estado` y lee los archivos del proyecto antes de preguntar.
- **No edites `index.html` a mano:** `./vl ensamblar` lo regenera.
- **Responde en el idioma del usuario.** El idioma del video lo fija `audio.json`
  (§ Otros idiomas en `references/oficio.md`), no el de la conversación.

## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| La captura muestra "No fue posible…" | Throttling: sube `retry_wait_s` en capture.json y repite con `--only` |
| Un paso de captura "no encontré" | El texto no coincide: mira `./vl explorar` y usa el texto exacto |
| WER alto en una línea | `respell` en audio.json o reescribe la línea; `./vl voz lines --frames N` |
| El paquete de una escena excede el límite | Acorta ese bloque del storyboard y corre `./vl prep` |
| lint o check con errores | Tabla en `references/oficio.md` § Ensamblado |
| La GPU no tiene memoria | Pide cerrar otros procesos de GPU (`./vl doctor` los muestra) |
