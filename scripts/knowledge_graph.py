"""Versioned institutional relationships with conservative as-of replay."""
from datetime import datetime, timezone

NODE_TYPES = {'institution', 'public_body', 'formal_role', 'decision', 'document', 'claim', 'event', 'forecast', 'source'}
PREDICATES = {'oversees', 'regulates', 'funds', 'owns', 'contracts_with', 'appoints', 'has_statutory_power_over', 'issued', 'cites', 'claims', 'contradicts', 'depends_on', 'can_approve', 'can_block', 'participated_in', 'same_underlying_source_as'}

def utc(value):
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.tzinfo is None or d.utcoffset().total_seconds() != 0:
        raise ValueError('UTC timestamp required')
    return d.astimezone(timezone.utc)

def validate(graph, evidence_ids):
    nodes, edges = graph['nodes'], graph['edges']
    ids = {n['id'] for n in nodes}
    if len(ids) != len(nodes) or any(n['type'] not in NODE_TYPES or not n.get('label') for n in nodes):
        raise ValueError('Invalid or duplicate graph nodes')
    seen = {}
    successors = set()
    for e in edges:
        if e['edge_id'] in seen or e['subject_id'] not in ids or e['object_id'] not in ids or e['predicate'] not in PREDICATES:
            raise ValueError('Invalid graph edge')
        if not e['evidence_ids'] or not set(e['evidence_ids']).issubset(evidence_ids):
            raise ValueError('Every edge needs known source provenance')
        if e['assertion_type'] not in {'documented_fact', 'attributed_claim', 'hypothesis', 'disputed'} or e['review_state'] not in {'candidate', 'verified', 'rejected'}:
            raise ValueError('Invalid assertion/review state')
        for field in ('scope', 'limitations', 'independence_group'):
            if not isinstance(e.get(field), str) or not e[field].strip(): raise ValueError('Missing ' + field)
        dates = {key: utc(e[key]) for key in ('valid_from', 'published_at', 'first_observed_at', 'recorded_at')}
        if dates['recorded_at'] < max(dates['published_at'], dates['first_observed_at']): raise ValueError('Recorded before available')
        if e.get('valid_to') and utc(e['valid_to']) <= dates['valid_from']: raise ValueError('Invalid validity window')
        if e['review_state'] == 'verified' and utc(e['reviewed_at']) < dates['recorded_at']: raise ValueError('Review precedes record')
        previous = e.get('supersedes')
        if previous:
            if previous not in seen or previous in successors or dates['recorded_at'] <= utc(seen[previous]['recorded_at']): raise ValueError('Invalid correction lineage')
            successors.add(previous)
        seen[e['edge_id']] = e
    return graph

def replay(graph, as_of, *, verified_only=True):
    """Availability, review and validity are distinct; corrections apply prospectively."""
    cutoff = utc(as_of)
    visible = [e for e in graph['edges'] if all(utc(e[k]) <= cutoff for k in ('published_at', 'first_observed_at', 'recorded_at'))]
    if verified_only:
        visible = [e for e in visible if e['review_state'] == 'verified' and utc(e['reviewed_at']) <= cutoff]
    superseded = {e['supersedes'] for e in visible if e.get('supersedes')}
    return [e for e in visible if e['edge_id'] not in superseded and utc(e['valid_from']) <= cutoff and (not e.get('valid_to') or cutoff < utc(e['valid_to']))]

def impacted_decisions(graph, evidence_ids, as_of):
    """Bounded dependency traversal, retaining the documentary paths for audit."""
    edges = replay(graph, as_of)
    reached = {e['subject_id'] for e in edges if set(e['evidence_ids']) & set(evidence_ids)} | {e['object_id'] for e in edges if set(e['evidence_ids']) & set(evidence_ids)}
    for _ in range(len(graph['nodes'])):
        next_ids = {e['subject_id'] for e in edges if e['predicate'] == 'depends_on' and e['object_id'] in reached}
        if next_ids.issubset(reached): break
        reached |= next_ids
    return sorted(n['id'] for n in graph['nodes'] if n['type'] == 'decision' and n['id'] in reached)

def features(graph, decision_id, as_of):
    edges = [e for e in replay(graph, as_of) if decision_id in (e['subject_id'], e['object_id'])]
    return {'as_of': as_of, 'decision_id': decision_id,
            'documented_approvers': len({e['subject_id'] for e in edges if e['predicate'] == 'can_approve' and e['assertion_type'] == 'documented_fact'}),
            'documented_blockers': len({e['subject_id'] for e in edges if e['predicate'] == 'can_block' and e['assertion_type'] == 'documented_fact'}),
            'independent_source_groups': len({e['independence_group'] for e in edges}),
            'edge_ids': sorted(e['edge_id'] for e in edges),
            'notice': 'Descriptive graph features; predictive usefulness has not been established.'}
