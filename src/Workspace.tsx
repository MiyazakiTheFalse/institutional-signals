import React from 'react'

type Submission = { id: string; filename: string; state: string; scan_state: string; received_at: string }
export type LiveStatus = { checked_at: string; fetched_at: string; stale: boolean; coverage: number; sources: { id: string; last_success_at?: string; consecutive_failures?: number }[] }
declare global {
  interface Window {
    institutionalDesktop?: {
      version: () => Promise<string>
      importEvidence: (id: string, metadata: { source_url: string; published_at: string }) => Promise<{ canceled?: boolean }>
      connect: (value: { url: string; token: string }) => Promise<{ remembered: boolean; user: string }>
      connection: () => Promise<{ connected: boolean; url?: string }>
      disconnect: () => Promise<unknown>
      status: () => Promise<LiveStatus>
      localSubmissions: () => Promise<Submission[]>
      remoteSubmissions: () => Promise<{ items: Submission[]; cursor: string | null }>
      submit: (id: string) => Promise<Submission>
    }
  }
}
const desktop = () => window.institutionalDesktop!
export function ImportEvidence({ requestId }: { requestId: string }) {
  const [expanded, setExpanded] = React.useState(false)
  const [url, setUrl] = React.useState('')
  const [date, setDate] = React.useState('')
  const [message, setMessage] = React.useState('')
  const [busy, setBusy] = React.useState(false)
  if (!window.institutionalDesktop) return null
  return <div className="import-evidence">
    <button type="button" onClick={() => setExpanded(!expanded)} aria-expanded={expanded}>Add this evidence</button>
    {expanded && <form onSubmit={async event => {
      event.preventDefault(); setBusy(true)
      try {
        const result = await desktop().importEvidence(requestId, { source_url: url, published_at: date })
        setMessage(result.canceled ? 'No file selected.' : 'Saved securely on this device. Open Workspace below to submit it for review.')
        window.dispatchEvent(new Event('evidence-imported'))
      } catch { setMessage('Could not import. Check the publisher URL, publication date, file type and 10 MiB limit.') }
      finally { setBusy(false) }
    }}>
      <label>Original publisher URL<input type="url" value={url} onChange={e => setUrl(e.target.value)} required maxLength={2000} placeholder="https://publisher.example/report" /></label>
      <label>Publication date<input type="date" value={date} onChange={e => setDate(e.target.value)} required max={new Date().toISOString().slice(0, 10)} /></label>
      <button disabled={busy} type="submit">{busy ? 'Importing…' : 'Choose document'}</button>
    </form>}
    <p role="status">{message}</p>
  </div>
}

export function Workspace() {
  const [url, setUrl] = React.useState('')
  const [token, setToken] = React.useState('')
  const [connected, setConnected] = React.useState(false)
  const [message, setMessage] = React.useState('')
  const [busy, setBusy] = React.useState(false)
  const [status, setStatus] = React.useState<LiveStatus | null>(null)
  const [local, setLocal] = React.useState<Submission[]>([])
  const [remote, setRemote] = React.useState<Submission[]>([])
  async function refresh() {
    setLocal(await desktop().localSubmissions())
    const current = await desktop().connection(); setConnected(current.connected)
    if (current.connected) {
      const [live, submissions] = await Promise.all([desktop().status(), desktop().remoteSubmissions()])
      if (!Array.isArray(live.sources) || typeof live.checked_at !== 'string' || !Array.isArray(submissions.items)) throw new Error('Invalid workspace response')
      setStatus(live); setRemote(submissions.items)
      setMessage(submissions.cursor ? 'Showing the first submission page. More records are available to the workspace operator.' : 'Workspace refreshed.')
    }
  }
  React.useEffect(() => {
    if (!window.institutionalDesktop) return
    const update = () => { void refresh().catch(() => { setStatus(null); setMessage('Workspace unavailable. Your local documents are retained; retry when connected.') }) }
    update(); window.addEventListener('evidence-imported', update)
    const timer = setInterval(update, 60000)
    return () => { clearInterval(timer); window.removeEventListener('evidence-imported', update) }
  }, [])
  if (!window.institutionalDesktop) return null
  return <section className="forecast-panel" aria-label="Workspace">
    <span className="eyebrow">YOUR WORKSPACE</span><h2>Evidence, from device to review</h2>
    {!connected ? <form onSubmit={async event => {
      event.preventDefault(); setBusy(true)
      try { const result = await desktop().connect({ url, token }); setToken(''); setConnected(true); await refresh(); setMessage(result.remembered ? 'Connected. Your invitation key is protected by the operating system.' : 'Connected for this session. Secure credential storage is unavailable, so the key was not saved.') }
      catch { setMessage('Could not connect. Check your workspace address and invitation key.') }
      finally { setBusy(false) }
    }}>
      <p>Use the address and personal invitation key supplied by your workspace operator. Imports work offline.</p>
      <label>Workspace address<input type="url" value={url} onChange={e => setUrl(e.target.value)} placeholder="https://institutional-signals-api.example.workers.dev" required /></label>
      <label>Invitation key<input type="password" value={token} onChange={e => setToken(e.target.value)} autoComplete="off" required minLength={43} maxLength={128} /></label>
      <button disabled={busy} type="submit">Connect workspace</button>
    </form> : <div className="workspace-actions"><button disabled={busy} onClick={() => void refresh().catch(() => { setStatus(null); setMessage('Refresh failed. Previously displayed collection status is no longer treated as live.') })}>Refresh</button><button onClick={async () => { await desktop().disconnect(); setConnected(false); setStatus(null); setRemote([]); setMessage('Disconnected. Local evidence is retained.') }}>Disconnect</button></div>}
    <p role="status">{message}</p>
    {status && <div><h3>{status.stale ? 'Collection delayed — forecasts remain on hold' : 'Collector status received'}</h3><p>Last collection: {new Date(status.checked_at).toLocaleString()}. This is collection health, not approval of evidence.</p><ul>{status.sources.map(s => <li key={s.id}><b>{s.id}</b> · {s.consecutive_failures ? 'Retrieval failure' : 'Last successful check'} · {s.last_success_at ? new Date(s.last_success_at).toLocaleString() : 'Never checked successfully'}</li>)}</ul></div>}
    <h3>Submission queue</h3>
    {!local.length && <p>No documents imported yet. Choose a missing evidence request above to begin.</p>}
    {local.map(item => { const uploaded = remote.find(r => r.id === item.id); return <article key={item.id}><h4>{item.filename}</h4><p>{uploaded ? `Cloud: ${uploaded.state} · Scan: ${uploaded.scan_state}` : 'On this device · Not confirmed in this workspace'} · Imported {new Date(item.received_at).toLocaleString()}</p>{!uploaded && <button disabled={!connected || busy} onClick={async () => {
      setBusy(true)
      try { await desktop().submit(item.id); await refresh(); setMessage('Submission received in private cloud quarantine. It cannot influence forecasts until scanned and verified.') }
      catch { setMessage('Submission was not confirmed. Your document is retained. Refresh and retry; the same submission ID prevents duplicates.') }
      finally { setBusy(false) }
    }}>Submit for review</button>}</article> })}
  </section>
}
