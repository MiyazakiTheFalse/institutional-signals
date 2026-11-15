"""Evidence dependency gates. Discovery is never treated as reviewed content."""
from datetime import datetime, timezone
from freshness import source_health


def utc(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('Evidence timestamps need a timezone')
    return dt.astimezone(timezone.utc)


def evaluate(requirements, sources, state, reviewed, now):
    registry = {s['source_id']: s for s in sources}
    results = []
    for requirement in requirements:
        accepted, reasons, groups = [], [], set()
        for route in requirement['routes']:
            sid = route['source_id']
            source, check = registry.get(sid), state.get(sid, {})
            if source is None:
                raise ValueError(f'Unknown dependency source: {sid}')
            health = source_health(checked_at=utc(check['last_success_at']) if check.get('last_success_at') else None,
                                   now=now, target_minutes=source['poll_target_minutes'],
                                   consecutive_failures=check.get('consecutive_failures', 0))
            matches = [r for r in reviewed if r['source_id'] == sid and r['sha256'] == check.get('sha256')
                       and utc(r['reviewed_at']) <= now and utc(r['available_at']) <= now
                       and r['review_state'] == 'verified'
                       and requirement['capability'] in r['capabilities']]
            valid = health['status'] == 'current' and bool(matches)
            manual = [r for r in reviewed if r.get('origin') == 'manual' and r['source_id'] == sid
                      and r['review_state'] == 'verified' and r.get('scan_state') == 'clean'
                      and r.get('scan_sha256') == r['sha256']
                      and utc(r['available_at']) <= now and utc(r['reviewed_at']) <= now < utc(r['valid_until'])
                      and (utc(r['valid_until']) - utc(r['reviewed_at'])).total_seconds() <= min(1440, source['poll_target_minutes'] * 3) * 60
                      and requirement['capability'] in r['capabilities']]
            if manual:
                matches = sorted(manual, key=lambda r: r['reviewed_at'])
                valid = True
            reasons.append({'source_id': sid, 'health': health['status'],
                            'reason': 'accepted' if valid else 'stale_or_unavailable' if health['status'] != 'current'
                            else 'current_content_not_verified_for_requirement'})
            if valid:
                record = matches[-1]
                accepted.append(sid)
                groups.add(record['primary_document_id'])
        met = len(groups) >= requirement.get('min_independent_documents', 1)
        results.append({'id': requirement['id'], 'label': requirement['label'],
                        'essential': requirement.get('essential', True), 'met': met,
                        'accepted_sources': accepted, 'independent_documents': len(groups), 'routes': reasons})
    essential = [r for r in results if r['essential']]
    ready = bool(essential) and all(r['met'] for r in essential)
    return {'evaluated_at': now.isoformat(), 'decision': 'ready_for_inference' if ready else 'hold',
            'can_update_forecast': ready, 'requirements': results,
            'missing_essential': [r['id'] for r in essential if not r['met']]}


def evaluate_cases(cases, sources, state, reviewed, now):
    ids = [c['case_id'] for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate case ID')
    return {c['case_id']: evaluate(c['requirements'], sources, state, reviewed, now) for c in cases}
