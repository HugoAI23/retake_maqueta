# Tasks: Obtención y Actualización de los Datos de la Liga

- **Spec**: [`spec.md`](spec.md) (`Aprobado`, 2026-09-23, con la revisión R-1)
- **Plan**: [`plan.md`](plan.md) (`Aprobado`, 2026-09-23)
- **Fecha**: `2026-09-23`
- **Estado**: `Aprobado` (aprobado por Hugo el 2026-09-23). En implementación: **F0, F1, F2 y F3 completadas** el 2026-09-23 (el acceso en vivo a la Wiki de I-17 se retiró con I-26). **F4 completada** el 2026-09-23 (T-037 a T-048 y T-091 a T-093). **F4b completada** el 2026-09-23 (importación de la Wiki por CSV, cambios C-15 a C-21; Hugo importó sus CSV reales: 14 campeonatos, 284 clasificaciones, 168 franquicias y 515 jugadores). **F5 a F8 completadas** el 2026-09-23 (F5 revisada según el plan, I-27). **F9:** T-084, T-085 y T-088 hechas; quedan T-086 y T-087 (Hugo), T-089 y T-094 (calendario) y T-090. Ajustes en el registro del plan, I-1 a I-34.

Checklist de tareas atómicas, en orden de ejecución. Cada tarea indica los requisitos que cubre (**RF**), de qué tareas depende (**Dep.**) y cuándo se considera terminada (**Hecho cuando**).

## Reglas de ejecución

1. **Orden:** las tareas se hacen en orden. Una tarea no empieza hasta que sus dependencias estén marcadas.
2. **Alcance cerrado:** solo se implementa lo que dice cada tarea (constitución §1.2). Si aparece un imprevisto, se detiene el trabajo y se consulta a Hugo; si cambia algo, se actualizan la spec y el plan (constitución §1.3).
3. **Regla P-1 de la spec:** si una fuente impide cumplir un requisito (normas, bloqueo o datos que no publica), se detiene el desarrollo de ese requisito y se consulta a Hugo, sin rebajarlo por cuenta propia.
4. **Pruebas primero:** en las tareas que dicen "Pruebas e implementación", las pruebas se escriben antes que el código y deben fallar antes de implementarlo.
5. **Sin internet en las pruebas:** ninguna prueba automática consulta las fuentes reales (RF-10). Los conectores se prueban con muestras recortadas y el transporte simulado de httpx (BreakingPoint) o `responses` (Wiki, con requests).
6. **Cierre de fase:** cada fase termina con una tarea de cierre, que exige:
   - todas las pruebas automáticas en verde (`uv run pytest` en `backend/` y `npm test` en la raíz);
   - la guía de verificación manual de la fase entregada a Hugo (constitución §5.1);
   - un mensaje de commit sugerido. El commit lo hace Hugo: el agente no ejecuta comandos de git que modifiquen el repositorio (constitución §8).
7. **Documentación del código:** en Python, docstrings en español; en JavaScript, comentarios JSDoc en español. Los nombres de código van en inglés (constitución §7).
8. **Tiempo en las pruebas:** el reloj se inyecta siempre; ninguna prueba espera tiempo real ni depende del reloj del sistema (plan §6.2).
9. **Credenciales:** el agente nunca escribe, pide ni guarda la contraseña del administrador. La crea Hugo con `retake set-admin-password`.

## Dependencias externas

| Qué | Lo aporta | Afecta a | Mientras tanto |
|---|---|---|---|
| Decisiones sobre los huecos que encuentre la exploración de las fuentes (regla P-1) | Hugo | T-007 | No se empieza F3. |
| Tabla de países (número de BreakingPoint → nombre) y uniones de jugadores Wiki ↔ BreakingPoint en `curation.yaml` | Hugo (curación manual, I-3 e I-6) | Guías de F4 y F5 | Países `No disponible` y jugadores de la Wiki retenidos, que son comportamientos válidos. |
| Contraseña del administrador | Hugo, con `retake set-admin-password` | Guías de F7 y F8 | Las pruebas automáticas usan una cuenta de prueba creada por ellas mismas. |
| Un partido real de la CDL en vivo (criterio 3 del §6 de la spec) | El calendario de la liga: la temporada 2026 terminó en julio y la 2027 no ha empezado | T-089 | El resto se verifica con la fuente simulada. La spec no puede cerrarse hasta medirlo o hasta que Hugo decida otra cosa. |
| Máquina encendida con `retake sync` en modo real | Hugo | T-086, T-089 | Se usa la fuente simulada. |

---

## F0 — Exploración de las fuentes

- [x] **T-001** BreakingPoint: localizar dónde está cada dato de la 002 en `/matches`, `/match/{id}` y las páginas de equipos y jugadores (temporadas, eventos, fases, franquicias, identidades y logos, rosters, jugadores y datos personales, partidos, mapas, estadísticas por modo, marcador en vivo, próxima temporada). Pocas consultas, identificado como Retake y con la pausa de 2 s.
  - **RF:** RF-1, RF-14, RF-36, RF-37, RF-39
  - **Dep.:** —
  - **Hecho cuando:** `source-map.md` (nuevo, en la carpeta de la spec) tiene la tabla de BreakingPoint: dato de la 002 → página y campo, o "no lo publica".
- [x] **T-002** Wiki: la misma tabla con sus consultas estructuradas (torneos, calendario, resultados y premios de campeonatos, rosters, jugadores y datos personales, mapas y estadísticas), solo a través de la API y con el parámetro de cortesía de MediaWiki. Comprobar si publica marcadores en vivo.
  - **RF:** RF-1, RF-4, RF-34, RF-38
  - **Dep.:** —
  - **Hecho cuando:** `source-map.md` tiene la tabla de la Wiki.
- [x] **T-003** Web de la CDL: localizar la petición interna con la que la página de posiciones carga la tabla (decisión H-3), y comprobar si la web publica marcadores en vivo.
  - **RF:** RF-1, RF-16
  - **Dep.:** —
  - **Hecho cuando:** `source-map.md` tiene la tabla de la CDL. Si no hay petición interna, se anota y se pasa a T-006 (el plan B exige volver a preguntar a Hugo).
  - **Resultado:** JSON de la tabla con dirección variable y CMS inestable; la CDL queda en reserva (I-4).
