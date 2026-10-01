# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versiones:
[SemVer](https://semver.org/lang/es/). La versión vigente está en `video-web/VERSION`.

## [1.2.0] — 2026-10-01

Lecciones de un video de capacitación real: lo que la skill ya detectaba y no mostraba, los
colores que obligaba a inventar y las escenas que cada worker construía a su manera.

### Agregado
- **`formato` en BRIEF.md** (`capacitacion` | `lanzamiento` | `explicativo`): decide el arco, la
  duración y qué dice cada línea. `./vl check guion` avisa si falta o si el guion es demasiado
  corto para el formato. Los dos arcos, en `references/oficio.md` § Guion.
- **`./vl escenas`**: un solo generador para todas las escenas con ventana, desde `scenes.json`.
  Misma geometría, colores tomados del CSS canónico de `frame.md` y anillos alineados con los
  rects. Cuatro tipos: `window`, `cover`, `close`, `steps`.
- **Captura con login SSO**: `./vl captura --profile <perfil-de-chrome>` (o `BROWSER_PROFILE`)
  usa una sesión ya abierta, sin formulario. En `capture.json`, `login.sso` y `login.ready`
  verifican que siga viva. Documentado en `references/captura.md` § Login SSO.
- **`./vl medir /ruta --texto "Nombre" [--ancho N]`**: el rect de un elemento desde el DOM, ya
  escalado, para capturas que no salieron de `./vl captura`.
- **`references/marca.md`**: de dónde sale cada color y por qué nunca se copian de un ejemplo.
- **`./vl marca sugerir --primary "#RRGGBB"`**: deriva la paleta cuando no hay `css-vars.json`,
  en vez de abortar.
- Cuatro evals nuevos: formato preguntado, capacitación que explica para qué sirve, marca sin
  colores inventados y hallazgos del navegador que no se ignoran.
- **Skill nueva `manual-app`** (independiente): manual de usuario en PDF con capturas reales.
  Reutiliza un proyecto de video-web si existe (`ml init --desde`), pero no lo necesita.

### Corregido
- **`./vl check escenas` leía mal el resultado de `hf check`.** Decidía con
  `"Check passed" in …`, y ese texto aparece aunque haya warnings dentro, porque el `ok` de la
  herramienta solo mira errores. Ocho fallos de contraste AA y seis solapes pasaron silenciosos a
  un video entregado. Ahora `./vl ensamblar` escribe también `.vl/check.json` y `.vl/lint.json`,
  y `check_findings` reporta los hallazgos con severidad `warning` e `info`, descartando los
  `content_overlap` que caen en una transición (dos escenas cruzándose es lo esperado).
- **`capture.json → brand` exigía `dark` y `spark`**, dos colores que casi ninguna app publica:
  con `marca sugerir` abortado, el camino que quedaba era copiarlos de un ejemplo, y así una app
  de marca roja salió con portada azul. Ahora solo se piden `primary`, `ink` y `canvas`; `dark`
  se deriva del primario y `spark` es un semántico con valor por omisión.
- **El contraste del chip se medía contra el lienzo**, no contra su propio fondo teñido, donde
  baja de 4.5:1. `brand.py` calcula un `chip_text` aparte y `check_marca` compone el fondo antes
  de medir.
- **Nada verificaba que la raíz del frame se llamara `root`.** Un `#root { color:#fff }` sobre un
  contenedor con otro id no aplica y el título hereda el negro del navegador; además
  `_frame_timing` se saltaba en silencio. Reglas nuevas: raíz ausente o renombrada, selectores
  CSS sin elemento, `#root` sin `color:`, ancho fijo en px junto a `white-space:nowrap` e
  imágenes mostradas con una relación de aspecto distinta a la nativa.
- `check_marca` avisa si un token tiene un tono lejano al primario: la firma de un color copiado.
- `./vl prep` publica en `assets/` todo lo que referencian las escenas, no solo los
  `asset_candidates` del storyboard.
- El 720p se genera desde 25 MB y no 30: con el límite justo, un render de 30.7 MB no se pudo
  enviar por los canales habituales.

### Cambiado
- `references/oficio.md` § Revisión: en las escenas con anillos hay que abrir los fotogramas
  completos de `renders/review/snaps/`; en la hoja de 12 no se ve un anillo corrido.
- `references/captura.md`: tabla de fallos del navegador del agente y su recuperación.
- `SKILL.md`: sección «Antes del guion: para qué es el video» y tabla de referencias.

## [1.1.0] — 2026-09-27

### Agregado
- Fuentes de contenido documentadas: app con URL, manual PDF, otros documentos, investigación
  web e imágenes de terceros (solo oficiales o con licencia libre, con `CREDITOS.md`).
- Uso de las skills de HyperFrames para motion graphics (`/motion-graphics`,
  `/hyperframes-animation`, `/hyperframes-creative`).
- README con GIF de demostración y casos de uso ampliados.

## [1.0.0] — 2026-09-27

Primera versión para el equipo, probada con hyperframes@0.8.80 (ver `video-web/compat.json`).

### Agregado
- Voz en 10 idiomas (los de Qwen3-TTS); WER por carácter en chino y japonés, y cualquier
  alfabeto en la validación (antes el cirílico daba WER 0 siempre).
- Licencia Apache-2.0.
- Modo explicativo (`tipo: explicativo` en BRIEF.md): videos sin app, con voz, música y marca.
- Voz sin GPU: CPU o MPS automáticos (`VL_DEVICE` para forzar).
- Captura: bloqueo de GET de acción (`deny_get`) y WebSockets (`websocket: true` para permitir).
- Credenciales en `.env` del proyecto; `vl init` lo agrega a `.gitignore`.
- `./vl check <id>` corre `hyperframes lint` de esa escena.
- `vl doctor` compara las skills de HyperFrames instaladas con las probadas (`compat.json`).
- `primary-text`: color de acento oscurecido para texto legible (contraste ≥ 4.5).
- Avisos de regiones no encontradas o desbordadas en `capture-report.json`.
- `marca sugerir` muestra colores calculados cuando la app no usa variables CSS.
- Mensaje con los procesos que ocupan la GPU si falta memoria.

### Cambiado
- `allow_mutations` exige ruta exacta (prefijo solo con `*` final).
- Lista negra de botones incluye verbos en inglés, `input[type=submit]` y botones de solo icono.
- Proyectos nuevos se crean con la versión de HyperFrames probada.
- Documentación genérica (sin datos de clientes) y README con requisitos y licencias.

### Corregido
- WER con `respell`: se compara contra el texto original o el respelleado (el menor).
- `asset_candidates: ninguno` ya no se toma como archivo.
- `vl init` crea `compositions/frames/`.
- `ensamblar` conserva la fecha de las escenas que no cambian.
- `vl` funciona en macOS (sin `setsid` ni `sed` de GNU).
