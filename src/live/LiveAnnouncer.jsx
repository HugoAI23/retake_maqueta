import { createContext, useCallback, useContext, useState } from 'react'

const AnnouncerContext = createContext(() => {})

/**
 * Región accesible que anuncia sin interrumpir los cambios de los datos en vivo, y solo esos
 * (spec 003: RF-94 a RF-96). El resto de cambios no se anuncia para no saturar a quien usa un
 * lector de pantalla.
 *
 * @param {{ children: import('react').ReactNode }} props
 */
export function LiveAnnouncerProvider({ children }) {
  const [message, setMessage] = useState('')
  const announce = useCallback((text, { dataset }) => {
    if (dataset === 'live') setMessage(text)
  }, [])
  return (
    <AnnouncerContext.Provider value={announce}>
      {children}
      <div role="status" aria-live="polite" aria-atomic="true" className="sr-only">
        {message}
      </div>
    </AnnouncerContext.Provider>
  )
}

/** @returns {(text: string, options: { dataset: string }) => void} */
export function useAnnouncer() {
  return useContext(AnnouncerContext)
}
