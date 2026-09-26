# Tasks: Tablas de Datos y Posiciones

- **Spec**: [`spec.md`](spec.md) (`Aprobado`, 2026-09-25, con la revisión QA-1 a QA-30 y el cambio C-29 a la 002)
- **Plan**: [`plan.md`](plan.md) (`Aprobado`, 2026-09-25)
- **Fecha**: `2026-09-25`
- **Estado**: `Aprobado` (aprobado por Hugo el 2026-09-25). En curso: F0 a F4 hechas; F5 hasta T-033. Guía comprobada por Hugo el 2026-09-26 (pruebas de todas las fases en verde y navegador con datos reales y con retake_guia); quedan RF-30, RF-51 y RF-51a con datos reales, que dependen del calendario. Por decisión de Hugo (2026-09-26), la 004 sigue abierta hasta que empiece la temporada 2027, en diciembre (como la 003); entonces se comprueban esas filas y se hace T-034. Ajustes del plan: I-1 a I-8; QA-30 en la spec.

Checklist de tareas atómicas, en orden de ejecución. Cada tarea indica los requisitos que cubre (**RF**), de qué tareas depende (**Dep.**) y cuándo se considera terminada (**Hecho cuando**). Los RF sin más indicación son de la 004; los de la 002 y la 003 se citan con su spec.

## Reglas de ejecución

1. **Orden:** las tareas se hacen en orden. Una tarea no empieza hasta que sus dependencias estén marcadas.
2. **Alcance cerrado:** solo se implementa lo que dice cada tarea (constitución §1.2). Si aparece un imprevisto, se detiene el trabajo y se consulta a Hugo; si cambia algo, se actualizan la spec y el plan (constitución §1.3). Un cambio a la spec aprobada se presenta y se aprueba por separado.
3. **Pruebas primero:** en las tareas que dicen "Pruebas e implementación", las pruebas se escriben antes que el código y deben fallar antes de implementarlo.
4. **Sin internet en las pruebas:** ninguna prueba automática consulta las fuentes reales. Las de extremo a extremo simulan la API en el navegador.
5. **Tiempo en las pruebas:** las animaciones se prueban con el reloj falso de Vitest o con "reducir movimiento" forzado; ninguna prueba espera tiempo real.
6. **Datos:** la base `retake` (datos reales, con `retake sync` en marcha) solo se lee. La verificación con los datos de prueba usa la base aparte `retake_guia` (guía de la 002). Los datos de prueba compartidos (`backend/fixtures/`, `backend/curation/fixtures.yaml`) no se cambian: los casos especiales se crean dentro de cada prueba.
7. **Procesos:** si hay que parar un proceso, solo por su PID exacto; nunca el `retake sync` de Hugo.
8. **Cierre de fase:** cada fase termina con una tarea de cierre, que exige:
   - las pruebas automáticas de la fase en verde;
   - la guía de verificación manual de la fase entregada a Hugo (constitución §5.1);
   - un mensaje de commit sugerido. El commit lo hace Hugo: el agente no ejecuta comandos de git que modifiquen el repositorio (constitución §8).
9. **Documentación del código:** en Python, docstrings en español; en JavaScript, comentarios JSDoc en español. Los nombres de código van en inglés (constitución §7).

## Dependencias externas

| Qué | Lo aporta | Afecta a | Mientras tanto |
|---|---|---|---|
| Datos reales de la temporada 2026 en `retake` (tabla, partidos con invitados en el CDL Major 3, Boston Breach / M80 Boston) | Ya cargados (spec 003) | T-032 (criterio 3) | — |
| Confirmación de cada fila de la guía | Hugo | T-032, T-034 | La 004 no se cierra. |

---

## F0 — Preparación

- [x] **T-001** Pruebas e implementación de los colores nuevos `positive` y `highlight` en `designTokens.js`, con sus parejas en la prueba de contraste: `positive` sobre `surface` y `bg`, y `text`, `positive` y `danger` sobre `highlight`.
  - **RF:** RF-22, RF-30, RF-35
  - **Dep.:** —
  - **Hecho cuando:** la prueba de contraste exige 4,5:1 en cada pareja nueva y pasa.
- [x] **T-002** Pruebas e implementación de los textos de la tabla y de Posiciones en español e inglés (plan §3.4). Incluye una prueba nueva que compara las claves de `standings.*` y `tables.*` en los dos diccionarios.
  - **RF:** RF-40, RF-42, RF-48
  - **Dep.:** T-001
  - **Hecho cuando:** cada clave nueva existe en los dos diccionarios y la prueba lo comprueba.
