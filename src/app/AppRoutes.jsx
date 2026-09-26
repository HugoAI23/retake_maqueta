import { lazy, Suspense } from 'react'
import { useRoutes } from 'react-router'
import { AdminPage } from '../admin/AdminPage.jsx'
import { AppShell } from '../layout/AppShell.jsx'
import { ComingSoonPage } from '../pages/ComingSoonPage.jsx'
import { HomePage } from '../pages/HomePage.jsx'
import { NotFoundPage } from '../pages/NotFoundPage.jsx'
import { StandingsPage } from '../pages/StandingsPage.jsx'
import { routeDefinitions } from './routeDefinitions.js'

// La página de demostración solo existe en desarrollo. En la versión de
// producción `import.meta.env.DEV` vale `false`, el compilador elimina esta
// importación y el archivo no llega al paquete final (RF-95, plan D-13).
const BlockDemoPage = import.meta.env.DEV ? lazy(() => import('../pages/dev/BlockDemoPage.jsx')) : null

/** Página de cada sección con contenido (`hasContent: true`), por su identificador. */
const contentPages = {
  standings: StandingsPage, // spec 004
}

/** @param {import('./routeDefinitions.js').RouteDefinition} definition */
function elementFor(definition) {
  switch (definition.kind) {
    case 'home':
      return <HomePage />
    case 'content': {
      const Page = contentPages[definition.sectionId]
      if (Page) return <Page />
      break
    }
    case 'comingSoon':
      return <ComingSoonPage sectionId={definition.sectionId} />
    case 'admin':
      return <AdminPage />
    case 'demo':
      if (!BlockDemoPage) return <NotFoundPage />
      return (
        <Suspense fallback={null}>
          <BlockDemoPage />
        </Suspense>
      )
    case 'notFound':
      return <NotFoundPage />
    default:
      break
  }
  // Una sección con `hasContent: true` necesita que su spec añada aquí su página.
  throw new Error(`Ruta sin página asignada: ${definition.path}`)
}

// Todas las rutas se pintan dentro del marco común (RF-1).
const routes = [
  {
    element: <AppShell />,
    children: routeDefinitions.map((definition) =>
      definition.path === '/'
        ? { index: true, element: elementFor(definition) }
        : { path: definition.path, element: elementFor(definition) },
    ),
  },
]

/** Tabla de rutas de la aplicación (plan §1.1, RF-26, RF-27, RF-54). */
export function AppRoutes() {
  return useRoutes(routes)
}
