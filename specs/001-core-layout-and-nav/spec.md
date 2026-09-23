# Spec: Estructura Base y Navegación

- **ID**: `001-core-layout-and-nav`
- **Fecha**: `2026-09-22` (creada el 2026-09-21; revisada tras la auditoría QA)
- **Estado**: `Aprobado` (aprobada por Hugo el 2026-09-22) · **Implementada y cerrada** (cierre aprobado por Hugo el 2026-09-22)

---

## 1. Contexto y Propósito (Por Qué)

Retake es un centro de estadísticas y predicciones de la Call of Duty League. Antes de construir cualquier sección (marcadores, spotlight, partidos, equipos, jugadores o Modelos de Machine Learning) hace falta un **marco común** que tengan todas las páginas. Ese marco sirve para que el usuario sepa siempre dónde está, pueda llegar a cualquier sección y la plataforma se vea coherente y accesible tanto en móvil como en escritorio.

Esta spec define **ese marco y la distribución de la página de inicio**:

- la franja de la cinta de marcadores y el menú de navegación;
- la zona de contenido y el pie de página;
- los huecos que ocupa cada bloque del inicio;
- cómo se comporta la navegación en pantallas estrechas y con los botones del navegador;
- qué ve el usuario cuando una sección o un bloque aún no tiene contenido, mientras carga, cuando falla, cuando no hay conexión o cuando la dirección no es válida;
- el idioma de la interfaz;
- los mínimos de accesibilidad y animación del marco.

La spec reserva los huecos, pero **no define qué contiene cada uno**. El contenido de la cinta de marcadores, el spotlight, las noticias y la cuadrícula de partidos se define en sus propias specs, a partir de la información de la liga descrita en la spec 002.

La plataforma prioriza a Modelos de Machine Learning como sección estrella, así que su acceso debe destacar sobre el resto desde el primer contacto.

**Nota sobre la constitución (§7.3):** la constitución pide dejar la interfaz *preparada* para traducirla en el futuro. Por decisión de Hugo (2026-09-22), esta spec va más allá y exige el inglés completo desde ya (§2.10). La constitución no se modifica.

---

## 2. Requisitos Funcionales (Notación EARS)

### 2.1 Estructura común

* **RF-1 (Ubicuo)**: EL SISTEMA mostrará en todas las páginas, incluidas "Próximamente" y "Página no encontrada", de arriba abajo y en este orden: la cinta de marcadores, el menú de navegación, la zona de contenido y el pie de página.
* **RF-2 (Ubicuo)**: EL SISTEMA reservará para la cinta de marcadores una franja que ocupe todo el ancho de la página, justo encima del menú de navegación.
* **RF-3 (Ubicuo)**: EL SISTEMA desplazará la cinta de marcadores y el menú de navegación junto con el resto de la página al hacer scroll, sin dejarlos fijos en pantalla.
* **RF-4 (Ubicuo)**: EL SISTEMA no provocará desplazamiento horizontal de la página en ningún ancho de ventana igual o superior a 320 px.
* **RF-5 (Ubicuo)**: EL SISTEMA mostrará la interfaz únicamente en tema oscuro, sin opción de tema claro.

### 2.2 Menú de navegación

* **RF-6 (Ubicuo)**: EL SISTEMA ordenará las entradas del menú así: Inicio, Partidos, Equipos, Jugadores, Torneos, Posiciones, Noticias y Modelos de ML.
* **RF-7 (Estado)**: MIENTRAS la ventana mida 1024 px de ancho o más, EL SISTEMA mostrará en una sola fila el logo de Retake, las ocho entradas del menú y el selector de idioma.
* **RF-8 (Ubicuo)**: EL SISTEMA mostrará la entrada Modelos de ML con un color de fondo que no comparte ninguna otra entrada del menú.
* **RF-9 (Ubicuo)**: EL SISTEMA mostrará un icono junto al nombre de la entrada Modelos de ML.
* **RF-10 (Ubicuo)**: EL SISTEMA mostrará la etiqueta "IA" junto al nombre de la entrada Modelos de ML.
* **RF-11 (Ubicuo)**: EL SISTEMA mostrará el logo de Retake en el menú de navegación de todas las páginas.
* **RF-12 (Dirigido por evento)**: CUANDO el usuario pulse el logo de Retake, EL SISTEMA lo llevará a Inicio.
* **RF-13 (No deseado)**: SI la imagen del logo de Retake no se puede cargar, ENTONCES EL SISTEMA mostrará en su lugar el texto "Retake".
* **RF-14 (Dirigido por evento)**: CUANDO el usuario pulse una entrada del menú, ya sea en la fila o en el panel, EL SISTEMA lo llevará a la sección correspondiente.
* **RF-15 (Dirigido por evento)**: CUANDO el usuario pulse la entrada de la sección en la que ya se encuentra, EL SISTEMA lo llevará al principio de esa página.

