# Guía de verificación manual — Spec 003

Guía paso a paso para que Hugo compruebe cada requisito de la spec 003 (constitución §5, tarea T-087). Cada fila dice **dónde** mirar, **qué** hacer y **qué** resultado esperar. Casi todo se comprueba con una prueba automática concreta, en la **API**, en la **terminal** o en el **navegador** (página de administración y bloque en vivo de la demostración).

Abreviaturas de las órdenes, desde la raíz del repositorio:

- **pt** = `uv run --directory backend pytest` (añade la ruta del archivo y `-v`).
- **vt** = `npx vitest run` (añade la ruta del archivo).
- **pw** = `npx playwright test` (añade la ruta del archivo).

## Preparación

1. PostgreSQL 18 en marcha y la base de datos al día:
   ```bash
   uv run --directory backend retake migrate
   ```
2. Todas las pruebas en verde antes de empezar:
   ```bash
   uv run --directory backend pytest
   ```
   ```bash
   npm test
   ```
   ```bash
   npx playwright test
   ```
3. Para lo que se mira a mano, dos terminales (backend y frontend):
   ```bash
   uv run --directory backend uvicorn app.main:app --port 8000
   ```
   ```bash
   npm run dev
   ```

> **Atención:** `retake source-mode` borra toda la liga de la base de desarrollo, también el historial de tus CSV, y el registro, las incidencias y los resúmenes del modo anterior (RF-12; C-27). La cuenta de administración se conserva. Al terminar, vuelve con `uv run --directory backend retake source-mode fixtures` e importa de nuevo con `uv run --directory backend retake import-wiki-csv`.

## Guía por fases

| Fase | Qué comprobar |
|---|---|
| F4b | `uv run --directory backend retake import-wiki-csv` → `Resultado: success`, 14 campeonatos, 284 clasificaciones, 168 franquicias y 515 jugadores; `http://localhost:8000/api/championships` muestra 2013 a 2026. |
| F5 (T-057) | **Escenario 1:** `uv run --directory backend retake source-mode simulated` y, en una terminal propia, `SIMULATED_SCENARIO=partido_en_vivo uv run --directory backend retake sync`. La consola muestra `bp initial_load: success`, las cuatro fichas de equipo (`bp initial_load 4`, `743`, `26`, `14`) y, desde el primer minuto, `bp live` y `bp live 900`; a los 5 min el partido acaba 3-1 (`/api/matches`). Parar con Ctrl+C. **Escenario 2:** repetir con `SIMULATED_SCENARIO=fuente_caida`: 2 min de `failure` y después `success`. En modo `fixtures`, `retake sync` se niega con un mensaje. |
| F6 (T-063) | Con el backend en marcha: `curl -N http://localhost:8000/api/stream` → primero `retry: 5000` y cada 15 s un `event: heartbeat`. `http://localhost:8000/api/freshness` devuelve los 8 conjuntos con `lastChangedAt` y `stale`. |
| F7 (T-069) | **Crear la cuenta:** `uv run --directory backend retake set-admin-password` (tecleas el usuario y la contraseña; no se muestra ni queda en el historial). **Bloqueo con curl:** 5 veces `curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/api/admin/login -H "X-Retake-Admin: 1" -H "Origin: http://localhost:8000" -H "Content-Type: application/json" -d '{"username":"x","password":"mala"}'` → cinco `401`; la sexta, aunque las credenciales sean las buenas, `429`. |
| F8 (T-083) | `http://localhost:5173/admin`: pantalla de acceso dentro del marco, sin entrada en el menú; entrar, ver fuentes, registro y resúmenes; "Cerrar sesión". `http://localhost:5173/dev/block-demo`: bloque en vivo con su hora y, con `source-mode simulated` + `retake sync`, cambios de marcador sin recargar. Pie con el año y los enlaces a las tres fuentes. |
| F9 | Checklist de seguridad (abajo), esta guía completa, y los pendientes que dependen del calendario (abajo). |

---

