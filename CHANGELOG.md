# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versiones:
[SemVer](https://semver.org/lang/es/). La versión vigente está en `video-web/VERSION`.

## [2.3.0] — 2026-11-19

El estilo aprobado de las clases de un curso (calma con intención) pasa de ser un kit de proyecto a
ser el método por defecto de la skill.

### Añadido
- **Plantilla `video.html`:** `calma()` (cámara casi quieta, empuje ≤ 1,06, un origen por escena
  acotado a la caja de contenido), `T()` (titular con palabra clave), `AN()` (anillo al aterrizar),
  ambiente de fondo, encabezado con fundidos correctos entre escenas y un solo empalme lateral
  suave (`push-left 0.8 in-out-sine`). `sceneCam` se conserva para pantallas capturadas.
- **`assets/templates/escenas.css`:** componentes de escena para celular (hoja, caja, burbuja,
  fila, chip, sello, hilo, anillo, ambiente) sobre los tokens de `marca.css`. `vl init` lo copia y
  la plantilla lo enlaza.
- **`oficio.md` § Escenas:** estilo por defecto, lo rechazado, mínimos para celular y revisión
  a 480 px con 3 cuadros por empalme.
- **GPU:** `vl voz` y `vl render` toman un candado (`flock`) y comprueban memoria libre antes de
  empezar; mensaje claro si falta. Nuevo `vl gpu`.

### Cambiado
- El aviso `still` de `check escenas` ya no castiga tramos quietos de ≤ 6 s (pasos pequeños
  sincronizados con la voz); los más largos siguen avisando.

## [2.2.0] — 2026-11-18

Lecciones de las dos primeras clases de un curso producidas con 2.1: cada tropiezo que hubo que
parchar desde fuera de la skill es ahora una corrección o un aviso.

### Corregido
- **Marca:** `./vl marca` respeta los tokens que fija la marca (`muted`, `accent-text`,
  `accent-bg`, `line`, `surface`, `campo`, `ok`, `ok-bg`, `bad`, `bad-bg`) en vez de
  aproximarlos. La clave `dark` de 1.x se ignoraba en silencio y la portada salió del primario
  oscurecido (#08163C) en vez del azul de la marca: ahora pasa a `campo` con un aviso, y las
  claves desconocidas se avisan. `./vl marca sugerir` ya no propone `dark`.
- **Texto sobre fondos de marca:** tokens nuevos `--on-campo` y `--on-accent` (blanco o tinta,
  el que contraste); portada, cierre, chip sólido y barra de progreso los usan en vez de
  blanco fijo. `./vl check marca` mide también el texto sobre el campo, sobre el acento y el
  gris sobre la superficie.
- **Voz desfasada:** cada toma guarda la huella de su texto, su voz y su `respell`
  (`assets/voice/firmas.json`). `./vl voz lines` genera solo las líneas nuevas o cambiadas
  (`--todas` para rehacerlas) y una línea cuyo guion cambió después de generarse queda en
  revisar; `./vl check voz` lo avisa, igual que una voz distinta de la de `audio.json`.
- **Falsos REV por números:** el WER compara los números en cifras («ciento cuarenta y ocho»
  = «148», «mil quinientos» = «1.500», «coma» y «%»).
- **Configuraciones de 1.x:** un `audio.json` viejo (`bgm.prompt` de MusicGen, referencia en la
  skill 1.x) se migra en memoria y se avisa en `./vl voz` y `./vl check voz`, con la voz de la
  plantilla.

### Agregado
- `./vl revisar` saca un cuadro de cada escena al 65 % de su duración
  (`renders/review/escenas/`, tiempos de `givemotion inspect`): las hojas automáticas podían
  caer en el inicio vacío de una escena.
- `./vl check escenas` avisa de escenas pobres (medidas en ese cuadro: ancho, alto y área que
  ocupa el contenido), texto menor de 24 px, `color: var(--bg)`, rellenos de acento que se
  pierden sobre un campo del mismo color y texto atenuado en portada y cierre.
- `references/oficio.md` § Un concepto por video: una sola idea y un arco claro en todo
  formato; el `message` del BRIEF lo pide.

## [2.1.0] — 2026-11-18

### Agregado
- **La voz del curso viene con la skill:** `assets/voces/instructora-2026` (la que ganó la
  prueba a ciegas) y es la voz por omisión de la plantilla. Todo el equipo narra con el mismo
  tono sin configurar nada. `voice.py` busca la voz primero en `$VL_VOCES` (las propias mandan)
  y luego en la skill; `vl doctor` lista ambas.

## [2.0.0] — 2026-11-18

Piloto de una cápsula de un curso de pago en Hotmart: la voz, el motor y el
estilo se eligieron en pruebas a ciegas; los fallos que el usuario encontró son ahora reglas.
**Rompe proyectos 1.x** (escenas HyperFrames): se terminan con la 1.2.0.

### Cambiado
- **Escenas con givemotion** (MIT, versión fijada en `compat.json`) en vez de HyperFrames: ganó
  la comparación a ciegas de dos escenas idénticas. `vl init` instala su skill en el proyecto;
  `video.html` trae encabezado, sección, «Paso N de M», barra de progreso y cámara con foco
  (`sceneCam`) calculados desde los atributos de cada escena. Comandos nuevos: `./vl revisar`
  (givemotion check + hojas), `./vl gm …`; `./vl render` + `./vl final`.
- **Marca:** `./vl marca` escribe `marca.css` (fuentes locales, tokens y componentes del sistema
  visual ganador) en vez de `frame.md`. `./vl check marca` mide cada texto sobre su fondo.
- **Voz:** biblioteca de voces fuera del repo (`audio.json → voice.library`,
  `~/.config/video-web/voces/`), `./vl voz guardar`; clon con referencia completa (la receta que
  ganó a ciegas); salida a 48 kHz. Rutas de la máquina en `~/.config/video-web/entorno.sh`.
- **Música solo con licencia comercial:** `./vl musica <pista> --licencia "…"` (anota en
  `CREDITOS.md`). `./vl final` mezcla con la música que baja con la voz y sube en las secciones,
  y masteriza a −16 LUFS / −1,5 dBTP.

### Agregado
- **Entrega para cursos:** `renders/video.vtt` con la ortografía del guion y `miniatura.png`.
- **Detector de habla oculta:** Whisper transcribe una frase repetida una sola vez (WER 0); una
  frase doble llegó así al piloto. `voice.py` marca huecos con habla y ritmo < 2,3 palabras/s,
  reintenta, y `./vl check voz` lo muestra.
- `./vl check escenas`: una escena por voz, duración ≥ voz, inclusión en `video.html`, sin
  colores en hexadecimal y los avisos de givemotion.
- `references/oficio.md`: el caso concreto rotulado «Ejemplo ficticio», tamaños mínimos, lienzo,
  foco, quietud ≤ 1,5 s, sonido, entrega; los fallos conocidos de givemotion 0.1.6.
- Evals: voz sin frases repetidas y cápsula de curso con entregables.

### Corregido
- **Frase dicha dos veces:** el clon arrastra la última frase de la referencia; si la línea
  empezaba igual, el recorte conservaba ambas. Ahora se recorta la frase arrastrada.

### Eliminado
- HyperFrames y sus dependencias internas (`product-launch-video`, `media-use`),
  `assets/galeria/`, `scenes.py`, `qa.py`, `bgm.py`, `./vl prep|escenas|ensamblar|snap` y
  MusicGen (CC-BY-NC: no sirve para cursos de pago).

## [1.2.0] — 2026-10-01

Lecciones de un video de capacitación real: lo que la skill ya detectaba y no mostraba, los
colores que obligaba a inventar y las escenas que cada worker construía a su manera.

### Agregado
- **La receta de voz es el comportamiento por defecto.** El instruct `es` de `audio.json` (mujer
  colombiana de Bogotá, nativa) es el que produjo la voz aprobada; ahora `./vl voz design`
  **mide tono y ritmo** de cada candidata (f0 por autocorrelación y palabras/s con Whisper) y las
  ordena primero por perfil cumplido. `voice.perfil` trae los rangos probados (f0 230–275 Hz,
  2.0–2.6 palabras/s) y `gates.ref_min_p_lang` sube de 0.97 a **0.99**, que es el único umbral
  que detecta el acento extranjero: la referencia que sonaba a inglés daba 0.90 y las buenas dan
  0.998–1.0. La elección final sigue siendo del usuario, de oído.
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
- **Skill nueva `manual-app`**, al mismo nivel que el video y no como un extra: manual de usuario
  en PDF con capturas reales, una sección por pantalla con su propósito y el orden de trabajo.
  Funciona sola (Python con `markdown` y `playwright`: ni GPU, ni Node, ni ffmpeg) y reutiliza un
  proyecto de video-web si existe (`ml init --desde`).

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
