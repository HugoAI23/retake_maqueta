import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'

const ConnectionContext = createContext(null)

function readOnline() {
  return globalThis.navigator?.onLine ?? true
}

/**
 * Estado de conexión del dispositivo (plan §1.7, decisión D-7).
 *
 * Se basa en el estado de red del navegador y en sus eventos `online` y
 * `offline`. Además permite suscribirse a la recuperación de la red, que los
 * bloques en error usan para reintentar solos (RF-53).
 *
 * @param {{ children: import('react').ReactNode }} props
 */
export function ConnectionProvider({ children }) {
  const [isOnline, setIsOnline] = useState(readOnline)
  const listeners = useRef(new Set())

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true)
      listeners.current.forEach((fn) => fn())
    }
    const handleOffline = () => setIsOnline(false)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  const onReconnect = useCallback((fn) => {
    listeners.current.add(fn)
    return () => listeners.current.delete(fn)
  }, [])

  const value = useMemo(() => ({ isOnline, onReconnect }), [isOnline, onReconnect])
  return <ConnectionContext.Provider value={value}>{children}</ConnectionContext.Provider>
}

/**
 * @returns {{ isOnline: boolean, onReconnect: (fn: () => void) => () => void }}
 *   `onReconnect` devuelve la función para cancelar la suscripción.
 */
export function useConnection() {
  const value = useContext(ConnectionContext)
  if (!value) throw new Error('useConnection debe usarse dentro de <ConnectionProvider>')
  return value
}
