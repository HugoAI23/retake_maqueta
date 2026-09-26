# Spec: Tablas de Datos y Posiciones

- **ID**: `004-tables-and-standings`
- **Fecha**: `2026-09-25`
- **Estado**: `Aprobado` (aprobada por Hugo el 2026-09-25; cambio C-29 a la 002 aprobado el mismo día, §5.2; revisión QA del mismo día, §5.3)

---

## 1. Contexto y Propósito (Por Qué)

Retake ya guarda los datos de la liga (spec 002) y los mantiene al día (spec 003), pero ninguna sección los muestra: todas enseñan "Próximamente" (RF-37 de la 001). Hugo quiere cubrir todas las secciones con datos, una spec por sección, y empezar por lo común.

Esta spec define **lo común que necesita la primera sección** y **la sección Posiciones**, su primer uso real:

- las tablas de datos: cabecera, orden por columnas, comportamiento en pantallas estrechas, carga, error y vacío;
- cómo aparece un equipo en una tabla y cuándo enlaza a su ficha;
- el formato de los balances "ganados–perdidos" y de las diferencias;
- las animaciones de las tablas;
- la tabla de posiciones de la temporada actual, con los puntos publicados y el balance de series y mapas de cada equipo.

Las demás piezas comunes (fichas de detalle, filtros, pestañas, búsqueda) las definirá la primera spec que las necesite, y quedarán como comunes para las siguientes (decisión de Hugo: nada diseñado sin un uso real).

El balance de series y mapas es un **dato nuevo**, calculado a partir de los partidos. Las reglas de ese cálculo pertenecen a la spec 002 y están en su cambio C-29, aprobado el 2026-09-25 (§5.2).

---

## 2. Requisitos Funcionales (Notación EARS)

Las reglas de §2.1 a §2.6 obligan a todas las specs visuales con tablas de datos (005 en adelante). Cada una decide sus columnas, su orden por defecto y lo que la 004 le deja decidir, pero no puede contradecirlas; si necesita otra cosa, se cambia la 004.

### 2.1 Tablas de datos

Se entiende por **tabla de datos** cada tabla con datos de la liga de cualquier sección. Su **orden por defecto** lo fija la spec de la sección. Toda columna de una tabla de datos es **ordenable**, salvo que la spec de su sección la excluya. La spec de la sección define qué significa «de mejor a peor» en cada columna ordenable.

* **RF-1 (Ubicuo)**: EL SISTEMA mostrará cada tabla de datos con una fila de cabecera que nombre cada columna.
* **RF-2 (Ubicuo)**: EL SISTEMA mostrará cada tabla de datos, al abrirla, en su orden por defecto.
* **RF-3 (Dirigido por evento)**: CUANDO el usuario pulse la cabecera de una columna ordenable, EL SISTEMA pasará esa columna al siguiente estado de su ciclo: de mejor a peor, de peor a mejor y orden por defecto, y vuelta a empezar.
* **RF-4 (Dirigido por evento)**: CUANDO el usuario pulse la cabecera de una columna distinta de la que ordena la tabla, EL SISTEMA empezará el ciclo de esa columna por el estado «de mejor a peor».
* **RF-5 (Ubicuo)**: EL SISTEMA no cambiará el estado del ciclo cuando lleguen datos nuevos.
* **RF-6 (Ubicuo)**: EL SISTEMA indicará a la vista y a los lectores de pantalla por qué columna y en qué sentido está ordenada la tabla.
* **RF-7 (No deseado)**: SI dos filas tienen el mismo valor en la columna por la que se ordena, ENTONCES EL SISTEMA mantendrá entre ellas su orden por defecto.
* **RF-7a (Ubicuo)**: EL SISTEMA ordenará alfabéticamente con las reglas del idioma de la interfaz, sin distinguir mayúsculas de minúsculas, con cada letra acentuada junto a la misma letra sin acento y con los números por su valor (ej. «Team 2» antes que «Team 10»).
* **RF-8 (Ubicuo)**: EL SISTEMA ordenará una columna de balance "ganados–perdidos" por el porcentaje de victorias (ganados entre jugados) y, a igual porcentaje, por el número de ganados.
* **RF-9 (No deseado)**: SI una fila no tiene valor en la columna por la que se ordena (un dato `No disponible` o un balance sin partidos jugados), ENTONCES EL SISTEMA la colocará detrás de las demás al ordenar por esa columna, en cualquier sentido.
* **RF-10 (Estado)**: MIENTRAS el usuario permanezca en la página, EL SISTEMA conservará el orden que haya elegido, también cuando lleguen datos nuevos (RF-83 de la 003), cambie el idioma o cambie el ancho de la ventana.
* **RF-11 (Dirigido por evento)**: CUANDO el usuario vuelva a la página con Atrás o Adelante del navegador, EL SISTEMA mostrará la tabla con el orden que tenía al salir.
* **RF-11a (Dirigido por evento)**: CUANDO el usuario entre en la página desde un enlace o el menú, o la recargue, EL SISTEMA mostrará la tabla en su orden por defecto.
* **RF-12 (Estado)**: MIENTRAS la tabla sea más ancha que su espacio, EL SISTEMA permitirá desplazarla horizontalmente dentro de su caja, sin desplazar la página (RF-4 de la 001).
* **RF-13 (Estado)**: MIENTRAS la tabla se desplace horizontalmente, EL SISTEMA mantendrá visibles a la izquierda las columnas fijas que defina la spec de su sección.

