---
tipo: app          # app (hay URL que capturar) o explicativo (tema, artículo o notas, sin app)
formato: <FORMATO> # para qué es el video: capacitacion | lanzamiento | explicativo.
                   # 🛑 si el usuario no lo dijo, PREGÚNTASELO antes de escribir el guion:
                   # cambia el arco, la duración y qué dice cada línea (oficio.md § Guion).
producto: "<NOMBRE DEL PRODUCTO>"
url: "<URL DE LA APP O SITIO>"
message: "<MENSAJE CENTRAL EN UNA FRASE>"
audience: "<A QUIÉN VA DIRIGIDO>"
length: 60s
language: es-419
aspect: 1920x1080
captions: no
datos: "<DE PRUEBA O REALES>"
workflow: product-launch-video
flow: automation
narration: yes
voice: qwen3-tts-12hz-1.7b
---

## Intención

<QUÉ DEBE LOGRAR EL VIDEO: QUÉ FUNCIONES MOSTRAR, EN QUÉ ORDEN Y CON QUÉ TONO>

<SI formato: capacitacion — QUÉ DEBE SABER HACER QUIEN LO VEA AL TERMINAR, Y EN QUÉ ORDEN
SE USAN LAS PANTALLAS. Los verbos propios del negocio que hay que explicar: <CUÁLES>.>

## Fuentes

- App: <URL>. Login: <SÍ O NO>. Las credenciales van solo en las variables de entorno
  APP_USER y APP_PASS al correr `./vl captura`; nunca en archivos.
- Manual: manual.txt (si `./vl init` recibió `--manual`).
- Capturas previas: <CARPETA O NINGUNA>. Se recortan con `./vl crop`.
- Otros documentos: <WORD, PPT, NOTAS… O NINGUNO>.
- Investigación: <TEMA Y FUENTES CONSULTADAS, CADA DATO CON SU URL, O NINGUNA>.
- Imágenes de terceros: <SOLO OFICIALES O CON LICENCIA LIBRE; ORIGEN EN CREDITOS.md, O NINGUNA>.

## Restricciones

- Solo lectura en la app: nada de crear, editar, aprobar, pagar ni enviar.
- <OTRAS RESTRICCIONES DEL USUARIO O NINGUNA>
