# Plan: Tablas de Datos y Posiciones

- **Spec**: [`004-tables-and-standings/spec.md`](spec.md) (`Aprobado`, 2026-09-25; revisión QA-1 a QA-30 y cambio C-29 a la 002)
- **Fecha**: `2026-09-25`
- **Estado**: `Aprobado` (aprobado por Hugo el 2026-09-25)

Este documento describe **CÓMO** se construirá la spec 004. No contiene código: define módulos, contratos de datos, decisiones y fases. Cada parte indica qué requisitos (RF) cubre.

---

## 0. Resumen

- **Qué se construye:**
  - En el **backend**, el balance de series y mapas de la 002 (C-29: RF-136 a RF-139) y la identidad de cada fila de la tabla (RF-41a, RF-41b). Se añaden a la respuesta de `/api/standings`, sin tablas ni migraciones nuevas: se calculan al leer.
  - En el **frontend**, un módulo común de tablas de datos (`src/tables/`) y la página de la sección Posiciones, que deja de ser "Próximamente".
- **Herramientas:** ninguna nueva. Tablas con React y funciones propias, y burbuja propia para el nombre recortado (decisiones de Hugo, §8.2). Anime.js, ya en el proyecto, hace la entrada, los contadores, el resaltado y la recolocación.
- **Reutiliza** lo que ya existe:
  - de la 001: cargador de bloques, esqueleto, error y "Reintentar", conexión, idioma, reducir movimiento y título de la pestaña;
  - de la 002: insignia del equipo (`resolveTeamBadge`), `No disponible` y disponibilidad de la tabla (`isStandingsAvailable`);
  - de la 003: bloque que se actualiza solo (`LiveBlock`), frescura, aviso de datos sin actualizar y última actualización.
- **Dónde está la lógica:** las reglas de datos, que son de la 002, se calculan en el servidor, en un único sitio. Las reglas de presentación de la 004 (orden, formato, animaciones) son funciones puras del frontend, que se prueban sin navegador.

---

## 1. Módulos

### 1.1 Backend

| Módulo | Qué hace | RF |
|---|---|---|
| `app/domain/season_balance.py` (nuevo) | Funciones puras del balance: recibe los resultados de los partidos y devuelve, por franquicia, series y mapas ganados y perdidos, o "no disponible". | RF-136 a RF-139 de la 002 |
| `app/db/queries.py` (ampliado) | Partidos `finalizado` de la temporada actual con sus lados, ganador y marcador; último partido `en vivo` o `finalizado` de cada franquicia en la temporada actual. | RF-41a, RF-136 |
| `app/api/views.py` (`standing_views`) | Identidad de cada fila (último partido jugado o, si no hay, la vigente), balance y `changedAt` de la fila. | RF-41a, RF-41b, RF-45, RF-45a, RF-53e |
| `app/api/schemas.py` | `StandingOut` gana `series` y `maps` (§3.1). | RF-45 |

### 1.2 Frontend

```
src/
├── tables/                       Común a todas las tablas de datos (§2.1 a §2.6 de la spec)
│   ├── sortCycle.js              Ciclo de 3 estados por columna (función pura)
│   ├── sortRows.js               Orden con desempates, vacíos detrás, % de victorias y alfabético
│   ├── tableFormat.js            Balance "12–5", diferencia con "−", cifras con el formato del idioma
│   ├── useSortState.js           Orden elegido: se conserva en la página y con Atrás/Adelante
│   ├── useTableMotion.js         Entrada, contadores, resaltado y recolocación (Anime.js)
│   ├── DataTable.jsx             Tabla semántica, cabeceras ordenables, columnas fijas y desplazamiento
│   ├── TeamCell.jsx              Insignia + nombre corto o abreviatura
│   └── TruncatedName.jsx         Nombre recortado consultable (WCAG 1.4.13)
├── pages/StandingsPage.jsx       Sección Posiciones
├── blocks/BlockSkeleton.jsx      Nueva forma de esqueleto: 'table'
├── motion/PageTransition.jsx     Avisa de cuándo termina la transición entre páginas
├── config/designTokens.js        Colores de diferencia positiva y resaltado (con su contraste)
├── config/sectionsRegistry.js    standings → hasContent: true
├── app/AppRoutes.jsx             Página de cada sección con contenido
└── i18n/dictionaries/{es,en}.js  Textos de la tabla y de Posiciones
```

