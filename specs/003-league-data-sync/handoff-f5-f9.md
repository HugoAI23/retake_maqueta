# Traspaso: fases F5 a F9 de la spec 003

> **Actualización (2026-09-23): F5 a F8 ya están implementadas y F9 casi cerrada** (registro I-27 a I-31 del plan). Queda lo que depende de Hugo o del calendario: T-086, T-087, T-089, T-094 y T-090. Este documento se conserva como registro del traspaso.

> Resumen para el agente que continúe la implementación de la spec 003 (`003-league-data-sync`) de Retake.
> Fecha: 2026-09-23. Último commit con código: `0bfd961`. Estado de las pruebas: backend 562 en verde (`uv run pytest -q` en `backend/`), frontend 259 en verde (`npx vitest run` en la raíz).
> Este documento **no sustituye** a la spec, al plan ni a las tareas: resume dónde está todo y qué reglas no se pueden romper. Ante cualquier duda, mandan los documentos de §2.

---

## 1. El proyecto en una línea

Retake es una web de estadísticas de la Call of Duty League (CDL). Tiene un backend en Python y un frontend en React. La spec 003 hace que los datos de la liga se obtengan y actualicen solos desde BreakingPoint.gg. La Wiki entra por archivos CSV importados a mano.

- **Backend:** Python 3.13, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 18 y uv. Pruebas con pytest. Clientes HTTP con httpx y logos con Pillow.
- **Frontend:** React con Vite. Pruebas con Vitest y, de extremo a extremo, con Playwright y axe.
- **Bases de datos locales:** `retake` (desarrollo) y `retake_test` (pruebas). La conexión se lee de `backend/.env`, que está fuera de git.

## 2. Documentos que mandan (léelos antes de tocar nada)

| Documento | Qué contiene |
|---|---|
| `maqueta/constitution.md` | Reglas del proyecto: desarrollo guiado por specs, seguridad, pruebas y verificación manual. |
| `specs/003-league-data-sync/spec.md` | Requisitos RF-1 a RF-160, en formato EARS. Los cambios C-1 a C-21 están aprobados y aplicados (§5). |
| `specs/003-league-data-sync/plan.md` | Módulos, contratos, planificación de las consultas (§5), seguridad (§9) y **registro de ajustes I-1 a I-26** (conviene leerlo entero). |
| `specs/003-league-data-sync/tasks.md` | Tareas T-001 a T-099 con su RF, sus dependencias y su criterio de "Hecho cuando". Las que faltan están sin marcar. |
| `specs/003-league-data-sync/source-map.md` | Dónde está cada dato en cada fuente (exploración de F0). |
| `specs/001-*`, `specs/002-league-data/` | Specs anteriores: marco visual, bloques de carga de la 001, datos de la liga y reglas de ingesta de la 002. |

## 3. Reglas de trabajo que Hugo exige (no negociables)

1. **Proceso guiado por specs.** Aprobar algo no autoriza el paso siguiente: que Hugo apruebe una spec o un plan no significa que puedas implementar. Haz solo la fase que Hugo pida y detente al cerrarla.
2. **Cambios a specs ya aprobadas:** propón cada cambio con su texto exacto y espera a que Hugo lo apruebe **uno por uno** antes de aplicarlo. Numéralos a partir de **C-22**.
3. **Ajustes del plan durante la implementación:** anótalos en el registro de `plan.md` a partir de **I-27** (fase, qué, por qué y RF afectados).
4. **Primero las pruebas.** Escribe la prueba, comprueba que falla, implementa y comprueba que pasa. Marca la tarea en `tasks.md` solo cuando cumpla su criterio de "Hecho cuando".
5. **Git:** solo órdenes de lectura (`status`, `diff`, `log`). Nunca `add`, `commit`, `rm`, `reset`, `push` ni nada que cambie el índice o el historial. Al cerrar cada fase, **sugiere** el mensaje de commit y Hugo lo hace.
6. **Ninguna prueba sale a internet** (RF-10). Los conectores se prueban con transportes simulados y la fuente simulada.
7. **Datos de prueba:** siempre ficticios, marcados con `[FICTICIO]`. En producción no se carga nada ficticio (RF-9).
8. **Una fase termina** con todas las pruebas en verde, una guía de verificación para Hugo, el registro del plan al día y el commit sugerido.
9. **Idioma:** documentos, textos, comentarios y nombres de las pruebas, en español, como el código existente. Cita los RF en las descripciones de funciones y pruebas.

## 4. Límites de seguridad y de uso de las fuentes

