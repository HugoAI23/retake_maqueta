# Plan: Estructura Base y Navegación

- **Spec**: [`001-core-layout-and-nav/spec.md`](spec.md) (`Aprobado`, 2026-09-22)
- **Fecha**: `2026-09-22`
- **Estado**: `Aprobado` (aprobado por Hugo el 2026-09-22)

Este documento describe **CÓMO** se construirá la spec 001. No contiene código: define módulos, contratos de datos, decisiones y fases. Cada parte indica qué requisitos (RF) cubre.

---

## 0. Resumen

- **Qué se construye:** una aplicación web de una sola página, solo frontend: Vite, React y Tailwind CSS, con Anime.js para las animaciones.
- **Qué no hace falta todavía:** backend (Python), base de datos (PostgreSQL) ni Bklit UI. La 001 no muestra datos de la liga ni gráficas.
- **Única excepción de datos:** el año de temporada del pie (RF-58), que por ahora es un valor provisional (§3.6 y P-6).
- **Cómo se organiza:** todo el marco cuelga de un **registro de secciones** y de un **registro de bloques**. Son dos listas declarativas que indican qué existe, en qué dirección y si ya tiene contenido. Cuando se implemente la spec de contenido de una sección o bloque, bastará con cambiar su marca para que deje de mostrar "Próximamente".
- **Dos piezas con estado:**
  - el **cargador de bloques**, una máquina de estados que cubre carga, error, 15 s, datos tardíos, reintentos y conexión;
  - el **módulo de idioma**, que resuelve el idioma inicial, lo guarda y lo aplica a cada pestaña.
- **Herramientas nuevas elegidas por Hugo** (constitución §3.2, detalle en §4.2): JavaScript, React Router, react-i18next, Vitest + Testing Library y Playwright + axe. El año del pie usa un valor provisional hasta que exista la spec 003.

---

## 1. Módulos

Estructura prevista de la aplicación, que vive en la **raíz del repositorio**, junto a `specs/` y `maqueta/` (decisión de Hugo, 2026-09-22). Los nombres de carpetas, archivos y componentes van en inglés (constitución §7.1).

```
src/
├── app/            Arranque, proveedores globales y tabla de rutas
├── config/         Constantes del marco y registros de secciones y bloques
├── layout/         Marco común: cinta, cabecera, menú, panel, pie, aviso de conexión
├── navigation/     Lógica de navegación: entrada activa, scroll al inicio, cierre del panel
├── pages/          Inicio, Próximamente, Página no encontrada y demostración (solo desarrollo)
├── blocks/         Huecos del inicio, esqueleto, aviso de error y cargador de bloques
├── connection/     Estado de conexión del dispositivo
├── i18n/           Idioma: resolución, persistencia, diccionarios y formatos
├── motion/         Animaciones con Anime.js y preferencia de reducir movimiento
└── shared/         Piezas reutilizables: logo, título de pestaña, foco
```

### 1.1 `app/` — arranque y rutas

| Pieza | Responsabilidad | RF |
|---|---|---|
| `App` | Monta los proveedores globales (idioma, conexión, movimiento) y el enrutador. | RF-1 |
| `routes` | Tabla de rutas generada a partir del registro de secciones: una por sección, la de "Página no encontrada" para cualquier otra dirección y la de demostración solo en desarrollo. | RF-26, RF-27, RF-54, RF-89, RF-95 |

### 1.2 `config/` — constantes y registros

| Pieza | Responsabilidad | RF |
|---|---|---|
| `layoutConstants` | Umbral de 1024 px, espera máxima de 15 000 ms, duración máxima de animación de 300 ms y ancho mínimo garantizado de 320 px. | RF-4, RF-7, RF-16, RF-42, RF-87 |
| `sectionsRegistry` | Las ocho secciones en orden, con su dirección, clave de texto, marca de destacada y marca de contenido (§3.1). | RF-6, RF-8 a RF-10, RF-26, RF-37 |
| `homeBlocksRegistry` | Los cuatro bloques (cinta, spotlight, noticias, cuadrícula) con su marca de contenido (§3.2). | RF-38, RF-39 |

### 1.3 `layout/` — marco común

| Componente | Responsabilidad | RF |
|---|---|---|
| `AppShell` | Ordena de arriba abajo la cinta, la cabecera, el aviso de conexión, la zona de contenido y el pie. Se usa en **todas** las rutas, incluidas la 404 y la de demostración. | RF-1, RF-3 |
| `ScoreTickerSlot` | Franja a todo el ancho, encima del menú. Muestra el bloque `ticker` según el registro. | RF-2, RF-38 |
| `SiteHeader` | Contiene el logo, el menú en fila (1024 px o más) o la versión plegada (menos de 1024 px), y el selector de idioma. | RF-7, RF-11, RF-16, RF-17 |
| `MainNav` | Fila horizontal con las ocho entradas, visible desde 1024 px. | RF-6, RF-7, RF-14, RF-24, RF-25, RF-80 |
| `NavItem` | Una entrada del menú: enlace, subrayado si está activa y tratamiento destacado (fondo, icono y "IA") si es Modelos de ML. | RF-8 a RF-10, RF-14, RF-15, RF-24, RF-75 a RF-77, RF-80 |
| `CompactNavBar` | Por debajo de 1024 px: logo, acceso directo a Modelos de ML y botón de menú. | RF-16, RF-17 |
| `MobileNavPanel` | Panel con las ocho entradas y, al final, el selector de idioma. Cubre las reglas de apertura y cierre, el fondo bloqueado y el foco atrapado. | RF-18 a RF-23, RF-29, RF-82 a RF-84 |
| `OfflineBanner` | Aviso general "Sin conexión" mientras no hay red. | RF-50, RF-52 |
| `SiteFooter` | Nombre, aviso de proyecto escolar y año de la temporada actual. | RF-56 a RF-58 |