| Módulo | RF |
|---|---|
| `sortCycle.js` | RF-3 a RF-5 |
| `sortRows.js` | RF-2, RF-7, RF-7a, RF-8, RF-9, RF-47, RF-49 |
| `tableFormat.js` | RF-20 a RF-23 |
| `useSortState.js` | RF-10, RF-11, RF-11a, RF-51a |
| `useTableMotion.js` | RF-28 a RF-34, RF-50a |
| `DataTable.jsx` | RF-1, RF-6, RF-12, RF-13, RF-36, RF-36a, RF-37, RF-38, RF-39, RF-50, RF-50b |
| `TeamCell.jsx` y `TruncatedName.jsx` | §2.2, RF-14 a RF-18 |
| `StandingsPage.jsx` | RF-24 a RF-27, RF-41 a RF-53e |

---

## 2. Piezas con comportamiento

### 2.1 Balance de la temporada (backend, 002 C-29)

Para cada partido `finalizado` de la temporada actual se obtienen: la franquicia de cada lado, el ganador (`winner_side`) y el marcador final (`maps_won_1`, `maps_won_2`).

1. **Serie**: se suma una ganada al ganador y una perdida al rival (RF-136). Si falta el ganador pero hay marcador, gana el lado con más mapas, porque el marcador final lo determina (decisión D-5).
2. **Mapas**: si hay marcador, cada lado suma como ganados sus mapas y como perdidos los del rival (RF-137). Si solo hay ganador, la serie cuenta pero los mapas no (RF-138).
3. Sin ganador ni marcador, no cuenta (RF-138a).
4. Los partidos contra invitados cuentan para el equipo de la liga (RF-136). El invitado no está en la tabla (RF-117c de la 002).
5. **No disponible** (RF-139): la temporada actual no tiene ningún partido registrado (decisión D-6). En ese caso, `series` y `maps` son `null` en todas las filas.
6. Un equipo de la tabla sin partidos finalizados queda con `0–0` (se sabe que no ha jugado).

### 2.2 Identidad de cada fila (backend)

Es la identidad del último partido `en vivo` o `finalizado` de la franquicia en la temporada actual, el último por su fecha y hora de inicio programadas. Se calcula con la misma regla que los lados de los partidos (RF-12 de la 002, `identity_of_franchise_at`). Si la franquicia no ha jugado ninguno, es la vigente ahora (RF-41a, RF-41b).

### 2.3 Orden (frontend, funciones puras)

- **Estado del orden:** `null` (orden por defecto) o `{ columnId, direction: 'best' | 'worst' }`.
- **`nextSortState(state, columnId)`:**
  - misma columna: `best` → `worst` → `null`;
  - otra columna: `best` (RF-3, RF-4).
  - Los datos nuevos no lo cambian (RF-5).
- **`sortRows(rows, columns, state, locale)`:**
  - Filas sin valor en la columna: siempre detrás (RF-9).
  - Las demás, por la regla "de mejor a peor" de la columna, invertida en `worst`.
  - Empates: se mantiene el orden por defecto de la sección (RF-7).
  - El orden es estable: el mismo resultado con los mismos datos.
- **Reglas por tipo de columna** (las elige la sección; RF-8, RF-49):
  - `ascending`: menor es mejor (Posición);
  - `descending`: mayor es mejor (Puntos, ±Mapas);
  - `text`: alfabético con `Intl.Collator(locale, { sensitivity: 'base', numeric: true })` (RF-7a);
  - `record`: porcentaje de victorias y, a igualdad, más ganadas (RF-8).
- **Orden por defecto de Posiciones** (RF-47): posición ascendente, las filas sin posición al final y los empates por el texto que se ve. Por eso depende del ancho, que la página le pasa (RF-14, RF-15; QA-3).

### 2.4 Orden conservado (`useSortState`)

- El estado se guarda en la entrada del historial del navegador (`history.state`), junto con una **marca de la carga de la aplicación**: un valor al azar que se genera al arrancar.
- **Volver con Atrás o Adelante:** la marca coincide y se recupera el orden (RF-11).
- **Entrar desde el menú o un enlace:** crea una entrada nueva sin estado, así que se muestra el orden por defecto (RF-11a).
- **Recargar:** conserva `history.state`, pero la marca cambia, así que también se muestra el orden por defecto (RF-11a; decisión D-3).
- **Cambiar de idioma o de ancho** no toca el estado (RF-10).
- **Cambio de temporada con la página abierta:** vuelve al orden por defecto (RF-51a).

### 2.5 Animaciones (`useTableMotion`)