### 2.3 Menú plegado (pantallas estrechas)

* **RF-16 (Estado)**: MIENTRAS la ventana mida menos de 1024 px de ancho, EL SISTEMA agrupará las ocho entradas del menú detrás de un botón de menú.
* **RF-17 (Estado)**: MIENTRAS la ventana mida menos de 1024 px de ancho, EL SISTEMA mantendrá visibles fuera del panel el logo de Retake, el acceso a Modelos de ML y el botón de menú.
* **RF-18 (Dirigido por evento)**: CUANDO el usuario pulse el botón de menú, EL SISTEMA abrirá un panel con las ocho entradas del menú.
* **RF-19 (Estado)**: MIENTRAS la ventana mida menos de 1024 px de ancho, EL SISTEMA mostrará el selector de idioma al final del panel.
* **RF-20 (Dirigido por evento)**: CUANDO el usuario pulse una entrada del panel, EL SISTEMA cerrará el panel.
* **RF-21 (Dirigido por evento)**: CUANDO el usuario pulse fuera del panel o la tecla Escape, EL SISTEMA cerrará el panel.
* **RF-22 (Estado)**: MIENTRAS el panel esté abierto, EL SISTEMA impedirá que la página de detrás se desplace.
* **RF-23 (No deseado)**: SI la ventana pasa a medir 1024 px de ancho o más con el panel abierto, ENTONCES EL SISTEMA cerrará el panel.

### 2.4 Entrada activa, direcciones y navegación del navegador

* **RF-24 (Estado)**: MIENTRAS el usuario esté en una sección o en una de sus subpáginas, EL SISTEMA subrayará la entrada de esa sección como activa.
* **RF-25 (Estado)**: MIENTRAS el usuario esté en "Página no encontrada", EL SISTEMA no marcará ninguna entrada del menú como activa.
* **RF-26 (Ubicuo)**: EL SISTEMA asignará a cada sección del menú una dirección propia.
* **RF-27 (Dirigido por evento)**: CUANDO el usuario abra directamente o recargue la dirección de una sección, EL SISTEMA mostrará esa sección.
* **RF-28 (Dirigido por evento)**: CUANDO el usuario pulse Atrás o Adelante en el navegador, EL SISTEMA mostrará la página correspondiente a la dirección resultante.
* **RF-29 (No deseado)**: SI el usuario pulsa Atrás o Adelante en el navegador con el panel abierto, ENTONCES EL SISTEMA cerrará el panel.
* **RF-30 (Ubicuo)**: EL SISTEMA titulará la pestaña del navegador como "<nombre de la página> · Retake", en el idioma activo.
* **RF-31 (Estado)**: MIENTRAS el usuario esté en Inicio, EL SISTEMA titulará la pestaña del navegador únicamente como "Retake".

### 2.5 Distribución de la página de inicio

