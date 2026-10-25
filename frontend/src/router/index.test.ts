import { describe, expect, it, vi } from 'vitest'

vi.mock('@/config/features', () => ({
  features: Object.freeze({
    dubs: false,
    reactor: false,
    twoFactor: false,
    studioReactions: false,
    studioSync: false,
  }),
}))

import router from './index'

describe('release feature routes', () => {
  it('keeps the user directory available while disabled dubs routes use the normal 404 route', () => {
    expect(router.hasRoute('people')).toBe(true)
    expect(router.hasRoute('people-detail')).toBe(false)
    expect(router.resolve('/people').name).toBe('people')
    expect(router.resolve('/people/123').name).toBe('not-found')
    expect(router.resolve('/reactor/posts/example').name).toBe('not-found')
  })

  it('exposes the public anime roulette route', () => {
    expect(router.resolve('/roulette').name).toBe('roulette')
  })
})
