# Guía de verificación manual — Spec 002

Guía paso a paso para que Hugo compruebe cada requisito de la spec 002 (constitución §5.1, tarea T-072). La 002 no pinta pantallas: casi todo se comprueba en la **API**, en **`psql`**, en la **consola del navegador** o con una **prueba** concreta. Cada fila indica dónde mirar, qué hacer y qué resultado esperar con los datos de prueba (muestra real + casos `[FICTICIO]`).

## Preparación

1. PostgreSQL 18 en marcha (la 14, detenida):
   ```bash
   brew services start postgresql@18
   ```
2. **Base aparte con los datos de prueba** (`retake_guia`). La base `retake` tiene los datos reales de la 003 y no se toca: **no uses `retake source-mode`**, que reescribe `backend/.env` y borra la liga (RF-12 de la 003). En una terminal propia, que se usa para todo lo del backend:
   ```bash
   createdb -h localhost retake_guia
   ```
   ```bash
   export DATABASE_URL="$(grep '^DATABASE_URL=' backend/.env | cut -d= -f2- | sed 's#/retake$#/retake_guia#')" SOURCE_MODE=fixtures
   ```
   ```bash
   uv run --directory backend retake migrate
   ```
   ```bash
   uv run --directory backend retake load-fixtures
   ```
3. Arrancar el backend de la guía (en esa misma terminal) y la web apuntando a él (en otra):
   ```bash
   uv run --directory backend uvicorn app.main:app --port 8002
   ```
   ```bash
   RETAKE_API_TARGET=http://localhost:8002 npx vite --port 5174
   ```
   Al terminar la guía, parar los dos con Ctrl+C y, si quieres, borrar la base: `dropdb -h localhost retake_guia`.
4. Herramientas:
   - **API**: abrir `http://localhost:8002/docs`, desplegar la ruta, **Try it out** → **Execute**. Para una ruta de detalle, copiar el `id` desde la lista.
   - **psql**: ejecutar la orden de la fila en una terminal (sobre `retake_guia`).
   - **Consola**: abrir `http://localhost:5174`, la consola del navegador (filtro **All**) y pegar una sola vez:
     ```js
     (async () => {
       window.api = await import('/src/league/leagueApi.js');
       window.rules = Object.assign({}, ...(await Promise.all(['labels', 'historyRules', 'playerRules', 'matchRules', 'correctionRules', 'standingsRules', 'teamBadge'].map(n => import(`/src/league/${n}.js`)))));
       const { createI18n } = await import('/src/i18n/createI18n.js');
       window.t = createI18n('es').t; window.tEn = createI18n('en').t;
       return 'listo';
     })();
     ```
     Las órdenes que devuelven una promesa (`api...then`) muestran su resultado al desplegar `Promise → result`.
   - **Prueba**: ejecutar la orden desde la raíz del repositorio (las de `pytest`, con `uv run --directory backend` delante).

Pruebas automáticas (deben estar en verde antes de empezar):

```bash
uv run --directory backend pytest
```

```bash
npm test
```

## Cambios de la spec 003 en esta spec

La 003 cambió algunos requisitos de la 002 (§5.1 de la 002). Las filas de esta guía siguen valiendo con los datos de prueba; el comportamiento nuevo se comprueba en la guía de la 003:
C-4 (RF-1: calendario de la próxima temporada guardado sin mostrar), C-5 (RF-3: cambio de temporada automático), C-6 (RF-67: en vivo manda el marcador más avanzado), C-7 (RF-73: identidad nueva según el resultado combinado), C-8 y C-25 (RF-96: plazos de corrección), C-9 (RF-131: uniones también de partidos, eventos y franquicias), C-10 (RF-78: la retirada impide volver a guardar los datos), C-12 (RF-79: K/D calculado si ninguna fuente lo publica), C-13 (RF-31: semana calculada en clasificatorios) y C-23 (RF-117a a RF-117d: equipos invitados).

## Guía por fases

