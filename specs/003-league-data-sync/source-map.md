# Mapa de datos de las fuentes (fase F0)

- **Spec**: [`spec.md`](spec.md) · **Plan**: [`plan.md`](plan.md) · **Tareas**: T-001 a T-007 de [`tasks.md`](tasks.md)
- **Fecha de la exploración**: `2026-09-23` (temporada 2026 terminada; la 2027 aún no está publicada)
- **Estado**: decisiones tomadas por Hugo el 2026-09-23 (§5). Fase F0 lista para cerrar (T-007).

Documento de trabajo de la fase F0: dónde está cada dato de la spec 002 en cada fuente, cómo se accede, qué falta y qué hay que decidir antes de escribir los conectores. Todas las consultas se hicieron identificadas como Retake, sin hacerse pasar por un navegador. La pausa fue de 2 s como mínimo, y de 20–25 s en la Wiki tras su aviso de límite. En total: unas 16 consultas a BreakingPoint, unas 32 a la Wiki y 6 a la CDL.

---

## 1. Acceso a cada fuente

| Fuente | Vía | Qué se ha comprobado | Observaciones |
|---|---|---|---|
| **BreakingPoint.gg** | **API interna JSON (tRPC)**: `/api/trpc/cached.matches.fetchMatchesPage`, `matches.fetchEventIdsWithCompletedMatches` y `cached.matches.fetchMatchPageMatch`; en el JSON incrustado de cada partido, `matches.fetchGameBans` (mapas previstos de la serie) y `mapPicks.fetchMapPicksAndVetoes` (vetos). **JSON incrustado** (`__NEXT_DATA__`) en `/matches`, `/match/{id}`, `/teams/{id}` y `/players/{id}`. | 200 identificado como Retake, con httpx y con curl. La API pagina con `nextCursor` y filtra por temporada, evento y estado (`completed`, `upcoming_live`). | Es la API que usa la propia web. No está documentada y puede cambiar sin aviso. Sin límites de frecuencia visibles. |
| **Wiki (Fandom)** | **API de MediaWiki**: `action=parse` (HTML de una página, como en `CDL-data-analysis`) y consultas estructuradas (`action=cargoquery`). 70 tablas; útiles: `Tournaments`, `MatchSchedule`, `TournamentResults`, `TournamentPlayers`, `Players`, `PlayerRedirects`, `PlayerRenames`, `Teams`, `TeamRedirects`, `Standings`. | **Cloudflare rechaza (403) las peticiones de httpx**; con **requests** (como `CDL-data-analysis`) y la identificación de Retake, `action=parse` responde 200. **Límite de consultas muy estricto:** con 20–25 s entre consultas, 3 de 9 fueron rechazadas con `ratelimited`. | Ver huecos H-1 y H-2. El HTML de las páginas sigue tapado por Cloudflare (403). |
| **Web oficial de la CDL** *(en reserva, decisión H-7)* | **Archivo JSON** de la tabla en el servidor de contenidos: `assets.blz-contentstack.com/…/2026-regular-standings.json`. | 200 con httpx y con curl. | **La dirección cambia con cada versión** del archivo. Solo se descubre desde el CMS de la página (`cdl-other-services…/content-types/tab/…`), que respondió **503 de forma intermitente** incluso desde el navegador. La página no incluye la dirección en su HTML. Ver hueco H-7. |

---

## 2. Dato de la 002 → fuente

Leyenda: ✅ lo publica en una vía comprobada · ⚠️ lo publica con limitaciones · ❌ no lo publica · — no aplica.

