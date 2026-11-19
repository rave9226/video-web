# Oficio: guion, voz, escenas, sonido, revisión y entrega

Lo aprendido en videos reales: uno de producto (2:40, aprobado por el cliente), un informe de
junta directiva y el piloto de cápsula de curso para Hotmart (2026-11-18), donde voz, motor y
estilo se eligieron en pruebas a ciegas. Son punto de partida, no dogma; lo que rompe la entrega
lo avisa `./vl check`.

## Guion (SCRIPT.md)

**Formato que lee la voz** (esto sí es fijo): una cabecera `## Line N — Tema (Frame N)` por
escena, numeradas de 1 a N, con el texto hablado indentado con 4 espacios. Plantilla:
`assets/templates/SCRIPT.md`. Cada frame dura lo que dura su voz.

- **Longitud.** ≈ 2.4 palabras por segundo más pausas: 60 s ≈ 120 palabras en 5–7 líneas.
  Líneas de más de 45 palabras suenan peor en el TTS: divídelas.
- **Estilo.** Español latino neutro, frases cortas, verbos concretos ("aprueba", "firma"). Una
  sola forma de trato (tú o usted). Cada línea nombra lo que se verá en su escena.
- **Datos.** Solo lo que muestran la app o el manual. Nada de cifras ni clientes inventados.

### Un concepto por video

Cada video enseña **una sola idea**, y su arco va de la pregunta a la respuesta sin desvíos. Si
el tema junta dos preguntas («qué es X y por qué falla», «cómo se configura y cómo se reporta»),
son dos videos, o una manda y la otra no pasa de una línea al servicio de la primera. En un
piloto, una clase mezcló «qué es un modelo» con «por qué se equivoca» y hubo que separarla
después de la voz.

- **Prueba antes de escribir:** el `message` del BRIEF cabe en una frase sin «y además», y el
  título no tiene dos preguntas.
- **Prueba al terminar:** cada línea del guion sirve a esa idea; la que abre otra (un segundo
  «¿por qué?», otra definición) se corta o va al video siguiente, que el cierre anuncia.
- **Arco claro:** situación → la idea → cómo se aplica → qué te llevas. Una idea nueva a mitad
  de camino rompe el arco aunque cada línea esté bien escrita.

### El arco depende del `formato` del BRIEF

**🛑 Si el BRIEF no trae `formato`, pregúntaselo al usuario antes de escribir una línea.** Un
video para vender y uno para enseñar no se parecen en nada, y rehacerlo cuesta el guion, la voz,
la música y todas las escenas.

| | `lanzamiento` | `capacitacion` |
|---|---|---|
| Para qué | que quieran el producto | que sepan usarlo |
| Duración | 30–120 s, 5–8 líneas | 3–10 min, 12–20 líneas |
| Arco | gancho (el problema en una frase) → funciones en el orden real del usuario → control y administración → lo que ve el cliente final → cierre con el nombre | **el modelo primero** (de qué partes consta y cómo se relacionan) → una pantalla por función, **cada una con su propósito** → el vocabulario del negocio → **el orden de trabajo** al cierre |
| Cada línea | nombra lo que se verá | dice **para qué sirve**, no solo qué es |
| Cierre | el nombre del producto | el orden en que se usan las pantallas |

**En `capacitacion` esto no es opcional:**

- **Empieza por el modelo.** Antes de la primera pantalla, una escena que explique de qué partes
  consta el sistema y cómo dependen entre sí (p. ej. «hay tres niveles: los catálogos, que son los
  datos base; las relaciones, que los conectan; y los movimientos de cada mes»). Sin ese marco,
  cada pantalla se ve como un formulario suelto.
- **Cada pantalla responde "¿para qué sirve?".** No «aquí están los proveedores, con su nombre y
  su identificación», sino «aquí están los proveedores; la identificación es el dato con el que el
  sistema los reconoce al cargar una factura, y si está mal, no los encuentra».
- **Explica los verbos del negocio.** Toda app tiene palabras que solo significan algo adentro
  (causar, conciliar, legalizar, provisionar). Si la voz las usa sin explicarlas, el video no
  capacita. Y si dos marcas parecen lo mismo y no lo son, dilo.