### 2.2 Equipos y jugadores en las tablas

La **insignia** de un equipo es el logo de la identidad que se muestra. Si no tiene logo, se aplican los respaldos de la 002 (RF-14, RF-15 y RF-118 de la 002): el logo de la identidad más reciente, o la abreviatura sobre su color primario o sobre el color neutro.

* **RF-14 (Estado)**: MIENTRAS la ventana mida 1024 px de ancho o más, EL SISTEMA mostrará cada equipo de una tabla con su insignia (§2.2) y su nombre corto.
* **RF-15 (Estado)**: MIENTRAS la ventana mida menos de 1024 px de ancho, EL SISTEMA mostrará cada equipo de una tabla con su insignia y su abreviatura.
* **RF-16 (Ubicuo)**: EL SISTEMA dará a cada equipo de una tabla su nombre corto como nombre legible por los lectores de pantalla, también cuando se muestre la abreviatura.
* **RF-17 (No deseado)**: SI el nombre corto de un equipo no cabe en su columna, ENTONCES EL SISTEMA lo recortará con puntos suspensivos y permitirá consultar el nombre completo al pasar el puntero, al recibir el foco del teclado o al tocarlo.
* **RF-17a (Ubicuo)**: EL SISTEMA permitirá que un nombre recortado reciba el foco del teclado aunque no sea un enlace.
* **RF-17b (Ubicuo)**: EL SISTEMA mostrará el nombre completo de forma que se pueda cerrar sin mover el puntero ni el foco, se pueda pasar el puntero por encima sin que desaparezca y siga visible mientras el puntero o el foco estén sobre el nombre (WCAG 2.2, criterio 1.4.13).
* **RF-18 (Estado)**: MIENTRAS la spec de la ficha de un equipo o de un jugador no esté implementada, EL SISTEMA mostrará su nombre en las tablas como texto, sin enlace.
* **RF-19**: retirado en la revisión QA (QA-24). El enlace a las fichas lo añadirán las specs de Equipos y de Jugadores.

### 2.3 Balances y diferencias

* **RF-20 (Ubicuo)**: EL SISTEMA mostrará cada balance como "ganados–perdidos", con una raya entre las dos cifras (ej. `12–5`).
* **RF-21 (Ubicuo)**: EL SISTEMA mostrará cada diferencia con su signo: `+` si es positiva, el signo menos `−` (U+2212) si es negativa y sin signo si es 0, en cualquier idioma.
* **RF-22 (Ubicuo)**: EL SISTEMA distinguirá las diferencias positivas de las negativas con un color, además de con el signo, y mostrará las diferencias de 0 con el color normal del texto.
* **RF-23 (Ubicuo)**: EL SISTEMA mostrará los dígitos de las cifras con el formato del idioma de la interfaz, salvo el signo de las diferencias (RF-21).

### 2.4 Carga, error y vacío de las tablas

Cada tabla de datos es un **bloque con contenido** a efectos de la 001 (§2.6 y §2.7 de la 001) y de la 003 (RF-79 a RF-96 de la 003).

* **RF-24 (Estado)**: MIENTRAS una tabla de datos se cargue por primera vez, EL SISTEMA mostrará en su lugar un esqueleto con forma de tabla (RF-40 de la 001).
* **RF-25 (Ubicuo)**: EL SISTEMA aplicará a cada tabla de datos las reglas de carga, error y conexión de los bloques de la 001 (RF-40 a RF-53 de la 001), incluidos el aviso de error, el botón "Reintentar" y el aviso "Sin conexión".
* **RF-26 (Estado)**: MIENTRAS una tabla de datos esté vacía según la spec de su sección, EL SISTEMA mostrará en su lugar el mensaje de vacío que esa spec defina.
* **RF-27 (Ubicuo)**: EL SISTEMA actualizará cada tabla de datos con las reglas de actualización automática de la 003 (RF-79 a RF-96 de la 003).

### 2.5 Animaciones de las tablas

