# Plan: Datos de la Liga

- **Spec**: [`002-league-data/spec.md`](spec.md) (`Aprobado`, 2026-09-22, con las revisiones R-1 y R-2)
- **Fecha**: `2026-09-22`
- **Estado**: `Aprobado` (aprobado por Hugo el 2026-09-22)

Este documento describe **CÓMO** se construirá la spec 002. No contiene código: define módulos, contratos de datos, decisiones y fases. Cada parte indica qué requisitos (RF) cubre.

---

## 0. Resumen

- **Qué se construye:** el **backend** de Retake (Python, FastAPI y PostgreSQL) con el modelo de datos de la liga y todas sus reglas de escritura, una **API de solo lectura** y, en el frontend, las **reglas comunes de presentación** de §2.9 como funciones puras.
- **Qué no se construye:** la obtención de datos de BreakingPoint.gg, la Wiki y la web oficial (spec 003) ni ninguna pantalla con datos (specs 004 en adelante). El pie de la 001 sigue con el año provisional (D-18).
- **Idea central:** todo dato entra como un **registro de fuente** (`SourceRecord`, §2.1). El backend guarda lo que dice cada fuente por separado (**observaciones**) y calcula el **valor resuelto** aplicando la prioridad de fuentes, la validación, las correcciones y la curación manual (D-2). La 003 solo tendrá que producir registros de fuente; las reglas de la 002 ya estarán hechas y probadas.
- **Mientras no exista la 003**, los registros de fuente salen de **datos de prueba**: una muestra real pequeña transcrita a mano y registros ficticios marcados para cada caso límite (P-6).
- **Curación manual** (roles, uniones y separaciones de jugadores, retirada de datos personales): un **archivo versionado** en el repositorio que el backend aplica encima de las fuentes (P-4).
- **Herramientas nuevas elegidas por Hugo** (constitución §3.2, detalle en §4.2): FastAPI, SQLAlchemy 2 + Alembic, uv + pytest y PostgreSQL 18 de Homebrew.
- **Revisiones de la spec surgidas al planificar** (ya aplicadas en la spec): R-1, fase desconocida → partido sin fase; R-2, la edad se calcula con la fecha UTC para no exponer la fecha de nacimiento.

---

## 1. Módulos

El backend vive en una carpeta nueva, `backend/`, en la raíz del repositorio junto al frontend (`src/`), `specs/` y `maqueta/` (D-1). Los nombres de carpetas, archivos, tablas, campos y rutas van en inglés (constitución §7.1).

```
backend/
├── app/
│   ├── main.py          Aplicación FastAPI y registro de rutas
│   ├── config.py        Configuración leída de variables de entorno
│   ├── db/              Conexión, sesión y modelos de tablas (SQLAlchemy)
│   ├── domain/          Reglas de la 002 como funciones puras, sin base de datos
│   ├── ingest/          Entrada de registros de fuente y cambio de temporada
│   ├── curation/        Lectura y aplicación del archivo de curación
│   ├── api/             Rutas de solo lectura y esquemas de respuesta
│   └── cli.py           Comandos: migrar, cargar datos de prueba, aplicar curación
├── migrations/          Migraciones de Alembic
├── curation/
│   └── curation.yaml    Archivo de curación manual (P-4)
├── fixtures/
│   ├── real/            Muestra real transcrita, con fuente y fecha por archivo
│   └── fictional/       Registros ficticios para casos límite (D-16)
├── tests/
│   ├── unit/            Reglas de dominio
│   └── integration/     Ingesta y API contra una base de datos de prueba
├── pyproject.toml       Dependencias (uv)
├── uv.lock
├── alembic.ini
└── .env.example         Variables necesarias, sin valores secretos

src/
├── league/              NUEVO: cliente de la API y reglas de §2.9
└── shared/contrast.js   NUEVO: cálculo de contraste WCAG compartido (D-13)
```

### 1.1 `backend/app/domain/` — reglas puras

| Pieza | Responsabilidad | RF |
|---|---|---|
| `validation` | Decide si un valor es imposible: estadísticas, marcadores, K/D o premios negativos; porcentaje fuera de 0–100; mapas ganados por encima de ⌊N/2⌋+1. Valida que un logo sea una dirección `https` con extensión de imagen. | RF-100, RF-101, RF-130 |
| `priority` | Elige el valor resuelto de un campo entre las observaciones válidas de cada fuente: BreakingPoint.gg > Wiki > web oficial, salvo en la tabla de posiciones, donde manda la web oficial. | RF-66, RF-67, RF-75, RF-110 |
| `entity_links` | Agrupa las referencias externas que son la misma entidad: enlaces que declara una fuente, uniones de la curación y separaciones de la curación, en ese orden. Nunca une por coincidencia de nombre o gamertag. | RF-10, RF-18, RF-19, RF-113 a RF-115, RF-131 a RF-133 |
| `identities` | Detecta cuándo nace una identidad nueva (cambia cualquiera de sus cinco datos) y devuelve la identidad vigente en un instante dado. Para campeonatos sin fecha de final, busca por nombre publicado y, si no coincide, usa el 31 de diciembre de ese año. | RF-11 a RF-13, RF-73, RF-74, RF-121, RF-124 |
| `match_state` | Traduce el estado de la fuente (`scheduled`, `live`, `finished`, `postponed`, `forfeit`, `cancelled`) a los tres estados de Retake y aplica la regla de no retroceder (§3.4). | RF-35, RF-62, RF-63, RF-81 a RF-83 |
| `seasons` | Calcula la temporada actual a partir de las temporadas que ya empezaron. Una temporada empieza cuando cualquier partido oficial suyo pasa a `en vivo`, y ese inicio nunca se deshace. | RF-2, RF-3, RF-52, RF-53, RF-123 |
| `corrections` | Decide si un cambio de valor resuelto es una corrección: la entidad está cerrada (partido `finalizado` o historial) y el campo ya había recibido alguna observación antes. | RF-96 a RF-98 |
| `ages` | Calcula la edad con la fecha UTC como rango `{min, max}`: exacta con fecha completa y de dos valores con solo el año. Convierte una edad publicada sin fecha en un año aproximado. | RF-23, RF-108, RF-109 |
| `phases` | Traduce la fase de la fuente a una de las cinco fases, o a "sin fase" si no es ninguna. | RF-31, RF-134 |

### 1.2 `backend/app/ingest/` — entrada de datos

| Pieza | Responsabilidad | RF |
|---|---|---|
| `records` | Modelos de validación (Pydantic) de cada tipo de `SourceRecord` (§2.1). Rechaza registros mal formados sin afectar a los demás. | RF-66, RF-129 |
| `pipeline` | Por cada registro: valida los campos, guarda las observaciones (también las no válidas, marcadas), agrupa referencias, recalcula el valor resuelto de las entidades afectadas, marca correcciones, aplica las reglas de estado e identidad y aplica la curación. | RF-1 a RF-133 (escritura) |
| `rollover` | Al empezar una temporada nueva, borra el detalle competitivo de la anterior (eventos, partidos, mapas, estadísticas, posiciones, rosters) y las franquicias y jugadores que ya no figuran ni en la temporada nueva ni en el historial. | RF-1, RF-80, RF-105, RF-116 |

### 1.3 `backend/app/curation/`

| Pieza | Responsabilidad | RF |
|---|---|---|
| `loader` | Lee y valida `curation.yaml` (§2.2). Un error de formato detiene la aplicación con un mensaje claro y no deja cambios a medias. | — |
| `overlay` | Aplica encima de las fuentes: roles, uniones y separaciones de jugadores, y retiradas de datos personales. | RF-26, RF-27, RF-76, RF-78, RF-131, RF-133 |

### 1.4 `backend/app/api/` — solo lectura