- **Advierte de los errores.** Donde la app permite equivocarse, dilo con su consecuencia: «el
  total debe coincidir con el monto; si no, el registro llega con valores errados».
- **Cierra con el orden de trabajo**, no con el nombre del producto.

`./vl check guion` avisa de numeración rota, líneas largas, `formato` ausente y guiones demasiado
cortos para el formato que declaran; y estima la duración.

### Cápsula de curso (`explicativo` para un curso de pago)

Arco que funcionó en un curso de pago para directivos: portada (el título completo, que es la
miniatura) → la situación (el problema concreto que vive el alumno) → la idea clave → una
analogía → cómo se resuelve, en pasos numerados («Paso N de M») → la misma práctica en otra
herramienta → qué te llevas → controles → la acción de la semana → cierre con la decisión del
alumno y el nombre de la cápsula siguiente. 2–4 min, 12–14 líneas.

- **No repitas la misma idea con otras palabras en dos líneas** («dos resúmenes coincidentes
  pueden repetir errores» en la 9 y «dos respuestas coincidentes pueden repetir el mismo error»
  en la 11): el alumno lo oye como una repetición.
- **Números y fechas con letras** en el guion («setenta coma cuatro por ciento»); en pantalla,
  en cifras. Whisper los oye en cifras, y el WER los compara así (no es un error).

## Voz (Qwen3-TTS local)

### La voz sale de la biblioteca

La skill trae la voz del curso, **`instructora-2026`** (`assets/voces/`), y es la de la
plantilla: un proyecto nuevo narra con ella sin configurar nada. Las voces propias van en
`$VL_VOCES/<nombre>/` (por omisión `~/.config/video-web/voces/`) y mandan sobre las de la skill
si se llaman igual. Cada voz es `ref.wav` + `voz.json` con su `ref_text` exacto y su semilla:
**no los cambies**, son los que dan el mismo tono en todos los videos. `audio.json →
voice.library` elige la voz; `vl init` pone la de `VL_VOZ` si está definida. **No
diseñes una voz nueva por proyecto**: un curso debe sonar al mismo narrador en todas sus
cápsulas.

**Receta que ganó a ciegas** (2026-11-18, contra la voz por línea de producción, CosyVoice3 y
variantes): voz diseñada con `Qwen3-TTS-12Hz-1.7B-VoiceDesign` a partir de una instrucción de
*instructora colombiana de curso*, recortada a ~10 s + 0,6 s de silencio como referencia, y
clonada con `-Base` en **modo referencia completa** (audio + texto), una generación por línea,
semilla fija de la voz. El modo «solo huella» (x-vector) sonaba a España; forzar el seseo en el
texto no lo arregló del todo.

### Lo que hace `./vl voz lines` (y por qué)

| Paso | Por qué |
|---|---|
| Recorta la frase de la referencia que el clon dice antes de la línea | el clon **arrastra la última frase del `ref_text`** al inicio de cada toma. Si la línea empieza con esa misma frase, recortar «donde empieza la línea» conservaba las dos: así llegó una frase doble a un video |
| Detector de habla oculta: huecos > 1 s que no son silencio y < 2,3 palabras/s | **Whisper transcribe una frase repetida una sola vez**: el WER sale 0 con una frase doble. Las líneas sanas miden 2,6–3,4 palabras/s |
| Reintenta con otra semilla las líneas con WER alto o habla oculta | lo que falla una vez casi nunca falla con otra semilla |
| −18 LUFS por línea, 48 kHz mono | el master final (`./vl final`) lleva todo a −16 |

**La voz sigue al guion por contenido.** Cada toma guarda la huella del texto, la voz y el
`respell` con que se generó (`assets/voice/firmas.json`). `./vl voz lines` genera solo las líneas
nuevas o cambiadas (`--todas` las rehace todas) y, si `SCRIPT.md` cambia mientras corre o
después, la línea queda marcada y `./vl check voz` lo avisa: un video salió con cuatro líneas
del guion anterior.

**Una línea marcada «revisar» se escucha antes de seguir.** Nunca digas que la narración está
limpia apoyándote solo en el WER.

### Diseñar una voz nueva (solo si el usuario la pide)