* **RF-28 (Dirigido por evento)**: CUANDO una tabla de datos aparezca (al llegar a su página, también con Atrás o Adelante, tras un «Reintentar» con éxito o al pasar de su mensaje de vacío a tener datos), EL SISTEMA hará aparecer sus filas de forma escalonada y hará contar desde 0 hasta su valor las cifras que defina la spec de su sección.
* **RF-28a (Dirigido por evento)**: CUANDO el usuario llegue a una página con una tabla de datos, EL SISTEMA empezará la animación de entrada de la tabla cuando termine la transición entre páginas de la 001 (RF-85 de la 001).
* **RF-28b (Ubicuo)**: EL SISTEMA no repetirá la animación de entrada al actualizar una tabla que ya se ve; los cambios se muestran con el resaltado y la recolocación (RF-30, RF-31).
* **RF-28c (No deseado)**: SI llegan datos nuevos durante la animación de entrada, ENTONCES EL SISTEMA hará que las cifras terminen de contar hacia el valor nuevo, sin repetir la entrada.
* **RF-28d (Ubicuo)**: EL SISTEMA aplicará la entrada escalonada y los contadores solo a las filas visibles cuando aparece la tabla; las demás aparecerán ya con su valor, sin animación.
* **RF-29 (Ubicuo)**: EL SISTEMA completará la animación de entrada de una tabla en 800 ms o menos, contados desde que empieza.
* **RF-30 (Dirigido por evento)**: CUANDO cambie el valor de una celda visible por un dato nuevo, EL SISTEMA resaltará el fondo de esa celda con un color de acento que se desvanecerá, sin mover la celda.
* **RF-31 (Dirigido por evento)**: CUANDO cambie el orden de las filas, por decisión del usuario o por datos nuevos, EL SISTEMA desplazará cada fila hasta su nuevo sitio con una animación, sin desplazar la vista del usuario (RF-84 de la 003).
* **RF-31a (No deseado)**: SI la fila que tiene el foco del teclado se recoloca, ENTONCES EL SISTEMA mantendrá el foco en esa fila (RF-83 de la 003), aunque salga de la vista, sin desplazar la vista (RF-84 de la 003).
* **RF-32 (Ubicuo)**: EL SISTEMA completará cada resaltado y cada recolocación de filas en 300 ms o menos.
* **RF-33 (Opcional)**: DONDE el usuario tenga activada la preferencia de reducir movimiento en su sistema, EL SISTEMA mostrará las tablas y sus cambios sin ninguna animación.
* **RF-34 (Ubicuo)**: EL SISTEMA permitirá leer y usar la tabla durante sus animaciones, y dará a los lectores de pantalla el valor final de cada cifra desde el primer momento.

*Nota:* el límite de 300 ms de la 001 (RF-87 de la 001) se aplica a las animaciones del marco común. Las de las tablas tienen los suyos (RF-29 y RF-32), y los datos se pueden leer y usar desde el primer instante (RF-34).

### 2.6 Accesibilidad e idioma de las tablas

* **RF-35 (Ubicuo)**: EL SISTEMA cumplirá el nivel AA de las WCAG 2.2 en todas las tablas de datos.
* **RF-36 (Ubicuo)**: EL SISTEMA asociará cada celda de una tabla de datos con su cabecera de columna y con su fila, para los lectores de pantalla.
* **RF-36a (Ubicuo)**: EL SISTEMA usará como cabecera de cada fila, para los lectores de pantalla, la columna que defina la spec de su sección.
* **RF-37 (Ubicuo)**: EL SISTEMA permitirá ordenar las tablas de datos solo con el teclado, con las mismas reglas que con el puntero.
* **RF-38 (Ubicuo)**: EL SISTEMA mostrará los estados hover, foco y active de la 001 (RF-75 a RF-77 de la 001) en cada cabecera ordenable y en cada enlace de una tabla.
* **RF-39 (Estado)**: MIENTRAS el navegador tenga un zoom del 200 %, EL SISTEMA mantendrá visibles y utilizables todos los contenidos y funciones de las tablas de datos.
* **RF-40 (Ubicuo)**: EL SISTEMA mostrará en español y en inglés todos los textos de las tablas de datos: cabeceras, nombres para los lectores de pantalla, mensajes de vacío y avisos.

### 2.7 Sección Posiciones