- [x] **T-004** Enlaces entre fuentes: medir si las fuentes se relacionan entre sí (identificadores de otra fuente, enlaces `same_as`) para partidos, eventos, franquicias y jugadores, y estimar cuántos registros quedarían retenidos por temporada.
  - **RF:** RF-54, RF-55
  - **Dep.:** T-001, T-002, T-003
  - **Hecho cuando:** `source-map.md` tiene la estimación de registros retenidos por tipo.
- [x] **T-005** Guardar las muestras recortadas de cada tipo de respuesta en `backend/tests/snapshots/<fuente>/`, solo con los campos usados y con su fuente, dirección y fecha de consulta (plan D-16).
  - **RF:** RF-10
  - **Dep.:** T-001, T-002, T-003
  - **Hecho cuando:** hay al menos una muestra por tipo de consulta de §5 del plan, incluida una de partido en vivo si alguna fuente la ofrece fuera de temporada. Si no, se anota como hueco.
- [x] **T-006** Informe de exploración para Hugo: datos que ninguna fuente publica, requisitos afectados (regla P-1), carga de retenidos estimada y, si hace falta, el plan B de la tabla de la CDL.
  - **RF:** —
  - **Dep.:** T-004, T-005
  - **Hecho cuando:** Hugo ha decidido sobre cada hueco y las decisiones están anotadas en el registro del plan (§12).
- [x] **T-007 · Cierre F0**
  - **Dep.:** T-001 a T-006
  - **Hecho cuando:** `source-map.md` está completo, las decisiones de T-006 están tomadas y se ha sugerido el commit.

---

## F1 — Dependencias, configuración y modelo de datos

- [x] **T-008** Añadir con uv las dependencias de H-1, H-2, H-7 y H-9: httpx (de desarrollo pasa a principal), requests (Wiki, I-1), beautifulsoup4, argon2-cffi y pillow; y como dependencia de desarrollo, responses (pruebas de requests sin internet).
  - **RF:** —
  - **Dep.:** T-007
  - **Hecho cuando:** `uv sync` instala todo y las pruebas de la 002 siguen en verde.
- [x] **T-009** `app/config`: variables nuevas: `SOURCE_MODE` (`fixtures`, `real` o `simulated`), `TRUSTED_PROXY` (opcional). La cookie de sesión va con `Secure` en producción. La configuración rechaza `simulated` y `fixtures` en producción. Añadirlas a `.env.example`, sin valores secretos.
  - **RF:** RF-9, RF-11
  - **Dep.:** T-008
  - **Hecho cuando:** pruebas de configuración en verde, incluido el rechazo en producción.
- [x] **T-010** Migración, parte de ingesta: `external_ref.last_seen_at` y `retained_since`; `observation.invalid_reason` (`impossible` o `unreadable`); `changed_at` en las tablas resueltas; `match.stats_complete_at` y `disappeared_at`.
  - **RF:** RF-48 a RF-52, RF-55, RF-157
  - **Dep.:** T-008
  - **Hecho cuando:** la migración se aplica sobre una base de datos con los datos de prueba de la 002 sin perder nada.
- [x] **T-011** Migración, parte de logos y frescura: `logo_image`, `identity.logo_image_id` y `dataset_change`.
  - **RF:** RF-65 a RF-71, RF-155, RF-158
  - **Dep.:** T-010
  - **Hecho cuando:** la migración se aplica y se deshace sin errores.
- [x] **T-012** Migración, parte de obtención: `source_state`, `sync_job`, `sync_request`, `sync_run`, `incident` (única por fuente, tipo, dato, valor y motivo), `incident_day` y `daily_summary`, con listas cerradas mediante CHECK (como en la 002).
  - **RF:** RF-100 a RF-114, RF-140 a RF-154
  - **Dep.:** T-011
  - **Hecho cuando:** la migración se aplica y se deshace sin errores.
- [x] **T-013** Migración, parte de administración: `admin_user` (una sola fila), `admin_session` (solo el *hash* del identificador) y `login_origin`.
  - **RF:** RF-121, RF-125, RF-127, RF-134
  - **Dep.:** T-012
  - **Hecho cuando:** la migración se aplica y se deshace sin errores.
- [x] **T-014** Pruebas del esquema: todas las tablas y columnas nuevas existen; las restricciones rechazan valores fuera de las listas cerradas; `admin_user` no admite una segunda fila.
  - **RF:** RF-121
  - **Dep.:** T-013
  - **Hecho cuando:** las pruebas pasan desde una base de datos vacía.
- [x] **T-015 · Cierre F1**
  - **Dep.:** T-008 a T-014
  - **Hecho cuando:** las pruebas están en verde, se ha entregado la guía manual (tablas nuevas en `psql`) y se ha sugerido el commit.

---

## F2 — Reglas de dominio

- [x] **T-016** `domain/vocabulary`: umbrales (60 s y 1 h; ciclos de página de 30 s y 5 min) como constantes únicas. *(Las listas cerradas —tipos de consulta, resultados, tipos de incidencia, conjuntos de datos, formatos de logo— se adelantaron a F1 porque las necesitaban las restricciones de la migración; registro del plan I-9.)*
  - **RF:** RF-16, RF-18, RF-89
  - **Dep.:** T-015
  - **Hecho cuando:** los modelos y las migraciones importan de aquí las listas cerradas.
- [x] **T-017** Pruebas e implementación de `live_score`: más mapas terminados y, si empatan, más puntos del mapa en curso; nunca retrocede; solo mientras el partido está en vivo.
  - **RF:** RF-57 a RF-59
  - **Dep.:** T-016
  - **Hecho cuando:** cubre fuentes contradictorias, marcador ausente y empate exacto.
- [x] **T-018** Pruebas e implementación de `cancellation`: la cancelación solo vale si la publica la fuente de mayor prioridad entre las que publican el partido; en otro caso, devuelve "discrepancia".
  - **RF:** RF-53
  - **Dep.:** T-016
  - **Hecho cuando:** cubre las combinaciones de las tres fuentes.
- [x] **T-019** Pruebas e implementación de `identity_merge`: combinación campo a campo (con la fecha de vigencia) según la prioridad de la 002, y si el resultado combinado cambió.
  - **RF:** RF-61 a RF-63
  - **Dep.:** T-016
  - **Hecho cuando:** un cambio solo en una fuente secundaria que no altera el resultado no produce una identidad nueva.
