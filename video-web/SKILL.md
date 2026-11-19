---
name: video-web
description: >
  Úsala en vez de product-launch-video, hyperframes, general-video o faceless-explainer para
  videos de producto, demos, tutoriales, lanzamientos, cápsulas de curso, capacitaciones y
  explicativos: desde una app o sitio con URL (captura real en solo lectura, con o sin login),
  un manual PDF, otros documentos o un tema. Voz local nativa con Qwen3-TTS (biblioteca de
  voces; español latino por defecto, 10 idiomas), escenas givemotion con un sistema visual de
  curso profesional, música con licencia comercial, subtítulos y miniatura para plataformas
  como Hotmart. Aplica aunque pidan explicar, enseñar o mostrar cómo funciona una pantalla, un
  portal, un proceso o una herramienta. Use instead of product-launch-video for launch, demo,
  tutorial, course or explainer videos from a web app URL, a PDF manual, documents or topics.
compatibility: Linux, macOS o Windows con WSL2; GPU NVIDIA opcional (sin ella la voz corre en CPU, más lenta), Node 20+, ffmpeg, venvs de Python descritos en ./vl doctor. Escenas con givemotion (fijado en compat.json).
---

# Video de una app, un curso o un tema

`./vl` hace lo mecánico: captura segura, marca, voz, revisión, render, mezcla y entrega. Tú
haces el video: qué contar, en qué orden y cómo se mueve cada escena. No hay fases obligatorias:
usa las herramientas que el video necesite y vuelve atrás cuando haga falta.

Las escenas se escriben en **givemotion** (HTML + CSS + `gm.timeline`). Su manual queda en el
proyecto: **lee `.claude/skills/givemotion/SKILL.md` antes de escribir la primera escena.**

## Reglas de oro (no negociables)

1. **Solo lectura en la app del cliente.** Nunca crees, edites, apruebes, pagues ni envíes
   nada. `./vl explorar` y `./vl captura` bloquean escrituras y botones de acción; por eso **no
   navegues la app con MCP, Playwright ni el navegador, salvo que el usuario lo pida
   explícitamente**.
2. **Credenciales solo en variables de entorno**: en el comando (`APP_USER=… APP_PASS=… ./vl
   captura`) o en un `.env` del proyecto que crea el usuario (`vl init` lo pone en
   `.gitignore`). Nunca en archivos del proyecto, notas ni resúmenes; no leas ni muestres el
   `.env`. Pide un usuario de prueba o de solo lectura.
3. **Nada inventado que parezca real.** Capturas reales, datos que muestran la app o el manual y
   rects medidos (`capture/extracted/regions.md` o `./vl medir`). En videos explicativos y
   cursos sí se usa un **caso ficticio concreto**, siempre rotulado con el chip «Ejemplo
   ficticio» (`references/oficio.md` § El caso). Nunca una interfaz que imite un producto real.
4. **🛑 Pregunta antes de mostrar datos.** Si no sabes si son de prueba, pregunta. Si son
   reales, solo con permiso explícito y sin datos personales.
5. **Licencia comercial en todo lo que suena.** Música solo con licencia que permita el uso
   (CC0, comprada); se registra con `./vl musica … --licencia`. Un curso de pago es uso
   comercial.
6. **Ruta del proyecto sin espacios**: ffmpeg y givemotion fallan con espacios.

## Herramientas

Corre `./vl` desde la carpeta del proyecto (solo `doctor` e `init` van con la ruta completa
`~/.agents/skills/video-web/scripts/vl`). Las rutas propias de la máquina (venvs, biblioteca de
voces, `GIVEMOTION_NO_SANDBOX`) viven en `~/.config/video-web/entorno.sh`, fuera del repo.