### 1.4 `navigation/` — comportamiento de navegación

| Pieza | Responsabilidad | RF |
|---|---|---|
| `useActiveSection` | Calcula la sección activa a partir de la dirección actual: coincide la sección o cualquiera de sus subpáginas. En la 404 no hay ninguna. | RF-24, RF-25 |
| `useScrollTopOnSameSection` | Si se pulsa la entrada de la sección actual, vuelve al principio de la página: sin animación con reducir movimiento, con desplazamiento suave en caso contrario. | RF-15, RF-88 |
| `useNavPanelState` | Estado abierto o cerrado del panel. Se cierra al pulsar una entrada, al cambiar de dirección (incluidos Atrás y Adelante), con Escape, al pulsar fuera y al superar 1024 px. | RF-20, RF-21, RF-23, RF-28, RF-29 |

### 1.5 `pages/`

| Página | Responsabilidad | RF |
|---|---|---|
| `HomePage` | Rejilla de tres columnas desde 1024 px (spotlight en dos, noticias en una, cuadrícula debajo a todo el ancho) y una sola columna por debajo. | RF-32 a RF-36 |
| `ComingSoonPage` | Nombre de la sección y aviso "Próximamente". La usan todas las secciones marcadas sin contenido. | RF-37 |
| `NotFoundPage` | Aviso "Página no encontrada" y enlace a Inicio. | RF-54, RF-55, RF-95 |
| `BlockDemoPage` | **Solo en desarrollo.** Un bloque de prueba con controles para forzar cada escenario (§3.5). | RF-89 a RF-93 |

### 1.6 `blocks/`

| Pieza | Responsabilidad | RF |
|---|---|---|
| `BlockSlot` | Punto de entrada de cada hueco. Si el bloque no tiene contenido, muestra `ComingSoonBlock` y **no** pone en marcha el cargador. Si lo tiene, delega en `AsyncBlock`. | RF-38, RF-39 |
| `ComingSoonBlock` | Nombre del bloque y aviso "Próximamente". | RF-38 |
| `AsyncBlock` | Muestra el esqueleto, el error con "Reintentar" o el contenido según el estado del cargador. | RF-40, RF-41, RF-47 |
| `BlockSkeleton` | Esqueleto genérico al que cada spec de contenido dará su forma, mediante un parámetro de forma. | RF-40 |
| `BlockError` | Aviso de error y botón "Reintentar". El botón tiene un nombre accesible que incluye el nombre del bloque. | RF-41, RF-44, RF-79 |
| `useBlockLoader` | Máquina de estados del cargador (§3.4). | RF-42 a RF-49, RF-53, RF-90 |

### 1.7 `connection/`

| Pieza | Responsabilidad | RF |
|---|---|---|
| `ConnectionProvider` | Expone si hay conexión, a partir del estado de red del navegador y sus eventos de conexión y desconexión, y avisa cuando la red vuelve. | RF-50 a RF-53 |

### 1.8 `i18n/`

| Pieza | Responsabilidad | RF |
|---|---|---|
| `resolveInitialLocale` | Regla de primera visita: recorre la lista de idiomas del navegador, reduce cada variante a su idioma base y devuelve el primero que sea `es` o `en`. Si no hay ninguno, devuelve `es`. | RF-60 a RF-62, RF-69 |
| `localeStorage` | Guarda y lee la elección del usuario. Tolera que el almacenamiento no esté disponible y valida el valor leído (§5). | RF-65 a RF-67, RF-69 |
| `LocaleProvider` | Lee el idioma **solo al cargar la pestaña** y no escucha cambios de otras pestañas. Al cambiarlo, actualiza el idioma del documento y los textos sin reiniciar la página. | RF-63, RF-64, RF-68 |
| `LanguageSwitcher` | Selector de dos opciones (ES/EN). Indica cuál está activa y cada opción tiene un nombre accesible en su propio idioma. | RF-59, RF-63, RF-79 |
| `dictionaries` | Textos del marco en `es` y `en`, además de las etiquetas de estado y fase de la spec 002. | RF-63, RF-70 |
| `formatters` | Formato de fechas y horas según el idioma activo, con la API de internacionalización nativa del navegador. | RF-71 |

### 1.9 `motion/`

| Pieza | Responsabilidad | RF |
|---|---|---|
| `useReducedMotion` | Indica si el sistema pide reducir movimiento y reacciona si cambia. | RF-88 |
| `motionPresets` | Duraciones y curvas comunes, todas de 300 ms o menos. | RF-87 |
| `useSlideAnimation` | Deslizamiento de entrada y salida del panel con Anime.js. | RF-84 |
| `PageTransition` | Transición de la zona de contenido al cambiar de dirección. | RF-85 |
| `useHoverAnimation` | Animación de hover de los botones del marco con Anime.js. | RF-86 |

### 1.10 `shared/`

