# Mantener este repo

Trae dos skills independientes: `video-web/` (video) y `manual-app/` (manual escrito).
`manual-app` no tiene dependencias de la otra: solo Python con `markdown` y `playwright`.
Los pasos de abajo son de `video-web`; para `manual-app` basta
`cd manual-app && python3 -m pylint scripts/manual.py` y una prueba de punta a punta
(`scripts/ml init <tmp> --titulo X`, `./ml check`, `./ml pdf`).

## Publicar una versión de video-web


1. Corre los tests: `cd video-web/scripts && python3 -m pytest tests -q`.
2. Corre las evals de `video-web/evals/evals.json` con un agente (una a la vez; comparten GPU).
   Todas las aserciones deben pasar.
3. Si actualizaste las skills de HyperFrames para esta versión, graba sus huellas:
   `python3 video-web/scripts/checks.py compat ~/.agents/skills --grabar`
   y pon en `video-web/compat.json` → `hyperframes` la versión de la CLI con que probaste
   (`npx hyperframes --version`).
4. Sube `video-web/VERSION` (SemVer: mayor si rompe proyectos existentes, menor si agrega,
   parche si corrige) y anota los cambios en `CHANGELOG.md`.
5. Commit, tag `vX.Y.Z` y push. Empaqueta con
   `tar -czf video-web-skill-X.Y.Z.tar.gz video-web`.

## Por qué `compat.json`

`vl` usa scripts internos de `product-launch-video`, `media-use` y `hyperframes`. No son una
API pública: un `npx hyperframes skills update` puede cambiarlos. `vl doctor` compara sus
huellas con las probadas y avisa si difieren; en ese caso corre las evals antes de usar la
skill en videos reales.
