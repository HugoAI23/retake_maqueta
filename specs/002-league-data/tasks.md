# Tasks: Datos de la Liga

- **Spec**: [`spec.md`](spec.md) (`Aprobado`, 2026-09-22, con las revisiones R-1 y R-2)
- **Plan**: [`plan.md`](plan.md) (`Aprobado`, 2026-09-22)
- **Fecha**: `2026-09-22`
- **Estado**: `Aprobado` (aprobado por Hugo el 2026-09-22). En implementación: F0 a F6 completadas; F7 en curso (T-070, T-071 y T-073 hechas; T-072 pendiente de la confirmación de Hugo; T-074 pendiente de aprobación). Muestra real revisada y confirmada por Hugo el 2026-09-22.

Checklist de tareas atómicas, en orden de ejecución. Cada tarea indica los requisitos que cubre (**RF**), de qué tareas depende (**Dep.**) y cuándo se considera terminada (**Hecho cuando**).

## Reglas de ejecución

1. **Orden:** las tareas se hacen en orden. Una tarea no empieza hasta que sus dependencias estén marcadas.
2. **Alcance cerrado:** solo se implementa lo que dice cada tarea (constitución §1.2). Si aparece un imprevisto, se detiene el trabajo y se consulta a Hugo antes de seguir; si cambia algo, se actualizan la spec y el plan (constitución §1.3).
3. **Pruebas primero:** en las tareas que dicen "Pruebas e implementación", las pruebas se escriben antes que el código y deben fallar antes de implementarlo.
4. **Cierre de fase:** cada fase termina con una tarea de cierre, que exige:
   - todas las pruebas automáticas en verde (`uv run pytest` en `backend/` y `npm test` en la raíz);
   - la guía de verificación manual de la fase entregada a Hugo (constitución §5.1);
   - un mensaje de commit sugerido. El commit lo hace Hugo: el agente no ejecuta comandos de git que modifiquen el repositorio (constitución §8).
5. **Documentación del código:** en Python, docstrings en español; en JavaScript, comentarios JSDoc en español (plan D-17 de la 001). Los nombres de código van en inglés (constitución §7).
6. **Tiempo en las pruebas:** el "hoy" y el instante de observación se inyectan; ninguna prueba depende del reloj real (plan §6.3).

## Dependencias externas

| Qué | Lo aporta | Afecta a | Mientras tanto |
|---|---|---|---|
| PostgreSQL 18 arrancado en el puerto 5432, con la versión 14 detenida | Hugo (es un servicio del sistema) | T-004 | La fase F0 no puede cerrarse. La guía de T-004 indica los dos comandos de Homebrew. |
| Revisión de la muestra real transcrita | Hugo | T-048 | La fase F4 no puede cerrarse. |
| Roles (`SMG` o `AR`) de los jugadores reales de la muestra | Hugo (RF-26: los asigna Retake) | T-046 | Esos jugadores quedan como `Sin rol`, que es un comportamiento válido (RF-27). |

---

## F0 — Base del backend

- [x] **T-001** Crear con uv un proyecto Python 3.13 en `backend/`, con las dependencias del plan: FastAPI, Uvicorn, SQLAlchemy 2, el controlador psycopg, Alembic, pydantic-settings y PyYAML; y como dependencias de desarrollo, pytest y httpx.
  - **RF:** —
  - **Dep.:** —
  - **Hecho cuando:** `uv sync` instala todo y existe `uv.lock`.
- [x] **T-002** Crear las carpetas del plan §1 dentro de `backend/`: `app/db`, `app/domain`, `app/ingest`, `app/curation`, `app/api`, `migrations`, `curation`, `fixtures/real`, `fixtures/fictional`, `tests/unit` y `tests/integration`.
  - **RF:** —
  - **Dep.:** T-001
  - **Hecho cuando:** la estructura existe y `uv run python -c "import app"` funciona.
- [x] **T-003** `app/config`: lee `DATABASE_URL`, `TEST_DATABASE_URL` y `APP_ENV` (`development`, `test` o `production`) de variables de entorno y de `backend/.env`. Crear `backend/.env.example` sin secretos y añadir `backend/.env` y `backend/.venv` a `.gitignore`.
  - **RF:** —
  - **Dep.:** T-002
  - **Hecho cuando:** una prueba comprueba que falta una variable obligatoria da un error claro, y `git status` no muestra `backend/.env`.
- [x] **T-004** Comprobar la conexión con PostgreSQL 18 y crear las bases de datos `retake` y `retake_test`. La conexión verifica la versión del servidor y se niega a seguir con una versión anterior a la 18.
  - **RF:** —
  - **Dep.:** T-003 y la dependencia externa de PostgreSQL 18
  - **Hecho cuando:** existen las dos bases de datos y una prueba comprueba el rechazo de una versión anterior (con un servidor simulado).
