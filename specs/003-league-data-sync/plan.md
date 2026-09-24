# Plan: Obtención y Actualización de los Datos de la Liga

- **Spec**: [`003-league-data-sync/spec.md`](spec.md) (`Aprobado`, 2026-09-23, con la revisión R-1)
- **Fecha**: `2026-09-23`
- **Estado**: `Aprobado` (aprobado por Hugo el 2026-09-23)

Este documento describe **CÓMO** se construirá la spec 003. No contiene código: define módulos, contratos de datos, decisiones y fases. Cada parte indica qué requisitos (RF) cubre.

> **Nombres:** las decisiones que ha tomado Hugo se llaman **H-1 a H-9**, para no confundirlas con las reglas de proceso P-1 y P-2 de la spec. En la conversación se preguntaron como P-1 a P-9.

---

## 0. Resumen

- **Qué se construye:**
  - **Conectores** para las tres fuentes: traducen lo que publica cada una a los registros de fuente (`SourceRecord`) que la 002 ya sabe ingerir.
  - Un **proceso de obtención** aparte (`retake sync`) con su propio planificador.
  - Las **reglas nuevas** de la 003 en la ingesta.
  - Un canal de **eventos del servidor** para que las páginas abiertas se actualicen solas.
  - La **página de administración** con su acceso.
  - En el frontend: el **pie** con el año calculado y la atribución de las fuentes, el soporte de actualización automática para las specs visuales y la página de administración.
- **Idea central:** la 003 **no toca las reglas de la 002**, las alimenta. Cada consulta produce registros de fuente que entran por el mismo `ingest_records`, y los datos que antes eran manuales pasan a ser automáticos (D-1).
- **Revisión de las condiciones de uso (regla P-2), hecha el 2026-09-23** (detalle en §1): las tres fuentes exigen permiso por escrito para el acceso automático. Hugo decidió seguir sin él, con la API donde exista y leyendo las páginas públicas donde no, como en `CDL-data-analysis`. Es la **revisión R-1** de la spec (RF-36 cambia y se añade la atribución, RF-160), ya aplicada. El cambio **C-11** en la 001 está aprobado y aplicado.
- **Herramientas nuevas elegidas por Hugo** (constitución §3.2, detalle en §8.2): httpx (H-1; **requests para la Wiki** tras F0, I-1), BeautifulSoup (H-2), petición interna de la CDL con navegador sin interfaz como plan B (H-3; **CDL en reserva** tras F0, I-4), proceso aparte (H-4), bucle propio con reloj inyectable (H-5), eventos del servidor (SSE, H-6), Argon2id con argon2-cffi (H-7), sesión en servidor con cookie HttpOnly (H-8) y Pillow con copia de los logos en PostgreSQL (H-9).
- **Primera fase = exploración de las fuentes (F0):** hay datos cuya ubicación exacta todavía no se conoce (la tabla de la CDL, las fichas de jugadores de BreakingPoint, los enlaces entre fuentes). F0 los localiza antes de escribir los conectores. Si algo impide cumplir un requisito, se aplica la regla P-1 y se vuelve a Hugo.

---

## 1. Revisión de las fuentes (regla P-2)

### 1.1 Condiciones de uso (consultadas el 2026-09-23)

| Fuente | Qué dicen | Consecuencia |
|---|---|---|
| **BreakingPoint.gg** | *Terms*: es dueño de todo el contenido y "All use requires our written consent". *EULA*: licencia personal y no comercial, sin distribuir. Su "API" no es pública: se pide por correo (`contact@breakingpoint.gg`). | Acceso sin permiso por decisión de Hugo (R-1). |
| **Wiki (Fandom)** | Prohíbe "any robot, spider, scraper or other automated means… without our express written permission". El **texto** de la Wiki está bajo CC BY-SA 3.0; las **imágenes** no tienen por qué estarlo. | Acceso sin permiso por decisión de Hugo (R-1). Atribución en el pie (RF-160). Los logos se toman de BreakingPoint siempre que se pueda (D-14). |
| **Web oficial de la CDL** | Condiciones de Activision: no reproducir ni distribuir "any part of the Product except as expressly authorized". La página de condiciones propia de la CDL no mostró texto al consultarla. | Acceso sin permiso por decisión de Hugo (R-1). |

### 1.2 Normas para programas automáticos y acceso

| Fuente | Normas para robots | Acceso comprobado | Qué ofrece |
|---|---|---|---|
| BreakingPoint.gg | No publica `robots.txt` (404). | 200, identificado como Retake. | `/matches` trae en su JSON incrustado (`__NEXT_DATA__`) las temporadas, los 12 equipos con sus logos, los eventos y las listas de partidos en vivo, próximos y terminados. `/match/{id}` trae un partido con sus mapas, modos, marcadores y estadísticas por jugador. |
| Wiki (Fandom) | `robots.txt` tapado por Cloudflare (403). | La API (`api.php`) responde 200. | Consultas estructuradas en JSON (`action=cargoquery`): comprobadas `Tournaments` y `MatchSchedule` con los datos de 2026. Se estudiarán en F0 las de resultados, jugadores y rosters. |
| Web oficial de la CDL | No publica `robots.txt` (404). | 200. | La página de posiciones no trae la tabla en su HTML: la carga con JavaScript desde una dirección que hay que localizar en F0 (H-3). |

**Pausa mínima entre dos consultas a la misma fuente (RF-39): 2 segundos** en BreakingPoint y la CDL; **10 segundos en la Wiki**, con espera creciente si responde `ratelimited` (ajuste I-2 tras F0). Es algo más prudente que los 1,5 s de `CDL-data-analysis`, y cabe de sobra en el ciclo de 60 s: en vivo, unas 3 consultas por minuto a BreakingPoint (§5). A la API de la Wiki se le añade además el parámetro de cortesía de MediaWiki que la frena si el servidor va cargado (D-15).

**Identificación (RF-37):** `Retake/<versión> (+https://github.com/HugoAI23/retake_maqueta)`.

---

## 2. Módulos

Los nombres de carpetas, archivos, tablas, campos y rutas van en inglés (constitución §7.1).