- [x] **T-020** Pruebas e implementación de `review_windows`: revisar cada hora mientras haya estadísticas pendientes y durante 7 días desde que se completan; después, no.
  - **RF:** RF-19 a RF-21
  - **Dep.:** T-016
  - **Hecho cuando:** cubre el partido sin mapas (forfeit) y los límites exactos de los 7 días.
- [x] **T-021** Pruebas e implementación de `disappearance`: desaparecido tras 24 h sin aparecer en ninguna consulta con éxito de las fuentes que lo publicaban; en vivo sin aparecer más de 60 s.
  - **RF:** RF-50, RF-90
  - **Dep.:** T-016
  - **Hecho cuando:** una consulta fallida no cuenta como "no aparecer".
- [x] **T-022** Pruebas e implementación de `freshness`: conjunto sin actualizar a partir de su última consulta con éxito y su umbral; fuente parada si pasa más del doble de su ciclo más corto sin consultas.
  - **RF:** RF-89, RF-114
  - **Dep.:** T-016
  - **Hecho cuando:** cubre los dos umbrales y el cambio de ciclo cuando empieza o acaba un partido en vivo.
- [x] **T-023** Pruebas e implementación de `live_priority`: con varios partidos en vivo que no caben en 60 s, el prioritario (el del spotlight o, sin su spec, el de hora de inicio más temprana) cada 60 s y los demás cada 2 min.
  - **RF:** RF-23 a RF-26
  - **Dep.:** T-016
  - **Hecho cuando:** cubre el empate de hora de inicio con un desempate estable.
- [x] **T-024 · Cierre F2**
  - **Dep.:** T-016 a T-023
  - **Hecho cuando:** las pruebas están en verde, se ha entregado la guía y se ha sugerido el commit.

---

## F3 — Conectores, logos y fuente simulada

- [x] **T-025** `sources/http`: cliente por fuente (httpx para BreakingPoint, requests para la Wiki, I-1) con identificación de Retake, pausa mínima por fuente (2 s; Wiki 10 s con espera creciente ante `ratelimited`, I-2), tiempo de espera de 15 s y lectura de las normas para robots si la fuente las publica. Una consulta prohibida devuelve `forbidden` sin hacerse.
  - **RF:** RF-35, RF-37, RF-39, RF-40, RF-42
  - **Dep.:** T-024
  - **Hecho cuando:** pruebas con transporte simulado comprueban la cabecera, la pausa medida con el reloj simulado y la negativa ante una norma que prohíbe.
- [x] **T-026** Contrato del resultado de consulta (plan §3.1): `outcome`, `records`, `seen`, `rejected` y `message` en texto plano de 500 caracteres como máximo; marca de campo ilegible (plan §3.2).
  - **RF:** RF-47, RF-48, RF-119, RF-120
  - **Dep.:** T-025
  - **Hecho cuando:** `records.py` acepta la marca de ilegible y las pruebas de la 002 siguen en verde.
- [x] **T-027** Pruebas e implementación del conector de BreakingPoint, listado: `/matches` (temporadas, también la próxima; eventos, solo los de la CDL; franquicias e identidades con logo) y API interna `fetchMatchesPage` paginada (partidos con estado, horario, formato, marcador, ronda → fase y origen del bracket), con las referencias vistas. Una respuesta sin partidos donde antes había cuenta como fallo.
  - **RF:** RF-1, RF-14, RF-16, RF-17, RF-46, RF-47
  - **Dep.:** T-026
  - **Hecho cuando:** traduce las muestras de T-005 y marca como ilegible lo que no entiende.
- [x] **T-028** Pruebas e implementación del conector de BreakingPoint, detalle de partido (`/match/{id}`): mapas jugados, mapas no jugados (a partir de `fetchGameBans`, I-7), modos, marcadores, marcador en vivo y estadísticas por jugador y modo.
  - **RF:** RF-1, RF-16, RF-19
  - **Dep.:** T-027
  - **Hecho cuando:** traduce las muestras y distingue una estadística ausente de un 0.
- [x] **T-029** Pruebas e implementación de BreakingPoint, equipos y jugadores: `/teams/{id}` (tabla: puesto y puntos) y `/players/{id}` (datos personales, `country_id`, retirada e historial de equipos → rosters).
  - **RF:** RF-1, RF-18
  - **Dep.:** T-027
  - **Hecho cuando:** traduce las muestras; los jugadores retirados no entran en el roster.
- [x] **T-030** Pruebas e implementación del conector de la Wiki, jugadores (I-3): `Players` y `PlayerRedirects` (datos personales y gamertags anteriores) con requests, solo por la API, de una en una, con el parámetro de cortesía y la pausa de I-2.
  - **RF:** RF-1, RF-18, RF-38
  - **Dep.:** T-026
  - **Hecho cuando:** traduce las muestras, nunca pide una página web de la Wiki y respeta la espera creciente ante `ratelimited`.
- [x] **T-031** *(No aplica tras F0, I-3: los rosters salen de BreakingPoint y los jugadores de la Wiki van en T-030.)*
  - **RF:** RF-1, RF-18
  - **Dep.:** T-030
  - **Hecho cuando:** traduce las muestras.
- [x] **T-032** Pruebas e implementación del conector de la Wiki, historial, con `action=parse` y BeautifulSoup (I-1): campeonatos, clasificaciones, premios, porcentaje de la bolsa, rosters con el gamertag de la final y datos personales de los jugadores que solo están en el historial. Reutiliza la lógica de `get_tables_champs_all_years.py` de `CDL-data-analysis` (columnas dinámicas, filas de mostrar/ocultar).
  - **RF:** RF-4, RF-34
  - **Dep.:** T-030
  - **Hecho cuando:** traduce las muestras, incluidos un lugar compartido y un `DQ`.
- [x] **T-033** *(No aplica tras F0, I-4: la web de la CDL queda en reserva y la tabla sale de BreakingPoint en T-029.)*
  - **RF:** RF-1, RF-18
  - **Dep.:** T-026
  - **Hecho cuando:** traduce las muestras, incluidas las posiciones compartidas.
- [x] **T-034** Pruebas e implementación de `logos/`: descarga con el cliente educado; Pillow verifica que es PNG, JPEG o WebP; 1 MB como máximo; huella SHA-256 para no duplicar; un logo no válido se rechaza con su motivo.
  - **RF:** RF-65 a RF-70
  - **Dep.:** T-025
  - **Hecho cuando:** rechaza un SVG, un GIF, un archivo de más de 1 MB y un falso PNG, y guarda una sola vez dos descargas idénticas.
