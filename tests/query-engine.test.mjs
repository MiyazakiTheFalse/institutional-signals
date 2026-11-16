import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { searchResearch } from '../src/queryEngine.ts'

const data = JSON.parse(readFileSync(new URL('../public/data/dashboard.json', import.meta.url), 'utf8'))
const corpus = {
  cases: data.query_cases,
  sources: data.sources,
  observations: data.observations,
  knowledge_graph: data.knowledge_graph,
}
const current = '2026-11-16'

test('existing registered Ofwat question returns only source-backed records', () => {
  const result = searchResearch('What did Ofwat publish about operational performance?', corpus, current)
  assert.equal(result.status, 'evidence_found')
  assert.equal(result.research_case?.id, 'uk-water-thames')
  assert.ok(result.matched_sources.some(s => s.id === 'OFWAT-2026'))
  assert.ok(result.matched_observations.some(o => o.id === 'OBS-003'))
  assert.ok(result.matched_observations.every(o => o.source_ids.every(id => corpus.sources.some(s => s.id === id))))
  assert.ok(result.limitations.some(x => x.includes('Keyword retrieval')))
})

test('unregistered domain cannot borrow evidence from an unrelated case', () => {
  const result = searchResearch('Which university will increase admissions?', corpus, current)
  assert.equal(result.status, 'uncovered')
  assert.equal(result.research_case, null)
  assert.equal(result.matched_sources.length, 0)
  assert.equal(result.matched_observations.length, 0)
  assert.equal(result.matched_edges.length, 0)
  assert.equal(result.draft?.intent, 'forecast')
  assert.ok(result.draft?.source_requirements.length)
})

test('unsupported topic inside a known case does not fabricate matches', () => {
  const result = searchResearch('Thames Water hypothetical dragons', corpus, current)
  assert.equal(result.status, 'no_relevant_evidence')
  assert.equal(result.matched_sources.length, 0)
  assert.equal(result.matched_observations.length, 0)
  assert.equal(result.matched_edges.length, 0)
})

test('historical cutoff hides reviewed graph edges and not-yet-verified source records', () => {
  const early = searchResearch('What about Thames Water?', corpus, '2026-11-14')
  assert.equal(early.matched_sources.length, 0)
  assert.equal(early.matched_observations.length, 0)
  assert.equal(early.matched_edges.length, 0)
  const priorReview = searchResearch('What about Thames Water?', corpus, '2026-11-15')
  assert.equal(priorReview.matched_edges.length, 0)
  const later = searchResearch('What about Thames Water?', corpus, current)
  assert.equal(later.matched_edges.length, 4)
  assert.ok(later.matched_edges.every(e => e.review_state === 'verified'))
})

test('forecast query never generates probabilities or confident predictions', () => {
  const result = searchResearch('Will Thames Water receive court approval?', corpus, current)
  assert.equal(result.intent, 'forecast')
  assert.ok(result.limitations.some(x => x.includes('No probability was computed')))
  assert.equal('probability' in result, false)
})

test('causal question is flagged as requiring independent analysis', () => {
  const result = searchResearch('Why did Ofwat intervene?', corpus, current)
  assert.equal(result.intent, 'explanation')
  assert.ok(result.limitations.some(x => x.includes('causation')))
})

test('same engine supports a second independent case without code modifications', () => {
  const metro = {
    id: 'metro-transit',
    title: 'Metro Transit service policy',
    summary: 'Synthetic case for testing only.',
    geography: 'Fictional region',
    domain: 'transport',
    aliases: ['metro transit'],
    topics: ['operations'],
    readiness: 'research_only',
    source_ids: ['MT-001'],
    observation_ids: ['MT-OBS'],
    entity_ids: [],
  }
  const sources = [...corpus.sources, {
    id: 'MT-001', title: 'Service announcement', publisher: 'Metro Transit',
    published_at: '2026-11-12', verified_at: '2026-11-13',
    type: 'company_statement', reliability_note: 'Test source only.',
    url: 'https://example.org/metro',
  }]
  const observations = [...corpus.observations, {
    id: 'MT-OBS', date: '2026-11-12', subject: 'Metro Transit',
    summary: 'Metro Transit announced a synthetic service change.',
    event_type: 'announcement', source_ids: ['MT-001'], status: 'statement',
  }]
  const expanded = { ...corpus, cases: [...corpus.cases, metro], sources, observations }
  const result = searchResearch('What did Metro Transit announce?', expanded, current)
  assert.equal(result.research_case?.id, 'metro-transit')
  assert.ok(result.matched_sources.some(s => s.id === 'MT-001'))
  assert.ok(result.matched_observations.some(o => o.id === 'MT-OBS'))
  assert.ok(result.matched_sources.every(s => s.id === 'MT-001'))
  assert.ok(result.matched_observations.every(o => o.id === 'MT-OBS'))
  const early = searchResearch('Metro Transit announce', expanded, '2026-11-12')
  assert.equal(early.matched_sources.length, 0)
  assert.equal(early.matched_observations.length, 0)
})

test('invalid or empty queries return no evidence, not a fabricated answer', () => {
  const empty = searchResearch('   ', corpus, current)
  assert.equal(empty.status, 'empty')
  assert.equal(empty.matched_sources.length, 0)
  const badDate = searchResearch('Ofwat', corpus, '2026-02-30')
  assert.equal(badDate.status, 'empty')
  assert.ok(badDate.limitations.some(x => x.includes('Invalid UTC')))
})

test('aliased terms are matched on word boundaries, not accidental substrings', () => {
  const unrelated = searchResearch('Who reports on the watermelons?', corpus, current)
  assert.equal(unrelated.status, 'uncovered')
})
