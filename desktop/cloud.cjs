const fs = require('node:fs/promises')
const path = require('node:path')
const zlib = require('node:zlib')
const { app, safeStorage, net } = require('electron')
const connectionPath = () => path.join(app.getPath('userData'), 'workspace.bin')
let connection
function endpoint(value) {
  const url = new URL(value)
  if (url.protocol !== 'https:' || url.username || url.password || url.port || url.search || url.hash || url.pathname !== '/' || !url.hostname.endsWith('.workers.dev')) throw new Error('Use the workspace HTTPS workers.dev address')
  return url.origin
}
async function load() {
  if (connection) return connection
  try {
    if (!safeStorage.isEncryptionAvailable() || (process.platform === 'linux' && safeStorage.getSelectedStorageBackend() === 'basic_text')) return null
    connection = JSON.parse(safeStorage.decryptString(await fs.readFile(connectionPath())))
    connection.url = endpoint(connection.url)
    return connection
  } catch { return null }
}
async function call(route, options = {}, config) {
  const current = config || await load()
  if (!current) throw new Error('Connect a workspace first')
  const response = await net.fetch(current.url + route, { ...options, redirect: 'error', signal: AbortSignal.timeout(30000),
    headers: { ...options.headers, Authorization: 'Bearer ' + current.token } })
  const reader = response.body.getReader(); const chunks = []; let length = 0
  for (;;) { const { done, value } = await reader.read(); if (done) break; length += value.length; if (length > 4 * 1024 * 1024) { await reader.cancel(); throw new Error('Workspace response too large') }; chunks.push(Buffer.from(value)) }
  if (!response.ok) throw new Error(`Workspace request failed (${response.status}). Refresh or check your invitation key.`)
  return JSON.parse(Buffer.concat(chunks).toString('utf8'))
}
async function connect(value) {
  if (!value || typeof value.token !== 'string' || !/^[A-Za-z0-9_-]{43,128}$/.test(value.token)) throw new Error('Invalid invitation key')
  const next = { url: endpoint(value.url), token: value.token }
  const identity = await call('/v1/workspace', {}, next)
  const encrypted = safeStorage.isEncryptionAvailable() && !(process.platform === 'linux' && safeStorage.getSelectedStorageBackend() === 'basic_text')
  if (encrypted) await fs.writeFile(connectionPath(), safeStorage.encryptString(JSON.stringify(next)), { mode: 0o600 })
  else await fs.rm(connectionPath(), { force: true })
  connection = next
  return { ...identity, url: next.url, remembered: Boolean(encrypted) }
}
async function info() { const c = await load(); return c ? { connected: true, url: c.url } : { connected: false } }
async function disconnect() { connection = null; await fs.rm(connectionPath(), { force: true }); return { connected: false } }
async function listLocal() {
  const root = path.join(app.getPath('userData'), 'quarantine')
  const entries = await fs.readdir(root, { withFileTypes: true }).catch(() => [])
  const rows = []
  for (const entry of entries.slice(0, 1000)) {
    if (!entry.isDirectory() || !/^[a-f0-9-]{36}$/.test(entry.name)) continue
    try { rows.push(JSON.parse(await fs.readFile(path.join(root, entry.name, 'manifest.json'), 'utf8'))) } catch {}
  }
  return rows.sort((a, b) => b.received_at.localeCompare(a.received_at))
}
async function submit(id) {
  if (typeof id !== 'string' || !/^[a-f0-9-]{36}$/.test(id)) throw new Error('Invalid submission')
  const folder = path.join(app.getPath('userData'), 'quarantine', id)
  const record = JSON.parse(await fs.readFile(path.join(folder, 'manifest.json'), 'utf8'))
  if (!/^[a-f0-9]{64}$/.test(record.sha256)) throw new Error('Invalid content hash')
  const body = zlib.gunzipSync(await fs.readFile(path.join(folder, record.sha256 + '.gz')), { maxOutputLength: 10485760 })
  const result = await call('/v1/submissions/' + id, { method: 'PUT', body, headers: {
    'Content-Type': 'application/octet-stream', 'X-Request-Id': record.request_id, 'X-Filename': encodeURIComponent(record.filename),
    'X-Source-Url': encodeURIComponent(record.source_url), 'X-Published-Date': record.published_at.slice(0, 10)
  } })
  const current = await load()
  await fs.writeFile(path.join(folder, 'receipt.json'), JSON.stringify({ id: result.id, workspace: current.url, state: result.state, received_at: result.received_at }), { mode: 0o600 })
  return result
}
module.exports = { connect, info, disconnect, call, listLocal, submit }