* **RF-32 (Ubicuo)**: EL SISTEMA reservará en Inicio un bloque para el spotlight justo debajo del menú de navegación.
* **RF-33 (Estado)**: MIENTRAS la ventana mida 1024 px de ancho o más, EL SISTEMA colocará el bloque de noticias a la derecha del spotlight.
* **RF-34 (Estado)**: MIENTRAS la ventana mida 1024 px de ancho o más, EL SISTEMA dará al spotlight dos tercios del ancho de la zona de contenido y al bloque de noticias el tercio restante.
* **RF-35 (Ubicuo)**: EL SISTEMA reservará en Inicio un bloque para la cuadrícula de partidos justo debajo del spotlight y del bloque de noticias.
* **RF-36 (Estado)**: MIENTRAS la ventana mida menos de 1024 px de ancho, EL SISTEMA apilará en una sola columna, en este orden, el spotlight, el bloque de noticias y la cuadrícula de partidos.

### 2.6 Secciones y bloques sin contenido

Se entiende por **bloque** cada uno de los huecos con contenido de la liga: la cinta de marcadores, el spotlight, las noticias y la cuadrícula de partidos. Una sección o un bloque **tiene contenido** cuando su propia spec de contenido está implementada. El bloque de demostración (§2.13) se considera un bloque con contenido.

* **RF-37 (Estado)**: MIENTRAS una sección del menú no tenga implementada su spec de contenido, EL SISTEMA mostrará en ella una página con el nombre de la sección y el aviso "Próximamente".
* **RF-38 (Estado)**: MIENTRAS un bloque no tenga implementada su spec de contenido, EL SISTEMA mostrará en su hueco el nombre del bloque y el aviso "Próximamente".
* **RF-39 (Estado)**: MIENTRAS un bloque no tenga implementada su spec de contenido, EL SISTEMA no mostrará en él ningún esqueleto de carga ni aviso de error.

### 2.7 Carga, errores y conexión de los bloques con contenido

* **RF-40 (Estado)**: MIENTRAS el contenido de un bloque se esté cargando, EL SISTEMA mostrará en ese bloque un esqueleto con la forma que defina su spec de contenido.
* **RF-41 (No deseado)**: SI el contenido de un bloque no se puede cargar, ENTONCES EL SISTEMA mostrará en ese bloque un aviso de error y un botón "Reintentar".
* **RF-42 (No deseado)**: SI un intento de carga de un bloque dura más de 15 segundos, contados desde el inicio de ese intento, ENTONCES EL SISTEMA lo tratará como un fallo de carga.
* **RF-43 (No deseado)**: SI el contenido de un bloque llega después de haberse mostrado su aviso de error, ENTONCES EL SISTEMA sustituirá el aviso por el contenido.
* **RF-44 (Dirigido por evento)**: CUANDO el usuario pulse "Reintentar" en un bloque, EL SISTEMA iniciará un nuevo intento de carga de ese bloque.
* **RF-45 (Ubicuo)**: EL SISTEMA no limitará el número de veces que el usuario puede pulsar "Reintentar".
* **RF-46 (No deseado)**: SI el usuario pulsa "Reintentar" varias veces seguidas, ENTONCES EL SISTEMA mantendrá un único intento de carga en curso para ese bloque.
* **RF-47 (Dirigido por evento)**: CUANDO un intento de carga termine con éxito, EL SISTEMA sustituirá el esqueleto por el contenido sin mostrar ningún aviso adicional.
* **RF-48 (No deseado)**: SI falla la carga de un bloque, ENTONCES EL SISTEMA mantendrá operativos el menú de navegación y el resto de bloques.
* **RF-49 (No deseado)**: SI cambia el tamaño de la ventana o se gira el dispositivo, ENTONCES EL SISTEMA conservará el estado de carga, error o contenido de cada bloque.
* **RF-50 (Estado)**: MIENTRAS el dispositivo no tenga conexión, EL SISTEMA mostrará un aviso general "Sin conexión".
* **RF-51 (Estado)**: MIENTRAS el dispositivo no tenga conexión, EL SISTEMA mantendrá visible el contenido ya cargado.
* **RF-52 (Dirigido por evento)**: CUANDO el dispositivo recupere la conexión, EL SISTEMA retirará el aviso "Sin conexión".
* **RF-53 (Dirigido por evento)**: CUANDO el dispositivo recupere la conexión, EL SISTEMA iniciará un nuevo intento de carga en cada bloque que esté mostrando un aviso de error.