- **No consultes la Wiki (Fandom) nunca** (RF-38, cambio C-18). Sus datos entran con `uv run retake import-wiki-csv` (plan I-26). No vuelvas a añadir su conector, `requests`, cambios de cifrado TLS ni nada que esquive Cloudflare u otra protección. Ya se retiró en F4b.
- **Identifícate siempre como Retake** (RF-37) con el User-Agent de `backend/app/sources/http.py`. No te hagas pasar por un navegador ni cambies el User-Agent para evitar un bloqueo.
- **No uses la clave interna de Supabase de BreakingPoint.** Solo sus páginas y su API interna pública, como ya hace `sources/bp.py`.
- **Respeta en BreakingPoint** la pausa de 2 s, los tiempos de espera y `robots.txt` (RF-35 a RF-42).
- **Si una fuente impide cumplir un requisito,** aplica la regla **P-1**: detente y pregunta a Hugo. No rebajes el requisito por tu cuenta.
- **La contraseña del administrador la crea Hugo** con `retake set-admin-password` (T-064). No la escribas, no la pidas y no la guardes en ningún sitio, ni en pruebas ni en documentos.
- **Credenciales solo en `backend/.env`** (fuera de git). Los CSV de la Wiki van en `backend/data/wiki/`, también fuera de git, porque llevan datos personales.

## 5. Estado actual (F0 a F4b completadas)

| Fase | Qué quedó hecho |
|---|---|
| F0 | Exploración de las fuentes (`source-map.md`). |
| F1 | Dependencias, configuración (`SOURCE_MODE`, `TRUSTED_PROXY`, `WIKI_CSV_DIR`) y esquema. Migraciones hasta `a1c0e3f5b705`. |
| F2 | Reglas de dominio puras en `backend/app/domain/`: marcador en vivo, cancelación, identidad combinada, ventanas de revisión, desaparición, frescura, prioridad en vivo, K/D y semanas. |
| F3 | Conector de BreakingPoint (`sources/bp.py`), cliente educado (`sources/http.py`), logos (`logos/`) y fuente simulada con escenarios (`sources/simulated.py`). |
| F4 | Ingesta ampliada (`backend/app/ingest/`): ilegibles, `changed_at` y `dataset_change`, avistamientos y desaparición, marcador en vivo, cancelación, identidades y logos, retención, curación (`merges`, `confirmed_new`, `countries`), retirada de datos personales, `stats_complete_at` y `retake list-retained`. |
| F4b | Importación de la Wiki por CSV (`sources/wiki_csv.py`, `ingest/wiki_import.py`, `retake import-wiki-csv`). Hugo ya importó sus CSV reales: 14 campeonatos, 284 clasificaciones, 168 franquicias y 515 jugadores. |

**Piezas clave que vas a reutilizar:**
- `ingest.pipeline.ingest_records(session, records, curation=..., now=..., logo_fetcher=...)` → `IngestReport`, con `accepted`, `rejected`, `changed_datasets`, `discrepancies`, `retained` y `untranslated_countries`. Todo dato de una fuente entra por aquí.
- `ingest.sightings`: `apply_sightings` y `detect_disappearances`. Las usa el ejecutor de F5 tras cada consulta con éxito.
- `sources.contract.ConsultaResult` es lo que devuelven los conectores. `sources.bp` expone `consult_regular`, `consult_match` y `consult_teams`.
- **Tablas de F5 ya creadas** (`db/models/sync.py`): `source_state`, `sync_job`, `sync_request`, `sync_run`, `incident`, `incident_day`, `daily_summary` y `dataset_change`.
- **Tablas de F7 ya creadas** (`db/models/admin.py`): `admin_user`, `admin_session` y `login_origin`.
- **Listas cerradas y tiempos** en `domain/vocabulary.py`: `SYNC_JOBS`, `RUN_OUTCOMES`, `INCIDENT_KINDS`, `DATASETS`, ciclos, umbrales y `MIN_PAUSE` (solo `bp` y `cdl`).
- `domain.freshness.is_source_stopped` nunca marca la Wiki como parada (C-19).
- **Órdenes que ya existen:** `migrate`, `load-fixtures`, `apply-curation`, `sync-once --source bp`, `list-retained` e `import-wiki-csv`.

## 6. Lo que falta: fases F5 a F9

El detalle de cada tarea está en `tasks.md`. Aquí van los puntos que más fácilmente se pasan por alto.

### F5 · Proceso de obtención (T-049 a T-057)
Módulos nuevos en `backend/app/sync/`: `planner.py` (función pura), `runner.py`, `worker.py`, `registry.py` y `notify.py` (plan §2.4 y §5).
- **Sin consultas a la Wiki en el planificador:**
  - sin relecturas del Champs;
  - sin la consulta de historial;
  - sin `POST /history/reread`;
  - sin peticiones `history_reread`, aunque el tipo siga en el esquema.

  Así lo fijan C-17 a C-19 e I-26. La carga inicial es solo la temporada actual (y la próxima, si existe).
- **Registro de actualizaciones:**
  - una incidencia idéntica solo aumenta su contador;
  - nunca guarda el valor de un dato personal;
  - se borra a los 7 días.

  Ver RF-140 a RF-149.
- **Ejecutor:** cada consulta pasa por el conector, la ingesta, los avistamientos, el registro, `source_state` y el aviso de cambios. Una respuesta vacía donde antes había datos cuenta como consulta fallida (RF-46).
- **Aviso de cambios:** `NOTIFY` con los conjuntos de datos cambiados, que salen de `report.changed_datasets`.
- **`retake sync`:**
  - una cola por fuente;
  - peticiones del administrador, con una sola en curso por fuente;
  - se niega a arrancar en producción con la fuente simulada o con datos ficticios.
