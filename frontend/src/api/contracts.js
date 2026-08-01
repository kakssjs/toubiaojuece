const CONTRACT_FIELDS = [
  'basic_info',
  'tender_content',
  'reference_points',
  'scoring_rules',
  'risk_tags',
  'material_checklist',
  'source_maintenance_info',
]

function normalizeContractPayload(contract) {
  return CONTRACT_FIELDS.reduce((payload, field) => {
    payload[field] = String(contract?.[field] ?? '').trim()
    return payload
  }, {})
}

async function parseJsonResponse(response) {
  const payload = await response.json().catch(() => ({}))
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.error || '合同标书数据请求失败')
  }
  return payload
}

export async function createContract(contract) {
  const response = await fetch('/api/contracts/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(normalizeContractPayload(contract)),
  })

  const payload = await parseJsonResponse(response)
  return payload.contract
}

export async function listContracts({ limit = 0 } = {}) {
  const query = limit ? `?limit=${encodeURIComponent(limit)}` : ''
  const response = await fetch(`/api/contracts/${query}`, {
    headers: {
      Accept: 'application/json',
    },
  })

  const payload = await parseJsonResponse(response)
  return { contracts: payload.contracts, total: payload.total ?? payload.contracts.length }
}
