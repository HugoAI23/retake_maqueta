# Spec: Datos de la Liga

- **ID**: `002-league-data`
- **Fecha**: `2026-09-22` (creada el 2026-09-21; revisada tras la revisión QA, revisión QA cerrada)
- **Estado**: `Aprobado` (aprobada por Hugo el 2026-09-22; revisiones R-1 y R-2 del 2026-09-22 durante el plan y aclaraciones R-3 a R-5 durante la implementación; cambios C-4 a C-10, C-12 y C-13 de la spec 003 aplicados el 2026-09-23; ver §5.1)

---

## 1. Contexto y Propósito (Por Qué)

Retake es un centro de estadísticas y predicciones de la Call of Duty League. Todas sus secciones (cinta de marcadores, spotlight, cuadrícula de partidos, páginas de equipos, jugadores y torneos, y más adelante los modelos de Machine Learning) consumen la misma información de la liga.

Esta spec define **qué información de la liga existe en Retake, con qué nivel de detalle y cómo se comporta cuando falta o cambia**, para que todas las secciones hablen del mismo equipo, el mismo jugador y el mismo partido. Además fija un grupo pequeño de **reglas comunes de presentación** (§2.9) que todas las specs visuales deben respetar, para que un mismo caso (un dato ausente, una descalificación, un rol desconocido) se vea igual en toda la plataforma.

No define cómo se obtiene ni cómo se actualiza esa información (spec 003), ni dónde ni con qué diseño aparece cada dato en pantalla (specs 004 en adelante).

Alcance temporal: detalle completo de la **temporada actual** y, de temporadas anteriores, únicamente el **historial de campeonatos mundiales**.

### 1.1 Glosario

| Término | Significado en esta spec |
|---|---|
| **Temporada** | Periodo de competición que la liga nombra con un año oficial (ej. `CDL 2026`). |
| **Partido** | Enfrentamiento completo entre dos equipos, al mejor de N mapas. |
| **Mapa** | Cada juego dentro de un partido, con un modo y un nombre de mapa. |
| **Mapa jugado** | Mapa que terminó con un ganador. El mapa en curso no es un mapa jugado hasta que termina. |
| **Mapa no jugado** | Mapa previsto en un partido `finalizado` que no llegó a jugarse porque el partido ya estaba decidido. |
| **Suplente** | Jugador que disputa un partido con un equipo a cuyo roster no pertenece. |
| **Agente libre** | Jugador de la temporada actual que no pertenece a ningún equipo. |
| **Franquicia** | Equipo de la liga, que sigue siendo el mismo aunque cambie de nombre. |
| **Identidad** | Conjunto de nombre corto, abreviatura, logo, color primario y color secundario que una franquicia usa desde una fecha. |
| **Campeonato mundial** | El campeonato que cierra cada año competitivo (ver RF-54). |
| **Fuente** | Cualquiera de las fuentes de datos de RF-66, con la prioridad de RF-67 (o de RF-75 en la tabla de posiciones). |

### 1.2 Convención de verbos

* **Registrará, mantendrá, asociará, reconocerá, distinguirá**: el dato existe en Retake y puede consultarse. Se verifica comprobando el dato, no la pantalla.
* **Mostrará, indicará**: regla de presentación. Solo aparece en §2.9 y obliga a todas las specs visuales.

---

## 2. Requisitos Funcionales (Notación EARS)

> Los números de requisito son estables. Los añadidos en la revisión del 2026-09-22 van a partir de RF-52 y se colocan en la sección que les corresponde. Los retirados conservan su número para no romper las referencias de otras specs (por ejemplo, la 001 cita RF-2 y RF-3). El número RF-93 no se usa. RF-134 y RF-135 se añadieron en la revisión R-1.

### 2.1 Temporada actual

* **RF-1 (Ubicuo)**: EL SISTEMA mantendrá eventos, partidos, mapas, estadísticas, posiciones y rosters de equipos únicamente de la temporada actual, sin contar los rosters del historial de campeonatos (RF-6).
  * *Nota (2026-09-23, cambio C-4 de la spec 003):* excepción: se mantiene también el calendario de la próxima temporada, sin mostrarlo, hasta que pase a ser la actual (RF-14 y RF-15 de la 003). Sin él no se podría detectar el cambio de temporada (RF-3).
* **RF-80 (Ubicuo)**: EL SISTEMA mantendrá las franquicias, sus identidades y los jugadores que aparezcan en la temporada actual o en el historial de campeonatos.
* **RF-52 (Ubicuo)**: EL SISTEMA identificará cada temporada por el año con el que la liga la nombra oficialmente (ej. `CDL 2026`), aunque su primer partido se juegue el año anterior.
* **RF-53 (Ubicuo)**: EL SISTEMA considerará partido oficial de una temporada cualquier partido de un evento de esa temporada, incluidos los Qualifiers.
* **RF-2 (Estado)**: MIENTRAS ningún partido oficial de una nueva temporada haya pasado a `en vivo`, EL SISTEMA considerará como temporada actual la temporada anterior.
* **RF-3 (Dirigido por evento)**: CUANDO el primer partido oficial de una nueva temporada pase a `en vivo`, EL SISTEMA pasará a considerarla la temporada actual.
* **RF-123 (Ubicuo)**: EL SISTEMA no volverá a considerar actual una temporada anterior una vez que la nueva haya pasado a ser la actual, aunque se cancele el partido que provocó el cambio.
  * *Nota (2026-09-22, decisión C-8, aplica a RF-3):* el cambio automático es el comportamiento definitivo. Hasta que exista la spec 003, RF-3 se cumple con un valor mantenido a mano (decisión P-6 de la spec 001), que hay que cambiar el mismo día en que empiece la nueva temporada. La spec 003 debe hacer el cambio automático.
  * *Nota (2026-09-23, cambio C-5 de la spec 003):* cumplido por la spec 003 (RF-72 de la 003). El cambio de temporada es automático y se retira el valor manual. El cambio en el código lo hará la implementación de la 003.

### 2.2 Historial de campeonatos mundiales

* **RF-4 (Ubicuo)**: EL SISTEMA mantendrá, para cada año desde 2013, la clasificación final del campeonato mundial de ese año.
* **RF-54 (Ubicuo)**: EL SISTEMA considerará campeonato mundial el Call of Duty Championship de 2013 a 2016, el CWL Championship de 2017 a 2019 y el CDL Championship (Champs) desde 2020.
* **RF-55 (Estado)**: MIENTRAS no haya terminado la final del campeonato mundial de la temporada actual, EL SISTEMA no incluirá esa temporada en el historial de campeonatos.
* **RF-5 (Ubicuo)**: EL SISTEMA registrará para cada equipo de la clasificación final su lugar, el premio obtenido, el porcentaje de la bolsa que representa, el juego y la fecha de la final.
* **RF-56 (Ubicuo)**: EL SISTEMA registrará cada premio en dólares estadounidenses con el importe nominal publicado, sin ajustarlo por inflación.
* **RF-57 (Ubicuo)**: EL SISTEMA registrará el porcentaje de la bolsa tal como lo publica la fuente, sin calcularlo.
* **RF-58 (Ubicuo)**: EL SISTEMA registrará para el juego de cada campeonato su nombre oficial (ej. `Call of Duty: Black Ops 6`) y su abreviatura (ej. `BO6`).
* **RF-6 (Ubicuo)**: EL SISTEMA asociará a cada equipo de la clasificación final la lista de jugadores de su roster en ese campeonato.
* **RF-59 (Ubicuo)**: EL SISTEMA registrará para cada jugador de un roster histórico el gamertag que usaba en la fecha de esa final.
* **RF-7 (Ubicuo)**: EL SISTEMA registrará en cada campeonato un único premio por equipo, que pertenece al equipo y no a cada jugador de su roster.
* **RF-119 (No deseado)**: SI a un campeonato del historial le faltan datos de RF-5 o RF-6, ENTONCES EL SISTEMA lo registrará con los datos disponibles.
* **RF-121 (No deseado)**: SI falta la fecha de la final de un campeonato, ENTONCES EL SISTEMA asociará a cada equipo la identidad cuyo nombre corto coincide con el nombre que la fuente publica para ese equipo en ese campeonato.
* **RF-124 (No deseado)**: SI falta la fecha de la final y el nombre publicado no coincide con ninguna identidad de la franquicia, ENTONCES EL SISTEMA le asociará la identidad vigente al terminar el año de ese campeonato.
* **RF-8** y **RF-9**: trasladados a §2.9 (reglas comunes de presentación).

