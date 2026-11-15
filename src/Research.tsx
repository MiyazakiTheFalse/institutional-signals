import React from 'react'
type Edge = { edge_id: string; subject_id: string; predicate: string; object_id: string; evidence_ids: string[]; valid_from: string; valid_to: string | null; published_at: string; first_observed_at: string; recorded_at: string; reviewed_at?: string; review_state: string; assertion_type: string; scope: string; limitations: string; independence_group: string; supersedes?: string }
export type Graph = { nodes: { id: string; type: string; label: string }[]; edges: Edge[] }
type Source = { id: string; title: string; url: string }
export function Research({ graph, sources }: { graph: Graph; sources: Source[] }) {
  const [cutoff, setCutoff] = React.useState(new Date().toISOString().slice(0, 10))
  const [entity, setEntity] = React.useState(graph.nodes[0]?.id || '')
  const [showClaims, setShowClaims] = React.useState(false)
  const end = cutoff + 'T23:59:59.999Z'
  const visible = graph.edges.filter(e => [e.published_at,e.first_observed_at,e.recorded_at].every(t => Date.parse(t) <= Date.parse(end)) && e.review_state === 'verified' && !!e.reviewed_at && Date.parse(e.reviewed_at) <= Date.parse(end))
  const superseded = new Set(visible.flatMap(e => e.supersedes ? [e.supersedes] : []))
  const edges = visible.filter(e => !superseded.has(e.edge_id) && Date.parse(e.valid_from) <= Date.parse(end) && (!e.valid_to || Date.parse(e.valid_to) > Date.parse(end)) && (showClaims || e.assertion_type === 'documented_fact') && [e.subject_id,e.object_id].includes(entity))
  const label = (id: string) => graph.nodes.find(n => n.id === id)?.label || id
  return <section className="forecast-panel" aria-label="Institutional knowledge graph"><span className="eyebrow">DECISION INTELLIGENCE</span><h2>Who can act, and on what evidence?</h2>
    <p>Explore documented institutional relationships as they were available to this system. Public availability does not establish what an individual privately knew.</p>
    <label>Institution or decision<select value={entity} onChange={e => setEntity(e.target.value)}>{graph.nodes.map(n => <option key={n.id} value={n.id}>{n.label}</option>)}</select></label>
    <label>Evidence available by (UTC)<input type="date" value={cutoff} onChange={e => setCutoff(e.target.value)} max={new Date().toISOString().slice(0,10)} /></label>
    <label><input type="checkbox" checked={showClaims} onChange={e => setShowClaims(e.target.checked)} /> Include reviewed attributed claims, hypotheses and disputes</label>
    {!edges.length && <p>No reviewed relationships are available for this selection. The source library remains available; missing relationships are not inferred from association.</p>}
    {edges.map(e => <article key={e.edge_id}><h3>{label(e.subject_id)} → {e.predicate.replaceAll('_',' ')} → {label(e.object_id)}</h3><p><b>{e.assertion_type.replaceAll('_',' ')}</b> · {e.scope}</p><p>{e.limitations}</p><details><summary>Inspect provenance and timing</summary><p>Published {e.published_at}; first observed {e.first_observed_at}; reviewed {e.reviewed_at}. Underlying source group: {e.independence_group}.</p>{e.evidence_ids.map(id => { const s=sources.find(row=>row.id===id); return s && <p key={id}><a href={s.url} target="_blank" rel="noopener noreferrer">{s.title}</a></p> })}</details></article>)}
    <details><summary>Research briefing for this selection</summary><p><b>Documented relationships:</b> {edges.filter(e=>e.assertion_type==='documented_fact').length}. <b>Other reviewed assertions:</b> {edges.filter(e=>e.assertion_type!=='documented_fact').length}.</p><p><b>Watchpoints:</b> changes in documented approval, blocking or dependency relationships. Every new interpretation requires evidence review.</p><p><b>Uncertainty:</b> an empty or incomplete graph cannot establish the absence of a relationship. No predictive benefit has been demonstrated.</p></details>
  </section>
}
