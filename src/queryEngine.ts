/**
 * Deterministic, offline query planner for explicitly registered research cases.
 * This is NOT an LLM, live web search, source reviewer, or forecasting model.
 * Evidence snippets are copied from curated records; no factual prose is invented.
 */
export type QueryCase = {
  id: string
  title: string
  summary: string
  domain: string
  geography: string
  aliases: string[]
  topics: string[]
  source_ids: string[]
  observation_ids: string[]
  entity_ids: string[]
  readiness: 'research_only'
}
export type QuerySource = {
  id: string
  title: string
  publisher: string
  published_at: string
  verified_at: string
  type: string
  url: string
  reliability_note: string
}
export type QueryObservation = {
  id: string
  date: string
  subject: string
  summary: string
  event_type: string
  source_ids: string[]
  status: string
}
export type QueryEdge = {
  edge_id: string
  subject_id: string
  object_id: string
  predicate: string
  review_state: string
  assertion_type: string
  evidence_ids: string[]
  published_at: string
  first_observed_at: string
  recorded_at: string
  reviewed_at?: string
  valid_from: string
  valid_to: string | null
  supersedes?: string
  scope: string
  limitations: string
}
export type QueryDataset = {
  cases: QueryCase[]
  sources: QuerySource[]
  observations: QueryObservation[]
  knowledge_graph: {
    nodes: { id: string; type: string; label: string }[]
    edges: QueryEdge[]
  }
}
export type QueryIntent = 'evidence' | 'timeline' | 'relationships' | 'forecast' | 'explanation' | 'general'
export type QueryStatus = 'empty' | 'uncovered' | 'evidence_found' | 'no_relevant_evidence'
export type QueryResult = {
  status: QueryStatus
  intent: QueryIntent
  query: string
  as_of: string
  research_case: QueryCase | null
  matched_sources: QuerySource[]
  matched_observations: QueryObservation[]
  matched_edges: QueryEdge[]
  limitations: string[]
  draft: { question: string; intent: QueryIntent; source_requirements: string[] } | null
}
const STOPWORDS = new Set([
  'a','an','and','are','as','at','be','by','can','could','did','do','does','for','from',
  'has','have','how','i','in','is','it','me','my','of','on','or','our','show','tell','than',
  'that','the','their','them','there','these','this','to','us','was','were','what','when',
  'where','which','who','with','would','you','about','give','find','please',
  'relation','relations','relationship','relationships','connected','connect',
  'evidence','sources','source','graph','documents','document','timeline',
  'forecast','forecasts','prediction','predictions','predict','likely','probability',
  'will','chance','future','why','reason','reasons','because','influence',
  'summary','overview','case','study','report','reports','published',
])
const SOURCE_REQUIREMENTS: Record<QueryIntent, string[]> = {
  general: ['Primary, attributable documents with publication dates', 'An independently reviewed event register'],
  evidence: ['Authoritative source registry, formats and reuse rights', 'Exact document versions, identifiers and reviewer decisions'],
  timeline: ['Dated primary records and event resolution rules', 'Publication and first-observed timestamps'],
  relationships: ['Primary evidence for each relationship and its validity period', 'Independently reviewed provenance and counterevidence'],
  forecast: ['A preregistered outcome with resolution date and independent resolver', 'Verified as-of evidence and a defensible baseline'],
  explanation: ['Evidence for competing hypotheses', 'Causal identification strategy; correlation and association are insufficient'],
}
function normalize(text: string): string {
  return text.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim()
}
function words(text: string): string[] {
  return [...new Set(normalize(text).split(' ').filter(term => term.length >= 3 && !STOPWORDS.has(term)))]
}
function hasPhrase(haystack: string, phrase: string): boolean {
  return (' ' + haystack + ' ').includes(' ' + normalize(phrase) + ' ')
}
function classify(question: string): QueryIntent {
  const q = ' ' + normalize(question) + ' '
  if (/\b(will|likely|forecast|predict|prediction|probability|chance|risk)\b/.test(q)) return 'forecast'
  if (/\b(why|cause|caused|influence|motivated|motive|corrupt)\b/.test(q)) return 'explanation'
  if (/\b(related|relationship|relationships|connected|links|network|who regulates|who published)\b/.test(q)) return 'relationships'
  if (/\b(when|timeline|history|changed|change|events|happened)\b/.test(q)) return 'timeline'
  if (/\b(source|sources|document|documents|report|evidence|records|data|published)\b/.test(q)) return 'evidence'
  return 'general'
}
function dayEnd(day: string): number {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return NaN
  const millis = Date.parse(day + 'T23:59:59.999Z')
  return Number.isNaN(millis) || new Date(millis).toISOString().slice(0, 10) !== day ? NaN : millis
}
function score(item: string, topics: string[]): number {
  const text = normalize(item)
  return topics.reduce((total, topic) => total + (text.split(' ').some(term => term.startsWith(topic)) ? 1 : 0), 0)
}
function edgeAvailable(edge: QueryEdge, until: number): boolean {
  if (edge.review_state !== 'verified' || !edge.reviewed_at || !edge.evidence_ids.length) return false
  const observed = [edge.published_at, edge.first_observed_at, edge.recorded_at, edge.reviewed_at, edge.valid_from]
  if (!observed.every(v => Number.isFinite(Date.parse(v)) && Date.parse(v) <= until)) return false
  return edge.valid_to === null || (Number.isFinite(Date.parse(edge.valid_to)) && Date.parse(edge.valid_to) > until)
}
export function searchResearch(question: string, dataset: QueryDataset, asOfDate: string): QueryResult {
  const q = question.trim().slice(0, 500)
  const intent = classify(q)
  const until = dayEnd(asOfDate)
  const base: QueryResult = {
    status: 'empty', intent, query: q, as_of: asOfDate, research_case: null,
    matched_sources: [], matched_observations: [], matched_edges: [], limitations: [], draft: null,
  }
  if (!Number.isFinite(until)) {
    return { ...base, limitations: ['Invalid UTC evidence cutoff. Use YYYY-MM-DD.'] }
  }
  if (!q) return base
  const normalized = normalize(q)
  const ranked = dataset.cases.map(researchCase => {
    const matchedAliases = researchCase.aliases.filter(alias => hasPhrase(normalized, alias))
    return { researchCase, matchedAliases, strength: Math.max(0, ...matchedAliases.map(alias => normalize(alias).length)) }
  }).filter(x => x.strength > 0).sort((a, b) => b.strength - a.strength || a.researchCase.id.localeCompare(b.researchCase.id))
  if (!ranked.length) {
    return { ...base, status: 'uncovered', limitations: [
      'No registered case matches this question. No external source discovery or live search was performed.',
      'A case must be configured and its relevant source records independently reviewed before evidence-backed answers are possible.',
    ], draft: { question: q, intent, source_requirements: SOURCE_REQUIREMENTS[intent] } }
  }
  const researchCase = ranked[0].researchCase
  const aliasTerms = new Set(ranked[0].matchedAliases.flatMap(words))
  const topics = words(q).filter(term => !aliasTerms.has(term))
  const sourceIds = new Set(researchCase.source_ids)
  const observationIds = new Set(researchCase.observation_ids)
  const entityIds = new Set(researchCase.entity_ids)
  const sourceMap = new Map(dataset.sources.map(s => [s.id, s]))
  const readySources = dataset.sources.filter(s => sourceIds.has(s.id) &&
    Number.isFinite(dayEnd(s.verified_at)) && dayEnd(s.verified_at) <= until &&
    Number.isFinite(dayEnd(s.published_at)) && dayEnd(s.published_at) <= until)
  const sourceMatches = readySources.map(s => ({
    record: s, relevance: topics.length ? score([s.title, s.publisher, s.type, s.reliability_note].join(' '), topics) : 1,
  })).filter(s => s.relevance > 0).sort((a, b) =>
    b.relevance - a.relevance || b.record.published_at.localeCompare(a.record.published_at)
  ).slice(0, 10).map(x => x.record)
  const observationMatches = dataset.observations.filter(o => observationIds.has(o.id) &&
    Number.isFinite(dayEnd(o.date)) && dayEnd(o.date) <= until &&
    o.source_ids.length > 0 && o.source_ids.every(id => sourceIds.has(id) && readySources.some(s => s.id === id) && sourceMap.has(id))
  ).map(o => ({
    record: o, relevance: topics.length ? score([o.subject, o.summary, o.event_type].join(' '), topics) : 1,
  })).filter(o => o.relevance > 0).sort((a, b) =>
    b.relevance - a.relevance || b.record.date.localeCompare(a.record.date)
  ).slice(0, 10).map(x => x.record)
  const eligibleEdges = dataset.knowledge_graph.edges.filter(edge =>
    edgeAvailable(edge, until) && edge.evidence_ids.every(id => sourceIds.has(id) && readySources.some(s => s.id === id)) &&
    (entityIds.has(edge.subject_id) || entityIds.has(edge.object_id))
  )
  const replaced = new Set(eligibleEdges.map(e => e.supersedes).filter((id): id is string => Boolean(id)))
  const edges = eligibleEdges.filter(e => !replaced.has(e.edge_id) && (intent === 'relationships' || topics.length === 0 ||
    score([dataset.knowledge_graph.nodes.find(n => n.id === e.subject_id)?.label || '', dataset.knowledge_graph.nodes.find(n => n.id === e.object_id)?.label || '',
      e.scope].join(' '), topics) > 0)).slice(0, 12)
  const found = sourceMatches.length + observationMatches.length + edges.length > 0
  const limitations = [
    'Keyword retrieval over a fixed, curated case registry—not open-web search, autonomous discovery or natural-language reasoning.',
    'Results are excerpts of registered observations, source records and reviewed graph edges, not a newly verified claim or complete answer.',
    'Records are eligible only after their recorded availability/verification dates; the static catalogue cannot establish live source freshness.',
  ]
  if (intent === 'forecast') limitations.unshift('No probability was computed. Prospective forecasts require a locked question, baseline, current reviewed evidence and independent outcome resolution.')
  if (intent === 'explanation') limitations.unshift('The returned records do not establish motives or causation. Competing explanations and causal identification require independent evaluation.')
  if (!found) limitations.unshift('This registered case has no matching evidence available at the selected cutoff. Do not infer that the event or relationship does not exist.')
  return { ...base, status: found ? 'evidence_found' : 'no_relevant_evidence',
    research_case: researchCase, matched_sources: sourceMatches, matched_observations: observationMatches,
    matched_edges: edges, limitations }
}