- **T-055:** `sync-once` ya existe solo para `bp`; falta `source-mode`.
- **T-056:** pruebas de punta a punta con la fuente simulada y el reloj simulado. El escenario `champs_tardio` ya no existe.

### F6 · API ampliada y eventos del servidor (T-058 a T-063)
- `changedAt` en todas las respuestas de la 002 e `isStale` en cada partido.
- `GET /api/freshness`: los conjuntos de datos que solo vienen de la Wiki (el historial) nunca aparecen como desactualizados (C-20).
- `GET /api/logos/{id}`: la copia propia, con `nosniff` y caché larga.
- `GET /api/stream`: eventos del servidor con `LISTEN`, latido cada 15 s y `retry: 5000`.
- Ninguna ruta devuelve datos de la próxima temporada.

### F7 · Administración, servidor (T-064 a T-069)
- Contraseña con Argon2id. La crea Hugo con `retake set-admin-password`, que la pide sin mostrarla y nunca la recibe como argumento.
- Bloqueo por origen: 5 fallos seguidos bloquean 15 minutos, y solo se confía en `X-Forwarded-For` si `TRUSTED_PROXY` está configurado.
- Sesiones en el servidor con cookie HttpOnly de 8 horas.
- Cabecera `X-Retake-Admin: 1` contra peticiones falsificadas.
- Rutas del plan §3.4. En la página de administración, la Wiki muestra la fecha de su última importación (`source_state` `wiki`/`history`) y no se puede actualizar desde la web (C-19).

### F8 · Frontend (T-070 a T-083)
- `src/live/`: canal de eventos, bloques que se recargan solos sin esqueleto, reglas de frescura y anuncios accesibles.
- Bloque de demostración en vivo, solo en desarrollo.
- Diccionarios `es` y `en`.
- Página `/admin` sin entrada en el menú. Su panel no tiene "releer historial".
- Pie de página:
  - el año de la temporada;
  - la atribución de las tres fuentes con enlace;
  - la licencia CC BY-SA del texto de la Wiki (RF-160).
- Pruebas de extremo a extremo con Playwright y auditoría WCAG 2.2 AA con axe.

### F9 · Cierre (T-084 a T-090)
- Checklist de seguridad del plan §9.
- Todas las pruebas en verde.
- Recorrido en modo real con `retake sync`.
- `verification-guide.md` con una fila por RF.
- Sincronizar spec, plan y código.
- **Pendiente de añadir al checklist:** `backend/curation/curation.yaml` mezcla entradas de los datos de prueba (`bp:fx-…`, `wiki:Twin_2`, `wiki:Split_B`) con las reales. En una base de producción, `retake apply-curation` fallaría por referencias desconocidas. Hay que proponer a Hugo cómo separarlas. **Resuelto con I-35** (2026-09-24): dos archivos, `curation.yaml` (real) y `fixtures.yaml` (prueba).

### Dependen del calendario (no se pueden cerrar antes)
- **T-094:** repetir la exploración del en vivo y de la próxima temporada cuando BreakingPoint publique el calendario de 2027.
- **T-089:** medir el ciclo de 60 s y los márgenes de pantalla con un partido real en vivo (criterio 3 de la spec).

## 7. Limitaciones y avisos conocidos

- **RF-75 de la 002 incumplido:** la web oficial de la CDL está en reserva, sin conector (F0-3), así que la tabla de posiciones sale de BreakingPoint. Hugo debe decidir en el cierre si lo acepta.
- **Curación pendiente, de Hugo:** tras F5 en modo `real`, unir los jugadores de la Wiki con los de BreakingPoint (`player_merges`) y rellenar `countries` con la ayuda de `retake list-retained`. No lo hagas tú.
- **La base de desarrollo tiene datos de prueba y los CSV reales a la vez.** Por eso algunos Champs muestran equipos de más y hay unos 697 registros retenidos. Es lo esperado y no es un fallo.
- **Pruebas en paralelo:** la base `retake_test` se recrea en cada prueba de integración. Si Hugo ejecuta pytest a la vez que tú, salen fallos falsos ("relation does not exist"). Comprueba antes que no haya otro pytest en marcha.
- **Un nuevo tipo de consulta o de dato** va primero a `domain/vocabulary.py` y, si tiene restricción CHECK, necesita migración.

## 8. Órdenes útiles

Desde `backend/`:

```bash
uv run pytest -q
```

```bash
uv run retake migrate
```

```bash
uv run uvicorn app.main:app --port 8000
```

Desde la raíz del repositorio:

```bash
npx vitest run
```

```bash
npm run test:e2e
```

## 9. Cómo empezar

1. Lee `constitution.md`, la spec 003 (§2 y §5), el plan (§2.4, §5, §9 y el registro I-1 a I-26) y la sección F5 de `tasks.md`.
2. Confirma con Hugo que quiere empezar F5. No empieces sin su orden.
3. Empieza por T-049 (planificador): primero la prueba y después la implementación.
