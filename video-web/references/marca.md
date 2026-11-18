# Marca: los colores salen de la app, no de un ejemplo

El error más visible que puede tener un video de una app es verse como otro producto. Pasa cuando
un color del ejemplo se queda en `capture.json`. En un video de una app de marca roja la portada
salió azul oscuro, porque el campo `dark` se llenó copiándolo de otro proyecto. Nadie lo notó
hasta que el cliente vio el render.

**La regla:** si un color no se puede justificar señalando dónde aparece en la app, no va en
`capture.json`.

## De dónde sale cada color

`capture.json → brand` solo pide **tres**:

| Clave | Qué es | Dónde se ve en la app |
|---|---|---|
| `primary` | el acento de la marca | botón principal, logo, ítem activo del menú |
| `ink` | el color del texto | los títulos sobre fondo claro |
| `canvas` | el fondo | el fondo de la página, no el de las tarjetas |

El resto se **deriva** y no hay que escribirlo:

- `campo` — el fondo de portada, separadores y cierre: el primario oscurecido. Solo se declara si
  la marca tiene un color propio documentado para eso (hay marcas que usan su primario
  de fondo), nunca «uno que combine».
- `ok` y `bad` — los estados (respaldado / no aparece). Son **semánticos, no de marca**: verde y
  rojo por omisión, oscurecidos lo justo para cumplir AA sobre su fondo.
- `muted`, `accent-text`, `accent-bg`, `line`, `surface`, `ok-bg`, `bad-bg` — calculados desde
  lienzo, tinta y primario. `primary` casi nunca sirve como texto: `accent-text` es su versión
  legible.

## Cómo conseguirlos

1. `./vl captura` escribe `capture/extracted/css-vars.json` con las variables CSS de la app.
2. `./vl marca sugerir` los lista: de ahí salen `primary`, `ink` y `canvas`.
3. `./vl marca` escribe `marca.css`: las fuentes locales, los tokens y los componentes.

**Si no hay `css-vars.json`** (la app no usa variables CSS, o se capturó de otra forma):
`./vl marca sugerir --primary "#RRGGBB"` deriva el resto de esa semilla. El primario se saca del
CSS de la app, del logo, o se le pregunta al usuario. Nunca de un ejemplo.

## marca.css manda

`marca.css` trae los tokens (`--bg`, `--ink`, `--accent`, `--accent-text`, `--ok`, `--bad`,
`--campo`…) y los componentes del sistema visual (encabezado, título, tarjeta, fila, chips por
intención, sellos de estado, botón, «Tú»). **Las escenas los reutilizan y nunca escriben un
color en hexadecimal**: `var(--token)` en CSS y `C('token')` en los tweens. Un hex en una escena
es cómo los colores de un video se cuelan en el siguiente (`./vl check escenas` lo avisa).
No edites `marca.css` a mano: cambia `capture.json` y repite `./vl marca`.

## Portada y cierre

Van sobre `.campo` (`--campo`) con tipografía blanca, y **las dos
con el mismo tratamiento**. Una portada clara con un cierre oscuro, o un título que hereda el
negro del navegador, se lee como un error de montaje.

## Verificación

- `./vl check marca` mide el contraste de cada texto **sobre su propio fondo** (el acento sobre su tinte, el verde sobre el suyo) y avisa si un token
  tiene un tono lejano al primario, que es la firma de un color copiado.
- A ojo: abre una captura de la app y el fotograma de portada lado a lado. Si parecen dos
  productos, el problema es la marca, no la escena.
