import React from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

declare global {
  interface Window {
    institutionalDesktop?: { version: () => Promise<string>; importEvidence: (requestId: string) => Promise<{ canceled?: boolean; state?: string; location?: string }> }
  }
}

type Source = {
  id: string; title: string; publisher: string; published_at: string;
  url: string; type: string; reliability_note: string
}
type Observation = {
  id: string; date: string; subject: string; summary: string;
  event_type: string; source_ids: string[]; status: string
}
type Forecast = {
  id: string; question: string; institution: string; status: string;
  probability: number | null; close_at: string
}
type UploadRequest = { request_id: string; document: string; why: string; instructions: string; accepted_formats: string[] }
type Dataset = { as_of: string; notice: string; sources: Source[]; observations: Observation[]; forecasts: Forecast[]; upload_requests: UploadRequest[] }

function safeLink(value: string): string | undefined {
  try { const u = new URL(value); return u.protocol === 'https:' && !u.username && !u.password ? u.href : undefined }
  catch { return undefined }
}

function validateDataset(value: unknown): Dataset {
  if (!value || typeof value !== 'object') throw new Error('Invalid dataset')
  const d = value as Dataset
  if (typeof d.as_of !== 'string' || typeof d.notice !== 'string') throw new Error('Invalid metadata')
  for (const rows of [d.sources, d.observations, d.forecasts, d.upload_requests]) {
    if (!Array.isArray(rows) || rows.length > 10000) throw new Error('Invalid collection')
  }
  if (d.sources.some(s => !s || typeof s.id !== 'string' || typeof s.url !== 'string' || !safeLink(s.url))) throw new Error('Invalid source link')
  if (d.upload_requests.some(r => !r || typeof r.document !== 'string' || typeof r.instructions !== 'string' || !Array.isArray(r.accepted_formats))) throw new Error('Invalid upload request')
  return d
}