- [x] **T-035** `sources/simulated`: formato de escenario (respuestas de las tres fuentes que cambian con el reloj) y escenarios del plan §6.4. El proceso de obtención se niega a arrancar con ella en producción.
  - **RF:** RF-9 a RF-11
  - **Dep.:** T-027 a T-033
  - **Hecho cuando:** cada escenario se reproduce igual dos veces seguidas con el reloj simulado.
- [x] **T-036 · Cierre F3**
  - **Dep.:** T-025 a T-035
  - **Hecho cuando:** las pruebas están en verde, la guía incluye una consulta real de cada fuente con `sync-once` (sin guardar) y se ha sugerido el commit.

---

## F4 — Ingesta ampliada y curación

- [x] **T-037** Pruebas e implementación de "ilegible" frente a "imposible": un ilegible cede el turno a la siguiente fuente; si ninguna lo publica de forma legible, se conserva el valor registrado; un imposible sigue pasando a ausente.
  - **RF:** RF-48, RF-49
  - **Dep.:** T-036
  - **Hecho cuando:** cubre las tres situaciones y las pruebas de la 002 siguen en verde.
- [x] **T-038** `changed_at` en cada fila cuyo valor resuelto cambia, y registro de los conjuntos de datos cambiados en `dataset_change` y en el informe de la ingesta.
  - **RF:** RF-157 a RF-159
  - **Dep.:** T-036
  - **Hecho cuando:** reingerir los mismos datos no mueve `changed_at`, y el primer registro de un dato sí lo fija.
- [x] **T-039** `last_seen_at` de las referencias vistas en cada consulta con éxito; partido desaparecido a las 24 h y reaparecido cuando vuelve.
  - **RF:** RF-50 a RF-52
  - **Dep.:** T-038
  - **Hecho cuando:** un partido desaparecido se conserva tal cual, también en vivo, y vuelve a actualizarse al reaparecer.
- [x] **T-040** Marcador en vivo con `live_score` en el cálculo del partido; al finalizar, el marcador final vuelve a la prioridad de fuentes.
  - **RF:** RF-57 a RF-59
  - **Dep.:** T-036
  - **Hecho cuando:** el marcador en vivo nunca retrocede aunque la fuente principal vaya por detrás.
- [x] **T-041** Cancelación con `cancellation`; si no se aplica, se informa la discrepancia.
  - **RF:** RF-53
  - **Dep.:** T-036
  - **Hecho cuando:** una cancelación de una fuente secundaria no borra el partido.
- [x] **T-042** Identidades combinadas con `identity_merge` (sustituye el ajuste I-15 de la 002). El logo de la identidad es la copia propia; sin logo tras combinar, rigen las reglas de logo ausente de la 002; un logo que la fuente deja de publicar se conserva.
  - **RF:** RF-61 a RF-65, RF-71
  - **Dep.:** T-036
  - **Hecho cuando:** dos fuentes con identidades distintas dan una sola identidad vigente, y las pruebas de I-15 se actualizan con el motivo anotado en el registro del plan.
- [x] **T-043** Registros retenidos: una referencia sin enlazar, cuando una fuente de mayor prioridad publica ese tipo, queda retenida y no forma parte de ninguna entidad visible; se informa.
  - **RF:** RF-54, RF-55
  - **Dep.:** T-036
  - **Hecho cuando:** un partido de la Wiki sin enlace no duplica el de BreakingPoint y aparece como retenido.
- [x] **T-044** Curación: secciones `merges` (partidos, eventos y franquicias) y `confirmed_new`, con validación; al unir o confirmar, el registro deja de estar retenido.
  - **RF:** RF-54, RF-56
  - **Dep.:** T-043
  - **Hecho cuando:** unir o confirmar libera el registro, y un error de formato no aplica nada (como en la 002).
- [x] **T-045** Retirada permanente: el cálculo de un jugador con los datos retirados ignora los datos personales que publiquen las fuentes.
  - **RF:** RF-60
  - **Dep.:** T-036
  - **Hecho cuando:** reingerir un jugador retirado no devuelve ningún dato personal, ni un instante.
- [x] **T-046** `stats_complete_at`: se fija cuando un partido finalizado tiene todas sus estadísticas registradas.
  - **RF:** RF-19, RF-20
  - **Dep.:** T-038
  - **Hecho cuando:** un forfeit sin mapas lo tiene desde que finaliza.
- [x] **T-047** Orden `retake list-retained`: lista los retenidos y sugiere candidatos parecidos, sin unir nada.
  - **RF:** RF-54, RF-56
  - **Dep.:** T-044
  - **Hecho cuando:** una prueba comprueba que la orden no cambia ningún dato.
- [x] **T-091** Pruebas e implementación del K/D calculado (C-12): si ninguna fuente lo publica, kills ÷ deaths con 2 decimales; con 0 deaths, K/D = kills; si falta alguno, ausente.
  - **RF:** RF-2 (RF-79 de la 002 revisado)
  - **Dep.:** T-036 (C-12 aplicado a la 002 el 2026-09-23)
  - **Hecho cuando:** cubre 0 deaths, kills ausente y un K/D publicado, que manda sobre el calculado.
- [x] **T-092** Pruebas e implementación de la semana calculada (C-13): orden de la semana (lunes a domingo, hora de Ciudad de México) entre las semanas con partidos del evento, solo si la fuente no publica la semana.
  - **RF:** RF-2 (RF-31 de la 002 revisado)
  - **Dep.:** T-036 (C-13 aplicado a la 002 el 2026-09-23)
  - **Hecho cuando:** con los partidos de la muestra del clasificatorio del Major 1, da "semana 1" y "semana 4" donde la Wiki dice "Week 1" y "Week 4", incluido el parón navideño.
- [x] **T-093** Tabla de países en la curación (I-6): sección `countries` (número de BreakingPoint → nombre) con validación; un número sin traducir es `No disponible` y se anota como incidencia.
  - **RF:** RF-2, RF-142
  - **Dep.:** T-044
  - **Hecho cuando:** un jugador con un número sin traducir aparece sin país y con su incidencia.
