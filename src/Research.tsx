import React from 'react'

export type GraphNode = { id: string; type: string; label: string }
export type GraphEdge = {
  edge_id: string; subject_id: string; predicate: string; object_id: string; evidence_ids: string[];
  valid_from: string; valid_to: string | null; published_at: string; first_observed_at: string;
  recorded_at: string; reviewed_at?: string; review_state: string; assertion_type: string;
  scope: string; limitations: string; independence_group: string; supersedes?: string
}
export type Graph = { version?: string; nodes: GraphNode[]; edges: GraphEdge[] }
type Source = { id: string; title: string; url: string }
type Position = { x: number; y: number }
const WIDTH = 960
const HEIGHT = 500

function positions(nodes: GraphNode[]): Map<string, Position> {
  const institutions = nodes.filter(n => n.type !== 'document')
  const documents = nodes.filter(n => n.type === 'document')
  const output = new Map<string, Position>()
  institutions.forEach((node, index) => output.set(node.id, {
    x: 215, y: (index + 1) * HEIGHT / (institutions.length + 1),
  }))
  documents.forEach((node, index) => output.set(node.id, {
    x: 725, y: (index + 1) * HEIGHT / (documents.length + 1),
  }))
  return output
}
function visibleOnDate(edge: GraphEdge, end: number) {
  if (edge.review_state !== 'verified' || !edge.reviewed_at || !edge.evidence_ids.length) return false
  const timestamps = [edge.published_at, edge.first_observed_at, edge.recorded_at, edge.reviewed_at]
  return timestamps.every(value => Number.isFinite(Date.parse(value)) && Date.parse(value) <= end) &&
    Date.parse(edge.valid_from) <= end &&
    (!edge.valid_to || Date.parse(edge.valid_to) > end)
}
export function Research({ graph, sources }: { graph: Graph; sources: Source[] }) {
  const [cutoff, setCutoff] = React.useState(new Date().toISOString().slice(0, 10))
  const [selected, setSelected] = React.useState(graph.nodes.find(n => n.type !== 'document')?.id || graph.nodes[0]?.id || '')
  const [showClaims, setShowClaims] = React.useState(false)
  const [query, setQuery] = React.useState('')
  const cutoffEnd = Date.parse(cutoff + 'T23:59:59.999Z')
  const eligible = graph.edges.filter(edge => visibleOnDate(edge, cutoffEnd))
  const overridden = new Set(eligible.map(edge => edge.supersedes).filter((id): id is string => Boolean(id)))
  const active = eligible.filter(e => !overridden.has(e.edge_id) && (showClaims || e.assertion_type === 'documented_fact'))
  const connected = active.filter(edge => edge.subject_id === selected || edge.object_id === selected)
  const sourceMap = new Map(sources.map(source => [source.id, source]))
  const nodeMap = new Map(graph.nodes.map(node => [node.id, node]))
  const points = positions(graph.nodes)
  const matches = query.trim() ? graph.nodes.filter(n => n.label.toLowerCase().includes(query.trim().toLowerCase())).slice(0, 12) : []
  const selectedNode = nodeMap.get(selected)
  const selectedEdgeIds = new Set(connected.map(e => e.edge_id))
  return <section className="network-page" aria-label="Institutional relationship explorer">
    <div className="page-heading">
      <span className="eyebrow">INSTITUTIONAL KNOWLEDGE GRAPH</span>
      <h1>Explore the relationships</h1>
      <p>Investigate documented connections and the evidence supporting them. This graph currently records publisher attribution; it does not establish influence, wrongdoing or legal decision rights.</p>
    </div>
    <div className="graph-insights" aria-label="Graph summary">
      <div><span>Entities</span><strong>{graph.nodes.length}</strong><small>Institutions and documents</small></div>
      <div><span>Reviewed relations visible</span><strong>{active.length}</strong><small>As of {cutoff} UTC</small></div>
      <div><span>Relationship scope</span><strong>Attribution</strong><small>Additional relationship categories require review</small></div>
    </div>

    <div className="graph-controls">
      <label htmlFor="entity-picker">Inspect entity
        <select id="entity-picker" value={selected} onChange={event => setSelected(event.target.value)}>
          {graph.nodes.map(n => <option key={n.id} value={n.id}>{n.label} · {n.type.replaceAll('_', ' ')}</option>)}
        </select>
      </label>
      <label htmlFor="evidence-date">Evidence known by (UTC)
        <input id="evidence-date" type="date" value={cutoff} onChange={event => setCutoff(event.target.value)}
          max={new Date().toISOString().slice(0, 10)} />
      </label>
      <label htmlFor="network-search">Find another entity
        <input id="network-search" type="search" value={query} onChange={event => setQuery(event.target.value)}
          placeholder="Institution or document title" />
      </label>
      <label className="graph-toggle" htmlFor="include-claims">
        <input id="include-claims" type="checkbox" checked={showClaims} onChange={event => setShowClaims(event.target.checked)}/>
        Include reviewed attributed claims, disputes and hypotheses
      </label>
    </div>

    {matches.length > 0 && <div className="network-search-results" aria-label="Matching entities">
      {matches.map(node => <button key={node.id} type="button" onClick={() => { setSelected(node.id); setQuery('') }}>
        {node.label}<span>{node.type.replaceAll('_', ' ')}</span>
      </button>)}
    </div>}
    {query.trim() && !matches.length && <p className="result-count" role="status">No entities match this search.</p>}

    <div className="network-frame">
      <div className="network-legend">
        <div><span className="legend-dot institution"/> Institution / public body</div>
        <div><span className="legend-dot document"/> Document</div>
        <div><span className="legend-line"/> Reviewed relation</div>
      </div>
      <p className="network-instructions">Select any node to inspect its relationships. The diagram scrolls horizontally on narrow screens; the entity selector and list below provide keyboard alternatives.</p>
      <div className="network-scroll" tabIndex={0} aria-label="Interactive institutional relationship map">
        <div className="network-canvas">
          <svg className="network-lines" viewBox={'0 0 ' + WIDTH + ' ' + HEIGHT} aria-hidden="true">
            {active.map(edge => {
              const first = points.get(edge.subject_id)
              const second = points.get(edge.object_id)
              if (!first || !second) return null
              return <line key={edge.edge_id} x1={first.x} y1={first.y} x2={second.x} y2={second.y}
                className={selectedEdgeIds.has(edge.edge_id) ? 'network-link selected' : 'network-link'}/>
            })}
          </svg>
          {graph.nodes.map(node => {
            const point = points.get(node.id)
            if (!point) return null
            const related = active.some(edge => edge.subject_id === node.id || edge.object_id === node.id)
            return <button key={node.id} type="button"
              style={{ left: String(point.x / WIDTH * 100) + '%', top: String(point.y / HEIGHT * 100) + '%' }}
              className={'network-node ' + (node.type === 'document' ? 'document' : 'institution') +
                (node.id === selected ? ' selected' : '') + (!related ? ' unavailable' : '')}
              aria-pressed={node.id === selected}
              onClick={() => setSelected(node.id)}
              title={node.label}>
              <span className="network-node-type">{node.type.replaceAll('_', ' ')}</span>
              <span className="network-node-name">{node.label}</span>
            </button>
          })}
        </div>
      </div>
      <div className="network-footnote">Only reviewed relationships visible at the selected time appear as connections. An absent line does not establish that no real-world relationship exists.</div>
    </div>

    <div className="section-head network-section-head">
      <div><span className="eyebrow">SELECTED ENTITY</span><h2>{selectedNode?.label || 'Choose an entity'}</h2></div>
      <small>{connected.length} supported {connected.length === 1 ? 'relation' : 'relations'}</small>
    </div>
    {!connected.length && <div className="empty-state" role="status">
      No reviewed relationships for this entity at the selected evidence date. Choose a later date or a different entity. This does not imply there were no real-world connections.
    </div>}
    <div className="relationship-list">{connected.map(edge => <article className="relationship-card" key={edge.edge_id}>
      <span className="eyebrow">{edge.assertion_type.replaceAll('_', ' ')} · REVIEWED</span>
      <h3>{nodeMap.get(edge.subject_id)?.label || edge.subject_id} <span className="relation-verb">{edge.predicate.replaceAll('_', ' ')}</span> {nodeMap.get(edge.object_id)?.label || edge.object_id}</h3>
      <p>{edge.scope}</p><p className="caveat">{edge.limitations}</p>
      <details><summary>Inspect primary source and timestamps</summary>
        <dl className="provenance-details">
          <div><dt>Published</dt><dd>{edge.published_at}</dd></div>
          <div><dt>First observed</dt><dd>{edge.first_observed_at}</dd></div>
          <div><dt>Reviewed</dt><dd>{edge.reviewed_at}</dd></div>
          <div><dt>Source group</dt><dd>{edge.independence_group}</dd></div>
        </dl>
        {edge.evidence_ids.map(id => {
          const source = sourceMap.get(id)
          return source ? <p key={id}><a href={source.url} target="_blank" rel="noopener noreferrer">{source.title} · {id} ↗</a></p>
            : <p key={id}>Source {id} not present in the bundled catalogue.</p>
        })}
      </details>
    </article>)}</div>
    <div className="graph-method-note"><strong>Why the cautious language?</strong> Publication can establish who issued a document, but it cannot establish who privately knew what, how a decision was made, or whether a person or institution acted improperly. Those questions demand different primary evidence and independent review.</div>
  </section>
}
