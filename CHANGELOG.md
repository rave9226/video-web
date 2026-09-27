# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versiones:
[SemVer](https://semver.org/lang/es/). La versión vigente está en `video-web/VERSION`.

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
