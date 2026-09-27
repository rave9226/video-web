# Captura de la app

Objetivo: capturas reales a 2x (2880×1800) de cada pantalla que el video va a mostrar, con los
rectángulos medidos de los elementos que la voz nombra. Todo en **solo lectura**. `capture.py`
bloquea en la red cualquier POST/PUT/PATCH/DELETE que no esté en `allow_mutations`, los GET a
rutas de acción (`/logout`, `/delete`, `/approve`, `/cancelar`…) y los WebSockets, y rechaza
los clics en botones de acción. Aun así, no le pidas que haga nada que modifique datos: un GET
con efectos y nombre inocente (`/orders/7?do=1`) no se puede detectar.

## 1. Explora antes de escribir capture.json

```bash
./vl explorar https://app.ejemplo.com/ruta   # antes de llenar base_url en capture.json
./vl explorar /ruta                 # pantalla pública
./vl explorar /ruta --auth          # pantalla tras login (credenciales en variables de entorno)
./vl explorar /suscripciones --auth --steps '[{"fill": "Buscar por código", "value": "S02967"}]'
```

`explorar` produce dos archivos:

- `capture/extracted/explorar-<ruta>.md`: títulos, controles y campos, con ⛔ en los botones
  bloqueados.
- `capture/review/explorar-<ruta>.png`: la captura de la pantalla. Mírala.

Usa esos textos exactos en los pasos y en las regiones. También lee `manual.txt`, si existe,
para saber qué pantallas importan.

## 2. capture.json

| Campo | Qué es |
|---|---|
| `base_url` | URL sin barra final |
| `brand` | se llena después de capturar (`./vl marca sugerir`); deja `null` hasta entonces |
| `fonts` | familia de la app en Google Fonts, p. ej. `[{"family": "Poppins", "weights": [400,500,600,700]}]` |
| `login` | ruta, etiquetas de los campos, texto del botón y `wait_url`. Bórralo si la app no tiene login |
| `allow_mutations` | solo la ruta **exacta** de la API de login (p. ej. `/api/auth/login`). Un `*` final la vuelve prefijo (`/api/auth/*`), pero entonces también permite `/api/auth/cambiar-clave`: evítalo |
| `deny_get` | regex de rutas GET a bloquear (por defecto verbos de acción y cierre de sesión); `""` lo desactiva |
| `websocket` | `true` si la app necesita WebSockets para mostrar datos (bloqueados por defecto: pueden enviar comandos) |
| `modal` | selector CSS del contenedor de modales (por defecto `[role=dialog]`) |
| `brand_assets` | logo o mascota servidos por la app (`url`, `name`, `white: true` para crear la versión blanca) |
| `shots` | una entrada por pantalla, descritas en la tabla siguiente |

Cada entrada de `shots`:

| Campo | Qué es |
|---|---|
| `name` | `app-<pantalla>` en minúsculas; será `capture/assets/<name>.png` |
| `route` | ruta dentro de `base_url` |
| `auth` | `false` para pantallas públicas; por defecto, `true` si hay login |
| `desc` | qué se ve (lo leen el storyboard y los workers) |
| `steps` | acciones de lectura antes de capturar |
| `after` | acciones para deshacer el estado (p. ej. volver al tema claro) |
| `target` | `viewport` (defecto), `full` (página completa) o `modal` (modal completo sin scroll + `-vista` en contexto) |
| `regions` | `{"clave": {"text": "Texto visible", "min": [w, h], "nth": 0}}` o `{"clave": {"css": "selector"}}` |
| `crops` | recortes de tarjetas o secciones: `{"name", "text", "container": "section", "pad", "desc", "regions"}` |

**Pasos permitidos:**

- `{"click": "Texto"}`: botón, pestaña, enlace o ítem de menú.
- `{"click_css": "selector"}`.
- `{"fill": "Placeholder o etiqueta", "value": "…"}`.
- `{"type": "texto"}`.
- `{"hover": "Texto"}`.
- `{"key": "Escape"}`: solo Escape, Tab, flechas, PageUp o PageDown.
- `{"wait": 2}`.

No hay paso de "enviar". Abrir un modal de "Nuevo …" para mostrarlo está bien. Llenarlo y
guardarlo, jamás.

**Regiones.** `text` es el inicio del texto visible (o del placeholder) del elemento. `min` es
el tamaño mínimo en px CSS del contenedor que quieres medir: el script sube desde el texto
hasta el primer ancestro de ese tamaño. Usa `min: [30, 20]` para una pestaña, `[200, 30]` para
un campo y `[1000, 60]` para una fila completa. Las claves van en `snake_case` corto. Los rects
salen en píxeles de la imagen (2x) y los ves en `capture/extracted/regions.md`.

## 3. Correr y revisar

```bash
APP_USER='usuario' APP_PASS='clave' ./vl captura          # todas
APP_USER='usuario' APP_PASS='clave' ./vl captura --only app-leads,app-planes
```

- **Credenciales.** Por variables de entorno en el mismo comando o en un `.env` del proyecto
  (`APP_USER=…` y `APP_PASS=…`, una por línea) que crea el usuario; `vl init` lo agrega a
  `.gitignore`. Nunca las escribas en capture.json, BRIEF.md, notas ni commits.
- **Qué login falla.** Si el login no avanza, mira `capture/extracted/requests.log`: una línea
  `BLOQUEADO POST …` con la ruta del login significa que falta en `allow_mutations` (exacta).
- **Throttling.** Si la app responde "No fue posible…" o parecido, `capture.py` espera
  `retry_wait_s` y reintenta hasta `tries` veces. Si aun así falla, sube `retry_wait_s` a 60 y
  repite solo esa toma con `--only`.
- **Fallos.** "no encontré" o un timeout en un paso significan que el texto no coincide.
  Revisa `explorar` y usa el texto exacto.
- **Escrituras bloqueadas.** Si el reporte lista alguna, un paso disparó una acción. Quita ese
  paso: una escritura bloqueada significa que la toma no muestra lo que crees.

**Revisa tú cada hoja `capture/review/capturas-N.jpg`** (ábrela y mírala). Busca:

- pantallas de error;
- tablas vacías o spinners de carga;
- modales que no abrieron;
- tema equivocado;
- datos personales reales, si el BRIEF no dice `datos: prueba`.

Corrige y repite las tomas que fallen con `--only`. `./vl check captura` resume fallas,
escrituras bloqueadas e imágenes vacías.

## Imágenes que ya existen (manual, carpeta img/)

```bash
./vl crop --src ../img/firma.png --name manual-firma --desc "firma completada" --card
./vl crop --src ../img/rol.png --name manual-rol-admin --desc "vista del rol admin" --box 120,80,900,640
```

`--card` detecta la tarjeta blanca centrada. `--box` recorta `x,y,w,h` en píxeles de la imagen.