* **RF-41 (Ubicuo)**: EL SISTEMA mostrará en la sección Posiciones la tabla de posiciones de la temporada actual (RF-49 de la 002), con una fila por franquicia de la tabla y sin equipos invitados (RF-117c de la 002).
* **RF-41a (Ubicuo)**: EL SISTEMA mostrará en cada fila de la tabla de posiciones la identidad (nombre, abreviatura y logo) con la que la franquicia jugó su último partido `en vivo` o `finalizado` de la temporada actual.
* **RF-41b (No deseado)**: SI la franquicia no ha jugado todavía ningún partido de la temporada actual, ENTONCES EL SISTEMA mostrará en su fila su identidad vigente.
* **RF-41c (No deseado)**: SI una franquicia de la liga no figura en la tabla de posiciones publicada, ENTONCES EL SISTEMA no la mostrará en la tabla.
* **RF-42 (Ubicuo)**: EL SISTEMA mostrará en la sección Posiciones el título "Posiciones" y, debajo, "Temporada <año>" (en inglés, "<año> Season"), con el año de la temporada actual tal como lo usa el pie de página (RF-58 de la 001).
* **RF-42a (No deseado)**: SI no hay temporada actual, ENTONCES EL SISTEMA mostrará solo el título "Posiciones" y el texto de RF-51.
* **RF-42b (Ubicuo)**: EL SISTEMA titulará la pestaña del navegador de la sección según RF-30 de la 001 ("Posiciones · Retake" / "Standings · Retake").
* **RF-43 (Ubicuo)**: EL SISTEMA mostrará en la tabla de posiciones, en este orden, las columnas Posición, Equipo, Puntos, Series, Mapas y ±Mapas.
* **RF-44 (Ubicuo)**: EL SISTEMA mostrará la posición y los puntos de cada equipo tal como los registra la 002 (RF-50 y RF-122 de la 002).
* **RF-44a (No deseado)**: SI a un equipo de la tabla de posiciones le falta la posición o los puntos, ENTONCES EL SISTEMA mostrará `No disponible` en esa celda.
* **RF-45 (Ubicuo)**: EL SISTEMA mostrará en Series el balance de series de cada equipo y en Mapas su balance de mapas (RF-136 y RF-137 de la 002, cambio C-29).
* **RF-45a (No deseado)**: SI el balance de un equipo no está disponible (RF-139 de la 002), ENTONCES EL SISTEMA mostrará `No disponible` en Series, Mapas y ±Mapas, y esas celdas irán detrás al ordenar por ellas (RF-9).
* **RF-46 (Ubicuo)**: EL SISTEMA mostrará en ±Mapas la diferencia entre los mapas ganados y los perdidos de cada equipo.
* **RF-47 (Ubicuo)**: EL SISTEMA ordenará por defecto la tabla de posiciones por la posición publicada, de menor a mayor, y los equipos que compartan posición por orden alfabético del texto con que se muestran (RF-14, RF-15); las filas sin posición van al final, entre ellas por orden alfabético del texto con que se muestran.
* **RF-48 (Ubicuo)**: EL SISTEMA mostrará una posición compartida con el mismo número en cada fila, y la indicará como compartida a los lectores de pantalla.
* **RF-49 (Ubicuo)**: EL SISTEMA permitirá ordenar la tabla de posiciones por todas sus columnas; de mejor a peor significa: Posición, de menor a mayor; Equipo, por orden alfabético del texto con que se muestra (RF-14, RF-15); Puntos y ±Mapas, de mayor a menor; Series y Mapas, de mayor a menor porcentaje de victorias (RF-8).
* **RF-50 (Estado)**: MIENTRAS la tabla de posiciones se desplace horizontalmente, EL SISTEMA mantendrá fijas las columnas Posición y Equipo.
* **RF-50a (Ubicuo)**: EL SISTEMA hará contar en la entrada de la tabla de posiciones los Puntos, las dos cifras de Series y de Mapas, y ±Mapas desde 0 hacia su valor con su signo; la posición no cuenta.
* **RF-50b (Ubicuo)**: EL SISTEMA usará la columna Equipo como cabecera de cada fila de la tabla de posiciones.
* **RF-51 (No deseado)**: SI la temporada actual no tiene tabla de posiciones, o la tiene sin puntos para ningún equipo (RF-51 de la 002), ENTONCES EL SISTEMA mostrará en la sección, en lugar de la tabla, el texto "La tabla de posiciones todavía no está disponible".
* **RF-51a (Dirigido por evento)**: CUANDO cambie la temporada actual con la sección abierta, EL SISTEMA mostrará el año nuevo en el título, devolverá la tabla a su orden por defecto y la mostrará como una tabla que aparece (RF-28) o, si no tiene datos, con el texto de RF-51, sin anunciarlo a los lectores de pantalla (RF-53).
* **RF-52 (Ubicuo)**: EL SISTEMA dejará de mostrar "Próximamente" en la sección Posiciones (RF-37 de la 001).
* **RF-53 (Ubicuo)**: EL SISTEMA no anunciará a los lectores de pantalla los cambios de la tabla de posiciones, porque son del resto de datos (RF-96 de la 003).
* **RF-53a (Ubicuo)**: EL SISTEMA tratará la tabla de posiciones como dependiente de dos conjuntos de datos: la tabla de posiciones y los partidos finalizados (resto de datos de la 003).
* **RF-53b (Dirigido por evento)**: CUANDO cambie cualquiera de esos dos conjuntos, EL SISTEMA mostrará los datos nuevos en la tabla en los plazos de la 003 para el resto de datos (RF-81 de la 003).
* **RF-53c (No deseado)**: SI cualquiera de esos dos conjuntos supera su umbral de desactualización, ENTONCES EL SISTEMA mostrará en la tabla el aviso discreto de datos sin actualizar (RF-89 de la 003), debajo de la última actualización.
* **RF-53d (Ubicuo)**: EL SISTEMA mostrará en la sección Posiciones, debajo de la temporada, cuándo fue su última actualización con el texto de la 003, también cuando muestre el texto de RF-51 (RF-155 de la 003).
* **RF-53e (Ubicuo)**: EL SISTEMA considerará como última actualización de la sección el cambio más reciente de la tabla de posiciones o de los partidos que cuentan en el balance; si no hay datos que mostrar, el último cambio de esos dos conjuntos (RF-157 a RF-159 de la 003).