- [x] **T-005** `app/main`: aplicación FastAPI con `GET /api/health`, que devuelve el estado del servicio y si la base de datos responde.
  - **RF:** —
  - **Dep.:** T-004
  - **Hecho cuando:** `uv run uvicorn app.main:app` arranca y `/api/health` responde con la base de datos disponible.
- [x] **T-006** Configurar Alembic en `backend/migrations`, leyendo la conexión de `app/config`.
  - **RF:** —
  - **Dep.:** T-004
  - **Hecho cuando:** `uv run alembic upgrade head` se ejecuta sin errores sobre `retake`.
- [x] **T-007** Configurar pytest: cada prueba de integración recibe `retake_test` vacía y con las migraciones aplicadas, y un reloj inyectable. Prueba de humo de `/api/health` con el cliente de pruebas.
  - **RF:** —
  - **Dep.:** T-005, T-006
  - **Hecho cuando:** `uv run pytest` pasa y nunca toca `retake`.
- [x] **T-008** `app/cli` con el comando `migrate` (aplica las migraciones). Los comandos `load-fixtures` y `apply-curation` se añaden en F3 y F4.
  - **RF:** —
  - **Dep.:** T-006
  - **Hecho cuando:** `uv run retake migrate` aplica las migraciones.
- [x] **T-009** Añadir el proxy `/api` → `http://localhost:8000` en `vite.config.js` y la configuración `retake-api` (Uvicorn en el puerto 8000) en `.claude/launch.json`.
  - **RF:** —
  - **Dep.:** T-005
  - **Hecho cuando:** con los dos servidores arrancados, `http://localhost:5173/api/health` responde desde el backend.
- [x] **T-010 · Cierre F0**
  - **Dep.:** T-001 a T-009
  - **Hecho cuando:** pytest y `npm test` están en verde, se ha entregado la guía manual (arrancar PostgreSQL 18, el backend y el frontend, y abrir `/api/health` y `/docs`) y se ha sugerido el commit.

---

## F1 — Modelo de datos

- [x] **T-011** Modelos de las tablas de entrada del plan §3.1: `external_ref`, `ref_link` y `observation` (con `is_valid`, `first_seen_at` y `last_seen_at`).
  - **RF:** RF-65, RF-98
  - **Dep.:** T-006
  - **Hecho cuando:** los modelos existen, documentados con docstrings.
- [x] **T-012** Modelos `season` (`year` único y `started_at`), `event`, `franchise` e `identity`.
  - **RF:** RF-11, RF-52, RF-74
  - **Dep.:** T-011
  - **Hecho cuando:** los modelos existen, documentados con docstrings.
- [x] **T-013** Modelos `player` (sin campos de rol calculados; con `personal_data_removed`), `player_gamertag` y `roster_membership`.
  - **RF:** RF-16, RF-17, RF-21, RF-22, RF-26
  - **Dep.:** T-011
  - **Hecho cuando:** los modelos existen, documentados con docstrings.
- [x] **T-014** Modelos `match` (fase nula o una de las cinco; estado de tres valores; `corrected_fields`), `match_schedule`, `match_slot`, `match_map` y `player_map_stats` (las 13 estadísticas admiten nulo).
  - **RF:** RF-31, RF-35, RF-65, RF-97, RF-134
  - **Dep.:** T-012, T-013
  - **Hecho cuando:** los modelos existen, documentados con docstrings.
- [x] **T-015** Modelos `standing`, `championship`, `placement` (una fila por equipo) y `placement_roster`.
  - **RF:** RF-5, RF-7, RF-49
  - **Dep.:** T-012, T-013
  - **Hecho cuando:** los modelos existen, documentados con docstrings.
- [x] **T-016** Generar y revisar la primera migración con todas las tablas. Prueba de integración que inserta y lee una fila de cada tabla y comprueba las restricciones: año de temporada único, fase fuera de la lista rechazada por la base de datos, estadística nula aceptada.
  - **RF:** RF-31, RF-52, RF-65
  - **Dep.:** T-011 a T-015
  - **Hecho cuando:** la migración se aplica desde cero y la prueba pasa.
- [x] **T-017 · Cierre F1**
  - **Dep.:** T-011 a T-016
  - **Hecho cuando:** las pruebas están en verde, se ha entregado la guía manual (ver las tablas en `psql` con `\dt`) y se ha sugerido el commit.

---

## F2 — Reglas de dominio

Funciones puras en `backend/app/domain/`, sin base de datos (plan D-5).