- [x] **T-048 · Cierre F4**
  - **Dep.:** T-037 a T-047, T-091 a T-093
  - **Hecho cuando:** las pruebas de la 002 y de la 003 están en verde, se ha entregado la guía y se ha sugerido el commit.

---

## F4b — Importación de la Wiki por CSV (cambios C-15 a C-21, I-26)

> Tareas nuevas del 2026-09-23, **aprobadas por Hugo el mismo día**. Sustituyen el acceso en vivo a la Wiki.

- [x] **T-095** Configuración: `WIKI_CSV_DIR` (por defecto `backend/data/wiki/`), carpeta ignorada por git y documentada en `.env.example`.
  - **RF:** RF-4, RF-4a
  - **Dep.:** T-048
  - **Hecho cuando:** la ruta se lee de la configuración y `git status` no muestra los CSV copiados en la carpeta.
- [x] **T-096** Pruebas e implementación de `sources/wiki_csv` (lectura y conversión), con CSV de prueba ficticios:
  - una clasificación por año y equipo con su roster, y el premio del equipo, nunca por jugador;
  - campeonato con identificador de página, competición y juego por año, fecha de la final y completado si hay 1.er puesto;
  - lugares con rango (`9-12`) y `DQ` tal cual; premio y porcentaje vacíos, ausentes; ilegibles, marcados como ilegibles;
  - datos personales solo de los jugadores del historial o de un roster (RF-4a); `Stream`, `Twitter` y `Age` nunca se leen;
  - archivo que falta o columna que falta → error que nombra el archivo, sin registros.
  - **RF:** RF-4 a RF-4c, RF-7 de la 002
  - **Dep.:** T-095
  - **Hecho cuando:** los registros pasan la validación del contrato de la 002 y cada caso tiene su prueba.
- [x] **T-097** Orden `retake import-wiki-csv [--dir RUTA]`: registros → `ingest_records` con la curación vigente, en una sola transacción (sin `apply_curation`, I-26); muestra el resultado (éxito, parcial o fallo) y sus incidencias, y lo anota en `sync_run` (`wiki`, `history`).
  - **RF:** RF-4b, RF-4c, RF-32
  - **Dep.:** T-096
  - **Hecho cuando:** una prueba de integración importa los CSV ficticios dos veces sin duplicar nada, y un archivo roto no deja ningún cambio en la base de datos.
- [x] **T-098** Retirar el acceso en vivo a la Wiki (C-18): `sources/wiki.py` (la tabla `GAMES` y los nombres de los campeonatos pasan a `wiki_csv`), el adaptador TLS y el cliente real de la Wiki en `sources/http.py`, `sync-once --source wiki`, sus pruebas y muestras, y la dependencia `requests` (y `responses` si ya no la usa ninguna prueba).
  - **RF:** RF-38
  - **Dep.:** T-097
  - **Hecho cuando:** `grep` no encuentra en `app/` ninguna dirección de la Wiki ni `requests`, y todas las pruebas siguen en verde.
- [x] **T-099 · Cierre F4b**: guía de verificación (copiar los CSV, importar, comprobar el historial en la API y `list-retained`), sugerencia de commit y registro del plan al día.
  - **Dep.:** T-095 a T-098
  - **Hecho cuando:** Hugo ha importado sus CSV reales en su base de desarrollo y lo ha comprobado.

---

## F5 — Proceso de obtención

- [x] **T-049** Pruebas e implementación de `sync/planner` (función pura), con cada consulta del plan §5:
  - carga inicial en orden (temporada antes que historial; entre temporadas, la última con partidos oficiales);
  - en vivo, antes del partido, resto cada hora, partidos terminados y próxima temporada;
  - ~~relecturas del Champs a 1 h y de 24 h a 168 h, y reintentos cada hora~~ (eliminadas por C-17, I-26: el historial llega con `retake import-wiki-csv`);
  - resumen diario y limpieza;
  - recuperación tras una parada.
  - **RF:** RF-3, RF-6, RF-14, RF-16 a RF-21, RF-23 a RF-29, RF-150
  - **Dep.:** T-048
  - **Hecho cuando:** cada fila del §5 del plan tiene su prueba con el reloj simulado.
- [x] **T-050** `sync/registry`:
  - una entrada por consulta;
  - incidencias sin repeticiones (contador y última repetición), con repeticiones por día de Ciudad de México;
  - nunca guarda el valor de un dato personal;
  - borrado a los 7 días de la última repetición.
  - **RF:** RF-140 a RF-149
  - **Dep.:** T-048
  - **Hecho cuando:** 100 repeticiones iguales dejan una sola incidencia con contador 100.
- [x] **T-051** `sync/runner`: conector → ingesta → curación → registro → estado de la fuente → aviso de cambios. Anota la desaparición, la retención, la discrepancia de cancelación y las consultas prohibidas.
  - **RF:** RF-22, RF-43 a RF-47, RF-141 a RF-146
  - **Dep.:** T-049, T-050
  - **Hecho cuando:** una consulta fallida no borra nada y no frena a las demás fuentes.
- [x] **T-052** `sync/notify`: aviso `NOTIFY` con los conjuntos de datos cambiados, de una lista cerrada.
  - **RF:** RF-80, RF-81
  - **Dep.:** T-051
  - **Hecho cuando:** una prueba de integración recibe el aviso en otra conexión.
- [x] **T-053** `sync/worker` y orden `retake sync`:
  - bucle de 5 s con una cola por fuente;
  - recoge las peticiones del administrador (`sync_request`), con una sola en curso por fuente (sin relectura del historial: C-19, I-26);
  - termina lo empezado aunque caduque la sesión que lo pidió;
  - se niega a arrancar en producción con la fuente simulada o con datos ficticios.
  - **RF:** RF-9, RF-44, RF-100, RF-107, RF-136
  - **Dep.:** T-051, T-052
  - **Hecho cuando:** las pruebas cubren las colas, las peticiones y la negativa en producción.
- [x] **T-054** Resumen diario a las 00:00 de `America/Mexico_City`: totales y lista de incidencias distintas por fuente; sin resumen si no hubo incidencias; borrado a los 7 días.
  - **RF:** RF-150 a RF-154
  - **Dep.:** T-050
  - **Hecho cuando:** cubre un día sin incidencias y el paso de medianoche con el reloj simulado.