## 2.1 Origen de los datos, carga inicial y entornos

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-1 | Prueba | pt `tests/unit/sync/test_planner.py tests/integration/sync/test_runner.py` | Todo lo de BreakingPoint llega sin intervención (planificador → conector → ingesta); la Wiki solo por importación. |
| RF-2 | Prueba | pt `tests/integration/ingest` | La ingesta aplica prioridad, validación, correcciones y curación de la 002 a todo dato de una fuente. |
| RF-3 | Prueba | pt `tests/integration/sync/test_simulated_e2e.py -k vida_completa` | Con la base vacía, la carga inicial trae la temporada con sus partidos, también los finalizados. |
| RF-4 | Terminal | `uv run --directory backend retake import-wiki-csv` | Importa el historial completo y los datos personales de sus jugadores. |
| RF-4a | Prueba | pt `tests/unit/sources/test_wiki_csv.py -k datos_personales` | De `players_birthday.csv` solo entran los jugadores del historial o de un roster. |
| RF-4b | Terminal | La misma orden | Muestra `Resultado: success/partial/failure` e incidencias; queda en `sync_run` (fuente `wiki`, tipo `history`). |
| RF-4c | Prueba | pt `tests/integration/ingest/test_003_wiki_import.py -k roto` | Un archivo o una columna que falta: no se registra nada y se nombra el archivo. |
| RF-5 | — | — | Sin efecto (C-16). |
| RF-6 | Prueba | pt `tests/integration/ingest/test_matches.py -k temporada` | Entre temporadas, la actual es la última con partidos oficiales (reglas de la 002). |
| RF-7 | Prueba | vt `src/live` | Los bloques muestran lo ya cargado; lo que falta no bloquea nada. |
| RF-8 | Prueba | pt `tests/integration/api/test_003_api.py -k sin_ninguna_consulta` | Sin consultas todavía, nada sale "sin actualizar" y lo que falta es "sin datos" (404 en la temporada, listas vacías). |
| RF-9 | Prueba | pt `tests/integration/sync/test_worker.py -k produccion` | En producción no arranca con la fuente simulada ni con datos ficticios. |
| RF-10 | Prueba | `grep -rn "real_client\|breakingpoint.gg" backend/tests` | Ninguna prueba crea un cliente real; todas usan transportes simulados. |
| RF-11 | Terminal | `uv run --directory backend retake source-mode simulated` | En desarrollo se puede elegir `fixtures`, `real` o `simulated`; fuera de desarrollo se niega. |
| RF-12 | Prueba | pt `tests/integration/sync/test_source_mode.py` | Al cambiar de modo se borran la liga guardada y el registro, las incidencias y los resúmenes del modo anterior; la cuenta de administración, sus sesiones y el bloqueo por intentos se conservan (C-27). |
| RF-13 | Prueba | La misma | Se programa una carga inicial nueva (o se cargan los datos de prueba en `fixtures`). |
| RF-14 | Prueba | pt `tests/integration/sync/test_simulated_e2e.py -k cambio_de_temporada` | El calendario de la próxima temporada se obtiene y se guarda. |
| RF-15 | Prueba | pt `tests/integration/api/test_003_api.py -k proxima_temporada` | Ninguna ruta devuelve datos de la próxima temporada. |

