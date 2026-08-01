export async function listHistoricalBidCases({ limit = 6 } = {}) {
  const response = await fetch(`/api/historical-bids/?limit=${encodeURIComponent(limit)}`, {
    headers: { Accept: 'application/json' },
  })
  const payload = await response.json()
  if (!response.ok || !payload.ok) throw new Error(payload.error || '历史项目加载失败')
  return payload
}