- [x] **T-018** Pruebas unitarias e implementación de `validation`:
  - estadística, marcador, K/D o premio negativos → no válido;
  - porcentaje de la bolsa menor que 0 o mayor que 100 → no válido;
  - al mejor de 5, 4 mapas ganados → no válido; 3 → válido;
  - 0 → válido (no es ausencia);
  - logo `https://…/x.png` → válido; `http://…`, `javascript:…` o sin extensión de imagen → no válido.
  - **RF:** RF-100, RF-101, RF-130
  - **Dep.:** T-007
  - **Hecho cuando:** las pruebas pasan.
- [x] **T-019** Pruebas unitarias e implementación de `priority`:
  - con valores de las tres fuentes gana BreakingPoint; sin él, la Wiki; sin los dos, la web oficial;
  - un valor no válido de la fuente principal cede ante uno válido de otra;
  - en la tabla de posiciones, el orden es web oficial > BreakingPoint > Wiki;
  - sin ningún valor válido → nulo.
  - **RF:** RF-66, RF-67, RF-75, RF-110
  - **Dep.:** T-007
  - **Hecho cuando:** las pruebas pasan.
- [x] **T-020** Pruebas unitarias e implementación de `entity_links`:
  - dos referencias con el mismo gamertag y sin enlace → dos personas;
  - enlace `same_as` declarado por una fuente → una persona;
  - unión de la curación → una persona; separación de la curación sobre un enlace de fuente → dos personas;
  - franquicia con `predecessor` → la misma; sin él → franquicia nueva.
  - **RF:** RF-10, RF-18, RF-19, RF-113, RF-114, RF-115, RF-131, RF-132, RF-133
  - **Dep.:** T-007
  - **Hecho cuando:** las pruebas pasan.
- [x] **T-021** Pruebas unitarias e implementación de `phases`: las cinco fases de la fuente se traducen; cualquier otra (`play-in`, `tiebreaker`, `final`) → sin fase.
  - **RF:** RF-31, RF-134
  - **Dep.:** T-007
  - **Hecho cuando:** las pruebas pasan.
- [x] **T-022** Pruebas unitarias e implementación de `match_state` con la tabla del plan §3.4: cada estado de la fuente, `postponed` → `scheduled`, `forfeit` → `finished`, `cancelled` → borrar, y ningún retroceso (`finished` + `live` → `finished`).
  - **RF:** RF-35, RF-62, RF-63, RF-81, RF-82, RF-83
  - **Dep.:** T-007
  - **Hecho cuando:** las pruebas pasan.
- [x] **T-023** Pruebas unitarias e implementación de `seasons`:
  - sin temporadas empezadas → ninguna actual;
  - 2026 empezada y 2027 no → 2026;
  - un partido de Qualifiers de 2027 en vivo → 2027;
  - cancelado después ese partido → sigue 2027.
  - **RF:** RF-2, RF-3, RF-52, RF-53, RF-123
  - **Dep.:** T-007
  - **Hecho cuando:** las pruebas pasan.
- [x] **T-024** Pruebas unitarias e implementación de `identities` (partidos):
  - cambiar solo el color secundario crea una identidad nueva; repetir los mismos cinco datos no;
  - `valid_from` es la fecha publicada o, si no la hay, el instante de observación;
  - identidad de un partido: la vigente en su hora de inicio, incluido un cambio el mismo día una hora antes o después.
  - **RF:** RF-11, RF-12, RF-73, RF-74
  - **Dep.:** T-007
  - **Hecho cuando:** las pruebas pasan.
- [x] **T-025** Pruebas unitarias e implementación de `identities` (campeonatos): con fecha de final, la vigente ese día; sin fecha, la que coincide por nombre publicado; sin coincidencia, la vigente el 31 de diciembre de ese año.
  - **RF:** RF-13, RF-121, RF-124
  - **Dep.:** T-024
  - **Hecho cuando:** las pruebas pasan.
- [x] **T-026** Pruebas unitarias e implementación de `corrections`:
  - partido `finished` con un valor que cambia → corregido;
  - partido `live` que cambia → no;
  - primera llegada de un dato → no;
  - dato que llegó como no válido y luego válido en un partido `finished` → corregido.
  - **RF:** RF-96, RF-97, RF-98
  - **Dep.:** T-007
  - **Hecho cuando:** las pruebas pasan.
- [x] **T-027** Pruebas unitarias e implementación de `ages` con un "hoy" UTC inyectado:
  - fecha completa → `{min, max}` iguales, también el día del cumpleaños;
  - solo año → dos edades consecutivas;
  - edad publicada 24 en 2026 → año aproximado 2002;
  - sin datos → nulo.
  - **RF:** RF-23, RF-108, RF-109
  - **Dep.:** T-007
  - **Hecho cuando:** las pruebas pasan.
- [x] **T-028 · Cierre F2**
  - **Dep.:** T-018 a T-027
  - **Hecho cuando:** las pruebas están en verde, se ha entregado la guía manual (ejecutar `uv run pytest tests/unit -v` y leer los nombres de las pruebas frente a la spec) y se ha sugerido el commit.