### 2.8 Dirección inexistente

* **RF-54 (No deseado)**: SI el usuario abre una dirección que no corresponde a ninguna sección ni página de Retake, ENTONCES EL SISTEMA mostrará una página con el aviso "Página no encontrada".
* **RF-55 (Ubicuo)**: EL SISTEMA incluirá en la página "Página no encontrada" un enlace a Inicio.

### 2.9 Pie de página

* **RF-56 (Ubicuo)**: EL SISTEMA mostrará en el pie de página el nombre Retake.
* **RF-57 (Ubicuo)**: EL SISTEMA mostrará en el pie de página un aviso de que Retake es un proyecto escolar sin afiliación oficial con la Call of Duty League.
* **RF-58 (Ubicuo)**: EL SISTEMA mostrará en el pie de página el año de la temporada actual, tal como la define la spec 002 (RF-2 y RF-3 de esa spec).
  * *Nota (2026-09-22, decisión P-6 del plan):* hasta que exista la spec 003, el año es un valor provisional que se actualiza a mano en cada cambio de temporada.

### 2.10 Idioma de la interfaz

* **RF-59 (Ubicuo)**: EL SISTEMA ofrecerá en todas las páginas un selector de idioma con dos opciones: español e inglés.
* **RF-60 (Dirigido por evento)**: CUANDO un usuario visite Retake por primera vez, EL SISTEMA mostrará la interfaz en el primer idioma de la lista de preferencias del navegador que sea español o inglés.
* **RF-61 (Ubicuo)**: EL SISTEMA tratará cualquier variante regional del español (ej. `es-MX`) como español y cualquier variante regional del inglés (ej. `en-GB`) como inglés.
* **RF-62 (No deseado)**: SI la lista de preferencias del navegador no contiene español ni inglés, ENTONCES EL SISTEMA mostrará la interfaz en español.
* **RF-63 (Dirigido por evento)**: CUANDO el usuario elija un idioma en el selector, EL SISTEMA mostrará todos los textos de la interfaz en ese idioma.
* **RF-64 (Dirigido por evento)**: CUANDO el usuario elija un idioma en el selector, EL SISTEMA conservará la página, la posición de scroll y el estado del panel en que se encontraba.
* **RF-65 (Dirigido por evento)**: CUANDO el usuario vuelva a Retake desde el mismo navegador, EL SISTEMA mostrará la interfaz en el último idioma que eligió.
* **RF-66 (Ubicuo)**: EL SISTEMA recordará el idioma elegido sin fecha de caducidad.
* **RF-67 (Ubicuo)**: EL SISTEMA dará prioridad al idioma elegido en Retake sobre cualquier cambio posterior del idioma del navegador.
* **RF-68 (Estado)**: MIENTRAS una pestaña de Retake permanezca abierta sin recargarse, EL SISTEMA mantendrá en ella su idioma aunque el usuario elija otro en una pestaña distinta.
* **RF-69 (No deseado)**: SI no se puede recuperar el idioma que el usuario eligió anteriormente, ENTONCES EL SISTEMA aplicará la regla de primera visita (RF-60 a RF-62).
* **RF-70 (Ubicuo)**: EL SISTEMA traducirá las etiquetas de estado y de fase definidas en la spec 002 (ej. `en vivo`, `No disponible`, `Sin rol`, "Estadísticas pendientes", "semana").
  * *Nota (2026-09-22, aprobación de la spec 002):* la lista de etiquetas es la de la spec 002 aprobada: las fases son semana, grupo, winners bracket, losers bracket y gran final (RF-31 de la 002; "final" desaparece), y se añaden las etiquetas de su §2.9 (`Por definir`, "Ganador de", "Perdedor de", `No jugado`, `Corregido`, `Agente libre` y el aviso de tabla de posiciones no disponible). Las siglas `DQ`, `SMG` y `AR` no se traducen (RF-125 de la 002). La 001 se aprobó con una versión provisional de la 002; esta nota cierra esa excepción (decisión K-4 de la 002).