```
backend/app/
├── sources/             NUEVO: una fuente = un conector
│   ├── http.py          Cliente educado (httpx; requests para la Wiki): identificación, pausa por fuente, tiempos de espera
│   ├── bp.py            BreakingPoint: API interna JSON (tRPC) y JSON incrustado de partidos, equipos y jugadores
│   ├── wiki.py          Wiki (con requests): historial con action=parse y jugadores con consultas estructuradas
│   ├── cdl.py           Web de la CDL: EN RESERVA tras F0 (I-4), sin conector por ahora
│   └── simulated.py     Fuente simulada para desarrollo y pruebas (§6.4)
├── sync/                NUEVO: proceso de obtención (H-4, H-5)
│   ├── planner.py       Función pura: qué consultas tocan ahora (§5)
│   ├── runner.py        Ejecuta una consulta: conector → ingesta → registro → aviso de cambios
│   ├── worker.py        Bucle del proceso `retake sync`, con una cola por fuente
│   ├── registry.py      Registro de actualizaciones, incidencias y resumen diario
│   └── notify.py        Aviso de cambios a la API (PostgreSQL LISTEN/NOTIFY, D-6)
├── logos/               NUEVO: descarga, validación con Pillow y copia (H-9)
├── admin/               NUEVO: cuenta, contraseñas, sesiones, bloqueo por origen (H-7, H-8)
├── domain/              + reglas nuevas de la 003 (§2.1)
├── ingest/              + cambios de §2.3
├── curation/            + uniones de partidos, eventos y franquicias, y confirmación de nuevos
├── api/                 + frescura, logos, eventos del servidor y rutas de administración
└── cli.py               + sync, sync-once, set-admin-password, source-mode, list-retained

src/
├── live/                NUEVO: actualización automática para las specs visuales
├── admin/               NUEVO: página de administración
└── layout/SiteFooter    Año desde la API y atribución de las fuentes
```

### 2.1 `backend/app/domain/` — reglas nuevas (funciones puras)

| Pieza | Responsabilidad | RF |
|---|---|---|
| `live_score` | Elige entre los marcadores en vivo de todas las fuentes el más avanzado: más mapas terminados y, si empatan, más puntos sumados en el mapa en curso. Nunca devuelve uno menos avanzado que el registrado. | RF-57 a RF-59 |
| `cancellation` | Decide si se aplica una cancelación: solo si la publica la fuente de mayor prioridad entre las que publican el partido. | RF-53 |
| `identity_merge` | Combina campo a campo las identidades que publican las fuentes para una franquicia, incluida la fecha de vigencia, e indica si el resultado combinado cambió. Sustituye el comportamiento del ajuste I-15 de la 002. | RF-61 a RF-63 |
| `review_windows` | Dice si un partido `finalizado` debe revisarse: mientras tenga estadísticas pendientes y 7 días más. | RF-19 a RF-21 |
| `disappearance` | Dice si un partido está desaparecido (24 h sin aparecer en ninguna consulta con éxito de las fuentes que lo publicaban) o si un partido en vivo lleva más de 60 s sin aparecer. | RF-50, RF-90 |
| `freshness` | Umbrales de desactualización (60 s en vivo, 1 h el resto) y cálculo de "sin actualizar" de un conjunto de datos a partir de la última consulta con éxito. | RF-89 |
| `live_priority` | Elige el partido prioritario cuando no caben todos los partidos en vivo en 60 s. | RF-23 a RF-26 |

### 2.2 `backend/app/sources/` — conectores

| Pieza | Responsabilidad | RF |
|---|---|---|
| `http` | Un cliente por fuente (httpx para BreakingPoint; requests para la Wiki, I-1) con identificación de Retake, pausa mínima por fuente (2 s; Wiki 10 s con espera creciente, I-2), tiempo de espera de 15 s y lectura de las normas para robots si la fuente las publica. Nunca se hace pasar por un navegador. | RF-35, RF-37, RF-39 a RF-42 |
| `bp` | API interna (`fetchMatchesPage`, paginada, y `fetchEventIdsWithCompletedMatches`): partidos de la temporada con estado, horario, formato, marcador, ronda (fase) y origen del bracket. `/matches`: temporadas, eventos (solo los de la CDL) y franquicias con identidad y logo. `/match/{id}`: mapas, marcadores, estadísticas por jugador y modo, y mapas previstos de la serie (`fetchGameBans`, para los no jugados). `/teams/{id}`: tabla (puesto y puntos). `/players/{id}`: datos personales, `country_id` e historial de equipos (rosters). | RF-1, RF-14, RF-16 a RF-20 |
| `wiki` | Con `requests` (I-1). Historial: `action=parse` de la página de cada campeonato (tabla `tournament-results`: lugar, premio, porcentaje, equipo y roster), como en `CDL-data-analysis`. Jugadores: `Players` y `PlayerRedirects` (datos personales y gamertags anteriores, I-3). Sin partidos ni eventos de la temporada (I-3). | RF-1, RF-4, RF-30 a RF-34, RF-38 |
| `cdl` | **En reserva** tras F0 (I-4): sin conector. Se retomará si hace falta (por ejemplo, marcadores en vivo en 2027). | — |
| `simulated` | Responde como las fuentes reales a partir de escenarios de desarrollo (§6.4). Nunca se activa en producción. | RF-10, RF-11 |

Cada conector sigue el contrato de §3.1. **Lo que no entiende no lo inventa:** omite el campo, lo marca como ilegible (D-8) y lo informa como dato rechazado.

### 2.3 Cambios en `backend/app/ingest/`

| Cambio | RF |
|---|---|
| Las identidades se combinan campo a campo con `identity_merge`: solo nace una identidad nueva si cambia el resultado combinado. | RF-61 a RF-64 |
| Mientras un partido está en vivo, el marcador sale de `live_score`, no de la prioridad de fuentes. | RF-57 a RF-59 |
| Una cancelación solo se aplica según `cancellation`; si no, se anota la discrepancia. | RF-53, RF-146 |
| Registros retenidos: una referencia sin enlazar, de una fuente con menos prioridad que otra que publica ese tipo, queda retenida y no participa en ninguna entidad visible hasta que la curación la una o la confirme como nueva. | RF-54 a RF-56 |
| Un dato ilegible deja de contar para esa fuente. Si ninguna fuente lo publica de forma legible, se conserva el valor registrado, a diferencia de un valor imposible, que pasa a ausente (D-8). | RF-48, RF-49 |
| Un jugador con los datos personales retirados nunca vuelve a recibirlos de las fuentes: el cálculo del jugador los ignora. | RF-60 |
| Cada fila guarda `changed_at`, el instante en que cambió su valor resuelto, y se anotan los conjuntos de datos que cambiaron para avisar a la API. | RF-157 a RF-159 |
| Cada referencia guarda `last_seen_at`, la última consulta con éxito que la incluyó, para detectar desapariciones y reapariciones. | RF-50 a RF-52 |

### 2.4 `backend/app/sync/` — proceso de obtención