| Ruta | Devuelve | RF |
|---|---|---|
| `GET /api/health` | Estado del servicio y de la base de datos. | — |
| `GET /api/season/current` | Temporada actual. | RF-2, RF-3, RF-52 |
| `GET /api/franchises` | Franquicias con todas sus identidades. | RF-10, RF-11, RF-14, RF-15, RF-74 |
| `GET /api/players`, `GET /api/players/{id}` | Jugadores con sus datos, sin fecha de nacimiento. | RF-16 a RF-27, RF-60, RF-105 a RF-111 |
| `GET /api/events` | Eventos de la temporada actual. | RF-30, RF-61 |
| `GET /api/matches`, `GET /api/matches/{id}` | Partidos con equipos, horarios, marcadores, mapas y estadísticas. | RF-12, RF-29 a RF-48, RF-62 a RF-65, RF-81 a RF-95, RF-103 |
| `GET /api/standings` | Tabla de posiciones de la temporada actual. | RF-49 a RF-51, RF-75, RF-122 |
| `GET /api/championships` | Historial de campeonatos mundiales con clasificación y rosters. | RF-4 a RF-9, RF-13, RF-20, RF-54 a RF-59, RF-119 a RF-121, RF-124 |

Los contratos de respuesta están en §2.3.

### 1.5 `src/league/` — frontend

| Pieza | Responsabilidad | RF |
|---|---|---|
| `leagueApi` | Funciones de lectura de cada ruta de §1.4. Devuelven los datos o fallan con un error, de modo que se enchufan directamente al cargador de bloques de la 001 (`load`). | — |
| `labels` | Siglas que nunca se traducen (`DQ`, `SMG`, `AR`) y acceso a las etiquetas traducidas de la 001. | RF-125, RF-126 |
| `historyRules` | Lugar publicado, rango o `DQ`; gamertag de la final junto al actual, o una sola vez si coinciden; `No disponible` para datos ausentes del historial. | RF-8, RF-9, RF-69, RF-112, RF-120 |
| `playerRules` | Edad (exacta o rango), datos personales ausentes, rol o `Sin rol`, equipo o `Agente libre`. | RF-23 a RF-25, RF-68, RF-71, RF-107, RF-108 |
| `matchRules` | Fecha y hora en la zona del dispositivo; equipo por decidir ("Ganador de…", "Perdedor de…" o `Por definir`); marcador en vivo ausente; mapas no jugados; estadística ausente; aviso "Estadísticas pendientes"; fase ausente. | RF-46 a RF-48, RF-70, RF-72, RF-85, RF-86, RF-90, RF-94, RF-135 |
| `correctionRules` | Indica si un campo concreto está marcado como corregido. | RF-99 |
| `standingsRules` | Indica si la tabla de posiciones está disponible. | RF-51 |
| `teamBadge` | Decide qué pintar como escudo de un equipo: el logo de la identidad, el de la identidad más reciente o la abreviatura con su color de fondo y un texto blanco o negro. | RF-14, RF-15, RF-118, RF-127, RF-128 |

Ninguna de estas piezas es un componente con diseño: cada spec visual decide dónde y cómo se pintan (§2.9 de la spec, D-12).

---

## 2. Contratos

Se describen en tablas, sin código.

### 2.1 `SourceRecord` — contrato de entrada (lo producirá la spec 003)

Campos comunes a todos los registros:

| Campo | Tipo | Descripción |
|---|---|---|
| `kind` | texto | Tipo de registro: `season`, `event`, `franchise`, `identity`, `player`, `roster`, `match`, `match_map`, `player_map_stats`, `standing`, `championship` o `placement`. |
| `source` | `bp`, `wiki` o `cdl` | BreakingPoint.gg, Call of Duty Esports Wiki o web oficial de la CDL (RF-66). |
| `source_id` | texto | Identificador del objeto en esa fuente. Junto con `source` forma la **referencia externa**. |
| `observed_at` | fecha y hora UTC | Momento en que se obtuvo el dato. |
| `same_as` | lista de referencias externas | Otras referencias que **la propia fuente** declara como el mismo objeto (p. ej. la Wiki enlaza la ficha de BreakingPoint). Es la única vía automática para unir registros (RF-131). |
| `fictional` | booleano | `true` solo en los datos de prueba ficticios (D-16). |

Campos propios de cada tipo (resumen; `tasks.md` detallará la validación de cada uno):

| `kind` | Campos |
|---|---|
| `season` | `year` oficial, `name` (ej. `CDL 2026`). |
| `event` | `season_year`, `name` tal como se publica. |
| `franchise` | `predecessor` (referencia externa de la plaza que continúa, si la fuente la declara; RF-114). |
| `identity` | `franchise_ref`, `short_name`, `abbreviation`, `logo_url`, `primary_color`, `secondary_color`, `valid_from` (si la fuente la publica). |
| `player` | `gamertag`, `previous_gamertags`, `real_name`, `country`, `birth_date` o `birth_year` o `age`, `retired`. |
| `roster` | `franchise_ref`, `player_ref`, `from`, `to`. |
| `match` | `event_ref`, `phase`, `best_of`, `status`, `scheduled_at`, `slots` (dos: `franchise_ref` u `origin` = `{match_ref, outcome}`), `maps_won`, `live_map` (`mode`, `score`), `winner_side`. |
| `match_map` | `match_ref`, `position`, `mode`, `map_name`, `status` (`played`, `not_played` o `voided`), `score`, `winner_side`. |
| `player_map_stats` | `map_ref`, `player_ref`, `franchise_ref`, estadísticas comunes y las del modo. |
| `standing` | `season_year`, `franchise_ref`, `position`, `points`. |
| `championship` | `year`, `competition`, `game_name`, `game_abbreviation`, `final_date`, `completed`. |
| `placement` | `championship_ref`, `franchise_ref`, `published_team_name`, `place` (texto publicado: `1`, `9-12`, `DQ`), `prize_usd`, `pool_percent`, `roster` (lista de `{player_ref, gamertag_at_final}`). |

Reglas del contrato:
- Un campo **omitido o nulo** significa "la fuente no lo publica en esta observación" y **no borra** un valor observado antes (D-8). Así se cumplen el último marcador conocido (RF-91) y la distinción entre ausente y 0 (RF-65).
- Los textos se guardan tal cual, sin interpretar (RF-129).

### 2.2 `curation.yaml` — archivo de curación (P-4)

| Sección | Contenido de cada entrada | RF |
|---|---|---|
| `roles` | referencia de jugador, `SMG` o `AR`, motivo | RF-26, RF-27, RF-76 |
| `player_merges` | dos o más referencias de jugador que son la misma persona, motivo | RF-131 |
| `player_splits` | dos referencias que una fuente relaciona pero son personas distintas, motivo | RF-133 |
| `personal_data_removals` | referencia de jugador, fecha de la petición | RF-78 |

- Toda entrada lleva **motivo o fecha**; el historial de git registra quién la cambió y cuándo.
- El archivo solo contiene referencias y motivos, **nunca datos personales** (§5).
- Se aplica con un comando (`apply-curation`) y en cada carga de datos. Aplicarlo dos veces da el mismo resultado.

### 2.3 Respuestas de la API

JSON con nombres de campo en `camelCase`, fechas en ISO 8601 con zona UTC. Cada fila que puede corregirse lleva `correctedFields`: la lista de campos marcados como corregidos (RF-97).

**`Identity`**

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | texto | Identificador interno. |
| `shortName`, `abbreviation` | texto | RF-11. |
| `logoUrl` | texto o nulo | Solo si pasó la validación de imagen (RF-130). |
| `primaryColor`, `secondaryColor` | color o nulo | RF-11. |
| `validFrom` | fecha y hora | RF-74. |

**`Franchise`**: `id`, `identities` (lista de `Identity` ordenada por `validFrom`).

**`Player`**

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | texto | Identificador interno estable. |
| `currentGamertag` | texto | RF-16, RF-111. |
| `previousGamertags` | lista de texto | RF-17. |
| `realName`, `country` | texto o nulo | Nulo si no se conoce o se retiró (RF-25, RF-78, RF-110). |
| `age` | `{min, max}` o nulo | Calculada en UTC en el servidor: `min = max` con fecha completa; dos valores con solo el año (RF-23, RF-108). **Nunca se envía la fecha ni el año de nacimiento** (RF-24, D-10). |
| `role` | `SMG`, `AR` o nulo | Nulo = `Sin rol` (RF-26, RF-27). |
| `teamFranchiseId` | texto o nulo | Equipo actual. |
| `isCurrentSeason` | booleano | RF-105. |
| `isFreeAgent` | booleano | Jugador de la temporada sin equipo (RF-106). |
| `championshipIds` | lista | Campeonatos del historial en los que estuvo (RF-20). |

**`Match`**