- **Entrada** (RF-28 a RF-29):
  - Empieza cuando `PageTransition` avisa de que ha terminado la transición (≤ 200 ms), o al momento si no la hay (RF-28a).
  - Afecta solo a las filas visibles. Las mide `IntersectionObserver` al aparecer la tabla, y las demás salen ya con su valor (RF-28d).
  - Las filas entran escalonadas y las cifras que indica cada columna (`countUp: true`) cuentan desde 0. En Posiciones: Puntos, las dos cifras de Series y Mapas y ±Mapas, con su signo (RF-50a).
  - Todo termina en ≤ 800 ms (RF-29).
- **Datos nuevos durante la entrada:** los contadores siguen hacia el valor nuevo, sin repetir la entrada (RF-28c).
- **Actualizaciones:** no repiten la entrada (RF-28b).
  - **Resaltado** (RF-30, RF-32): el fondo de la celda cambia al color de resaltado y se desvanece en ≤ 300 ms, sin mover la celda.
  - **Recolocación** (RF-31, RF-32): técnica FLIP. Se mide la posición de cada fila antes y después y se anima la diferencia con `translateY` en ≤ 300 ms. No cambia el scroll de la página, y el foco se queda en su fila (RF-31a).
- **Reducir movimiento** (RF-33): sin entrada, sin contadores, sin resaltado y sin recolocación animada.
- **Lectores de pantalla** (RF-34): la cifra que cuenta es solo visual (`aria-hidden`). Al lado, una copia oculta a la vista lleva el valor final desde el primer momento.

### 2.6 Nombre recortado (`TruncatedName`, componente propio)

- Solo se activa si el texto no cabe, comparando `scrollWidth` con `clientWidth` (RF-17).
- **Cuando se activa:**
  - puede recibir el foco (`tabIndex=0`) aunque no sea un enlace (RF-17a);
  - la burbuja con el nombre completo tiene `role="tooltip"` y se asocia con `aria-describedby`;
  - se abre al pasar el puntero, con el foco o al tocar;
  - se cierra con Escape y sigue abierta mientras el puntero esté sobre el nombre o sobre la propia burbuja (WCAG 1.4.13; RF-17b).
- Se coloca debajo de la celda, por encima de la columna fija, y se desplaza para no salirse de la pantalla a 320 px (riesgo R-2).

---

## 3. Contratos

### 3.1 `/api/standings` (ampliación compatible)

```
StandingRow {
  franchiseId: string
  identity: Identity | null      ← última identidad jugada en la temporada, o la vigente (RF-41a, RF-41b)
  position: number | null
  points: number | null
  series: { won: number, lost: number } | null   ← null = no disponible (RF-139 de la 002)
  maps:   { won: number, lost: number } | null
  changedAt: string | null       ← el cambio más reciente de la fila o de sus partidos contados (RF-53e)
}
```

- Los campos nuevos se **añaden**; los existentes no cambian.
- `±Mapas` no viaja: lo calcula el frontend como `maps.won − maps.lost` (RF-46).
- Las filas llegan en el orden por defecto del servidor. El frontend vuelve a ordenarlas con las reglas de la 004 y el texto que se ve.

### 3.2 Columnas de una tabla (`DataTable`)

```
Column {
  id: string
  header: string                   ← ya traducido (RF-40)
  sortKind: 'ascending' | 'descending' | 'text' | 'record' | null   ← null = excluida (§2.1 de la spec)
  value: (row) => number | string | Record | null     ← para ordenar; null = sin valor (RF-9)
  render: (row) => ReactNode
  sticky?: boolean                 ← columnas fijas (RF-13, RF-50)
  rowHeader?: boolean              ← cabecera de fila (RF-36a, RF-50b)
  countUp?: boolean                ← cuenta en la entrada (RF-50a)
}
DataTable { caption, columns, rows, rowKey, defaultOrder, sortState, onSortChange }
```

### 3.3 Frescura y actualización de Posiciones

- **Conjuntos que vigila la página:** `LiveBlock` con `datasets: ['standings', 'matches']` y ciclo del resto de datos, 5 min como máximo (RF-53a, RF-53b; RF-81 de la 003).
- **Aviso de datos sin actualizar:** se muestra si cualquiera de los dos conjuntos lo está (`useDatasetFreshness` de cada uno), debajo de la última actualización (RF-53c).
- **Última actualización:** `lastUpdatedOf(rows, max(standings.lastChangedAt, matches.lastChangedAt))`, con el texto de la 003 (RF-53d, RF-53e).

### 3.4 Textos nuevos (es / en)