- [x] **T-055** Órdenes `retake sync-once --source <fuente>` (una consulta para depurar) y `retake source-mode <modo>` (en desarrollo: borra los datos de la liga y programa una carga inicial). Añadir `retake-sync` a `.claude/launch.json`.
  - **RF:** RF-11 a RF-13
  - **Dep.:** T-053
  - **Hecho cuando:** `source-mode` se niega fuera de desarrollo y, en desarrollo, deja la base de datos solo con el modo elegido.
- [x] **T-056** Pruebas de integración de punta a punta con la fuente simulada y el reloj simulado:
  - vida completa de un partido en vivo;
  - varios partidos en vivo con prioridad;
  - fuente caída y respuesta vacía;
  - dato ilegible;
  - desaparición y reaparición;
  - parada y recuperación;
  - cambio de temporada automático, con la próxima temporada oculta hasta entonces;
  - ~~final del Champs con clasificación tardía y sus relecturas~~ (eliminado por C-17; la importación se prueba en T-097).
  - **RF:** RF-3, RF-6 a RF-29, RF-43 a RF-53, RF-72, RF-73
  - **Dep.:** T-053 a T-055
  - **Hecho cuando:** todos los escenarios pasan.
- [x] **T-057 · Cierre F5**
  - **Dep.:** T-049 a T-056
  - **Hecho cuando:** las pruebas están en verde, la guía recorre dos escenarios con `retake sync` en modo simulado y se ha sugerido el commit.

---

## F6 — API ampliada y eventos del servidor

- [x] **T-058** `changedAt` en todas las respuestas de la 002 e `isStale` en cada partido (en vivo sin aparecer en las fuentes).
  - **RF:** RF-90, RF-157
  - **Dep.:** T-057
  - **Hecho cuando:** las pruebas de la API de la 002 siguen en verde con los campos nuevos.
- [x] **T-059** `GET /api/freshness`: `lastChangedAt` y `stale` por conjunto de datos.
  - **RF:** RF-89, RF-155, RF-158
  - **Dep.:** T-058
  - **Hecho cuando:** cubre un conjunto al día, uno sin actualizar y uno sin datos.
- [x] **T-060** `GET /api/logos/{id}`: la copia con su tipo real, `X-Content-Type-Options: nosniff` y caché larga; el `logoUrl` de las identidades apunta a la copia.
  - **RF:** RF-65, RF-71
  - **Dep.:** T-058
  - **Hecho cuando:** un identificador inexistente da 404 y la respuesta lleva las cabeceras.
- [x] **T-061** `GET /api/stream`: escucha los avisos (`LISTEN`) y emite `change`, `freshness` y un latido cada 15 s, con `retry: 5000`. Configurar el proxy de Vite para que deje pasar la conexión abierta.
  - **RF:** RF-79 a RF-81, RF-89
  - **Dep.:** T-059
  - **Hecho cuando:** una prueba de integración recibe un `change` tras una ingesta, y otra comprueba el latido a través del proxy de Vite.
- [x] **T-062** Comprobar que ninguna ruta devuelve datos de la próxima temporada.
  - **RF:** RF-15
  - **Dep.:** T-058
  - **Hecho cuando:** con partidos de la próxima temporada guardados, ninguna respuesta los incluye.
- [x] **T-063 · Cierre F6**
  - **Dep.:** T-058 a T-062
  - **Hecho cuando:** las pruebas están en verde, la guía muestra el canal de eventos con `curl` y se ha sugerido el commit.

---

## F7 — Administración (backend)

- [x] **T-064** Contraseñas con Argon2id y orden `retake set-admin-password`: pide usuario y contraseña sin mostrarla, nunca los recibe como argumento y solo existe una cuenta.
  - **RF:** RF-121 a RF-123
  - **Dep.:** T-063
  - **Hecho cuando:** las pruebas comprueban que en la base de datos solo hay un *hash* Argon2id y que una segunda cuenta se rechaza.
- [x] **T-065** Pruebas e implementación del bloqueo por origen:
  - el origen es la IP del cliente, o la cabecera del proxy solo si `TRUSTED_PROXY` está configurado;
  - 5 fallos seguidos con cualquier usuario bloquean 15 min, también a las credenciales correctas;
  - el bloqueo no afecta a otros orígenes;
  - el contador vuelve a cero con un acceso correcto o al acabar el bloqueo;
  - cada bloqueo se anota como incidencia.
  - **RF:** RF-126 a RF-133
  - **Dep.:** T-064
  - **Hecho cuando:** cubre cada caso con el reloj simulado.
- [x] **T-066** Sesiones:
  - identificador aleatorio de 32 bytes y solo su *hash* guardado;
  - cookie `HttpOnly`, `SameSite=Strict`, limitada a `/api/admin` y con `Secure` en producción;
  - caducidad a las 8 h y varias sesiones a la vez;
  - "Cerrar sesión" invalida la sesión en el servidor.
  - **RF:** RF-124, RF-125, RF-134, RF-135, RF-137, RF-138
  - **Dep.:** T-064
  - **Hecho cuando:** una sesión cerrada o caducada responde 401.
- [x] **T-067** Protección contra peticiones falsificadas (plan D-11): toda petición de administración que cambia algo exige la cabecera `X-Retake-Admin: 1` y el mismo origen.
  - **RF:** RF-139
  - **Dep.:** T-066
  - **Hecho cuando:** una petición sin la cabecera o desde otro origen se rechaza.
- [x] **T-068** Rutas de §3.4 del plan:
  - `login`, `logout` y `me`;
  - `sources`: última consulta, última con éxito y fuente parada;
  - `sources/{source}/refresh` y `history/reread`: una sola en curso y motivo si las normas lo prohíben;
  - `requests/{id}`: éxito, parcial o fallo, con el número de incidencias;
  - `log` y `summaries`.

  Todas responden 401 sin sesión y devuelven los textos de las fuentes como texto plano recortado.
  - **RF:** RF-100 a RF-114, RF-118 a RF-120, RF-139 a RF-154
  - **Dep.:** T-065 a T-067
  - **Hecho cuando:** cada ruta tiene sus pruebas de integración, incluida la respuesta 401.
- [x] **T-069 · Cierre F7**
  - **Dep.:** T-064 a T-068
  - **Hecho cuando:** las pruebas están en verde, la guía incluye crear la cuenta (Hugo teclea su contraseña) y probar el bloqueo con `curl`, y se ha sugerido el commit.