| Fase | Qué comprobar |
|---|---|
| F0 | `/api/health` responde `{"status":"ok","database":"ok"}` a través de `http://localhost:5174/api/health`, y `/docs` abre. |
| F1 | `psql -h localhost -d retake_guia -c '\dt'` lista 31 tablas más `alembic_version` (19 de la 002 y 12 que añadió la 003). |
| F2 | `uv run --directory backend pytest tests/unit/domain -v`: los nombres de las pruebas describen cada regla. |
| F3 | Dos registros del mismo jugador de dos fuentes quedan en uno; `apply-curation` asigna y retira roles. |
| F4 | `load-fixtures` acepta 253 registros sin rechazos; el historial muestra `ATL FaZe` en 2021 y `DAL Empire` en 2020. |
| F5 | Las 10 rutas de la 002 en `/docs` (`health`, `season/current`, `franchises`, `players` y su detalle, `events`, `matches` y su detalle, `standings` y `championships`; las demás son de la 003) responden con los datos de prueba; ninguna respuesta de jugadores contiene "birth". |
| F6 | En la consola, `rules.displayMaps` de la gran final da 7 marcadores y 2 "No jugado". |
| F7 | Checklist de seguridad (abajo) y esta guía completa. |

---

## 2.1 Temporada actual

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-1 | Prueba | `uv run --directory backend pytest -k "rollover or franquicia_que_sale" -v` | Al empezar 2027 desaparecen eventos, partidos, posiciones y rosters de 2026; el historial se conserva. |
| RF-80 | Prueba | `pytest -k "rollover or franquicia_que_sale" -v` | Tras el cambio de temporada siguen las franquicias y los jugadores del historial (FaZe y Simp) y desaparecen los que no figuran en ninguna parte. |
| RF-52 | API `/api/season/current` | Execute. | `year: 2026` aunque la temporada empezó el 5-12-2025 (fuente consultada). |
| RF-53 | Prueba | `pytest -k qualifiers -v` | Un partido de Qualifiers en vivo hace actual la temporada nueva. |
| RF-2 | Prueba | `pytest -k "2026_empezada" -v` | Con 2027 sin empezar, la actual sigue siendo 2026. |
| RF-3 | API `/api/season/current` | Execute. | `year: 2026`, `name: "Call of Duty League 2026"` y `startedAt` con fecha (la gran final se vio finalizada). |
| RF-123 | Prueba | `pytest -k "cancela_ese_partido or temporada_sigue_iniciada" -v` | Si se cancela el partido que empezó la temporada, sigue siendo la actual. |

## 2.2 Historial de campeonatos mundiales

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-4 | API `/api/championships` | Execute. | Años 2026, 2025, 2021, 2020, 2014 (ficticio) y 2013. |
| RF-54 | API `/api/championships` | Mirar `competition`. | 2013: "Call of Duty Championship"; 2020 en adelante: "Call of Duty League Championship". |
| RF-55 | Prueba | `pytest -k no_terminado -v` | Un campeonato con `completed: false` no aparece. |
| RF-5 | API `/api/championships` | Mirar el 1.º de 2026. | `place "1"`, `prizeUsd 800000`, `poolPercent 40`, juego y `finalDate 2026-07-19`. |
| RF-56 | API `/api/championships` | Mirar `prizeUsd`. | Importes en USD nominales tal como se publicaron (2020: 1500000). |
| RF-57 | API `/api/championships` | Mirar el 1.º de 2020. | `poolPercent 32.61`, tal como lo publica la Wiki (no recalculado). |
| RF-58 | API `/api/championships` | Mirar 2026. | `gameName "Call of Duty: Black Ops 7"`, `gameAbbreviation "BO7"`. |
| RF-6 | API `/api/championships` | Mirar el `roster` de FaZe VGS 2026. | Simp, Drazah, 04 y Abuzah. |
| RF-59 | API `/api/championships` | Mirar `gamertagAtFinal` del ficticio de 2014. | `[FICTICIO] Nombre De Antes`, distinto de su `currentGamertag`. |
| RF-7 | API `/api/championships` | Mirar FaZe VGS 2026. | Un solo premio de 800000, no 3200000 (4 × 800000). |
| RF-119 | API `/api/championships` | Mirar la fila `DQ` de 2014. | Se registra sin premio ni porcentaje (`null`). |
| RF-121 | API `/api/championships` | Mirar el 1.º de 2014 (sin fecha de final). | Identidad `[FICTICIO] Nombre Antiguo`, la que coincide con el nombre publicado. |
| RF-124 | API `/api/championships` | Mirar la fila `DQ` de 2014. | Nombre publicado sin coincidencia → identidad vigente el 31-12-2014 (`[FICTICIO] Equipo A`, la más antigua). |