### 2.3 Franquicias e identidad visual

* **RF-10 (Ubicuo)**: EL SISTEMA reconocerá como una misma franquicia a un equipo que haya cambiado de nombre.
* **RF-11 (Ubicuo)**: EL SISTEMA mantendrá para cada identidad de una franquicia un nombre corto (ej. `FaZe VGS`), una abreviatura (ej. `VGS`), un logo, un color primario y un color secundario.
* **RF-73 (Dirigido por evento)**: CUANDO una franquicia cambie su nombre corto, su abreviatura, su logo, su color primario o su color secundario, EL SISTEMA registrará una nueva identidad de esa franquicia.
  * *Nota (2026-09-23, cambio C-7 de la spec 003):* el cambio se mide sobre el resultado de combinar las fuentes campo a campo (RF-62 y RF-63 de la 003), no sobre lo que publica cada fuente por separado.
* **RF-74 (Ubicuo)**: EL SISTEMA registrará para cada identidad la fecha y hora desde la que está vigente.
* **RF-12 (Ubicuo)**: EL SISTEMA asociará a cada partido la identidad que cada franquicia tenía vigente en la fecha y hora de inicio programadas del partido, cualquiera que sea su estado.
* **RF-13 (Ubicuo)**: EL SISTEMA asociará a cada registro del historial de campeonatos la identidad que la franquicia tenía vigente en la fecha de esa final.
* **RF-114 (Ubicuo)**: EL SISTEMA considerará la misma franquicia a la que ocupe la misma plaza en la liga, aunque cambie de dueño, de ciudad o de nombre.
* **RF-115 (No deseado)**: SI la fuente publica como franquicia nueva a la que ocupa una plaza ya existente, ENTONCES EL SISTEMA la tratará como franquicia nueva.
* **RF-116 (No deseado)**: SI una franquicia deja la liga y no figura en el historial de campeonatos, ENTONCES EL SISTEMA dejará de mantenerla.
* **RF-117 (Ubicuo)**: EL SISTEMA tratará a los equipos del historial que nunca fueron franquicia de la CDL como franquicias con sus propias identidades.
* **RF-14** y **RF-15**: trasladados a §2.9 (reglas comunes de presentación).

### 2.4 Jugadores

* **RF-16 (Ubicuo)**: EL SISTEMA mantendrá el gamertag actual de cada jugador.
* **RF-111 (Ubicuo)**: EL SISTEMA considerará gamertag actual de un jugador retirado el último que usó en competición.
* **RF-17 (Ubicuo)**: EL SISTEMA registrará los gamertags anteriores de cada jugador.
* **RF-18 (Ubicuo)**: EL SISTEMA reconocerá como la misma persona a un jugador de la temporada actual y a un jugador del historial de campeonatos que usó cualquiera de sus gamertags.
* **RF-19 (Ubicuo)**: EL SISTEMA distinguirá como personas diferentes a dos jugadores que hayan usado el mismo gamertag.
* **RF-131 (Ubicuo)**: EL SISTEMA considerará la misma persona a dos registros de jugador solo si una fuente los relaciona, según la prioridad de RF-67, o si Retake los une a mano.
  * *Nota (2026-09-23, cambio C-9 de la spec 003):* la misma regla vale para partidos, eventos y franquicias (RF-54 de la 003). Un registro sin enlazar se retiene sin mostrarlo si una fuente de mayor prioridad publica registros de ese tipo (RF-55 y RF-56 de la 003).
* **RF-132 (Ubicuo)**: EL SISTEMA no considerará la misma persona a dos registros de jugador solo porque coincida su gamertag.
* **RF-133 (Dirigido por evento)**: CUANDO Retake separe a mano dos registros de jugador que una fuente relaciona, EL SISTEMA los tratará como personas distintas.
* **RF-113 (No deseado)**: SI ninguna fuente relaciona dos registros de jugador y Retake no los ha unido, ENTONCES EL SISTEMA los tratará como personas distintas.
* **RF-20 (Ubicuo)**: EL SISTEMA asociará a cada jugador de la temporada actual los campeonatos del historial en los que formó parte de un roster.
* **RF-21 (Ubicuo)**: EL SISTEMA mantendrá de cada jugador su nombre real.
* **RF-22 (Ubicuo)**: EL SISTEMA mantendrá de cada jugador su país.
* **RF-110 (Ubicuo)**: EL SISTEMA mantendrá un único país por jugador, tomado según la prioridad de RF-67.
* **RF-109 (No deseado)**: SI la fuente publica la edad de un jugador sin fecha ni año de nacimiento, ENTONCES EL SISTEMA registrará como año de nacimiento aproximado el que resulta de restar esa edad al año en que se obtuvo el dato.
* **RF-60 (Ubicuo)**: EL SISTEMA mantendrá el nombre real, el país y la edad tanto de los jugadores de la temporada actual como de los que solo figuran en el historial de campeonatos.
* **RF-77 (Ubicuo)**: EL SISTEMA solo mantendrá los datos personales de un jugador (nombre real, país y fecha o año de nacimiento) que estén publicados en alguna de las fuentes de RF-66.
* **RF-78 (Dirigido por evento)**: CUANDO un jugador o su representante pida retirar sus datos personales, EL SISTEMA dejará de mantenerlos y los tratará como no registrados (RF-25).
  * *Nota (2026-09-23, cambio C-10 de la spec 003):* una vez retirados, no se vuelven a registrar aunque las fuentes los sigan publicando, mientras Retake no revierta la retirada a mano (RF-60 de la 003).