| Clave | es | en |
|---|---|---|
| `standings.season` | Temporada {{year}} | {{year}} Season |
| `tables.columns.position` / `team` / `points` / `series` / `maps` / `mapDiff` | Pos. / Equipo / Puntos / Series / Mapas / ±Mapas | Pos. / Team / Points / Series / Maps / ±Maps |
| `tables.sort.best` / `worst` | ordenada de mejor a peor / de peor a mejor | sorted best to worst / worst to best |
| `tables.sort.action` | Ordenar por {{column}} | Sort by {{column}} |
| `tables.sharedPosition` | {{position}}.º, compartido | {{position}}, tied |
| `tables.caption.standings` | Tabla de posiciones, temporada {{year}} | Standings, {{year}} season |

El texto `No disponible`, el de tabla sin datos (RF-51) y los de última actualización y datos sin actualizar ya existen en la 002 y la 003.

---

## 4. Modelo de datos

No hay tablas, columnas ni migraciones nuevas: el balance y la identidad de cada fila se calculan al leer, a partir de lo que ya guardan la 002 y la 003 (`match`, `match_slot`, `match_schedule`, `event`, `standing`, `identity`). Para una temporada de unos 300 partidos, el cálculo es de milisegundos (riesgo R-4).

---

## 5. Colores (variables de diseño)

| Variable | Uso | Contraste exigido |
|---|---|---|
| `positive` (p. ej. `#5fe39a`) | Diferencia positiva (RF-22) | ≥ 4,5:1 sobre `surface` y `bg` |
| `danger` (ya existe) | Diferencia negativa (RF-22) | ya comprobado |
| `text` (ya existe) | Diferencia 0 (RF-22) | ya comprobado |
| `highlight` (p. ej. `#16384a`) | Fondo del resaltado (RF-30) | `text`, `positive` y `danger` ≥ 4,5:1 sobre él |

Los valores definitivos los fija la prueba de contraste existente (`designTokens.test.js`), que se amplía con las parejas nuevas (RF-35).

---

## 6. Estrategia de pruebas

### 6.1 Niveles

| Nivel | Herramienta | Qué cubre |
|---|---|---|
| Unidad backend | pytest | Reglas del balance: series, mapas, sin marcador, sin ganador, invitados, no disponible |
| Integración backend | pytest + PostgreSQL | `/api/standings`: identidad del último partido (caso tipo Boston Breach / M80 Boston), balance con los datos de prueba, `changedAt` |
| Unidad frontend | Vitest | `sortCycle`, `sortRows`, `tableFormat`, `useSortState` (con historial simulado) |
| Componentes | Vitest + Testing Library | `DataTable` (cabeceras, `aria-sort`, teclado, cabecera de fila), `TeamCell`, `TruncatedName`, `StandingsPage` con la API simulada (vacío, error, sin balance, cambio de temporada) |
| Extremo a extremo | Playwright + axe | 320, 1023, 1024 y 1440 px; teclado; Atrás/Adelante y recarga; reducir movimiento; zoom al 200 %; auditoría AA |

### 6.2 Reglas

- Pruebas primero en cada tarea de "pruebas e implementación" (como en la 001 a la 003).
- Ninguna prueba consulta fuentes reales. Las de extremo a extremo simulan la API en el navegador, como las de la 001.
- Las animaciones se prueban sin esperar tiempo real: con el reloj falso de Vitest y con reducir movimiento forzado.
- **Invitado en el balance** (criterio 3a): prueba de unidad y de integración con un partido ficticio contra un invitado, creado en la propia prueba; **no** se cambian los datos de prueba compartidos.

### 6.3 Matriz de cobertura (resumen)

| Bloque de la spec | Pruebas |
|---|---|
| §2.1 Orden y desplazamiento (RF-1 a RF-13) | Unidad (`sortCycle`, `sortRows`, `useSortState`) · componentes · extremo a extremo (teclado, Atrás/Adelante, recarga, 320 px) |
| §2.2 Equipos (RF-14 a RF-18) | Componentes (`TeamCell`, `TruncatedName`) · extremo a extremo (1023 frente a 1024 px, toque, Escape) |
| §2.3 Balances (RF-20 a RF-23) | Unidad (`tableFormat`) · contraste de los colores |
| §2.4 Carga, error, vacío y actualización (RF-24 a RF-27) | Componentes (estados del bloque) · pruebas existentes de `LiveBlock` |
| §2.5 Animaciones (RF-28 a RF-34) | Componentes con reloj falso · extremo a extremo con reducir movimiento |
| §2.6 Accesibilidad e idioma (RF-35 a RF-40) | axe · teclado · zoom al 200 % · es/en |
| §2.7 Posiciones (RF-41 a RF-53e) | Integración backend · componentes · extremo a extremo con datos simulados y comprobación manual con datos reales |
| C-29 (RF-136 a RF-139 de la 002) | Unidad e integración backend |