## 2.3 Franquicias e identidad visual

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-10 | API `/api/franchises` | Buscar la franquicia de FaZe. | Una sola franquicia con las identidades `ATL FaZe` y `FaZe VGS`. |
| RF-11 | API `/api/franchises` | Mirar una identidad. | Campos `shortName`, `abbreviation`, `logoUrl`, `primaryColor`, `secondaryColor`. |
| RF-73 | API `/api/franchises` | Buscar `[FICTICIO] Nombre Nuevo`. | Su franquicia tiene dos identidades: `Nombre Antiguo` (2013) y `Nombre Nuevo` (2024). |
| RF-74 | API `/api/franchises` | Mirar `validFrom` de `FaZe VGS`. | `2025-09-19T00:00:00Z`. |
| RF-12 | API `/api/matches` | Buscar la gran final (`bestOf: 9`). | Lados con identidad `FaZe VGS` y `OpTic TEX` (vigentes el 19-07-2026). |
| RF-13 | API `/api/championships` | Mirar el campeón de 2021 y el de 2020. | `ATL FaZe` y `DAL Empire`: la identidad de la fecha de la final, no la actual. |
| RF-114 | API `/api/franchises` | Buscar OpTic. | `DAL Empire` y `OpTic TEX` son la misma franquicia (misma plaza). |
| RF-115 | Prueba | `pytest -k sin_predecesora -v` | Una franquicia sin predecesora es una franquicia nueva. |
| RF-116 | Prueba | `pytest -k franquicia_que_sale -v` | `[FICTICIO] Se Va` desaparece al cambiar de temporada; lo del historial queda. |
| RF-117 | API `/api/franchises` | Buscar `Fariko Impact`. | Existe como franquicia con su identidad, aunque nunca fue de la CDL. |
| RF-117a | Prueba | `pytest tests/unit/sources/test_bp_unlisted.py -k invitado -v` | Un equipo de fuera de la CDL en un evento de la CDL se registra como franquicia invitada, con su identidad y sin plaza (C-23 de la 003). |
| RF-117b | Prueba | `pytest tests/unit/sources/test_bp_unlisted.py -k ficha_mensual -v` | De sus jugadores se guardan los mismos datos, con las mismas reglas, que de los de la CDL. |
| RF-117c | Prueba | `pytest tests/integration/api/test_003_guests.py -v` | No salen en `/api/franchises`, `/api/standings` ni `/api/players`; en sus partidos salen marcados (`isGuest`, `teamIsGuest`) y con sus estadísticas. |
| RF-117d | Prueba | `pytest tests/integration/ingest/test_003_unlisted.py -k deja_de_serlo -v` | Si entra en la lista de la CDL deja de ser invitado y conserva sus identidades. |

