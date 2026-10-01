---
name: manual-app
description: >-
  Úsala para escribir el manual de usuario o la guía de una app, un portal o un sistema web:
  capturas reales de cada pantalla, qué hace cada una y para qué sirve, y un PDF con los colores
  de la marca. Aplica cuando pidan «hazme un manual de esta app», «documenta este portal»,
  «guía de usuario de…», «instructivo escrito» o «documentación para los usuarios». No necesita
  video ni ningún otro proyecto. Si además quieren un video, esa es la skill video-web; las dos
  se pueden combinar, pero ninguna depende de la otra.
  Use for a user manual or written guide of a web app, site or portal: real screenshots, what
  each screen is for, and a branded PDF. Standalone, no video needed.
license: Apache-2.0
---

# Manual de usuario de una app

Un manual se usa de otra forma que un video: la gente llega buscando **una** cosa, con la app
abierta al lado. Así que gana el que dice **para qué sirve cada pantalla y en qué orden se usan**,
no el que describe campos.

## Reglas de oro (no negociables)

1. **Solo lectura en la app del cliente.** Nunca crees, edites, apruebes, pagues ni envíes nada.
   `./ml pantalla` bloquea POST, PUT, PATCH y DELETE; aun así, no abras flujos que guarden.
2. **🛑 Pregunta por los datos.** Si no sabes si los de la app son de prueba, pregunta. Si son
   reales, muéstralos solo con permiso y sin datos personales.
3. **Nada inventado.** Capturas reales y datos que muestra la app. Ningún campo, menú, cifra ni
   mensaje de error que no hayas visto. Si no pudiste verlo, dilo en el manual o pregúntalo; no
   lo describas de memoria.
4. **Credenciales nunca en archivos.** Si la app pide login, se usa un perfil de Chrome con la
   sesión ya abierta (`--perfil`), no credenciales escritas.
5. **Ruta del proyecto sin espacios.**

## Herramientas

`./ml` dentro del proyecto (solo `init` va con la ruta completa
`~/.agents/skills/manual-app/scripts/ml`).

| Para… | Comando |
|---|---|
| crear el proyecto | `ml init <ruta> [--desde <proyecto-video-web>] [--titulo "Nombre"]` |
| capturar una pantalla | `./ml pantalla --url https://app --ruta /facturas --nombre app-facturas [--perfil <perfil-chrome>]` |
| generar el PDF | `./ml pdf [--salida manual.pdf]` |
| avisos objetivos | `./ml check` |

## Recorrido

1. **`ml init <ruta>`** crea `manual.md` desde la plantilla, la carpeta `img/` y el enlace `./ml`.
2. **Capturas.** Una por pantalla, a 2x:
   ```bash
   ./ml pantalla --url https://app.ejemplo.com --ruta /facturas --nombre app-facturas
   ```
   Con login, abre una vez `chromium --user-data-dir=/ruta/perfil`, inicia sesión, y pasa
   `--perfil /ruta/perfil`. **Mira cada PNG** antes de usarlo: tablas vacías, spinners o
   pantallas de error no sirven. Si ya existe un proyecto de `video-web`,
   `ml init --desde <proyecto>` trae sus capturas y sus colores y no hace falta capturar.
3. **Escribe `manual.md`** siguiendo la plantilla. El orden de las secciones es lo que hace útil
   el manual, ver abajo.
4. **`./ml check`** y arregla lo que marque.
5. **`./ml pdf`** y 🛑 muéstraselo al usuario.

## Lo que hace útil un manual

- **Empieza por cómo está organizado el sistema.** De qué partes consta, cómo dependen entre sí
  y **en qué orden se usan**. Es la sección que evita la mayoría de los errores, y va primero.
- **Explica los verbos del negocio.** Toda app tiene palabras que solo significan algo adentro
  (causar, conciliar, legalizar, provisionar). Si el manual las usa sin definirlas, no capacita.
  Y si dos estados parecen lo mismo y no lo son, dilo con un ejemplo.
- **Cada concepto dice para qué sirve, no solo qué es.** Las tablas llevan tres columnas:
  concepto, qué es y **para qué sirve / por qué importa**. `./ml check` avisa si falta.
- **Cada pantalla, en el mismo orden:** para qué sirve → captura → pasos numerados → tabla de
  campos → aviso de verificación.
- **Advierte donde se puede equivocar**, con la consecuencia, en un `>` de cita: «el total debe
  coincidir con el monto; si no, el registro llega con valores errados».
- **Preguntas frecuentes que empiecen por «¿por dónde empiezo?»**.

## Marca

`marca.json` con `primary`, `ink`, `canvas`, `muted` y `font`. Los colores **salen de la app**:
del CSS, del logo, o se le preguntan al usuario. **Nunca se copian de un ejemplo ni de otro
proyecto.** `ml init --desde <proyecto-video-web>` los toma de su `frame.md`, que ya los tiene
calculados para cumplir contraste AA. Sin `marca.json` el PDF sale en grises neutros, que es
mejor que una marca equivocada.

## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| `falta playwright` | `pip install markdown playwright && playwright install chromium` |
| la captura sale en la pantalla de login | la sesión del perfil se cerró: ábrela de nuevo en ese perfil |
| `./ml check` pide la columna de propósito | agrégala: es la razón de ser del manual |
| el PDF sale en grises | falta `marca.json` (a propósito: no se inventan colores) |

## Cómo trabajar

- **Mira las capturas.** Eres multimodal: ábrelas antes de referenciarlas.
- **🛑 El usuario aprueba** los datos reales y el PDF final.
- **Responde en español** (o en el idioma del manual).
