# Oficio: guion, voz, música, storyboard, escenas y revisión

Consejos sacados de un video real de producto (2:40 min, aprobado por el cliente). Son punto de partida, no
reglas: cámbialos cuando el producto o el usuario pidan otra cosa. Lo que rompe el render lo
avisa `./vl check`; lo demás es criterio tuyo.

## Guion (SCRIPT.md)

**Formato que lee la voz** (esto sí es fijo): una cabecera `## Line N — Tema (Frame N)` por
escena, numeradas de 1 a N, con el texto hablado indentado con 4 espacios. Plantilla:
`assets/templates/SCRIPT.md`. Cada frame dura lo que dura su voz.

- **Longitud.** ≈ 2.4 palabras por segundo más pausas: 60 s ≈ 120 palabras en 5–7 líneas.
  Líneas de más de 45 palabras suenan peor en el TTS: divídelas.
- **Arco que funcionó:** gancho (el problema en una frase) → funciones en el orden real del
  usuario → control y administración → lo que ve el cliente final → cierre con el nombre del
  producto. Un tutorial o un video de un solo módulo puede tener otro arco.
- **Estilo.** Español latino neutro, frases cortas, verbos concretos ("aprueba", "firma"). Una
  sola forma de trato (tú o usted). Cada línea nombra lo que se verá en su escena.
- **Datos.** Solo lo que muestran la app o el manual. Nada de cifras ni clientes inventados.

`./vl check guion` avisa de numeración rota y líneas largas, y estima la duración.

## Voz (Qwen3-TTS local)

1. En `audio.json`, escribe `voice.ref_text`: 20–30 palabras en el idioma del video sobre el
   producto. Si su nombre es de otro idioma ("Books to Scrape" en un video en español), déjalo
   fuera de `ref_text`: baja P(idioma) y ninguna candidata pasa; en las líneas del guion usa
   `respell`. Los `instructs` van en el idioma del video y describen a una hablante **nativa**
   de una ciudad concreta; un instruct en inglés para otro idioma da acento extranjero
   (`voice.py` lo rechaza).
2. `./vl voz design` y `./vl esperar voz`: 3 candidatas por instruct, ordenadas por P(español)
   y WER.
3. 🛑 Envía al usuario las rutas de las mejores (✓) y deja que elija de oído. Pon su elección en
   `audio.json` → `voice.ref_audio`. Si ya hay una voz aprobada de otro proyecto, puedes
   reusarla con la misma `ref_text`.
4. `./vl voz lines` y `./vl esperar voz`: clona cada línea, reintenta con otra semilla las de
   WER alto, nivela a −18 LUFS y escribe `audio_meta.json` y `cues.md` (segundo de cada palabra).

Si una línea no pasa: mira qué oyó Whisper. Si pronuncia mal una marca o sigla, agrégala a
`respell` (p. ej. `{"Wompi": "Uómpi", "CRM": "ce erre eme"}`; solo cambia lo que oye el TTS) y
repite `./vl voz lines --frames N`. Si cambias una línea del guion, repite solo esa.

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

## Música (opcional)

**Licencia.** `facebook/musicgen-small` es CC-BY-NC-4.0: úsalo solo en videos internos o no
comerciales. 🛑 Si el video es comercial (cliente, redes, ventas), pide una pista con licencia,
cópiala a `assets/bgm/track.wav` y corre solo `./vl musica mezclar`; o entrega sin música.

`./vl musica` y `./vl esperar musica`: MusicGen genera la pista con `bgm.prompt` (2–6 min),
calibra el volumen `under_voice_db` (12.5 dB) por debajo de la voz y arma
`renders/preview-audio.mp3`. 🛑 Envíalo al usuario. Más música → baja `under_voice_db`; menos →
súbelo; luego `./vl musica mezclar` (instantáneo). Otro estilo → cambia el prompt y regenera.
Sin música: sáltate este paso; el ensamblador acepta `bgm: null`.

## Storyboard (STORYBOARD.md)

**Campos que necesitan los scripts de ensamblado** (fijos), un bloque por línea del guion:

```markdown
## Frame N — Título corto

- src: compositions/frames/fNN-<slug>.html   (NN con dos dígitos; slug en minúsculas)
- duration: 11.59s                            (`./vl prep` lo sincroniza con la voz)
- transition_in: crossfade                    (cut, crossfade, blur-crossfade,
                                               push-slide LEFT, zoom-through, squeeze)
- status: animated
- voiceover: "<la línea N de SCRIPT.md>"
- asset_candidates: assets/a.png — qué es; assets/b.png — qué es
```

Todo lo demás es libre: describe la escena como quieras que la construya el worker. Lo que
mejor funcionó fue concreto: líneas `Scene N (a–bs): …` con el segundo de cada revelado sacado
de `cues.md` y los rects `[x,y,w,h]` copiados de `capture/extracted/regions.md`. Un storyboard
vago da escenas genéricas. Ejemplo completo: `assets/templates/STORYBOARD.md`.

**Ideas de forma.** `assets/galeria/INDICE.md` lista 12 escenas reales de ese video
(ventana con zoom, clic que abre modal, comparación, tarjetas, stepper, cierre con logo…).
Úsalas como inspiración o punto de partida, o busca otra forma en `/hyperframes-animation`
(blueprints): un campo opcional `- blueprint: <id>` en el bloque mete ese blueprint en el
paquete del worker. Consejos de ritmo: alterna escenas densas con respiros y varía las transiciones
(`zoom-through` para cambios de sección).