---

## 3. Casos Límite y Manejo de Errores

1. **Datos vacíos o no disponibles**:
   - Temporada nueva sin tabla todavía, o tabla sin puntos para ningún equipo (por ejemplo, al empezar la de 2027 en diciembre) → texto de RF-51, sin tabla vacía (RF-26, RF-51).
   - Equipo sin posición o sin puntos en la tabla publicada → `No disponible` en la celda; al final en el orden por defecto y detrás al ordenar por esa columna (RF-9, RF-44a, RF-47).
   - Equipo de la tabla sin ningún partido finalizado → Series `0–0`, Mapas `0–0` y ±Mapas `0`; al ordenar por Series o Mapas va detrás de los demás (RF-9, RF-21).
   - Cambio de identidad fuera de temporada (Boston Breach pasa a M80 Boston el 2026-09-24) → en la tabla de 2026 sigue «Boston Breach»; en la de 2027 sale «M80 Boston», su identidad vigente hasta su primer partido y la de sus partidos después (RF-41a, RF-41b).
   - Partidos de la temporada todavía sin obtener → `No disponible` en Series, Mapas y ±Mapas; `0–0` solo cuando se sabe que el equipo no ha jugado (RF-45a; RF-139 de la 002).
   - Franquicia de la liga que no está en la tabla publicada → no sale (RF-41c).
   - La temporada cambia con la página abierta → año nuevo en el título, orden por defecto y entrada, o texto de RF-51 si no hay datos (RF-51a).
   - Partido contra un equipo invitado → cuenta en el balance del equipo de la liga; el invitado no aparece en la tabla (RF-41; C-29).
   - Partido finalizado con ganador pero sin marcador (por ejemplo, por incomparecencia) → cuenta la serie, no los mapas; sin ganador ni marcador, o cancelado → no cuenta (RF-138 y RF-138a de la 002).
2. **Entradas del usuario**:
   - Pulsaciones rápidas en una cabecera → cada pulsación avanza un estado del ciclo; pulsar otra columna empieza su ciclo de mejor a peor (RF-3 a RF-5).
   - Orden elegido y llegan datos nuevos → se conserva el orden y las filas se recolocan sin mover la vista (RF-10, RF-31).
3. **Fallos externos**:
   - Falla la primera carga → esqueleto, aviso de error y "Reintentar" como en los bloques de la 001 (RF-24, RF-25).
   - Sin conexión → aviso general «Sin conexión» y se mantiene la tabla ya cargada; al recuperarla, se vuelve a cargar si mostraba un error (RF-25; RF-50 a RF-53 de la 001).
   - Falla una actualización automática con la tabla ya visible → sigue la tabla, con el aviso discreto de datos sin actualizar si procede (RF-27; RF-86 a RF-92 de la 003).
4. **Pantallas y preferencias**:
   - A 320 px de ancho → la tabla se desliza dentro de su caja, con Posición y Equipo fijos, y la página no tiene scroll horizontal (RF-12, RF-13, RF-50).
   - Cambiar el ancho de la ventana por encima o por debajo de 1024 px → el orden alfabético de la columna Equipo y de los empates se recalcula con el texto que se ve, sin cambiar el estado del ciclo (RF-47, RF-49).
   - Nombre de equipo largo → recortado con puntos suspensivos; el nombre completo se consulta con el puntero, con el foco o tocando (RF-17 a RF-17b).
   - Reducir movimiento activado → sin entrada escalonada, sin contadores, sin resaltados ni recolocación animada (RF-33).

---

## 4. Fuera de Alcance