| Pieza | Responsabilidad | RF |
|---|---|---|
| `planner` | Función pura: con el estado guardado y la hora, devuelve las consultas que tocan (§5). | RF-3 a RF-6, RF-14, RF-16 a RF-34 |
| `runner` | Ejecuta una consulta: conector → `ingest_records` → curación → registro → aviso de cambios. Una respuesta vacía donde antes había datos cuenta como fallo. | RF-22, RF-43 a RF-47, RF-140 a RF-146 |
| `worker` | Bucle de `retake sync`: cada 5 s pregunta al planificador, reparte las consultas en una cola por fuente (así la pausa de una no frena a las demás) y recoge las peticiones del administrador. | RF-16, RF-23, RF-100, RF-102, RF-107, RF-108 |
| `registry` | Registro de consultas, incidencias sin repeticiones, resumen diario a las 00:00 de Ciudad de México y borrado a los 7 días. | RF-140 a RF-154 |
| `notify` | Tras cada ingesta con cambios, avisa a la API por `NOTIFY` con los conjuntos de datos cambiados. | RF-79 a RF-81 |

### 2.5 API: rutas nuevas y ampliadas

| Ruta | Devuelve | RF |
|---|---|---|
| Todas las de la 002 | Cada fila añade `changedAt`, y cada partido añade `isStale` (en vivo sin aparecer en las fuentes, RF-90). Siguen filtrando por la temporada actual, así que la próxima nunca se ve. | RF-15, RF-90, RF-157 |
| `GET /api/freshness` | Por cada conjunto de datos (`live`, `matches`, `standings`, `franchises`, `players`, `events`, `championships`, `season`): `lastChangedAt` y `stale`. | RF-89, RF-155, RF-158 |
| `GET /api/stream` | Canal de eventos del servidor (§3.3). | RF-79 a RF-81, RF-89 |
| `GET /api/logos/{id}` | La copia propia de un logo, con su tipo de imagen y caché larga. | RF-65 a RF-71 |
| `/api/admin/...` | Acceso y funciones de administración (§3.4). | RF-97 a RF-139 |

### 2.6 Frontend

| Pieza | Responsabilidad | RF |
|---|---|---|
| `src/live/liveChannel` | Una sola conexión de eventos del servidor por pestaña. Se cierra cuando la pestaña se oculta y se reabre al volver. Detecta el corte (sin latido en 45 s). | RF-79, RF-82, RF-89 |
| `src/live/useLiveBlock` | Amplía el cargador de bloques de la 001: la primera carga usa sus reglas (esqueleto, error, "Reintentar"). Después, recarga en silencio los datos cuando el canal avisa, sin esqueleto; si falla, conserva los datos; al volver a verse la pestaña, recarga en 5 s como máximo. | RF-79 a RF-88 |
| `src/live/freshnessRules` | Funciones puras: `lastUpdatedOf` (el `changedAt` más reciente de lo que se muestra, o el del conjunto si no hay nada), `isStale` (el servidor dice "sin actualizar" o el canal lleva cortado más que el umbral) y `formatLastUpdated`. | RF-89, RF-92, RF-155 a RF-159 |
| `src/live/LiveAnnouncer` | Región accesible que anuncia sin interrumpir los cambios de datos en vivo, y solo esos. | RF-94 a RF-96 |
| `src/layout/SiteFooter` | Año desde `/api/season/current`: sin año hasta obtenerlo, y lo mantiene si luego falla. Atribución de las tres fuentes con enlace. Se elimina el valor provisional de `src/config/season.js`. | RF-74 a RF-78, RF-160 |
| `src/admin/` | Página `/admin` (fuera del menú, dentro del marco común): acceso, estado de las fuentes, peticiones con su resultado, registro y resúmenes. Cada parte es un bloque de la 001. | RF-97 a RF-139 |

Igual que en la 002 (D-12), la 003 **no diseña** cómo se ve la hora de actualización ni el aviso de datos sin actualizar en los bloques de la liga. Da las funciones y el cargador, y cada spec visual decide el aspecto. La única excepción es la página de administración, que se construye aquí con los componentes y la paleta de la 001.

---

## 3. Contratos

### 3.1 Conector → proceso de obtención

Cada consulta devuelve un **resultado de consulta**:

| Campo | Descripción |
|---|---|
| `source`, `job` | Fuente y tipo de consulta (§5). |
| `outcome` | `success`, `partial` (hubo datos rechazados), `failure` o `forbidden` (las normas la prohíben). |
| `records` | Lista de `SourceRecord` (contrato de la 002, §2.1). |
| `seen` | Referencias que la respuesta incluía, para `last_seen_at` y las desapariciones. |
| `rejected` | Datos no entendidos: referencia, campo, valor recortado y motivo. |
| `message` | Motivo de un fallo, como texto plano de 500 caracteres como máximo (RF-119, RF-120). |

### 3.2 Ampliaciones de `SourceRecord`

| Cambio | Motivo | RF |
|---|---|---|
| Un campo puede llegar marcado como **ilegible** (`{"unreadable": true}`). Se guarda como observación no válida por "ilegible", distinta de "imposible". | D-8 | RF-48, RF-49 |
| `identity.logo_url` sigue siendo la dirección original: la ingesta la descarga y la sustituye por la copia propia. | RF-65 | RF-65 a RF-71 |

### 3.3 Eventos del servidor (`/api/stream`)

| Evento | Contenido | Cuándo |
|---|---|---|
| `change` | `{datasets: [...], changedAt}` | Tras cada ingesta con cambios (aviso `NOTIFY` del proceso de obtención). |
| `freshness` | `{dataset: stale}` para los que cambian de estado | Al pasar un umbral de desactualización o recuperarse. |
| `heartbeat` | `{now}` | Cada 15 s. Si no llega en 45 s, el frontend da el canal por cortado. |

El navegador se reconecta solo (`retry: 5000`). Los datos no viajan por el canal: la página los vuelve a pedir a su ruta normal. Así las reglas de la 002 y los filtros de temporada se aplican siempre en un único sitio.

### 3.4 API de administración

Todas bajo `/api/admin`, respondiendo 401 sin sesión válida (RF-137, RF-139). Toda petición que cambia algo exige además la cabecera `X-Retake-Admin: 1` y el mismo origen (D-11).