* **RF-26 (Ubicuo)**: EL SISTEMA mantendrá para cada jugador de la temporada actual como máximo un rol, `SMG` o `AR`, asignado a mano por Retake.
* **RF-76 (Dirigido por evento)**: CUANDO Retake cambie el rol de un jugador, EL SISTEMA sustituirá el rol anterior por el nuevo para toda la temporada actual, sin guardar historial de roles.
* **RF-27 (No deseado)**: SI Retake no ha asignado el rol de un jugador, ENTONCES EL SISTEMA registrará a ese jugador como `Sin rol`.
* **RF-28**: *Retirado el 2026-09-22 (decisión A-13).* La exclusión de los jugadores `Sin rol` pasa a las specs que definan clasificaciones o rankings por rol.
* **RF-105 (Ubicuo)**: EL SISTEMA mantendrá como jugador de la temporada actual, hasta que termine, a todo jugador que haya jugado al menos un partido de esa temporada.
* **RF-106 (No deseado)**: SI un jugador de la temporada actual deja de pertenecer a un equipo, ENTONCES EL SISTEMA lo registrará como agente libre conservando su rol.
* **RF-102 (Ubicuo)**: EL SISTEMA registrará como jugador de la temporada actual a quien juegue un partido de esa temporada como suplente.
* **RF-103 (Ubicuo)**: EL SISTEMA marcará cada partido que un jugador haya jugado como suplente.
* **RF-104 (Ubicuo)**: EL SISTEMA no incluirá a un suplente en el roster del equipo con el que jugó como suplente.
* **RF-29 (Ubicuo)**: EL SISTEMA atribuirá las estadísticas de un jugador en un partido al equipo en el que jugaba en la fecha de ese partido.
* **RF-23**, **RF-24** y **RF-25**: trasladados a §2.9 (reglas comunes de presentación).

### 2.5 Eventos y partidos

* **RF-30 (Ubicuo)**: EL SISTEMA asignará cada partido de la temporada actual a un evento (ej. Major 2 Qualifiers, Major 2, Champs).
* **RF-61 (Ubicuo)**: EL SISTEMA registrará el nombre de cada evento tal como lo publica la fuente, sin limitarlo a una lista fija.
* **RF-31 (Ubicuo)**: EL SISTEMA asignará a cada partido como máximo una de estas fases: semana, grupo, winners bracket, losers bracket o gran final.
  * *Nota (2026-09-23, cambio C-13 de la spec 003):* si la fuente no publica la semana de un partido de clasificatorio, EL SISTEMA la calculará como el orden de la semana (de lunes a domingo, hora de Ciudad de México) entre las semanas con partidos de ese evento. Es una excepción a RF-45.
* **RF-134 (No deseado)**: SI la fuente publica para un partido una fase distinta de las cinco de RF-31, ENTONCES EL SISTEMA registrará el partido sin fase.
* **RF-32 (Ubicuo)**: EL SISTEMA registrará para cada partido los dos equipos que lo disputan, en cuanto se conozcan.
* **RF-84 (Opcional)**: DONDE un equipo de un partido aún no se conozca, EL SISTEMA registrará su origen como ganador o perdedor de otro partido registrado.
* **RF-33 (Ubicuo)**: EL SISTEMA registrará para cada partido la fecha y hora exactas de inicio programadas.
* **RF-87 (Dirigido por evento)**: CUANDO cambie la fecha y hora de inicio programadas de un partido, EL SISTEMA registrará la nueva conservando todas las anteriores en orden.
* **RF-88 (Ubicuo)**: EL SISTEMA usará la fecha y hora de inicio programadas más reciente de cada partido en todo requisito que dependa de ella (ej. RF-12).
* **RF-34 (Ubicuo)**: EL SISTEMA registrará para cada partido su formato expresado como "al mejor de N mapas".
* **RF-35 (Ubicuo)**: EL SISTEMA asignará a cada partido exactamente uno de estos estados: `programado`, `en vivo` o `finalizado`.
* **RF-62 (Ubicuo)**: EL SISTEMA nunca devolverá un partido a un estado anterior en el orden `programado`, `en vivo`, `finalizado`.
* **RF-63 (No deseado)**: SI la fuente publica para un partido un estado anterior al que ya tiene registrado, ENTONCES EL SISTEMA conservará el estado más avanzado.
* **RF-81 (No deseado)**: SI la fuente publica que un partido `programado` se pospone, ENTONCES EL SISTEMA lo mantendrá como `programado` con su nueva fecha y hora (RF-87).
* **RF-82 (No deseado)**: SI un partido se decide por forfeit, ENTONCES EL SISTEMA lo registrará como `finalizado` con el ganador y el marcador que publique la fuente.
* **RF-83 (No deseado)**: SI la fuente publica que un partido se cancela, ENTONCES EL SISTEMA dejará de mantenerlo.
* **RF-36 (Estado)**: MIENTRAS un partido esté `en vivo`, EL SISTEMA mantendrá el número de mapas ganados por cada equipo.
* **RF-89 (No deseado)**: SI un partido pasa a `en vivo` y la fuente aún no publica su marcador, ENTONCES EL SISTEMA registrará 0 mapas ganados para cada equipo.
* **RF-91 (Estado)**: MIENTRAS la fuente no publique un marcador nuevo de un partido `en vivo`, EL SISTEMA conservará el último marcador conocido.
* **RF-37 (Estado)**: MIENTRAS un partido esté `en vivo`, EL SISTEMA mantendrá el marcador del mapa en curso en la unidad propia de su modo: puntos en Hardpoint, rondas en Search & Destroy y overloads anotados en Overload.
* **RF-38 (Dirigido por evento)**: CUANDO un partido pase a `finalizado`, EL SISTEMA registrará el marcador final del partido en mapas ganados por cada equipo.
* **RF-39 (Dirigido por evento)**: CUANDO un partido pase a `finalizado`, EL SISTEMA registrará el equipo ganador.
* **RF-40 (Ubicuo)**: EL SISTEMA registrará para cada mapa jugado su posición en el partido, su modo, el nombre del mapa, el marcador final y el equipo ganador.
* **RF-64 (No deseado)**: SI un mapa se repite, ENTONCES EL SISTEMA registrará como mapa jugado solo la versión que terminó con ganador.
* **RF-92 (Dirigido por evento)**: CUANDO un partido pase a `finalizado`, EL SISTEMA registrará como mapas no jugados los mapas previstos que publique la fuente y que no llegaron a jugarse, con su posición, su modo y su nombre.
* **RF-95 (No deseado)**: SI un mapa jugado es de un modo distinto de Hardpoint, Search & Destroy u Overload, ENTONCES EL SISTEMA lo registrará con el modo y el marcador tal como los publica la fuente, y solo con las estadísticas de RF-41.

### 2.6 Estadísticas de jugadores por mapa

* **RF-41 (Ubicuo)**: EL SISTEMA registrará para cada jugador en cada mapa jugado: kills, deaths, K/D, daño y asistencias.
* **RF-42 (Opcional)**: DONDE el modo del mapa sea Hardpoint, EL SISTEMA registrará además el hill time y el contested hill time de cada jugador.
* **RF-43 (Opcional)**: DONDE el modo del mapa sea Search & Destroy, EL SISTEMA registrará además los first bloods, first deaths, plants y defuses de cada jugador.
* **RF-44 (Opcional)**: DONDE el modo del mapa sea Overload, EL SISTEMA registrará además las zone captures y los overloads de cada jugador.
* **RF-79 (Ubicuo)**: EL SISTEMA registrará el K/D de cada jugador tal como lo publica la fuente, sin calcularlo a partir de kills y deaths.
  * *Nota (2026-09-23, cambio C-12 de la spec 003):* si ninguna fuente publica el K/D, EL SISTEMA lo calculará como kills ÷ deaths con 2 decimales; con 0 deaths, K/D = kills; si falta kills o deaths, el K/D queda ausente. Un K/D publicado manda sobre el calculado. Es una excepción a RF-45.