## 2.4 Jugadores

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-16 | API `/api/players` | Buscar Simp. | `currentGamertag: "Simp"`. |
| RF-111 | API `/api/players` | Buscar `[FICTICIO] Retirado`. | Su gamertag actual es el último que usó. |
| RF-17 | API `/api/players` | Mirar Simp. | `previousGamertags: ["Simplicity"]`. |
| RF-18 | API `/api/players` | Mirar Abuzah. | Dos `championshipIds` (2025 con VAN Surge y 2026 con FaZe VGS): la misma persona. |
| RF-19 | API `/api/players` | Buscar `[FICTICIO] Gemelo`. | Aparecen dos jugadores distintos. |
| RF-131 | API `/api/players` | Buscar `[FICTICIO] Unido`. | Un solo jugador: la curación los une. |
| RF-132 | API `/api/players` | Buscar `[FICTICIO] Gemelo`. | Dos jugadores: el mismo gamertag no basta para unirlos. |
| RF-133 | API `/api/players` | Buscar `[FICTICIO] Separado A` y `B`. | Dos jugadores aunque la fuente los enlaza: la curación los separa. |
| RF-113 | Prueba | `pytest -k mismo_gamertag -v` | Sin enlace de fuente ni curación, son personas distintas. |
| RF-20 | API `/api/players` | Mirar Simp. | Dos `championshipIds` (2021 y 2026). |
| RF-21 | API `/api/players` | Mirar Simp. | `realName: "Chris Lehr"`. |
| RF-22 | Prueba | `pytest -k pais_unico -v` | Se guarda el país publicado por la fuente. |
| RF-110 | Prueba | `pytest -k pais_unico -v` | Con dos fuentes, queda un único país, el de BreakingPoint. |
| RF-109 | API `/api/players` | Mirar `[FICTICIO] Solo Edad`. | `age: {min: 20, max: 21}` (edad 21 publicada en 2026 → año aproximado 2005). |
| RF-60 | Prueba | `pytest -k datos_personales -v` | Los datos personales se guardan también de jugadores solo históricos si la fuente los publica. |
| RF-77 | psql | `psql -h localhost -d retake_guia -c "select current_gamertag, real_name from player where real_name is not null"` | Solo los nombres reales publicados en las fuentes (los 8 de la gran final). |
| RF-78 | API `/api/players` | Mirar `[FICTICIO] Retirada`. | `realName`, `country` y `age` a `null`. |
| RF-26 | API `/api/players` | Mirar `[FICTICIO] A1` y `A2`. | `role: "SMG"` y `"AR"` (asignados en `curation.yaml`). |
| RF-76 | Prueba | `pytest tests/integration/ingest/test_curation.py -k roles_se_asignan -v` | Un rol se sustituye por el nuevo para toda la temporada, sin historial, y sin entrada vuelve a `Sin rol`. Con datos reales, el cambio de KiSMET de SMG a AR del 2026-09-24 (`curation.yaml` + `apply-curation`): su rol pasó a `AR` sin rastro del anterior. |
| RF-27 | API `/api/players` | Mirar Simp. | `role: null` (sin rol asignado por Retake). |
| RF-105 | API `/api/players` | Mirar `[FICTICIO] Libre`. | `isCurrentSeason: true` aunque ya no tiene equipo. |
| RF-106 | API `/api/players` | Mirar `[FICTICIO] Libre`. | `isFreeAgent: true`, `teamFranchiseId: null`. |
| RF-102 | API `/api/players` | Mirar `[FICTICIO] Suplente`. | `isCurrentSeason: true`. |
| RF-103 | API `/api/matches` | Partido `[FICTICIO]` al mejor de 5 con 5 mapas, mapa 1. | La fila de `[FICTICIO] Suplente` tiene `isSubstitute: true`. |
| RF-104 | psql | `psql -h localhost -d retake_guia -c "select count(*) from roster_membership r join player p on p.id=r.player_id where p.current_gamertag='[FICTICIO] Suplente'"` | `0`: el suplente no entra en el roster. |
| RF-29 | API `/api/matches` | Mismo mapa. | El suplente tiene el `franchiseId` del equipo con el que jugó. |