| Ruta | Función | RF |
|---|---|---|
| `POST /login` | Usuario y contraseña → sesión en cookie. Sin decir qué falló; con bloqueo por origen. | RF-124 a RF-133 |
| `POST /logout` | Cierra la sesión actual. | RF-138 |
| `GET /me` | Si hay sesión válida. | RF-124 |
| `GET /sources` | Por fuente: última consulta, última con éxito, si está parada, ciclo vigente y peticiones en curso. | RF-103, RF-112 a RF-114 |
| `POST /sources/{source}/refresh` | Pide actualizar una fuente. Si ya hay una en curso, devuelve esa; si las normas lo prohíben, devuelve el motivo. | RF-100, RF-107, RF-109 a RF-111 |
| `POST /history/reread` | Pide releer el historial. | RF-102, RF-108, RF-109 |
| `GET /requests/{id}` | Estado y resultado (`success`, `partial`, `failure`) con el número de incidencias y el enlace a ellas. | RF-103 a RF-106 |
| `GET /log` | Registro de los últimos 7 días, paginado y filtrable por fuente. | RF-140 a RF-149 |
| `GET /summaries` | Resúmenes diarios de los últimos 7 días. | RF-150 a RF-154 |

### 3.5 `curation.yaml` — secciones nuevas

| Sección | Contenido de cada entrada | RF |
|---|---|---|
| `merges` | Tipo (`match`, `event`, `franchise`) y dos o más referencias que son lo mismo, con su motivo. Los jugadores siguen en `player_merges`. | RF-54, RF-56 |
| `confirmed_new` | Referencia retenida que es de verdad un objeto nuevo, con su motivo. | RF-56 |

La orden `retake list-retained` lista los registros retenidos y, para ayudar a Hugo, sugiere candidatos parecidos (mismos equipos y fecha, o mismo gamertag). **Solo sugiere: nunca une nada** (RF-54, RF-132 de la 002).

---

## 4. Modelo de datos (una migración nueva)

| Tabla o cambio | Contenido | RF |
|---|---|---|
| `external_ref` + `last_seen_at`, `retained_since` | Última vez vista en una consulta con éxito; si está retenida y desde cuándo. | RF-50 a RF-52, RF-55 |
| `observation` + `invalid_reason` | `impossible` o `unreadable` cuando `is_valid` es falso. | RF-48, RF-49 |
| Tablas resueltas de la 002 + `changed_at` | Instante del último cambio del valor resuelto de la fila. | RF-157 a RF-159 |
| `match` + `stats_complete_at`, `disappeared_at` | Cuándo se completaron sus estadísticas; si está desaparecido. | RF-19 a RF-21, RF-50 a RF-52 |
| `logo_image` | Huella SHA-256 (identificador), contenido, tipo, tamaño y fecha. Una imagen idéntica se guarda una sola vez. | RF-65 a RF-70 |
| `identity` + `logo_image_id` | Copia propia del logo de la identidad. | RF-65, RF-71 |
| `dataset_change` | Último cambio por conjunto de datos (para `/api/freshness` y los bloques vacíos). | RF-155, RF-158 |
| `source_state` | Por fuente: última consulta, última consulta con éxito y número de elementos de la última respuesta (para detectar respuestas vacías). | RF-46, RF-112 a RF-114 |
| `sync_job` | Tareas con fecha: relecturas del Champs (1 h y 24–168 h), reintentos del historial, carga inicial y cambios de modo. | RF-3 a RF-5, RF-12, RF-13, RF-30 a RF-33 |
| `sync_request` | Peticiones del administrador: tipo, fuente, estado, resultado y número de incidencias. | RF-100 a RF-111, RF-136 |
| `sync_run` | Una fila por consulta: fuente, tipo, inicio, fin, resultado, mensaje y petición asociada. Se borra a los 7 días. | RF-140, RF-141 |
| `incident` | Única por fuente + tipo + dato + valor + motivo: primera y última aparición, y repeticiones. Se borra 7 días después de su última repetición. | RF-142 a RF-149 |
| `incident_day` | Repeticiones de cada incidencia por día natural de Ciudad de México, para el resumen. | RF-150 a RF-152 |
| `daily_summary` | Día y contenido del resumen. Se borra a los 7 días. | RF-150 a RF-154 |
| `admin_user` | Usuario y *hash* Argon2id. Una sola fila. | RF-121 |
| `admin_session` | *Hash* del identificador de sesión, creación, caducidad (8 h) y origen. | RF-125, RF-134 a RF-138 |
| `login_origin` | Por origen: intentos fallidos seguidos y fin del bloqueo. | RF-127 a RF-133 |

---

## 5. Planificación de las consultas

Cada 5 s, `planner` calcula qué toca a partir del estado guardado y del reloj inyectado (H-5). Todo lo que depende de la hora se prueba sin esperar (§6).

| Consulta | Cuándo | Fuentes | RF |
|---|---|---|---|
| **Carga inicial** | Base de datos vacía, o cambio de modo en desarrollo: primero la temporada actual (y la próxima, si existe) y después el historial. | Las tres | RF-3 a RF-6, RF-12, RF-13 |
| **En vivo** | Cada 60 s por partido `en vivo`: su página de partido y la lista de partidos en vivo. Si no caben todos, el prioritario cada 60 s y los demás cada 2 min. | BreakingPoint (a comprobar en 2027, I-7) | RF-16, RF-23 a RF-26, RF-57 |
| **Antes del partido** | Cada 60 s mientras algún partido `programado` esté a 1 h o menos de su hora, o la haya pasado sin empezar. | BreakingPoint (lista) | RF-17 |
| **Resto** | Cada hora: calendario, eventos, equipos, identidades y logos, rosters, jugadores, tabla, próxima temporada. | BreakingPoint; la Wiki para los jugadores (I-3) | RF-14, RF-18 |
| **Partidos terminados** | Cada hora, cada partido `finalizado` con estadísticas pendientes o completado hace menos de 7 días. | BreakingPoint | RF-19 a RF-21 |
| **Historial** | Carga inicial; final del Champs registrada + 1 h; +24, 48, 72, 96, 120, 144 y 168 h; reintento cada hora si falla; a petición. | Wiki | RF-4, RF-30 a RF-34, RF-102 |
| **Resumen diario** | A las 00:00 de `America/Mexico_City`. | — | RF-150 a RF-153 |
| **Limpieza** | Cada hora: registro, incidencias y resúmenes de más de 7 días. | — | RF-149, RF-154 |

- **Al reanudar tras una parada**, las consultas vencidas se ejecutan en el primer ciclo: los datos en vivo quedan al día en 60 s y el resto en 1 h, con su estado actual (RF-27 a RF-29).
- **Fuente parada:** si la última consulta a una fuente es más antigua que el doble de su ciclo más corto vigente (RF-114).

---

## 6. Estrategia de pruebas

### 6.1 Niveles