* **RF-45 (Ubicuo)**: EL SISTEMA registrará únicamente las estadísticas que publica la fuente, sin métricas derivadas.
  * *Nota (2026-09-23, cambios C-12 y C-13 de la spec 003):* excepciones: el K/D calculado (RF-79) y la semana calculada de los clasificatorios (RF-31).
* **RF-65 (Ubicuo)**: EL SISTEMA distinguirá una estadística ausente en la fuente de una estadística con valor 0.
* **RF-46**, **RF-47** y **RF-48**: trasladados a §2.9 (reglas comunes de presentación).

### 2.7 Tabla de posiciones

* **RF-49 (Ubicuo)**: EL SISTEMA mantendrá la tabla de posiciones oficial de la temporada actual con la posición y los puntos CDL de cada equipo.
* **RF-50 (Ubicuo)**: EL SISTEMA registrará los puntos CDL exactamente como los publica la liga, sin recalcularlos a partir de resultados.
* **RF-75 (Ubicuo)**: EL SISTEMA tomará la posición y los puntos CDL de cada equipo primero de la web oficial de la CDL, en su defecto de BreakingPoint.gg y en último lugar de Call of Duty Esports Wiki.
* **RF-122 (Ubicuo)**: EL SISTEMA registrará la posición de cada equipo tal como la publica la fuente de la tabla, incluidas las posiciones compartidas, sin desempatar.
* **RF-51**: trasladado a §2.9 (reglas comunes de presentación).

### 2.8 Fuentes de datos

* **RF-66 (Ubicuo)**: EL SISTEMA tomará los datos de la liga de tres fuentes: BreakingPoint.gg, Call of Duty Esports Wiki (Fandom) y la web oficial de la CDL.
* **RF-67 (No deseado)**: SI dos fuentes publican valores distintos para el mismo dato, ENTONCES EL SISTEMA usará el de BreakingPoint.gg, en su defecto el de Call of Duty Esports Wiki y en último lugar el de la web oficial de la CDL, salvo en la tabla de posiciones (RF-75).
  * *Nota (2026-09-23, cambio C-6 de la spec 003):* segunda excepción: mientras un partido está `en vivo`, vale el marcador más avanzado que publique cualquier fuente, y nunca retrocede (RF-57 a RF-59 de la 003). El marcador final de un partido `finalizado` vuelve a seguir esta prioridad.

**Seguridad de los datos recibidos**

* **RF-129 (Ubicuo)**: EL SISTEMA tratará todo texto recibido de una fuente como texto plano, sin interpretarlo nunca como código, formato ni enlace.
* **RF-130 (Ubicuo)**: EL SISTEMA solo aceptará los logos recibidos de una fuente como imágenes.

**Correcciones y valores no válidos**

* **RF-96 (Dirigido por evento)**: CUANDO la fuente cambie un dato ya registrado de un partido `finalizado` o del historial de campeonatos, EL SISTEMA registrará el valor nuevo.
  * *Nota (2026-09-23, cambio C-8 de la spec 003):* las correcciones solo llegan dentro de los plazos de revisión de la 003:
    - partidos `finalizado`: hasta 7 días después de tener todas sus estadísticas (RF-19 a RF-21 de la 003);
    - historial: con las relecturas de cada Champs (RF-30 a RF-33 de la 003);
    - en ambos casos, también cuando lo pida el administrador (RF-100 y RF-102 de la 003).

    Una corrección publicada fuera de esos plazos no llega sola.
* **RF-97 (Dirigido por evento)**: CUANDO ocurra un cambio de RF-96, EL SISTEMA marcará como corregido el dato concreto que cambió, sin guardar el valor anterior.
* **RF-98 (Ubicuo)**: EL SISTEMA no considerará corrección el primer registro de un dato que nunca había llegado de la fuente (ej. estadísticas pendientes, RF-48).
* **RF-101 (Ubicuo)**: EL SISTEMA considerará imposible cualquier estadística, marcador, K/D o premio negativo, un porcentaje de la bolsa menor que 0 o mayor que 100, y un número de mapas ganados por un equipo mayor que el necesario para ganar un partido al mejor de N.
* **RF-100 (No deseado)**: SI la fuente publica un valor imposible, ENTONCES EL SISTEMA no lo registrará y tratará ese dato como ausente, sin descartar el resto de datos del partido o del registro.

### 2.9 Reglas comunes de presentación

Estas reglas obligan a todas las specs visuales (004 en adelante). Cada spec visual decide dónde y con qué diseño se aplican, pero no puede contradecirlas.

**Idioma de las etiquetas**

* **RF-125 (Ubicuo)**: EL SISTEMA mostrará las siglas `DQ`, `SMG` y `AR` sin traducir en todos los idiomas.
* **RF-126 (Ubicuo)**: EL SISTEMA traducirá al idioma activo el resto de etiquetas y avisos de esta sección.

**Historial de campeonatos**

* **RF-8 (Opcional)**: DONDE el lugar de un equipo sea un rango compartido (ej. `9-12`), EL SISTEMA mostrará el rango tal como fue publicado.
* **RF-9 (Opcional)**: DONDE un equipo haya sido descalificado, EL SISTEMA mostrará `DQ` en lugar de un lugar numérico.
* **RF-69 (Opcional)**: DONDE un jugador aparezca en un roster del historial de campeonatos, EL SISTEMA lo mostrará con el gamertag que usaba en esa final junto a su gamertag actual.
* **RF-112 (Opcional)**: DONDE el gamertag de un jugador en una final coincida con su gamertag actual, EL SISTEMA lo mostrará una sola vez.
* **RF-120 (No deseado)**: SI falta un dato de un campeonato del historial, ENTONCES EL SISTEMA mostrará `No disponible` en su lugar.

**Identidad visual**

* **RF-14 (No deseado)**: SI una identidad de una franquicia no tiene logo registrado, ENTONCES EL SISTEMA mostrará el logo de la identidad más reciente de esa franquicia.
* **RF-15 (No deseado)**: SI ni la identidad ni la identidad más reciente de la franquicia tienen logo registrado, ENTONCES EL SISTEMA mostrará la abreviatura de la identidad sobre su color primario, aunque alguna identidad anterior sí tenga logo.
* **RF-118 (No deseado)**: SI en el caso de RF-15 la identidad tampoco tiene color primario registrado, ENTONCES EL SISTEMA mostrará la abreviatura sobre el color neutro común de Retake.
* **RF-127 (Ubicuo)**: EL SISTEMA pintará la abreviatura de RF-15 y RF-118 en blanco o en negro, el que dé mayor contraste con su fondo.
* **RF-128 (Ubicuo)**: EL SISTEMA mantendrá un contraste mínimo de 4,5:1 entre la abreviatura de RF-15 y RF-118 y su fondo.

**Jugadores**

* **RF-68 (Opcional)**: DONDE un jugador aparezca fuera del historial de campeonatos, EL SISTEMA lo mostrará con su gamertag actual.
* **RF-23 (Opcional)**: DONDE conste la fecha de nacimiento completa de un jugador, EL SISTEMA mostrará su edad en años cumplidos según la fecha UTC.
  * *Nota (2026-09-22, revisión R-2):* sustituye a "según la fecha local del dispositivo del usuario" (decisión A-11). Calcular la edad con la fecha local obliga a entregar al navegador datos de los que se deduce la fecha de nacimiento completa, lo que vaciaría RF-24. El día del cumpleaños, un usuario alejado de UTC puede ver la edad con unas horas de desfase.
