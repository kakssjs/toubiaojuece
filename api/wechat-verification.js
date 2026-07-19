const VERIFICATION_TOKEN = '56c841b6c154201a1f8f6dfb22ea7e83a1c2d303'

module.exports = (request, response) => {
  response.statusCode = 200
  response.setHeader('Content-Type', 'text/plain; charset=utf-8')
  response.setHeader('Content-Length', Buffer.byteLength(VERIFICATION_TOKEN))
  response.setHeader('Cache-Control', 'public, max-age=0, must-revalidate')
  response.end(request.method === 'HEAD' ? '' : VERIFICATION_TOKEN)
}
