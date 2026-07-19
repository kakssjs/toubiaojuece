export function githubPagesBaseFor(locationLike, configuredBase = '') {
  const hostname = String(locationLike?.hostname || '')
  if (hostname.endsWith('github.io')) {
    const repository = String(locationLike?.pathname || '/')
      .split('/')
      .filter(Boolean)[0]

    return repository ? `/${repository}` : ''
  }

  const isExplicitShowcase = new URLSearchParams(String(locationLike?.search || '')).has('showcase')
  const normalizedBase = String(configuredBase || '').replace(/\/+$/, '')
  return isExplicitShowcase && normalizedBase !== '/' ? normalizedBase : ''
}

export function appPathForLocation(locationLike, configuredBase = githubPagesBaseFor(locationLike)) {
  const pathname = String(locationLike?.pathname || '/')
  const hash = String(locationLike?.hash || '')
  const base = configuredBase

  if (base && hash.startsWith('#/')) return hash.slice(1)
  if (base && pathname.startsWith(base)) return pathname.slice(base.length) || '/'
  return pathname
}

export function staticShowcaseHref(href, base) {
  const path = String(href || '')
  if (!base || !path.startsWith('/') || path.startsWith('/api/')) return path
  return `${base}/#${path}`
}