## 2.2 Ciclos de consulta

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-16 | Prueba | pt `tests/unit/sync/test_planner.py -k en_vivo` y pt `tests/integration/sync/test_worker.py -k en_vivo` | Cada partido en vivo cada 60 s, antes que la cola de partidos terminados. |
| RF-17 | Prueba | pt `tests/unit/sync/test_planner.py -k antes_del_partido` | Cada 60 s desde 1 h antes de la hora y mientras no empiece. |
| RF-18 | Prueba | pt `tests/unit/sync/test_planner.py -k resto` y pt `tests/integration/sync/test_worker.py -k fichas` | El "Resto" cada hora, con las fichas de equipo (tabla, rosters y jugadores). |
| RF-18a | Prueba | pt `tests/unit/sources/test_bp_unlisted.py -k "tabla_se_registra or conocidos"` y pt `tests/integration/ingest/test_003_unlisted.py -k "sin_listar or nombre_antiguo or identidades_nuevas"` | Un equipo que la fuente ya no lista pero está en la tabla entra como franquicia, antes que sus partidos; unido a su nombre siguiente, los partidos de la temporada llevan el antiguo y no se crean identidades de más (C-22). En la base real: Boston Breach con sus 37 partidos. |
| RF-18b | Prueba | pt `tests/unit/sources/test_bp_unlisted.py -k invitado` y pt `tests/integration/sync/test_guest_refresh.py` | Un equipo que no está en la tabla entra como invitado; su ficha y las de sus jugadores, al aparecer y después una vez al mes; si falla, con el siguiente listado (C-24). En la base real: 4 invitados y 9 partidos. |
| RF-18c | Prueba | pt `tests/integration/ingest/test_003_unlisted.py -k "ajeno or siguen_rechazando"` y pt `tests/integration/sync/test_runner.py -k ajeno` | El roster de un equipo que no es de la CDL ni invitado se descarta sin anotarlo; las demás referencias desconocidas se siguen rechazando (C-26). |
| RF-19 | Prueba | pt `tests/unit/domain/test_review_windows.py` y pt `tests/unit/sync/test_planner.py -k recien_finalizado` | Al finalizar, o al registrarse ya finalizado, se consulta su página una vez (C-25). |
| RF-20 | Prueba | pt `tests/integration/sync/test_worker.py -k "tres_dias or reinicie or antiguo"` | Otra consulta a las 24, 48 y 72 horas, guardada en la base (un reinicio no repite nada); ninguna si el partido ya llevaba más de 3 días jugado (C-25). En la base real: los 281 partidos de julio, sin revisiones. |
| RF-21 | Prueba | pt `tests/unit/sync/test_planner.py -k "tres_revisiones or fallo_se_repite"` | Después, solo si lo pide el administrador; una consulta que falla se repite a la hora. |
| RF-22 | Prueba | pt `tests/integration/sync/test_runner.py -k con_exito` | Lo nuevo o cambiado se registra al terminar la consulta. |
| RF-23 | Prueba | pt `tests/unit/sync/test_planner.py -k prioridad` | Si no caben todos, el prioritario cada 60 s… |
| RF-24 | Prueba | La misma | …y los demás cada 2 min. |
| RF-25 | Prueba | pt `tests/unit/domain/test_live_priority.py` | El partido del spotlight es el prioritario. |
| RF-26 | Prueba | La misma | Sin spotlight, el de hora de inicio más temprana. |
| RF-27 | Prueba | pt `tests/integration/sync/test_simulated_e2e.py -k parada` | Tras una parada, el en vivo al día en el primer ciclo. |
| RF-28 | Prueba | pt `tests/unit/sync/test_planner.py -k recuperacion` | El resto de datos, en la primera hora. |
| RF-29 | Prueba | La misma | Solo el estado actual, sin los valores intermedios. |

## 2.3 Historial de campeonatos

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-30, RF-31, RF-33 | — | — | Eliminados (C-17). |
| RF-32 | Prueba | `grep -rn "wiki" backend/app/sync` | El proceso automático no consulta la Wiki; sus datos solo entran por `import-wiki-csv`. |
| RF-34 | — | — | Sin efecto (C-16). |

## 2.4 Buen uso de las fuentes

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-35 | Prueba | pt `tests/unit/sources/test_http.py -k robots` | Se leen y se cumplen las normas para robots de cada fuente. |
| RF-36 | Prueba | pt `tests/unit/sources/test_bp.py` | BreakingPoint por su API interna JSON y sus páginas públicas. |
| RF-37 | Prueba | pt `tests/unit/sources/test_http.py -k retake` | Cada consulta se identifica como Retake, nunca como navegador. |
| RF-38 | Prueba | `grep -rn "fandom" backend/app` | Ninguna consulta a la Wiki (solo aparece la atribución en el pie del frontend). |
| RF-39 | Prueba | pt `tests/unit/sources/test_http.py -k pausa` | 2 s entre dos consultas a BreakingPoint. |
| RF-40 | Prueba | pt `tests/unit/domain/test_timing.py` | Pausas y ciclos dentro de los límites publicados. |
| RF-41 | Prueba | pt `tests/integration/sync/test_worker.py -k peticion` | Las peticiones del administrador pasan por la misma cola, con la misma pausa. |
| RF-42 | Prueba | pt `tests/unit/sources/test_http.py -k prohibe` | Una consulta prohibida no se hace (`forbidden`). |