function App() {
  const [data, setData] = React.useState<Dataset | null>(null)
  const [error, setError] = React.useState(false)
  const [intakeStatus, setIntakeStatus] = React.useState('')
  const [importing, setImporting] = React.useState(false)
  const [welcome, setWelcome] = React.useState(() => {
    try { return localStorage.getItem('onboarded-v1') !== 'true' } catch { return true }
  })
  async function importEvidence(requestId: string) {
    if (!window.institutionalDesktop || importing) return
    setImporting(true)
    try {
      const result = await window.institutionalDesktop.importEvidence(requestId)
      setIntakeStatus(result.canceled ? 'Import cancelled.' : 'Saved on this device in quarantine. Not uploaded to the cloud, scanned or approved for forecasting.')
    } catch { setIntakeStatus('Import refused. Check the requested format, size and file contents.') }
    finally { setImporting(false) }
  }
  const [tab, setTab] = React.useState<'timeline' | 'sources' | 'forecasts'>('timeline')
  React.useEffect(() => {
    fetch('./data/dashboard.json')
      .then(response => { if (!response.ok) throw new Error('Dataset unavailable'); return response.json() })
      .then(payload => setData(validateDataset(payload)))
      .catch(() => setError(true))
  }, [])
  const sources = new Map(data?.sources.map(source => [source.id, source]))

  return <div className="app">
    <header className="site-header">
      <a href="/" className="brand"><span className="brand-mark">IS</span><span>INSTITUTIONAL <b>SIGNALS</b></span></a>
      <span className="header-note">PUBLIC RESEARCH LAB · V0.1</span>
    </header>

    <main className="container">
      {welcome && <section className="forecast-panel"><span className="eyebrow">WELCOME TO INSTITUTIONAL SIGNALS</span><h2>Start with the evidence</h2><p>Explore the source library, review the timeline, then check which evidence is missing. Forecasts stay on hold until their required evidence is current and reviewed.</p><p>This version includes a bundled research dataset. Live collection runs separately in the cloud. Desktop imports stay on your device in quarantine.</p><button type="button" onClick={() => { setWelcome(false); try { localStorage.setItem('onboarded-v1', 'true') } catch {} }}>Explore the research</button></section>}
      <div className="eyebrow">RESEARCH / CASE 001</div>
      <div className="hero-layout">
        <div>
          <h1>See the evidence.<br/><em>Test the prediction.</em></h1>
          <p className="subtitle">An open, auditable approach to studying institutional decisions. We separate public documents, behavioural hypotheses and testable forecasts.</p>
        </div>
        <div className="case-card"><span className="case-label">ACTIVE CASE STUDY</span><strong>Thames Water<br/>+ Ofwat</strong><span className="case-meta">United Kingdom · Water sector</span><span className="case-pill">Research prototype</span></div>
      </div>

      <div className="callout"><b>Evidence, not accusation.</b> A parliamentary concern about regulatory capture is not proof of corruption. This site contains no automated wrongdoing score or validated predictive-accuracy claim.</div>

      {error && <p className="message" role="alert">Could not load the local research dataset. Run the Python export script and reload.</p>}
      {!data && !error && <p className="message">Loading documented sources...</p>}
      {data && <>
        <section className="forecast-panel" aria-label="Evidence needed">
          <span className="eyebrow">EVIDENCE ASSISTANT</span><h2>What we still need</h2>
          <p>These are the case's evidence requirements. Live upload requests are generated separately by the collector; this static view does not show current R2 coverage.</p>
          {data.upload_requests.map(r => <article key={r.request_id}><h3>{r.document}</h3><p>{r.why} {r.instructions}</p><small>Formats: {r.accepted_formats.join(', ').toUpperCase()} · Maximum 10 MiB · Review required</small>{window.institutionalDesktop && <p><button type="button" disabled={importing} onClick={() => void importEvidence(r.request_id)}>Import document on this device</button></p>}</article>)}
          <p role="status">{intakeStatus}</p>
          <p>{window.institutionalDesktop ? 'Documents remain quarantined on this device. Cloud submission and reviewer approval are not connected yet.' : 'Secure intake is currently operator-assisted. Public file uploads are not enabled.'}</p>
        </section>
        <section className="metrics" aria-label="Project status">
          <div><span>Verified source records</span><strong>{data.sources.length.toString().padStart(2, '0')}</strong><small>Publisher-linked references</small></div>
          <div><span>Recorded events</span><strong>{data.observations.length.toString().padStart(2, '0')}</strong><small>Historical and attributed</small></div>
          <div><span>Registered forecasts</span><strong>{data.forecasts.length.toString().padStart(2, '0')}</strong><small>No accuracy claim yet</small></div>
        </section>

        <div className="section-head"><div><span className="eyebrow">CASE EVIDENCE</span><h2>Research register</h2></div><small>Dataset verified {data.as_of}</small></div>
        <nav className="tab-list" aria-label="Research views">
          {([['timeline', 'Event timeline'], ['sources', 'Source library'], ['forecasts', 'Prediction ledger']] as const).map(([key, label]) => <button key={key} type="button" className={tab === key ? 'selected' : ''} onClick={() => setTab(key)} aria-pressed={tab === key}>{label}</button>)}
        </nav>
        {tab === 'timeline' && <div className="feed">{data.observations.map(event => <article className="event" key={event.id}>
          <div className="event-date">{event.date}</div><div className="event-body"><span className="event-type">{event.event_type.replaceAll('_',' ')}</span><h3>{event.subject}</h3><p>{event.summary}</p><div className="source-links">{event.source_ids.map(id => { const s = sources.get(id); return s ? <a target="_blank" rel="noopener noreferrer" href={safeLink(s.url)} key={id}>Read source · {id} ↗</a> : <span key={id}>{id}</span> })}</div></div>
        </article>)}</div>}
        {tab === 'sources' && <div className="source-grid">{data.sources.map(s => <article className="source-card" key={s.id}><div className="card-top"><span>{s.type.replaceAll('_',' ')}</span><small>{s.published_at}</small></div><h3>{s.title}</h3><p className="publisher">{s.publisher}</p><p>{s.reliability_note}</p><a href={safeLink(s.url)} target="_blank" rel="noopener noreferrer">Open primary source ↗</a></article>)}</div>}
        {tab === 'forecasts' && <div className="forecast-panel">{data.forecasts.length === 0 ? <><span className="eyebrow">NO FORECASTS REGISTERED</span><h3>A good prediction starts with its failure condition.</h3><p>The first formal forecast will appear only after its binary outcome, cutoff, evidence, baseline and independent resolution rule are fixed before the relevant future decision.</p><a href="https://github.com/MiyazakiTheFalse/institutional-signals/blob/main/docs/RESEARCH_PROTOCOL.md" target="_blank" rel="noopener noreferrer">Research protocol ↗</a></> : data.forecasts.map(f => <article key={f.id}><h3>{f.question}</h3><p>{f.institution} · {f.status} · closes {f.close_at}</p><strong>{f.probability == null ? 'No probability assigned' : `${Math.round(f.probability * 100)}%`}</strong></article>)}</div>}
      </>}
    </main>
    <footer className="site-footer"><span>INSTITUTIONAL SIGNALS</span><span>Open methods · Verifiable sources · Transparent uncertainty</span><span>Research only. No financial or legal advice.</span></footer>
  </div>
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>)