1. En `audio.json`: `voice.ref_text` de 20–30 palabras en el idioma del video, **sin nombres
   de otro idioma** (bajan P(idioma) y ninguna candidata pasa). `instructs` en el idioma del
   video, describiendo a una hablante **nativa de una ciudad concreta** (un instruct en inglés da
   acento extranjero; `voice.py` lo rechaza).
2. `./vl voz design` y `./vl esperar voz`: candidatas ordenadas por P(idioma) ≥ 0,99 (el único
   umbral que detecta el acento extranjero), WER, tono y ritmo.
3. 🛑 El usuario elige **de oído, a ciegas** (sin decirle cuál es cuál).
4. `./vl voz guardar <nombre>` la guarda en la biblioteca para todos los proyectos.

**Respell** (`audio.json → respell`): solo cambia lo que oye el TTS: `{"Claude": "Clod",
"CRM": "ce erre eme"}`. Si una sigla suena mal, ahí se arregla.

### Otros idiomas

Qwen3-TTS habla 10 idiomas: español, inglés, portugués, francés, alemán, italiano, ruso,
chino, japonés y coreano. Para otro que no sea español, en `audio.json` cambia
`voice.language` (nombre en inglés: `"English"`, `"Portuguese"`, `"French"`, `"German"`,
`"Italian"`, `"Russian"`, `"Chinese"`, `"Japanese"`, `"Korean"`), `voice.whisper_lang`
(código ISO: `en`, `pt`, `fr`, `de`, `it`, `ru`, `zh`, `ja`, `ko`), `ref_text` e
`instructs` en ese idioma, y escribe `SCRIPT.md` en él. En `BRIEF.md`, `language`. El ritmo de
≈ 2.4 palabras por segundo es del español; en chino y japonés el WER se mide por carácter.
Probado: inglés y portugués de Brasil (WER 0, P(idioma) > 0.98). Fuera de esos 10 idiomas,
la voz local no sirve.

## El caso concreto (lo que más subió la calidad)

En el video en producción las tarjetas mostraban **barras grises** en lugar de texto: el ojo no
tenía qué leer mientras la voz explicaba. La versión que ganó usa **un solo caso ficticio que
recorre toda la cápsula** (p. ej. un «Informe de ventas del tercer trimestre» con cuatro
afirmaciones y un resumen de IA con una cifra que no está en el informe).

- Rotula cada documento inventado con el chip `.chip.fic` «Ejemplo ficticio».
- Cifras coherentes entre escenas; ninguna que parezca un dato real de alguien.
- 3–4 afirmaciones legibles por tarjeta, nunca más de 12 palabras visibles por tarjeta.
- Si el curso tiene un prompt o una plantilla, **muéstralo escrito** en una ventana de
  conversación genérica (sin logos ni colores de Claude o ChatGPT) con sus marcadores en acento.

## Escenas (givemotion)

Lee `.claude/skills/givemotion/SKILL.md` en el proyecto (y solo las 1–3 recetas que el video
necesite: `camera-moves`, `text-reveals`, `numbers-and-charts`, `scene-transitions`).

**Estructura** (plantillas en `assets/templates/givemotion/` de la skill):

- `video.html`: comentario DIRECTION (look, caso, lista de tomas con segundos de `cues.md`),
  `marca.css`, la secuencia de `<gm-include src="scenes/sNN.html">`, encabezado fijo y barra de
  progreso. **El encabezado se arma solo** desde los atributos de cada escena:
  `data-seccion="CÓMO LO RESUELVES"` y `data-paso="2 de 4"`; sin `data-seccion` la escena va
  sin encabezado (portada y cierre, sobre `.campo`).
- `scenes/sNN.html`: una por línea del guion, con su voz `<audio src="assets/voice/NN.wav">`,
  `data-duration` = voz + 0,6 s (+1,2 s antes de un cambio de sección). Parte de
  `escena-ejemplo.html` (tarjetas y caso) o de `escena-ventana.html` (una pantalla capturada).
- **Pantallas de la app** (`escena-ventana.html`): la captura a 2x dentro de `.win`, los
  anillos con `data-rect` **copiado de `capture/extracted/regions.md`** (o de `./vl medir`), y
  el foco de `sceneCam` sobre el anillo que nombra la voz. `video.html` los escala solos.
