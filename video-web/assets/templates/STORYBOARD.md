---
format: 1920x1080
duration: 45s
message: "Todo el ciclo de la afiliación de salud visual en una sola plataforma."
music: uplifting corporate tech underscore, warm piano and soft synth pads, 100 bpm
---

<!-- EJEMPLO REAL (Acme). Reemplaza TODO por tu producto: títulos, voiceover (copiado de
SCRIPT.md), imágenes de capture/assets, rects de ui-regions.json y segundos de cues.md.
Un bloque "## Frame N" por línea del guion, en el mismo orden. Fijos: src, duration,
transition_in, status, voiceover y asset_candidates. El resto (ejemplo, scene, roles, líneas
Scene) es libre: escribe lo que el worker necesite para construir la escena. -->

## Video direction

- **Paleta por rol (frame.md)** — escenas de contenido sobre `bg`, pantallas en `surface`,
  títulos en `text`, apoyo en `text-muted`, eyebrows, números y chips en `primary`. Portada y
  cierre sobre `brand-dark` con tipografía blanca. `brand-spark` solo para anillos de foco.
- **Pantallas** — siempre capturas reales dentro de la ventana canónica de frame.md. Columna de
  texto a la izquierda (x≈110–640) y ventana a la derecha (≈1120×700).
- **Rects** — todo `[x,y,w,h]` sale de ui-regions.json, en píxeles de la imagen nombrada.
- **Movimiento** — asentamientos `power3.out`, sin rebotes. Zoom ≤ 1.6 sobre la zona que la
  voz nombra. Revelado al ritmo de la voz (segundos de cues.md) y quietud al resolver.
- **Prohibido** — UI inventada, datos falsos, fotos de stock, gradientes morados, emojis,
  palabras en inglés en pantalla (salvo nombres de producto), nada importante en el 17 %
  inferior, mascota fuera de portada/cierre.

## Frame 1 — Muchos pasos, un solo lugar

- ejemplo: galeria/hook-steps-to-logo.html
- src: compositions/frames/f01-hook.html
- duration: 19.75s
- transition_in: cut
- status: animated
- voiceover: "Una afiliación de salud visual tiene muchos pasos: el interesado, los términos, la firma, el pago, los documentos, la activación… y, un año después, la renovación. Ahora, todo ese recorrido vive en un solo lugar: la Plataforma de Afiliaciones de Acme Salud."
- scene: Sobre fondo oscuro, los pasos aparecen como estaciones de un recorrido y colapsan en el logo
- focal: assets/brand-logo-blanco.png
- asset_candidates: assets/brand-logo-blanco.png — logo en blanco para fondo oscuro

Scene 1 (0.0–11.0s): título "Una afiliación de salud visual tiene muchos pasos" arriba a la izquierda; siete estaciones con icono y etiqueta (Interesado 3.9 · Términos 4.8 · Firma 5.7 · Pago 6.4 · Documentos 7.2 · Activación 8.3 · Renovación 10.5) aparecen en su palabra sobre una línea que se dibuja.
Scene 2 (11.0–19.75s): en "todo ese recorrido" (12.4) las estaciones convergen al centro y se funden; el logo blanco se revela (15.2) con el subtítulo "Plataforma de Afiliaciones" (17.0). Sostener.

## Frame 2 — Todo empieza con un lead

- ejemplo: galeria/window-feature-zoom.html
- src: compositions/frames/f02-leads.html
- duration: 11.59s
- transition_in: crossfade
- status: animated
- voiceover: "Todo empieza con un lead. Llegue por formulario, chatbot, referido o carga de archivos, avanza por un embudo claro: captura, elegibilidad, cotización y cierre."
- scene: La pantalla de Leads con sus canales de origen y el embudo por etapas resaltado pestaña a pestaña
- focal: assets/app-leads.png
- asset_candidates: assets/app-leads.png — listado de leads con pestañas de etapa; assets/app-leads-nuevo.png — modal Nuevo lead con canal de origen
- roles: app-leads = cutout (ventana principal) · app-leads-nuevo = supporting (cambio dentro de la ventana)

Scene 1 (0.0–1.5s): la ventana con `app-leads.png` entra desde la derecha; eyebrow "LEADS" y h2 "Todo empieza con un lead" palabra a palabra.
Scene 2 (1.5–5.6s): chips de canal en la columna izquierda en su palabra: Formulario 2.2 · Chatbot 3.0 · Referido 3.7 · Carga de archivos 4.5. En 2.2 la ventana cambia a `app-leads-nuevo.png` con anillo en "Canal de origen" (rect [818,1016,606,124]).
Scene 3 (5.6–11.59s): vuelve `app-leads.png` (5.8); zoom 1.5 a la fila de pestañas (rect [1392,272,1104,68]); una píldora recorre Captura [1540,272,164,68] 7.3 · Elegibilidad [1716,272,216,68] 8.2 · Cotización [1944,272,202,68] 9.2 · Cierre [2158,272,132,68] 10.3. Sostener.

## Frame 3 — Todo el ciclo, en un solo lugar

- ejemplo: galeria/logo-lockup-close.html
- src: compositions/frames/f03-cierre.html
- duration: 8.06s
- transition_in: blur-crossfade
- status: animated
- voiceover: "Acme Salud. Todo el ciclo de la afiliación, en un solo lugar."
- scene: Cierre sobre fondo oscuro con el logo, el lema y la mascota
- focal: assets/brand-logo-blanco.png
- asset_candidates: assets/brand-logo-blanco.png — logo en blanco; assets/brand-mascota.webp — mascota

Scene 1 (0.0–3.0s): el logo blanco se asienta al centro; anillos concéntricos suaves se expanden detrás.
Scene 2 (3.0–8.06s): el lema "Todo el ciclo, en un solo lugar" aparece en 3.4; la mascota entra por la derecha en 4.2. Retención larga.