| Pieza | Responsabilidad | RF |
|---|---|---|
| `Logo` | Imagen del logo que enlaza a Inicio. Si la imagen falla, muestra el texto "Retake" sin perder el enlace. | RF-11 a RF-13 |
| `usePageTitle` | Título de la pestaña ("<página> · Retake", o solo "Retake" en Inicio), recalculado al cambiar de idioma. | RF-30, RF-31 |
| `useFocusContainment` | Mientras el panel está abierto, vuelve inerte el resto de la página y, al cerrarlo, devuelve el foco al botón de menú. | RF-82, RF-83 |

---

## 2. Contratos entre módulos (props e interfaces)

Se describen en tablas, sin código.

### 2.1 `NavItem`

| Prop | Tipo | Descripción |
|---|---|---|
| `section` | `SectionDefinition` | Entrada que representa (§3.1). |
| `isActive` | booleano | Si debe mostrarse subrayada e indicarse como página actual a los lectores de pantalla. |
| `variant` | `"row"` o `"panel"` | Si se pinta en la fila horizontal o dentro del panel. |
| `onNavigate` | acción | Se ejecuta al pulsar: el panel la usa para cerrarse (RF-20). |

### 2.2 `BlockSlot` y `AsyncBlock`

| Prop | Tipo | Descripción |
|---|---|---|
| `block` | `HomeBlockDefinition` | Qué bloque es y si tiene contenido (§3.2). |
| `load` | operación asíncrona que devuelve los datos | La aporta cada spec de contenido. En la 001 solo la usa el bloque de demostración. |
| `skeletonShape` | identificador de forma | Forma del esqueleto que definirá cada spec de contenido (RF-40). |
| `renderContent` | función de datos a vista | Cómo se pinta el contenido cargado. |

### 2.3 `useBlockLoader`

| Entrada | Salida |
|---|---|
| `load`, espera máxima (por defecto la constante de 15 s) | `state` (`BlockLoadState`, §3.4) y la acción `retry` |

### 2.4 Proveedores globales

| Proveedor | Expone |
|---|---|
| `LocaleProvider` | idioma activo, acción de cambio de idioma, función de traducción y formateadores |
| `ConnectionProvider` | si hay conexión y una suscripción al evento de recuperación de la red |
| `MotionProvider` | si hay que reducir el movimiento |

---

## 3. Modelo de datos

La 001 no guarda nada en servidor ni en base de datos. Los únicos datos son configuración estática, estado en memoria y una preferencia guardada en el navegador.

### 3.1 `SectionDefinition` (configuración estática)

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | texto | Identificador interno. |
| `path` | texto | Dirección propia de la sección (RF-26). |
| `labelKey` | texto | Clave del nombre en los diccionarios. |
| `featured` | booleano | `true` solo para Modelos de ML (RF-8 a RF-10, RF-17). |
| `hasContent` | booleano | `false` mientras no esté implementada su spec de contenido (RF-37). |

Valores iniciales, en el orden de RF-6. Las direcciones van en inglés (constitución §7.1):

| Orden | `id` | `path` | `featured` | `hasContent` |
|---|---|---|---|---|
| 1 | `home` | `/` | no | sí (la página de inicio, con sus huecos, forma parte de la 001) |
| 2 | `matches` | `/matches` | no | no |
| 3 | `teams` | `/teams` | no | no |
| 4 | `players` | `/players` | no | no |
| 5 | `tournaments` | `/tournaments` | no | no |
| 6 | `standings` | `/standings` | no | no |
| 7 | `news` | `/news` | no | no |
| 8 | `mlModels` | `/ml-models` | **sí** | no |

Dirección de la página de demostración: `/dev/block-demo`. No figura en el registro, así que nunca aparece en el menú (RF-94).

### 3.2 `HomeBlockDefinition` (configuración estática)

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `ticker`, `spotlight`, `news` o `matchGrid` | Identificador del bloque. |
| `labelKey` | texto | Clave del nombre del bloque, que se muestra con "Próximamente". |
| `hasContent` | booleano | En la 001 los cuatro valen `false` (RF-38, RF-39). |

### 3.3 `LocaleCode` y preferencia guardada

| Elemento | Valor | Descripción |
|---|---|---|
| `LocaleCode` | `es` o `en` | Idiomas admitidos (RF-59). |
| Clave guardada | `retake.locale` | Almacenamiento local del navegador, sin caducidad (RF-66). |
| Validación | solo `es` o `en` | Cualquier otro valor, o un almacenamiento inaccesible, se trata como "sin elección" y se aplica la regla de primera visita (RF-69). |

### 3.4 `BlockLoadState` (estado en memoria de cada bloque)

| Campo | Tipo | Descripción |
|---|---|---|
| `status` | `loading`, `error` o `ready` | Estado visible del bloque. |
| `errorReason` | `failed` o `timeout` | Motivo del error (para registro y pruebas; el aviso visible es el mismo). |
| `data` | datos del bloque | Presente solo en `ready`. |
| `attempt` | número | Contador de intentos, para distinguir el intento vigente de los antiguos. |
| `inFlight` | booleano | Si hay un intento dentro de su ventana de 15 s. |

**Transiciones:**

| Desde | Evento | Hacia | RF |
|---|---|---|---|
| (inicio) | se monta el bloque | `loading` | RF-40 |
| `loading` | llegan los datos | `ready` | RF-47 |
| `loading` | falla la operación | `error` (`failed`) | RF-41 |
| `loading` | pasan 15 s desde el inicio del intento | `error` (`timeout`) | RF-42 |
| `error` | llegan los datos de un intento anterior | `ready` | RF-43 |
| `error` | el usuario pulsa "Reintentar" | `loading` (nuevo intento) | RF-44, RF-45 |
| `error` | la red vuelve | `loading` (nuevo intento) | RF-53 |
| `loading` | "Reintentar" o vuelta de la red | se ignora: sigue un único intento en curso | RF-46 |
| cualquiera | cambia el tamaño o la orientación | sin cambio | RF-49 |
| `ready` | se pierde la red | sin cambio: el contenido sigue visible | RF-51 |