## 2.5 Fallos, formatos y desapariciones

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-43 | Prueba | pt `tests/integration/sync/test_runner.py -k fallida` | Una consulta fallida no borra nada. |
| RF-44 | Prueba | pt `tests/integration/sync/test_worker.py -k colas` | Una cola por fuente; un fallo no frena a las demás. |
| RF-45 | Prueba | pt `tests/integration/sync/test_simulated_e2e.py -k caida` | Se repite en el siguiente ciclo y se recupera. |
| RF-46 | Prueba | pt `tests/integration/sync/test_simulated_e2e.py -k vacia` | Un listado vacío donde había datos cuenta como fallo y conserva los datos. |
| RF-47 | Prueba | pt `tests/integration/sync/test_runner.py -k parcial` | Se registra lo entendido; la consulta queda parcial. |
| RF-48 | Prueba | pt `tests/integration/ingest/test_003_unreadable.py` | Un dato ilegible cede el turno a la siguiente fuente. |
| RF-49 | Prueba | La misma | Si ninguna lo publica legible, se conserva el valor registrado. |
| RF-50 | Prueba | pt `tests/integration/sync/test_runner.py -k desaparec` | 24 h sin aparecer en listados con éxito → desaparecido; el detalle de otro partido no cuenta. |
| RF-51 | Prueba | pt `tests/integration/ingest/test_003_sightings.py` | Se conserva tal cual, también en vivo. |
| RF-52 | Prueba | La misma | Si reaparece, se actualiza como el mismo partido. |
| RF-53 | Prueba | pt `tests/integration/ingest/test_003_live_and_cancel.py -k cancel` | Una cancelación solo de una fuente secundaria no borra el partido. |

## 2.6 Enlace entre fuentes, marcador en vivo y datos de Retake

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-54 | Prueba | pt `tests/integration/ingest/test_003_curation.py` | Solo se une lo que una fuente relaciona o une la curación (`merges`). |
| RF-55 | Prueba | pt `tests/integration/ingest/test_003_retention.py` | Lo no enlazado de una fuente secundaria queda retenido: no sale en las listas de la temporada; el historial sí lo usa (C-14). |
| RF-56 | Prueba | pt `tests/integration/ingest/test_003_curation.py -k libera` · Terminal `retake list-retained` | Unir o `confirmed_new` lo libera; `list-retained` solo sugiere. |
| RF-57 | Prueba | pt `tests/integration/ingest/test_003_live_and_cancel.py -k mas_avanzado` | En vivo manda el marcador más avanzado de cualquier fuente. |
| RF-58 | Prueba | pt `tests/unit/domain/test_live_score.py` | Más mapas; si empatan, más puntos del mapa en curso. |
| RF-59 | Prueba | pt `tests/integration/ingest/test_003_live_and_cancel.py -k retrocede` | Nunca retrocede. |
| RF-60 | Prueba | pt `tests/integration/ingest/test_003_personal_removal.py` | Un jugador retirado no recibe datos personales, ni un instante. |

## 2.7 Identidades y logos

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-61 | Prueba | pt `tests/integration/ingest/test_003_identities.py -k una_sola` | Una sola identidad vigente con dos fuentes. |
| RF-62 | Prueba | pt `tests/unit/domain/test_identity_merge.py` | Cada campo, de la fuente con más prioridad que lo publica, también la fecha. |
| RF-63 | Prueba | pt `tests/integration/ingest/test_003_identities.py -k cambio_real` | Solo nace una identidad nueva si cambia el resultado combinado. |
| RF-64 | Prueba | vt `src/league/rules.test.js` | Sin logo tras combinar, las reglas de logo ausente de la 002. |
| RF-65 | Prueba | pt `tests/integration/api/test_003_api.py -k logo_se_sirve` | El logo se copia y `logoUrl` apunta a `/api/logos/{huella}`. |
| RF-66 | Prueba | pt `tests/integration/ingest/test_003_identities.py -k identica` | Una imagen idéntica se guarda una vez. |
| RF-67 | Prueba | pt `tests/integration/ingest/test_003_identities.py -k imagen_nueva` | Imagen nueva en la misma dirección = logo nuevo. |
| RF-68 | Prueba | pt `tests/unit/sources/test_logos.py` | Solo PNG, JPEG y WebP (nunca SVG). |
| RF-69 | Prueba | La misma | Hasta 1 MB. |
| RF-70 | Prueba | pt `tests/integration/api/test_003_api.py -k sin_copia` | Sin copia válida, logo no registrado (`logoUrl: null`). |
| RF-71 | Prueba | pt `tests/integration/ingest/test_003_identities.py -k conserva` | Si la fuente deja de publicarlo, se usa la copia. |