| Campo | Tipo | Descripción |
|---|---|---|
| `id`, `eventId`, `eventName` | texto | RF-30, RF-61. |
| `phase` | una de las cinco fases o nulo | RF-31, RF-134. |
| `bestOf` | número | RF-34. |
| `status` | `scheduled`, `live` o `finished` | RF-35. |
| `scheduledAt` | fecha y hora | La más reciente (RF-88). |
| `scheduleHistory` | lista de fechas y horas | Todas, en orden (RF-87). |
| `slots` | dos elementos | Cada uno con `franchiseId` y la `identity` vigente en `scheduledAt` (RF-12), u `origin` = `{matchId, outcome}` si el equipo aún no se conoce (RF-84), o ambos nulos (RF-86). |
| `mapsWon` | `[a, b]` o nulo | En vivo y final (RF-36, RF-38, RF-89). |
| `liveMap` | `{mode, score}` o nulo | `score` nulo si no se publica (RF-37, RF-90). |
| `winnerSide` | `1`, `2` o nulo | RF-39. |
| `maps` | lista de `MatchMap` | Ver abajo. |

**`MatchMap`**: `position`, `mode`, `mapName`, `played` (booleano), `score` y `winnerSide` (solo si se jugó), `correctedFields`, y `stats`: lista de `{playerId, franchiseId, isSubstitute, kills, deaths, kd, damage, assists, hillTime, contestedHillTime, firstBloods, firstDeaths, plants, defuses, zoneCaptures, overloads, correctedFields}`. Cada estadística es un número o **nulo = no publicada** (RF-41 a RF-46, RF-65, RF-79, RF-95, RF-103).

**`StandingRow`**: `franchiseId`, `identity`, `position`, `points` (RF-49, RF-50, RF-122).

**`Championship`**: `year`, `competition`, `gameName`, `gameAbbreviation`, `finalDate` (o nulo) y `placements`: lista de `{franchiseId, identity, place, isDq, prizeUsd, poolPercent, roster: [{playerId, gamertagAtFinal, currentGamertag}], correctedFields}`. Solo se incluyen campeonatos terminados (RF-55).

### 2.4 Reglas de §2.9 en el frontend

| Función | Entrada | Salida | RF |
|---|---|---|---|
| `formatPlace` | lugar publicado e `isDq` | `DQ`, el rango o el número tal cual | RF-8, RF-9, RF-125 |
| `formatRosterGamertag` | gamertag de la final y actual | uno o los dos | RF-69, RF-112 |
| `formatAge` | `age` | `24`, `24–25` o `No disponible` | RF-23, RF-24, RF-25, RF-108 |
| `formatPersonalField` | texto o nulo | el texto o `No disponible` | RF-25, RF-120 |
| `formatRole` | `role` | `SMG`, `AR` o `Sin rol` traducido | RF-71, RF-125 |
| `formatTeam` | jugador | identidad del equipo o `Agente libre` | RF-68, RF-107 |
| `formatMatchDateTime` | fecha y hora UTC, idioma | texto en la zona del dispositivo, con los formateadores de la 001 | RF-70 |
| `formatSlot` | `slot`, texto del partido de origen | nombre del equipo, "Ganador de…", "Perdedor de…" o `Por definir` | RF-85, RF-86 |
| `formatLiveMapScore` | `liveMap` | marcador o `No disponible` | RF-90 |
| `displayMaps` | `maps` | mapas jugados y no jugados, estos con `No jugado` y sin marcador | RF-94 |
| `formatStat` | número o nulo | el número (incluido 0) o `No disponible` | RF-46 |
| `needsStatsPendingNotice` | partido | verdadero si está `finished` y algún mapa jugado tiene algún jugador con todas sus estadísticas nulas | RF-47, RF-48, RF-72 |
| `formatPhase` | `phase` | fase traducida o `No disponible` | RF-126, RF-135 |
| `isCorrected` | fila y campo | booleano, para pintar `Corregido` | RF-99 |
| `isStandingsAvailable` | filas de la tabla | falso si no hay filas o ningún equipo tiene puntos | RF-51 |
| `resolveTeamBadge` | identidad y lista de identidades de la franquicia | `{kind: "logo", src}` o `{kind: "abbreviation", text, background, foreground}` | RF-14, RF-15, RF-118, RF-127, RF-128 |

---

## 3. Modelo de datos

Base de datos PostgreSQL 18. Todas las fechas y horas se guardan con zona horaria y se tratan en UTC (D-19).

### 3.1 Tablas de entrada

| Tabla | Contenido | RF |
|---|---|---|
| `external_ref` | Cada referencia externa (`source` + `source_id` + `kind`) y la entidad interna a la que pertenece. | RF-131 a RF-133 |
| `ref_link` | Enlaces `same_as` y `predecessor` declarados por las fuentes. | RF-114, RF-115, RF-131 |
| `observation` | Un valor por referencia externa y campo: `value`, `is_valid`, `first_seen_at`, `last_seen_at`. Guarda también los valores no válidos para saber que el dato "ya había llegado" (RF-98). | RF-65, RF-67, RF-91, RF-96 a RF-101 |

### 3.2 Tablas resueltas (lo que lee la API)

| Tabla | Campos principales | RF |
|---|---|---|
| `season` | `year` (único), `name`, `started_at` (se fija una vez y no se borra). | RF-2, RF-3, RF-52, RF-123 |
| `event` | `season_year`, `name`. | RF-30, RF-61 |
| `franchise` | `id`. | RF-10, RF-114 a RF-117 |
| `identity` | `franchise_id`, `short_name`, `abbreviation`, `logo_url`, `primary_color`, `secondary_color`, `valid_from`. | RF-11, RF-73, RF-74 |
| `player` | `current_gamertag`, `real_name`, `country`, `birth_date`, `birth_year`, `birth_year_is_approx`, `role`, `personal_data_removed`. | RF-16, RF-21 a RF-27, RF-60, RF-77, RF-78, RF-109 a RF-111 |
| `player_gamertag` | `player_id`, `gamertag`, orden de uso. | RF-17 |
| `roster_membership` | `player_id`, `franchise_id`, `from`, `to`. Solo sale de registros `roster`, nunca de haber jugado un partido. | RF-104, RF-106 |
| `match` | `event_id`, `phase` (nula si desconocida), `best_of`, `status`, `went_live_at`, `maps_won_1`, `maps_won_2`, `live_mode`, `live_score_1`, `live_score_2`, `winner_side`, `corrected_fields`. | RF-30 a RF-39, RF-62, RF-63, RF-89, RF-91, RF-134 |
| `match_schedule` | `match_id`, `scheduled_at`, `seq`. | RF-33, RF-81, RF-87, RF-88 |
| `match_slot` | `match_id`, `side`, `franchise_id` o `origin_match_id` + `origin_outcome`. | RF-32, RF-84 |
| `match_map` | `match_id`, `position`, `mode`, `map_name`, `played`, `score_1`, `score_2`, `winner_side`, `corrected_fields`. | RF-40, RF-64, RF-92, RF-95 |
| `player_map_stats` | `map_id`, `player_id`, `franchise_id`, `is_substitute`, las 13 estadísticas de RF-41 a RF-44 (nulas = no publicadas), `corrected_fields`. | RF-29, RF-41 a RF-45, RF-65, RF-79, RF-102, RF-103 |
| `standing` | `season_year`, `franchise_id`, `position`, `points`. | RF-49, RF-50, RF-75, RF-122 |
| `championship` | `year`, `competition`, `game_name`, `game_abbreviation`, `final_date`, `completed`. | RF-4, RF-54, RF-55, RF-58, RF-119 |
| `placement` | `championship_id`, `franchise_id`, `identity_id`, `published_team_name`, `place`, `is_dq`, `prize_usd`, `pool_percent`, `corrected_fields`. Una fila por equipo: el premio nunca se reparte por jugador. | RF-5 a RF-9, RF-13, RF-56, RF-57, RF-121, RF-124 |
| `placement_roster` | `placement_id`, `player_id`, `gamertag_at_final`. | RF-6, RF-20, RF-59 |

### 3.3 Cálculo del valor resuelto

1. Por cada campo de una entidad se reúnen las observaciones **válidas** de todas sus referencias externas.
2. Se elige la de la fuente con más prioridad (RF-67; RF-75 en la tabla de posiciones). Si ninguna fuente tiene un valor válido, el campo queda nulo (ausente, RF-100).
3. Si el valor resuelto cambia, la entidad está cerrada y el campo tenía alguna observación previa, se añade el campo a `corrected_fields` (RF-96 a RF-98).
4. Se aplica la curación (§2.2).