---

## F3 — Ingesta, curación y cambio de temporada

- [x] **T-029** Pruebas e implementación de `ingest/records`: modelos de validación de los doce tipos de `SourceRecord` con los campos comunes y propios del plan §2.1. Un registro mal formado se rechaza con su motivo sin detener los demás. Los textos se conservan byte a byte.
  - **RF:** RF-66, RF-129
  - **Dep.:** T-016
  - **Hecho cuando:** las pruebas cubren un registro válido de cada tipo, uno mal formado y un texto con HTML que se conserva literal.
- [x] **T-030** Pruebas de integración e implementación del núcleo del `pipeline`: guarda referencias externas, enlaces y observaciones (válidas y no válidas), y agrupa referencias en entidades con `entity_links`. Los identificadores internos son estables: al unir se conserva el más antiguo; al separar, la referencia separada recibe uno nuevo.
  - **RF:** RF-18, RF-19, RF-113, RF-114, RF-115, RF-131, RF-132
  - **Dep.:** T-020, T-029
  - **Hecho cuando:** las pruebas cubren alta, unión y separación sin perder observaciones.
- [x] **T-031** Pruebas de integración e implementación del cálculo del valor resuelto (plan §3.3): prioridad, nulo = ausente, un campo omitido no borra el valor previo, valores imposibles descartados y marca de correcciones.
  - **RF:** RF-65, RF-67, RF-91, RF-96, RF-97, RF-98, RF-100, RF-101
  - **Dep.:** T-018, T-019, T-026, T-030
  - **Hecho cuando:** las pruebas cubren cada paso de §3.3.
- [x] **T-032** Ingesta de `season`, `event`, `franchise` e `identity`: temporada por año oficial, evento tal cual, plaza continuada, franquicia nueva declarada, equipos del historial como franquicias y creación de identidades.
  - **RF:** RF-10, RF-11, RF-30, RF-52, RF-53, RF-61, RF-73, RF-74, RF-114, RF-115, RF-117
  - **Dep.:** T-024, T-031
  - **Hecho cuando:** las pruebas de integración pasan.
- [x] **T-033** Ingesta de `player` y `roster`: gamertag actual (el último usado si está retirado), gamertags anteriores, datos personales solo de fuentes, país único, año aproximado desde una edad, y rosters que solo salen de registros `roster`.
  - **RF:** RF-16, RF-17, RF-21, RF-22, RF-60, RF-77, RF-104, RF-109, RF-110, RF-111
  - **Dep.:** T-027, T-031
  - **Hecho cuando:** las pruebas de integración pasan.
- [x] **T-034** Ingesta de `match`: estado con `match_state`, historial de horarios (manda el último), equipos u origen de cada lado, marcador en vivo (0-0 al pasar a en vivo sin marcador; se conserva el último conocido), `went_live_at` y `season.started_at`, fase con `phases` y borrado al cancelarse.
  - **RF:** RF-3, RF-32 a RF-39, RF-62, RF-63, RF-81 a RF-84, RF-87, RF-88, RF-89, RF-91, RF-123, RF-134
  - **Dep.:** T-021, T-022, T-023, T-032
  - **Hecho cuando:** las pruebas de integración cubren cada fila de la tabla del plan §3.4.
- [x] **T-035** Ingesta de `match_map` y `player_map_stats`: mapas jugados, repetidos (`voided` se descarta), no jugados (solo visibles con el partido `finished`), estadísticas por modo, modo desconocido con solo las comunes, K/D publicado, equipo del partido y marca de suplente (no pertenece al roster de ese equipo en la fecha del partido).
  - **RF:** RF-29, RF-40 a RF-45, RF-64, RF-79, RF-92, RF-95, RF-102, RF-103
  - **Dep.:** T-033, T-034
  - **Hecho cuando:** las pruebas de integración pasan.
- [x] **T-036** Ingesta de `standing`: posición y puntos tal como se publican, con la prioridad de la tabla (web oficial primero) y posiciones compartidas.
  - **RF:** RF-49, RF-50, RF-75, RF-122
  - **Dep.:** T-032
  - **Hecho cuando:** las pruebas de integración pasan.
- [x] **T-037** Ingesta de `championship` y `placement`: competición por año, juego, lugar publicado (`DQ` y rangos), premio en USD y porcentaje tal cual, un premio por equipo, roster con el gamertag de la final, identidad de la final y registro de campeonatos incompletos. Un campeonato no terminado se guarda pero no se expone.
  - **RF:** RF-4 a RF-7, RF-13, RF-54 a RF-59, RF-119, RF-121, RF-124
  - **Dep.:** T-025, T-033
  - **Hecho cuando:** las pruebas de integración pasan, incluido el caso de un premio de 800 000 USD con cuatro jugadores que sigue siendo 800 000.