* **RF-71 (Ubicuo)**: EL SISTEMA mostrará las fechas y horas con el formato propio del idioma activo.
* **RF-72 (Ubicuo)**: EL SISTEMA mostrará sin traducir los nombres propios de la liga (franquicias, gamertags, eventos, mapas y modos de juego).

### 2.11 Accesibilidad (requisitos no funcionales)

* **RF-73 (Ubicuo)**: EL SISTEMA cumplirá el nivel AA de las WCAG 2.2 en todos los elementos del marco común.
* **RF-74 (Ubicuo)**: EL SISTEMA mantendrá un contraste mínimo de 4,5:1 entre cada texto del marco común y su fondo, incluida la entrada Modelos de ML sobre su color exclusivo.
* **RF-75 (Dirigido por evento)**: CUANDO el puntero pase sobre un elemento interactivo, EL SISTEMA mostrará un estado hover visible en ese elemento.
* **RF-76 (Dirigido por evento)**: CUANDO un elemento interactivo reciba el foco del teclado, EL SISTEMA mostrará un indicador de foco visible en ese elemento.
* **RF-77 (Dirigido por evento)**: CUANDO el usuario pulse un elemento interactivo, EL SISTEMA mostrará un estado active visible en ese elemento.
* **RF-78 (Ubicuo)**: EL SISTEMA permitirá usar con el teclado todos los elementos interactivos del marco común.
* **RF-79 (Ubicuo)**: EL SISTEMA dará un nombre legible por lectores de pantalla a cada elemento interactivo del marco común.
* **RF-80 (Ubicuo)**: EL SISTEMA indicará a los lectores de pantalla cuál es la entrada activa del menú.
* **RF-81 (Estado)**: MIENTRAS el navegador tenga un zoom del 200 %, EL SISTEMA mantendrá visibles y utilizables todos los contenidos y funciones del marco común.
* **RF-82 (Estado)**: MIENTRAS el panel esté abierto, EL SISTEMA mantendrá el foco del teclado dentro del panel.
* **RF-83 (Dirigido por evento)**: CUANDO se cierre el panel, EL SISTEMA devolverá el foco del teclado al botón de menú.

### 2.12 Animaciones del marco común

* **RF-84 (Dirigido por evento)**: CUANDO el panel se abra o se cierre, EL SISTEMA lo animará con un deslizamiento.
* **RF-85 (Dirigido por evento)**: CUANDO el usuario cambie de página, EL SISTEMA mostrará una transición entre la página anterior y la nueva.
* **RF-86 (Dirigido por evento)**: CUANDO el puntero pase sobre un botón del marco común, EL SISTEMA animará su estado hover.
* **RF-87 (Ubicuo)**: EL SISTEMA completará cada animación del marco común en 300 ms o menos.
* **RF-88 (Opcional)**: DONDE el usuario tenga activada la preferencia de reducir movimiento en su sistema, EL SISTEMA desactivará las animaciones del marco común.

### 2.13 Bloque de demostración

Mientras ningún bloque tenga su spec de contenido implementada, las reglas de carga, error y conexión (§2.7) no se podrían comprobar. El bloque de demostración existe solo para verificarlas y nunca lo ve el usuario final.

* **RF-89 (Opcional)**: DONDE Retake se ejecute en el entorno de desarrollo, EL SISTEMA ofrecerá una página de demostración con un bloque de contenido de prueba.
* **RF-90 (Ubicuo)**: EL SISTEMA aplicará al bloque de demostración todas las reglas de carga, error y conexión de los bloques con contenido (RF-40 a RF-53).
* **RF-91 (Opcional)**: DONDE Retake se ejecute en el entorno de desarrollo, EL SISTEMA permitirá forzar que la carga del bloque de demostración dure más de 15 segundos.
* **RF-92 (Opcional)**: DONDE Retake se ejecute en el entorno de desarrollo, EL SISTEMA permitirá forzar que la carga del bloque de demostración falle.
* **RF-93 (Opcional)**: DONDE Retake se ejecute en el entorno de desarrollo, EL SISTEMA permitirá forzar que el contenido del bloque de demostración llegue después de mostrarse su aviso de error.
* **RF-94 (Ubicuo)**: EL SISTEMA no mostrará en el menú ninguna entrada que lleve a la página de demostración.
* **RF-95 (No deseado)**: SI se abre la dirección de la página de demostración fuera del entorno de desarrollo, ENTONCES EL SISTEMA mostrará "Página no encontrada".