## 2.8 Temporada actual y año del pie

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-72 | Prueba | pt `tests/integration/sync/test_simulated_e2e.py -k cambio_de_temporada` | El cambio de temporada sale solo de los datos de las fuentes. |
| RF-73 | Prueba | pt `tests/integration/ingest/test_matches.py` | Un partido pertenece a la temporada de su evento. |
| RF-74 | Navegador | `http://localhost:5173` | El pie muestra "Temporada 2026" (de `/api/season/current`). |
| RF-75 | Prueba | vt `src/layout/footer.test.jsx` | Cambia en 5 min como máximo. |
| RF-76 | Prueba | La misma | Sin año hasta obtenerlo. |
| RF-77 | Prueba | La misma | Lo añade al obtenerlo. |
| RF-78 | Prueba | La misma | Si luego falla, mantiene el año. |

## 2.9 Actualización de las páginas abiertas

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-79 | Navegador | `/dev/block-demo` con `source-mode simulated` + `retake sync` (escenario `partido_en_vivo`) | El marcador cambia sin recargar. |
| RF-80 | Prueba | vt `src/live/useLiveBlock.test.jsx` | Recarga al avisar el canal y al menos cada 30 s en vivo. |
| RF-81 | Prueba | La misma | El resto, al menos cada 5 min. |
| RF-82 | Prueba | vt `src/live/liveChannel.test.js` y `src/live/useLiveBlock.test.jsx` | Al volver a la pestaña, al día en 5 s como máximo. |
| RF-83 | Navegador | Demostración: hacer scroll y poner el foco en un control; esperar un cambio | Scroll y foco se conservan (el bloque no se vuelve a montar). |
| RF-84 | Navegador | La misma | La vista no se desplaza. |
| RF-85 | Prueba | vt `src/live/useLiveBlock.test.jsx -t "sin esqueleto"` | Sin esqueleto al actualizar. |
| RF-86 | Prueba | vt `src/live/useLiveBlock.test.jsx -t "falla"` | Conserva los datos. |
| RF-87 | Prueba | La misma | Sin aviso de error ni "Reintentar". |
| RF-88 | Prueba | La misma | Lo intenta en el siguiente ciclo. |
| RF-89 | Prueba | vt `src/live/freshnessRules.test.js` · pt `tests/integration/api/test_003_api.py -k frescura` | Aviso si el servidor dice "sin actualizar" o el canal lleva cortado más que el umbral. |
| RF-90 | Prueba | pt `tests/integration/api/test_003_api.py -k 60_s` | Partido en vivo sin aparecer más de 60 s → `isStale`. |
| RF-91 | Prueba | vt `src/pages/dev/LiveDemoBlock.test.jsx -t "sin retirar"` | El aviso no retira el contenido. |
| RF-92 | Prueba | vt `src/live/freshnessRules.test.js -t "se retira"` | Se retira al volver a actualizarse. |
| RF-93 | Navegador | Demostración con la fuente caída (`fuente_caida`) | El aviso no dice qué falló. |
| RF-94 | Prueba | pw `e2e/dev/live.spec.js` | Auditoría WCAG 2.2 AA sin incumplimientos. |
| RF-95 | Prueba | vt `src/live/LiveAnnouncer.test.jsx` y `src/pages/dev/LiveDemoBlock.test.jsx -t anuncia` | Anuncia los cambios en vivo sin interrumpir (`aria-live="polite"`). |
| RF-96 | Prueba | vt `src/live/LiveAnnouncer.test.jsx -t nunca` | Nunca anuncia el resto de datos. |