Reglas complementarias:
- Una vez en `ready`, los resultados tardíos de intentos anteriores se descartan.
- Cada bloque tiene su propio cargador, así que el fallo de uno no afecta a los demás (RF-48).

### 3.5 `DemoScenario` (solo desarrollo)

| Escenario | Comportamiento del bloque de demostración | RF |
|---|---|---|
| `ok` | Los datos llegan en 1 s. | RF-47 |
| `fail` | La carga falla en 1 s. | RF-92 |
| `hang` | La carga no termina nunca, así que el error sale a los 15 s. | RF-91 |
| `late` | Los datos llegan a los 20 s, después del error de los 15 s. | RF-91, RF-93 |

El corte de conexión no es un escenario: se simula desde el propio navegador, en las herramientas de desarrollo o poniendo el equipo sin red.

### 3.6 `SeasonInfo` (contrato con la spec 002)

| Campo | Tipo | Descripción |
|---|---|---|
| `year` | número | Año de la temporada actual según RF-2 y RF-3 de la spec 002. |

**Origen provisional (P-6):** mientras no exista la spec 003, `year` sale de un valor de configuración (`2026`) que se actualiza a mano en cada cambio de temporada. El pie solo conoce el contrato `SeasonInfo`, así que cuando exista la 003 bastará con cambiar la fuente del valor, sin tocar el pie.

---

## 4. Decisiones

### 4.1 Decisiones de diseño (dentro del stack aprobado)

| # | Decisión | Alternativa descartada | Justificación | RF |
|---|---|---|---|---|
| D-1 | **Adaptación a pantalla solo con estilos:** los bloques se pintan una sola vez y los estilos los recolocan en cada tamaño. | Montar componentes distintos según el ancho. | Si cambia el componente al cruzar los 1024 px, React lo desmonta y el bloque pierde su estado de carga o error. Hacerlo solo con estilos cumple RF-49 sin lógica extra. | RF-33 a RF-36, RF-49 |
| D-2 | **Umbral en el punto `lg` de Tailwind (1024 px).** | Definir un punto de corte propio. | El `lg` de Tailwind vale exactamente 1024 px, así que no hace falta configuración adicional y es la convención que conoce cualquier desarrollador de Tailwind. | RF-7, RF-16, RF-23, RF-33, RF-34, RF-36 |
| D-3 | **Registros declarativos** de secciones y bloques, con la marca `hasContent`. | Comprobar en cada página si existe su implementación. | Una lista única alimenta el menú, las rutas, "Próximamente" y los títulos. Activar una sección en el futuro consiste en cambiar una marca, y el orden de RF-6 queda en un solo sitio. | RF-6, RF-26, RF-37, RF-38 |
| D-4 | **Máquina de estados explícita** en el cargador de bloques. | Varios indicadores independientes (cargando, error, datos) sin transiciones definidas. | Los casos de 15 s, datos tardíos, intento único y vuelta de la red se cruzan entre sí. Una tabla de transiciones cerrada (§3.4) evita estados imposibles y se prueba entera con temporizadores simulados. | RF-40 a RF-47, RF-53 |
| D-5 | **Al agotar los 15 s no se cancela la petición**, solo se marca el error. | Cancelar la petición al llegar a los 15 s. | Si se cancelara, los datos nunca llegarían tarde y RF-43 no se podría cumplir. | RF-42, RF-43 |
| D-6 | **"Intento en curso" es el que está dentro de su ventana de 15 s.** Los intentos vencidos pueden seguir entregando datos. | Bloquear "Reintentar" hasta que termine cualquier petición previa. | Tras un error por tiempo, el usuario debe poder reintentar (RF-44) aunque la petición antigua siga viva, y si esta llega antes, se aprovecha (RF-43). | RF-43, RF-44, RF-46 |
| D-7 | **Estado de conexión según el navegador**, con sus eventos de conexión y desconexión. | Consultar periódicamente un servidor para comprobar la red. | La 001 no tiene servidor, y consultar cada pocos segundos gasta batería y datos. Limitación asumida: el navegador puede creer que hay red en una wifi sin internet; en ese caso, el bloque fallará por tiempo (RF-42), que es el comportamiento previsto. | RF-50 a RF-53 |
| D-8 | **El idioma se lee solo al cargar la pestaña** y no se escuchan los cambios de otras pestañas. | Sincronizar el idioma entre pestañas. | RF-68 exige que cada pestaña conserve su idioma hasta recargarla. | RF-65 a RF-68 |
| D-9 | **El idioma no forma parte de la dirección:** `/players` y no `/es/players`. | Prefijo de idioma en la dirección. | La spec no pide direcciones por idioma, y el prefijo obligaría a redirigir al cambiar de idioma, cuando RF-64 pide conservar página y scroll. | RF-26, RF-64 |
| D-10 | **Foco atrapado con el atributo nativo `inert`** sobre el resto de la página mientras el panel está abierto. | Librería de captura de foco. | `inert` es estándar en todos los navegadores actuales: bloquea el foco **y** oculta el fondo a los lectores de pantalla, sin añadir dependencias. | RF-82, RF-83 |
| D-11 | **Hover animado con Anime.js**, como indica la constitución. | Transiciones de CSS de Tailwind. | La constitución (§2) asigna expresamente a Anime.js los estados hover y active de los botones. Las transiciones de CSS serían más sencillas, pero contradirían ese punto. | RF-86, RF-87 |
| D-12 | **Una sola capa de movimiento** (`motion/`) por la que pasan todas las animaciones y que consulta la preferencia de reducir movimiento. | Que cada componente compruebe la preferencia por su cuenta. | Garantiza que ninguna animación olvide RF-87 o RF-88, y la regla se prueba en un solo sitio. | RF-84 a RF-88 |
| D-13 | **Página de demostración solo en el paquete de desarrollo:** se registra y se carga únicamente en el modo de desarrollo de Vite. | Página siempre incluida, oculta tras una bandera. | Cumple RF-95 y evita distribuir en producción código que solo sirve para pruebas (constitución §6). | RF-89, RF-94, RF-95 |
| D-14 | **Selector de idioma de dos botones** (ES/EN) que indican cuál está activo. | Lista desplegable. | Con dos idiomas, un conmutador permite cambiar con una sola pulsación y deja ver ambas opciones. | RF-59, RF-79 |
| D-15 | **Los nombres propios de la liga no pasan por el traductor:** se pintan tal cual llegan en los datos. Solo pasan por los diccionarios los textos del marco y las etiquetas de la spec 002. | Traducir cualquier texto visible. | Así RF-72 se cumple por construcción y no depende de que nadie añada excepciones. | RF-70, RF-72 |
| D-16 | **Contraste de colores fijado en variables de diseño** del tema de Tailwind, cada una con su contraste verificado. | Elegir colores componente a componente. | El 4,5:1 se comprueba una sola vez por pareja de colores y la paleta es la misma en todo el sitio (constitución §4.5). | RF-5, RF-74 |
| D-17 | **Contratos documentados con comentarios JSDoc** (en español) y verificados con pruebas, como consecuencia de P-1. | Validar las props en ejecución con PropTypes. | PropTypes es una dependencia más, y React 19 ya no la tiene en cuenta. Los comentarios JSDoc dan al editor ayuda de autocompletado sin añadir ninguna librería. | §2, §3 |

