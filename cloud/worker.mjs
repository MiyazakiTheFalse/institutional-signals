import { Buffer } from 'node:buffer'
import { gzipSync, gunzipSync } from 'node:zlib'
import validation from '../desktop/validation.cjs'
import provenance from '../desktop/provenance.cjs'

const MAX = 10485760
const ID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
const json = (value, status = 200) => Response.json(value, { status, headers: { 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'Content-Security-Policy': "default-src 'none'" } })
class Rejection extends Error { constructor(status, message) { super(message); this.status = status } }
export async function digest(body) { return Buffer.from(await crypto.subtle.digest('SHA-256', body)).toString('hex') }

async function authenticate(request, env) {
  // Individual revocable invitation tokens; only SHA-256 digests live in the secret.
  const token = request.headers.get('Authorization')?.match(/^Bearer ([A-Za-z0-9_-]{43,128})$/)?.[1]
  if (!token) throw new Rejection(401, 'Sign in with your workspace invitation key')
  const users = JSON.parse(env.AUTH_USERS || '[]')
  const hash = await digest(new TextEncoder().encode(token))
  const user = users.find(u => u.token_sha256 === hash && /^[a-zA-Z0-9_-]{1,64}$/.test(u.id) && ['contributor', 'reviewer'].includes(u.role))
  if (!user) throw new Rejection(401, 'Invitation key is invalid or revoked')
  return user
}
async function bounded(request, limit) {
  if (Number(request.headers.get('Content-Length')) > limit) throw new Rejection(413, 'Upload too large')
  const reader = request.body?.getReader()
  if (!reader) throw new Rejection(400, 'Body required')
  let size = 0; const chunks = []
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    size += value.byteLength
    if (size > limit) { await reader.cancel(); throw new Rejection(413, 'Upload too large') }
    chunks.push(Buffer.from(value))
  }
  return Buffer.concat(chunks)
}
async function readJSON(bucket, key, compressed = false) {
  const object = await bucket.get(key)
  if (!object) return null
  const body = Buffer.from(await object.arrayBuffer())
  return JSON.parse((compressed ? gunzipSync(body, { maxOutputLength: 4 * 1024 * 1024 }) : body).toString('utf8'))
}
const SAFE_FAILURE_CODE = /^(?:http_[45][0-9]{2}|robots_disallowed|validation_error|network_error)$/
const SAFE_SOURCE_ID = /^[A-Za-z0-9_-]{1,64}$/
const SAFE_HASH = /^[a-f0-9]{64}$/

function publicChanges(report) {
  // Source snapshots may contain untrusted response metadata; expose only explicit fields.
  if (!Array.isArray(report?.recent_changes)) return []
  const known = new Set(Object.keys(report.sources || {}))
  return report.recent_changes.slice(0, 100).filter(c =>
    c && SAFE_SOURCE_ID.test(c.source_id) && known.has(c.source_id) &&
    SAFE_HASH.test(c.sha256) && typeof c.observed_at === 'string' &&
    Number.isFinite(Date.parse(c.observed_at)) && c.review_state === 'unreviewed_content_change'
  ).map(c => ({
    source_id: c.source_id, observed_at: c.observed_at, sha256: c.sha256,
    previous_sha256: SAFE_HASH.test(c.previous_sha256) ? c.previous_sha256 : null,
    review_state: 'unreviewed_content_change',
    coverage_scope: typeof c.coverage_scope === 'string' && c.coverage_scope.length <= 80
      ? c.coverage_scope : 'unspecified',
  }))
}