---

## F8 — Frontend

- [x] **T-070** `src/live/liveChannel`: una conexión de eventos por pestaña; se cierra al ocultarse y se reabre al volver; da el canal por cortado si no llega un latido en 45 s.
  - **RF:** RF-79, RF-82, RF-89
  - **Dep.:** T-069
  - **Hecho cuando:** pruebas con un canal y una visibilidad simulados.
- [x] **T-071** `src/live/useLiveBlock`, sobre el cargador de la 001:
  - la primera carga sigue sus reglas;
  - después recarga en silencio cuando el canal avisa: sin esqueleto, conservando los datos si falla y reintentando en el siguiente ciclo de la página;
  - al volver a verse la pestaña, recarga en 5 s como máximo;
  - conserva el estado de la página y no desplaza la vista.
  - **RF:** RF-79 a RF-88
  - **Dep.:** T-070
  - **Hecho cuando:** las pruebas cubren cada caso y las pruebas de la 001 siguen en verde.
- [x] **T-072** `src/live/freshnessRules` y `leagueApi.getFreshness`: `lastUpdatedOf`, `isStale` (el servidor lo dice, o el canal lleva cortado más que el umbral) y `formatLastUpdated` en los dos idiomas. El aviso se retira al volver a actualizarse.
  - **RF:** RF-89, RF-91 a RF-93, RF-155 a RF-159
  - **Dep.:** T-070
  - **Hecho cuando:** pruebas de las funciones en español y en inglés.
- [x] **T-073** `src/live/LiveAnnouncer`: anuncia sin interrumpir los cambios de datos en vivo, y nunca los del resto de datos.
  - **RF:** RF-94 a RF-96
  - **Dep.:** T-071
  - **Hecho cuando:** pruebas de la región accesible y de su silencio con el resto de datos.
- [x] **T-074** Bloque de demostración en vivo en la página de demostración de la 001 (solo en desarrollo, fuera del menú): muestra partidos de la fuente simulada con su hora de última actualización, el aviso de datos sin actualizar y los anuncios en vivo, para verificar RF-79 a RF-96 y RF-155 a RF-159 mientras no exista ninguna spec visual que los use. Anotar el añadido en el registro del plan (§12).
  - **RF:** RF-79 a RF-96, RF-155 a RF-159
  - **Dep.:** T-071 a T-073
  - **Hecho cuando:** fuera de desarrollo la dirección da "Página no encontrada" (RF-95 de la 001).
- [x] **T-075** Diccionarios `es` y `en`: textos de la página de administración, del acceso, de los resultados y de la atribución.
  - **RF:** RF-117, RF-118
  - **Dep.:** T-069
  - **Hecho cuando:** la prueba de diccionarios de la 001 confirma que los dos idiomas tienen las mismas claves.
- [x] **T-076** `src/admin/adminApi`: cliente de las rutas de §3.4 con la cabecera de D-11; un 401 lleva a la pantalla de acceso.
  - **RF:** RF-124, RF-137, RF-139
  - **Dep.:** T-069
  - **Hecho cuando:** pruebas con respuestas simuladas.
- [x] **T-077** Ruta `/admin` dentro del marco común, sin entrada en el menú ni entrada activa: pantalla de acceso (mensaje único ante credenciales incorrectas) y "Cerrar sesión".
  - **RF:** RF-97 a RF-99, RF-124 a RF-126, RF-138
  - **Dep.:** T-075, T-076
  - **Hecho cuando:** pruebas de componentes y de rutas.
- [x] **T-078** Paneles de administración como bloques de la 001:
  - estado de las fuentes (última consulta, última con éxito, parada);
  - acciones (actualizar fuente; sin releer historial por C-19), desactivadas sin conexión; la Wiki muestra su última importación y nunca aparece como parada;
  - resultado de cada petición (en curso, éxito, parcial o fallo, con el número de incidencias).
  - **RF:** RF-100 a RF-116
  - **Dep.:** T-077
  - **Hecho cuando:** pruebas de cada estado, incluida la petición ya en curso y la prohibida.
- [x] **T-079** Paneles de registro y resúmenes: incidencias con repeticiones y última hora; mensajes de las fuentes sin traducir y como texto plano.
  - **RF:** RF-118 a RF-120, RF-140 a RF-154
  - **Dep.:** T-077
  - **Hecho cuando:** un mensaje con HTML se ve literal.
- [x] **T-080** Pie de página, año de la temporada desde `/api/season/current`:
  - sin año hasta obtenerlo;
  - lo mantiene si luego falla;
  - lo cambia en 5 min como máximo cuando cambia la temporada.

  Se elimina el valor provisional de `src/config/season.js`.
  - **RF:** RF-74 a RF-78
  - **Dep.:** T-070
  - **Hecho cuando:** pruebas de los tres casos; las pruebas del pie de la 001 se actualizan con el motivo anotado en el registro del plan.
- [x] **T-081** Pie de página, atribución: nombre de las tres fuentes con un enlace a cada una (y a la licencia CC BY-SA del texto de la Wiki), en todas las páginas y con el contraste AA de la 001.
  - **RF:** RF-160
  - **Dep.:** T-080 (C-11 aplicado a la 001 el 2026-09-23)
  - **Hecho cuando:** aparece en las páginas de sección, "Próximamente", "Página no encontrada" y administración.
- [x] **T-082** Pruebas de extremo a extremo (Playwright + axe):
  - acceso, bloqueo y cierre de sesión;
  - año y atribución en el pie;
  - actualización en vivo y aviso de datos sin actualizar en el bloque de demostración con la fuente simulada, a través del proxy de Vite;
  - auditoría WCAG 2.2 AA de la administración y del bloque de demostración.
  - **RF:** RF-79 a RF-99, RF-124 a RF-139, RF-160
  - **Dep.:** T-074, T-078 a T-081
  - **Hecho cuando:** todo en verde en desarrollo y en producción.
- [x] **T-083 · Cierre F8**
  - **Dep.:** T-070 a T-082
  - **Hecho cuando:** las pruebas están en verde (también las de la 001 y la 002), se ha entregado la guía y se ha sugerido el commit.

---

## F9 — Cierre