## 2.5 Eventos y partidos

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-30 | API `/api/matches` | Mirar `eventName` de la gran final. | `Call of Duty League Championship 2026`. |
| RF-61 | API `/api/events` | Execute. | Nombres tal como se publican, incluido `[FICTICIO] Evento de casos límite`. |
| RF-31 | API `/api/matches` | Gran final. | `phase: "grand_final"`. |
| RF-134 | API `/api/matches` | Partido con fase `play-in` en la fuente (al mejor de 3). | `phase: null`. |
| RF-32 | API `/api/matches` | Gran final. | Dos lados con `franchiseId`. |
| RF-84 | API `/api/matches` | Partido al mejor de 7 programado. | Lado 1 con `origin: {outcome: "winner"}`, lado 2 con `"loser"`. |
| RF-33 | API `/api/matches` | Gran final. | `scheduledAt: "2026-07-19T22:00:00Z"`. |
| RF-87 | API `/api/matches` | Partido aplazado (`scheduleHistory` con 2 fechas). | `["2026-10-01T18:00:00Z", "2026-10-02T18:00:00Z"]`. |
| RF-88 | API `/api/matches` | Mismo partido. | `scheduledAt` es la última: `2026-10-02T18:00:00Z`. |
| RF-34 | API `/api/matches` | Gran final. | `bestOf: 9`. |
| RF-35 | API `/api/matches` | Recorrer la lista. | Cada partido tiene uno de `scheduled`, `live`, `finished`. |
| RF-62 | Prueba | `pytest -k nunca_retrocede -v` | Un partido finalizado no vuelve a en vivo. |
| RF-63 | Prueba | `pytest -k no_vuelve_a_en_vivo -v` | Se conserva el estado más avanzado. |
| RF-81 | API `/api/matches` | Partido aplazado. | `status: "scheduled"` con la nueva fecha. |
| RF-82 | API `/api/matches` | Partido `[FICTICIO]` en `losers_bracket` finalizado. | `status: "finished"`, `mapsWon: [3, 0]`, `winnerSide: 1`, sin mapas. |
| RF-83 | API `/api/matches` | Contar partidos. | 8: el cancelado no está. |
| RF-36 | API `/api/matches` | Partido `live`. | `mapsWon` presente. |
| RF-89 | API `/api/matches` | Partido `live`. | `mapsWon: [0, 0]` (la fuente no publicó marcador). |
| RF-91 | Prueba | `pytest -k ultimo_marcador -v` | Sin marcador nuevo, se conserva el último conocido. |
| RF-37 | Prueba | `pytest -k ultimo_marcador -v` | El marcador del mapa en curso se guarda con su modo. |
| RF-38 | API `/api/matches` | Gran final. | `mapsWon: [5, 2]`. |
| RF-39 | API `/api/matches` | Gran final. | `winnerSide: 1` (FaZe VGS). |
| RF-40 | API `/api/matches` | Mapas de la gran final. | Posición, modo, nombre, marcador y ganador de los 7 jugados. |
| RF-64 | API `/api/matches` | Partido `[FICTICIO]` con 5 mapas, mapa 2. | Una sola versión, la jugada (`6–2`); la anulada no aparece. |
| RF-92 | API `/api/matches` | Gran final, mapas 8 y 9. | Gridlock y Sake con `played: false`, sin marcador. |
| RF-95 | API `/api/matches` | Partido de fase `null`, mapa `Control`. | Solo estadísticas comunes: `zoneCaptures` y `hillTime` a `null`. |

## 2.6 Estadísticas de jugadores por mapa

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-41 | API `/api/matches` | Gran final, mapa 1. | Kills, deaths y K/D de los 8 jugadores. |
| RF-42 | API `/api/matches` | Mapa 1 (Hardpoint). | `hillTime` con valor (Dashy: 132). |
| RF-43 | API `/api/matches` | Mapa 2 (Search & Destroy). | `firstBloods`, `firstDeaths`, `plants`, `defuses` (Simp: 3, 2, 0, 2). |
| RF-44 | API `/api/matches` | Mapa 3 (Overload). | `overloads` con valor (Abuzah: 2). |
| RF-79 | API `/api/matches` | Mapa 2, Simp. | `kd: 1.33`, tal como se publica. |
| RF-45 | API `/api/matches` | Cualquier fila de la gran final. | `damage` y `assists` a `null`: la fuente no los publica. |
| RF-65 | API `/api/matches` | Mapa 2, jugador 04. | `plants: 0` (un 0 real) frente a `damage: null` (no publicado). |

## 2.7 Tabla de posiciones

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-49 | API `/api/standings` | Execute. | 14 filas con posición y puntos. |
| RF-50 | API `/api/standings` | Primera fila. | `OpTic TEX`, posición 1, 575 puntos, tal como se publican. |
| RF-75 | Prueba | `pytest -k prioridad_de_la_web_oficial -v` | En la tabla, la web oficial manda sobre BreakingPoint. |
| RF-122 | API `/api/standings` | Últimas filas. | Dos equipos en la posición 13 (compartida). |
| RF-136 | API `/api/standings` | Mirar `series`. | Equipo A `3–0`, Equipo B `0–3`, FaZe VGS `1–0`, OpTic TEX `0–1` y el resto `0–0` (C-29; los partidos contra invitados cuentan: `pytest tests/integration/api/test_004_standings.py -k invitado -v`). |
| RF-137 | API `/api/standings` | Mirar `maps`. | Equipo A `8–0` (3–0, 3–0 y 2–0), FaZe VGS `5–2`: los mapas del marcador final, los del rival como perdidos. |
| RF-138 | Prueba | `pytest tests/unit/domain/test_season_balance.py -k sin_marcador -v` | Con ganador y sin marcador cuenta la serie, no los mapas. |
| RF-138a | Prueba | `pytest tests/unit/domain/test_season_balance.py -k ni_marcador -v` | Sin ganador ni marcador no cuenta. |
| RF-139 | Prueba | `pytest tests/integration/api/test_004_standings.py -k no_esta_disponible -v` | Sin partidos de la temporada, `series` y `maps` son `null` en todas las filas. |