| Nivel | Herramienta | Qué prueba |
|---|---|---|
| **Unitario (backend)** | pytest | Reglas de `domain/` (§2.1), `planner` con reloj simulado (cada ciclo, ventana, prioridad y reintento de §5) y el cálculo del resumen y de las repeticiones. |
| **Conectores** | pytest + transporte simulado de httpx | Cada conector con **muestras recortadas** de respuestas reales (solo los campos que se usan, con su fuente y fecha, D-16): traduce bien, marca lo ilegible, detecta la respuesta vacía, respeta la pausa y la identificación. **Ninguna prueba sale a internet** (RF-10). |
| **Integración (backend)** | pytest + `retake_test` | Proceso de obtención de punta a punta con la fuente simulada y el reloj simulado; ingesta ampliada (§2.3); API ampliada, eventos del servidor y administración (acceso, bloqueo, sesiones, peticiones). |
| **Unitario (frontend)** | Vitest | `src/live/` con un canal de eventos y una visibilidad simulados, pie, página de administración y diccionarios en los dos idiomas. |
| **Extremo a extremo** | Playwright + axe | Acceso de administración, atribución y año del pie, aviso de datos sin actualizar con la fuente simulada y auditoría WCAG 2.2 AA de un bloque que se actualiza solo. |
| **Manual** | Guía paso a paso (constitución §5) | Cada RF, con los escenarios de la fuente simulada y, para los ciclos en vivo, un partido real (criterio 3 del §6 de la spec). |

### 6.2 Reglas

- El reloj siempre se inyecta, y la hora de Ciudad de México se calcula con `zoneinfo`, nunca con un desfase fijo.
- Las muestras de respuestas reales se recortan a los campos que se usan. No se guardan páginas completas en el repositorio.
- Cada fase del §7 termina con sus pruebas en verde y su bloque de la guía manual.

### 6.3 Matriz de cobertura (resumen por bloques de la spec)

| RF | Qué se comprueba | Unit. | Conect. | Integ. | FE | E2E | Manual |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|
| RF-1 a RF-15 | Carga inicial en orden, arranque entre temporadas, datos parciales durante la carga, modos y entornos, próxima temporada oculta | ✓ | ✓ | ✓ | | | ✓ |
| RF-16 a RF-29 | Ciclos, ventana previa, partidos terminados, prioridad con varios en vivo y recuperación tras una parada | ✓ | | ✓ | | | ✓ |
| RF-30 a RF-34 | Relecturas del Champs, reintentos y datos personales de jugadores históricos | ✓ | ✓ | ✓ | | | ✓ |
| RF-35 a RF-42 | Identificación, pausa, límites, consultas prohibidas, API de la Wiki | | ✓ | ✓ | | | ✓ |
| RF-43 a RF-53 | Fallos, respuesta vacía, datos a medias o ilegibles, desaparición, reaparición y cancelación | ✓ | ✓ | ✓ | | | ✓ |
| RF-54 a RF-60 | Enlaces, retención, marcador más avanzado, retirada permanente | ✓ | | ✓ | | | ✓ |
| RF-61 a RF-71 | Identidad combinada, logos: copia, duplicados, formato, tamaño y logo retirado | ✓ | ✓ | ✓ | | | ✓ |
| RF-72 a RF-78, RF-160 | Temporada automática, año del pie y atribución | ✓ | | ✓ | ✓ | ✓ | ✓ |
| RF-79 a RF-96 | Actualización sin recargar, márgenes, segundo plano, estado conservado, aviso de datos sin actualizar, accesibilidad | | | ✓ | ✓ | ✓ | ✓ |
| RF-97 a RF-139 | Página de administración, peticiones, resultados, acceso, bloqueo por origen y sesiones | ✓ | | ✓ | ✓ | ✓ | ✓ |
| RF-140 a RF-154 | Registro, repeticiones, conservación, resumen diario | ✓ | | ✓ | ✓ | | ✓ |
| RF-155 a RF-159 | Hora de última actualización | ✓ | | ✓ | ✓ | | ✓ |

### 6.4 Fuente simulada

Funciona en desarrollo y en las pruebas; en producción, el proceso se niega a arrancar con ella. Responde como las tres fuentes a partir de **escenarios** (archivos JSON con respuestas que cambian con el tiempo): partido que empieza y termina, marcadores contradictorios, fuente caída, respuesta vacía, dato ilegible, partido que desaparece y reaparece, varios partidos en vivo, cambio de temporada y final del Champs con la clasificación publicada días después. Así se verifican a mano los casos que la spec pide simular (criterio 4 de su §6), igual que el bloque de demostración de la 001.

---

## 7. Plan de implementación (fases)

Cada fase se puede verificar por separado. `tasks.md` desglosará cada una en tareas atómicas.

| Fase | Contenido | RF |
|---|---|---|
| **F0. Exploración de las fuentes** | Mapa definitivo de dónde sale cada dato de la 002 en cada fuente: fichas de jugadores y rosters de BreakingPoint, consultas estructuradas de la Wiki (resultados, jugadores, rosters, estadísticas), petición interna de la tabla de la CDL (H-3), si alguna fuente publica marcadores en vivo además de BreakingPoint y si las fuentes se enlazan entre sí (`same_as`). Se guardan las muestras recortadas para las pruebas. **Puerta:** si algo impide cumplir un requisito, se aplica la regla P-1 y se vuelve a Hugo. | RF-1, RF-36, RF-38 |
| **F1. Modelo de datos** | Migración de §4 y dependencias nuevas (httpx, BeautifulSoup, argon2-cffi y Pillow). | Base |
| **F2. Reglas de dominio** | Piezas de §2.1 con sus pruebas unitarias. | RF-19 a RF-26, RF-50, RF-53, RF-57 a RF-63, RF-89, RF-90 |
| **F3. Conectores y logos** | `sources/` (§2.2), fuente simulada con escenarios y `logos/`. | RF-1, RF-14, RF-35 a RF-42, RF-46 a RF-48, RF-65 a RF-71 |
| **F4. Ingesta ampliada y curación** | Cambios de §2.3 y secciones nuevas de la curación, con `list-retained`. | RF-48, RF-49, RF-51 a RF-64, RF-157 a RF-159 |
| **F5. Proceso de obtención** | `sync/` (§2.4), órdenes `sync`, `sync-once` y `source-mode`. | RF-3 a RF-34, RF-43 a RF-47, RF-50, RF-72, RF-73, RF-140 a RF-154 |
| **F6. API ampliada y eventos del servidor** | `changedAt`, `isStale`, `/api/freshness`, `/api/logos/{id}`, `/api/stream` y el aviso por `LISTEN/NOTIFY`. | RF-15, RF-79 a RF-81, RF-89, RF-90, RF-155 a RF-159 |
| **F7. Administración (backend)** | `admin/` y rutas de §3.4, orden `set-admin-password`. | RF-97 a RF-154 (servidor) |
| **F8. Frontend** | `src/live/`, pie (año y atribución), página `/admin` y diccionarios `es` y `en`. | RF-74 a RF-99, RF-103 a RF-120, RF-124 a RF-139, RF-155 a RF-160 |
| **F9. Cierre** | Checklist de seguridad (§9), guía manual, medición con un partido real y sincronización de spec, plan y código (C-11 ya aplicado en la 001). | — |