* Las demás secciones: Partidos, Jugadores, Equipos y Torneos tendrán cada una su spec, en ese orden (decisión de Hugo, 2026-09-25). Noticias y Modelos de ML, más adelante, cuando tengan de dónde sacar sus datos.
* Los bloques de Inicio (cinta de marcadores, spotlight, noticias y cuadrícula de partidos).
* Las fichas de equipo y de jugador. La spec de Equipos y la de Jugadores incluirán cada una el enlace desde las tablas de datos existentes y lo comprobarán al cerrarse.
* Filtros, pestañas, búsqueda y paginación: los definirá la primera spec que los necesite.
* Las tablas de posiciones de temporadas anteriores: la 002 solo guarda la de la temporada actual (RF-49 de la 002).
* Zonas de clasificación (por ejemplo, plazas para el Champs) y forma reciente: no hay datos ni reglas para ellas.
* Cómo se calcula el balance de series y mapas: lo fija la 002 (cambio C-29).

---

## 5. Dudas y Aclaraciones Pendientes

### 5.1 Entrevista con Hugo (2026-09-24 y 2026-09-25)

| # | Duda | Decisión | Requisitos |
|---|---|---|---|
| 1 | Qué secciones cubrir | Todas las que tienen datos | §1, §4 |
| 2 | Cómo repartirlas en specs | 004 común y una spec por sección | §1 |
| 3 | Cómo se ve y se comprueba lo común | Estrenándolo con la sección Posiciones, dentro de esta spec | RF-41 a RF-53 |
| 4 | Columnas de Posiciones | Lo publicado más series y mapas ganados–perdidos | RF-43 a RF-46; C-29 |
| 5 | Qué partidos cuentan en el balance | Todos los finalizados de la temporada: clasificatorios, Majors, Minors y Champs | C-29 |
| 6 | Partidos contra invitados | Cuentan en el balance del equipo de la liga | C-29 |
| 7 | Reordenar la tabla | Sí, por cualquier columna, con vuelta al orden por defecto | RF-3 a RF-11, RF-49 |
| 8 | Tablas en móvil | Desplazamiento dentro de la tabla con columnas fijas | RF-12, RF-13, RF-50 |
| 9 | Enlaces a las fichas | Solo cuando exista la ficha | RF-18 (RF-19 retirado, QA-24) |
| 10 | Formato de series y mapas | "12–5" y columna de diferencia de mapas | RF-20 a RF-22, RF-43 |
| 11 | Orden de una columna "G–P" | Por porcentaje de victorias; a igualdad, más ganados | RF-8 |
| 12 | Animaciones | Entrada escalonada con contadores, resaltado de cambios y recolocación de filas | RF-28 a RF-34 |
| 13 | Qué piezas comunes define la 004 | Solo las que usa Posiciones | §1, §4 |
| 14 | Cómo aparece el equipo | Insignia y nombre corto; abreviatura por debajo de 1024 px (el mismo corte que el menú de la 001) | RF-14 a RF-17 |
| 15 | Posición compartida | El mismo número en cada fila; empatados por orden alfabético | RF-47, RF-48 |
| 16 | Orden de las siguientes specs | Partidos, Jugadores, Equipos y Torneos | §4 |
| 17 | Duración de las animaciones | Entrada, 800 ms como máximo; resaltado y recolocación, 300 ms | RF-29, RF-32 |

### 5.2 Cambio a la spec 002

La 004 necesita un dato que la 002 no define. Por la constitución (§1.3), el cambio se aprueba por separado, antes que esta spec.

| # | Spec | Cambio | Origen | Estado |
|---|---|---|---|---|
| C-29 | 002, §2.7 (nuevos RF-136 a RF-139) | Balance de series y de mapas de cada franquicia de la tabla, calculado con todos sus partidos finalizados de la temporada actual | Entrevista de la 004, decisiones 4 a 6 | Aprobado (2026-09-25) · escrito en la 002; se implementa con esta spec |

Texto aprobado y escrito en el §2.7 de la 002:

* **RF-136 (Ubicuo)**: EL SISTEMA calculará para cada franquicia de la tabla de posiciones de la temporada actual sus series ganadas y perdidas, con todos sus partidos `finalizado` de la temporada actual, incluidos los jugados contra equipos invitados.
* **RF-137 (Ubicuo)**: EL SISTEMA calculará para cada franquicia de la tabla de posiciones de la temporada actual sus mapas ganados, sumando los mapas que ganó en el marcador final de cada uno de esos partidos (RF-38 de la 002), y sus mapas perdidos, sumando los que ganó su rival (ej. un 3–1 suma 3 ganados y 1 perdido).
* **RF-138 (No deseado)**: SI un partido `finalizado` tiene registrado su ganador pero no su marcador final (por ejemplo, porque se ganó por incomparecencia), ENTONCES EL SISTEMA lo contará en las series de los dos equipos y no lo contará en sus mapas.
* **RF-138a (No deseado)**: SI un partido `finalizado` no tiene registrados ni su ganador ni su marcador final, ENTONCES EL SISTEMA no lo contará en las series ni en los mapas de ningún equipo.
* **RF-139 (No deseado)**: SI Retake todavía no ha obtenido los partidos de la temporada actual, ENTONCES EL SISTEMA dará como no disponible el balance de series y de mapas de todas las franquicias de la tabla de posiciones.
  * *Nota:* los partidos cancelados ya no forman parte de los datos (RF-83 de la 002). Un partido contra un invitado cuenta para el equipo de la liga; el invitado sigue sin aparecer en la tabla ni en los resúmenes de la temporada (RF-117c de la 002).