### 3.4 Estado de un partido

Cada estado de Retake tiene un rango: `scheduled` = 1, `live` = 2, `finished` = 3.

| Estado de la fuente | Estado de Retake | Efecto adicional | RF |
|---|---|---|---|
| `scheduled` | `scheduled` | — | RF-35 |
| `postponed` | `scheduled` | Se añade la nueva fecha a `match_schedule`. | RF-81, RF-87 |
| `live` | `live` | Se fija `went_live_at` y, si es el primer partido de su temporada, `season.started_at`. Si no hay marcador, `maps_won` = 0-0. | RF-3, RF-89 |
| `finished` | `finished` | — | RF-38, RF-39 |
| `forfeit` | `finished` | Ganador y marcador de la fuente, sin mapas. | RF-82 |
| `cancelled` | — | El partido deja de guardarse. `season.started_at` no se deshace. | RF-83, RF-123 |

Si el rango que llega es menor que el guardado, se conserva el guardado (RF-62, RF-63).

### 3.5 Temporada actual y cambio de temporada

- **Temporada actual** = la de mayor `year` entre las que tienen `started_at` (RF-2, RF-3). Como `started_at` nunca se borra, el cambio es definitivo (RF-123).
- **Cambio de temporada:** cuando una temporada nueva recibe `started_at`, `rollover` borra el detalle de la anterior y lo que ya no pertenece a ninguna parte (§1.2). El historial de campeonatos no se toca: viene de sus propios registros (RF-4, RF-55).

### 3.6 Identidades

- Al llegar un registro `identity`, si alguno de sus cinco datos difiere de la última identidad de la franquicia, se crea una identidad nueva con `valid_from` = la fecha que publique la fuente o, si no la publica, el `observed_at` (RF-73, RF-74).
- **Identidad de un partido:** la última con `valid_from` ≤ `scheduledAt` vigente (RF-12, RF-88).
- **Identidad de un campeonato:** la vigente en `final_date`; sin fecha, la que tenga `short_name` igual a `published_team_name`; si ninguna, la vigente el 31 de diciembre de ese año (RF-13, RF-121, RF-124).

---

## 4. Decisiones

### 4.1 Decisiones de diseño (dentro del stack aprobado)

| # | Decisión | Alternativa descartada | Justificación | RF |
|---|---|---|---|---|
| D-1 | **Monorepo:** el backend en `backend/`, junto al frontend de la raíz. | Repositorio aparte para el backend. | Una spec cambia a menudo las dos partes; un solo repositorio mantiene spec, plan y código en el mismo historial. | — |
| D-2 | **Observaciones por fuente + valor resuelto.** | Guardar solo el último valor recibido. | La prioridad entre fuentes, las correcciones, "el dato ya había llegado" y el último marcador conocido necesitan saber qué dijo cada fuente. Guardar solo el último valor perdería esa información. | RF-67, RF-75, RF-91, RF-96 a RF-98 |
| D-3 | **Contrato `SourceRecord` independiente de la fuente.** | Que cada fuente escriba directamente en las tablas. | La 003 solo tendrá que traducir cada fuente a registros; todas las reglas de la 002 quedan en un único sitio y se prueban sin conexión a internet. | RF-66 |
| D-4 | **Identidad de entidades por referencias externas y enlaces explícitos**, más la curación. | Unir por nombre o gamertag. | RF-132 prohíbe unir por gamertag. Los enlaces explícitos y la curación son exactamente lo que piden RF-131 y RF-133. | RF-18, RF-19, RF-113, RF-131 a RF-133 |
| D-5 | **Reglas de dominio como funciones puras**, sin base de datos. | Reglas dentro de las consultas o de la API. | Se prueban miles de casos en milisegundos y se leen como la spec. | Todas las de escritura |
| D-6 | **Estado de partido con rango numérico.** | Comparar estados uno a uno. | "No retroceder" se reduce a "no bajar de rango", una regla de una línea que se prueba entera. | RF-62, RF-63 |
| D-7 | **La temporada actual se calcula, no se guarda**, a partir de `started_at`. | Una bandera `is_current` que hay que mantener. | No puede haber dos temporadas actuales ni ninguna, y el cambio definitivo sale solo. | RF-2, RF-3, RF-123 |
| D-8 | **Nulo = ausente, nunca 0;** un campo omitido no borra un valor previo. | Rellenar con 0 o borrar lo que no llega. | Es la distinción entre "no lo hizo" y "no se sabe" de la spec, y mantiene el último marcador conocido. | RF-46, RF-65, RF-91 |
| D-9 | **Correcciones como lista `corrected_fields` por fila.** | Tabla de historial de valores. | La spec pide marcar el dato concreto sin guardar el anterior; una lista por fila es lo mínimo. | RF-97 |
| D-10 | **La edad se calcula en el servidor** en UTC y se envía como rango; la fecha nunca sale. | Enviar la fecha de nacimiento al navegador. | Revisión R-2 de la spec: protege RF-24 de verdad. | RF-23, RF-24, RF-108 |
| D-11 | **API de solo lectura bajo `/api`**, con un proxy de Vite en desarrollo. | Configurar CORS entre dos orígenes. | El frontend llama a `/api` como si fuera su propio origen, sin configuración de CORS ni cambios de dirección entre entornos. | — |
| D-12 | **Reglas de §2.9 como funciones puras**, sin componentes con diseño. | Componentes listos con estilos (p. ej. `TeamBadge`). | La spec deja el diseño a cada spec visual; las funciones garantizan la regla sin decidir el aspecto. | §2.9 |
| D-13 | **Extraer el cálculo de contraste** de la prueba de la 001 a `src/shared/contrast.js` y hacer que esa prueba lo use. | Duplicar la fórmula. | RF-127 y RF-128 necesitan la misma fórmula que ya valida la paleta; una sola copia evita que diverjan. Es el único cambio en código de la 001 (sin cambio de comportamiento). | RF-127, RF-128 |
| D-14 | **Fase desconocida → nula** (revisión R-1). | Descartar el partido. | Decisión de Hugo. | RF-31, RF-134, RF-135 |
| D-15 | **Logos: solo direcciones `https` con extensión de imagen**, y el frontend solo los pinta como imagen. | Aceptar cualquier dirección. | Una dirección que no es imagen no puede ejecutar nada si solo se usa como imagen y se descarta en la entrada. | RF-130 |
| D-16 | **Los datos ficticios llevan `fictional: true` y nombres que empiezan por `[FICTICIO]`**, y solo se cargan en las bases de datos de desarrollo y prueba. | Datos ficticios con aspecto real. | Nunca pueden confundirse con datos reales de la liga. | — |
| D-17 | **El rol solo sale de la curación;** los roles que publiquen las fuentes se ignoran. | Usar el rol de la fuente por defecto. | RF-26 dice "asignado a mano por Retake". | RF-26, RF-27, RF-76 |
| D-18 | **El pie de la 001 no se toca.** La ruta `/api/season/current` queda lista, pero el cambio del pie se hará con la 003. | Conectar ya el pie a la API. | Hasta la 003 no hay partidos reales que pasen a `en vivo`, así que la temporada calculada sería la de los datos de prueba (nota de RF-3). | RF-3 |
| D-19 | **Fechas y horas con zona horaria, tratadas en UTC.** | Horas locales. | Las comparaciones de identidad (RF-12) y de edad (RF-23) son exactas; la conversión a la zona del usuario solo ocurre al pintar (RF-70). | RF-12, RF-23, RF-70 |
| D-20 | **Color neutro de equipo como variable de diseño nueva** (`team-neutral`) en el módulo de colores de la 001. | Un color fijo dentro de la regla. | Mantiene la paleta en un solo sitio (constitución §4.5). | RF-118 |

### 4.2 Decisiones tomadas por Hugo (constitución §3.2)