---

## 8. Decisiones

### 8.1 Decisiones de diseño (dentro del stack aprobado)

| # | Decisión | Alternativa descartada | Justificación | RF |
|---|---|---|---|---|
| D-1 | **Los conectores producen `SourceRecord` y entran por `ingest_records`.** | Que cada conector escriba en las tablas. | Las reglas de la 002 siguen en un único sitio, ya probadas (D-3 de la 002). | RF-2 |
| D-2 | **El planificador es una función pura** del estado y la hora. | Temporizadores sueltos. | Cada regla de tiempo de la spec se prueba en milisegundos (H-5). | RF-16 a RF-33 |
| D-3 | **Una cola por fuente** en el proceso de obtención. | Una sola cola para todo. | La pausa de 2 s de una fuente no retrasa a las demás, y el en vivo de BreakingPoint no espera a la Wiki. | RF-16, RF-39 |
| D-4 | **Las peticiones del administrador pasan por la base de datos** (`sync_request`). | Que la API llame al proceso de obtención. | La API y el proceso de obtención están separados (H-4); la tabla también guarda el resultado que muestra la página. | RF-100 a RF-111, RF-136 |
| D-5 | **Los datos no viajan por el canal de eventos:** solo el aviso de qué cambió. | Enviar los datos por el canal. | Las reglas de la 002 y el filtro de temporada se aplican en las rutas de siempre. Un mensaje perdido no deja datos a medias: el siguiente aviso o la vuelta a la pestaña los recarga. | RF-15, RF-79 a RF-82 |
| D-6 | **`LISTEN/NOTIFY` de PostgreSQL** para avisar a la API. | Que la API consulte la base de datos cada pocos segundos. | Viene con PostgreSQL y psycopg, sin librerías nuevas, y el aviso es inmediato. | RF-80, RF-81 |
| D-7 | **`changed_at` por fila y `dataset_change` por conjunto.** | Una sola hora global. | RF-157 pide la hora de los datos que el bloque muestra; RF-158, la de lo que vigila un bloque vacío. | RF-155 a RF-159 |
| D-8 | **"Ilegible" distinto de "imposible".** | Tratar los dos igual. | Un imposible pasa a ausente (RF-100 de la 002); un ilegible cede el turno a otra fuente o conserva el valor (RF-48, RF-49). | RF-48, RF-49 |
| D-9 | **La retirada de datos personales se aplica en el cálculo del jugador,** no solo con `apply-curation`. | Aplicarla después de cada ingesta. | Así un dato retirado no aparece ni un instante entre una ingesta y la curación. | RF-60 |
| D-10 | **Bloqueo por origen = dirección IP del cliente.** Detrás de un proxy, solo se confía en su cabecera si está configurado. | Bloquear por cuenta. | Decisión Q-33; confiar siempre en la cabecera permitiría falsificar el origen. | RF-127 a RF-133 |
| D-11 | **Protección contra peticiones falsificadas:** cookie `SameSite=Strict`, cabecera propia obligatoria y comprobación del origen en toda petición de administración que cambia algo. | Solo la cookie. | Una web ajena no puede lanzar una actualización con la sesión de Hugo. | RF-139 |
| D-12 | **La cuenta se crea fuera de la web** con `retake set-admin-password`, que pide la contraseña sin mostrarla y nunca la recibe como argumento. | Variable de entorno con la contraseña. | Las contraseñas no quedan en el historial de la terminal ni en archivos (RF-122, RF-123, constitución §6.3). | RF-121 a RF-123 |
| D-13 | **Cada logo se identifica por su huella SHA-256.** | Por su dirección. | Una imagen idéntica se guarda una sola vez, y una imagen nueva en la misma dirección se detecta (Q-46). | RF-66, RF-67 |
| D-14 | **Logos de BreakingPoint primero**; los de la Wiki solo si BreakingPoint no tiene. | Seguir solo la prioridad de campos. | Las imágenes de Fandom no están bajo CC BY-SA (§1.1). Coincide con la prioridad de RF-67 de la 002. | RF-62, RF-65 |
| D-15 | **API de la Wiki con el parámetro de cortesía de MediaWiki** (se frena si el servidor va cargado) y consultas de una en una. | Consultas en paralelo. | Es la norma de uso de las API de MediaWiki y reduce el riesgo de bloqueo. | RF-39, RF-40 |
| D-16 | **Muestras de respuesta recortadas** para las pruebas de los conectores. | Guardar páginas completas. | Menos contenido ajeno en el repositorio y pruebas más claras; cada muestra lleva su fuente y fecha, como la muestra real de la 002. | — |
| D-17 | **El frontend no calcula la desactualización por su cuenta**, salvo la del canal cortado: el servidor dice si un conjunto está sin actualizar. | Calcularlo todo en el navegador. | Solo el servidor sabe cuándo se consultó con éxito cada fuente. | RF-89 |

### 8.2 Decisiones tomadas por Hugo (constitución §3.2)

| # | Decisión de Hugo | Descartadas | Recomendación del agente |
|---|---|---|---|
| H-1 | **httpx** (BreakingPoint) y **requests** (Wiki, decisión de F0, I-1) | — | httpx; requests para la Wiki tras F0 |
| H-2 | **BeautifulSoup** | selectolax; solo la librería estándar | BeautifulSoup |
| H-3 | **Buscar la petición interna de la CDL; navegador sin interfaz solo como plan B** (habría que volver a preguntar) | Playwright para Python desde el principio; no usar la CDL para la tabla | Buscar la petición interna |
| H-4 | **Proceso aparte** (`retake sync`) | Dentro de la API | Proceso aparte |
| H-5 | **Bucle propio con reloj inyectable** | APScheduler; cron/launchd | Bucle propio |
| H-6 | **Eventos del servidor (SSE)** | Consulta periódica; WebSocket | Consulta periódica |
| H-7 | **Argon2id con argon2-cffi** | bcrypt | Argon2id |
| H-8 | **Sesión en servidor + cookie HttpOnly** | JWT | Sesión en servidor |
| H-9 | **Pillow y copia de los logos en PostgreSQL** | Firma de bytes a mano y copia en disco | Pillow y PostgreSQL |

