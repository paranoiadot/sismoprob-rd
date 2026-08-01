# SismoProb RD

Mapa/dashboard web que estima probabilidades de actividad sísmica en República
Dominicana y el Caribe cercano, usando datos en vivo de USGS y un modelo
Bayes-Poisson + Gutenberg-Richter. Es una PWA instalable (ícono, manifest,
service worker).

## Stack y arquitectura

- **Backend**: FastAPI (`app.py`), servido con `uvicorn`.
  - `GET /` → sirve `index.html` (lee el archivo del disco en cada request, no hay
    templating).
  - `GET /static/*` → assets estáticos (`static/`, iconos PWA).
  - `GET /api/sismos` → JSON con eventos filtrados + estadísticas del modelo.
- **Lógica de dominio**: `motor_usgs.py` (todo el motor estadístico vive acá,
  sin capa de servicios ni ORM — es un módulo plano de funciones puras).
  - `obtener_sismos_caribe()`: pega al feed público de USGS
    (`all_month.geojson`), filtra por magnitud mínima y por una bounding box
    fija de RD/Caribe (`lat 17.0–20.5`, `lon -75.0–-68.0`).
  - `calcular_valor_b()`: valor *b* de Gutenberg-Richter (método de Aki).
  - `calcular_probabilidades_bayes_poisson()`: probabilidad de ≥1 sismo en
    ventanas de 24h/7d/30d vía proceso de Poisson, con intervalo de confianza
    90% aproximado.
- **Frontend**: `index.html` es un archivo único (HTML+CSS+JS inline, ~750
  líneas), sin build step ni framework. Usa Leaflet (CDN, `unpkg.com`) para el
  mapa y CartoDB dark tiles.
- **PWA**: `manifest.json` + `sw.js` (cache-first simple sobre `/` y
  `/api/sismos`).
- **Deploy**: `Dockerfile` (Python 3.11-slim → `uvicorn app:app --port 8000`) +
  `render.yaml` (blueprint de Render, servicio Docker, `autoDeploy: true` sobre
  `main`). El deploy real en Render requiere que el dueño de la cuenta conecte
  el repo desde el dashboard de Render la primera vez (Claude no tiene acceso
  a esa cuenta) — una vez conectado, cada push a `main` dispara un deploy
  automático.

## Cómo correr en local

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt   # incluye requirements.txt + pytest
uvicorn app:app --reload --port 8000
```

Con Docker Desktop (mismo entorno que usa Render):

```bash
docker build -t sismoprob-rd:local .
docker run --rm -p 8000:8000 sismoprob-rd:local
```

### Tests

```bash
python -m pytest -q
```

`tests/test_motor_usgs.py` cubre el filtrado de `obtener_sismos_caribe`
(mockeando `requests.get`, sin pegarle a la red real) y valores de referencia
(golden values) para `calcular_valor_b` y
`calcular_probabilidades_bayes_poisson`. Si se toca la fórmula del modelo, hay
que actualizar los valores esperados a propósito (ver preaviso abajo) — un
test que empieza a fallar ahí es una señal de alarma, no un typo a silenciar.

## Convenciones del proyecto

- Nombres de funciones/variables en **español** (`obtener_sismos_caribe`,
  `calcular_valor_b`) — seguir ese idioma al tocar `motor_usgs.py`/`app.py`.
- `index.html` mezcla estilo y lógica inline a propósito (proyecto pequeño,
  sin build step) — no introducir un bundler/framework sin que se pida.
- `.venv/` está en `.gitignore`; no committear el entorno virtual.

## Cosas a tener en cuenta (quirks conocidos, no "arreglar" sin avisar)

- `brier_score: 0.041` en `motor_usgs.py:117` está **hardcodeado**, no se
  calcula. Si toca esa función, avisar en vez de "corregirlo" silenciosamente.
- `obtener_sismos_caribe()` no maneja excepciones de red (`requests.get` sin
  timeout ni try/except) — si falla la respuesta HTTP falla toda `/api/sismos`.
- El service worker cachea `/api/sismos` con estrategia cache-first, así que
  en modo offline/PWA puede servir datos sísmicos desactualizados. Es
  información sensible a tiempo real — cualquier cambio al cacheo debe
  dejarlo explícito.
- La bounding box del Caribe está hardcodeada en `motor_usgs.py`; si se pide
  ampliar cobertura geográfica, confirmar los nuevos límites antes de tocar
  el filtro.

## Preavisos — avisar antes de actuar, no proceder solo

- **Push a `main`**: el repo tiene una sola rama (`main`) sin CI/tests. Un
  push directo puede ir a producción sin red de seguridad. Avisar antes de
  cualquier `git push`.
- **Cambios al modelo estadístico** (`calcular_valor_b`,
  `calcular_probabilidades_bayes_poisson`): son la razón de ser de la app.
  Cualquier cambio de fórmula, ventana temporal, magnitud mínima o bounding
  box debe explicarse y confirmarse antes de aplicarse — no es un detalle de
  implementación, es contenido que la gente puede leer como una predicción
  real de riesgo sísmico.
- **Dependencias/Docker**: cambios a `requirements.txt` o `Dockerfile` afectan
  el build de despliegue; confirmar antes de subir versiones o agregar
  paquetes nuevos.
- **PWA (`manifest.json`, `sw.js`)**: cambios de caché o de ícono/nombre
  pueden romper la instalación existente en los teléfonos de usuarios reales;
  avisar antes de tocarlos.
- No asumir un proveedor de hosting/CI que no esté en el repo — preguntar.

## Integraciones activas

- **GitHub Actions** (`.github/workflows/`):
  - `ci.yml`: corre `pytest` y valida que el `Dockerfile` construya en cada
    push/PR a `main`.
  - `claude.yml`: responde a menciones `@claude` en comentarios de issues/PRs.
  - `claude-review.yml`: revisión automática de Claude en cada PR nuevo o
    actualizado (usa el skill `code-review` vía `anthropics/claude-code-action`).
  - Ambos workflows de Claude requieren el secret `ANTHROPIC_API_KEY` en
    Settings → Secrets and variables → Actions del repo en GitHub. Ese secret
    lo agrega el dueño del repo manualmente (Claude no maneja API keys ni
    credenciales) — sin él, `claude.yml`/`claude-review.yml` fallan pero
    `ci.yml` sigue funcionando normal.
- **Docker Desktop**: usado localmente para validar que la imagen de
  producción construye y sirve `/` y `/api/sismos` antes de confirmar un
  cambio grande (ver comandos arriba).
- **Render**: `render.yaml` define el servicio; el deploy real depende de que
  el repo esté conectado en el dashboard de Render (fuera del alcance de
  Claude — solo lo puede hacer el dueño de la cuenta).
- **Terminal + VS Code**: ambos apuntan al mismo working directory de este
  repo, así que los cambios de una sesión de Claude Code en terminal son
  inmediatamente visibles en VS Code y viceversa — no hace falta sincronizar
  nada aparte.