- [x] **T-003** Pruebas e implementación de la forma `table` de `BlockSkeleton`: filas y columnas de marcador de posición, sin texto y oculta a los lectores como las demás formas.
  - **RF:** RF-24
  - **Dep.:** T-001
  - **Hecho cuando:** `<BlockSkeleton shape="table" />` se pinta con forma de tabla y las formas existentes no cambian.
- [x] **T-004 · Cierre F0**
  - **Dep.:** T-001 a T-003
  - **Hecho cuando:** las pruebas están en verde, se ha entregado la guía y se ha sugerido el commit.

## F1 — Backend: balance e identidad de cada fila

- [x] **T-005** Pruebas e implementación de `domain/season_balance` (función pura):
  - serie para el ganador y derrota para el rival;
  - mapas ganados propios y perdidos del rival;
  - sin ganador pero con marcador, gana el lado con más mapas (D-5);
  - con ganador y sin marcador, cuenta la serie y no los mapas;
  - sin ganador ni marcador, no cuenta;
  - los partidos contra invitados cuentan para el equipo de la liga;
  - un equipo sin partidos queda en `0–0`;
  - sin ningún partido en la temporada, el balance es "no disponible" (D-6).
  - **RF:** RF-136 a RF-139 de la 002 (con RF-138a)
  - **Dep.:** T-004
  - **Hecho cuando:** cada regla tiene su prueba y todas pasan.
- [x] **T-006** Consultas en `db/queries`:
  - partidos `finalizado` de la temporada actual con la franquicia de cada lado, el ganador y el marcador;
  - último partido `en vivo` o `finalizado` de cada franquicia en la temporada actual, por su fecha y hora de inicio programadas.
  - **RF:** RF-41a, RF-136 de la 002
  - **Dep.:** T-005
  - **Hecho cuando:** sus pruebas de integración pasan con partidos creados en la propia prueba.
- [x] **T-007** Pruebas e implementación de la identidad de cada fila en `standing_views`:
  - la del último partido jugado en la temporada;
  - si la franquicia no ha jugado ninguno, la vigente.
  - Incluye un caso tipo Boston Breach / M80 Boston, creado en la prueba: identidad nueva después del último partido de la temporada.
  - **RF:** RF-41a, RF-41b
  - **Dep.:** T-006
  - **Hecho cuando:** la fila muestra el nombre de la temporada y no el posterior; sin partidos, el vigente.
- [x] **T-008** Pruebas e implementación de `series`, `maps` y `changedAt` en `/api/standings` (plan §3.1):
  - `changedAt` es el más reciente entre la fila y sus partidos contados (D-7);
  - con los datos de prueba, los balances son los esperados;
  - hay un caso con un partido ficticio contra un invitado, creado en la prueba (criterio 3a).
  - Las pruebas existentes de la 002 y la 003 siguen en verde.
  - **RF:** RF-45, RF-45a, RF-53e; RF-136 a RF-139 de la 002
  - **Dep.:** T-007
  - **Hecho cuando:** la respuesta cumple el contrato del plan §3.1 y la batería del backend pasa.
- [x] **T-009 · Cierre F1**
  - **Dep.:** T-005 a T-008
  - **Hecho cuando:** pytest está en verde, se ha entregado la guía (`/api/standings` con `retake_guia` y con los datos reales) y se ha sugerido el commit.

## F2 — Tablas de datos comunes

- [x] **T-010** Pruebas e implementación de `tables/sortCycle`: ciclo `best` → `worst` → orden por defecto en la misma columna; otra columna empieza en `best`.
  - **RF:** RF-3 a RF-5
  - **Dep.:** T-009
  - **Hecho cuando:** cubre pulsaciones seguidas, cambios de columna y la vuelta al orden por defecto.
- [x] **T-011** Pruebas e implementación de `tables/sortRows`:
  - tipos de columna `ascending`, `descending`, `text` y `record`;
  - `record` por porcentaje de victorias y, a igualdad, más ganadas;
  - filas sin valor detrás, en cualquier sentido;
  - empates en el orden por defecto;
  - alfabético con `Intl.Collator`, sin distinguir mayúsculas y con los números por su valor.
  - **RF:** RF-2, RF-7, RF-7a, RF-8, RF-9
  - **Dep.:** T-010
  - **Hecho cuando:** cubre acentos, mayúsculas, "Team 2" frente a "Team 10", balances `0–0` y empates.