---

## 3. Casos Límite y Manejo de Errores

1. **Datos vacíos o no disponibles**:
   - Sección del menú sin spec de contenido implementada → página con su nombre y "Próximamente", también si se entra escribiendo su dirección (RF-27, RF-37).
   - Bloque sin spec de contenido implementada → su nombre y "Próximamente", sin esqueleto ni error (RF-38, RF-39).
   - Qué muestra cada bloque cuando la liga no tiene datos (por ejemplo, no hay partidos en vivo) lo decide la spec de ese bloque.
2. **Entradas no válidas**:
   - Dirección que no existe → "Página no encontrada" con enlace a Inicio, sin ninguna entrada activa (RF-25, RF-54, RF-55).
   - Idioma del navegador distinto de español o inglés → español (RF-62); variantes regionales → su idioma base (RF-61).
   - Idioma elegido que no se puede recuperar (por ejemplo, navegación privada o datos del navegador borrados) → regla de primera visita (RF-69).
   - Logo de Retake que no carga → texto "Retake" (RF-13).
3. **Peticiones lentas o interrumpidas**:
   - Cada bloque carga por separado y muestra su propio esqueleto (RF-40).
   - Un intento de más de 15 s cuenta como fallo; si los datos llegan después, sustituyen al aviso (RF-42, RF-43).
   - "Reintentar" no tiene límite de pulsaciones, pero solo hay un intento en curso por bloque (RF-44 a RF-46).
   - Un bloque en error no afecta al menú ni a los demás bloques (RF-48).
   - Sin conexión (al abrir o durante la navegación) → aviso general, se conserva lo ya cargado y, al volver la red, los bloques en error reintentan solos (RF-50 a RF-53).
4. **Cambios de tamaño y orientación**:
   - Al cruzar los 1024 px con el panel abierto, el panel se cierra (RF-23).
   - Los bloques conservan su estado al redimensionar o girar el dispositivo (RF-49).
   - Ningún ancho a partir de 320 px provoca scroll horizontal (RF-4).
5. **Navegación**:
   - Atrás y Adelante del navegador cambian de página y cierran el panel (RF-28, RF-29).
   - Pulsar la sección actual lleva al principio de la página (RF-15).
   - En las subpáginas queda activa la sección madre (RF-24).
6. **Idioma entre pestañas**: cada pestaña abierta conserva su idioma hasta que se recarga (RF-68).

---

## 4. Fuera de Alcance

* Contenido de la cinta de marcadores: qué partidos muestra, en qué orden y cómo se ve cada uno.
* Contenido del spotlight: marcador, votación de fanáticos, gráfica de tendencia, pestañas y resumen de jugadores.
* Contenido del bloque de noticias, incluido el carrusel.
* Contenido de la cuadrícula de partidos, incluidas la votación y los colores de cada franquicia.
* Estados vacíos propios de cada bloque (por ejemplo, "no hay partidos en vivo").
* Contenido de las secciones Partidos, Equipos, Jugadores, Torneos, Posiciones, Noticias y Modelos de ML.
* Qué ocurre con las direcciones de elementos inexistentes dentro de una sección (por ejemplo, un jugador que no existe); lo decide la spec de cada sección.
* Animaciones del contenido de los bloques y secciones (contadores, barras de progreso, gráficas); las definen sus specs de contenido.
* Comportamiento en ventanas de menos de 320 px de ancho.
* Cinta de marcadores o menú fijos al hacer scroll.
* Tema claro.
* Búsqueda global.
* Cuentas de usuario, inicio de sesión y perfiles.
* Idiomas distintos del español y el inglés.
* Traducción del contenido de las noticias.
* Redes sociales, enlaces legales y enlaces de contacto en el pie de página.
* Cómo se obtienen y actualizan los datos de la liga (spec 003).

