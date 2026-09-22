# Requerimientos Página Web Retake

Documento de requisitos base proporcionados por Hugo Portillo para la plataforma y maqueta de **Retake** (Centro de estadísticas, predicciones y modelos de Machine Learning para la Call of Duty League).

---

## Requisitos Generales y de Estructura Principal

1. **Centro de Estadísticas y Datos CDL**:
   - Plataforma integral con información y métricas detalladas de equipos, jugadores y torneos de la Call of Duty League.

2. **Cinta de Marcadores (Scoreboard Ticker)**:
   - Cinta horizontal superior que muestra los resultados de los partidos ya finalizados y el estado de los partidos que se están jugando en vivo en ese momento.

3. **Cinta de Navegación y Menú**:
   - Menú de opciones dispuesto en forma de cinta horizontal, ubicado inmediatamente debajo de la cinta de marcadores.
   - Dentro de este menú, destacar de forma visualmente llamativa y prioritaria el acceso a la sección de **Modelos de Machine Learning** (predicciones de partidos, MVP season, mejor SMG/AR, mejores equipos).

4. **Sección Principal: Spotlight del Partido en Vivo / Destacado**:
   - Recuadro de gran formato (*spotlight*) dedicado al partido en vivo actual (o al más relevante de la jornada si hay varios o está por comenzar).
   - Elementos del Spotlight:
     - Marcador detallado del encuentro.
     - Sistema de votación de los fanáticos sobre qué equipo ganará, acompañado de una gráfica interactiva de tendencia de probabilidades y cuotas de votos (al estilo visual de **Polymarket**).
     - Pestañas de navegación interna para acceder a estadísticas avanzadas del enfrentamiento.
     - Resumen breve de estadísticas individuales de los jugadores de ambos equipos.

5. **Módulo Lateral de Noticias (News Slider)**:
   - Recuadro de menor tamaño ubicado al lado del *spotlight* principal.
   - Carrusel / deslizador (*slide*) para explorar y visualizar las noticias y novedades más importantes de la liga.

6. **Sección Inferior: Cuadrícula de Próximos Partidos (Match Squares)**:
   - Dispuesta en la página principal, inmediatamente debajo de la sección de Spotlight.
   - Recuadros individuales (*squares*) para cada uno de los partidos programados o próximos a jugarse.
   - Elementos de cada Match Square:
     - Marcador en vivo (si el partido está en curso) o información de horario programado.
     - Opción interactiva para que los usuarios voten por su equipo favorito.
     - Identificación visual de los botones/recuadros de votación con los colores e identidad visual de cada franquicia CDL.