**Escenas sin capturas (modo explicativo).** Una idea por escena, dicha en pantalla con 3–6
palabras; la voz explica el resto. Formas que funcionan: título cinético (palabra a palabra en
su cue), diagrama que se construye nodo a nodo, número grande que cuenta hasta su valor,
comparación en dos columnas, lista que se revela ítem a ítem y cierre con la idea central. Sin
`asset_candidates` de capturas: iconos o formas simples en SVG inline con los colores de
`frame.md`. Cada cifra o nombre en pantalla debe estar en el texto del usuario.

**Video direction.** Después del frontmatter (`format`, `duration`, `message`, `music`), un
bloque `## Video direction` con la paleta por rol, cómo se muestran las pantallas, el
movimiento y lo prohibido (UI inventada, datos falsos, stock, emojis).

`./vl prep` sincroniza duraciones, copia los assets a `assets/`, arma un paquete por escena en
`.hyperframes/frame-packets/` y corre `./vl check storyboard`.

## Escenas

Cada escena es `compositions/frames/fNN-slug.html`. Puedes escribirlas tú o despachar un worker
por escena (hasta 4 en paralelo; Claude Code: `Agent` con `general-purpose`; OpenCode: `task`
con `general`). Prompt sugerido:

```text
Eres el worker de la escena <id> de un video HyperFrames. Trabaja solo en <ruta>.
Lee <ruta>/.hyperframes/frame-packets/_role.md, <ruta>/.hyperframes/frame-packets/<id>.md,
<skill>/references/oficio.md § Escenas (ruta de la skill: `dirname $(dirname $(readlink -f ./vl))`), y los cues y rects de
tu frame en <ruta>/cues.md y <ruta>/capture/extracted/regions.md. Si tu bloque cita un ejemplo
de assets/galeria/, adáptalo. Crea <ruta>/compositions/frames/<id>.html y corre
`./vl check <id>` desde <ruta> hasta ✅ (esto manda sobre el "no corras la CLI" de _role.md). No edites otros archivos. Responde en una línea.
```

**Lo que rompe el render** (lo avisa `./vl check <id>`):

- Id = nombre del archivo (`f06-planes`): `data-composition-id="f06-planes"`, todos los ids
  empiezan por `f06-` (un id que empieza con dígito rompe el CSS) y el timeline se registra
  en `window.__timelines["f06-planes"] = tl;`.
- `gsap.timeline({ paused: true })`; nada de `Math.random`, `Date.now`, `repeat: -1` ni `yoyo`
  (si algo va y vuelve, dos tweens).
- Sin fuentes de red (usa el `@font-face` de `frame.md`), sin `<audio>`, solo imágenes de
  `assets/`.
- `data-duration` de la raíz y de los clips de fondo = duración exacta del frame; si quedan más
  cortos, la transición sale en blanco.

**Lo que se ve bien:**

- Rects en píxeles de la imagen nombrada: escálalos con el mismo factor con que la muestras
  (2880 px mostrada a 1120 px → × 1120/2880); no los estimes a ojo.
- Cada revelado cae en el segundo de su palabra en `cues.md` (0.04–0.08 s antes). La segunda
  mitad también revela algo; al final la escena se sostiene quieta.
- Etiquetas cortas en pantalla (eyebrow, h2 de 3–6 palabras, chips); repetir la frase de la voz
  entera suele sobrar, salvo en gancho y cierre.
- Zoom ≤ 1.6 sobre capturas con poco contenido. Nada importante en el 17 % inferior.
- `frame.md` manda sobre colores, fuente y el CSS de ventana, eyebrow, chip y anillo.

## Ensamblado

`./vl ensamblar` arma `index.html` con voz y música, inyecta transiciones y corre `hyperframes
lint` (`.vl/lint.txt`) y `check` (`.vl/check.txt`). No edites `index.html` a mano: se regenera.

| Hallazgo | Arreglo |
|---|---|
| `content_overlap` entre palabras de un mismo título | `data-layout-allow-overlap` en el contenedor más pequeño de esas palabras |
| `content_overlap` entre dos textos | mueve uno o haz que el otro salga antes |
| `text_clipping` / `container_overflow` | ensancha la caja o baja la fuente; no lo escondas con `overflow: hidden` |
| `primary-offscreen` | revisa `left`/`top` y la cámara; limita el foco del zoom con `clamp` |
| `id_requires_css_escape` | prefijo `fNN-`, nunca `NN-` |
| `timeline_track_too_dense` | vuelve a correr `./vl ensamblar` |
| timeline no registrado o duración 0 | falta `window.__timelines["<id>"] = tl` o el id no coincide |

## Revisión visual

`./vl snap` toma inicio, medio y final de cada escena y cada corte, y arma
`renders/review/escenas-N.jpg`. **Abre cada hoja y mírala.** Revisa:

1. Ningún texto cortado ni encimado.
2. Cada ventana muestra la pantalla correcta, sin error ni spinner; ningún zoom la deja vacía.
3. El anillo o la píldora cae sobre lo que nombra la voz.
4. Colores y logo de `frame.md`.
5. El medio muestra más que el inicio (si `qa-report.json` marca "sin movimiento", revísala).
6. Cortes limpios, sin cuadro negro.
7. Nada importante en el 17 % inferior.

Corrige y repite con `./vl snap --frames 4,6`. 🛑 Envía las hojas al usuario antes del render.

## Render y entrega

`./vl render` (10–25 min, en segundo plano), `./vl esperar render` hasta ✅ y `./vl final`
(métricas, grilla y 720p si pesa > 30 MB; corre `./vl check entrega`). Entrega
`renders/video.mp4`, el 720p si existe y `renders/review/final-grilla.jpg`.