---

## 5. Dudas y Aclaraciones Pendientes

### 5.1 Entrevista inicial con Hugo (2026-09-21)

| # | Duda | Decisión | Requisitos |
|---|---|---|---|
| 1 | Alcance de la cinta de marcadores | Solo el hueco; su contenido va en otra spec | RF-2 |
| 2 | Distribución de la página de inicio | Entra en la 001, pero solo los huecos | RF-32 a RF-36 |
| 3 | Entradas del menú | Inicio, Partidos, Equipos, Jugadores, Torneos, Posiciones, Noticias y Modelos de ML | RF-6 |
| 4 | Sección aún sin construir | Página navegable con el aviso "Próximamente" | RF-37 |
| 5 | Comportamiento al hacer scroll | Ni la cinta ni el menú quedan fijos | RF-3 |
| 6 | Menú en móvil | Se pliega tras un botón que abre un panel | RF-16 a RF-23 |
| 7 | Carga y fallos | Esqueleto y "Reintentar" en cada bloque; el resto sigue funcionando | RF-40 a RF-48 |
| 8 | Elementos del marco común | Entran la página 404, el logo que lleva a Inicio, el pie de página y el selector de idioma | RF-11, RF-12, RF-54 a RF-59 |
| 9 | Idioma inicial y persistencia | Idioma del navegador (ES/EN, si no, español) y se recuerda la elección | RF-60 a RF-69 |
| 10 | Orden del menú | Modelos de ML al final | RF-6 |
| 11 | Orden de los bloques del inicio en móvil | Spotlight, noticias y cuadrícula de partidos | RF-36 |
| 12 | Espera máxima de carga | 15 segundos | RF-42 |

### 5.2 Resolución de la auditoría QA con Hugo (2026-09-22)

| # | Hallazgo QA | Decisión | Requisitos |
|---|---|---|---|
| 13 | Qué muestran los huecos sin contenido (1.2, 1.3, 2.3) | Su nombre y "Próximamente"; sin esqueleto ni error | RF-38, RF-39 |
| 14 | Cómputo de los 15 s y datos tardíos (1.4, 2.4) | Por intento; si los datos llegan tarde, sustituyen al aviso | RF-42, RF-43 |
| 15 | Reintentos y conexión (3.4 a 3.7) | Sin límite, con un solo intento en curso; reintento automático al volver la red; aviso general "Sin conexión" | RF-44 a RF-46, RF-50 a RF-53 |
| 16 | Pérdida de conexión durante la navegación | El mismo aviso general; se conserva lo ya cargado | RF-50 a RF-52 |
| 17 | Cinta en "Próximamente" y 404 (1.1) | Sí, el marco es idéntico en todas las páginas | RF-1 |
| 18 | El menú no cabe a 768 px (2.2) | El umbral pasa a 1024 px | RF-7, RF-16 |
| 19 | Proporción del inicio (1.9, 4.8) | 2/3 spotlight y 1/3 noticias desde 1024 px | RF-33, RF-34, RF-36 |
| 20 | Modelos de ML y selector de idioma en el menú plegado (1.6, 1.13) | Fuera del panel: logo, ML y botón; el panel lleva las 8 entradas y, al final, el selector | RF-17 a RF-19 |
| 21 | Destacado de ML frente a la entrada activa (2.5, 4.6) | ML: fondo exclusivo, icono y etiqueta "IA"; la entrada activa se subraya | RF-8 a RF-10, RF-24 |
| 22 | Entrada activa en subpáginas y en la 404 (1.5) | Queda activa la sección madre; en la 404, ninguna | RF-24, RF-25 |
| 23 | Direcciones y botones del navegador (1.11, 3.8 a 3.11, 3.18) | Dirección propia por sección; Atrás y Adelante funcionan y cierran el panel; los elementos inexistentes los decide cada spec | RF-15, RF-26 a RF-29 |
| 24 | Alcance de la traducción (1.14, 1.15, 1.17) | Interfaz, etiquetas de la spec 002 y formatos de fecha; los nombres propios no se traducen | RF-60 a RF-62, RF-70 a RF-72 |
| 25 | Conflicto con la constitución §7.3 (4.7) | Se mantiene el inglés completo desde ya y queda registrado; la constitución no cambia | §1, §2.10 |
| 26 | Accesibilidad (4.1, 4.4, 4.5, 3.3, 3.19) | WCAG 2.2 nivel AA | RF-73 a RF-83 |
| 27 | Animaciones (4.3, 3.20) | Panel, transición de página y hover; 300 ms o menos; se desactivan con "reducir movimiento" | RF-84 a RF-88 |
| 28 | Ancho mínimo y tema (3.1, 4.6) | Desde 320 px; solo tema oscuro | RF-4, RF-5 |
| 29 | Persistencia del idioma (1.16, 3.13, 3.15, 3.16) | Sin caducidad; prevalece sobre el navegador; cada pestaña conserva el suyo; cambiar de idioma conserva página, scroll y panel | RF-64, RF-66 a RF-68 |
| 30 | Año del pie (1.12) | Año de la temporada actual según la spec 002 | RF-58 |
| 31 | Logo que no carga (3.17) | Texto "Retake" | RF-13 |
| 32 | Detalles de interfaz (3.2, 3.12, 3.21, 4.2) | Título de la pestaña, fondo bloqueado con el panel abierto, éxito sin aviso extra y estado conservado al redimensionar | RF-22, RF-30, RF-31, RF-47, RF-49 |
| 33 | RF-40 a RF-53 no se podían verificar porque la 001 no tiene bloques con contenido | Bloque de demostración, solo en el entorno de desarrollo y nunca visible para el usuario final | RF-89 a RF-95 |