* **RF-108 (No deseado)**: SI de un jugador solo se conoce el año de nacimiento, exacto o aproximado, ENTONCES EL SISTEMA mostrará su edad como el rango de las dos edades posibles (ej. `24–25`).
* **RF-24 (Ubicuo)**: EL SISTEMA no mostrará la fecha de nacimiento exacta de ningún jugador.
* **RF-25 (No deseado)**: SI un dato personal de un jugador (nombre real, país o edad) no está registrado, ENTONCES EL SISTEMA mostrará `No disponible` en lugar de dejar el espacio en blanco.
* **RF-71 (Opcional)**: DONDE un jugador esté registrado como `Sin rol`, EL SISTEMA mostrará `Sin rol` en el lugar de su rol.
* **RF-107 (Opcional)**: DONDE un jugador esté registrado como agente libre, EL SISTEMA mostrará `Agente libre` en el lugar de su equipo.

**Partidos y estadísticas**

* **RF-70 (Ubicuo)**: EL SISTEMA mostrará las fechas y horas de los partidos convertidas a la zona horaria del dispositivo del usuario.
* **RF-85 (Opcional)**: DONDE un equipo de un partido aún no se conozca, EL SISTEMA mostrará "Ganador de" o "Perdedor de" seguido del partido de origen.
* **RF-86 (No deseado)**: SI un equipo de un partido aún no se conoce y la fuente no publica su origen, ENTONCES EL SISTEMA mostrará `Por definir`.
* **RF-90 (No deseado)**: SI la fuente aún no publica el marcador del mapa en curso de un partido `en vivo`, ENTONCES EL SISTEMA mostrará ese marcador como `No disponible`.
* **RF-94 (Opcional)**: DONDE un partido tenga mapas no jugados, EL SISTEMA los mostrará con su modo, su nombre y la etiqueta `No jugado`, sin marcador.
* **RF-99 (Opcional)**: DONDE un dato esté marcado como corregido, EL SISTEMA mostrará junto a él la etiqueta `Corregido`.
* **RF-46 (No deseado)**: SI una estadística concreta de un jugador no viene en la fuente, ENTONCES EL SISTEMA la mostrará como `No disponible` en lugar de 0.
* **RF-47 (No deseado)**: SI a algún mapa jugado de un partido `finalizado` le faltan todas las estadísticas de al menos un jugador, ENTONCES EL SISTEMA mostrará el aviso "Estadísticas pendientes" junto al marcador final del partido.
* **RF-72 (No deseado)**: SI a un jugador le falta una estadística concreta de un mapa pero tiene otras registradas en ese mapa, ENTONCES EL SISTEMA no mostrará el aviso "Estadísticas pendientes" por esa ausencia.
* **RF-48 (Dirigido por evento)**: CUANDO todos los jugadores de todos los mapas jugados de un partido que mostraba "Estadísticas pendientes" tengan estadísticas registradas, EL SISTEMA retirará el aviso.
* **RF-135 (No deseado)**: SI un partido no tiene fase registrada, ENTONCES EL SISTEMA mostrará `No disponible` en el lugar de la fase.

**Tabla de posiciones**

* **RF-51 (No deseado)**: SI la fuente no tiene tabla de posiciones de la temporada actual, o la tiene sin puntos para ningún equipo, ENTONCES EL SISTEMA indicará que la tabla de posiciones todavía no está disponible.

---

## 3. Casos Límite y Manejo de Errores

1. **Datos vacíos o no disponibles**:
   - Partido finalizado al que le faltan todas las estadísticas de algún jugador en algún mapa → marcador final con aviso "Estadísticas pendientes"; el aviso se retira cuando están todas (RF-47, RF-48).
   - Estadística concreta ausente con el resto presente → `No disponible`, nunca 0, y sin aviso de pendientes; un 0 significa "no lo hizo", un vacío significa "no se sabe" (RF-46, RF-65, RF-72).
   - Dato personal de un jugador sin registrar, también de jugadores solo históricos → `No disponible`, la misma etiqueta que una estadística ausente (RF-25, RF-60).
   - Rol no asignado por Retake → `Sin rol` (RF-27, RF-71).
   - Tabla de posiciones no publicada o sin puntos → aviso explícito (RF-51).
   - Identidad sin logo → logo de la identidad más reciente; si tampoco lo tiene, abreviatura sobre color primario (RF-14, RF-15).
2. **Cambio de temporada**:
   - Entre temporadas se sigue mostrando la anterior hasta que el primer partido oficial de la nueva (Qualifiers incluidos) pase a `en vivo`; si se retrasa, sigue la anterior (RF-2, RF-3, RF-53).
   - La temporada se identifica por su año oficial, aunque empiece a finales del año anterior (RF-52).
   - Al cambiar, el detalle de la temporada que termina deja de mantenerse y solo permanece su clasificación final en el historial, que entra cuando termina su final (RF-1, RF-4, RF-55).
3. **Cambios de identidad**:
   - Una franquicia que cambia de nombre sigue siendo la misma (RF-10); cualquier cambio de nombre, abreviatura, logo o colores crea una identidad nueva con su fecha de inicio (RF-73, RF-74).
   - Cada partido lleva la identidad vigente en su fecha y hora de inicio, también si está `programado` o `en vivo` (RF-12); cada final, la de su fecha (RF-13).
   - Un jugador que cambia de gamertag sigue siendo la misma persona (RF-17, RF-18); dos personas con el mismo gamertag se mantienen separadas (RF-19).
   - En el historial, cada jugador aparece con el gamertag de esa final y con el actual (RF-59, RF-69).
   - Un jugador traspasado a mitad de temporada conserva sus estadísticas en el equipo con el que las hizo (RF-29).
4. **Estados y mapas**:
   - Un partido nunca vuelve a un estado anterior; si la fuente lo intenta, se conserva el más avanzado (RF-62, RF-63).
   - Un mapa en curso no es un mapa jugado hasta que termina con ganador; si un mapa se repite, solo cuenta la versión con ganador (RF-40, RF-64).
5. **Datos del historial con formato especial**:
   - Lugares compartidos (`9-12`) y descalificaciones (`DQ`) se muestran tal como fueron publicados (RF-8, RF-9).
   - El premio es del equipo, no de cada jugador; nunca se suma por jugador (RF-7). Detectado en el spike: sumar por jugador daba $3,200,000 a FaZe VGS 2026 en vez de $800,000.
   - Premios en USD nominales y porcentaje de la bolsa tal como se publicó (RF-56, RF-57).