| # | Decisión de Hugo | Descartadas |
|---|---|---|
| P-1 | **Backend Python + PostgreSQL ya** | Solo frontend con datos de ejemplo; base de datos y reglas sin API |
| P-2 | **FastAPI** | Flask |
| P-3 | **SQLAlchemy 2 + Alembic** | SQL a mano con psycopg; SQLModel |
| P-4 | **Archivo de curación versionado** | Endpoints de administración; scripts de línea de comandos |
| P-5 | **uv + pytest + PostgreSQL 18 de Homebrew** | pip + venv; Docker para PostgreSQL |
| P-6 | **Muestra real pequeña + casos límite ficticios** | Todo ficticio; solo muestra real |

Comparativas que sirvieron de base:

#### P-1 — Dónde viven los datos y sus reglas

| | **A. Backend Python + PostgreSQL** | **B. Solo frontend** | **C. BD y reglas en Python, sin API** |
|---|---|---|---|
| Ventajas | Stack de la constitución; las reglas de escritura viven junto a los datos y la 003 solo las alimenta. | Sin servidor; todo en JavaScript. | Se modela la base de datos sin servidor web todavía. |
| Desventajas | Más piezas: API, base de datos y migraciones. | Reglas en el navegador que habría que rehacer en la 003; sin PostgreSQL. | El frontend no puede consumir nada aún. |
| Curva | Media-alta. | Baja. | Media. |

Recomendación del agente: A. **Decisión de Hugo: A.**

#### P-2 — Framework de la API

| | **A. FastAPI** | **B. Flask** |
|---|---|---|
| Ventajas | Valida entradas y salidas con modelos; documentación interactiva automática en `/docs`; muy usado hoy. | Mínimo, didáctico y con mucho material. |
| Desventajas | Introduce tipos y funciones asíncronas. | Validación y documentación con librerías extra. |
| Curva | Media. | Baja. |

Recomendación del agente: A. **Decisión de Hugo: A.** Los modelos de validación (Pydantic) sirven a la vez para el contrato `SourceRecord` (§2.1) y para las respuestas (§2.3).

#### P-3 — Acceso a PostgreSQL

| | **A. SQLAlchemy 2 + Alembic** | **B. psycopg + SQL a mano** | **C. SQLModel + Alembic** |
|---|---|---|---|
| Ventajas | ORM estándar; consultas parametrizadas por construcción; migraciones versionadas. | SQL real; migraciones como archivos `.sql`. | Una sola clase para tabla y modelo de la API. |
| Desventajas | Dos herramientas y una capa que oculta algo de SQL. | Más código repetitivo y mapeo manual. | Más joven y con menos documentación. |
| Curva | Media-alta. | Media. | Media. |

Recomendación del agente: A. **Decisión de Hugo: A.**

#### P-4 — Curación manual

| | **A. Archivo versionado** | **B. Endpoints de administración** | **C. Scripts de línea de comandos** |
|---|---|---|---|
| Ventajas | Cada cambio queda en git con su motivo; se prueba fácil; sin autenticación. | Preparado para una pantalla de administración. | Sencillo. |
| Desventajas | Hay que editar un archivo y volver a aplicarlo. | Autenticación y superficie de ataque antes de necesitarlas. | Los cambios no se versionan y se pierden al recrear la base de datos. |
| Curva | Baja. | Media. | Baja. |

Recomendación del agente: A. **Decisión de Hugo: A.**

#### P-5 — Entorno de Python, pruebas y PostgreSQL

| | **A. uv + pytest + PostgreSQL 18 (Homebrew)** | **B. pip + venv + pytest** | **C. uv + pytest + Docker** |
|---|---|---|---|
| Ventajas | uv ya está instalado, gestiona Python y dependencias con archivo de bloqueo; PostgreSQL ya está instalado. | Herramientas clásicas. | Mismo PostgreSQL en cualquier equipo. |
| Desventajas | Depende de la instalación local de PostgreSQL. | Más pasos y sin bloqueo real de versiones. | Hay que instalar Docker Desktop. |
| Curva | Baja-media. | Baja. | Media. |

Recomendación del agente: A. **Decisión de Hugo: A.** Hay dos versiones de PostgreSQL instaladas (14 y 18); se usa la 18 (riesgo en §8).

#### P-6 — Datos de prueba

| | **A. Muestra real + ficticios** | **B. Todo ficticio** | **C. Solo real** |
|---|---|---|---|
| Ventajas | Realista y cubre todos los casos límite. | Rápido. | Muy realista. |
| Desventajas | Hay que transcribir a mano la parte real. | No reproduce el caso real del spike. | Muchos casos límite quedarían sin probar. |

Recomendación del agente: A. **Decisión de Hugo: A.**

---

## 5. Seguridad (constitución §6)

| Vector | Medida en la 002 | RF |
|---|---|---|
| Inyección SQL | Todo acceso pasa por SQLAlchemy con parámetros; prohibido construir SQL concatenando texto. | — |
| XSS por datos de las fuentes | Los textos se guardan tal cual y el frontend los pinta solo como texto (escapado nativo de React); prohibido insertar HTML sin escapar. Un registro ficticio con un gamertag que contiene HTML comprueba que llega literal. | RF-129 |
| Logos maliciosos | Solo direcciones `https` con extensión de imagen; solo se pintan como imagen. | RF-130 |
| Privacidad | La fecha y el año de nacimiento nunca salen del servidor. Los datos personales solo vienen de las fuentes y se retiran con la curación. El archivo de curación no contiene datos personales. | RF-24, RF-77, RF-78 |
| Credenciales | La conexión a la base de datos se lee de `DATABASE_URL` y `TEST_DATABASE_URL` en `backend/.env`, que queda fuera de git; solo se sube `.env.example` sin secretos. | — |
| Superficie de la API | Solo lectura; no hay rutas de escritura ni autenticación que proteger. La carga de datos y la curación son comandos locales. | — |
| Datos ficticios en producción | Llevan `fictional: true`; el comando de carga se niega a cargarlos si la base de datos no es de desarrollo o prueba. | — |

---

## 6. Estrategia de pruebas

### 6.1 Niveles

| Nivel | Herramienta | Qué prueba |
|---|---|---|
| **Unitario (backend)** | pytest | Funciones de `domain/`: validación, prioridad, agrupación de referencias, identidades, estados, temporadas, correcciones, edades y fases. |
| **Integración (backend)** | pytest + base de datos `retake_test` | Ingesta completa de registros, curación, cambio de temporada y respuestas de cada ruta de la API. Cada prueba empieza con la base de datos vacía. |
| **Unitario (frontend)** | Vitest | Funciones de `src/league/`, incluida una prueba de propiedad: para cualquier color de fondo, `resolveTeamBadge` da un contraste de 4,5:1 o más. |
| **Manual** | Guía paso a paso (constitución §5) | Cargar los datos de prueba y recorrer la API desde `/docs`, comprobando cada caso límite. |

No hay pruebas de extremo a extremo nuevas: la 002 no pinta nada en pantalla.

### 6.2 Matriz de cobertura