### 4.2 Decisiones tomadas por Hugo (constitución §3.2)

Estas herramientas no figuran en el stack de la constitución, así que se presentaron como comparativa y **Hugo eligió** el 2026-09-22:

| # | Decisión de Hugo | Descartada |
|---|---|---|
| P-1 | **JavaScript** | TypeScript |
| P-2 | **React Router** | TanStack Router |
| P-3 | **react-i18next**, con detección y persistencia del idioma propias | Solución propia completa |
| P-4 | **Vitest + Testing Library** | Jest + Testing Library |
| P-5 | **Playwright + axe** | Cypress |
| P-6 | **Valor de configuración provisional** para el año del pie | Esperar a la spec 003 |

A continuación se conservan las comparativas que sirvieron de base.

#### P-1 — Lenguaje: TypeScript o JavaScript

| | **A. TypeScript** | **B. JavaScript** |
|---|---|---|
| Ventajas | Los contratos de §2 y §3 quedan comprobados por el editor. Los errores de props y estados se detectan antes de ejecutar. Es el estándar del sector y aporta valor al portafolio. | Sin paso de tipos: se escribe menos y se arranca antes. |
| Desventajas | Hay que aprender la sintaxis de tipos. | Los contratos quedan solo como documentación y los errores aparecen en ejecución. |
| Curva | Media: los tipos básicos se aprenden en pocos días. | Ninguna. |

Recomendación del agente: A. **Decisión de Hugo: B (JavaScript).** Consecuencia: los contratos de §2 y §3 se documentan con comentarios JSDoc y se protegen con pruebas (D-17).

#### P-2 — Enrutador

| | **A. React Router** | **B. TanStack Router** |
|---|---|---|
| Ventajas | El más usado del ecosistema, con mucha documentación. Marca la entrada activa de forma nativa (RF-24, RF-80) y gestiona Atrás y Adelante sin configuración. | Direcciones con tipos estrictos y carga de datos integrada. |
| Desventajas | Tiene varios modos de uso que pueden confundir al empezar. | Comunidad más pequeña y más conceptos que aprender. |
| Curva | Baja. | Media-alta. |

**Decisión de Hugo: A (React Router)**, en su modo de librería, el más simple: la 001 solo necesita rutas, enlaces y la marca de entrada activa.

#### P-3 — Internacionalización

| | **A. react-i18next** | **B. Solución propia** (contexto de React con diccionarios JSON) |
|---|---|---|
| Ventajas | Estándar del sector. Resuelve de serie las variantes regionales (RF-61), el primer idioma admitido de la lista (RF-60), los plurales y las interpolaciones. | Sin dependencias, y cada línea es didáctica. |
| Desventajas | Tiene muchas opciones y hay que configurarlo con cuidado para que no sincronice pestañas (RF-68). | Plurales, interpolación y detección hay que escribirlos y probarlos a mano. |
| Curva | Media. | Baja al principio, pero el coste crece con cada spec. |

**Decisión de Hugo: A (react-i18next)**, con la detección y la persistencia **propias** (`resolveInitialLocale` y `localeStorage`) para controlar exactamente RF-60 a RF-69.

#### P-4 — Pruebas unitarias y de componentes