Las comparativas completas (ventajas, desventajas y curva de aprendizaje) se presentaron en la conversación del 2026-09-23. Resumen de las decisiones con más consecuencias:

- **H-4 (proceso aparte):** hay que arrancar dos procesos, la API y `retake sync`. Se añade `retake-sync` a `.claude/launch.json` para arrancarlo desde la app.
- **H-6 (SSE), que no era la recomendación:** exige que la API se entere de los cambios que hace el otro proceso (D-6) y que el proxy de Vite en desarrollo deje pasar la conexión abierta (riesgo en §10). A cambio, los datos en vivo llegan a la página en cuanto se registran, muy por debajo de los 30 s de RF-80.
- **H-9 (Pillow):** solo se aceptan PNG, JPEG y WebP que Pillow abre y verifica, de 1 MB como máximo. SVG y GIF se rechazan (RF-68).

---

## 9. Seguridad (constitución §6)

| Vector | Medida en la 003 | RF |
|---|---|---|
| Inyección SQL | Todo pasa por SQLAlchemy con parámetros, también el canal `NOTIFY` (nombres de conjunto de una lista cerrada). | — |
| XSS por texto de las fuentes | Texto plano siempre (escapado de React), también los mensajes de error, recortados a 500 caracteres. | RF-119, RF-120 |
| Imágenes maliciosas | Pillow verifica la imagen; solo PNG, JPEG y WebP de 1 MB como máximo. Se sirven con su tipo real y la cabecera `X-Content-Type-Options: nosniff`. | RF-68 a RF-70 |
| Contraseña | Argon2id; nunca en claro, ni en registros ni en argumentos. | RF-121, RF-123 |
| Sesiones | Identificador aleatorio de 32 bytes; solo se guarda su *hash*; cookie `HttpOnly`, `Secure` en producción, `SameSite=Strict`, limitada a `/api/admin`; 8 h. | RF-134 a RF-139 |
| Fuerza bruta | 5 fallos seguidos bloquean el origen 15 min; se anota como incidencia. Mismo mensaje para usuario inexistente y contraseña incorrecta. | RF-126 a RF-133 |
| Peticiones falsificadas | D-11. | RF-139 |
| Acceso a funciones de administración | Todas las rutas `/api/admin` salvo `login` exigen sesión. Documentación de la API desactivada en producción (como en la 002). | RF-139 |
| Carga sobre las fuentes | Pausa, límites, identificación y parámetro de cortesía (§1.2, D-15). | RF-37 a RF-42 |
| Datos personales | La retirada es permanente (D-9). El registro de incidencias nunca guarda el valor de un dato personal rechazado, solo su campo y el motivo. | RF-60 |
| Credenciales | En `backend/.env`, fuera de git. Variables nuevas en `.env.example`, sin valores. | — |
| Fuente simulada y datos de prueba | El proceso se niega a arrancar en producción con la fuente simulada o con datos ficticios. | RF-9 |

---

## 10. Riesgos y dependencias

| Riesgo | Impacto | Mitigación |
|---|---|---|
| **Acceso sin permiso de las fuentes (R-1)** | Una fuente puede bloquear a Retake o reclamar. | Decisión consciente de Hugo. Carga mínima (pausa, cortesía, identificación). Si una fuente bloquea, la incidencia aparece en la página de administración y se aplica la regla P-1. |
| **Pocos enlaces entre fuentes** (`same_as`) | Si BreakingPoint y la Wiki no se enlazan, casi todo lo de la Wiki que también publica BreakingPoint quedará retenido (RF-55) hasta unirlo a mano. | F0 mide cuántos enlaces hay. `list-retained` sugiere candidatos (sin unir). Si la carga manual es inasumible, se vuelve a Hugo (regla P-1) antes de F4. |
| **Ubicación de algunos datos por confirmar** | Tabla de la CDL, fichas de jugadores, estadísticas en la Wiki, marcadores en vivo fuera de BreakingPoint. | F0 lo resuelve primero; H-3 fija el plan B de la tabla. |
| **Cambios de formato de las fuentes** | Los conectores leen páginas sin contrato. | Muestras recortadas en las pruebas, datos ilegibles tratados según RF-48 y RF-49, e incidencias visibles para Hugo. |
| **Cloudflare en la Wiki** | Hoy la API responde; mañana podría bloquearse. | Incidencia y regla P-1. |
| **SSE y proxies** | El proxy de Vite o un futuro alojamiento podrían cortar las conexiones abiertas. | Latido cada 15 s, reconexión automática y prueba de extremo a extremo a través del proxy de Vite. Si falla, el aviso de datos sin actualizar lo delata (RF-89). |
| **Alojamiento 24 h sin decidir** | El proceso de obtención necesita una máquina encendida siempre. | Fuera de esta spec, igual que en la 001 y la 002. Mientras tanto, se cumple lo de las paradas (RF-27 a RF-29, RF-114). |
| **Volumen de reagrupación** (I-21 de la 002) | Con datos reales cada hora, recalcular los grupos de todo un tipo puede ser lento. | Se mide en F5; si hace falta, se limita a las referencias afectadas y se registra como ajuste. |
| **Hora de Ciudad de México** | Cambios de horario futuros. | `zoneinfo` con la zona `America/Mexico_City`, nunca un desfase fijo. |

---

## 11. Pendiente para aprobar este plan

1. ~~Revisar las condiciones de uso de las fuentes (regla P-2).~~ Hecho el 2026-09-23 (§1); dio lugar a la revisión R-1.
2. ~~Decidir cómo seguir ante las condiciones de uso (regla P-1).~~ Hugo: API donde exista y lectura de páginas públicas donde no. Revisión R-1 aprobada y aplicada en la spec.
3. ~~Aprobar el cambio C-11 en la 001.~~ Aprobado y aplicado el 2026-09-23.
4. ~~Elegir H-1 a H-9 (§8.2).~~ Hecho el 2026-09-23.
5. ~~Aprobar el plan.~~ Aprobado el 2026-09-23. El siguiente paso, cuando Hugo lo pida, es `tasks.md`.

---

## 12. Registro de implementación

Ajustes surgidos al implementar, registrados para que plan y código no se desincronicen (constitución §1.3). Detalle de la fase F0 en [`source-map.md`](source-map.md).