| Para… | Comando |
|---|---|
| revisar el equipo | `vl doctor` (y `vl setup-tts` si falta el venv de voz) |
| crear el proyecto | `vl init <ruta> [--manual manual.pdf]`: plantillas, `video.html`, skill de givemotion, `./vl` |
| ver qué hay hecho | `./vl estado` (lo deduce de los archivos) |
| mirar una pantalla | `./vl explorar <url o /ruta> [--auth] [--steps '[…]']` |
| capturar la app | `./vl captura [--only a,b]` según `capture.json` → `references/captura.md` |
| recortar o medir | `./vl crop …` · `./vl medir /ruta --texto "Nombre"` |
| colores y fuentes | `./vl marca sugerir [--primary "#RRGGBB"]`, luego `./vl marca` → `marca.css` |
| voz | `./vl voz lines` con la voz del curso (`instructora-2026`, viene con la skill): genera solo las líneas que cambiaron en `SCRIPT.md` (`--frames N` o `--todas` para forzar); voz nueva: `./vl voz design` → 🛑 elige el usuario → `./vl voz guardar <nombre>` |
| música | `./vl musica <pista> --licencia "…"` (opcional) |
| revisar escenas | `./vl revisar`: `givemotion check`, hojas de cuadros y `./vl check escenas` |
| render | `./vl render` (imagen + voces + efectos) y `./vl final` (mezcla −16 LUFS, `video.vtt`, miniatura) |
| givemotion directo | `./vl gm still video.html -t 12.3 -o f.png`, `./vl gm review video.html` |
| tareas largas | `./vl esperar voz\|render`; repite hasta ✅ |
| avisos objetivos | `./vl check [captura\|marca\|guion\|voz\|escenas\|entrega\|todo]` |

`./vl check` solo avisa; lo que marca rompe la entrega, así que arréglalo o explica al usuario
por qué queda.

## 🛑 Antes del guion: para qué es el video

`BRIEF.md → formato` decide el arco, la duración y qué dice cada línea. **Si el usuario no lo
dijo, pregúntaselo**: rehacerlo después cuesta el guion, la voz y todas las escenas.

| | `lanzamiento` | `capacitacion` | `explicativo` (cápsula, tema) |
|---|---|---|---|
| Para qué | que quieran el producto | que sepan usarlo | que entiendan **una** idea y la apliquen |
| Duración | 30–120 s | 3–10 min (o módulos de 3–6) | 1–4 min |
| Cada línea | nombra lo que se verá | dice **para qué sirve** | una idea, con su ejemplo |

En los tres, **un concepto por video**: si el tema junta dos preguntas, son dos videos
(`references/oficio.md` § Un concepto por video). Detalle de los arcos: `references/oficio.md` § Guion. ¿Solo un manual escrito? Skill `manual-app`.

## Recorrido habitual

1. **Preparar:** `vl doctor`, `vl init`, leer `manual.txt` o las fuentes, `./vl explorar` las
   pantallas clave (mira las imágenes). Completa `BRIEF.md` y `capture.json`.
2. **Capturar** (si hay app): `./vl captura`. **Abre cada hoja `capture/review/capturas-N.jpg`**
   y busca errores, tablas vacías, spinners o modales que no abrieron. Repite con `--only`.
3. **Marca:** `./vl marca sugerir`, solo `primary`, `ink` y `canvas` en `capture.json → brand`
   (y `campo` si la portada va en otro color de la marca; si la marca tiene manual, sus tokens
   exactos: `references/marca.md`). **No inventes ni copies colores**. `./vl marca` escribe
   `marca.css`.
4. **Guion y voz:** `SCRIPT.md` según el `formato`, `./vl voz lines`. Lee los avisos: una línea
   marcada para revisar **se escucha antes de seguir** (§ Voz en `references/oficio.md`).
5. **Escenas:** en el comentario DIRECTION de `video.html`, el caso concreto y la lista de
   tomas con los segundos de `cues.md`. Una escena por línea en `scenes/sNN.html`, partiendo de
   las plantillas de `assets/templates/givemotion/` de la skill y del sistema de `marca.css`:
   `escena-ventana.html` para mostrar una pantalla capturada (anillos con los rects de
   `regions.md`) y `escena-ejemplo.html` para tarjetas, comparaciones y el caso concreto.
   Reglas de oficio: `references/oficio.md` § Escenas.
6. **Revisión:** `./vl revisar`, mira las hojas y el cuadro de cada escena ya armada
   (`renders/review/escenas/`); corrige hasta que `./vl check escenas` quede limpio (también
   mide escenas pobres, texto chico y lo que se pierde sobre el campo). 🛑 Muestra cuadros al usuario antes del render final.