## 2.8 Fuentes, seguridad y correcciones

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-66 | psql | `psql -h localhost -d retake_guia -c "select source, count(*) from external_ref group by source"` | Aparecen `bp`, `wiki` y `cdl`. |
| RF-67 | Prueba | `pytest -k "prioridad or breakingpoint" -v` | BreakingPoint > Wiki > web oficial en cada campo. |
| RF-129 | API `/api/players` | Buscar el gamertag con `<img`. | Llega literal, como texto: `[FICTICIO] <img src=x onerror="alert(1)">`. |
| RF-130 | API `/api/franchises` | Buscar `[FICTICIO] Equipo B`. | `logoUrl: null` (la fuente publicó `javascript:`). |
| RF-96 | API `/api/matches` | Partido `[FICTICIO]` con 5 mapas, mapa 1. | `score: [250, 185]`: el valor corregido. |
| RF-97 | API `/api/matches` | Mismo mapa. | `correctedFields: ["score_2"]`. |
| RF-98 | API `/api/matches` | Gran final. | `correctedFields: []` en todo: la primera llegada no es corrección. |
| RF-101 | Prueba | `pytest tests/unit/domain/test_validation.py -v` | Negativos, porcentaje fuera de 0–100 y mapas ganados imposibles no son válidos. |
| RF-100 | API `/api/matches` | Partido `[FICTICIO]` con 5 mapas, mapa 2, `[FICTICIO] A1`. | `kills: null` (se publicó −3) y `deaths: 5` se conserva. |