### 5.3 Revisión QA (2026-09-25)

Revisión de la spec aprobada. Cada cambio se aprobó por separado.

| # | Hallazgo | Decisión | Requisitos |
|---|---|---|---|
| QA-1 | Tres condiciones distintas para la tabla vacía (RF-26, RF-51 y RF-51 de la 002) | La de la 002: sin tabla o sin puntos para ningún equipo; lo común deja a cada sección definir su vacío | RF-26, RF-51 |
| QA-2 | La tercera pulsación cumplía a la vez «invertir» y «volver al orden por defecto»; «seguida» sin definir | Ciclo de tres estados por columna; otra columna empieza de mejor a peor; los datos nuevos no cambian el estado | RF-3 a RF-5 |
| QA-3 | Orden alfabético por nombre corto mientras en móvil se ve la abreviatura | Por el texto que se ve: nombre corto o abreviatura según el ancho | RF-47, RF-49 |
| QA-4 | El nombre recortado solo se veía con el puntero o el foco, pero sin ficha no recibe el foco, y en pantallas táctiles no hay puntero | Recortado y consultable con puntero, foco o toque, cumpliendo WCAG 1.4.13 | RF-17 a RF-17b |
| QA-5 | El signo `−` de RF-21 frente al guion que da el formato del idioma (RF-23) | Siempre `−`; el formato del idioma solo afecta a los dígitos | RF-21, RF-23 |
| QA-6 | Se aplicaban reglas de «bloques» de la 001 y la 003, pero la 001 cierra la lista de bloques; faltaban el esqueleto (RF-40) y la conexión (RF-50 a RF-53) | Cada tabla de datos es un bloque con contenido a efectos de la 001 y la 003 | §2.4, RF-24, RF-25 |
| QA-7 | 800 ms de entrada frente a los 300 ms de la 001, y sin orden entre la transición de página y la entrada | La entrada empieza al acabar la transición (≤ 1,1 s en total); el límite de la 001 es solo del marco común | RF-28a, RF-29, nota del §2.5 |
| QA-8 | No se decía qué identidad se muestra en cada fila (caso real: Boston Breach / M80 Boston) | La de su último partido jugado de la temporada; si no ha jugado, la vigente | RF-41a, RF-41b |
| QA-9 | RF-137 de la 002 («por cada lado») podía leerse como sumar los dos lados | Ganados, los del equipo; perdidos, los del rival (cambio a la 002, amplía C-29) | RF-137 de la 002 |
| QA-10 | No se decía qué cifras cuentan ni qué es «por primera vez» | Cuentan puntos, balances y diferencia (no la posición); la entrada se repite cada vez que la tabla aparece, nunca al actualizarse | RF-28, RF-28b, RF-50a |
| QA-11 | «Volver a abrir la página» no aclaraba Atrás/Adelante, recarga ni cambio de idioma | Se conserva en la página y al volver con Atrás/Adelante; desde el menú o recargando, orden por defecto | RF-10, RF-11, RF-11a |
| QA-12 | No se decía quién decide qué columnas son ordenables ni qué es «mejor» | Todas ordenables salvo exclusión de la sección, que define «mejor» en cada una | §2.1, RF-49 |
| QA-13 | La tabla mezcla la tabla publicada y los partidos; no se decía cuál manda para actualizar y avisar | Los dos: se actualiza y avisa si cualquiera cambia o se retrasa | RF-53a a RF-53c |
| QA-14 | Criterio alfabético sin definir (idioma, acentos, mayúsculas) | Reglas del idioma, sin distinguir mayúsculas, acentos junto a su letra, números por su valor | RF-7a |
| QA-15 | Color del 0, forma del resaltado y cabecera de fila sin definir | 0 con el color del texto; fondo de acento que se desvanece; la sección define la cabecera de fila (Equipo en Posiciones) | RF-22, RF-30, RF-36a, RF-50b |
| QA-16 | «Nombre de la temporada» sin fijar («CDL 2026» o «Call of Duty League 2026»), sin caso sin temporada ni título de pestaña | «Temporada 2026» / «2026 Season» con el año del pie; sin temporada, solo el título; pestaña según la 001 | RF-42 a RF-42b |
| QA-17 | Fila con la posición o los puntos vacíos | `No disponible`; al final por defecto y detrás al ordenar | RF-9, RF-44a, RF-47 |
| QA-18 | Un balance que no se puede calcular se vería como `0–0` | `No disponible` en las tres columnas; «no calculable» = partidos de la temporada sin obtener (RF-139 nuevo en la 002, amplía C-29) | RF-45a; RF-139 de la 002 |
| QA-19 | Con ganador pero sin marcador (o incomparecencia), el partido no contaba ni como serie | Cuenta la serie, no los mapas; sin ganador ni marcador, no cuenta (cambio a la 002, amplía C-29) | RF-138, RF-138a de la 002 |
| QA-20 | Sin conexión no estaba cubierto | Ya resuelto por QA-6 | RF-25 |
| QA-21 | Datos nuevos durante la entrada; fila con el foco que se recoloca | Las cifras terminan en el valor nuevo sin repetir la entrada; el foco sigue en su fila sin mover la vista | RF-28c, RF-31a |
| QA-22 | Franquicia de la liga fuera de la tabla publicada; cambio de temporada con la página abierta | No sale; el cambio de temporada se trata como una tabla nueva | RF-41c, RF-51a |
| QA-23 | Entrada escalonada de 800 ms en tablas de cientos de filas | Solo las filas visibles al aparecer la tabla | RF-28d |
| QA-24 | RF-19 (enlazar cuando exista la ficha) no se podía comprobar al cerrar la 004 | Se retira; el enlace pasa a las specs de Equipos y Jugadores | RF-18, RF-19, §4 |
| QA-25 | No se decía si las reglas comunes obligan a las specs siguientes | Obligan, como las de la 002 y la 003; para apartarse, se cambia la 004 | §2 |
| QA-26 | Ningún criterio exigía comprobar que los partidos contra invitados cuentan | Con los datos reales de 2026 y con una prueba automática propia | §6, criterios 3 y 3a |
| QA-27 | El §1 decía que C-29 «se propone» | Redacción: ya está aprobado | §1 |
| QA-28 | RF-14 citaba solo los respaldos de la insignia de la 002 | Definición de insignia en el §2.2: logo propio y, si falta, los respaldos | §2.2, RF-14 |
| QA-29 | La 004 no recogía RF-155 a RF-159 de la 003 (última actualización); visto al preparar el plan | Bajo el título, con el cambio más reciente de los dos conjuntos | RF-53c a RF-53e |
| QA-30 | El criterio 3 pedía un partido contra invitados «en un Minor», pero en 2026 todos son del CDL Major 3; visto al redactar la guía (T-032) | «En un evento de la temporada (en 2026, el CDL Major 3)» (aprobado por Hugo el 2026-09-25) | Criterio 3 |