| | **A. Vitest + Testing Library** | **B. Jest + Testing Library** |
|---|---|---|
| Ventajas | Usa la misma configuración que Vite, arranca rápido y simula temporizadores, algo imprescindible para probar los 15 s. | El más conocido históricamente. |
| Desventajas | Algo menos de material antiguo en internet. | Necesita configuración extra para convivir con Vite. |
| Curva | Baja: su API es casi idéntica a la de Jest. | Baja. |

**Decisión de Hugo: A (Vitest + Testing Library).**

#### P-5 — Pruebas de extremo a extremo y accesibilidad

| | **A. Playwright + axe** | **B. Cypress** |
|---|---|---|
| Ventajas | Simula en una misma prueba el tamaño de ventana, la falta de red, la reducción de movimiento, el idioma del navegador y **varias pestañas** (RF-68). axe audita automáticamente el nivel AA de las WCAG. | Interfaz visual muy amigable. |
| Desventajas | Menos visual al depurar. | No admite varias pestañas, así que RF-68 no se podría probar, y la simulación de idioma y de red es más limitada. |
| Curva | Media. | Media. |

**Decisión de Hugo: A (Playwright + axe).**

#### P-6 — Origen del año de temporada del pie (RF-58)

| | **A. Valor de configuración provisional** | **B. Esperar a la spec 003** |
|---|---|---|
| Ventajas | La 001 se cierra completa. El pie consume el contrato `SeasonInfo` (§3.6), y cuando exista la spec 003 solo cambia de dónde sale el valor. | Nunca hay un dato mantenido a mano. |
| Desventajas | Hay que actualizar el valor a mano en cada cambio de temporada hasta que exista la 003, y eso incumple parcialmente RF-3 de la spec 002. | RF-58 no se podría verificar y la 001 no se podría cerrar. |

**Decisión de Hugo: A.** La spec 001 deja constancia en RF-58 de que el año es provisional hasta la 003, para evitar desviaciones entre spec y código (constitución §1.3).

---

## 5. Seguridad (constitución §6)

| Vector | Medida en la 001 | RF |
|---|---|---|
| XSS | No hay formularios. Todo texto se pinta con el escapado nativo de React y está prohibido insertar HTML sin escapar. La 404 no muestra la dirección escrita por el usuario. | RF-54 |
| Almacenamiento manipulado | El idioma guardado se valida contra `es` y `en`; cualquier otro valor se ignora. | RF-69 |
| Código de pruebas en producción | La página de demostración no se incluye en la versión de producción (D-13). | RF-95 |
| Credenciales | La 001 no usa claves ni secretos. Si más adelante aparecen, irán en variables de entorno (constitución §6.3). | — |
| SQL | La 001 no accede a base de datos. | — |

---

## 6. Estrategia de pruebas

Tres niveles automáticos más la guía manual obligatoria (constitución §5), con las herramientas elegidas en P-4 y P-5.

### 6.1 Niveles

| Nivel | Herramienta | Qué prueba |
|---|---|---|
| **Unitario** | Vitest | Lógica pura sin interfaz: `resolveInitialLocale`, `localeStorage`, `useActiveSection`, el cargador de bloques con temporizadores simulados, los registros y la completitud de los diccionarios. |
| **Componente** | Vitest + Testing Library | Cada componente del marco, aislado: menú, panel, logo, pie, bloques y selector de idioma, incluidos los roles y nombres accesibles. |
| **Extremo a extremo** | Playwright + axe | La aplicación real en el navegador: tamaños de ventana, recarga, Atrás y Adelante, falta de red, varias pestañas, idioma del navegador, reducción de movimiento, zoom y auditoría WCAG. |
| **Manual** | Guía paso a paso (constitución §5) | Todo lo visual y subjetivo: aspecto de los estados hover y active, fluidez de las animaciones y giro de un dispositivo real. |

### 6.2 Matriz de cobertura