## 2.10 Página de administración

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-97 | Prueba | pw `e2e/admin.spec.js` (proyectos `dev` y `prod`) | La página existe también en la versión compilada. |
| RF-98 | Navegador | `http://localhost:5173/admin` | Dentro del marco común, sin entrada activa en el menú. |
| RF-99 | Navegador | La misma | Ninguna entrada del menú lleva a `/admin`. |
| RF-100 | Navegador | Entrar y pulsar "Actualizar BreakingPoint.gg" (con `retake sync` en marcha) | Se lanza sin esperar al ciclo (listado y después fichas de equipo). |
| RF-101 | Prueba | pt `tests/integration/admin/test_003_admin.py -k wiki` | La Wiki no se puede actualizar desde la página. |
| RF-102 | — | — | Eliminado (C-19). |
| RF-103 | Prueba | vt `src/admin/AdminPage.test.jsx -t "en curso"` | Muestra "En curso"/"Pendiente". |
| RF-104 | Prueba | La misma | Después, "Éxito", "Parcial" o "Fallo". |
| RF-105 | Prueba | pt `tests/integration/sync/test_runner.py -k parcial` | Parcial = alguna consulta con éxito y alguna incidencia. |
| RF-106 | Prueba | vt `src/admin/AdminPage.test.jsx -t "en curso"` | "Incidencias: N" y "Ver en el registro". |
| RF-107 | Prueba | pt `tests/integration/admin/test_003_admin.py -k pedir_una` | Una sola en curso por fuente. |
| RF-108 | — | — | Eliminado (C-19). |
| RF-109 | Prueba | vt `src/admin/AdminPage.test.jsx -t "ya en curso"` | "Ya había una actualización en curso de esta fuente." |
| RF-110 | Prueba | pt `tests/integration/admin/test_003_admin.py -k wiki` | Una actualización no permitida no se hace (`forbidden`). |
| RF-111 | Navegador | `/admin`, filas de la Wiki y de la CDL | Muestran el motivo en lugar del botón. |
| RF-112 | Navegador | `/admin`, "Estado de las fuentes" | Última consulta de cada fuente. |
| RF-113 | Navegador | La misma | Última con éxito; para la Wiki, "Última importación". |
| RF-114 | Prueba | pt `tests/integration/admin/test_003_admin.py -k estado` | "Parada" pasado el doble del ciclo; la Wiki nunca. |
| RF-115 | Navegador | `/admin` con el backend parado | Cada panel con las reglas de bloque de la 001 (esqueleto, error, "Reintentar"). |
| RF-116 | Prueba | vt `src/admin/AdminPage.test.jsx -t "sin conexión"` | Sin conexión, los botones de actualizar se desactivan. |
| RF-117 | Prueba | vt `src/admin/AdminPage.test.jsx -t "inglés"` | Español e inglés con las reglas de la 001. |
| RF-118 | Prueba | vt `src/admin/AdminPage.test.jsx -t "texto literal"` | Los mensajes de las fuentes, sin traducir. |
| RF-119 | Prueba | La misma | Como texto plano (el HTML se ve literal). |
| RF-120 | Prueba | pt `tests/unit/sources/test_contract.py` | Recortados a 500 caracteres, terminando en "…". |

## 2.11 Acceso del administrador

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-121 | Prueba | pt `tests/integration/admin/test_003_admin.py -k "hash or segunda"` | Una única cuenta; en la base, solo un *hash* Argon2id. |
| RF-122 | Navegador | `/admin` | No hay forma de crear cuentas. |
| RF-123 | Navegador | La misma | Ni de cambiar o recuperar la contraseña (solo `retake set-admin-password`). |
| RF-124 | Navegador | `/admin` sin sesión | Pide usuario y contraseña. |
| RF-125 | Navegador | Entrar con la cuenta creada | Se abre la sesión. |
| RF-126 | Prueba | pt `tests/integration/admin/test_003_admin.py -k sin_decir_cual` | El mismo mensaje para usuario o contraseña incorrectos. |
| RF-127 | Terminal | curl de F7 (arriba) | 5 fallos → origen bloqueado 15 min. |
| RF-128 | Prueba | pt `tests/integration/admin/test_003_admin.py -k cinco_fallos` | Cuentan los intentos con cualquier usuario. |
| RF-129 | Prueba | La misma | Bloqueado también con las credenciales correctas (`429`). |
| RF-130 | Prueba | pt `tests/integration/admin/test_003_admin.py -k "otros_origenes or proxy"` | Los demás orígenes pueden entrar. |
| RF-131 | Prueba | pt `tests/integration/admin/test_003_admin.py -k pone_a_cero` | Un acceso correcto pone el contador a cero. |
| RF-132 | Prueba | pt `tests/integration/admin/test_003_admin.py -k al_acabar` | Al acabar el bloqueo, también. |
| RF-133 | Prueba | pt `tests/integration/admin/test_003_admin.py -k cinco_fallos` | Cada bloqueo es una incidencia `origin_blocked`. |
| RF-134 | Prueba | pt `tests/integration/admin/test_003_admin.py -k 8_horas` | La sesión caduca a las 8 h. |
| RF-135 | Prueba | pt `tests/integration/admin/test_003_admin.py -k varias` | Varias sesiones a la vez. |
| RF-136 | Prueba | pt `tests/integration/sync/test_worker.py -k peticion` | La actualización se termina aunque caduque la sesión (la hace el proceso, no la sesión). |
| RF-137 | Prueba | vt `src/admin/AdminPage.test.jsx -t caduca` | Con la sesión caducada vuelve a pedir usuario y contraseña. |
| RF-138 | Prueba | pt `tests/integration/admin/test_003_admin.py -k cerrar_sesion` · pw `e2e/admin.spec.js` | "Cerrar sesión" la invalida en el servidor. |
| RF-139 | Prueba | pt `tests/integration/admin/test_003_admin.py -k "401 or falsificadas"` | Sin sesión, 401; sin la cabecera propia o desde otro origen, 403. |