### 5.4 Pendientes

No queda ningún `[NECESITA ACLARACIÓN]` abierto.

---

## 6. Criterios de Finalización

La spec 004 se da por terminada cuando se cumplan todas estas condiciones:

1. Hugo ha aprobado el cambio C-29 y esta spec, y no queda ningún `[NECESITA ACLARACIÓN]` abierto.
2. Cada requisito de esta spec (de RF-1 a RF-53e, incluidos los que llevan letra, salvo RF-19, retirado) y los de C-29 (RF-136 a RF-139 de la 002, con RF-138a) tienen un paso en la guía de verificación manual (constitución §5) y Hugo los ha comprobado.
3. La sección Posiciones se ha comprobado con los datos reales de la temporada 2026, incluido que el balance de un equipo que jugó contra invitados en un evento de la temporada (en 2026, el CDL Major 3) cuenta esos partidos, y con los datos de prueba (posiciones compartidas y equipos sin partidos).
   - 3a. Hay una prueba automática del balance con un partido ficticio contra un invitado, sin cambiar los datos de prueba compartidos.
4. Las tablas se han comprobado con la ventana a 320 px, 1023 px, 1024 px y 1440 px de ancho, y con el zoom al 200 %.
5. El orden por columnas se ha recorrido con el puntero y solo con el teclado.
6. Con la preferencia "reducir movimiento" activada no se ve ninguna animación de las tablas.
7. Una auditoría de accesibilidad de la sección Posiciones no muestra ningún incumplimiento del nivel AA de las WCAG 2.2.
8. Todos los textos de la sección y de las tablas aparecen en español y en inglés.
9. Se ha revisado el checklist de seguridad de la constitución (§6) para todo lo que abarca esta spec.
10. El estado de la spec ha pasado a `Aprobado` y refleja lo que realmente se construyó, sin desviaciones (constitución §1.3).