| RF | Qué se comprueba | Unit. BE | Integ. | Unit. FE | Manual |
|---|---|:-:|:-:|:-:|:-:|
| RF-1, RF-80, RF-105, RF-116 | El cambio de temporada borra el detalle anterior y conserva lo que figura en el historial | | ✓ | | ✓ |
| RF-2, RF-3, RF-52, RF-53, RF-123 | Temporada actual antes y después del primer partido en vivo, Qualifiers incluidos, y cancelación posterior | ✓ | ✓ | | ✓ |
| RF-4 a RF-7, RF-54 a RF-59 | Historial: competición por año, un premio por equipo (caso FaZe VGS 2026: 800 000 USD), porcentaje publicado, juego y rosters | | ✓ | | ✓ |
| RF-55 | Un campeonato no terminado no aparece | ✓ | ✓ | | |
| RF-119 a RF-121, RF-124 | Campeonato incompleto e identidad sin fecha de final | ✓ | ✓ | | |
| RF-10 a RF-13, RF-73, RF-74 | Identidad nueva por cualquier cambio; identidad de un partido y de una final | ✓ | ✓ | | |
| RF-114 a RF-117 | Plaza continuada, franquicia nueva declarada, salida de la liga, equipos anteriores a 2020 | ✓ | ✓ | | |
| RF-16 a RF-19, RF-111, RF-113, RF-131 a RF-133 | Gamertags; uniones solo por enlace o curación; separación; mismo gamertag, personas distintas | ✓ | ✓ | | ✓ |
| RF-20 | Campeonatos de cada jugador | | ✓ | | |
| RF-21, RF-22, RF-60, RF-77, RF-78, RF-110 | Datos personales de fuentes, país único y retirada | ✓ | ✓ | | ✓ |
| RF-23, RF-24, RF-108, RF-109 | Edad en UTC, rango con solo año, año aproximado y ausencia de la fecha en la API | ✓ | ✓ | ✓ | ✓ |
| RF-26, RF-27, RF-76, RF-71 | Rol desde la curación, cambio sin historial, `Sin rol` | ✓ | ✓ | ✓ | |
| RF-29, RF-102 a RF-104, RF-106, RF-107 | Estadísticas en el equipo del partido, suplente marcado y fuera del roster, agente libre | ✓ | ✓ | ✓ | |
| RF-30, RF-31, RF-61, RF-134, RF-135 | Evento tal cual, fase cerrada y fase desconocida | ✓ | ✓ | ✓ | |
| RF-32, RF-84 a RF-86 | Equipo por decidir con y sin origen | | ✓ | ✓ | |
| RF-33, RF-81, RF-87, RF-88 | Aplazamiento y historial de horarios; manda el más reciente | ✓ | ✓ | | |
| RF-34 a RF-39, RF-62, RF-63, RF-82, RF-83, RF-89, RF-91 | Estados, no retroceder, forfeit, cancelación, 0-0 inicial y último marcador | ✓ | ✓ | | ✓ |
| RF-40, RF-64, RF-92, RF-94, RF-95 | Mapas jugados, repetidos, no jugados y de modo desconocido | ✓ | ✓ | ✓ | |
| RF-41 a RF-46, RF-65, RF-79 | Estadísticas por modo, K/D publicado, nulo distinto de 0 | ✓ | ✓ | ✓ | ✓ |
| RF-47, RF-48, RF-72 | Aviso "Estadísticas pendientes" y su retirada | | | ✓ | |
| RF-49 a RF-51, RF-75, RF-122 | Prioridad de la web oficial en la tabla, empates y tabla no disponible | ✓ | ✓ | ✓ | |
| RF-66, RF-67 | Prioridad BreakingPoint > Wiki > web oficial por campo | ✓ | ✓ | | |
| RF-96 a RF-101 | Correcciones marcadas por campo, primera llegada no es corrección, valores imposibles descartados | ✓ | ✓ | ✓ | ✓ |
| RF-129, RF-130 | Texto con HTML llega literal; logo no válido se descarta | ✓ | ✓ | | ✓ |
| RF-8, RF-9, RF-69, RF-112, RF-120, RF-125, RF-126 | Lugar, `DQ`, gamertags del historial, siglas sin traducir, etiquetas traducidas | | | ✓ | |
| RF-14, RF-15, RF-118, RF-127, RF-128 | Escudo: logo propio, logo reciente, abreviatura, color neutro y contraste | | | ✓ | |
| RF-68, RF-70, RF-90 | Gamertag actual, fecha en la zona del dispositivo, marcador en vivo ausente | | | ✓ | |

### 6.3 Reglas de las pruebas

- Las pruebas de integración usan una base de datos propia (`retake_test`) que nunca es la de desarrollo.
- El "hoy" de las edades y de los cambios de temporada se inyecta en las pruebas; nunca se depende del reloj real.
- Cada fase del §7 termina con sus pruebas en verde y su bloque de la guía manual.

---

## 7. Plan de implementación (fases)

Cada fase se puede verificar por separado. `tasks.md` desglosará cada una en tareas atómicas.

| Fase | Contenido | RF |
|---|---|---|
| **F0. Base del backend** | Proyecto uv en `backend/`, FastAPI con `/api/health`, configuración por variables de entorno, bases de datos `retake` y `retake_test` en PostgreSQL 18, Alembic, pytest, proxy `/api` en Vite y servidor de la API en `.claude/launch.json`. | — |
| **F1. Modelo de datos** | Tablas de §3.1 y §3.2 en la primera migración. | Base de todos |
| **F2. Reglas de dominio** | Módulos de `domain/` (§1.1) con sus pruebas unitarias. | RF-2, RF-3, RF-12, RF-13, RF-23, RF-31, RF-52, RF-53, RF-62, RF-63, RF-67, RF-73, RF-75, RF-81 a RF-83, RF-96 a RF-101, RF-108, RF-109, RF-121, RF-123, RF-124, RF-130, RF-131 a RF-134 |
| **F3. Ingesta, curación y cambio de temporada** | `records`, `pipeline`, `rollover`, `curation/` y comando `apply-curation`. | RF-1, RF-4 a RF-7, RF-10, RF-11, RF-16 a RF-22, RF-26 a RF-30, RF-32 a RF-45, RF-49 a RF-51, RF-54 a RF-61, RF-64 a RF-66, RF-74, RF-76 a RF-80, RF-84, RF-87 a RF-92, RF-95, RF-102 a RF-106, RF-110 a RF-117, RF-119, RF-122, RF-129 |
| **F4. Datos de prueba** | Muestra real transcrita (con fuente y fecha por archivo) y registros ficticios para cada caso límite; comando `load-fixtures`. | Todos los casos límite de §3 de la spec |
| **F5. API de lectura** | Rutas y esquemas de §1.4 y §2.3, con pruebas de integración. | Lectura de todos los anteriores |
| **F6. Reglas de presentación** | `src/league/`, `src/shared/contrast.js` (D-13), variable `team-neutral` (D-20). | RF-8, RF-9, RF-14, RF-15, RF-23 a RF-25, RF-46 a RF-48, RF-68 a RF-72, RF-85, RF-86, RF-90, RF-94, RF-99, RF-107, RF-108, RF-112, RF-118, RF-120, RF-125 a RF-128, RF-135 |
| **F7. Cierre** | Checklist de seguridad (§5), guía manual completa, sincronización de spec y plan con lo implementado. | — |

---

## 8. Riesgos y dependencias

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Las fuentes pueden no publicar identificadores estables o enlaces `same_as` | Sin enlaces, jugadores y franquicias no se unirían entre fuentes (RF-131). | El contrato ya lo contempla; si falta, la curación lo cubre (`player_merges`). Se revisará en la 003. |
| Dos versiones de PostgreSQL instaladas (14 y 18) | Podrían competir por el puerto 5432 o usarse la versión equivocada. | F0 comprueba la versión al conectar y la guía indica cómo arrancar solo la 18. |
| Transcripción manual de la muestra real | Errores de copia se tomarían por datos reales. | Cada archivo lleva fuente y fecha, y Hugo revisa la muestra en la guía de F4. |
| Logos enlazados a las fuentes | Pueden dejar de existir o cambiar de dirección. | Las reglas de RF-14, RF-15 y RF-118 cubren la ausencia; guardar copias propias queda para la 003. |
| Complejidad del cálculo del valor resuelto | Es la parte más delicada del backend. | Funciones puras con pruebas exhaustivas (D-5) antes de conectarlas a la base de datos. |
| Alojamiento de producción sin decidir | La API y la base de datos necesitan dónde desplegarse. | Fuera de esta spec; queda para la spec o tarea de despliegue (igual que en la 001). |
| Borrado al cambiar de temporada | Es irreversible. | Solo se dispara por un partido oficial que pasa a `en vivo` (RF-3); probado con datos de prueba antes de usarse con datos reales. |

---

## 9. Pendiente para aprobar este plan

1. ~~Elegir P-1 a P-6 (§4.2).~~ Resuelto el 2026-09-22.
2. ~~Resolver el hueco de la fase desconocida y el conflicto de la fecha de nacimiento.~~ Resuelto con las revisiones R-1 y R-2 de la spec.
3. ~~Aprobar el plan.~~ Aprobado el 2026-09-22. El siguiente paso, cuando Hugo lo pida, es `tasks.md`.

---

## 10. Registro de implementación

Ajustes surgidos al implementar, registrados para que plan y código no se desincronicen (constitución §1.3). Ninguno cambia los requisitos de la spec.

