const { handleUpload } = require('@vercel/blob/client')

const MAX_PDF_SIZE = 50 * 1024 * 1024
const PATH_PREFIX = 'client-tender-documents/'

function requestIsSameOrigin(request) {
  const origin = request.headers.origin
  const host = request.headers['x-forwarded-host'] || request.headers.host
  if (!origin || !host) return false

  try {
    return new URL(origin).host === host
  } catch {
    return false
  }
}

async function authorizeAuthenticatedUpload(request, companyId) {
  const host = request.headers['x-forwarded-host'] || request.headers.host
  const protocol = request.headers['x-forwarded-proto'] || 'https'
  const authorizationUrl = new URL('/api/auth/upload-authorize/', `${protocol}://${host}`)
  authorizationUrl.searchParams.set('company_id', String(companyId))

  const result = await fetch(authorizationUrl, {
    headers: { cookie: request.headers.cookie || '' },
    redirect: 'manual',
  })
  if (!result.ok) {
    const payload = await result.json().catch(() => ({}))
    throw new Error(payload.error || 'Please sign in before uploading')
  }
}

module.exports = async function blobUpload(request, response) {
  if (request.method !== 'POST') {
    return response.status(405).json({ error: 'Method not allowed' })
  }

  if (request.body?.type === 'blob.generate-client-token' && !requestIsSameOrigin(request)) {
    return response.status(403).json({ error: 'Upload origin is not allowed' })
  }

  try {
    const result = await handleUpload({
      body: request.body,
      request,
      onBeforeGenerateToken: async (pathname, clientPayload) => {
        let payload = {}
        try {
          payload = JSON.parse(clientPayload || '{}')
        } catch {
          throw new Error('Invalid upload payload')
        }

        if (!payload.companyId) throw new Error('A company profile is required')
        await authorizeAuthenticatedUpload(request, payload.companyId)
        if (!pathname.startsWith(PATH_PREFIX) || !pathname.toLowerCase().endsWith('.pdf')) {
          throw new Error('Only PDF tender documents are allowed')
        }

        return {
          allowedContentTypes: ['application/pdf'],
          maximumSizeInBytes: MAX_PDF_SIZE,
          addRandomSuffix: true,
          tokenPayload: JSON.stringify({ companyId: String(payload.companyId) }),
        }
      },
    })
    return response.status(200).json(result)
  } catch (error) {
    return response.status(400).json({ error: error.message || 'Unable to authorize upload' })
  }
}