### 5.3 Pendientes

Ninguna.

---

## 6. Criterios de Finalización

La spec 001 se da por terminada cuando se cumplan todas estas condiciones:

1. Hugo ha aprobado la spec y no queda ningún `[NECESITA ACLARACIÓN]` abierto.
2. Cada requisito, de RF-1 a RF-95, tiene un paso en la guía de verificación manual (constitución §5) y Hugo lo ha comprobado en el navegador.
3. Los requisitos de estructura, menú e inicio (RF-1 a RF-36) se han comprobado con la ventana a 320 px, 1023 px, 1024 px y 1440 px de ancho, y girando un dispositivo móvil.
4. Los requisitos de carga, error y conexión (RF-40 a RF-53) se han comprobado en el bloque de demostración (RF-89 a RF-93), simulando:
   - una carga lenta de más de 15 s;
   - una carga fallida;
   - datos que llegan después del error;
   - un corte y una recuperación de la conexión.
5. Fuera del entorno de desarrollo, la página de demostración no aparece en el menú y su dirección muestra "Página no encontrada" (RF-94, RF-95).
6. Todos los textos de la interfaz del marco común (menú, avisos, botones, títulos de pestaña, páginas "Próximamente" y "Página no encontrada", pie de página) aparecen en español y en inglés.
7. Una auditoría de accesibilidad del marco común no muestra ningún incumplimiento del nivel AA de las WCAG 2.2, y se ha completado un recorrido solo con teclado por todas las páginas del marco.
8. Con la preferencia "reducir movimiento" activada no se ve ninguna animación del marco común.
9. Se ha revisado el checklist de seguridad de la constitución (§6) para todo lo que abarca esta spec.
10. El estado de la spec ha pasado a `Aprobado` y refleja lo que realmente se construyó, sin desviaciones (constitución §1.3).

**Cierre (2026-09-22):** Hugo aprobó el cierre de la spec 001. Los diez criterios se dan por cumplidos:
- 206 pruebas unitarias y de componentes en verde;
- 118 pruebas de extremo a extremo en verde, en desarrollo y en producción;
- cero incumplimientos WCAG 2.2 AA;
- checklist de seguridad revisado;
- guía manual en [`verification-guide.md`](verification-guide.md);
- ajustes de implementación registrados en el plan, §10.