| Registro (`kind`) | BreakingPoint | Wiki | CDL |
|---|---|---|---|
| `season` (año, nombre) | ✅ `allSeasons`: `year`, fechas y juego (`title.name`, `name_short`). La 2027 aún no aparece. | ✅ `Tournaments.Year` | — |
| `event` (nombre publicado) | ✅ `allEvents` y `event` de cada partido (`name`, `tier`, `qualifier_event_id`, fechas). Mezcla la CDL con Challengers (CDC) y eventos externos (Esports World Cup): hay que filtrar los eventos de la CDL. | ✅ `Tournaments` (`Name`, `OverviewPage`, fechas) | — |
| Fase | ⚠️ `round.bracket_side`: `winners` → winners bracket, `elimination` → losers bracket, `grand_final` → gran final. **Los partidos de clasificatorio solo dicen "Major Qualifier", sin semana.** | ⚠️ `MatchSchedule.Tab` = "Week N" en los clasificatorios, pero sus partidos no se pueden enlazar con los de BreakingPoint (H-5). | — |
| `franchise` e `identity` (nombre corto, abreviatura, logo, colores) | ✅ `allTeams` / `team1`/`team2`: `name`, `name_short`, logos (webp y png) y `color_hex` (primario). El equipo de cada partido va con el nombre y logo **de ese evento** (`team1.event_id`), útil para RF-12 de la 002. ❌ Color secundario. | ⚠️ `Teams` (`Short`, `Image`): los logos de Fandom no son CC BY-SA (plan D-14). | ⚠️ `teamCard`: `name`, `abbreviation`, logos. |
| `player` (gamertag, nombre real, país, nacimiento, retirado) | ✅ `tag`, `first_name`, `last_name`, `date_of_birth`, `retired`. ⚠️ País solo como `country_id` numérico, sin la tabla de países (H-6). ❌ Gamertags anteriores. | ✅ `Players` (`Name`, `Country` en inglés, `Birthdate`, `IsRetired`); `PlayerRedirects` y `PlayerRenames` para los gamertags anteriores (RF-17 de la 002). | — |
| `roster` (franquicia, jugador, desde, hasta) | ✅ `teamHistory` de la ficha del jugador (`team_id`, `start_date`, `end_date`). La ficha de equipo mezcla jugadores actuales y retirados con el mismo `current_team_id`: se distinguen con `retired`. | ⚠️ `TournamentPlayers` por torneo (sin fechas). | — |
| `match` (evento, fase, formato, estado, horario, lados, marcador, ganador, origen) | ✅ API tRPC: `datetime`, `best_of`, `status` (`complete`…), `team_1_score`/`team_2_score`, `winner_id`, `winner_next_match_id` / `loser_next_match_id` (origen del bracket, RF-84 de la 002), `is_tiebreaker`. ⚠️ Marcador **en vivo** sin comprobar fuera de temporada (H-9). | ⚠️ `MatchSchedule` sin identificadores de BreakingPoint (H-4). | ❌ Sin comprobar fuera de temporada (H-9). |
| `match_map` (posición, modo, mapa, marcador, ganador) | ✅ `games`: `game_num`, `modes.name`, `maps.name`, marcadores y `winner_id`. ✅ **Mapas no jugados**: `matches.fetchGameBans` da los mapas previstos (`map_number`, `map_id`, `mode_id`); los que no aparecen en `games` no se jugaron (H-8). | ❌ `MatchScheduleGame` vacía en 2026. | — |
| `player_map_stats` | ✅ Las 13 de la 002: `kills`, `deaths`, `damage`, `assists`; HP: `hill_time`, `contested_hill_time`; S&D: `first_blood_count`, `first_death_count`, `plant_count`, `defuse_count`; Overload: `zone_capture_count`, `overloads`. ❌ **K/D** (H-3). | ❌ `ScoreboardPlayers` vacía en 2026. | — |
| `standing` (posición, puntos CDL) | ✅ Ficha de equipo: `standings.rank` y `points` de la temporada. | ✅ `Standings` (`Place`, `Points`). | ✅ `rank`, `cdlPoints` (fuente principal, RF-75 de la 002). |
| `championship` y `placement` (historial) | ⚠️ Eventos desde 2013 con `prizepool`, sin clasificación final comprobada. | ✅ `action=parse` de la página de cada campeonato: tabla `tournament-results` con lugar, premio, **porcentaje de la bolsa**, equipo y roster (comprobado con el Champs 2026). ✅ `TournamentResults` con lugar, premio y fecha. | — |

---

## 3. Enlaces entre fuentes y retenidos estimados (T-004)

**Ninguna fuente publica identificadores de las otras.** No hay `same_as` para ningún tipo, y según RF-54 de la spec los registros solo se unen por un enlace de la fuente o a mano. Si se consultara todo de las tres fuentes, quedaría retenido esto por temporada:

| Tipo | Fuente de mayor prioridad | Retenidos de las demás | Uniones a mano necesarias |
|---|---|---|---|
| Franquicias | BreakingPoint | 12 de la Wiki + 12 de la CDL | ~24 por temporada (casi estables de una temporada a otra) |
| Jugadores | BreakingPoint | ~50 de la Wiki | ~50 por temporada |
| Eventos | BreakingPoint | ~12 de la Wiki | ~12 |
| Partidos | BreakingPoint | ~300 de la Wiki | ~300 (inasumible) |

La tabla de la CDL es la fuente principal de posiciones (RF-75 de la 002). Sus filas apuntan a franquicias de la CDL: sin las 12 uniones de franquicias CDL–BreakingPoint, la tabla oficial quedaría retenida.

---

## 4. Muestras guardadas (T-005)

En `backend/tests/snapshots/`, recortadas a los campos usados y con fuente, dirección y fecha:

| Archivo | Contenido |
|---|---|
| `bp/matches_page.json` | Temporada, 2 equipos, eventos de ejemplo y listas de partidos (vacías en vivo y próximos, fuera de temporada). |
| `bp/trpc_matches_page.json` | 2 partidos del Major 1 por la API interna, con ronda, evento y equipos. |
| `bp/match_detail.json` | Gran final del Major 1: 3 mapas con 2 jugadores cada uno. |
| `bp/match_series_maps.json` | Partido 0-3 al mejor de 5: mapas jugados y mapas previstos de `fetchGameBans` (dos no jugados). |
| `bp/player_page.json` | Datos personales publicados e historial de equipos (sin redes ni fotos). |
| `cdl/regular_standings.json` | 3 filas de la tabla oficial de 2026. |
| `wiki/championship_parse.json` | Tabla `tournament-results` del Champs 2026 vía `action=parse`: cabecera y dos filas, con porcentaje y roster. |
| `wiki/tournament_results.json` | 2 puestos del Champs 2026 con premio. |
| `wiki/players.json` | Datos personales de un jugador. |
| `wiki/standings.json` | 2 filas de la tabla de 2026. |
| `wiki/match_schedule.json` | 2 partidos de un clasificatorio con su semana. |

**Huecos de muestra:** no hay muestra de partido **en vivo** ni de **próxima temporada**, porque no existen fuera de temporada. Tampoco de `PlayerRedirects`, que la Wiki rechazó por su límite de consultas: se tomará en F3 con la pausa de H-2.

---

## 5. Huecos y decisiones (T-006, regla P-1)

Decididos por Hugo el 2026-09-23:

| # | Hueco | Requisitos afectados | Decisión de Hugo |
|---|---|---|---|
| H-1 | La Wiki rechaza httpx en Cloudflare; responde a `requests` con `action=parse`. No se esquiva ninguna protección: si un día rechaza también `requests`, se respeta y se vuelve a Hugo. El volcado oficial es de julio de 2022 y no se descarga. | RF-1, RF-4, RF-34, RF-38; H-1 del plan | **`requests` para la Wiki** (con `action=parse` y BeautifulSoup, como en `CDL-data-analysis`); httpx para BreakingPoint. Sin volcado. |
| H-2 | Límite de consultas de la Wiki. | RF-39, RF-40; plan §1.2 | **10 s entre consultas a la Wiki** y, si responde `ratelimited`, espera creciente (20, 40, 80 s… hasta 10 min) con incidencia anotada. BreakingPoint sigue con 2 s. |
| H-3 | Nadie publica el K/D. | RF-79 de la 002 | **Se calcula kills ÷ deaths con 2 decimales** si ninguna fuente lo publica; con 0 deaths, K/D = kills; si falta alguno, ausente. Cambio **C-12** de la 002, aprobado. |
| H-4 | Sin enlaces entre fuentes. | RF-54 a RF-56 | **Temporada actual de BreakingPoint; historial de la Wiki**; la Wiki también para los jugadores (H-11). Sin partidos, eventos ni rosters de la Wiki. |
| H-5 | La semana de los clasificatorios. | RF-31 de la 002 | **Se calcula:** orden de la semana (lunes a domingo, hora de Ciudad de México) entre las semanas con partidos del evento. Comprobado con los 42 partidos del clasificatorio del Major 1. Cambio **C-13** de la 002, aprobado. |
| H-6 | País solo como número en BreakingPoint; su tabla está en su base de datos (clave interna, no se usa). | RF-22, RF-110 de la 002 | **Tabla de países en `curation.yaml`** (número de BreakingPoint → nombre), rellenada a mano; un número sin traducir es `No disponible` y se anota como incidencia. |
| H-7 | JSON de la tabla de la CDL con dirección variable y CMS que falla. | RF-75 de la 002 | **Tabla solo de BreakingPoint.** La web de la CDL queda **en reserva**: sigue siendo fuente en las specs, pero sin conector hasta que haga falta (por ejemplo, marcadores en vivo en 2027). **Mientras tanto, RF-75 de la 002 queda incumplido** (manda BreakingPoint, no la web oficial) y se anota en el plan. |
| H-8 | Mapas no jugados. | RF-92, RF-94 de la 002 | **Resuelto:** BreakingPoint los publica en `matches.fetchGameBans` (encontrado gracias a Hugo). |
| H-9 | En vivo y próxima temporada sin comprobar fuera de temporada. | RF-14, RF-16, RF-17, RF-57 | **Construir con la estructura conocida** (misma API, otro estado) y la fuente simulada; repetir la exploración del en vivo en cuanto empiece la temporada 2027 (dentro de T-089). |
| H-10 | Porcentaje de la bolsa. | RF-5, RF-57 de la 002 | **Resuelto** con `action=parse` (H-1). |
| H-11 | BreakingPoint no publica gamertags anteriores. | RF-17 de la 002 | **Consultar la Wiki** (`PlayerRedirects` y `Players`) para los jugadores actuales. Obliga a unir a mano los jugadores de la Wiki con los de BreakingPoint (~50 por temporada). |

### 5.1 Consecuencias para las uniones a mano (RF-54 a RF-56)

Con estas decisiones, las uniones necesarias por temporada son:

- **Jugadores Wiki ↔ BreakingPoint:** unos 50 (H-11), casi estables de una temporada a otra.
- **Franquicias y jugadores del historial que siguen en la liga:** unos 12 y 30, una sola vez.
- **Ningún partido ni evento.**