| # | Fase | Ajuste | Motivo | RF |
|---|---|---|---|---|
| I-1 | F0 | **La Wiki se consulta con `requests`**, no con httpx, y el historial con `action=parse` + BeautifulSoup, como en `CDL-data-analysis`. Nueva dependencia: `requests` (y `responses` para las pruebas sin internet). No se esquiva ninguna protección: si la Wiki rechaza también `requests`, se aplica la regla P-1. | Cloudflare rechaza httpx (403) y acepta `requests` con la identificación de Retake. Decisión de Hugo (H-1 de F0). | RF-38 |
| I-2 | F0 | **Pausa de la Wiki: 10 s**, y ante `ratelimited`, espera creciente (20, 40, 80 s… hasta 10 min) con incidencia anotada. | Su límite de consultas estructuradas rechazó alguna consulta incluso con 20–25 s de pausa (H-2 de F0). | RF-39, RF-40 |
| I-3 | F0 | **Papeles de las fuentes:** temporada actual de BreakingPoint; historial y jugadores (datos personales y gamertags anteriores) de la Wiki. La Wiki no aporta partidos, eventos ni rosters de la temporada. Uniones a mano: unos 50 jugadores por temporada, más las franquicias y jugadores del historial una vez. | Ninguna fuente publica identificadores de las otras; así se evitan unos 300 partidos retenidos por temporada (H-4 y H-11 de F0). | RF-1, RF-54 a RF-56 |
| I-4 | F0 | **La web de la CDL queda en reserva**, sin conector; la tabla sale de BreakingPoint. **RF-75 de la 002 queda incumplido** mientras tanto (limitación conocida, anotada en la spec, F0-3). | La dirección de su JSON cambia con cada versión y el CMS que la da falla a ratos (H-7 de F0). | RF-75 de la 002 |
| I-5 | F0 | **K/D calculado** (kills ÷ deaths con 2 decimales; con 0 deaths = kills) y **semana de clasificatorio calculada** (orden de la semana con partidos, hora de Ciudad de México). Cambios C-12 y C-13 de la 002, aprobados y aplicados el 2026-09-23. | Ninguna fuente publica el K/D; BreakingPoint no da la semana (H-3 y H-5 de F0). | RF-31, RF-79 de la 002 |
| I-6 | F0 | **Tabla de países en `curation.yaml`** (número de país de BreakingPoint → nombre). Un número sin traducir es `No disponible` y se anota como incidencia. | BreakingPoint solo publica `country_id`; su tabla está en su base de datos con una clave interna, que no se usa (H-6 de F0). | RF-22 de la 002 |
| I-7 | F0 | **En vivo y próxima temporada**, construidos con la estructura conocida y la fuente simulada; la exploración del en vivo se repite al empezar la temporada 2027 (dentro de T-089). **Mapas no jugados** desde `fetchGameBans` de BreakingPoint. | Fuera de temporada no hay datos en vivo; los mapas previstos sí se publican (H-8 y H-9 de F0). | RF-14, RF-16, RF-17, RF-57; RF-92, RF-94 de la 002 |
| I-8 | Tareas | **Bloque de demostración en vivo** en la página de demostración de la 001 (T-074). | Sin ninguna spec visual que use bloques que se actualicen solos, RF-79 a RF-96 no se podrían comprobar. | RF-79 a RF-96 |
| I-9 | F1 | Las **listas cerradas nuevas** (tipos de consulta, resultados, tipos de petición, estados, tipos de incidencia, conjuntos de datos, razones de invalidez, formatos y tamaño máximo de logo) se definen en `domain/vocabulary.py` ya en F1; T-016 queda para los umbrales. | Las restricciones CHECK de la migración las necesitaban. | — |
| I-10 | F1 | **Detalles del esquema** que el plan no fijaba: cuatro migraciones, una por tarea (`a1c0e3f5b701` a `…704`); `source_state` por fuente **y tipo de consulta** (la fuente parada se calcula con el más reciente); índice único parcial en `sync_request` que impide dos peticiones activas del mismo tipo y fuente también en la base de datos; `incident` única con los nulos como iguales (PostgreSQL 15+) y con `detail` opcional, sin guardar nunca el valor rechazado (solo su huella); `admin_user.id` fijo en 1 con CHECK; `changed_at` en las 11 tablas resueltas visibles (los cambios de horarios, lados, gamertags y rosters de campeonato se reflejarán en su fila madre en F4). Todas las columnas nuevas admiten nulo. | Integridad en la base de datos además de en el código, sin inventar valores para los datos de la 002. | RF-55, RF-107, RF-108, RF-121, RF-147, RF-157 |
| I-11 | F1 | La prueba "una fila en cada tabla" de la 002 (`test_schema.py`) se limita a las 19 tablas de la 002; las de la 003 las prueba `test_schema_003.py`. | Recorría todas las tablas de los modelos y las nuevas estaban vacías en esa prueba. | — |
| I-12 | F1 | **Configuración:** `SOURCE_MODE` (por defecto `fixtures`) y `TRUSTED_PROXY` (vacío = sin proxy). La combinación de entorno y modo se valida al cargar: producción solo `real` (RF-9) y pruebas nunca `real` (RF-10). `session_cookie_secure` se deriva de `APP_ENV`. Dependencias instaladas: httpx 0.28.1, requests 2.34.2, beautifulsoup4 4.15.0, argon2-cffi 25.1.0 y pillow 12.3.0; responses 0.26.3 para las pruebas. | Errores de configuración claros antes de arrancar nada. | RF-9 a RF-11 |
| I-13 | F2 | **Criterios de las reglas de dominio** que el plan no fijaba: (1) el marcador en vivo sin marcador del mapa en curso vale menos que cualquiera publicado, y un empate exacto de avance se resuelve por la prioridad de fuentes; (2) la fecha de vigencia se combina como un campo más, pero no cuenta para decidir si nace una identidad nueva; (3) una ausencia solo está comprobada entre la última consulta con éxito que incluía el partido y la última consulta con éxito de esa fuente, así que una fuente caída nunca hace desaparecer nada; (4) un conjunto sin ninguna consulta con éxito no está "sin actualizar" (no hay datos que avisar, p. ej. en la carga inicial); (5) una fuente nunca consultada está parada; (6) los partidos en vivo "caben" si `pausa × (1 + nº de partidos) ≤ 60 s`; (7) solo BreakingPoint tiene ciclo en vivo (I-3). Umbrales y ciclos en `domain/vocabulary.py` (T-016). | Reglas deterministas y probadas sin reloj real. | RF-23 a RF-26, RF-50, RF-57 a RF-63, RF-89, RF-90, RF-114 |