- [x] **T-038** Estado calculado de cada jugador: de la temporada actual (roster o al menos un partido), agente libre (de la temporada y sin roster abierto) y campeonatos en los que estuvo.
  - **RF:** RF-20, RF-105, RF-106
  - **Dep.:** T-035, T-037
  - **Hecho cuando:** las pruebas de integración pasan.
- [x] **T-039** Pruebas e implementación de `curation/loader`, `curation/overlay` y el comando `apply-curation`: roles (y su cambio sin historial), uniones, separaciones y retiradas de datos personales. Un archivo mal formado no aplica nada. Aplicarlo dos veces da el mismo resultado.
  - **RF:** RF-26, RF-27, RF-76, RF-78, RF-131, RF-133
  - **Dep.:** T-030, T-033
  - **Hecho cuando:** las pruebas cubren cada sección, el archivo mal formado y la repetición.
- [x] **T-040** Pruebas de integración e implementación de `ingest/rollover`: al empezar la temporada nueva se borra el detalle de la anterior y lo que ya no figura en ninguna parte; se conservan las franquicias y los jugadores del historial y el propio historial.
  - **RF:** RF-1, RF-80, RF-105, RF-116
  - **Dep.:** T-034, T-038
  - **Hecho cuando:** las pruebas comprueban qué se borra y qué se conserva.
- [x] **T-041** Prueba de integración de seguridad de la entrada: un gamertag con HTML llega a la base de datos sin cambios y un logo no válido queda como ausente.
  - **RF:** RF-129, RF-130
  - **Dep.:** T-032, T-033
  - **Hecho cuando:** la prueba pasa.
- [x] **T-042 · Cierre F3**
  - **Dep.:** T-029 a T-041
  - **Hecho cuando:** las pruebas están en verde, se ha entregado la guía manual (aplicar un archivo de curación de ejemplo y ver el cambio de rol en `psql`) y se ha sugerido el commit.

---

## F4 — Datos de prueba

- [x] **T-043** Comando `load-fixtures`: carga primero `fixtures/real`, después `fixtures/fictional`, y aplica la curación. Se niega a cargar registros con `fictional: true` si `APP_ENV` es `production`.
  - **RF:** —
  - **Dep.:** T-039, T-040
  - **Hecho cuando:** una prueba comprueba la negativa en producción y la carga completa en `test`.
- [x] **T-044** Transcribir a mano la muestra real desde las tres fuentes, solo con lectura de sus páginas públicas. Cada archivo indica fuente, dirección y fecha de consulta. Contenido mínimo:
  - la temporada 2026 con algunas franquicias y sus identidades, un evento, un partido finalizado con mapas y estadísticas, y la tabla de posiciones;
  - varios campeonatos mundiales del historial, incluido CDL Champs 2026 con el premio de FaZe VGS (800 000 USD, caso del spike).
  - **RF:** RF-4, RF-7, RF-66
  - **Dep.:** T-043
  - **Hecho cuando:** la muestra se carga sin registros rechazados.
- [x] **T-045** Registros ficticios, con `fictional: true` y nombres que empiezan por `[FICTICIO]`, para cada caso límite de §3 de la spec: forfeit, aplazamiento, cancelación, equipo por decidir con y sin origen, en vivo sin marcador, mapa repetido, mapas no jugados, modo y fase desconocidos, valores imposibles, corrección tras finalizar, suplente, agente libre, solo año o solo edad, jugador retirado, mismo gamertag en dos personas, identidad sin logo y sin color, franquicia que sale de la liga, campeonato sin fecha de final, empate en la tabla y gamertag con HTML.
  - **RF:** casos límite de §3 de la spec
  - **Dep.:** T-043
  - **Hecho cuando:** hay al menos un registro por caso y todos se cargan (los imposibles, como observaciones no válidas).
- [x] **T-046** `curation/curation.yaml` de ejemplo: roles de los jugadores de la muestra real que confirme Hugo, y una unión, una separación y una retirada de datos personales **solo sobre jugadores ficticios**.
  - **RF:** RF-26, RF-78, RF-131, RF-133
  - **Dep.:** T-045 y la dependencia externa de roles
  - **Hecho cuando:** el archivo se aplica sin errores y no contiene datos personales.
- [x] **T-047** Prueba de integración que carga todos los datos de prueba y comprueba, caso por caso, el resultado esperado de T-045.
  - **RF:** todos los de F3
  - **Dep.:** T-044, T-045, T-046
  - **Hecho cuando:** la prueba pasa.
