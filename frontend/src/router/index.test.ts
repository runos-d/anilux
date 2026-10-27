import { describe, expect, it, vi } from 'vitest'
import routerSource from './index.ts?raw'
import sidebarSource from '@/components/Navigation/SidebarNavigation.vue?raw'
import mobileSource from '@/components/Navigation/MobileNavigation.vue?raw'
import footerSource from '@/components/common/SeoNavigation.vue?raw'

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

type RouteMatrix = Record<
  | 'indexable_static'
  | 'indexable_when_public_and_substantial'
  | 'noindex'
  | 'canonical_redirect'
  | 'not_found_in_production',
  string[]
>

const routeMatrixModules = import.meta.glob('../../../backend/apps/seo/route_matrix.json', {
  eager: true,
  import: 'default',
})
const routeMatrix = Object.values(routeMatrixModules)[0] as RouteMatrix

describe('release feature routes', () => {
  it('keeps every declared route in the shared SEO route matrix', () => {
    const declared = [...routerSource.matchAll(/\bpath:\s*["']([^"']*)["']/g)].map((match) => match[1])
    const covered = [
      ...routeMatrix.indexable_static,
      ...routeMatrix.indexable_when_public_and_substantial,
      ...routeMatrix.noindex,
      ...routeMatrix.canonical_redirect,
      ...routeMatrix.not_found_in_production,
    ]
    expect([...new Set(declared)].sort()).toEqual([...new Set(covered)].sort())
    expect(covered).toHaveLength(new Set(covered).size)
  })

  it('pins the AniLux wordmark to white instead of a theme accent', () => {
    expect(sidebarSource).toMatch(/\.logo-text\s*\{[^}]*color:\s*#fff;/s)
    expect(mobileSource).toMatch(/\.mobile-logo\s*\{[^}]*color:\s*#fff;/s)
    expect(mobileSource).not.toMatch(/\.mobile-logo\s*\{[^}]*-webkit-text-fill-color:\s*transparent;/s)
    expect(footerSource).toMatch(/\.seo-navigation-heading h2\s*\{[^}]*color:\s*#fff;/s)
  })

  it('keeps the user directory available while disabled dubs routes use the normal 404 route', () => {
    expect(router.hasRoute('people')).toBe(true)
    expect(router.hasRoute('people-detail')).toBe(false)
    expect(router.resolve('/people').name).toBe('people')
    expect(router.resolve('/people/123').name).toBe('not-found')
    expect(router.resolve('/reactor/posts/example').name).toBe('not-found')
  })

  it('exposes the public anime roulette route', () => {
    expect(router.resolve('/roulette').name).toBe('roulette')
    expect(router.resolve('/anime/franchises').name).toBe('anime-franchises')
  })
})
