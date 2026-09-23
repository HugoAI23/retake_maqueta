import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createDemoLoad, DEMO_DATA } from './demoScenarios.js'

function track(promise) {
  const result = { status: 'pending', value: undefined }
  promise.then(
    (value) => Object.assign(result, { status: 'resolved', value }),
    () => Object.assign(result, { status: 'rejected' }),
  )
  return result
}

async function advance(ms) {
  await vi.advanceTimersByTimeAsync(ms)
}

describe('escenarios de demostración (RF-91 a RF-93)', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('ok: los datos llegan en 1 s', async () => {
    const result = track(createDemoLoad('ok')())
    await advance(999)
    expect(result.status).toBe('pending')
    await advance(1)
    expect(result).toEqual({ status: 'resolved', value: DEMO_DATA })
  })

  it('fail: falla en 1 s', async () => {
    const result = track(createDemoLoad('fail')())
    await advance(1000)
    expect(result.status).toBe('rejected')
  })

  it('hang: no termina nunca', async () => {
    const result = track(createDemoLoad('hang')())
    await advance(60000)
    expect(result.status).toBe('pending')
  })

  it('late: los datos llegan a los 20 s, después de los 15 s de espera', async () => {
    const result = track(createDemoLoad('late')())
    await advance(15000)
    expect(result.status).toBe('pending')
    await advance(5000)
    expect(result.status).toBe('resolved')
  })

  it('los datos incluyen nombres propios de la liga (RF-72)', () => {
    expect(DEMO_DATA.home).toBe('FaZe VGS')
  })
})