6. **Datos contradictorios entre fuentes**: manda BreakingPoint.gg, después la Wiki y por último la web oficial (RF-67); en la tabla de posiciones manda la web oficial (RF-50, RF-75).
7. **Datos personales**: solo se guardan los publicados en las fuentes; si un jugador o su representante pide retirarlos, pasan a `No disponible` (RF-25, RF-77, RF-78).
8. **Cambio de rol**: Retake puede corregir el rol en cualquier momento; el nuevo sustituye al anterior para toda la temporada (RF-26, RF-76).
9. **Partidos fuera de lo normal**:
   - Pospuesto → sigue `programado` con la nueva fecha; se conservan todas sus fechas y manda la más reciente (RF-81, RF-87, RF-88).
   - Forfeit → `finalizado` con el ganador y el marcador de la fuente; sin mapas jugados no activa "Estadísticas pendientes" (RF-82, RF-47).
   - Cancelado → deja de mantenerse (RF-83).
   - Rival por decidir → se registra su origen ("Ganador de…" / "Perdedor de…"), o `Por definir` si la fuente no lo publica (RF-84 a RF-86).
   - En vivo sin marcador → 0-0 en mapas y marcador del mapa en curso `No disponible`; si el marcador se detiene, se conserva el último conocido sin aviso (RF-89 a RF-91).
   - Mapas previstos que no llegaron a jugarse → `No jugado`, sin marcador (RF-92, RF-94).
   - Modo no contemplado → se registra con las estadísticas comunes (RF-95).
   - Fase no contemplada → el partido se registra sin fase y la fase se muestra como `No disponible` (RF-134, RF-135).
   - Mapa repetido o reiniciado → solo cuenta la versión con ganador (RF-64); en una prórroga, el marcador final es el que publique la fuente.
   - K/D con 0 deaths → el que publique la fuente o `No disponible` (RF-79, RF-46).
10. **Jugadores fuera de lo normal**:
   - Suplente → jugador de la temporada, con sus estadísticas en el equipo con el que jugó y el partido marcado como de suplente, sin entrar en su roster (RF-29, RF-102 a RF-104).
   - Liberado a mitad de temporada → sigue como jugador de la temporada, como `Agente libre` y con su rol (RF-105 a RF-107).
   - Solo año de nacimiento, o solo edad → edad aproximada como rango (RF-108, RF-109); un único país (RF-110).
   - Retirado → su gamertag actual es el último que usó; si la fuente no permite relacionar dos registros, son personas distintas (RF-111 a RF-113).
11. **Franquicias fuera de lo normal**:
   - Venta o mudanza → misma franquicia si ocupa la misma plaza, salvo que la fuente la publique como nueva (RF-114, RF-115).
   - Salida de la liga → solo se conserva si figura en el historial (RF-80, RF-116).
   - Equipos anteriores a 2020 que nunca fueron franquicia → se tratan como franquicias con identidades propias (RF-117).
   - Cambio de identidad el mismo día de un partido → manda la hora exacta de inicio (RF-12, RF-74).
12. **Historial y tabla**:
   - Campeonato incompleto → se registra con lo que haya; lo que falte es `No disponible`; sin fecha de final, la identidad cuyo nombre coincide con el publicado en ese campeonato y, si ninguno coincide, la vigente al terminar ese año (RF-119 a RF-121, RF-124).
   - Empates en la tabla → posición tal como la publica la fuente, compartida si así se publica (RF-122).
   - Temporada nueva cuyo primer partido se cancela → el cambio es definitivo (RF-123).
13. **Entradas no válidas**:
   - Un valor imposible (negativo, porcentaje fuera de 0–100, más mapas ganados de los posibles) no se registra y el dato pasa a ausente, sin descartar el resto (RF-100, RF-101).
   - Si después llega un valor válido, se registra; si el partido ya estaba `finalizado`, se marca como `Corregido` (RF-96, RF-97, RF-99).
   - Una corrección de la fuente en un partido `finalizado` o en el historial se aplica y el dato queda marcado como `Corregido` (RF-96 a RF-99).
14. **Seguridad**: un texto malicioso publicado en una fuente (por ejemplo, en la Wiki) se muestra como texto y nunca se ejecuta; los logos solo se aceptan como imagen (RF-129, RF-130).
15. **Identidad de jugadores**: dos registros son la misma persona solo si una fuente los relaciona o Retake los une a mano; un gamertag igual no basta, y Retake puede separar registros que una fuente relacione por error (RF-131 a RF-133, RF-113).
16. **Abreviatura sin logo**: se pinta en blanco o negro, el que más contraste dé, con un mínimo de 4,5:1; sin color primario, sobre el color neutro de Retake (RF-118, RF-127, RF-128).
17. **Peticiones lentas o interrumpidas**: fuera del alcance de esta spec. Si la fuente no responde, es un error de carga del bloque que la muestra, y se trata según la spec 001.

---

## 4. Fuera de Alcance

* Estadísticas, rosters, partidos y posiciones detalladas de temporadas anteriores (solo se conserva el historial de campeonatos mundiales).
* Campeonatos anteriores a 2020 distintos del campeonato mundial de cada año.
* Métricas derivadas o calculadas (KD ajustado, +/- acumulado, daño por minuto, etc.); se definirán en specs posteriores.
* Premios ajustados por inflación o convertidos a otras monedas.
* Estados de partido `pospuesto`, `cancelado` y `forfeit` como estados propios; esos casos se tratan con RF-81 a RF-83.
* Valor anterior de un dato corregido (solo se marca como `Corregido`).
* Estadísticas de jugadores actualizadas en vivo durante un mapa.
* Rol `Flex` y roles de jugador por mapa o por evento.
* Clasificaciones o rankings por rol, y el tratamiento de los jugadores `Sin rol` en ellos; se definirán en las specs que los introduzcan.
* Cambio manual de la temporada actual, salvo el valor provisional descrito en la nota de RF-3.
* Cómo asigna o corrige Retake el rol de un jugador, cómo une o separa registros de jugadores, y cómo recibe y atiende una petición de retirada de datos personales (herramientas y procesos internos).
* Historial de roles de un jugador.
* Cálculo propio de la tabla de posiciones.
* Fecha de nacimiento exacta y redes sociales (Twitch, Twitter) de los jugadores.
* Fotografías de jugadores.
* Nombre completo de las franquicias (ej. "FaZe Vegas"); se usa el nombre corto y la abreviatura.
* Dónde se usa el nombre corto y dónde la abreviatura; lo decide cada spec visual (004 en adelante).
* Cómo se obtienen, cargan y actualizan los datos (spec 003).
* Dónde y con qué diseño aparece cada dato en pantalla (specs 004 en adelante); esta spec solo fija las reglas comunes de §2.9.
* Predicciones y modelos de Machine Learning (specs 013–015).

---

## 5. Dudas y Aclaraciones Pendientes

### 5.1 Decisiones tomadas

Resueltas con Hugo el 2026-09-21:

| # | Duda | Decisión | Requisitos |
|---|---|---|---|
| 1 | Temporada actual entre temporadas | La anterior, hasta que comience el primer partido de la nueva | RF-2, RF-3 |
| 2 | Roles posibles y rol desconocido | Solo `SMG` y `AR`; si no se conoce, `Sin rol` | RF-26, RF-27 |
| 3 | Identidad sin logo | Logo de la identidad más reciente; si no hay, abreviatura sobre color primario | RF-14, RF-15 |
| 4 | Estadística vacía en la fuente | `No disponible`, nunca 0 | RF-46 |
| 5 | Campeón histórico que sigue activo | Es el mismo jugador; se registran sus gamertags anteriores | RF-17 a RF-20 |
| 6 | Nombre visible del equipo | Nombre corto (`FaZe VGS`) y abreviatura (`VGS`) | RF-11 |

Resueltas con Hugo el 2026-09-22 (revisión QA, bloque de ambigüedades):

