import React from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'
import './workstation.css'
import { ImportEvidence, Workspace, type LiveStatus } from './Workspace'
import { Research, type Graph } from './Research'

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
  probability: number | null; close_at: string;
  resolution_rule?: string; baseline_probability?: number | null
}
type UploadRequest = {
  request_id: string; document: string; why: string;
  instructions: string; accepted_formats: string[]
}
type Dataset = {
  as_of: string; notice: string; sources: Source[]; observations: Observation[];
  forecasts: Forecast[]; upload_requests: UploadRequest[]; knowledge_graph: Graph
}
type Page = 'overview' | 'timeline' | 'relationships' | 'evidence' | 'forecasts' | 'workspace'
type NavItem = { key: Page; label: string }
const NAV: NavItem[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'timeline', label: 'Timeline' },
  { key: 'relationships', label: 'Relationships' },
  { key: 'evidence', label: 'Evidence' },
  { key: 'forecasts', label: 'Forecasts' },
  { key: 'workspace', label: 'Workspace' },
]

function safeLink(value: string): string | undefined {
  try {
    const u = new URL(value)
    return u.protocol === 'https:' && !u.username && !u.password ? u.href : undefined
  } catch { return undefined }
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
  if (!d.knowledge_graph || !Array.isArray(d.knowledge_graph.nodes) || !Array.isArray(d.knowledge_graph.edges)) throw new Error('Invalid graph')
  return d
}
function SourceLink({ source, label = 'Open primary source' }: { source: Source; label?: string }) {
  return <a href={safeLink(source.url)} target="_blank" rel="noopener noreferrer">{label}<span aria-hidden="true"> ↗</span></a>
}
function PageHeading({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return <div className="page-heading">
    <span className="eyebrow">{eyebrow}</span>
    <h1>{title}</h1>
    <p>{description}</p>
  </div>
}

function Overview({ data, live, go }: { data: Dataset; live: LiveStatus | null; go: (page: Page) => void }) {
  const liveCurrent = live && !live.stale && Number.isFinite(Date.parse(live.fetched_at)) &&
    Date.now() - Date.parse(live.fetched_at) < 90 * 60000 && Date.now() >= Date.parse(live.fetched_at)
  const sourceMap = new Map(data.sources.map(s => [s.id, s]))
  const publisherNodes = data.knowledge_graph.nodes.filter(n => n.type !== 'document')
  return <>
    <div className="eyebrow">CASE STUDY 001 · UK WATER SECTOR</div>
    <div className="hero-layout">
      <div>
        <h1>Understand the institutions.<br/><em>Trace the evidence.</em></h1>
        <p className="subtitle">Explore what has actually been documented, how institutions are connected, and what evidence is still missing before any prediction can be trusted.</p>
        <div className="hero-actions">
          <button type="button" onClick={() => go('relationships')}>Explore relationships</button>
          <button type="button" className="secondary-action" onClick={() => go('timeline')}>View event timeline</button>
        </div>
      </div>
      <div className="case-card">
        <span className="case-label">INITIAL CASE · IN RESEARCH</span>
        <strong>Thames Water<br/>+ Ofwat</strong>
        <span className="case-meta">Regulation · Finance · Parliamentary scrutiny</span>
        <span className="case-pill">Evidence verification in progress</span>
      </div>
    </div>

    <section className="status-strip" aria-label="Research readiness">
      <div>
        <span className="eyebrow">COLLECTION HEALTH</span>
        <strong>{liveCurrent ? (live.coverage?.safe_to_claim_current ? 'Checks current' : 'Incomplete coverage') : 'Not verified live here'}</strong>
        <small>{liveCurrent ? 'Latest connected collector response; content review separate' : 'Open Workspace to retrieve a current collector report'}</small>
      </div>
      <div>
        <span className="eyebrow">FORECAST STATUS</span>
        <strong>{data.forecasts.length ? 'Registered forecasts' : 'No forecasts registered'}</strong>
        <small>Do not infer predictive skill from a research prototype</small>
      </div>
      <div>
        <span className="eyebrow">SOURCE DATASET</span>
        <strong>Curated · {data.as_of}</strong>
        <small>Bundled research data, not an automatically refreshed news feed</small>
      </div>
    </section>

    <div className="callout"><b>Evidence, not accusation.</b> Oversight concerns, company statements and research hypotheses are not proof of corruption or misconduct. Every relationship and event needs inspectable provenance.</div>

    <div className="section-head"><div><span className="eyebrow">EXPLORE THE CASE</span><h2>Start with a question</h2></div></div>
    <div className="journey-grid">
      <button className="journey-card" type="button" onClick={() => go('timeline')}>
        <span className="journey-number">01 · CHRONOLOGY</span><strong>What happened?</strong>
        <span>Review dated observations alongside the original publisher references.</span><span className="journey-link">Explore timeline →</span>
      </button>
      <button className="journey-card" type="button" onClick={() => go('relationships')}>
        <span className="journey-number">02 · CONTEXT</span><strong>Who is connected?</strong>
        <span>Inspect documented institutional relationships and their limitations.</span><span className="journey-link">Open network →</span>
      </button>
      <button className="journey-card" type="button" onClick={() => go('evidence')}>
        <span className="journey-number">03 · VERIFICATION</span><strong>What is still missing?</strong>
        <span>Check source provenance, blocked access and requirements awaiting review.</span><span className="journey-link">Inspect evidence →</span>
      </button>
      <button className="journey-card" type="button" onClick={() => go('forecasts')}>
        <span className="journey-number">04 · EVALUATION</span><strong>What can we predict?</strong>
        <span>See registered decision questions, baselines and outcomes when eligible.</span><span className="journey-link">View forecasts →</span>
      </button>
    </div>

    <div className="metrics" aria-label="Curated research records">
      <div><span>Source references</span><strong>{String(data.sources.length).padStart(2, '0')}</strong><small>Curated publisher-linked entries</small></div>
      <div><span>Documented observations</span><strong>{String(data.observations.length).padStart(2, '0')}</strong><small>Attributed historical notes</small></div>
      <div><span>Graph entities</span><strong>{String(data.knowledge_graph.nodes.length).padStart(2, '0')}</strong><small>{publisherNodes.length} non-document entities</small></div>
      <div><span>Graph relationships</span><strong>{String(data.knowledge_graph.edges.length).padStart(2, '0')}</strong><small>Publisher attribution, not proof of influence</small></div>
    </div>

    <div className="section-head">
      <div><span className="eyebrow">RECENT CURATED OBSERVATIONS</span><h2>Latest on the record</h2></div>
      <button type="button" className="text-action" onClick={() => go('timeline')}>Full timeline →</button>
    </div>
    <div className="feed">{data.observations.slice(0, 3).map(event => <article className="event" key={event.id}>
      <div className="event-date">{event.date}</div>
      <div className="event-body"><span className="event-type">{event.event_type.replaceAll('_', ' ')}</span>
        <h3>{event.subject}</h3><p>{event.summary}</p>
        <div className="source-links">{event.source_ids.map(id => {
          const source = sourceMap.get(id)
          return source ? <SourceLink key={id} source={source} label={'Source: ' + id} /> : <span key={id}>{id}</span>
        })}</div>
      </div>
    </article>)}</div>
  </>
}

function Timeline({ data }: { data: Dataset }) {
  const [query, setQuery] = React.useState('')
  const sourceMap = new Map(data.sources.map(s => [s.id, s]))
  const filtered = data.observations.filter(e => [e.subject, e.summary, e.event_type, e.date].join(' ').toLowerCase().includes(query.trim().toLowerCase()))
  return <>
    <PageHeading eyebrow="CHRONOLOGY" title="Event timeline" description="Dated observations from the curated register. Each observation is an attributed account or publication, not a finding of intent."/>
    <label className="search-label" htmlFor="event-search">Search observations
      <input id="event-search" type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search date, institution or event" />
    </label>
    <p className="result-count" role="status">{filtered.length} of {data.observations.length} observations shown · dataset {data.as_of}</p>
    {!filtered.length && <p className="empty-state">No observations match this search. Try another term.</p>}
    <div className="feed">{filtered.map(event => <article className="event" key={event.id}>
      <div className="event-date">{event.date}</div><div className="event-body">
        <span className="event-type">{event.event_type.replaceAll('_', ' ')}</span>
        <h2>{event.subject}</h2><p>{event.summary}</p>
        <div className="source-links">{event.source_ids.map(id => {
          const source = sourceMap.get(id)
          return source ? <SourceLink key={id} source={source} label={'Read source · ' + id} /> : <span key={id}>{id}</span>
        })}</div>
      </div>
    </article>)}</div>
  </>
}

function Evidence({ data, live, go }: { data: Dataset; live: LiveStatus | null; go: (page: Page) => void }) {
  const [query, setQuery] = React.useState('')
  const filtered = data.sources.filter(s => [s.title, s.publisher, s.type, s.id].join(' ').toLowerCase().includes(query.trim().toLowerCase()))
  const current = live && !live.stale && Date.now() - Date.parse(live.fetched_at) < 90 * 60000
  const requests = current ? live.upload_requests : data.upload_requests
  return <>
    <PageHeading eyebrow="EVIDENCE LIBRARY" title="Verify the record" description="Primary sources and publication records are the foundation. A retrieved document is not a verified claim until it has been reviewed."/>
    <section className="evidence-layout">
      <div className="evidence-main">
        <div className="section-head"><div><span className="eyebrow">SOURCE CATALOGUE</span><h2>Research documents</h2></div></div>
        <label className="search-label" htmlFor="source-search">Search by publisher or topic
          <input id="source-search" type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search source titles and publishers" />
        </label>
        <p role="status" className="result-count">{filtered.length} of {data.sources.length} curated references</p>
        {!filtered.length && <p className="empty-state">No sources match your search.</p>}
        <div className="source-grid">{filtered.map(s => <article className="source-card" key={s.id}>
          <div className="card-top"><span>{s.type.replaceAll('_', ' ')}</span><small>{s.published_at}</small></div>
          <h3>{s.title}</h3><p className="publisher">{s.publisher}</p><p>{s.reliability_note}</p>
          <SourceLink source={s}/>
        </article>)}</div>
      </div>
      <aside className="evidence-side" aria-label="Missing evidence">
        <span className="eyebrow">RESEARCH READINESS</span>
        <h2>Required before forecasting</h2>
        <p>{current ? 'Based on the latest connected collector assessment. Successful retrieval alone does not mean evidence is approved.' : 'Showing bundled requirements only. For current evidence coverage, connect the workspace.'}</p>
        {requests.length === 0 ? <p>No open requests in this assessment. Independent verification and forecasting eligibility are still separate checks.</p> :
          requests.map(r => <article className="requirement-card" key={r.request_id}>
            <h3>{r.document}</h3><p>{r.why}</p><p>{r.instructions}</p><small>Accepted: {r.accepted_formats.join(', ').toUpperCase()} · Up to 10 MiB</small>
            <ImportEvidence requestId={r.request_id}/>
          </article>)}
        <button type="button" className="secondary-action" onClick={() => go('workspace')}>Open collection workspace</button>
      </aside>
    </section>
  </>
}

function Forecasts({ data }: { data: Dataset }) {
  return <>
    <PageHeading eyebrow="PROSPECTIVE RESEARCH" title="Prediction ledger" description="Predictions must be registered before the relevant outcome, with an evidence cutoff, baseline and independent resolution rule."/>
    {!data.forecasts.length ? <div className="forecast-panel empty-forecast">
      <span className="eyebrow">NO FORECASTS REGISTERED</span>
      <h2>We don't invent probabilities to fill a dashboard.</h2>
      <p>The first forecast will appear when its exact decision question, outcome criteria, data cutoff, evidence, model baseline and independent resolution procedure are documented.</p>
      <a href="https://github.com/MiyazakiTheFalse/institutional-signals/blob/main/docs/RESEARCH_PROTOCOL.md" target="_blank" rel="noopener noreferrer">Read the research protocol ↗</a>
    </div> : <div className="forecast-list">{data.forecasts.map(f => <article className="forecast-panel" key={f.id}>
      <span className="eyebrow">{f.status.replaceAll('_', ' ')}</span><h2>{f.question}</h2>
      <p>{f.institution} · Registration closes {f.close_at}</p>
      <strong className="forecast-probability">{f.probability === null ? 'No probability assigned' : String(Math.round(f.probability * 100)) + '%'}</strong>
      {f.probability !== null && <progress max={100} value={Math.round(f.probability * 100)} aria-label="Registered forecast probability" />}
      {f.resolution_rule && <p>Resolution rule: {f.resolution_rule}</p>}
      {typeof f.baseline_probability === 'number' && <p>Baseline: {Math.round(f.baseline_probability * 100)}%</p>}
    </article>)}</div>}
    <p className="caveat">No accuracy, calibration or predictive improvement can be claimed until enough independent outcomes have been resolved and evaluated.</p>
  </>
}

function App() {
  const [data, setData] = React.useState<Dataset | null>(null)
  const [error, setError] = React.useState(false)
  const [live, setLive] = React.useState<LiveStatus | null>(null)
  const [page, setPage] = React.useState<Page>('overview')
  const [welcome, setWelcome] = React.useState(() => {
    try { return localStorage.getItem('onboarded-v1') !== 'true' } catch { return true }
  })
  React.useEffect(() => {
    let active = true
    fetch('./data/dashboard.json')
      .then(response => { if (!response.ok) throw new Error('Dataset unavailable'); return response.json() })
      .then(payload => { if (active) setData(validateDataset(payload)) })
      .catch(() => { if (active) setError(true) })
    return () => { active = false }
  }, [])
  function navigate(target: Page) {
    setPage(target)
    window.scrollTo({ top: 0, behavior: 'auto' })
    requestAnimationFrame(() => document.getElementById('main-content')?.focus({ preventScroll: true }))
  }
  return <div className="app">
    <a className="skip-link" href="#main-content">Skip to main content</a>
    <header className="site-header workstation-header">
      <button type="button" className="brand brand-button" onClick={() => navigate('overview')} aria-label="Institutional Signals — overview">
        <span className="brand-mark" aria-hidden="true">IS</span><span>INSTITUTIONAL <b>SIGNALS</b></span>
      </button>
      <span className="header-note">RESEARCH WORKSTATION · V0.3 PREVIEW</span>
    </header>
    <nav className="primary-nav" aria-label="Main navigation">
      <div className="primary-nav-inner">{NAV.map(item => <button type="button" key={item.key}
        aria-current={page === item.key ? 'page' : undefined}
        className={page === item.key ? 'active' : ''}
        onClick={() => navigate(item.key)}>{item.label}</button>)}</div>
    </nav>
    <main className="container workstation-main" id="main-content" tabIndex={-1}>
      <div className="sr-only" role="status" aria-live="polite">
        Viewing {NAV.find(item => item.key === page)?.label} research view
      </div>
      {error && <div className="message" role="alert">The curated data could not be loaded. Please reopen the app or reinstall a tested build.</div>}
      {!data && !error && <p className="message" role="status">Loading research dataset…</p>}
      {data && <>
        {page === 'overview' && <>
          {welcome && <section className="welcome-banner">
            <div><span className="eyebrow">GETTING STARTED</span><h2>Follow evidence, not assumptions.</h2>
              <p>Begin with the timeline or relationships. Source snapshots and forecasts remain unverified until their independent review gates are satisfied.</p></div>
            <button type="button" onClick={() => { setWelcome(false); try { localStorage.setItem('onboarded-v1', 'true') } catch {} }}>Got it</button>
          </section>}
          <Overview data={data} live={live} go={navigate}/>
        </>}
        {page === 'timeline' && <Timeline data={data}/>}
        {page === 'relationships' && <Research graph={data.knowledge_graph} sources={data.sources}/>}
        {page === 'evidence' && <Evidence data={data} live={live} go={navigate}/>}
        {page === 'forecasts' && <Forecasts data={data}/>}
        {page === 'workspace' && <>
          <PageHeading eyebrow="PRIVATE OPERATOR WORKSPACE" title="Collection and review" description="Connect to an explicitly provisioned workspace to inspect source health, import local evidence and submit it to the private review queue. The public research interface works offline."/>
          <Workspace onStatus={setLive}/>
        </>}
      </>}
    </main>
    <footer className="site-footer"><span>INSTITUTIONAL SIGNALS</span>
      <span>Open methods · Verifiable sources · Transparent uncertainty</span>
      <span>Research only. No financial or legal advice.</span>
    </footer>
  </div>
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>)
