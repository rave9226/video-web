# Mantener este repo

Trae dos skills independientes: `video-web/` (video) y `manual-app/` (manual escrito).
`manual-app` no tiene dependencias de la otra: solo Python con `markdown` y `playwright`.
Los pasos de abajo son de `video-web`; para `manual-app` basta
`cd manual-app && python3 -m pylint scripts/manual.py` y una prueba de punta a punta
(`scripts/ml init <tmp> --titulo X`, `./ml check`, `./ml pdf`).

## Instalar en esta máquina

La skill que producen los videos (`~/.agents/skills/video-web`) se instala **desde este repo**;
nunca se edita allí. Lo propio de la máquina vive fuera de los dos:

| Qué | Dónde |
|---|---|
| Rutas (venvs, sandbox de Chrome, voz por omisión) | `~/.config/video-web/entorno.sh` |
| Voces aprobadas | `~/.config/video-web/voces/<nombre>/{ref.wav,voz.json}` |

```bash
rsync -a --delete --exclude '__pycache__' --exclude '.pytest_cache' \
  video-web/ ~/.agents/skills/video-web/
~/.agents/skills/video-web/scripts/vl doctor
```

## Publicar una versión de video-web

1. Corre los tests: `cd video-web/scripts && python3 -m pytest tests -q`.
2. Corre las evals de `video-web/evals/evals.json` con un agente (una a la vez; comparten GPU).
   Todas las aserciones deben pasar.
3. Si cambias la versión de givemotion, ponla en `video-web/compat.json` → `givemotion` solo
   después de correr las evals con ella.
4. Sube `video-web/VERSION` (SemVer: mayor si rompe proyectos existentes, menor si agrega,
   parche si corrige) y anota los cambios en `CHANGELOG.md`.
5. Commit, tag `vX.Y.Z` y push. Empaqueta con
   `tar -czf video-web-skill-X.Y.Z.tar.gz video-web`.

## Por qué `compat.json`

givemotion es joven (0.1.x) y su API cambia entre versiones: `vl` usa siempre la versión fijada
(`npx givemotion@<versión>`), así un video se renderiza igual mañana. Los fallos conocidos de
la versión fijada están en `references/oficio.md` § Escenas.