| # | Duda | Decisión | Requisitos |
|---|---|---|---|
| A-1 | Qué significa cada verbo; datos frente a pantalla | La spec describe datos y tiene un apartado de reglas comunes de presentación que obligan a todas las specs visuales | §1.2, §2.9 |
| A-2 | Cuándo empieza una temporada y cómo se identifica | Cuando su primer partido oficial (Qualifiers incluidos) pasa a `en vivo`; se identifica por el año oficial de la liga | RF-2, RF-3, RF-52, RF-53 |
| A-3 | Qué campeonato cuenta antes de 2020 | El campeonato mundial de cada año: CoD Championship (2013–2016), CWL Championship (2017–2019), CDL Champs (2020+) | RF-4, RF-54 |
| A-4 | La temporada actual en el historial | Solo entra cuando termina su final | RF-55 |
| A-5 | Porcentaje, moneda y juego | Porcentaje tal como se publica; premio en USD nominales; juego con nombre oficial y abreviatura | RF-5, RF-56 a RF-58 |
| A-6 | Qué es una identidad nueva | Cualquier cambio de nombre corto, abreviatura, logo o colores | RF-73, RF-74 |
| A-7 | Identidad de un partido `programado` o `en vivo` | La vigente en su fecha y hora de inicio programadas | RF-12 |
| A-8 | Logo cuando la identidad más reciente tampoco lo tiene | Solo se mira la más reciente; si no tiene, abreviatura sobre color primario | RF-14, RF-15 |
| A-9 | Gamertag en los rosters históricos | El de la fecha de la final junto al actual | RF-59, RF-69 |
| A-10 | Datos personales de jugadores solo históricos | Se mantienen de todos los jugadores | RF-60 |
| A-11 | Fecha que manda para la edad | La fecha local del dispositivo del usuario. *Sustituida por R-2: fecha UTC* | RF-23 |
| A-12 | Origen del rol | Lo asigna Retake a mano; sin asignar, `Sin rol` | RF-26, RF-27 |
| A-13 | Exclusión de `Sin rol` en rankings | Se retira de la 002; pasa a las specs de rankings | RF-28 (retirado) |
| A-14 | Listas de eventos y fases | Eventos abiertos; fases cerradas: semana, grupo, winners bracket, losers bracket y gran final ("final" desaparece). *Fase desconocida: ver R-1* | RF-31, RF-61 |
| A-15 | Zona horaria de fechas y horas | La del dispositivo del usuario | RF-33, RF-70 |
| A-16 | Partido, serie y mapa | Partido = enfrentamiento completo; mapa = cada juego; se elimina "serie" | §1.1, RF-38, RF-40 |
| A-17 | Cambios de estado válidos | Solo hacia delante; si la fuente retrocede, se conserva el más avanzado | RF-62, RF-63 |
| A-18 | Unidad de Overload | Overloads anotados | RF-37 |
| A-19 | Qué es un mapa jugado | Solo mapas terminados con ganador; de un mapa repetido, solo la versión con ganador | §1.1, RF-40, RF-64 |
| A-20 | Cuál es la fuente | BreakingPoint.gg (principal), Call of Duty Esports Wiki (Fandom) y web oficial de la CDL, con esa prioridad | RF-66, RF-67 |
| A-21 | Qué activa "Estadísticas pendientes" | Que a algún mapa jugado le falten todas las estadísticas de algún jugador; una estadística suelta ausente no lo activa | RF-47, RF-48, RF-72 |
| A-22 | Qué casos distingue la tabla no disponible | Solo "no publicada" (o sin puntos); la fuente sin respuesta es un error de carga de la 001 | RF-51 |
| P-1 | Fuente que manda en los puntos CDL | La web oficial de la CDL; después BreakingPoint.gg y la Wiki. Excepción a RF-67 solo para la tabla | RF-50, RF-67, RF-75 |
| P-2 | ¿Se puede cambiar el rol asignado? | Retake puede corregirlo en cualquier momento; vale el último, sin historial | RF-26, RF-76 |
| P-3 | Límite de los datos personales | Solo datos publicados en las fuentes; se retiran si el jugador o su representante lo pide | RF-77, RF-78 |

Resueltas con Hugo el 2026-09-22 (revisión QA, bloque de contradicciones):

| # | Contradicción | Decisión | Requisitos |
|---|---|---|---|
| C-1 | La §1 excluía la presentación, pero había requisitos de pantalla | Resuelta por A-1: reglas de pantalla agrupadas en §2.9 | §1, §2.9 |
| C-2 | K/D frente a "sin métricas derivadas" | El K/D se registra tal como lo publica la fuente, sin calcularlo | RF-41, RF-45, RF-79 |
| C-3 | Rol único frente a `Sin rol` | Como máximo un rol; `Sin rol` es la ausencia de rol asignado, no un tercer rol | RF-26, RF-27 |
| C-4 | RF-1 frente a jugadores de rosters históricos | Dos niveles: detalle competitivo solo de la temporada actual; franquicias, identidades y jugadores de la temporada actual o del historial | RF-1, RF-80 |
| C-5 | RF-1 frente a identidades históricas | Resuelta por la decisión C-4 | RF-1, RF-80 |
| C-6 | Identidad de su fecha frente a gamertag actual | Resuelta por A-9: en el historial, gamertag de la fecha junto al actual | RF-59, RF-69 |
| C-7 | Texto de dato ausente en RF-25 frente a RF-46 | Una sola etiqueta, `No disponible` | RF-25, RF-46 |
| C-8 | Cambio automático de temporada frente al año manual de la 001 | Automático como comportamiento definitivo; el valor manual es provisional hasta la spec 003 | RF-3 (nota) |
| C-9 | Fases cerradas de la 002 frente a los diccionarios de la 001 | Se deja constancia aquí y la 001 se corrige después de aprobar la 002 | RF-31, §5.2 |

Resueltas con Hugo el 2026-09-22 (revisión QA, bloque de casos límite):

| # | Caso límite | Decisión | Requisitos |
|---|---|---|---|
| L-1 | Pospuesto, cancelado o forfeit | Se traducen a los tres estados: pospuesto sigue `programado`; forfeit, `finalizado` sin estadísticas; cancelado deja de mantenerse | RF-81 a RF-83 |
| L-2 | Rival por decidir | Se registra su origen como ganador o perdedor de otro partido; si no se publica, `Por definir` | RF-32, RF-84 a RF-86 |
| L-3 | Cambio de fecha u hora | Se conservan todas las fechas; manda la más reciente | RF-87, RF-88 |
| L-4 | En vivo sin marcador o detenido | 0-0 en mapas; marcador del mapa en curso `No disponible`; si se detiene, el último conocido sin aviso | RF-89 a RF-91 |
| L-5 | Mapa repetido, reiniciado o con prórroga | Cubierto por RF-64 y por el marcador de la fuente | RF-64 |
| L-6 | Mapas no jugados | Se registran al finalizar el partido y se muestran como `No jugado`, sin marcador | RF-92, RF-94 |
| L-7 | Modo no contemplado | Se registra con el modo y el marcador de la fuente y solo las estadísticas comunes | RF-95 |
| L-8 | K/D con 0 deaths | Cubierto por C-2: el de la fuente o `No disponible` | RF-79, RF-46 |
| L-9 | Correcciones de la fuente | Se aplican en partidos `finalizado` y en el historial, y se marca cada dato corregido con `Corregido` | RF-96 a RF-99 |
| L-10 | Valores imposibles | No se registran y el dato pasa a ausente, sin descartar el resto | RF-100, RF-101 |
| L-11 | Suplentes | Jugador de la temporada, con el partido marcado como de suplente y fuera del roster | RF-102 a RF-104 |
| L-12 | Liberado a mitad de temporada | Sigue como jugador de la temporada, como `Agente libre` y con su rol | RF-105 a RF-107 |
| L-13 | Edad y país parciales | Con solo año (o edad convertida a año aproximado), edad como rango; un único país | RF-23, RF-108 a RF-110 |
| L-14 | Jugador retirado | Gamertag actual = último conocido; se muestra una vez si coincide; sin relación, personas distintas | RF-111 a RF-113 |
| L-15 | Venta o mudanza | Misma plaza = misma franquicia, salvo que la fuente la publique como nueva | RF-114, RF-115 |
| L-16 | Salida de la liga | Solo se conserva si figura en el historial | RF-116 |
| L-17 | Cambio de identidad el mismo día | Cubierto por A-6 y A-7: manda la hora exacta | RF-12, RF-74 |
| L-18 | Logo en identidad antigua y no en la reciente | Cubierto por A-8 | RF-15 |
| L-19 | Equipos anteriores a 2020 | Se tratan como franquicias con identidades propias; sin color primario, color neutro de Retake | RF-117, RF-118 |
| L-20 | Campeonato incompleto | Se registra con lo que haya; el resto `No disponible`. Sin fecha de final, la identidad cuyo nombre coincide con el publicado en ese campeonato; si ninguno coincide, la vigente al terminar el año (revisado con Hugo el 2026-09-22) | RF-119 a RF-121, RF-124 |
| L-21 | Empates en la tabla | Posición tal como la publica la fuente; Retake no desempata | RF-122 |
| L-22 | Primer partido de temporada cancelado | El cambio de temporada es definitivo | RF-123 |

