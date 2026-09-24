import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createLiveChannel, HEARTBEAT_TIMEOUT_MS } from './liveChannel.js'

// EventSource simulado: guarda las instancias para poder emitir eventos desde la prueba.
class FakeEventSource {
  static instances = []
  constructor(url) {
    this.url = url
    this.listeners = {}
    this.closed = false
    FakeEventSource.instances.push(this)
  }
  addEventListener(type, fn) {
    ;(this.listeners[type] ??= []).push(fn)
  }
  emit(type, data) {
    for (const fn of this.listeners[type] ?? []) fn({ data: JSON.stringify(data) })
  }
  close() {
    this.closed = true
  }
}

function fakeDocument() {
  const listeners = []
  return {
    visibilityState: 'visible',
    addEventListener: (type, fn) => type === 'visibilitychange' && listeners.push(fn),
    removeEventListener: () => {},
    setVisibility(state) {
      this.visibilityState = state
      listeners.forEach((fn) => fn())
    },
  }
}

describe('canal de eventos (T-070; RF-79, RF-82, RF-89)', () => {
  let doc
  let events
  let channel

  beforeEach(() => {
    vi.useFakeTimers()
    FakeEventSource.instances = []
    doc = fakeDocument()
    events = []
    channel = createLiveChannel({ EventSourceImpl: FakeEventSource, doc, now: () => Date.now() })
    channel.subscribe((event) => events.push(event))
  })

  afterEach(() => {
    channel.close()
    vi.useRealTimers()
  })

  it('abre una sola conexión por pestaña y reparte los avisos', () => {
    channel.subscribe(() => {})
    expect(FakeEventSource.instances).toHaveLength(1)
    expect(FakeEventSource.instances[0].url).toBe('/api/stream')
    FakeEventSource.instances[0].emit('change', { datasets: ['live'], changedAt: '2026-12-05T20:00:00Z' })
    expect(events).toContainEqual({ type: 'change', datasets: ['live'], changedAt: '2026-12-05T20:00:00Z' })
  })

  it('se cierra al ocultar la pestaña y se reabre al volver, avisando para recargar', () => {
    doc.setVisibility('hidden')
    expect(FakeEventSource.instances[0].closed).toBe(true)
    doc.setVisibility('visible')
    expect(FakeEventSource.instances).toHaveLength(2)
    expect(events).toContainEqual({ type: 'visible' })
  })

  it('da el canal por cortado si no llega un latido en 45 s, y lo recupera con el siguiente', () => {
    FakeEventSource.instances[0].emit('heartbeat', { now: 'x' })
    vi.advanceTimersByTime(HEARTBEAT_TIMEOUT_MS - 1)
    expect(channel.getStatus().cutSince).toBeNull()
    vi.advanceTimersByTime(2)
    expect(channel.getStatus().cutSince).not.toBeNull()
    FakeEventSource.instances[0].emit('heartbeat', { now: 'y' })
    expect(channel.getStatus().cutSince).toBeNull()
  })

  it('oculta la pestaña no cuenta como corte', () => {
    doc.setVisibility('hidden')
    vi.advanceTimersByTime(HEARTBEAT_TIMEOUT_MS * 2)
    expect(channel.getStatus().cutSince).toBeNull()
  })

  it('sin EventSource (navegador antiguo o pruebas) no hace nada', () => {
    const inert = createLiveChannel({ EventSourceImpl: undefined, doc })
    expect(() => inert.subscribe(() => {})).not.toThrow()
    inert.close()
  })
})