const manifestKey = (user, id) => `submissions/${user}/${id}/manifest.json`
async function submission(env, user, id, owner = user.id) {
  if (!ID.test(id) || !/^[a-zA-Z0-9_-]{1,64}$/.test(owner)) throw new Rejection(400, 'Invalid submission')
  if (owner !== user.id && user.role !== 'reviewer') throw new Rejection(403, 'Not permitted')
  const record = await readJSON(env.EVIDENCE, manifestKey(owner, id))
  if (!record) throw new Rejection(404, 'Submission not found')
  return record
}
export default {
  async scheduled(_event, env) {
    const report = await readJSON(env.EVIDENCE, 'status/latest.json.gz', true)
    const age = report ? Date.now() - Date.parse(report.checked_at) : Infinity
    const status = { evaluated_at: new Date().toISOString(), collector_checked_at: report?.checked_at || null,
      alert: !Number.isFinite(age) || age < 0 || age > 90 * 60000 ? 'collector_heartbeat_missing_or_stale' : null }
    await env.EVIDENCE.put('status/watchdog.json', JSON.stringify(status))
  },
  async fetch(request, env) {
    try {
      if (!env.EVIDENCE || !env.AUTH_USERS) throw new Rejection(503, 'Workspace is not configured')
      const user = await authenticate(request, env)
      const url = new URL(request.url)
      if (request.method === 'GET' && url.pathname === '/v1/workspace') return json({ user: user.id, role: user.role })
      if (request.method === 'GET' && url.pathname === '/v1/status') {
        const [report, gates, requests] = await Promise.all(['latest', 'case-readiness', 'upload-requests'].map(k => readJSON(env.EVIDENCE, `status/${k}.json.gz`, true)))
        if (!report || !gates || !requests) throw new Rejection(503, 'Collector has not published a complete status')
        const age = Date.now() - Date.parse(report.checked_at)
        const stale = !Number.isFinite(age) || age < 0 || age > 90 * 60000
        return json({ checked_at: report.checked_at, fetched_at: new Date().toISOString(), stale, coverage: report.coverage,
          sources: Object.entries(report.sources).filter(([id]) => SAFE_SOURCE_ID.test(id)).map(([id, s]) => ({
            id, last_attempt_at: s.last_attempt_at, last_success_at: s.last_success_at,
            consecutive_failures: s.consecutive_failures,
            last_error_code: SAFE_FAILURE_CODE.test(s.last_error_code) ? s.last_error_code : null
          })),
          recent_changes: publicChanges(report),
          recent_changes_limited: Number.isInteger(report.recent_changes_limit),
          gates, upload_requests: requests })
      }
      if (request.method === 'GET' && url.pathname === '/v1/submissions') {
        const cursor = url.searchParams.get('cursor') || undefined
        if (cursor && cursor.length > 4096) throw new Rejection(400, 'Invalid cursor')
        const page = await env.EVIDENCE.list({ prefix: user.role === 'reviewer' ? 'submissions/' : `submissions/${user.id}/`, limit: 100, cursor })
        const rows = await Promise.all(page.objects.filter(o => o.key.endsWith('/manifest.json')).map(o => readJSON(env.EVIDENCE, o.key)))
        return json({ items: rows, cursor: page.truncated ? page.cursor : null })
      }
      const upload = url.pathname.match(/^\/v1\/submissions\/([^/]+)$/)
      if (upload && request.method === 'PUT') {
        const id = upload[1]
        if (!ID.test(id)) throw new Rejection(400, 'Invalid submission ID')
        if (request.headers.get('Content-Type') !== 'application/octet-stream') throw new Rejection(415, 'Use a binary upload')
        if (!env.UPLOAD_LIMITER) throw new Rejection(503, 'Upload limits are not configured')
        if (!(await env.UPLOAD_LIMITER.limit({ key: user.id })).success) throw new Rejection(429, 'Please wait before uploading again')
        const requestId = request.headers.get('X-Request-Id')
        const requests = await readJSON(env.EVIDENCE, 'status/upload-requests.json.gz', true)
        const needed = requests?.find(r => r.request_id === requestId)
        if (!needed) throw new Rejection(409, 'This evidence request is no longer active; refresh the workspace')
        let meta
        try { meta = provenance.validateProvenance({ source_url: decodeURIComponent(request.headers.get('X-Source-Url') || ''), published_at: request.headers.get('X-Published-Date') }) }
        catch { throw new Rejection(400, 'Invalid publication provenance') }
        const name = decodeURIComponent(request.headers.get('X-Filename') || '')
        const body = await bounded(request, MAX)
        try { validation.validateFile(name, body, needed.accepted_formats) } catch { throw new Rejection(400, 'File failed format or content validation') }
        const hash = await digest(body)
        const key = manifestKey(user.id, id)
        const existing = await readJSON(env.EVIDENCE, key)
        if (existing) {
          if (existing.sha256 !== hash || existing.request_id !== requestId || existing.source_url !== meta.source_url || existing.published_at !== meta.published_at) throw new Rejection(409, 'Submission ID already used')
          return json(existing)
        }
        const rawKey = `quarantine/${user.id}/${id}/${hash}.gz`
        await env.EVIDENCE.put(rawKey, gzipSync(body), { onlyIf: { etagDoesNotMatch: '*' }, httpMetadata: { contentType: 'application/gzip' } })
        const record = { id, owner: user.id, request_id: requestId, filename: name, ...meta, sha256: hash, bytes: body.length,
          received_at: new Date().toISOString(), state: 'quarantined', scan_state: 'not_scanned', raw_key: rawKey }
        const saved = await env.EVIDENCE.put(key, JSON.stringify(record), { onlyIf: { etagDoesNotMatch: '*' }, httpMetadata: { contentType: 'application/json' } })
        if (!saved) throw new Rejection(409, 'Submission was already created; refresh its status')
        return json(record, 201)
      }
      if (upload && request.method === 'GET') {
        const record = await submission(env, user, upload[1], url.searchParams.get('owner') || user.id)
        const page = await env.EVIDENCE.list({ prefix: `reviews/${record.owner}/${record.id}/`, limit: 100 })
        const reviews = await Promise.all(page.objects.map(o => readJSON(env.EVIDENCE, o.key)))
        return json({ ...record, reviews, reviews_truncated: page.truncated })
      }
      // Review records append to history. No unsafe byte downloads or automatic promotion.
      const review = url.pathname.match(/^\/v1\/submissions\/([^/]+)\/review$/)
      if (review && request.method === 'POST') {
        if (user.role !== 'reviewer') throw new Rejection(403, 'Reviewer access required')
        const input = JSON.parse((await bounded(request, 4096)).toString('utf8'))
        const record = await submission(env, user, review[1], input.owner)
        if (!['needs_changes', 'rejected'].includes(input.decision)) throw new Rejection(409, 'Approval requires an independent malware scan and evidence verification; promotion is disabled')
        if (typeof input.note !== 'string' || input.note.length < 3 || input.note.length > 2000 || /[\x00-\x08\x0b-\x1f\x7f]/.test(input.note)) throw new Rejection(400, 'Review explanation required')
        const event = { id: crypto.randomUUID(), submission_id: record.id, owner: record.owner, reviewer: user.id, decision: input.decision, note: input.note, reviewed_at: new Date().toISOString() }
        await env.EVIDENCE.put(`reviews/${record.owner}/${record.id}/${event.id}.json`, JSON.stringify(event), { onlyIf: { etagDoesNotMatch: '*' } })
        return json(event, 201)
      }
      throw new Rejection(404, 'Not found')
    } catch (error) {
      return json({ error: error instanceof Rejection ? error.message : 'Request could not be completed' }, error instanceof Rejection ? error.status : error instanceof SyntaxError || error instanceof URIError ? 400 : 500)
    }
  }
}