| # | Fase | Ajuste | Motivo | RF |
|---|---|---|---|---|
| I-1 | F0 | Módulos pequeños que no figuraban en el árbol de §1: `app/clock.py` (reloj inyectable), `app/db/base.py` (base de los modelos), `app/db/session.py` (conexión y comprobación de versión) y `app/db/engine.py` (motor compartido, creado bajo demanda). | Separan responsabilidades que el plan asignaba a `db/` y a la regla del reloj inyectable de `tasks.md`. | — |
| I-2 | F0 | `/api/health` responde 200 con la base de datos disponible y **503** sin ella, con `{"status", "database"}`. | Así un monitor distingue "la API está viva pero sin base de datos" de "todo funciona". | — |
| I-3 | F0 | El controlador de PostgreSQL se instala como `psycopg[binary]`, y el proyecto se empaqueta con hatchling para exponer el comando `retake`. | La variante binaria no necesita compilar nada en el equipo; el empaquetado permite `uv run retake migrate` (T-008). | — |
| I-4 | F0 | La conexión de Alembic sale siempre de `DATABASE_URL` (o de la URL que pasan las pruebas), nunca de `alembic.ini`, y también comprueba que el servidor es PostgreSQL 18. | Constitución §6.3 y riesgo de las dos versiones instaladas (§8). | — |
| I-5 | F0 | Versiones instaladas: Python 3.13.2, FastAPI 0.141, Uvicorn 0.53, SQLAlchemy 2.0.54, psycopg 3.3.6, Alembic 1.20, pydantic-settings 2.15, PyYAML 6.0.3, pytest 9.1, httpx 0.28; PostgreSQL 18.4. | Versiones estables vigentes. Starlette avisa de que prefiere `httpx2` para su cliente de pruebas; se mantiene `httpx`, que es lo aprobado, y el aviso no afecta a las pruebas. | — |
| I-6 | F1 | Corregido un fallo de `migrations/env.py` (F0): la consulta de versión abría una transacción implícita que Alembic no confirmaba, y las migraciones se deshacían sin error. Se cierra esa transacción antes de migrar. | Sin el arreglo, `upgrade head` no creaba ninguna tabla. La prueba "la migración crea todas las tablas" lo detecta. | — |
| I-7 | F1 | Detalles del esquema: identificadores internos UUID; listas cerradas (fuente, estado, fase, rol, origen, tipo de enlace) como texto con restricción CHECK en lugar de tipos ENUM nativos; restricciones CHECK de no negativos y de porcentaje 0–100 como segunda barrera tras la validación del dominio; `event`, `standing` y `roster_membership` enlazan con `season` por clave foránea (el plan decía `season_year`); `roster_membership` lleva `season_id` para que el cambio de temporada sepa qué borrar; `player.retired` para RF-111; `external_ref.fictional` para la negativa de cargar datos ficticios en producción; K/D como decimal de 3 cifras; tiempos de colina en segundos. | Las listas como texto + CHECK se amplían con una migración sencilla si la spec añade un valor. Las claves foráneas garantizan la integridad al borrar. | RF-1, RF-65, RF-101, RF-111 |
| I-8 | F1 | El plan y las tareas decían "14 estadísticas"; son **13** (RF-41 a RF-44: 5 comunes, 2 de Hardpoint, 4 de Search & Destroy y 2 de Overload). Corregido en §3.2 y en T-014. | Error de conteo en el plan. | RF-41 a RF-44 |
| I-9 | F2 | Las listas cerradas (fuentes, estados, fases, roles, orígenes, tipos de enlace) viven en `app/domain/vocabulary.py` y los modelos las importan de ahí. | El dominio no depende de la base de datos (D-5). | — |
| I-10 | F2 | **Interpretación de RF-3:** un partido cuenta como empezado si llega a `live` o más allá (también si pasa directamente de `scheduled` a `finished`, porque en la realidad se jugó); un forfeit no cuenta, porque no se juega. | La fuente puede no publicar nunca el momento en vivo de un partido. Confirmado por Hugo el 2026-09-22 (revisiones R-3 a R-5 de la spec). | RF-3 |
| I-11 | F2 | **Interpretación de RF-12:** si un partido es anterior a todas las identidades conocidas de su franquicia, se usa la más antigua. | La spec no cubre ese caso; mostrar la identidad más antigua conocida evita un equipo sin nombre. Confirmado por Hugo el 2026-09-22 (revisiones R-3 a R-5 de la spec). | RF-12 |
| I-12 | F2 | **Interpretación de RF-13:** con fecha de final, se usa la identidad vigente al terminar ese día, así que un cambio de identidad el mismo día de la final ya cuenta. | La final se juega ese día; la hora exacta no suele publicarse. Confirmado por Hugo el 2026-09-22 (revisiones R-3 a R-5 de la spec). | RF-13 |
| I-13 | F2 | La fase de la fuente se reconoce aunque venga con otra escritura ("Winners Bracket", "grand-final"); cualquier otra fase queda sin fase. Si una entidad tiene dos valores de la misma fuente, gana el más reciente. | Tolerancia a diferencias de escritura sin ampliar la lista cerrada; desempate determinista. | RF-31, RF-67, RF-134 |
| I-14 | F3 | **Arquitectura de la ingesta:** cada entidad se recalcula siempre a partir de las observaciones de todas sus referencias (`app/ingest/resolvers.py`), nunca del registro recién llegado. Jugadores, franquicias, eventos, partidos y rosters se agrupan por enlaces (y los jugadores, por la curación); temporadas y campeonatos por año, mapas por partido y posición, estadísticas por mapa y jugador, posiciones por temporada y franquicia, y clasificaciones por campeonato y franquicia. Lo que no se puede recalcular (estado del partido, horarios, inicio de temporada, identidades, correcciones) se conserva en la fila. | Recalcular tras una unión, una separación o la curación da siempre el mismo resultado, sin duplicar horarios ni identidades. | RF-1 a RF-133 (escritura) |
| I-15 | F3 | **Identidades entre fuentes:** los registros `identity` no se agrupan con `same_as`. Cada uno se compara con la identidad vigente en su fecha: si los cinco datos coinciden, se reutiliza (no se duplica); si difieren, nace una identidad nueva. Si dos fuentes publican a la vez identidades distintas para la misma franquicia, quedan las dos, ordenadas por fecha. | Evita duplicados en el caso normal sin inventar una regla de mezcla. La spec 003 debe enlazar las identidades de las fuentes o elegir una sola. | RF-11, RF-73 |
| I-16 | F3 | Un registro que apunta a un objeto que aún no existe (evento, partido, mapa, jugador, franquicia, campeonato) se **rechaza** con el motivo "Referencia desconocida"; un partido nuevo sin `best_of` también. Una observación más antigua que la guardada se ignora. | La spec 003 deberá enviar primero los objetos referenciados; un dato atrasado nunca pisa uno más reciente. | RF-66 |
| I-17 | F3 | Al **unir** dos entidades se mueven sus filas a la conservada y, si chocan con una clave única, se queda la de la conservada. Al **separar** jugadores, sus estadísticas, rosters y clasificaciones se recalculan; las filas que cambian de dueño se crean de nuevo y la antigua se borra, así que pierden su marca de corrección. | Las separaciones solo las hace la curación y son raras; conservar las marcas complicaría mucho el código. | RF-97, RF-131, RF-133 |
| I-18 | F3 | Detalles del contrato `SourceRecord` que `tasks.md` dejaba abiertos: las referencias se escriben como objeto o como texto `"fuente:id"`; `roster` exige `season_year`; `match_map` exige `position` y `status`; un lado vacío de un partido se guarda como `{}` ("se sabe que aún no hay equipo"). Los números (estadísticas, marcadores, premios…) se aceptan con cualquier forma y se validan después, para que un valor imposible descarte solo ese dato. | Cumplir RF-100 sin rechazar registros enteros. | RF-84, RF-86, RF-100 |
| I-19 | F3 | La ingesta usa por defecto el archivo de curación del proyecto, para no deshacer nunca una unión o separación hecha a mano. Los roles y las retiradas se aplican con `retake apply-curation` (y con `load-fixtures` en F4). | Una ingesta sin la curación volvería a unir jugadores separados a mano. | RF-26, RF-78, RF-131, RF-133 |
| I-20 | F3 | En el cambio de temporada se borran también las franquicias sin roster, lado de partido, estadísticas, posición ni clasificación. Una franquicia de la temporada nueva que en ese momento solo tuviera identidad se borraría y volvería a crearse con su siguiente registro. | Aplicación literal de RF-116. En la práctica, al empezar la temporada las franquicias ya tienen roster. | RF-116 |
| I-21 | F3 | Cada registro de un tipo agrupado por enlaces recalcula los grupos de todas las referencias de ese tipo. | Sencillo y suficiente para los datos de prueba; habrá que revisarlo en la spec 003 si el volumen crece. | — |
| I-22 | F3 | Añadido `choose` en `domain/priority` (devuelve la observación ganadora con su fuente y fecha) y un módulo de consultas `app/db/queries.py` para el estado calculado de los jugadores (T-038). | `choose` hace falta para el año aproximado de RF-109, que usa el año en que se observó la edad. | RF-20, RF-105, RF-106, RF-109 |
| I-23 | F4 | Formato de los datos de prueba: un JSON por archivo con `records` y una cabecera. La muestra real lleva `consulted` (fuente, dirección, fecha y para qué se usó) y `notes`; la ficticia lleva `description` y `cases` (caso → registros que lo cubren). `load-fixtures` valida que la muestra real no tenga registros ficticios y que todo lo de la carpeta ficticia lleve `fictional: true`, y se niega a cargar nada ficticio en producción. | Cada dato real se puede rastrear hasta su página; ningún dato inventado se confunde con uno real. | — |
| I-24 | F4 | **Muestra real** (consultada el 2026-09-22): temporada 2026, tabla de posiciones, gran final de Champs 2026 (7 mapas jugados y 2 no jugados, 56 filas de estadísticas) y campeonatos de 2013, 2020, 2021, 2025 y 2026, casi todo de la Wiki. De la web oficial, solo el resultado y la hora de la gran final, porque su tabla de temporada regular no se mostraba. De BreakingPoint, los datos de Simp (nombre real, fecha de nacimiento y gamertag anterior). Supuestos revisados y confirmados por Hugo el 2026-09-22: (1) de cada roster se toman los cuatro primeros nombres de la tabla de premios, porque los siguientes son entrenadores o suplentes; (2) el nombre oficial completo y la abreviatura del juego no aparecen en la Wiki y siguen la forma habitual; (3) sin logos ni colores, porque las páginas no los publican; (4) el `source_id` de la Wiki es el nombre de la página. | La muestra reproduce casos reales de la spec: plazas continuadas (FaZe Vegas ← Atlanta FaZe, OpTic Texas ← Dallas Empire), identidad de la fecha de la final, lugares compartidos, mapas no jugados, estadísticas no publicadas y el mismo jugador en la temporada y en el historial. | RF-4 a RF-18, RF-46, RF-52, RF-66, RF-92, RF-114 |
| I-25 | F4 | **Fallo corregido (segunda migración, `737618706e21`):** al borrar un partido que era el origen de otro (cancelación o cambio de temporada), la clave foránea dejaba vacío el partido de origen pero no su resultado, e incumplía la restricción `origin_complete`. Ahora esa restricción solo exige que un origen lleve su resultado, y al cancelar un partido se limpian también los resultados de los lados que lo tenían como origen. | La prueba de la carga completa lo detectó al simular un cambio de temporada. | RF-83, RF-84, RF-86 |
| I-26 | F4 | Los datos ficticios viven en la temporada 2026 y nunca empiezan una temporada nueva, para que cargarlos no borre la muestra real. El caso "franquicia que sale de la liga" se comprueba simulando el cambio de temporada dentro de la prueba, sin guardarlo. | Un partido ficticio de 2027 en vivo dispararía el cambio de temporada sobre los datos reales. | RF-1, RF-116 |
| I-27 | F5 | Estructura de la API: `app/api/deps.py` (sesión por petición, 503 sin base de datos, y reloj como dependencia para que las pruebas fijen "hoy"), `app/api/schemas.py` (respuestas), `app/api/views.py` (construcción de las respuestas) y `app/api/routes.py`. `app/main.py` expone `create_app(app_env)` y reexporta `engine_or_none`. | Separa HTTP, construcción de respuestas y consultas; `create_app` permite probar que en producción no hay `/docs` ni `/openapi.json`. | — |
| I-28 | F5 | Detalles de las respuestas que el plan no fijaba: franquicias por el nombre de su identidad vigente; jugadores (actuales e históricos) por gamertag; `teamFranchiseId` = roster abierto en la temporada actual en el momento de la consulta; partidos por hora de inicio y, si aún no tienen horario, la identidad de sus equipos es la vigente hoy; los mapas no jugados solo aparecen con el partido `finished`; tabla por posición y después por nombre; clasificaciones por número (el primero de un rango), después `DQ` y los lugares desconocidos; premios, porcentajes y K/D como números JSON; `/api/season/current` da 404 si ninguna temporada ha empezado. | Orden estable y útil para las specs visuales sin decidir su diseño. | RF-8, RF-9, RF-12, RF-92, RF-106, RF-122 |
| I-29 | F5 | El inicio de una temporada es el instante en que Retake **observa** el primer partido en vivo o finalizado. Con la muestra real (solo la gran final, observada el 2026-09-22), `startedAt` de 2026 es 2026-09-22 y no el 2025-12-05 real. Con datos de la spec 003 recibidos en tiempo real, ambas fechas coincidirán. | Consecuencia directa de RF-3 y de la aclaración R-3; no cambia qué temporada es la actual. | RF-3 |
| I-30 | F6 | Las reglas de §2.9 son funciones puras en `src/league/` que reciben la función de traducción `t` de la spec 001 (y el idioma cuando hace falta), así se prueban sin React en los dos idiomas y cualquier spec visual las usa con el `t` de su componente. `leagueApi` devuelve `null` en `getCurrentSeason` si ninguna temporada ha empezado (un estado válido, no un error) y lanza `LeagueApiError` con `status` (0 = sin red) en el resto de fallos. `designTokens.test.js` usa ahora `src/shared/contrast.js` (D-13). | Reutilizar la traducción y los formatos de la 001 sin acoplar las reglas a componentes. | RF-125, RF-126, RF-128 |
| I-31 | F6 | Detalles que la spec deja a la implementación: (1) la tabla no está disponible si no hay filas o **ningún equipo tiene más de 0 puntos** (decisión A-22: "sin puntos" incluye todos a 0); (2) un mapa jugado **sin ninguna fila de estadísticas** también activa "Estadísticas pendientes"; (3) si una identidad no tiene abreviatura, el escudo usa su nombre corto; (4) `formatSlot` recibe cómo nombrar el partido de origen, que decide cada spec visual; (5) los marcadores y rangos de edad se escriben con raya (`216–250`, `24–25`); (6) `team-neutral` = `#3a4252`. | Casos que aparecen con los datos reales (varios equipos sin abreviatura) o que la spec deja al diseño. | RF-15, RF-47, RF-51, RF-85, RF-118 |
| I-32 | F6 | **Fallo de la spec 001 detectado (resuelto en F7, ver I-34):** en desarrollo, `StrictMode` monta dos veces los efectos y `PageTransition` anima también la primera carga (su marca de "primera vez" sobrevive al doble montaje). Durante los 200 ms del fundido, axe mide poco contraste y la auditoría WCAG del proyecto `dev` falla de forma intermitente. En producción no ocurre. No se ha tocado el código de la 001. | Fuera del alcance de la spec 002 (constitución §1.2). | RF-73, RF-85 de la 001 |
| I-33 | F7 | Cierre: checklist de seguridad del §5 comprobado (sin SQL concatenado, sin HTML sin escapar, `backend/.env` fuera de git, negativa a cargar datos ficticios en producción, sin nacimiento en la API, curación sin datos personales, logos solo `https` de imagen). Guía de verificación en `verification-guide.md` con una fila por RF (133) y sus órdenes comprobadas. Pruebas: 275 del backend, 256 unitarias del frontend y 55 de extremo a extremo en producción en verde; en desarrollo fallan de forma intermitente las 4 auditorías WCAG por el fallo de la 001 descrito en I-32. | T-071 queda bloqueada hasta que Hugo decida sobre I-32. | — |
| I-34 | F7 | Resuelto I-32 a petición de Hugo: `PageTransition` solo anima cuando cambia la dirección (registro I-13 y tarea T-088 de la 001). Tras el arreglo: 259 pruebas unitarias del frontend, 275 del backend y 118 de extremo a extremo en verde en tres ejecuciones completas, y la auditoría WCAG de desarrollo en verde en cinco ejecuciones seguidas. | Desbloquea T-071. | RF-73, RF-85 de la 001 |