- [x] **T-048 · Cierre F4**
  - **Dep.:** T-043 a T-047 y la revisión de Hugo de la muestra real
  - **Hecho cuando:** las pruebas están en verde, Hugo ha revisado la muestra real frente a sus fuentes, se ha entregado la guía manual (cargar los datos en `retake` y contarlos en `psql`) y se ha sugerido el commit.

---

## F5 — API de lectura

- [x] **T-049** Esquemas de respuesta del plan §2.3, con nombres en `camelCase`, fechas ISO 8601 en UTC y `correctedFields` en las filas que pueden corregirse.
  - **RF:** RF-97
  - **Dep.:** T-016
  - **Hecho cuando:** los esquemas existen y aparecen en `/docs`.
- [x] **T-050** `GET /api/season/current`: la temporada actual, o 404 si ninguna ha empezado.
  - **RF:** RF-2, RF-3, RF-52
  - **Dep.:** T-047, T-049
  - **Hecho cuando:** las pruebas de integración pasan antes y después de un cambio de temporada.
- [x] **T-051** `GET /api/franchises`: franquicias con sus identidades ordenadas por `validFrom`.
  - **RF:** RF-10, RF-11, RF-74
  - **Dep.:** T-050
  - **Hecho cuando:** las pruebas de integración pasan.
- [x] **T-052** `GET /api/players` y `GET /api/players/{id}`: datos del plan §2.3. Ninguna respuesta contiene fecha ni año de nacimiento (la prueba recorre todas las claves de la respuesta).
  - **RF:** RF-16, RF-17, RF-20 a RF-24, RF-26, RF-27, RF-60, RF-105, RF-106, RF-110, RF-111
  - **Dep.:** T-050
  - **Hecho cuando:** las pruebas de integración pasan, incluida la de ausencia de la fecha.
- [x] **T-053** `GET /api/events`: eventos de la temporada actual.
  - **RF:** RF-30, RF-61
  - **Dep.:** T-050
  - **Hecho cuando:** las pruebas de integración pasan.
- [x] **T-054** `GET /api/matches` y `GET /api/matches/{id}`: identidad de cada lado según `scheduledAt`, origen de los equipos por decidir, historial de horarios, marcadores, mapas jugados y no jugados, y estadísticas con nulos.
  - **RF:** RF-12, RF-29 a RF-45, RF-62, RF-65, RF-79, RF-81 a RF-92, RF-95, RF-103, RF-134
  - **Dep.:** T-050
  - **Hecho cuando:** las pruebas de integración pasan con los partidos ficticios de T-045.
- [x] **T-055** `GET /api/standings`: tabla de la temporada actual, con posiciones compartidas.
  - **RF:** RF-49, RF-50, RF-75, RF-122
  - **Dep.:** T-050
  - **Hecho cuando:** las pruebas de integración pasan.
- [x] **T-056** `GET /api/championships`: solo campeonatos terminados, con clasificación, identidad de la final y rosters con los dos gamertags.
  - **RF:** RF-4 a RF-9, RF-13, RF-54 a RF-59, RF-119, RF-121, RF-124
  - **Dep.:** T-050
  - **Hecho cuando:** las pruebas de integración pasan, incluido que la temporada en curso no aparece.
- [x] **T-057** Identificador inexistente → 404 en las rutas de detalle; `/docs` disponible solo si `APP_ENV` no es `production`.
  - **RF:** —
  - **Dep.:** T-052, T-054
  - **Hecho cuando:** las pruebas de integración pasan.
- [x] **T-058 · Cierre F5**
  - **Dep.:** T-049 a T-057
  - **Hecho cuando:** las pruebas están en verde, se ha entregado la guía manual (recorrer cada ruta desde `/docs` con los datos de prueba) y se ha sugerido el commit.

---

## F6 — Reglas de presentación (frontend)

- [x] **T-059** Extraer el cálculo de luminancia y contraste de `src/config/designTokens.test.js` a `src/shared/contrast.js`, con sus pruebas, y hacer que la prueba de la paleta lo importe (plan D-13).
  - **RF:** RF-128
  - **Dep.:** —
  - **Hecho cuando:** `npm test` sigue en verde y la fórmula existe en un solo sitio.
- [x] **T-060** Añadir la variable de diseño `team-neutral` al módulo de colores (plan D-20).
  - **RF:** RF-118
  - **Dep.:** T-059
  - **Hecho cuando:** la variable existe y la prueba de la paleta sigue en verde.
- [x] **T-061** Pruebas unitarias e implementación de `src/league/leagueApi`: una función por ruta del plan §1.4, que devuelve los datos o falla con un error si la respuesta no es correcta (se enchufa al cargador de bloques de la 001). Contratos en JSDoc.
  - **RF:** —
  - **Dep.:** T-058
  - **Hecho cuando:** las pruebas cubren respuesta correcta, error del servidor y fallo de red, con `fetch` simulado.