- [x] **T-012** Pruebas e implementación de `tables/tableFormat`:
  - balance `12–5`;
  - diferencia con `+`, con `−` (U+2212) o sin signo en el 0;
  - dígitos con el formato del idioma.
  - **RF:** RF-20, RF-21, RF-23
  - **Dep.:** T-010
  - **Hecho cuando:** el signo es `−` en español y en inglés y los separadores siguen el idioma.
- [x] **T-013** Pruebas e implementación de `tables/useSortState` (plan §2.4, D-3), con historial simulado:
  - el orden se conserva al llegar datos o al cambiar de idioma o de ancho;
  - se recupera con Atrás y Adelante;
  - vuelve al orden por defecto al entrar desde el menú o al recargar (marca de la carga distinta);
  - se reinicia al pedirlo la página (cambio de temporada).
  - **RF:** RF-10, RF-11, RF-11a
  - **Dep.:** T-010
  - **Hecho cuando:** cada caso tiene su prueba y pasa.
- [x] **T-014** Pruebas e implementación de `tables/DataTable` (plan §3.2, D-8, D-9):
  - `<table>` con `<caption>` y `<th scope>`;
  - cabeceras ordenables como botones, con `aria-sort` y con nombre y sentido para el lector;
  - columnas excluidas no ordenables;
  - cabecera de fila;
  - caja con desplazamiento horizontal y columnas fijas;
  - estados hover, foco y active de la 001.
  - **RF:** RF-1, RF-6, RF-12, RF-13, RF-36, RF-36a, RF-37, RF-38, RF-39
  - **Dep.:** T-011, T-013
  - **Hecho cuando:** se ordena con el puntero y con el teclado con las mismas reglas, y el lector recibe la columna y el sentido.
- [x] **T-015** Pruebas e implementación de `tables/TruncatedName` (plan §2.6, decisión H-2):
  - solo se activa si el texto no cabe;
  - puede recibir el foco;
  - burbuja con `role="tooltip"` y `aria-describedby`;
  - se abre con el puntero, el foco o un toque;
  - se cierra con Escape;
  - sigue abierta con el puntero encima de la burbuja;
  - no se sale de la pantalla.
  - **RF:** RF-17, RF-17a, RF-17b
  - **Dep.:** T-014
  - **Hecho cuando:** cumple las tres condiciones de WCAG 1.4.13 en sus pruebas.
- [x] **T-016** Pruebas e implementación de `tables/TeamCell`:
  - insignia según §2.2 (`resolveTeamBadge`);
  - nombre corto desde 1024 px y abreviatura por debajo (`WIDE_MEDIA_QUERY`);
  - nombre corto como nombre accesible;
  - texto sin enlace.
  - **RF:** §2.2, RF-14, RF-15, RF-16, RF-18
  - **Dep.:** T-015
  - **Hecho cuando:** a 1023 y 1024 px se ve el texto correcto y el nombre accesible es siempre el nombre corto.
- [x] **T-017 · Cierre F2**
  - **Dep.:** T-010 a T-016
  - **Hecho cuando:** Vitest está en verde, se ha entregado la guía y se ha sugerido el commit.

## F3 — Animaciones de las tablas

- [x] **T-018** Pruebas e implementación del aviso de fin de transición en `motion/PageTransition`: se avisa al acabar la transición entre páginas, y al momento si no la hay (primera carga o reducir movimiento).
  - **RF:** RF-28a
  - **Dep.:** T-017
  - **Hecho cuando:** las transiciones existentes no cambian y el aviso llega en ≤ 200 ms.
- [x] **T-019** Pruebas e implementación de la entrada en `tables/useTableMotion`:
  - empieza tras el aviso de T-018;
  - solo las filas visibles;
  - escalonada, con contadores desde 0 en las columnas `countUp` y con signo;
  - ≤ 800 ms;
  - se repite cuando la tabla aparece (al llegar, con Atrás/Adelante, tras "Reintentar" o al pasar de vacío a datos), nunca al actualizarse;
  - si llegan datos a mitad, los contadores terminan en el valor nuevo.
  - **RF:** RF-28, RF-28a a RF-28d, RF-29
  - **Dep.:** T-018
  - **Hecho cuando:** con el reloj falso, la entrada termina en ≤ 800 ms y cada caso tiene su prueba.