- [x] **T-084** Checklist de seguridad del plan §9:
  - sin SQL concatenado, sin HTML sin escapar;
  - contraseña solo como *hash* Argon2id; sesión con sus banderas; bloqueo por origen; protección D-11;
  - imágenes verificadas; `.env` fuera de git;
  - negativa a usar la fuente simulada y los datos ficticios en producción;
  - ningún dato personal en el registro;
  - documentación de la API desactivada en producción.
  - **RF:** RF-9, RF-60, RF-68 a RF-70, RF-119 a RF-139
  - **Dep.:** T-083
  - **Hecho cuando:** cada punto está comprobado y anotado en la guía.
- [x] **T-085** Ejecutar todas las pruebas: pytest, `npm test` y `npm run test:e2e`.
  - **RF:** —
  - **Dep.:** T-084
  - **Hecho cuando:** todo está en verde.
- [ ] **T-086** Recorrido manual en modo real: `retake sync` durante al menos un ciclo de cada tipo que la temporada permita (resto y próxima temporada; el historial, con `retake import-wiki-csv`, I-26), revisando el registro y la página de administración.
  - **RF:** RF-1 a RF-42, RF-112 a RF-114
  - **Dep.:** T-085
  - **Hecho cuando:** Hugo lo ha comprobado en la página de administración.
- [ ] **T-087** Redactar `verification-guide.md` de la 003, con una fila por RF (constitución §5) y los escenarios de la fuente simulada que exige el criterio 4 de la spec.
  - **RF:** todos
  - **Dep.:** T-086
  - **Hecho cuando:** Hugo confirma cada fila, salvo las del partido real (T-089).
- [x] **T-088** Sincronizar la spec y el plan con los cambios surgidos durante la implementación, en el registro del plan (constitución §1.3).
  - **RF:** —
  - **Dep.:** T-087
  - **Hecho cuando:** la spec, el plan y el código coinciden.
- [ ] **T-094** Repetir la exploración del en vivo y de la próxima temporada en cuanto BreakingPoint publique el calendario de 2027: estructura de las listas `upcoming_live`, marcador en vivo del partido y de su mapa en curso. Ajustar el conector y la fuente simulada si difieren, anotándolo en el registro del plan (I-7).
  - **RF:** RF-14, RF-16, RF-17, RF-57
  - **Dep.:** T-088 y la dependencia externa del partido real
  - **Hecho cuando:** hay muestras reales de un partido en vivo y de la próxima temporada, y las pruebas pasan con ellas.
- [ ] **T-089** Medición con un partido real de la CDL en vivo: ciclo de 60 s, ventana previa de 1 h y margen de pantalla de 30 s (criterio 3 de la spec).
  - **RF:** RF-16, RF-17, RF-80
  - **Dep.:** T-094
  - **Hecho cuando:** Hugo ha comprobado los tres tiempos en un partido real.
- [ ] **T-090 · Cierre de la spec 003**
  - **Dep.:** T-084 a T-089
  - **Hecho cuando:** todas las pruebas están en verde, se ha sugerido el commit final y Hugo aprueba el cierre de la spec 003.

---

## Trazabilidad RF → tareas

| RF | Tareas |
|---|---|
| RF-1 | T-001 a T-003, T-027 a T-030, T-032, T-086 |
| RF-2 | T-051, T-056, T-091 a T-093 |
| RF-3 a RF-8 | T-049, T-056 |
| RF-9 | T-009, T-035, T-053, T-084 |
| RF-10 | T-005, T-035 (y la regla 5 de ejecución) |
| RF-11 a RF-13 | T-009, T-035, T-055 |
| RF-14 | T-001, T-027, T-049, T-056, T-094 |
| RF-15 | T-056, T-062 |
| RF-16, RF-17 | T-027, T-028, T-049, T-089, T-094 |
| RF-18 | T-029, T-030, T-049 |
| RF-19 a RF-21 | T-020, T-028, T-046, T-049 |
| RF-22 | T-051 |
| RF-23 a RF-26 | T-023, T-049, T-056 |
| RF-27 a RF-29 | T-049, T-056 |
| RF-30 a RF-33 | T-049, T-056 |
| RF-34 | T-002, T-032, T-049 |
| RF-35 | T-025 |
| RF-36 | T-001 a T-003 (y la revisión R-1) |
| RF-37 | T-001, T-025 |
| RF-38 | T-002, T-030 |
| RF-39, RF-40 | T-025 |
| RF-41 | T-025, T-053 |
| RF-42 | T-025 |
| RF-43 a RF-46 | T-027, T-051, T-056 |
| RF-47 | T-026, T-027, T-051 |
| RF-48, RF-49 | T-026, T-037 |
| RF-50 a RF-52 | T-021, T-039, T-056 |
| RF-53 | T-018, T-041 |
| RF-54 a RF-56 | T-004, T-043, T-044, T-047 |
| RF-57 a RF-59 | T-017, T-040, T-094 |
| RF-60 | T-045, T-084 |
| RF-61 a RF-64 | T-019, T-042 |
| RF-65 a RF-70 | T-034, T-042, T-060 |
| RF-71 | T-042, T-060 |
| RF-72, RF-73 | T-056 |
| RF-74 a RF-78 | T-080 |
| RF-79 a RF-88 | T-061, T-070, T-071, T-074, T-082 |
| RF-89 | T-022, T-059, T-061, T-070, T-072 |
| RF-90 | T-021, T-058 |
| RF-91 a RF-93 | T-072, T-074 |
| RF-94 a RF-96 | T-073, T-074, T-082 |
| RF-97 a RF-99 | T-077, T-082 |
| RF-100 a RF-111 | T-053, T-068, T-078 |
| RF-112 a RF-114 | T-022, T-068, T-078, T-086 |
| RF-115, RF-116 | T-078 |
| RF-117 | T-075 |
| RF-118 a RF-120 | T-026, T-068, T-075, T-079 |
| RF-121 a RF-123 | T-013, T-014, T-064 |
| RF-124 a RF-133 | T-065, T-066, T-077 |
| RF-134 a RF-138 | T-066, T-077 |
| RF-136 | T-053 |
| RF-139 | T-067, T-068, T-076 |
| RF-140 a RF-149 | T-050, T-051, T-068, T-079, T-093 |
| RF-150 a RF-154 | T-049, T-054, T-068, T-079 |
| RF-155 a RF-159 | T-038, T-059, T-072, T-074 |
| RF-160 | T-081, T-082 |