- **Colores solo de `marca.css`**: `var(--token)` en CSS y `C('token')` en los tweens. Un hex en
  una escena hace que la marca siguiente herede los colores de este video
  (`./vl check escenas` lo avisa).

**Reglas que separaron el video ganador del original:**

| Regla | Antes | Ahora |
|---|---|---|
| Texto mínimo | 16–22 px | pensado para celular: ver «Mínimos para celular» abajo (`escenas.css` ya los trae) |
| Lienzo | contenido hasta el 64 % del alto | la composición va de y ≈ 200 a 900; tarjetas que llenan el ancho (≥ 70–80 %) con texto real del caso, nunca barras grises como contenido |
| Franja inferior | vacía o con contenido | y > 900 libre para los subtítulos de la plataforma |
| Quietud | portada fija 13 s, tramos de 4–6 s | algo se mueve cada ≤ 1,5 s; la portada está armada en t = 0 pero respira (push lento, motivo que se anima en su palabra) |
| Foco | ninguno | un foco por escena con `sceneCam(world, dur, {at, back, fit, dim})`: zoom ≤ 1,25 a lo que nombra la voz, el resto atenuado; el título vive fuera del mundo y nunca se tapa |
| Sincronía | aproximada | cada revelado 0,04–0,08 s antes de su palabra en `cues.md` |
| Estados | colores sueltos | verde = respaldado (`.row.ok`, `.chip.ok`), rojo = no aparece (`.row.bad`, `.st.bad`), acento = la idea clave |

**Estilo por defecto: «calma con intención».** `video.html` y `escenas.css` lo traen hecho:

- *Aprobado:* cámara casi quieta con `calma(escena, mundo, dur, [[t, 1.05]], origen)`: deriva muy
  lenta y, en 3–4 momentos del video, un empuje de ≤ 1,06 hacia lo que nombra la voz, con un solo
  origen por escena acotado a la caja de contenido (x 156–1764, y 272–878) para que nada cruce los
  márgenes; un solo empalme lateral suave para todo el video (`push-left 0.8 in-out-sine`); morph
  solo donde el MISMO objeto continúa (`data-morph` en ambas escenas, y el titular de la que entra
  con `T(…, entra)`); el movimiento cuenta la idea al ritmo de `cues.md`; lo nuevo nace de algo ya en
  pantalla; el encabezado se apaga antes del corte y se enciende cuando el empalme termina.
- *Rechazado:* zooms de 1,3–1,5× y regresos de cámara, transiciones mezcladas (un empalme distinto
  por escena), barridos de luz o degradados que cruzan la pantalla (parecen un error de render).
- `sceneCam` (foco con zoom hasta 1,25) queda solo para pantallas capturadas, donde hay que acercarse
  a un anillo para que se lea.

**Mínimos para celular** (el video se ve a ~480 px de ancho, escala 0,25): texto principal ≥ 64 px,
nada < 36 px, ≤ 12 palabras visibles por escena, un foco que ocupe ≥ 70 % del ancho útil, márgenes de
96 px. Sin «→» si la fuente de la marca no lo trae (Geist no): usa una forma o un hilo.

**Antes de renderizar:** mira la hoja de cuadros reducida a 480 px (`ffmpeg -i hoja.png -vf scale=480:-1
hoja-480.png`) y **3 cuadros por empalme** (el último de la escena que sale, uno a mitad del empalme, el
primero estable de la que entra); si algo se ve cortado, encimado o ilegible así, está mal aunque
a 1920 px se vea bien.

**Portada y cierre (`.campo`):** el texto va en `var(--on-campo)` y, sobre un relleno de
acento, en `var(--on-accent)`; nunca `var(--bg)` ni blanco fijo (con un campo claro no se lee).
Si el campo es del color del acento, una burbuja, un botón o un punto de acento desaparece
sobre él: ahí va en `var(--bg)` con texto `var(--accent-text)`. El mensaje final no se atenúa
(opacidad ≥ 0,85): givemotion lo da por legible por ser grande, pero no se lee bien.