---

## 7. Plan de implementación (fases)

| Fase | Contenido | Cierre |
|---|---|---|
| **F0** | Preparación: colores nuevos con su prueba de contraste, textos es/en, forma `table` del esqueleto | Pruebas en verde |
| **F1** | Backend: reglas del balance (C-29), identidad de cada fila, ampliación de `/api/standings` | pytest en verde; guía de la fase |
| **F2** | Tablas comunes: `sortCycle`, `sortRows`, `tableFormat`, `useSortState`, `DataTable`, `TeamCell`, `TruncatedName` | Vitest en verde; guía de la fase |
| **F3** | Animaciones: aviso de fin de transición en `PageTransition` y `useTableMotion` | Vitest en verde; guía de la fase |
| **F4** | Sección Posiciones: página, registro y ruta, temporada, última actualización, aviso, vacío y cambio de temporada | Vitest en verde; guía de la fase |
| **F5** | Cierre: extremo a extremo y axe, checklist de seguridad, guía completa de la 004 con una fila por RF, filas de RF-136 a RF-139 en la guía de la 002, sincronizar spec y plan | Todas las pruebas en verde; Hugo aprueba el cierre |

Cada fase termina con sus pruebas en verde, su guía de verificación manual y un mensaje de commit sugerido. El commit lo hace Hugo (constitución §8).

---

## 8. Decisiones

### 8.1 Decisiones de diseño (dentro del stack aprobado)

| # | Decisión | Por qué | RF |
|---|---|---|---|
| D-1 | El balance y la identidad de cada fila se calculan en el servidor, al leer | Son reglas de datos de la 002: un solo sitio, igual para cualquier página futura, y el frontend no descarga todos los partidos para contar | RF-41a, RF-45; C-29 |
| D-2 | El orden y el formato son funciones puras del frontend | Son reglas de presentación de la 004; se prueban sin navegador y las reutilizan las specs 005 en adelante | §2.1, §2.3 |
| D-3 | Orden guardado en `history.state` con una marca de la carga | Así Atrás y Adelante lo recuperan y la recarga no, sin almacenamiento persistente | RF-10, RF-11, RF-11a |
| D-4 | La entrada espera al aviso de fin de `PageTransition` | La 001 anima la página 200 ms; la tabla entra después (QA-7) | RF-28a |
| D-5 | Sin ganador registrado pero con marcador, gana el lado con más mapas | El marcador final de una serie determina al ganador; evita perder series por un dato redundante que falte | RF-136 |
| D-6 | "Partidos todavía sin obtener" = la temporada actual no tiene ningún partido registrado | La temporada empieza con su primer partido en vivo (RF-3 de la 002), así que una temporada con partidos siempre los tiene obtenidos | RF-139 |
| D-7 | El `changedAt` de cada fila es el más reciente de la fila y de sus partidos contados | La última actualización debe reflejar también los cambios del balance | RF-53e |
| D-8 | Tabla HTML semántica (`<table>`, `<th scope>`, `<caption>`) con `position: sticky` para las columnas fijas | Accesible sin ARIA extra, y el desplazamiento horizontal queda dentro de su caja | RF-12, RF-13, RF-36 |
| D-9 | Cabeceras ordenables como `<button>` dentro del `<th>`, con `aria-sort` en el `<th>` | Patrón recomendado de tabla ordenable: teclado y lector sin código propio | RF-6, RF-37 |
| D-10 | Cifras que cuentan: texto visual `aria-hidden` y valor final oculto a la vista | El lector siempre lee el valor real, aunque la animación esté a medias | RF-34 |

### 8.2 Decisiones tomadas por Hugo (constitución §3.2)

| # | Pregunta | Opciones | Decisión |
|---|---|---|---|
| H-1 | Cómo construir las tablas | A: React + funciones propias · B: TanStack Table | **A** (2026-09-25) |
| H-2 | Cómo mostrar el nombre recortado | A: componente propio · B: Floating UI | **A** (2026-09-25) |

---

## 9. Seguridad (constitución §6)