## 2.12 Registro de actualizaciones y resumen diario

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-140 | Prueba | pt `tests/integration/sync/test_registry.py` | Cada consulta queda con su fuente, hora y resultado. |
| RF-141 | Prueba | pt `tests/integration/sync/test_runner.py -k fallida` | El motivo del fallo. |
| RF-142 | Prueba | pt `tests/integration/sync/test_runner.py -k "rechazados or pais"` | El dato y el motivo; el valor, solo como huella. |
| RF-143 | Prueba | pt `tests/integration/sync/test_runner.py -k prohibida` | La norma que prohíbe la consulta. |
| RF-144 | Prueba | pt `tests/integration/sync/test_runner.py -k desaparecido` | El partido desaparecido. |
| RF-145 | Prueba | pt `tests/integration/sync/test_runner.py` | Los registros retenidos nuevos. |
| RF-146 | Prueba | pt `tests/integration/sync/test_runner.py -k discrepancia` | La discrepancia de cancelación, con su partido y motivo. |
| RF-147 | Prueba | pt `tests/integration/sync/test_registry.py` | 100 repeticiones iguales = una sola entrada. |
| RF-148 | Prueba | La misma | Con el contador y la hora de la última. |
| RF-149 | Prueba | pt `tests/integration/sync/test_registry.py -k borrado` · pt `tests/integration/sync/test_worker.py -k limpieza` | Se borra a los 7 días; la limpieza corre cada hora. |
| RF-150 | Prueba | pt `tests/integration/sync/test_daily_summary.py -k medianoche` | A las 00:00 de Ciudad de México, el resumen del día. |
| RF-151 | Prueba | vt `src/admin/AdminPage.test.jsx -t detalla` | Por fuente, consultas fallidas y datos rechazados. |
| RF-152 | Prueba | La misma | Cada incidencia distinta con sus repeticiones y acceso al registro. |
| RF-153 | Prueba | pt `tests/integration/sync/test_daily_summary.py -k sin_incidencias` | Sin incidencias, sin resumen. |
| RF-154 | Prueba | pt `tests/integration/sync/test_registry.py` | El resumen se borra a los 7 días. |

## 2.13 Reglas comunes de presentación

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-155 | Prueba | vt `src/pages/dev/LiveDemoBlock.test.jsx` | El bloque muestra "Actualizado: …", también sin datos. Cada spec visual lo aplicará a sus bloques (plan D-12). |
| RF-156 | Navegador | Pie, `/admin` y el bloque de demostración de la 001 | Ninguno muestra la hora de última actualización. |
| RF-157 | Prueba | vt `src/live/freshnessRules.test.js -t "más reciente"` · pt `tests/integration/api/test_003_api.py -k changed_at` | Es el cambio más reciente de lo que se muestra (`changedAt`). |
| RF-158 | Prueba | vt `src/live/freshnessRules.test.js -t "sin datos"` | Sin datos, el último cambio del conjunto vigilado. |
| RF-159 | Prueba | pt `tests/integration/ingest/test_003_changes.py` | El primer registro de un dato cuenta como cambio. |
| RF-160 | Prueba | vt `src/layout/footer.test.jsx` · pw `e2e/footer.spec.js` | Las tres fuentes con enlace, y la licencia CC BY-SA de la Wiki, en todas las páginas. |

---

## Cambios en la spec 002 surgidos en la 003 (C-23, C-25)