## 2.9 Reglas comunes de presentación (consola del navegador)

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-125 | Consola | `rules.formatRole('SMG', t)` y `rules.formatPlace({place:'DQ', isDq:true}, t)` | `SMG` y `DQ` también con `tEn`. |
| RF-126 | Consola | `rules.leagueText(tEn, 'freeAgent')` | `Free agent` (en español, `Agente libre`). |
| RF-8 | Consola | `rules.formatPlace({place:'9-12', isDq:false}, t)` | `9-12`. |
| RF-9 | Consola | `rules.formatPlace({place:'DQ', isDq:true}, t)` | `DQ`. |
| RF-69 | Consola | `rules.formatRosterGamertag({gamertagAtFinal:'Simplicity', currentGamertag:'Simp'})` | `['Simplicity', 'Simp']`. |
| RF-112 | Consola | `rules.formatRosterGamertag({gamertagAtFinal:'Simp', currentGamertag:'Simp'})` | `['Simp']`. |
| RF-120 | Consola | `rules.formatHistoryField(null, t)` | `No disponible`. |
| RF-14 | Consola | `rules.resolveTeamBadge({logoUrl:null, validFrom:'2020'}, [{logoUrl:'https://x.test/a.png', validFrom:'2026'}])` | `{kind: 'logo', src: 'https://x.test/a.png'}`. |
| RF-15 | Consola | `api.getFranchises().then(f => f.find(x => x.identities.at(-1).shortName.includes('Nombre Nuevo'))).then(f => rules.resolveTeamBadge(f.identities.at(-1), f.identities))` | Abreviatura `FNN` sobre `#5b2c83`, aunque la identidad antigua tiene logo. |
| RF-118 | Consola | `rules.resolveTeamBadge({shortName:'X', abbreviation:'X', logoUrl:null, primaryColor:null, validFrom:'2026'}, [])` | `background: '#3a4252'` (color neutro). |
| RF-127 | Consola | `rules.bestTextColor('#f5d90a')` y `rules.bestTextColor('#3a4252')` | `#000000` y `#ffffff`. |
| RF-128 | Prueba | `npx vitest run src/league -t "nunca por debajo"` | Con 1000 colores al azar, el contraste nunca baja de 4,5:1. |
| RF-68 | Consola | `rules.currentGamertag({currentGamertag:'Simp'})` | `Simp`. |
| RF-23 | Consola | `rules.formatAge({min:25, max:25}, t)` | `25` (edad en UTC calculada en el servidor). |
| RF-108 | Consola | `rules.formatAge({min:22, max:23}, t)` | `22–23`. |
| RF-24 | API `/api/players` | Buscar "birth" en la respuesta (⌘F). | No aparece: ni fecha ni año de nacimiento. |
| RF-25 | Consola | `rules.formatPersonalField(null, t)` | `No disponible`. |
| RF-71 | Consola | `rules.formatRole(null, t)` | `Sin rol`. |
| RF-107 | Consola | `rules.formatTeam({isFreeAgent:true}, null, t)` | `Agente libre`. |
| RF-70 | Consola | `rules.formatMatchDateTime('2026-07-19T22:00:00Z', 'es')` | Fecha y hora en la zona de tu equipo (Ciudad de México: `19 de julio de 2026 a las 16:00`). |
| RF-85 | Consola | `rules.formatSlot({identity:null, origin:{matchId:'m', outcome:'winner'}}, t, () => 'la final de ganadores')` | `Ganador de la final de ganadores`. |
| RF-86 | Consola | `rules.formatSlot({identity:null, origin:null}, t, () => '')` | `Por definir`. |
| RF-90 | Consola | `rules.formatLiveMapScore({mode:null, score:null}, t)` | `No disponible`. |
| RF-94 | Consola | `api.getMatches().then(m => rules.displayMaps(m.find(x => x.bestOf === 9).maps, t).slice(7))` | Gridlock y Sake con `notPlayedLabel: 'No jugado'` y sin `scoreText`. |
| RF-99 | Consola | `rules.isCorrected({correctedFields:['score_2']}, 'score_2')` y `rules.leagueText(t, 'corrected')` | `true` y `Corregido`. |
| RF-46 | Consola | `rules.formatStat(null, t)` y `rules.formatStat(0, t)` | `No disponible` y `0`. |
| RF-47 | Consola | `api.getMatches().then(m => m.filter(rules.needsStatsPendingNotice).map(x => x.phase))` | `['winners_bracket']`: el partido ficticio con un jugador sin estadísticas. |
| RF-72 | Consola | Misma orden. | La gran final no sale, aunque no tiene `damage` ni `assists`. |
| RF-48 | Prueba | `npx vitest run src/league -t "pendientes"` | Cuando llegan todas las estadísticas, el aviso deja de salir. |
| RF-135 | Consola | `rules.formatPhase(null, t)` y `rules.formatPhase('grand_final', t)` | `No disponible` y `gran final`. |
| RF-51 | Consola | `rules.isStandingsAvailable([])` y `rules.standingsUnavailableText(t)` | `false` y `La tabla de posiciones todavía no está disponible`. |

---

## Checklist de seguridad (plan §5, T-070)

| Vector | Comprobación | Resultado (2026-09-22) |
|---|---|---|
| Inyección SQL | `grep -rnE "text\(|exec_driver_sql" backend/app` | Solo consultas fijas (`SELECT 1`, `SHOW server_version_num`) y valores por defecto; todo lo demás pasa por SQLAlchemy con parámetros. |
| XSS | `grep -rnE "dangerouslySetInnerHTML|innerHTML" src` | Ninguno. El gamertag con HTML llega literal (RF-129). |
| Logos | `backend/app/domain/validation.py` | Solo `https` con extensión de imagen (RF-130). |
| Credenciales | `git check-ignore -v backend/.env` | `backend/.env` ignorado; `.env.example` sin secretos. |
| Datos ficticios en producción | `load-fixtures` con `APP_ENV=production` | Se niega (prueba `test_en_produccion_se_niega...`). |
| Privacidad | `/api/players` | Ni fecha ni año de nacimiento (prueba que recorre todas las claves). |
| Curación | `backend/curation/curation.yaml` y `fixtures.yaml` (I-35 de la 003) | Solo referencias, motivos, roles y nombres de país; ningún dato personal (revisado de nuevo el 2026-09-24 con la curación real). |
