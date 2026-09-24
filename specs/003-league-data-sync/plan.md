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
│   ├── http.py          Cliente educado (httpx): identificación, pausa por fuente, tiempos de espera
│   ├── bp.py            BreakingPoint: API interna JSON (tRPC) y JSON incrustado de partidos, equipos y jugadores
│   ├── wiki_csv.py      Wiki: importación de los archivos CSV que prepara Hugo (I-26; sustituye a wiki.py, sin acceso en vivo)
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
| `wiki_csv` | Importación de los archivos de la Wiki (I-26): lee los CSV de `WIKI_CSV_DIR`, los convierte en registros de fuente `wiki` y los pasa por `ingest_records` y la curación, en una sola transacción. Sin acceso a la Wiki. | RF-1, RF-4 a RF-4c, RF-32 |
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
| ~~`POST /history/reread`~~ | Eliminada (C-19, I-26). | — |
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
| `sync_job` | Tareas con fecha: carga inicial y cambios de modo (sin relecturas del historial, I-26). | RF-3, RF-12, RF-13 |
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
| **Carga inicial** | Base de datos vacía, o cambio de modo en desarrollo: la temporada actual (y la próxima, si existe). El historial llega con la importación (I-26). | BreakingPoint y CDL | RF-3, RF-6, RF-12, RF-13 |
| **En vivo** | Cada 60 s por partido `en vivo`: su página de partido y la lista de partidos en vivo. Si no caben todos, el prioritario cada 60 s y los demás cada 2 min. | BreakingPoint (a comprobar en 2027, I-7) | RF-16, RF-23 a RF-26, RF-57 |
| **Antes del partido** | Cada 60 s mientras algún partido `programado` esté a 1 h o menos de su hora, o la haya pasado sin empezar. | BreakingPoint (lista) | RF-17 |
| **Resto** | Cada hora: calendario, eventos, equipos, identidades y logos, rosters, jugadores, tabla, próxima temporada. | BreakingPoint (la Wiki ya no, I-26) | RF-14, RF-18 |
| **Partidos terminados** | Cada hora, cada partido `finalizado` con estadísticas pendientes o completado hace menos de 7 días. | BreakingPoint | RF-19 a RF-21 |
| ~~**Historial**~~ | Eliminada (I-26): el historial llega con `retake import-wiki-csv`, fuera del planificador. | — | RF-4, RF-32 |
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
| RF-4 a RF-4c, RF-32 | Importación de los archivos de la Wiki (sustituye a RF-30 a RF-34, I-26) | ✓ | ✓ | | | | ✓ |
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