| RF | Qué se comprueba | Unit. | Comp. | E2E | Manual |
|---|---|:-:|:-:|:-:|:-:|
| RF-1 a RF-3 | Orden del marco en todas las rutas (incluidas la 404 y "Próximamente") y cinta y menú no fijos al hacer scroll | | ✓ | ✓ | ✓ |
| RF-4 | Sin scroll horizontal a 320, 1023, 1024 y 1440 px | | | ✓ | ✓ |
| RF-5 | Sin opción de tema claro; se mantiene oscuro aunque el sistema pida tema claro | | | ✓ | |
| RF-6 | Orden de las ocho entradas, en la fila y en el panel | ✓ | ✓ | | |
| RF-7 | Fila completa desde 1024 px | | | ✓ | ✓ |
| RF-8 a RF-10 | Destacado de Modelos de ML: fondo exclusivo, icono y "IA" | | ✓ | | ✓ |
| RF-11 a RF-13 | Logo en todas las páginas, lleva a Inicio, texto si falla la imagen | | ✓ | ✓ | |
| RF-14, RF-15 | Navegación por entradas y vuelta al principio en la sección actual | | ✓ | ✓ | |
| RF-16 a RF-23 | Menú plegado, panel, cierres (entrada, fuera, Escape, 1024 px) y fondo bloqueado | | ✓ | ✓ | ✓ |
| RF-24, RF-25 | Entrada activa (incluidas subpáginas) y ninguna en la 404 | ✓ | ✓ | | |
| RF-26 a RF-29 | Direcciones propias, apertura directa, recarga, Atrás y Adelante con el panel abierto | | | ✓ | |
| RF-30, RF-31 | Título de la pestaña por página e idioma | | ✓ | ✓ | |
| RF-32 a RF-36 | Distribución del inicio: 2/3 y 1/3 desde 1024 px, apilado por debajo | | | ✓ | ✓ |
| RF-37 | "Próximamente" en las siete secciones sin contenido | ✓ | ✓ | ✓ | |
| RF-38, RF-39 | Huecos con "Próximamente", sin esqueleto ni error | | ✓ | | |
| RF-40 a RF-47 | Esqueleto, error, 15 s, datos tardíos, reintento sin límite con intento único y éxito sin aviso | ✓ | ✓ | ✓ | ✓ |
| RF-48 | El fallo de un bloque no afecta al menú ni a otros bloques | | ✓ | ✓ | |
| RF-49 | El estado se conserva al cruzar 1024 px y al girar | | | ✓ | ✓ |
| RF-50 a RF-53 | Aviso "Sin conexión", contenido conservado y reintento automático al volver la red | ✓ | ✓ | ✓ | ✓ |
| RF-54, RF-55 | 404 con enlace a Inicio | | ✓ | ✓ | |
| RF-56 a RF-58 | Contenido del pie | | ✓ | | |
| RF-59 a RF-62 | Selector e idioma inicial (listas `fr,en`, `es-MX`, `en-GB`, `de` → `es`) | ✓ | ✓ | ✓ | |
| RF-63, RF-64 | Cambio de idioma que conserva página, scroll y panel | | ✓ | ✓ | |
| RF-65 a RF-69 | Persistencia, prioridad sobre el navegador, pestañas independientes y almacenamiento inaccesible o manipulado | ✓ | | ✓ | |
| RF-70 | Todas las etiquetas de la spec 002 existen en `es` y `en` | ✓ | | | |
| RF-71 | Formato de fecha y hora por idioma | ✓ | | | |
| RF-72 | Los nombres propios no pasan por el traductor (revisión de código y prueba con un nombre de ejemplo) | | ✓ | | |
| RF-73, RF-74 | Auditoría del nivel AA de las WCAG 2.2 en cada ruta, a 320 y 1440 px, con el panel abierto y cerrado; contraste de las variables de color | ✓ | | ✓ | |
| RF-75 a RF-77 | Estados hover, focus y active visibles | | | | ✓ |
| RF-78 a RF-80 | Recorrido completo con teclado, nombres accesibles y página actual indicada | | ✓ | ✓ | ✓ |
| RF-81 | Zoom al 200 %, simulado como una ventana de 1280 px al 50 % de ancho | | | ✓ | ✓ |
| RF-82, RF-83 | Foco atrapado en el panel y devuelto al botón | | ✓ | ✓ | |
| RF-84 a RF-87 | Animaciones presentes y de 300 ms o menos | ✓ | | | ✓ |
| RF-88 | Sin animaciones con reducción de movimiento | ✓ | | ✓ | |
| RF-89 a RF-93 | Página de demostración y sus cuatro escenarios | | ✓ | ✓ | ✓ |
| RF-94, RF-95 | Sin entrada en el menú; la versión de producción responde con 404 en `/dev/block-demo` | ✓ | | ✓ | |

### 6.3 Reglas de las pruebas

- Los tiempos (15 s, 20 s y 300 ms) se prueban con **temporizadores simulados**, nunca esperando en tiempo real.
- Las pruebas de extremo a extremo se ejecutan contra la **versión de producción** (para RF-95) y contra la de desarrollo (para RF-89 a RF-93).
- Cada fase del §7 termina con sus pruebas en verde y con su bloque de la guía manual entregado a Hugo.

---

## 7. Plan de implementación (fases)

Cada fase se puede verificar por separado. `tasks.md` desglosará cada una en tareas atómicas.

| Fase | Contenido | RF |
|---|---|---|
| **F0. Base del proyecto** | Proyecto Vite + React en JavaScript, Tailwind con las variables de diseño del tema oscuro, Anime.js, React Router, react-i18next, Vitest + Testing Library y Playwright + axe. Constantes de `config/`. | RF-5, RF-74 (paleta) |
| **F1. Idioma** | `resolveInitialLocale`, `localeStorage`, `LocaleProvider`, diccionarios `es` y `en` (incluidas las etiquetas de la spec 002) y formateadores. | RF-60 a RF-72 |
| **F2. Marco y rutas** | `AppShell`, registros, tabla de rutas, `ComingSoonPage`, `NotFoundPage`, `SiteFooter`, `Logo` y `usePageTitle`. | RF-1 a RF-4, RF-11 a RF-13, RF-26, RF-27, RF-30, RF-31, RF-37, RF-54 a RF-58 |
| **F3. Menú** | `MainNav`, `NavItem`, destacado de Modelos de ML, entrada activa, selector de idioma en la fila, vuelta al principio en la sección actual. | RF-6 a RF-10, RF-14, RF-15, RF-24, RF-25, RF-59, RF-80 |
| **F4. Menú plegado** | `CompactNavBar`, `MobileNavPanel`, estado del panel, fondo bloqueado, foco atrapado y cierres. | RF-16 a RF-23, RF-28, RF-29, RF-82, RF-83 |
| **F5. Inicio y huecos** | `HomePage`, `ScoreTickerSlot`, `BlockSlot` y `ComingSoonBlock`. | RF-32 a RF-39 |
| **F6. Carga y conexión** | `useBlockLoader`, `AsyncBlock`, `BlockSkeleton`, `BlockError`, `ConnectionProvider`, `OfflineBanner` y `BlockDemoPage`. | RF-40 a RF-53, RF-89 a RF-95 |
| **F7. Movimiento** | `motion/`: panel, transición de página, hover y reducción de movimiento. | RF-84 a RF-88 |
| **F8. Accesibilidad y cierre** | Auditoría WCAG, recorrido con teclado, zoom al 200 %, estados hover, focus y active, checklist de seguridad y guía manual completa. | RF-73 a RF-81, criterios de finalización 1 a 10 de la spec |

