import assert from 'node:assert/strict'
import test from 'node:test'

import {
  appPathForLocation,
  githubPagesBaseFor,
  staticShowcaseHref,
} from './github-pages-routing.js'

test('githubPagesBaseFor resolves a project Pages repository', () => {
  assert.equal(
    githubPagesBaseFor({ hostname: 'kakssjs.github.io', pathname: '/toubiaojuece/' }),
    '/toubiaojuece',
  )
})

test('githubPagesBaseFor supports an explicit static preview', () => {
  assert.equal(
    githubPagesBaseFor(
      { hostname: '127.0.0.1', pathname: '/toubiaojuece/', search: '?showcase' },
      '/toubiaojuece/',
    ),
    '/toubiaojuece',
  )
})

test('appPathForLocation prefers the hash route on GitHub Pages', () => {
  assert.equal(
    appPathForLocation({
      hostname: 'kakssjs.github.io',
      pathname: '/toubiaojuece/',
      hash: '#/agent/',
    }),
    '/agent/',
  )
})

test('appPathForLocation keeps normal server routes unchanged', () => {
  assert.equal(
    appPathForLocation({ hostname: 'localhost', pathname: '/projects/12/', hash: '' }),
    '/projects/12/',
  )
})

test('staticShowcaseHref produces a root request with a hash route', () => {
  assert.equal(staticShowcaseHref('/projects/', '/toubiaojuece'), '/toubiaojuece/#/projects/')
  assert.equal(staticShowcaseHref('/api/projects/', '/toubiaojuece'), '/api/projects/')
})