**Errores de givemotion 0.1.6 ya resueltos en la plantilla** (no los vuelvas a descubrir):
`gm.timing(<última escena>).end` devuelve un negativo (usa inicio + `data-duration`); fuera de `gm.onFrame`, `gm.timing()` devuelve 0 para todas las escenas (léelo dentro); un
`gm.timeline()` sobre elementos fuera de la secuencia no aplica sus tweens (usa `gm.onFrame`);
los `data-expect` usan tiempo del video, no de la escena; una clase global (`.blue`) se cuela en
`.chip.blue` sin aviso: usa los nombres de `marca.css`.

## Sonido

- **Música:** solo con licencia comercial: CC0 (p. ej. el catálogo de FreePD) o comprada.
  `./vl musica <pista> --licencia "…"` la copia y la anota en `CREDITOS.md`. **MusicGen ya no
  se usa: es CC-BY-NC** y un curso de pago es uso comercial.
- **Mezcla** (`./vl final`): plena antes de la primera palabra, `bgm.under_voice_db` (18 dB) bajo
  la voz, +6 dB en las pausas, +9 dB en los cambios de sección (`bgm.secciones`: números de
  escena), fundido de 2 s al final.
- **Efectos:** discretos, 18–22 dB bajo la voz: clic suave en cada check, «pop» en la entrada de
  una tarjeta importante (no en todas), barrido corto en los cambios de sección. La librería de
  `media-use` (`~/.agents/skills/media-use/audio/assets/sfx/`) es de licencia Pixabay, apta para
  uso comercial. Van como `<audio … data-start data-volume>` dentro de la escena.
- **Master:** −16 LUFS integrados, pico ≤ −1,5 dBTP, 48 kHz estéreo.

## Revisión

`./vl revisar` corre `givemotion check` (guardado en `.vl/check.json`), las hojas de cuadros en
`renders/review/`, **un cuadro por escena al 65 % de su duración** en `renders/review/escenas/`
(las hojas automáticas pueden caer al inicio de una escena, cuando aún está vacía) y `./vl check
escenas`, que además de givemotion avisa de:

- **escena pobre:** en su cuadro, el contenido ocupa < 60 % del ancho, < 40 % del alto útil o
  < 3 % del área (las escenas aprobadas del piloto miden ≈ 90 %, 95 % y 5–20 %);
- **texto chico:** `font-size` menor de 24 px (givemotion solo avisa bajo 22);
- **texto con `color: var(--bg)`** y lo que se pierde o se atenúa sobre el campo (§ Escenas).

**Abre las hojas y mira.** Para un momento exacto:
`./vl gm still video.html -t 12.3 -o f.png`. Revisa:

1. Ningún texto cortado, encimado ni menor de 24 px.
2. El tercio inferior no queda vacío en escenas de contenido; nada importante bajo y = 900.
3. El foco cae sobre lo que nombra la voz y no se mete bajo el encabezado.
4. Ningún tramo `still` > 6 s (los más cortos, sincronizados con la voz, son el estilo calma y no se avisan); ninguna escena arranca quieta.
   Con el estilo calma, la hoja de 480 px y los 3 cuadros por empalme de § Escenas.
5. Colores y logo de `marca.css`; el caso ficticio rotulado.
6. Cortes limpios entre escenas.

Avisos de givemotion: ✖ y ⚠ son fallas reales salvo que sean a propósito (dilo); ℹ son estilo.
Para un juicio independiente, pide una crítica a un subagente que no haya visto el código
(`./vl gm review video.html` arma su material).

## Entrega (plataformas de cursos)

`./vl render` (imagen + voces + efectos, CRF 16) y `./vl final`:

| Archivo | Para qué |
|---|---|
| `renders/video.mp4` | 1080p30 H.264 de alta calidad: Hotmart y similares recodifican y no mejoran la calidad |
| `renders/video.vtt` | subtítulos desde los tiempos de la voz con la ortografía del guion («cero», no «0»); ≤ 2 líneas de ≤ 42 caracteres |
| `renders/miniatura.png` | el primer cuadro (la portada) |
| `renders/video-720p.mp4` | solo si el original pesa más de 25 MB, para compartir por correo o chat |

Hotmart: hasta 20 GB por archivo y 3 videos por clase; acepta subtítulos `.srt` o `.vtt`.