Resueltos con Hugo el 2026-09-22 (revisión QA, bloque de conflictos con la constitución y la spec 001):

| # | Conflicto | Decisión | Requisitos |
|---|---|---|---|
| K-1 | Faltaba la sección "Entradas no válidas" de la plantilla | Resuelto por L-10 | §3 (13), RF-100, RF-101 |
| K-2 | La §5 decía que no quedaban dudas | Resuelto: la §5 separa decisiones y pendientes | §5 |
| K-3 | Desincronización con la 001 (constitución §1.3) | Resuelto por C-8 y C-9 | RF-3 (nota), §5.2 |
| K-4 | La 001 se aprobó antes que la 002 (constitución §1.1) | Excepción documentada en §5.2; la 001 se ajusta al aprobar la 002 | §5.2 |
| K-5 | Etiquetas sin traducción (constitución §7.3) | `DQ`, `SMG` y `AR` no se traducen; el resto de etiquetas y avisos sí | RF-125, RF-126 |
| K-6 | Contraste de la abreviatura sobre el color primario (constitución §4.6) | Texto blanco o negro, el de mayor contraste, con un mínimo de 4,5:1 | RF-127, RF-128 |
| K-7 | Seguridad de los datos recibidos (constitución §6) | Textos de las fuentes siempre como texto plano; logos solo como imagen | RF-129, RF-130 |
| K-8 | RF-18 y RF-19 no verificables | Misma persona solo si una fuente los relaciona o Retake los une a mano; Retake puede separarlos | RF-131 a RF-133, RF-113 |
| K-9 | RF-7 y RF-47 con dos comportamientos | RF-47 reescrito en la revisión de ambigüedades; RF-7 reescrito como un solo comportamiento | RF-7, RF-47 |

Revisiones decididas con Hugo el 2026-09-22 al redactar el plan y al implementar (la spec sigue aprobada):

| # | Motivo | Decisión | Requisitos |
|---|---|---|---|
| R-1 | Hueco: la spec no decía qué hacer con una fase que no es ninguna de las cinco | El partido se registra sin fase y la fase se muestra como `No disponible`; RF-31 pasa a "como máximo una" | RF-31, RF-134, RF-135 |
| R-2 | Calcular la edad con la fecha local obliga a exponer la fecha de nacimiento (conflicto con RF-24) | La edad se calcula con la fecha UTC; la fecha de nacimiento nunca sale del servidor | RF-23 |
| R-3 | Aclaración de RF-3 (fase F2 de la implementación) | Un partido cuenta como empezado si llega a `en vivo` o más allá, también si la fuente lo publica directamente como `finalizado`; un partido decidido por forfeit no cuenta, porque no se juega | RF-3 |
| R-4 | Aclaración de RF-12 (fase F2) | Si un partido es anterior a todas las identidades conocidas de su franquicia, se usa la más antigua | RF-12 |
| R-5 | Aclaración de RF-13 (fase F2) | Con fecha de final, vale la identidad vigente al terminar ese día: un cambio el mismo día de la final ya cuenta | RF-13 |

Cambios derivados de la spec 003, aprobados por Hugo uno a uno antes de aprobar la 003 (su decisión Q-17) y aplicados el 2026-09-23 (la spec sigue aprobada):

| # | Cambio | Requisitos |
|---|---|---|
| C-4 | Se mantiene el calendario de la próxima temporada, sin mostrarlo, hasta que sea la actual | RF-1 |
| C-5 | El cambio automático de temporada lo cumple la 003; se retira el valor manual | RF-3 (nota) |
| C-6 | En vivo vale el marcador más avanzado de cualquier fuente | RF-67 |
| C-7 | Una identidad nueva nace del cambio del resultado combinado de las fuentes | RF-73 |
| C-8 | Las correcciones llegan dentro de los plazos de revisión de la 003 o a petición del administrador | RF-96 |
| C-9 | La regla de "misma persona" se extiende a partidos, eventos y franquicias, con retención de lo que no se enlaza | RF-131 |
| C-10 | Unos datos personales retirados no vuelven a registrarse desde las fuentes | RF-78 |
| C-12 | Si ninguna fuente publica el K/D, se calcula como kills ÷ deaths (surgió en la fase F0 de la 003; aprobado y aplicado el 2026-09-23) | RF-45, RF-79 |
| C-13 | Si la fuente no publica la semana de un clasificatorio, se calcula por el orden de la semana con partidos (surgió en la fase F0 de la 003; aprobado y aplicado el 2026-09-23) | RF-31, RF-45 |

Los cambios C-1 a C-3 y C-11 afectan a la spec 001 (su §5.4).

### 5.2 Pendientes

Excepción de orden de aprobación (decisión K-4): la spec 001 se aprobó e implementó usando una versión provisional de esta spec, en concreto para su RF-58 (año de la temporada en el pie) y su RF-70 (etiquetas traducidas). Queda como excepción a la constitución §1.1 y se resuelve ajustando la 001 con la lista siguiente.

Impacto en la spec 001 (decisiones C-9 y K-5), a corregir después de aprobar la 002 como tarea propia. **Aplicado el 2026-09-22** (tareas T-084 a T-087 de la 001, ajuste I-12 de su plan):

* Quitar la fase "final" y añadir "gran final" en el plan y en los diccionarios `es` y `en` de la 001, para que coincidan con RF-31.
* Añadir y traducir las etiquetas nuevas de §2.9: `Por definir`, "Ganador de", "Perdedor de", `No jugado`, `Corregido`, `Agente libre` y el aviso de tabla de posiciones no disponible (RF-51).
* Dejar sin traducir las siglas `DQ`, `SMG` y `AR` (RF-125).

No quedan dudas abiertas: la revisión QA del 2026-09-22 está cerrada en sus cuatro bloques.