- **Texto de las fuentes:** los nombres de equipo se pintan como texto con React, nunca como HTML. Los logos, solo como `<img>` con las direcciones validadas por la 002 (RF-129, RF-130 de la 002).
- **API de solo lectura:** `/api/standings` no recibe parámetros nuevos. El cálculo usa SQLAlchemy con parámetros, sin SQL concatenado.
- **Datos personales:** la tabla no muestra ninguno.
- **Estado del navegador:** en `history.state` solo va el orden (identificador de columna y sentido) y la marca de la carga; nada personal.

---

## 10. Riesgos y dependencias

| # | Riesgo | Mitigación |
|---|---|---|
| R-1 | Las columnas fijas y el desplazamiento horizontal se comportan distinto en Safari | Prueba de extremo a extremo a 320 px y revisión manual en Safari en la guía |
| R-2 | La burbuja del nombre recortado queda tapada por la columna fija o se sale de la pantalla | Se coloca por encima de las columnas fijas y se ajusta al borde; prueba a 320 px |
| R-3 | La recolocación FLIP choca con el scroll o con el foco al llegar datos nuevos | Solo se anima `transform`; se comprueba con una prueba que el scroll y el foco no cambian |
| R-4 | Calcular el balance en cada petición es lento | Unos 300 partidos por temporada: milisegundos. Si no, se guarda en memoria hasta el siguiente cambio de `matches` |
| R-5 | El orden alfabético depende del motor del navegador (`Intl.Collator`) | Las pruebas fijan casos con acentos, mayúsculas y números |
| D-A | Los datos reales de 2026 tienen partidos contra invitados (en el CDL Major 3; QA-30 de la spec) | Necesarios para el criterio 3; la base `retake` ya los tiene |

---

## 11. Pendiente para aprobar este plan

- Nada: aprobado por Hugo el 2026-09-25. `tasks.md` se redacta solo cuando Hugo lo pida.

---

## 12. Registro de implementación

| # | Fecha | Ajuste | Por qué | RF |
|---|---|---|---|---|
| I-1 | 2026-09-25 | `Column` gana `align?: 'start' \| 'end'` (§3.2) | Las cifras van alineadas a la derecha; las columnas no traían cómo alinearse | RF-1, RF-39 |
| I-2 | 2026-09-25 | `defaultOrder` de `DataTable` es un comparador opcional; sin él, las filas se muestran en el orden en que llegan (§3.2) | El orden por defecto de Posiciones depende del texto que se ve (RF-47): la página lo calcula y la tabla lo aplica | RF-2, RF-47 |
| I-3 | 2026-09-25 | Módulo nuevo `tables/useIsWide.js`: si la ventana mide 1024 px o más (`WIDE_MEDIA_QUERY`) | Lo necesitan `TeamCell` y el orden por defecto de la página, que depende del texto que se ve | RF-14, RF-15, RF-47 |
| I-4 | 2026-09-25 | Módulo nuevo `tables/CountUp.jsx`: cifra que cuenta con su copia para los lectores; sigue el progreso de su fila, que mueve `useTableMotion` | Las columnas pintan sus celdas (`render`); así cada cifra cuenta sin que la tabla sepa su formato, y con datos nuevos a mitad termina en el valor nuevo | RF-28, RF-28c, RF-34, RF-50a |
| I-5 | 2026-09-25 | Las filas visibles se miden con su posición en la ventana al aparecer la tabla, no con `IntersectionObserver` (§2.5) | La medida es inmediata, antes de pintar, y se puede probar; la entrada no espera a un aviso asíncrono | RF-28d |
| I-6 | 2026-09-25 | La página carga también `/api/franchises`, junto con `/api/standings` | La insignia usa el logo de la identidad más reciente si la de la fila no tiene (§2.2; RF-14 de la 002), y la fila solo trae su identidad | §2.2, RF-41a |
| I-7 | 2026-09-25 | El cambio de temporada se cuenta en la página (`useSeasonChanges`): la llegada del primer año al abrir no cuenta. El contador reinicia el orden y es la clave de la tabla, que se vuelve a montar y hace su entrada | Reiniciar con el año borraba el orden recuperado con Atrás/Adelante, porque el año llega después de montar la página | RF-11, RF-51a |
| I-8 | 2026-09-25 | Respaldo de la entrada: si a los 800 ms + 200 ms no ha terminado (sin fotogramas), las filas se muestran ya con su valor | Visto en la verificación: sin fotogramas (vista oculta), las filas se quedaban ocultas y con las cifras en 0 | RF-29, RF-34 |
