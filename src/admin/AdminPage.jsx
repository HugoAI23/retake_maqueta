import { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { usePageTitle } from '../shared/usePageTitle.js'
import { AdminAuthError, logout, me } from './adminApi.js'
import { LogPanel } from './LogPanel.jsx'
import { LoginForm } from './LoginForm.jsx'
import { SourcesPanel } from './SourcesPanel.jsx'
import { SummariesPanel } from './SummariesPanel.jsx'

/**
 * Página de administración `/admin` (spec 003: RF-97 a RF-154; plan §2.6).
 *
 * Dentro del marco común, sin entrada en el menú. Sin sesión, pide usuario y contraseña; si la
 * sesión caduca mientras se usa, vuelve a pedirlos (RF-137). Cada panel es un bloque de la 001
 * con sus reglas de carga, error y conexión (RF-115).
 */
export function AdminPage() {
  const { t } = useTranslation()
  usePageTitle(t('admin.title'))
  const [auth, setAuth] = useState({ status: 'checking', username: null })
  const [logSource, setLogSource] = useState('')

  useEffect(() => {
    let active = true
    me().then((user) => active && setAuth({ status: 'ready', username: user?.username }))
      .catch(() => active && setAuth({ status: 'login', username: null }))
    return () => {
      active = false
    }
  }, [])

  const onAuthLost = useCallback((error) => {
    if (error instanceof AdminAuthError || error?.status === 401) setAuth({ status: 'login', username: null })
  }, [])

  // Toda carga de un panel que responda 401 devuelve a la pantalla de acceso.
  const guard = useCallback((load) => () => load().catch((error) => {
    onAuthLost(error)
    throw error
  }), [onAuthLost])

  const signOut = async () => {
    try {
      await logout()
    } finally {
      setAuth({ status: 'login', username: null })
    }
  }

  const showLog = (source) => {
    setLogSource(source)
    document.getElementById('admin-log')?.scrollIntoView?.()
  }

  if (auth.status === 'checking') return null
  if (auth.status === 'login') return <LoginForm onSignedIn={(username) => setAuth({ status: 'ready', username })} />

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-3xl font-bold">{t('admin.title')}</h1>
        <div className="flex items-center gap-3">
          {auth.username && <p className="text-sm text-muted">{t('admin.signedInAs', { username: auth.username })}</p>}
          <button type="button" onClick={signOut}
                  className="min-h-11 rounded-md border border-border bg-raised px-4 font-semibold hover:border-accent hover:text-accent">
            {t('admin.logout')}
          </button>
        </div>
      </header>
      <SourcesPanel guard={guard} onShowLog={showLog} onAuthLost={onAuthLost} />
      <LogPanel guard={guard} source={logSource} onSourceChange={setLogSource} />
      <SummariesPanel guard={guard} onShowLog={showLog} />
    </div>
  )
}