| RF de la 002 | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-117a | Prueba | pt `tests/integration/ingest/test_003_unlisted.py -k invitado` | Un equipo invitado es una franquicia marcada como invitada, con sus identidades y su roster. |
| RF-117b | Prueba | pt `tests/unit/sources/test_bp_unlisted.py -k ficha_mensual` | Sus jugadores, con los mismos datos que los de la CDL. |
| RF-117c | Prueba | pt `tests/integration/api/test_003_guests.py` | Solo en sus partidos, marcado (`isGuest`, `teamIsGuest`): nunca en la tabla ni en las listas de franquicias o jugadores. |
| RF-117d | Prueba | pt `tests/integration/ingest/test_003_unlisted.py -k deja_de_serlo` | Si entra en la lista de la liga, deja de ser invitado y conserva sus identidades. |
| §2, plazos de corrección | Prueba | Las de RF-19 a RF-21 de la 003 | Las correcciones de un partido llegan hasta 3 días después de finalizar (C-25). |

## Checklist de seguridad (constitución §6, plan §9, T-084)

| Vector | Comprobación | Resultado (2026-09-23) |
|---|---|---|
| Inyección SQL | `grep -rnE "text\(|exec_driver_sql" backend/app` | Solo consultas fijas; `pg_notify` con parámetros y nombres de una lista cerrada; `LISTEN` con un nombre fijo. |
| XSS | `grep -rnE "dangerouslySetInnerHTML|innerHTML" src` | Ninguno. Los mensajes de las fuentes se ven literales (RF-119). |
| Logos | `tests/unit/sources/test_logos.py`, `/api/logos/{id}` | Pillow verifica la imagen; solo PNG/JPEG/WebP ≤ 1 MB; se sirven con su tipo real y `nosniff`. |
| Contraseña | `tests/integration/admin/test_003_admin.py` | Argon2id; nunca en claro, ni como argumento, ni en registros. |
| Sesiones | La misma | 32 bytes aleatorios; solo su huella en la base; cookie `HttpOnly`, `SameSite=Strict`, `Path=/api/admin`, `Secure` en producción; 8 h. |
| Fuerza bruta | La misma | 5 fallos bloquean el origen 15 min; `X-Forwarded-For` solo con `TRUSTED_PROXY`. |
| Peticiones falsificadas | La misma | Cabecera `X-Retake-Admin: 1` y mismo origen en toda petición que cambia algo. |
| Acceso | La misma | Todas las rutas `/api/admin` salvo `login` exigen sesión; `/docs` desactivado en producción. |
| Carga sobre las fuentes | `tests/unit/sources/test_http.py`, `tests/integration/sync/test_worker.py` | Pausa, identificación, `robots.txt` y ciclos por partido; la Wiki no se consulta. |
| Datos personales | `tests/integration/ingest/test_003_personal_removal.py`, `registry.py` | La retirada es permanente; el registro guarda solo la huella de un valor rechazado. La IP de un origen bloqueado se guarda 7 días en su incidencia. |
| Credenciales | `git check-ignore -v backend/.env backend/data/wiki/players_birthday.csv` | Ambos ignorados; `.env.example` sin valores. |
| Datos de prueba en producción | `tests/integration/sync/test_worker.py -k produccion` | El proceso se niega a arrancar. |
| **Resuelto (I-35)** | `backend/curation/curation.yaml` y `fixtures.yaml` | La curación real y la de los datos de prueba van en archivos distintos; cada modo de fuente usa la suya y las dos se validan en modo estricto. |

## Pendiente que depende del calendario o de Hugo

| Tarea | Qué falta |
|---|---|
| T-086 | Recorrido en modo `real` con `retake sync` durante al menos un ciclo de cada tipo que la temporada permita (resto y próxima temporada), revisando el registro y `/admin`. |
| T-087 | Que Hugo confirme cada fila de esta guía. |
| T-089 | Medir con un partido real en vivo el ciclo de 60 s, la ventana previa de 1 h y el margen de 30 s en pantalla (criterio 3 de la spec). |
| T-094 | Repetir la exploración del en vivo y de la próxima temporada cuando BreakingPoint publique el calendario de 2027. |
| T-090 | Cierre de la spec, cuando todo lo anterior esté hecho. |
| Curación | Unir jugadores Wiki ↔ BreakingPoint y rellenar `countries` tras una carga real (`retake list-retained`). |
| RF-75 de la 002 | Incumplido mientras la web de la CDL esté en reserva (F0-3): decidir si se acepta así. |