---

## 8. Riesgos y dependencias

| Riesgo | Impacto | Mitigación |
|---|---|---|
| La spec 002 sigue en revisión | RF-58 (año de temporada) y RF-70 (lista de etiquetas) dependen de ella. | Año provisional (P-6). Las etiquetas se toman de la versión actual de la 002 y se revisan cuando se apruebe. |
| El alojamiento de producción aún no está decidido | RF-27 (abrir o recargar la dirección de una sección) exige que el servidor devuelva la aplicación en cualquier dirección. | Queda como requisito para la spec o tarea de despliegue. En desarrollo, Vite ya lo hace. |
| Ocho entradas, logo, "IA" y selector en inglés a 1024 px | Podría romperse RF-7 o aparecer scroll horizontal (RF-4). | Prueba de extremo a extremo específica a 1024 px en inglés. Si no cabe, hay que volver a la spec, no ajustar en silencio (constitución §1.3). |
| Falsos positivos del estado de red del navegador | Una wifi sin internet no muestra "Sin conexión". | Asumido en D-7: el bloque cae por tiempo a los 15 s (RF-42). |
| Hover animado con Anime.js en muchos botones | Coste de rendimiento si se anima cada elemento por separado. | Una sola capa de movimiento (D-12) y solo propiedades baratas de animar (opacidad y desplazamiento). |

---

## 9. Pendiente para aprobar este plan

1. ~~Elegir P-1 a P-6 (§4.2).~~ Resuelto el 2026-09-22.
2. ~~Anotar en la spec 001 que el año es provisional hasta la spec 003.~~ Hecho en RF-58.
3. ~~Aprobar el plan.~~ Aprobado el 2026-09-22. El siguiente paso, cuando Hugo lo pida, es `tasks.md`.

---

## 10. Registro de implementación (2026-09-22)

Ajustes surgidos al implementar, registrados para que plan y código no se desincronicen (constitución §1.3). Ninguno cambia los requisitos de la spec.

| # | Ajuste | Motivo | RF |
|---|---|---|---|
| I-1 | Enlace "Saltar al contenido" al principio de cada página. | El criterio 2.4.1 de las WCAG (nivel A) exige poder saltarse los bloques repetidos (cinta y menú). | RF-73, RF-78 |
| I-2 | Botón "Cerrar menú" dentro del panel móvil. | Con el resto de la página inerte (D-10), el botón ☰ deja de ser accesible; el panel necesita su propio control de cierre, además de Escape y pulsar fuera. | RF-21, RF-78, RF-82 |
| I-3 | El panel se anuncia como diálogo modal. | Así los lectores de pantalla saben que el resto de la página no está disponible mientras está abierto. | RF-79, RF-82 |
| I-4 | Los textos de la demostración están en `pages/dev/demoDictionary.js` y no en los diccionarios principales. La ruta de la demostración se añade a `routeDefinitions` con `devRoutes`, solo en desarrollo. | Así ni su código, ni sus textos, ni su dirección llegan al paquete de producción (comprobado con una prueba de extremo a extremo). | RF-95 |
| I-5 | `LOGO_SRC` vale `null` hasta que Hugo aporte el archivo del logo; mientras tanto se muestra el texto "Retake". | Dependencia externa de `tasks.md`. Cuando llegue el archivo, basta con ponerlo en `public/` y cambiar esa constante. | RF-11, RF-13 |
| I-6 | La vuelta al principio de la página (RF-15) se anima con Anime.js en 300 ms, en lugar del desplazamiento suave del navegador. | La duración del desplazamiento suave nativo no se puede controlar y podría superar los 300 ms de RF-87. | RF-15, RF-87 |
| I-7 | El hover animado se aplica mediante un componente común, `motion/AnimatedButton`: botón de menú, cierre del panel, selector de idioma y "Reintentar". | Un único punto consulta la preferencia de reducir movimiento (D-12). | RF-86, RF-88 |
| I-8 | El cargador de bloques lanza su primer intento una sola vez por instancia de componente. | En desarrollo, el `StrictMode` de React monta dos veces cada componente y habría duplicado la carga, lo que falsearía el contador de la demostración (RF-46). | RF-46 |
| I-9 | Tailwind CSS 4 lee los colores con `@config` desde `tailwind.config.js`, que importa `src/config/designTokens.js`. | Es la forma de que Tailwind y la prueba de contraste compartan un único módulo de colores (T-004, T-008). | RF-5, RF-74 |
| I-10 | Versiones instaladas: Vite 8, React 19, React Router 8, i18next 26 / react-i18next 17, Anime.js 4, Tailwind CSS 4, Vitest 5, Playwright 1.63. Se eliminó `oxlint`, que traía la plantilla de Vite. | Versiones estables vigentes. El linter no estaba entre las herramientas aprobadas (constitución §3.2). | — |
| I-11 | `.claude/launch.json` define el servidor de desarrollo para la vista previa del agente. | Herramienta de trabajo del agente; no forma parte de la aplicación. | — |
