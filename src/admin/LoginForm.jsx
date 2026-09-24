import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AdminAuthError, AdminBlockedError, login } from './adminApi.js'

/** Motivo del aviso: credenciales, bloqueo, servidor que no responde u otro fallo. */
function failureKind(failure) {
  if (failure instanceof AdminBlockedError) return 'blocked'
  if (failure instanceof AdminAuthError) return 'wrong'
  // Sin respuesta (0) o error del servidor o del proxy (5xx): no es un problema de la contraseña.
  if (failure?.status === 0 || failure?.status >= 500) return 'unreachable'
  return 'error'
}

const field = 'min-h-11 rounded-md border border-border bg-bg px-3 text-text focus-visible:border-accent'

/**
 * Pantalla de acceso (spec 003: RF-124 a RF-133). Un único mensaje ante credenciales incorrectas,
 * sin decir si falla el usuario o la contraseña (RF-126).
 *
 * @param {{ onSignedIn: (username: string) => void }} props
 */
export function LoginForm({ onSignedIn }) {
  const { t } = useTranslation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [sending, setSending] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    setSending(true)
    setError(null)
    try {
      const result = await login(username, password)
      setPassword('')
      onSignedIn(result?.username ?? username)
    } catch (failure) {
      setError(failureKind(failure))
    } finally {
      setSending(false)
    }
  }

  return (
    <section className="mx-auto flex w-full max-w-sm flex-col gap-4 rounded-xl border border-border bg-surface p-6">
      <h1 className="text-2xl font-bold">{t('admin.login.heading')}</h1>
      <form className="flex flex-col gap-4" onSubmit={submit} noValidate>
        <label className="flex flex-col gap-1 font-semibold">
          {t('admin.login.username')}
          <input className={field} value={username} onChange={(e) => setUsername(e.target.value)}
                 autoComplete="username" required />
        </label>
        <label className="flex flex-col gap-1 font-semibold">
          {t('admin.login.password')}
          <input className={field} type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                 autoComplete="current-password" required />
        </label>
        {error && (
          <p role="alert" className="rounded-md border border-border bg-raised p-3 text-text">
            {t(`admin.login.${error}`)}
          </p>
        )}
        <button type="submit" disabled={sending}
                className="min-h-11 rounded-md bg-accent px-4 font-semibold text-bg hover:opacity-90 disabled:opacity-60">
          {t('admin.login.submit')}
        </button>
      </form>
    </section>
  )
}