- [x] **T-020** Pruebas e implementación del resaltado y la recolocación:
  - resaltado de la celda que cambia, con el fondo `highlight` desvaneciéndose;
  - filas a su sitio nuevo con FLIP;
  - ambos en ≤ 300 ms, sin cambiar el scroll y con el foco en su fila.
  - **RF:** RF-30, RF-31, RF-31a, RF-32
  - **Dep.:** T-019
  - **Hecho cuando:** el scroll y el elemento con foco son los mismos antes y después de recolocar.
- [x] **T-021** Pruebas e implementación de "reducir movimiento" y del valor accesible:
  - sin ninguna animación de las tablas;
  - la cifra que cuenta es `aria-hidden` y el valor final está disponible para el lector desde el principio (D-10).
  - **RF:** RF-33, RF-34
  - **Dep.:** T-020
  - **Hecho cuando:** con reducir movimiento forzado no se crea ninguna animación y el lector lee siempre el valor final.
- [x] **T-022 · Cierre F3**
  - **Dep.:** T-018 a T-021
  - **Hecho cuando:** Vitest está en verde, se ha entregado la guía y se ha sugerido el commit.

## F4 — Sección Posiciones

- [x] **T-023** Pruebas e implementación de la ruta:
  - `standings` pasa a `hasContent: true`;
  - `AppRoutes` asigna la página a cada sección con contenido;
  - la sección deja de mostrar "Próximamente";
  - las demás secciones siguen igual.
  - **RF:** RF-52
  - **Dep.:** T-022
  - **Hecho cuando:** `/standings` pinta `StandingsPage` dentro del marco y el resto de rutas no cambia.
- [x] **T-024** Pruebas e implementación de la cabecera de `StandingsPage`:
  - título "Posiciones" y "Temporada <año>" con el año del pie;
  - sin temporada, solo el título;
  - título de la pestaña;
  - última actualización con el texto de la 003 (plan §3.3);
  - aviso de datos sin actualizar si lo está cualquiera de los dos conjuntos.
  - **RF:** RF-42, RF-42a, RF-42b, RF-53a a RF-53e
  - **Dep.:** T-023
  - **Hecho cuando:** cada caso tiene su prueba con la API y la frescura simuladas.
- [x] **T-025** Pruebas e implementación de la tabla de posiciones:
  - columnas en su orden y reglas de mejor a peor;
  - orden por defecto: posición, sin posición al final y empates por el texto que se ve;
  - columnas fijas Posición y Equipo, y Equipo como cabecera de fila;
  - posición compartida ("13.º, compartido" para el lector);
  - `No disponible` en posición o puntos, y en Series, Mapas y ±Mapas si no hay balance;
  - ±Mapas calculado;
  - Puntos, Series, Mapas y ±Mapas cuentan en la entrada;
  - solo las filas de la tabla publicada.
  - **RF:** RF-41, RF-41c, RF-43 a RF-50b
  - **Dep.:** T-024
  - **Hecho cuando:** cada regla tiene su prueba y las filas coinciden con la API.
- [x] **T-026** Pruebas e implementación de los estados de la sección con `LiveBlock` (vigila `standings` y `matches`, ciclo del resto de datos):
  - esqueleto `table`;
  - error y "Reintentar";
  - sin conexión;
  - actualización silenciosa sin anuncios al lector;
  - texto de RF-51 si no hay tabla o nadie tiene puntos.
  - **RF:** RF-24 a RF-27, RF-51, RF-53
  - **Dep.:** T-025
  - **Hecho cuando:** cada estado tiene su prueba y ninguna actualización se anuncia.
- [x] **T-027** Pruebas e implementación del cambio de temporada con la página abierta: año nuevo en el título, orden por defecto, y entrada o texto de RF-51 según haya datos.
  - **RF:** RF-51a
  - **Dep.:** T-026
  - **Hecho cuando:** al simular el cambio de temporada la página se comporta como una tabla nueva.
- [x] **T-028 · Cierre F4**
  - **Dep.:** T-023 a T-027
  - **Hecho cuando:** Vitest está en verde, se ha entregado la guía (con los datos reales y con `retake_guia`) y se ha sugerido el commit.

## F5 — Cierre