7. **Entrega:** `./vl render`, `./vl esperar render`, `./vl final`. Entrega `renders/video.mp4`,
   `renders/video.vtt`, `renders/miniatura.png` (y el 720p si existe).

## Fuentes de contenido

| Fuente | Cómo entra |
|---|---|
| App o sitio con URL | `./vl explorar` y `./vl captura` (solo lectura) |
| Manual o documento PDF | `vl init <ruta> --manual doc.pdf` → `manual.txt` y cada página en `capture/manual/`; sus capturas, con `./vl crop --src capture/manual/pagina-NN.png` |
| Otros documentos | léelos y resume lo necesario en `BRIEF.md` |
| Investigación en la web | cada dato con su fuente en `BRIEF.md` § Fuentes |
| Imágenes de terceros | solo oficiales o con licencia libre; origen y licencia en `CREDITOS.md` |

**Modo explicativo (sin app):** `tipo: explicativo` en `BRIEF.md`, sin captura. En
`capture.json` deja solo `brand` y `fonts`. Las escenas son tipografía, diagramas, tarjetas con
el caso ficticio y números que crecen; nunca una interfaz que imite un producto.

## Referencias

| Archivo | Para qué |
|---|---|
| `references/oficio.md` | guion, voz, el caso concreto, escenas, sonido, revisión y entrega para cursos |
| `references/captura.md` | `capture.json`, login (incluido SSO), medir rects, fallos del navegador |
| `references/marca.md` | de dónde salen los colores y por qué nunca se copian de un ejemplo |
| `assets/templates/givemotion/` | `video.html` (encabezado, progreso, cámara), `escena-ventana.html` (pantalla de la app) y `escena-ejemplo.html` (tarjetas) |
| `.claude/skills/givemotion/` (en el proyecto) | el motor: timeline, cámara, revisión, códigos de check |

## Cómo trabajar

- **🛑 = decide el usuario:** datos reales, voz nueva, música y aprobación antes de entregar.
  Comparte la ruta absoluta, haz una pregunta concreta y espera. Si pidió flujo autónomo, avisa
  y sigue.
- **Mira y escucha antes de afirmar.** Abre hojas y cuadros con tu herramienta de lectura. Una
  voz con WER 0 **no** prueba que esté limpia: Whisper omite frases repetidas (`./vl check voz`
  lo detecta; si lo marca, dilo).
- **Al retomar,** corre `./vl estado` y lee los archivos del proyecto antes de preguntar.
- **Responde en el idioma del usuario.** El idioma del video lo fija `audio.json`.

## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| La captura muestra "No fue posible…" | sube `retry_wait_s` en capture.json y repite con `--only` |
| Un paso de captura "no encontré" | el texto no coincide: mira `./vl explorar` y usa el texto exacto |
| Una voz marcada para revisar | escúchala; si repite o salta algo, `./vl voz lines --frames N` |
| «SCRIPT.md cambió después de generar su voz» | `./vl voz lines`: regenera solo esas líneas |
| WER alto solo por cifras («148» frente a «ciento cuarenta y ocho») | ya no pasa: el WER compara los números en cifras; si aparece, es otra palabra |
| Aviso «de video-web 1.x» en `./vl marca` o `./vl voz` | el proyecto heredó un `capture.json` o `audio.json` viejo: renombra `dark` a `campo`, quita `bgm.prompt` y revisa `voice.library` |
| WER alto en una línea | `respell` en audio.json o reescribe la línea |
| givemotion: Chrome sale con SIGTRAP | `export GIVEMOTION_NO_SANDBOX=1` en `~/.config/video-web/entorno.sh` |
| `still` en `./vl revisar` | algo debe moverse cada ≤ 1.5 s: un revelado, la cámara o un foco |
| Sonoridad fuera de −16 LUFS | vuelve a correr `./vl final` (nunca subas el volumen a mano) |
| La GPU no tiene memoria | pide cerrar otros procesos de GPU (`vl doctor` los muestra) |