- [x] **T-062** Pruebas unitarias e implementación de `labels`: `DQ`, `SMG` y `AR` iguales en `es` y `en`; el resto de etiquetas de §2.9 traducidas con los diccionarios de la 001.
  - **RF:** RF-125, RF-126
  - **Dep.:** T-059
  - **Hecho cuando:** las pruebas pasan en los dos idiomas.
- [x] **T-063** Pruebas unitarias e implementación de `historyRules`: `formatPlace` (`1`, `9-12`, `DQ`), `formatRosterGamertag` (dos gamertags, o uno si coinciden) y `No disponible` para datos ausentes del historial.
  - **RF:** RF-8, RF-9, RF-69, RF-112, RF-120
  - **Dep.:** T-062
  - **Hecho cuando:** las pruebas pasan.
- [x] **T-064** Pruebas unitarias e implementación de `playerRules`: `formatAge` (`24`, `24–25`, `No disponible`), `formatPersonalField`, `formatRole` (`SMG`, `AR`, `Sin rol`) y `formatTeam` (equipo o `Agente libre`).
  - **RF:** RF-23, RF-24, RF-25, RF-68, RF-71, RF-107, RF-108
  - **Dep.:** T-062
  - **Hecho cuando:** las pruebas pasan.
- [x] **T-065** Pruebas unitarias e implementación de `matchRules` (textos): `formatMatchDateTime` en la zona del dispositivo (probado con dos zonas simuladas), `formatSlot` ("Ganador de…", "Perdedor de…", `Por definir`), `formatLiveMapScore` y `formatPhase`.
  - **RF:** RF-70, RF-85, RF-86, RF-90, RF-135
  - **Dep.:** T-062
  - **Hecho cuando:** las pruebas pasan.
- [x] **T-066** Pruebas unitarias e implementación de `matchRules` (mapas y estadísticas): `displayMaps` (no jugados con `No jugado` y sin marcador), `formatStat` (0 se muestra; nulo → `No disponible`) y `needsStatsPendingNotice` (un jugador sin ninguna estadística activa el aviso; una estadística suelta ausente no; el aviso desaparece al llegar todas; un forfeit sin mapas no lo activa).
  - **RF:** RF-46, RF-47, RF-48, RF-72, RF-94
  - **Dep.:** T-062
  - **Hecho cuando:** las pruebas pasan.
- [x] **T-067** Pruebas unitarias e implementación de `correctionRules` (`isCorrected`) y `standingsRules` (`isStandingsAvailable`: sin filas o todos sin puntos → no disponible).
  - **RF:** RF-51, RF-99
  - **Dep.:** T-062
  - **Hecho cuando:** las pruebas pasan.
- [x] **T-068** Pruebas unitarias e implementación de `teamBadge`:
  - con logo propio → ese logo;
  - sin logo → el de la identidad más reciente;
  - ninguna de las dos con logo → abreviatura sobre el color primario, aunque una identidad antigua tenga logo;
  - sin color primario → abreviatura sobre `team-neutral`;
  - texto blanco o negro, el de mayor contraste, y prueba de propiedad: con 1000 colores de fondo aleatorios, el contraste nunca baja de 4,5:1.
  - **RF:** RF-14, RF-15, RF-118, RF-127, RF-128
  - **Dep.:** T-059, T-060
  - **Hecho cuando:** las pruebas pasan.
- [x] **T-069 · Cierre F6**
  - **Dep.:** T-059 a T-068
  - **Hecho cuando:** `npm test` y pytest están en verde, se ha entregado la guía manual (llamar a `leagueApi` desde la consola del navegador con los dos servidores arrancados) y se ha sugerido el commit.

---

## F7 — Cierre

- [x] **T-070** Checklist de seguridad del plan §5: ninguna consulta SQL construida concatenando texto; ningún `dangerouslySetInnerHTML`; `backend/.env` fuera de git; negativa a cargar datos ficticios en producción; fecha de nacimiento ausente de la API; archivo de curación sin datos personales.
  - **RF:** RF-24, RF-77, RF-129, RF-130
  - **Dep.:** T-069
  - **Hecho cuando:** cada punto está comprobado y anotado en la guía.
- [x] **T-071** *(Desbloqueada tras corregir el fallo de la 001, plan I-34.)* Ejecutar todas las pruebas: pytest, `npm test` y `npm run test:e2e` (para confirmar que la 001 no se ha roto).
  - **RF:** —
  - **Dep.:** T-070
  - **Hecho cuando:** todo está en verde.
- [ ] **T-072** Redactar `verification-guide.md` de la 002 con los pasos de cada fase y una fila por RF (constitución §5).
  - **RF:** todos
  - **Dep.:** T-071
  - **Hecho cuando:** Hugo confirma que todos los RF se cumplen.