Funciona en desarrollo y en las pruebas; en producción, el proceso se niega a arrancar con ella. Responde como las tres fuentes a partir de **escenarios** (archivos JSON con respuestas que cambian con el tiempo): partido que empieza y termina, marcadores contradictorios, fuente caída, respuesta vacía, dato ilegible, partido que desaparece y reaparece, varios partidos en vivo y cambio de temporada (el escenario del Champs tardío se retiró con I-26: la Wiki no se consulta). Así se verifican a mano los casos que la spec pide simular (criterio 4 de su §6), igual que el bloque de demostración de la 001.

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
| I-14 | F3 | **Formas de implementación** distintas de lo escrito en el plan: (1) la marca de ilegible es una lista `unreadable` con los nombres de campo en cada registro, validada contra sus campos, en lugar de un objeto `{"unreadable": true}` por campo; (2) los escenarios de la fuente simulada se definen en `app/sources/simulated.py` con ayudantes que reproducen la estructura real de las respuestas, en lugar de archivos JSON escritos a mano (9 escenarios, todos con equipos y jugadores `[FICTICIO]`); (3) `real_client(fuente)` construye el cliente real (httpx o requests) para el proceso de obtención y las comprobaciones manuales; la orden `sync-once` sigue siendo de F5 (T-055). | Menos duplicación y el mismo contrato; los escenarios no se desincronizan de la estructura de las fuentes. | RF-10, RF-11, RF-48 |
| I-15 | F3 | **Muestras de F0 corregidas:** tres muestras de BreakingPoint (`matches_page`, `match_detail`, `match_series_maps`) tenían claves renombradas (`map`/`mode` en vez de `maps.name`/`modes.name`) y cuatro de la Wiki habían perdido el envoltorio `{"title": …}` de cada fila. Se regeneraron desde las respuestas originales conservando la estructura exacta; los datos no cambian. | Unas pruebas sobre muestras con otra forma no garantizarían que el conector entiende las respuestas reales. | RF-10 |
| I-16 | F3 | **Criterios de los conectores:** (1) BreakingPoint: evento de la CDL = nombre que empieza por "CDL" (su filtro `cdlOnly` incluye la Esports World Cup); temporadas = la en curso por fecha de inicio y las posteriores, más la anterior mientras la en curso no haya jugado ningún partido (RF-2 de la 002; fallo detectado con la consulta real, que colaba la 2025); logo para fondo oscuro; país como `bp:<número>` para la tabla de países (I-6); mapas no jugados solo con el partido finalizado; roster = historial de equipos con papel de jugador que se solapa con la temporada, nunca para retirados; tabla desde la ficha de cada equipo. (2) Wiki: tabla de referencia de juegos por año (nombre oficial y abreviatura, mantenida a mano como en `CDL-data-analysis`; la Wiki no los publica); identidad de cada equipo histórico con el nombre publicado en su campeonato; campeonato completado si tiene 1.er puesto; jugadores de la temporada a partir de `TournamentPlayers`. | Reglas comprobadas con las muestras y con una consulta real de BreakingPoint (290 partidos, 11 eventos, 12 equipos). | RF-1, RF-4, RF-14, RF-17, RF-53, RF-58, RF-92 |
| I-17 | F3 | **Resolución del acceso a la Wiki:** el 403 de Cloudflare a `requests` se debía a la negociación de cifrados TLS de urllib3. Al montar en la sesión un adaptador SSL con los cifrados estándar (`DEFAULT@SECLEVEL=1`), Cloudflare responde 200 OK tanto en `action=parse` como en `action=cargoquery`. Verificado con `sync-once --source wiki` (57 registros del Champs 2026 extraídos en vivo). | Conexión limpia y conforme a las normas de la Wiki (RF-38). | RF-4, RF-30 a RF-34, RF-38 |
| I-18 | F4 | **Marcador en vivo y cancelación** (T-040, T-041): el valor de cada fuente se lee con `ObservationIndex.by_source`; el marcador en vivo es el más avanzado entre las fuentes y el registrado (nunca retrocede); al finalizar vuelve la prioridad. Una cancelación que no es de la fuente principal se ignora y se informa en `IngestReport.discrepancies` con la referencia de la fuente principal y el motivo. | Las reglas puras de F2 necesitaban el valor de cada fuente, no solo el ganador por prioridad. | RF-53, RF-57 a RF-59 |
| I-19 | F4 | **Número de semana** (T-092, C-13): la 002 tenía la fase `week` pero ningún campo para su número. Se añade `match.week` (migración `a1c0e3f5b705`, CHECK > 0) y el campo opcional `week` del registro de partido; BreakingPoint marca `round.stage = "qualifier"` como fase `week` (antes, sin fase). Se calcula al final de cada ingesta por evento y manda la semana publicada si existe. Prueba con las dos fechas reales de la muestra de la Wiki ("Week 1" y "Week 4") y dos fechas de prueba para las semanas 2 y 3, con el parón navideño entre ellas (la muestra solo tiene dos partidos). | Sin el campo no se podía cumplir C-13. | RF-31 de la 002 |
| I-20 | F4 | **Identidad combinada** (T-042, sustituye I-15 de la 002): se combina la identidad más reciente de cada fuente. Si se suma una fuente nueva, completa la identidad vigente sin crear otra; si cambia lo que publica una fuente que ya formaba parte, nace una identidad nueva. La fecha de vigencia se toma por prioridad (Q-45), sin saltar por encima de la identidad anterior. Las identidades anteriores de una fuente siguen siendo historial. Ninguna prueba de I-15 de la 002 tuvo que cambiar. **Logos:** descargador inyectable (`logo_fetcher`; sin él no se descarga); cada dirección se descarga una vez por ingesta (el ciclo horario de identidades la revisa); una imagen nueva en la misma dirección crea identidad nueva (RF-67); si la descarga falla, se conserva la copia de esa misma dirección (RF-71) y, si no la hay, queda sin copia (RF-70). | Ningún conector publica fecha de vigencia en sus identidades: "vigentes en la misma fecha" es la más reciente de cada fuente. | RF-61 a RF-71 |
| I-21 | F4 | **Retención** (T-043, C-14): se recalcula al final de cada ingesta y de cada curación (la fuente principal puede empezar a publicar un tipo después). Una fila está oculta si todas sus referencias están retenidas; se aplica a `/api/players`, `/api/franchises`, `/api/events` y `/api/matches`; el historial y las fichas siguen usándolas. Se informa en `IngestReport.retained`. **Datos de prueba:** la muestra real de la 002 se transcribió de la Wiki y quedaría retenida por los casos límite de `bp`; el cargador de datos de prueba la confirma como nueva (solo en ese modo, no en `curation.yaml`, para no afectar a referencias reales de la Wiki en producción). Los casos ficticios `wiki:Twin_2` y `wiki:Split_B` se confirman en `curation.yaml`, como las demás entradas ficticias. | La demo y las pruebas de la 002 siguen igual sin tocar sus datos. | RF-54 a RF-56 |
| I-22 | F4 | **Curación** (T-044, T-093): `merges` (tipo `match`, `event` o `franchise`, dos o más `refs` y motivo), `confirmed_new` (tipo, `ref` y motivo) y `countries` (número de BreakingPoint → nombre). Al aplicar: franquicias, eventos, partidos y jugadores, en ese orden; tras unir, se recalcula lo que cuelga de cada parte. Un número de país sin traducir es un dato no entendido (RF-48): manda el país de otra fuente y, si no hay, queda ausente y se informa en `IngestReport.untranslated_countries`. | Formato explícito y validado, como el resto de la curación. | RF-54, RF-56, RF-142 |
| I-23 | F4 | **Estadísticas completas** (T-046): criterio de RF-47 de la 002. Faltan si un mapa jugado no tiene ninguna estadística o algún jugador no tiene ninguna; una suelta ausente no cuenta (RF-72 de la 002). Un partido sin mapas jugados (forfeit) las tiene desde que finaliza. Si vuelven a faltar, la marca se retira. | Ninguna parte de la 002 calculaba aún el aviso de pendientes. | RF-19, RF-20 |
| I-24 | F4 | **K/D calculado** (T-091, C-12): redondeo a 2 decimales con la mitad hacia arriba. Si se corrige kills o deaths de un partido cerrado, el K/D calculado también se marca como corregido. | Que la marca de corrección sea coherente con el dato que se muestra. | RF-79, RF-96 a RF-98 de la 002 |
| I-25 | F4 | **Retirada permanente** (T-045): la ingesta no guarda ninguna observación personal de un jugador retirado, ni de una referencia enlazada a él, ni de una que la curación vigente pida retirar aunque todavía no se haya aplicado. | "Ni un instante": antes se guardaban y se borraban después. | RF-60 de la 003, RF-78 de la 002 |
| I-26 | Tras F4 | **La Wiki entra por archivos CSV** (cambios C-15 a C-21 de la spec, aprobados por Hugo el 2026-09-23). La Wiki bloquea a Retake (403 de Cloudflare) y sus condiciones exigen permiso por escrito; Hugo prepara los CSV fuera de Retake y los actualiza tras cada Champs. **Archivos** (formato de `CDL-data-analysis`, tal cual), en `WIKI_CSV_DIR` (por defecto `backend/data/wiki/`, fuera de git porque llevan datos personales): `cdl_all_years_champs_prizepool.csv` (obligatorio: `Place, Year, Game Version, final_date, Prize, Prize (%), Team, Player`, una fila por jugador), `players_birthday.csv` (obligatorio: `Player, Name, Birthday`) y `cdl_<año>_rosters.csv` (opcionales: se usan `ID, Country, Name, Birthday`; `Stream`, `Twitter`, `Age` y el resto se ignoran). **Conversión:** campeonato con el identificador de su página (`championship_page`, igual que la muestra de la 002) y el juego de la tabla `GAMES` por año; una clasificación por año y equipo, con su roster (nunca un premio por jugador, RF-7 de la 002); franquicia e identidad por nombre de equipo (sin identificadores de página: los cambios de nombre se unen en la curación); jugador por gamertag, con nombre, fecha de nacimiento y país solo si figura en el historial o en un roster (RF-4a). **Orden** `retake import-wiki-csv [--dir RUTA]`: todo o nada si falta un archivo o una columna (RF-4c); un valor ilegible se marca y la importación queda parcial; muestra el resultado y lo anota en `sync_run` (fuente `wiki`, tipo `history`). **Se retira** el acceso en vivo: `sources/wiki.py` (salvo la tabla `GAMES` y los nombres de los campeonatos, que pasan a `wiki_csv`), el adaptador TLS, el cliente real de la Wiki, `sync-once --source wiki` y la dependencia `requests`. Sin consulta de historial en el planificador ni `POST /history/reread`; la Wiki no tiene ciclo, no aparece como parada y sus bloques no muestran el aviso de datos sin actualizar. Sustituye a I-1, I-2 e I-17 y a la parte de la Wiki de I-3. **Ajustes al implementar (T-095 a T-098):** (1) la importación no llama a `apply_curation`: la ingesta ya respeta uniones, separaciones, retiradas de datos personales y `confirmed_new`, y `curation.yaml` lleva referencias de los datos de prueba (`bp:fx-…`) que harían fallar la importación en una base sin ellos; (2) los registros retenidos no cuentan como incidencia de la importación (el historial los usa, C-14): se informan aparte y se revisan con `list-retained`; (3) una fila con un año no válido se descarta y deja la importación parcial; un premio, porcentaje o fecha ilegibles se marcan como ilegibles (RF-48); (4) la última importación se guarda en `source_state` (`wiki`, `history`) para RF-113, porque `sync_run` se borra a los 7 días; (5) `is_source_stopped` nunca marca la Wiki como parada (C-19); (6) también se retiran, por quedar sin uso, la espera creciente del cliente (I-2), la pausa mínima de la Wiki, `HISTORY_REREAD_OFFSETS`, el escenario simulado `champs_tardio`, la parte de la Wiki de `dato_ilegible`, las muestras `tests/snapshots/wiki/` y la dependencia `beautifulsoup4`. El tipo de petición `history_reread` queda en el esquema sin uso. **Fallo corregido en T-099:** `resolve_championship` (002) marcaba correcciones en campeonatos, que no tienen `corrected_fields`; al importar sobre los datos de prueba rompía la ingesta. Ahora los cambios del campeonato se registran sin marca. **Comprobado** con los CSV reales de `CDL-data-analysis` (agosto de 2026): 14 campeonatos, 284 clasificaciones, 168 franquicias y 515 jugadores (302 con fecha de nacimiento y 88 con país), sin registros inválidos. | Datos de la Wiki sin acceso automático, que Hugo actualiza a mano una vez al año. | RF-1, RF-4 a RF-5, RF-18, RF-30 a RF-34, RF-38, RF-89, RF-100 a RF-114 |
| I-27 | F5 | **Revisión de F5 (T-049 a T-056) según §5 y la spec:** (1) `retake sync` no arranca en modo `fixtures` (los datos son los de prueba; RF-9 a RF-11) y sale con un mensaje claro; en producción ya no falla al buscar datos ficticios (usa la marca `fictional` de las referencias y `current_gamertag`). (2) Cada consulta usa la del conector que fija §5: listado completo en la carga inicial y el "Resto"; solo la lista de próximos y en vivo (`bp.consult_upcoming`, nueva) antes del partido y en vivo; la página del partido en vivo y en la revisión, **pedida por su identificador en BreakingPoint** (antes se pedía por el UUID interno y fallaba siempre). (3) El "Resto" incluye tabla, rosters y jugadores: tras cada listado con éxito se encolan las fichas de cada equipo (`consult_teams`); el listado devuelve los equipos y las fechas de la temporada (`ConsultaResult.teams` y `season`). La fuente simulada responde fichas ficticias de equipo y jugador en todos los escenarios. (4) Ciclos: el trabajador recuerda cuándo consultó cada partido en vivo y cada partido terminado (60 s y 1 h) y cuándo limpió el registro (1 h); antes se reconsultaban en cada ciclo de 5 s. La carga inicial cuenta como "Resto". (5) Orden dentro de la cola de una fuente: peticiones del administrador, en vivo, antes del partido, carga inicial, "Resto", fichas de equipo y, al final, partidos terminados (RF-16). (6) RF-46 solo en los listados completos (la lista de próximos puede vaciarse); las fichas de equipo no cambian el estado de la consulta; la desaparición (RF-50) solo cuenta los listados con éxito. (7) El registro guarda el partido y el motivo reales de las discrepancias de cancelación y de los países sin traducir; una excepción inesperada se deshace, se anota como consulta fallida y el proceso sigue. (8) En modo `real`, el trabajador pasa el descargador de logos (RF-65, I-20). (9) `source-mode` recuerda volver a importar los archivos de la Wiki, porque RF-12 también los borra; sigue escribiendo `SOURCE_MODE` en `backend/.env`. Limitación conocida: una consulta larga (el listado completo, con su paginación) ocupa la cola de BreakingPoint mientras dura; se comprobará con la temporada 2027 (T-094). | Proceso que respeta los ciclos del plan y no sobrecarga la fuente. | RF-9 a RF-11, RF-16 a RF-21, RF-46, RF-50, RF-65, RF-142, RF-146 |
| I-28 | F6 | **API ampliada y canal de eventos (T-058 a T-062):** `changedAt` en cada fila de las respuestas de la 002 (temporada, identidad, evento, jugador, partido, mapa, estadísticas, posición, campeonato y clasificación; la franquicia no tiene columna propia) e `isStale` en cada partido. **Frescura:** un conjunto está sin actualizar si BreakingPoint lleva más de su umbral sin un listado con éxito; el en vivo, solo mientras haya partidos en vivo y con su propia consulta; el historial nunca (C-20); sin ninguna consulta, nunca (RF-8). **`logoUrl`** apunta a la copia propia (`/api/logos/{huella}`) o es `null` si no la hay (RF-70); la prueba de la 002 que listaba los campos de una identidad añade `changedAt`. **`/api/stream`** usa `LISTEN` con psycopg asíncrono, `retry: 5000`, latido cada 15 s y `freshness` solo para los conjuntos que cambian; cabeceras `Cache-Control: no-cache` y `X-Accel-Buffering: no`. La próxima temporada ya quedaba fuera por los filtros de la 002. | Contratos del plan §2.5 y §3.3. | RF-15, RF-65, RF-70, RF-79 a RF-81, RF-89, RF-90, RF-155 a RF-159 |
| I-29 | F7 | **Administración en el servidor (T-064 a T-068):** `retake set-admin-password` pide usuario y contraseña (dos veces, sin mostrarla, nunca como argumento), solo exige que no estén vacíos y **cierra todas las sesiones** al cambiarla. `verify_login` compara siempre contra un *hash* (también con usuario inexistente) para no delatar qué usuarios existen. La protección D-11 (cabecera y mismo origen, comparando `Origin` o `Referer` con `Host`) también se exige en `login` y `logout`. Origen bloqueado → `429`; credenciales incorrectas → `401` con el mismo mensaje. Con `TRUSTED_PROXY`, el origen es la última dirección de `X-Forwarded-For`. Actualizar la Wiki o la web de la CDL deja una petición `forbidden` con su motivo (C-19, I-4). `GET /log` pagina consultas e incidencias de 7 días; `GET /summaries`, los 7 últimos días. La IP de un origen bloqueado queda como asunto de su incidencia (se borra a los 7 días). | Seguridad del plan §9 sin inventar reglas no documentadas (longitud mínima de la contraseña). | RF-100 a RF-154 |
| I-30 | F8 | **Frontend (T-070 a T-082):** `src/live/` (canal único por pestaña; corte a los 45 s sin mensajes; bloque que se recarga en silencio al avisar el canal, cada ciclo de la página y al volver a la pestaña; frescura y anuncios solo del en vivo) y `src/admin/` (acceso, estado de las fuentes con petición y resultado, registro y resúmenes con el detalle por fuente de RF-151 y RF-152). **Pie:** el año sale de `/api/season/current` (se retira `src/config/season.js`) y lleva la atribución de las tres fuentes y de la licencia CC BY-SA. Por eso se actualizan pruebas de la 001: las del pie simulan la respuesta de la API, y la de idioma de extremo a extremo también; la del scroll al cambiar de idioma pulsa con `dispatchEvent`, porque con el pie más alto Playwright desplazaba la página para ver el botón. **Bloque en vivo** en la página de demostración (T-074, solo desarrollo). Las pruebas unitarias simulan `fetch` por defecto (ninguna sale a la red). Playwright arranca también la API (para el canal a través del proxy de Vite) y `vite preview` usa el mismo proxy. | Plan §2.6 y D-12: la 003 da las funciones y el cargador; cada spec visual decide el aspecto. | RF-74 a RF-160 |
| I-31 | F9 | **Cierre (T-084, T-085, T-087, T-088):** checklist de seguridad en `verification-guide.md` sin incumplimientos, salvo un pendiente: `curation.yaml` mezcla entradas de los datos de prueba con las reales y en producción `apply-curation` fallaría por referencias desconocidas (decisión de Hugo antes de desplegar). Todas las pruebas en verde: backend 683, frontend 422 y extremo a extremo 138. Quedan T-086 (recorrido en modo real), T-087 (confirmación de Hugo), T-089 y T-094 (dependen del calendario) y T-090. | Constitución §5 y §6. | — |
| I-32 | F5 | **Reloj del modo simulado:** los escenarios fijan sus partidos el 2026-12-05; con el reloj del sistema, `retake sync` en modo simulado nunca llegaba a la ventana previa de 1 h y no veía el en vivo (lo detectó Hugo al recorrer el escenario `partido_en_vivo`). En modo simulado, el trabajador usa `ScenarioClock`, que empieza en `SCENARIO_START` (una hora antes de los partidos) y avanza en tiempo real. Las pruebas ya usaban un reloj fijo en esa fecha. | Que el recorrido manual de T-057 muestre el en vivo. | RF-16, RF-17 |
| I-33 | F5 | **Páginas de partido en los escenarios simulados:** cinco escenarios (`marcador_que_retrocede`, `fuente_caida`, `respuesta_vacia`, `partido_desaparece` y `cambio_de_temporada`) publicaban partidos en vivo o terminados sin su página `/match/{id}`, y cada revisión registraba un 404 (lo detectó Hugo al recorrer `fuente_caida`). Se añade el ayudante `_series`, que monta la página con mapas que cuadran con el marcador, y una prueba que exige página para cada partido en vivo o terminado de cada escenario. En `partido_desaparece`, la página tampoco responde mientras el partido falta: si respondiera, seguiría apareciendo (RF-50). | Que los recorridos manuales de T-057 no registren fallos que no están en el escenario. | RF-16, RF-19, RF-50 |
| I-34 | F5 | **Un solo `retake sync` por base de datos** (aprobado por Hugo el 2026-09-24): al recorrer T-057 se colaron dos veces dos procesos a la vez, que se pisaban (uno hizo la carga inicial con otro reloj y dejó el partido del escenario como terminado). `retake sync` retiene un bloqueo consultivo de PostgreSQL (`pg_try_advisory_lock`, `app/sync/lock.py`) en una conexión propia mientras está en marcha; un segundo proceso no lo obtiene y se niega a arrancar con un mensaje que explica cómo localizar el otro. Si el proceso se cae, PostgreSQL suelta el bloqueo al cerrarse la conexión. El bloqueo es de cada base de datos, así que las pruebas no chocan con el proceso de desarrollo. | Que no puedan correr dos procesos de obtención contra la misma base. | RF-44 |
| I-35 | T-086 | **Curación real separada de la de prueba** (decisión de Hugo, 2026-09-24): `curation/curation.yaml` lleva solo datos reales y `curation/fixtures.yaml` las entradas `[FICTICIO]`. `curation_path(modo)` elige el archivo: el de prueba en `fixtures` (`load-fixtures`, y `apply-curation` e `import-wiki-csv` en ese modo); el real en `real` y `simulated` (la obtención y la ingesta por defecto). Las dos se siguen validando en modo estricto: antes, las entradas reales rompían `load-fixtures` y las de prueba habrían roto `apply-curation` en una base real. **Primera curación real** (primera carga, T-086): 11 países (el 74 queda sin traducir: manda la Wiki), 11 franquicias actuales unidas a su nombre corto de la Wiki (M80 Boston con BOS Breach, confirmado por Hugo) y 60 jugadores con el mismo gamertag en BreakingPoint y en el roster 2026 de la Wiki; `wiki:LuCkY` y `wiki:Super` no se unen (jugadores antiguos). Los nombres de país van en inglés, como los de la Wiki; el 233 es `United Kingdom` por decisión de Hugo. **Pruebas:** fijan su modo de fuente (`fixtures`) en vez de heredar el de `.env`, y el módulo que carga los datos de prueba cierra su sesión aunque la carga falle (antes, un fallo dejaba la batería colgada). | Curación de los datos reales sin romper la de los de prueba. | RF-54, RF-56, RF-142 |
| I-36 | T-086 | **Franquicias de la temporada que la fuente ya no lista** (cambio C-22, aprobado por Hugo el 2026-09-24). En la primera carga real, BreakingPoint lista a Boston Breach como M80 Boston (bp:1176, sin tabla), mientras sus partidos, su tabla y sus rosters de 2026 siguen con bp:6; todo eso se rechazaba. **Conector:** tras leer los partidos del listado (`consult_regular` y `consult_upcoming`), se piden las fichas `/teams/{id}` de los equipos que no están en `allTeams`; si su tabla es de una de las temporadas del listado, se añaden su franquicia, su identidad y su posición antes de los partidos, y el equipo se suma a `teams` para seguir con sus fichas en el "Resto". Su identidad empieza en la fecha de alta de la ficha (`start_date`), para que, al unirla con su nombre siguiente, quede como identidad anterior: los partidos de 2026 llevan Boston Breach y la vigente es M80 Boston, sin que las dos referencias de la misma fuente se turnen. **Coste:** `UnlistedTeams` recuerda 24 h los equipos comprobados que no están en la tabla (unas 19 fichas al día en vez de cada hora); no recuerda las franquicias reconocidas (su identidad puede cambiar) ni las fichas que fallaron (pasajero). Una ficha que falla se anota como dato rechazado (`team`) y la consulta sigue; `Forbidden` detiene la consulta como en el resto del conector. El trabajador guarda la memoria y la pasa al runner. **Curación:** `bp:1176`, `bp:6` y `wiki:BOS_Breach` son la misma franquicia. **Escenario simulado** `franquicia_sin_listar`. Los equipos de fuera de la CDL siguen rechazándose y anotándose hasta que se decida C-23. **Exploración del 2026-09-24 (26 consultas identificadas como Retake):** `division_id` de BreakingPoint no sirve para distinguirlos (bp:6 y un equipo que no es de la CDL comparten el 8). | Que no se pierda la temporada de una franquicia renombrada con otro número. | RF-18, RF-18a, RF-54, RF-142 |
| I-37 | T-086 | **Unir franquicias ya cargadas dejaba identidades repetidas** (fallo de T-042/T-044, visto al comprobar C-22 en la base real). Si la franquicia de la Wiki ya existía, con su clasificación, cuando la curación la unía a la de BreakingPoint, la referencia de BreakingPoint pasaba a la fila de la Wiki (más reciente) y su fila original se quedaba sin referencias, con los mismos datos y con las clasificaciones antiguas: dos identidades seguidas iguales, contra RF-73 de la 002. Les pasó a las 11 franquicias unidas en I-35. **Arreglo:** `collapse_repeated_identities` junta las identidades seguidas con los mismos datos (y la misma imagen de logo, si ambas tienen copia; RF-67): sobrevive la más antigua, con las referencias y las clasificaciones de la otra, y se recalculan las clasificaciones de la franquicia. Se aplica tras cada unión de franquicias y, en `apply-curation`, a todas las franquicias, para arreglar las bases ya cargadas. Los cambios de nombre de verdad (datos distintos) siguen siendo historial. Comprobado en la base de desarrollo: 11 identidades repetidas juntadas y ninguna identidad sin referencias. | Una identidad por nombre, como pide RF-73 de la 002. | RF-73 de la 002; RF-54, RF-61 a RF-64 |
| I-38 | T-086 | **Equipos invitados** (cambios C-23 y C-24, aprobados por Hugo el 2026-09-24; decisiones: mismos datos personales que los de la CDL, estadísticas del partido guardadas pero fuera de la temporada, visibles solo en sus partidos, fichas una vez al mes). **Base de datos** (migración `a1c0e3f5b706`): `franchise.is_guest` y `franchise.guest_checked_at`. **Ingesta:** el registro de franquicia lleva `guest`; una franquicia es invitada si alguna referencia lo publica y ninguna la publica como de la liga, así que deja de serlo en cuanto aparece en `allTeams` (RF-117d); la Wiki no lo publica. **Conector:** un equipo de un partido que no está en `allTeams` ni en la tabla entra como invitado (franquicia e identidad, sin posición), antes que los partidos; los invitados que ya están en la base (`known_guests`, que el trabajador refresca en cada ciclo) no se vuelven a pedir en el listado. `consult_teams` con `guests` trae además la identidad del invitado. Se retira la memoria de 24 h de I-36: ya no queda ningún equipo sin clasificar. **Trabajador:** tras cada listado con éxito encola, detrás de las fichas de la liga, las de los invitados de esa temporada que nunca se consultaron o llevan 30 días (`GUEST_CYCLE`) sin consultarse (`PlannedQuery.guest`); `guest_checked_at` solo se anota si la ficha sale bien (si falla, va con el siguiente listado). **API:** `/api/franchises` y `/api/standings` excluyen a los invitados; `/api/players` excluye a los jugadores que solo aparecen con invitados (`guest_only_player_ids`: ningún roster ni estadística con una franquicia de la liga ni historial de campeonatos); los lados de cada partido llevan `isGuest` y los jugadores `teamIsGuest`. Las estadísticas de los invitados siguen en el detalle del partido; la API aún no calcula medias ni rankings de temporada: las specs que los añadan deben excluirlas (RF-117c). La prueba de la 002 que listaba los campos de un lado de partido añade `isGuest`. **Escenario simulado** `franquicia_sin_listar` con un invitado y su jugador. Los rosters del historial de un jugador con equipos que no son ni de la liga ni invitados (nunca jugaron un evento de la CDL) se siguen rechazando y anotando (RF-142). | Minors completos sin mezclar a los invitados con la liga. | RF-18a, RF-18b, RF-117a a RF-117d de la 002 |
| I-39 | T-086 | **Revisión de partidos finalizados** (cambio C-25, aprobado por Hugo el 2026-09-24). En la primera carga real, los 281 partidos de la temporada (el último, del 19 de julio) entraron en la revisión horaria de 7 días porque sus estadísticas se registraron ese día; además, el trabajador recordaba en memoria cuándo consultó cada uno y, al reiniciarse, los repasaba todos. **Ahora:** una consulta al finalizar o al registrarse ya finalizado (RF-19) y otra a las 24, 48 y 72 horas (RF-20); si el partido ya llevaba más de 3 días jugado cuando se hizo la primera, se dan por hechas las tres (`reviews_after_first_check`). **Base de datos** (migración `a1c0e3f5b707`): `match.finished_checked_at` y `match.finished_reviews`; los partidos que ya tenían todas sus estadísticas se dan por consultados en esa fecha y, si ya llevaban más de 3 días jugados, con sus tres revisiones hechas. **Trabajador:** solo carga los partidos con revisiones pendientes; anota cada consulta que sale bien (también `partial`); si una falla, la memoria del proceso la repite a la hora (RF-45), no en cada vuelta de 5 s. **Plazos:** `FINISHED_REVIEWS`, `FINISHED_REVIEW_INTERVAL` y `FINISHED_REVIEW_AGE_LIMIT` sustituyen a `REVIEW_WINDOW`; `review_due` sustituye a `needs_review`. `stats_complete_at` sigue siendo el aviso de "Estadísticas pendientes" (RF-47 de la 002). | Pocas consultas a BreakingPoint y ninguna repetida tras un reinicio. | RF-19 a RF-21, RF-45 |
| I-40 | T-086 | **Rosters de equipos ajenos a la CDL** (cambio C-26, aprobado por Hugo el 2026-09-24). Tras C-22 a C-24, lo único que dejaba las consultas `partial` eran 33 rosters de 23 equipos del historial de algunos jugadores (Challengers), que no son franquicias ni invitados. **Ingesta:** un registro de roster cuya franquicia no existe se descarta sin anotarlo y se cuenta en `IngestReport.discarded`; `UnknownReferenceError` guarda el tipo y la clave de la referencia. Cualquier otra referencia desconocida (una identidad, un partido, el jugador de un roster) se sigue rechazando y anotando (RF-142). La prueba de la 002 que usaba un roster con una franquicia desconocida como ejemplo de referencia desconocida pasa a usar una identidad. **Curación:** países 148 (`Mexico`) y 250 (`Scotland`, aparte del Reino Unido en BreakingPoint), cruzados con la Wiki. | Que `partial` vuelva a significar un problema real. | RF-18c, RF-142 |
| I-41 | T-087 | **Acceso de administración a través del proxy de desarrollo** (visto por Hugo al entrar por primera vez en `/admin`): con la forma abreviada del proxy (`'/api': 'http://localhost:8000'`), Vite 8 activa `changeOrigin` y reescribe el `Host` a `localhost:8000`, mientras el navegador manda `Origin: localhost:5173`; la protección D-11 rechazaba el acceso con 403 antes de comprobar la contraseña. `vite.config.js` usa ahora `{ target, changeOrigin: false }` en `server` y `preview`. Comprobado a través del proxy: la propia web pasa, y siguen rechazadas las peticiones sin `X-Retake-Admin` o de otro origen. Las pruebas de extremo a extremo de `/admin` no lo detectaron porque simulan la API en el navegador. | Poder entrar en `/admin` en desarrollo sin rebajar D-11. | RF-124, RF-139; D-11 |
| I-42 | T-087 | **Registro al cambiar de modo** (cambio C-27, aprobado por Hugo el 2026-09-24). El registro de `/admin` mostraba arriba del todo 140 consultas y 3 incidencias de las pruebas en modo simulado, con fecha del 5 de diciembre (reloj del escenario, I-32), que la limpieza de 7 días no habría borrado hasta el 12 de diciembre. **Ahora:** `source-mode` borra también `sync_run`, `incident` y `daily_summary`; conserva `admin_user`, `admin_session` y `login_origin`. El mensaje de la orden lo dice. **Base de desarrollo:** con el permiso de Hugo, se borraron a mano esas 143 entradas con fecha futura; las 1.697 consultas reales de ese día se conservan. | Que el registro de `/admin` solo describa el modo en uso. | RF-12, RF-140 a RF-149 |

