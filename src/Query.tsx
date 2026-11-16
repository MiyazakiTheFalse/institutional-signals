import React from 'react'
import { searchResearch, type QueryCase, type QueryDataset, type QuerySource } from './queryEngine'

function officialLink(source: QuerySource) {
  try {
    const url = new URL(source.url)
    return url.protocol === 'https:' && !url.username && !url.password ? url.href : undefined
  } catch {
    return undefined
  }
}
function CaseChip({ researchCase, onChoose }: { researchCase: QueryCase; onChoose: (question: string) => void }) {
  return <button className="question-case-chip" type="button"
    onClick={() => onChoose('What has ' + researchCase.aliases[0] + ' published or announced?')}>
    <span>{researchCase.title}</span><small>{researchCase.domain.replaceAll('-', ' ')}</small>
  </button>
}
export function QueryResearch({ data }: { data: QueryDataset & { as_of: string } }) {
  const [question, setQuestion] = React.useState('')
  const [submitted, setSubmitted] = React.useState('')
  const [asOf, setAsOf] = React.useState(new Date().toISOString().slice(0, 10))
  const [copyNotice, setCopyNotice] = React.useState('')
  const result = React.useMemo(() => submitted ? searchResearch(submitted, {
    cases: data.cases, sources: data.sources, observations: data.observations,
    knowledge_graph: data.knowledge_graph,
  }, asOf) : null, [submitted, asOf, data])
  const sourceById = new Map(data.sources.map(s => [s.id, s]))
  const nodeById = new Map(data.knowledge_graph.nodes.map(n => [n.id, n]))
  const examples = [
    'What did Ofwat publish about operational performance?',
    'How has Thames Water financing changed?',
    'Who is connected to Thames Water through documented publications?',
    'Will Thames Water receive court approval?',
  ]
  function ask(q: string) {
    setQuestion(q)
    setSubmitted(q)
    setCopyNotice('')
  }
  async function copyBrief() {
    if (!result?.draft) return
    const note = [
      'RESEARCH QUESTION: ' + result.draft.question,
      'TOPIC CLASSIFICATION: ' + result.draft.intent,
      'STATUS: Uncovered; no source search or claim verification performed.',
      'INITIAL EVIDENCE REQUIREMENTS:',
      ...result.draft.source_requirements.map(s => '- ' + s),
      'NEXT STEP: Register a case and review authoritative sources before making claims.',
    ].join('\n')
    try {
      await navigator.clipboard.writeText(note)
      setCopyNotice('Research brief copied. This is a planning template, not verified research.')
    } catch {
      setCopyNotice('Clipboard unavailable. Select the text from the research brief below.')
    }
  }
  return <section className="question-workspace" aria-label="Ask a research question">
    <div className="page-heading">
      <span className="eyebrow">QUERY-DRIVEN INTELLIGENCE · EXPERIMENTAL</span>
      <h1>Ask an evidence question</h1>
      <p>Search the cases and primary-source references already registered in Institutional Signals. This first version runs locally, without a paid AI API, external search or automated interpretation of source contents.</p>
    </div>
    <div className="question-callout"><strong>Scope matters.</strong> A match means relevant records were found in the curated register, not that the question has been conclusively answered. Unsupported questions receive an explicit research brief, not a fabricated result.</div>
    <form className="question-form" onSubmit={event => {
      event.preventDefault()
      if (question.trim()) ask(question.trim())
    }}>
      <label htmlFor="research-question">Research question
        <textarea id="research-question" value={question} onChange={event => setQuestion(event.target.value)}
          rows={3} maxLength={500} required placeholder="e.g. What has Ofwat published about Thames Water?" />
      </label>
      <div className="question-controls">
        <label htmlFor="query-cutoff">Evidence available by (UTC)
          <input id="query-cutoff" type="date" value={asOf} onChange={event => setAsOf(event.target.value)}
            max={new Date().toISOString().slice(0,10)} required />
        </label>
        <button type="submit">Search registered evidence</button>
      </div>
    </form>
    <div className="question-examples">
      <span className="eyebrow">EXAMPLE QUESTIONS</span>
      <div>{examples.map(e => <button type="button" key={e} onClick={() => ask(e)}>{e}</button>)}</div>
    </div>
    <div className="registered-case-list">
      <h2>Registered research cases</h2>
      {data.cases.map(c => <CaseChip key={c.id} researchCase={c} onChoose={ask} />)}
      <p>Other topics can be scoped as new cases, but cannot be answered until authorised sources are registered and reviewed.</p>
    </div>
    {result && <section className="query-results" aria-label="Search results">
      <div className="section-head">
        <div><span className="eyebrow">EVIDENCE RETRIEVAL</span>
          <h2>{result.status === 'uncovered' ? 'Not covered by the research register'
            : result.status === 'no_relevant_evidence' ? 'No matching evidence in this case'
            : result.status === 'empty' ? 'Enter a question'
            : 'Relevant curated records'}</h2>
        </div>
      </div>
      {result.research_case && <div className="query-case-context">
        <strong>{result.research_case.title}</strong>
        <span>{result.research_case.geography} · {result.research_case.domain} · research only</span>
        <p>{result.research_case.summary}</p>
      </div>}
      <div className="query-result-metadata">
        <span>Question type: <strong>{result.intent.replaceAll('_',' ')}</strong></span>
        <span>Evidence cutoff: <strong>{result.as_of} UTC</strong></span>
        <span>Curated dataset: <strong>{data.as_of}</strong></span>
      </div>

      {result.draft && <div className="research-brief">
        <h3>Draft a new research case</h3>
        <p>There is no matching registered domain. The system has not searched the open web or checked any new source.</p>
        <p><b>Question:</b> {result.draft.question}</p>
        <h4>Evidence that would be needed</h4>
        <ul>{result.draft.source_requirements.map(x => <li key={x}>{x}</li>)}</ul>
        <button type="button" onClick={() => void copyBrief()}>Copy case brief</button>
        <p role="status">{copyNotice}</p>
      </div>}

      {result.research_case && <>
        {result.intent === 'forecast' && <div className="query-alert">
          <strong>Prediction withheld.</strong> This feature cannot estimate an outcome or assign probability. Only preregistered and eligible forecasts with independently reviewed evidence can be reported.
        </div>}
        {result.intent === 'explanation' && <div className="query-alert">
          <strong>Causal interpretation withheld.</strong> Matching records cannot establish motive, wrongdoing or causation.
        </div>}
        <div className="query-summary" aria-label="Matching records">
          <div><strong>{result.matched_observations.length}</strong><span>Curated observations</span></div>
          <div><strong>{result.matched_sources.length}</strong><span>Source records</span></div>
          <div><strong>{result.matched_edges.length}</strong><span>Reviewed graph links</span></div>
        </div>
        {result.status === 'no_relevant_evidence' && <p className="empty-state">No indexed evidence matched the topic and cutoff. This is a gap in our registered coverage, not evidence that nothing happened.</p>}
        {result.matched_observations.length > 0 && <>
          <h3>Relevant observations</h3>
          <div className="query-record-list">{result.matched_observations.map(o => <article key={o.id} className="query-record">
            <span className="eyebrow">{o.date} · {o.event_type.replaceAll('_',' ')} · curated</span>
            <h4>{o.subject}</h4><p>{o.summary}</p>
            <div className="source-links">{o.source_ids.map(id => {
              const s = sourceById.get(id)
              return s && officialLink(s) ? <a key={id} href={officialLink(s)} target="_blank" rel="noopener noreferrer">Source {id} ↗</a>
                : <span key={id}>Unavailable source ID: {id}</span>
            })}</div>
          </article>)}</div>
        </>}
        {result.matched_sources.length > 0 && <>
          <h3>Relevant publisher records</h3>
          <div className="query-record-list">{result.matched_sources.map(s => <article className="query-record" key={s.id}>
            <span className="eyebrow">{s.published_at} · {s.type.replaceAll('_',' ')}</span>
            <h4>{s.title}</h4><p>{s.publisher}</p><p className="caveat">{s.reliability_note}</p>
            {officialLink(s) && <a href={officialLink(s)} target="_blank" rel="noopener noreferrer">View publisher record ↗</a>}
          </article>)}</div>
        </>}
        {result.matched_edges.length > 0 && <>
          <h3>Reviewed relationship records</h3>
          <div className="query-record-list">{result.matched_edges.map(edge => <article key={edge.edge_id} className="query-record">
            <span className="eyebrow">{edge.assertion_type.replaceAll('_',' ')} · reviewed</span>
            <h4>{nodeById.get(edge.subject_id)?.label || edge.subject_id} → {edge.predicate.replaceAll('_',' ')} → {nodeById.get(edge.object_id)?.label || edge.object_id}</h4>
            <p>{edge.scope}</p><p className="caveat">{edge.limitations}</p>
            <details><summary>Inspect evidence and review timestamps</summary>
              <p>Published: {edge.published_at} · First observed: {edge.first_observed_at} · Reviewed: {edge.reviewed_at}</p>
              {edge.evidence_ids.map(id => {
                const s = sourceById.get(id)
                return s && officialLink(s) ? <p key={id}><a href={officialLink(s)} target="_blank" rel="noopener noreferrer">{s.title} ↗</a></p>
                  : <p key={id}>Missing source metadata: {id}</p>
              })}
            </details>
          </article>)}</div>
        </>}
      </>}
      <div className="query-limitations"><h3>What this result cannot establish</h3>
        <ul>{result.limitations.map((limitation, i) => <li key={i}>{limitation}</li>)}</ul>
      </div>
    </section>}
  </section>
}