- [x] **T-073** Sincronizar la spec y el plan con cualquier cambio surgido durante la implementación, en un registro de implementación en el plan (constitución §1.3).
  - **RF:** —
  - **Dep.:** T-072
  - **Hecho cuando:** la spec, el plan y el código coinciden.
- [ ] **T-074 · Cierre de la spec 002**
  - **Dep.:** T-070 a T-073
  - **Hecho cuando:** todas las pruebas están en verde, se ha sugerido el commit final y Hugo aprueba el cierre de la spec 002.

---

## Trazabilidad RF → tareas

| RF | Tareas |
|---|---|
| RF-1 | T-040 |
| RF-2, RF-3 | T-023, T-034, T-050 |
| RF-4 a RF-7 | T-015, T-037, T-044, T-056 |
| RF-8, RF-9 | T-056, T-063 |
| RF-10, RF-11 | T-012, T-020, T-024, T-032, T-051 |
| RF-12 | T-024, T-054 |
| RF-13 | T-025, T-037, T-056 |
| RF-14, RF-15 | T-068 |
| RF-16, RF-17 | T-013, T-033, T-052 |
| RF-18, RF-19 | T-020, T-030 |
| RF-20 | T-038, T-052 |
| RF-21, RF-22 | T-013, T-033, T-052 |
| RF-23 | T-027, T-052, T-064 |
| RF-24 | T-052, T-064, T-070 |
| RF-25 | T-064 |
| RF-26, RF-27 | T-013, T-039, T-046, T-052 |
| RF-29 | T-035, T-054 |
| RF-30, RF-31 | T-014, T-016, T-021, T-032, T-034, T-053, T-054 |
| RF-32 a RF-39 | T-014, T-022, T-034, T-054 |
| RF-40 a RF-45 | T-035, T-054 |
| RF-46 a RF-48 | T-066 |
| RF-49, RF-50 | T-015, T-036, T-055 |
| RF-51 | T-067 |
| RF-52, RF-53 | T-012, T-016, T-023, T-032, T-050 |
| RF-54 a RF-59 | T-037, T-056 |
| RF-60 | T-033, T-052 |
| RF-61 | T-032, T-053 |
| RF-62, RF-63 | T-022, T-034, T-054 |
| RF-64 | T-035 |
| RF-65 | T-011, T-014, T-016, T-031, T-054 |
| RF-66, RF-67 | T-019, T-029, T-031, T-044 |
| RF-68 | T-064 |
| RF-69 | T-063 |
| RF-70 | T-065 |
| RF-71 | T-064 |
| RF-72 | T-066 |
| RF-73, RF-74 | T-012, T-024, T-032, T-051 |
| RF-75 | T-019, T-036, T-055 |
| RF-76 | T-039 |
| RF-77 | T-033, T-070 |
| RF-78 | T-039, T-046 |
| RF-79 | T-035, T-054 |
| RF-80 | T-040 |
| RF-81 a RF-83 | T-022, T-034, T-054 |
| RF-84 | T-034, T-054 |
| RF-85, RF-86 | T-065 |
| RF-87 a RF-89 | T-034, T-054 |
| RF-90 | T-065 |
| RF-91 | T-031, T-034, T-054 |
| RF-92 | T-035, T-054 |
| RF-94 | T-066 |
| RF-95 | T-035, T-054 |
| RF-96 a RF-98 | T-011, T-026, T-031, T-049 |
| RF-99 | T-067 |
| RF-100, RF-101 | T-018, T-031 |
| RF-102, RF-103 | T-035, T-054 |
| RF-104 | T-033 |
| RF-105, RF-106 | T-038, T-040, T-052 |
| RF-107, RF-108 | T-027, T-064 |
| RF-109 | T-027, T-033 |
| RF-110, RF-111 | T-019, T-033, T-052 |
| RF-112 | T-063 |
| RF-113 a RF-115 | T-020, T-030, T-032 |
| RF-116 | T-040 |
| RF-117 | T-032 |
| RF-118 | T-060, T-068 |
| RF-119 | T-037, T-056 |
| RF-120 | T-063 |
| RF-121 | T-025, T-037, T-056 |
| RF-122 | T-036, T-055 |
| RF-123 | T-023, T-034 |
| RF-124 | T-025, T-037, T-056 |
| RF-125, RF-126 | T-062 |
| RF-127 | T-068 |
| RF-128 | T-059, T-068 |
| RF-129 | T-029, T-041, T-070 |
| RF-130 | T-018, T-041, T-070 |
| RF-131 a RF-133 | T-020, T-030, T-039, T-046 |
| RF-134 | T-014, T-021, T-034, T-054 |
| RF-135 | T-065 |
