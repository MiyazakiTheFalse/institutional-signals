import { test } from 'node:test'
import assert from 'node:assert/strict'
import { gzipSync } from 'node:zlib'
import worker, { digest } from './worker.mjs'
const token = 'a'.repeat(43), id = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
class Bucket {
  objects = new Map()
  async get(key) { const b = this.objects.get(key); return b ? { arrayBuffer: async () => b, key } : null }
  async put(key, value, options) {
    if (options?.onlyIf && this.objects.has(key)) return null
    this.objects.set(key, Buffer.from(value)); return { key }
  }
  async list({ prefix }) { return { objects: [...this.objects.keys()].filter(k => k.startsWith(prefix)).map(key => ({ key })), truncated: false } }
}
async function setup(role = 'contributor') {
  const env = { EVIDENCE: new Bucket(), AUTH_USERS: JSON.stringify([{ id: 'alice', role, token_sha256: await digest(Buffer.from(token)) }]), UPLOAD_LIMITER: { limit: async () => ({ success: true }) } }
  await env.EVIDENCE.put('status/upload-requests.json.gz', gzipSync(JSON.stringify([{ request_id: 'case:report', accepted_formats: ['pdf'] }])))
  return env
}
function request(path, method = 'GET', body, extra = {}) {
  return new Request('https://workspace.example.workers.dev' + path, { method, body, headers: { Authorization: 'Bearer ' + token, ...extra } })
}
const upload = (body = '%PDF-1.7\n%%EOF', extra = {}) => request('/v1/submissions/' + id, 'PUT', body, { 'Content-Type': 'application/octet-stream', 'X-Request-Id': 'case:report', 'X-Filename': 'report.pdf', 'X-Source-Url': 'https://publisher.example/report', 'X-Published-Date': '2026-01-01', ...extra })
test('fails closed before provisioning', async () => assert.equal((await worker.fetch(request('/v1/workspace'), {})).status, 503))
test('rejects missing and revoked credentials', async () => {
  const env = await setup()
  assert.equal((await worker.fetch(new Request('https://example.org/v1/workspace'), env)).status, 401)
  env.AUTH_USERS = '[]'; assert.equal((await worker.fetch(request('/v1/workspace'), env)).status, 401)
})
test('imports compressed immutable quarantine and retries idempotently', async () => {
  const env = await setup()
  const first = await worker.fetch(upload(), env); assert.equal(first.status, 201)
  const row = await first.json(); assert.equal(row.state, 'quarantined'); assert.equal(row.scan_state, 'not_scanned')
  assert.equal((await worker.fetch(upload(), env)).status, 200)
  assert.equal((await worker.fetch(upload('%PDF-1.7\nchanged\n%%EOF'), env)).status, 409)
  assert.equal([...env.EVIDENCE.objects.keys()].filter(k => k.startsWith('submissions/')).length, 1)
})
test('owner isolation prevents other contributors reading records', async () => {
  const env = await setup(); await worker.fetch(upload(), env)
  env.AUTH_USERS = JSON.stringify([{ id: 'bob', role: 'contributor', token_sha256: await digest(Buffer.from(token)) }])
  assert.equal((await worker.fetch(request('/v1/submissions/' + id + '?owner=alice'), env)).status, 403)
  assert.deepEqual((await (await worker.fetch(request('/v1/submissions'), env)).json()).items, [])
})
test('rejects oversized, active, wrong format and unknown requests', async () => {
  const env = await setup()
  assert.equal((await worker.fetch(upload('x', { 'Content-Length': '10485761' }), env)).status, 413)
  assert.equal((await worker.fetch(upload('%PDF-1.7\n/JavaScript\n%%EOF'), env)).status, 400)
  assert.equal((await worker.fetch(upload('MZ'), env)).status, 400)
  assert.equal((await worker.fetch(upload(undefined, { 'X-Request-Id': 'invented' }), env)).status, 409)
})
test('upload limits fail closed and enforce exhaustion', async () => {
  const env = await setup(); env.UPLOAD_LIMITER = undefined
  assert.equal((await worker.fetch(upload(), env)).status, 503)
  env.UPLOAD_LIMITER = { limit: async () => ({ success: false }) }
  assert.equal((await worker.fetch(upload(), env)).status, 429)
})
test('contributors cannot review; reviewer cannot approve unscanned evidence', async () => {
  const env = await setup(); await worker.fetch(upload(), env)
  const review = decision => request('/v1/submissions/' + id + '/review', 'POST', JSON.stringify({ owner: 'alice', decision, note: 'Verified source requested' }))
  assert.equal((await worker.fetch(review('rejected'), env)).status, 403)
  env.AUTH_USERS = JSON.stringify([{ id: 'alice', role: 'reviewer', token_sha256: await digest(Buffer.from(token)) }])
  assert.equal((await worker.fetch(review('approved'), env)).status, 409)
  assert.equal((await worker.fetch(review('needs_changes'), env)).status, 201)
  assert.equal([...env.EVIDENCE.objects.keys()].filter(k => k.startsWith('reviews/')).length, 1)
})
test('old collection heartbeat is visibly stale', async () => {
  const env = await setup()
  await env.EVIDENCE.put('status/latest.json.gz', gzipSync(JSON.stringify({ checked_at: '2020-01-01T00:00:00Z', coverage: 1, sources: {} })))
  await env.EVIDENCE.put('status/case-readiness.json.gz', gzipSync('{}'))
  const result = await (await worker.fetch(request('/v1/status'), env)).json()
  assert.equal(result.stale, true)
})

test('workspace exposes only reviewed-safe collection diagnostics and unreviewed changes', async () => {
  const env = await setup()
  const observed_at = new Date().toISOString()
  const hash = 'a'.repeat(64)
  await env.EVIDENCE.put('status/latest.json.gz', gzipSync(JSON.stringify({
    checked_at: observed_at,
    coverage: { fraction_current: 0.5, safe_to_claim_current: false },
    sources: { official: { last_attempt_at: observed_at, last_success_at: null, consecutive_failures: 2, last_error_code: 'http_403', last_error: 'private upstream diagnostic' } },
    recent_changes_limit: 100,
    recent_changes: [
      { source_id: 'official', observed_at, sha256: hash, previous_sha256: null, coverage_scope: 'original_document', review_state: 'unreviewed_content_change', raw_key: 'raw/not-public', body: 'secret payload' },
      { source_id: 'official', observed_at, sha256: 'bad', review_state: 'unreviewed_content_change' }
    ]
  })))
  await env.EVIDENCE.put('status/case-readiness.json.gz', gzipSync('{}'))
  const response = await worker.fetch(request('/v1/status'), env)
  assert.equal(response.status, 200)
  const raw = await response.text()
  const result = JSON.parse(raw)
  assert.equal(result.sources[0].last_error_code, 'http_403')
  assert.equal(result.coverage.safe_to_claim_current, false)
  assert.equal(result.recent_changes.length, 1)
  assert.equal(result.recent_changes[0].sha256, hash)
  assert.equal(result.recent_changes[0].review_state, 'unreviewed_content_change')
  assert.equal(result.recent_changes_limited, true)
  assert.ok(!raw.includes('private upstream diagnostic'))
  assert.ok(!raw.includes('raw/not-public'))
  assert.ok(!raw.includes('secret payload'))
})
