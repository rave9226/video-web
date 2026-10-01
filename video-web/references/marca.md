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

- `dark` — el campo de portada y cierre: el primario oscurecido. Solo se declara si la marca
  tiene un oscuro propio documentado (un azul corporativo, por ejemplo), nunca «uno que combine».
- `spark` — el anillo de foco. Es **semántico, no de marca**, como `positive` y `negative`: ámbar
  por omisión, para que resalte sobre cualquier primario.
- `muted`, `primary-text`, `chip-text` — calculados para cumplir contraste AA (4.5:1). `primary`
  casi nunca sirve como texto: `primary-text` es su versión oscurecida, y `chip-text` es la del
  chip, que va sobre su propio fondo teñido y necesita un poco más.

## Cómo conseguirlos

1. `./vl captura` escribe `capture/extracted/css-vars.json` con las variables CSS de la app.
2. `./vl marca sugerir` los lista: de ahí salen `primary`, `ink` y `canvas`.
3. `./vl marca` escribe `frame.md` con los tokens derivados y el CSS canónico.

**Si no hay `css-vars.json`** (la app no usa variables CSS, o se capturó de otra forma):
`./vl marca sugerir --primary "#RRGGBB"` deriva el resto de esa semilla. El primario se saca del
CSS de la app, del logo, o se le pregunta al usuario. Nunca de un ejemplo.

## El CSS canónico manda

`./vl marca` anexa a `frame.md` un bloque con `.PFX-win`, `.PFX-eyebrow`, `.PFX-h2`, `.PFX-chip`
y `.PFX-ring`, con los colores ya resueltos para cumplir AA. **Las escenas reutilizan esas
clases; no vuelven a derivar colores.** Reimplementarlas a mano es cómo se cuela un eyebrow con
`primary` en vez de `primary-text`, que falla AA por poco y no se ve a simple vista.

## Portada y cierre

Van sobre el campo de marca (`dark`, el primario oscurecido) con tipografía blanca, y **las dos
con el mismo tratamiento**. Una portada clara con un cierre oscuro, o un título que hereda el
negro del navegador, se lee como un error de montaje.

## Verificación

- `./vl check marca` mide el contraste de cada clase **sobre su propio fondo** y avisa si un token
  tiene un tono lejano al primario, que es la firma de un color copiado.
- A ojo: abre una captura de la app y el fotograma de portada lado a lado. Si parecen dos
  productos, el problema es la marca, no la escena.