- [x] **T-029** Pruebas de extremo a extremo de Posiciones con la API simulada:
  - 320, 1023, 1024 y 1440 px, sin scroll horizontal de la página y con las columnas fijas;
  - ordenar con el teclado;
  - Atrás/Adelante y recarga;
  - nombre recortado con toque y Escape;
  - reducir movimiento;
  - zoom al 200 %;
  - español e inglés.
  - Además, `/standings` entra en las auditorías axe existentes.
  - **RF:** RF-12 a RF-17b, RF-33, RF-35 a RF-40; criterios 4 a 8
  - **Dep.:** T-028
  - **Hecho cuando:** las pruebas nuevas y las existentes pasan en los proyectos `dev` y `prod`.
- [x] **T-030** Checklist de seguridad del plan §9:
  - texto de las fuentes solo como texto y logos solo como `<img>`;
  - sin SQL concatenado;
  - ningún dato personal en la tabla ni en `history.state`.
  - **RF:** criterio 9
  - **Dep.:** T-029
  - **Hecho cuando:** cada punto está comprobado y anotado en la guía.
- [x] **T-031** Ejecutar todas las pruebas: pytest, `npm test` y `npm run test:e2e`.
  - **RF:** —
  - **Dep.:** T-030
  - **Hecho cuando:** todo está en verde.
- [x] **T-032** Redactar `verification-guide.md` de la 004 con una fila por RF y por los de C-29, y añadir las filas de RF-136 a RF-139 a la guía de la 002. Comprobar:
  - con los datos reales: Boston Breach en la tabla de 2026 y el balance con los partidos contra invitados (CDL Major 3; QA-30);
  - con `retake_guia`: posiciones compartidas y equipos sin partidos.
  - **RF:** todos; criterios 2 y 3
  - **Dep.:** T-031
  - **Hecho cuando:** Hugo confirma cada fila.
- [x] **T-033** Sincronizar la spec y el plan con los cambios surgidos durante la implementación, en el registro del plan (constitución §1.3).
  - **RF:** criterio 10
  - **Dep.:** T-032
  - **Hecho cuando:** la spec, el plan y el código coinciden.
- [ ] **T-034 · Cierre de la spec 004**
  - **Dep.:** T-029 a T-033
  - **Hecho cuando:** todas las pruebas están en verde, se ha sugerido el commit final y Hugo aprueba el cierre de la spec 004.

---

## Trazabilidad RF → tareas

| RF | Tareas |
|---|---|
| RF-1, RF-6 | T-014, T-029 |
| RF-2, RF-7, RF-7a, RF-8, RF-9 | T-011, T-025 |
| RF-3 a RF-5 | T-010, T-014, T-029 |
| RF-10, RF-11, RF-11a | T-013, T-029 |
| RF-12, RF-13 | T-014, T-029 |
| §2.2, RF-14 a RF-16, RF-18 | T-016, T-029 |
| RF-17, RF-17a, RF-17b | T-015, T-029 |
| RF-19 | Retirado (QA-24) |
| RF-20, RF-21, RF-23 | T-012 |
| RF-22 | T-001, T-012, T-025 |
| RF-24 | T-003, T-026 |
| RF-25 a RF-27 | T-026 |
| RF-28, RF-28a a RF-28d, RF-29 | T-018, T-019 |
| RF-30 | T-001, T-020 |
| RF-31, RF-31a, RF-32 | T-020 |
| RF-33, RF-34 | T-021, T-029 |
| RF-35 | T-001, T-029 |
| RF-36, RF-36a, RF-37 a RF-39 | T-014, T-029 |
| RF-40 | T-002, T-029 |
| RF-41, RF-41c | T-025 |
| RF-41a, RF-41b | T-006, T-007 |
| RF-42, RF-42a, RF-42b | T-002, T-024 |
| RF-43 a RF-44a, RF-46 a RF-50b | T-025 |
| RF-45, RF-45a | T-008, T-025 |
| RF-48 | T-002, T-025 |
| RF-51, RF-53 | T-026 |
| RF-51a | T-013, T-027 |
| RF-52 | T-023 |
| RF-53a a RF-53d | T-024 |
| RF-53e | T-008, T-024 |
| RF-136 a RF-139 de la 002 (con RF-138a) | T-005, T-006, T-008, T-032 |
| Criterios 2 y 3 (con 3a) | T-008, T-032 |
| Criterios 4 a 8 | T-029 |
| Criterio 9 | T-030 |
| Criterio 10 | T-033 |
