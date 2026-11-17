"""Reviewed-event -> dependency gate -> immutable experimental forecast.

Offline batch adapter only. No automatic model training, publicity or inference
from missing publications. Caller supplies versioned historical source state.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from coverage import evaluate
from evidence_journal import canonical, read_journal, replay
from forecast_engine import append_snapshot, baseline_snapshot
from knowledge_graph import utc

def issue(case, requirements, sources, state, reviews, journal, outcomes, as_of,
          *, minimum_outcomes=20, previous=None):
    cutoff = utc(as_of)
    visible = [r for r in reviews if utc(r['available_at']) <= cutoff
               and utc(r['reviewed_at']) <= cutoff]
    gate = evaluate(requirements, sources, state, visible, cutoff)
    if not gate['can_update_forecast']:
        return {'status': 'hold', 'reason': 'essential_source_coverage_or_review_missing',
                'missing_essential': gate['missing_essential'], 'gate': gate}
    allowed = {sid for requirement in gate['requirements'] if requirement['met']
               for sid in requirement['accepted_sources']}
    active = [e for e in replay(journal, as_of) if e['source_id'] in allowed]
    if not active:
        return {'status': 'hold', 'reason': 'no_verified_structured_events'}
    footprint = hashlib.sha256(canonical([e['event_id'] for e in active])).hexdigest()
    if (previous and previous.get('event_footprint') == footprint
            and previous.get('horizon_end') == case['horizon_end']):
        return {'status': 'no_change', 'reason': 'no_new_material_verified_evidence'}
    evidence = [dict(id=e['event_id'], available_at=e['available_at'],
                     reviewed_at=e['verified_at'], review_state='verified') for e in active]
    result = baseline_snapshot(case, gate, outcomes, evidence, as_of,
                               minimum_outcomes=minimum_outcomes,
                               prior_id=previous.get('id') if previous else None)
    if result['status'] == 'hold':
        return result
    result['event_footprint'] = footprint
    essential = [r for r in gate['requirements'] if r['essential']]
    result['source_coverage'] = {'essential_requirements': len(essential),
                                 'met_essential': sum(r['met'] for r in essential)}
    result['change_reason'] = 'new_verified_evidence' if previous else 'initial_verified_forecast'
    result['id'] = hashlib.sha256(canonical({k: v for k, v in result.items() if k != 'id'})).hexdigest()
    return result

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def main():
    parser = argparse.ArgumentParser(description='Offline audited forecast inference (does not publish)')
    for key in ('case', 'requirements', 'sources', 'state', 'reviews',
                'journal', 'outcomes', 'as-of', 'output'):
        parser.add_argument('--' + key, required=True)
    parser.add_argument('--minimum-outcomes', type=int, default=20)
    args = parser.parse_args()
    result = issue(load(args.case), load(args.requirements), load(args.sources),
                   load(args.state), load(args.reviews), read_journal(args.journal),
                   load(args.outcomes), args.as_of, minimum_outcomes=args.minimum_outcomes)
    if result['status'] not in ('hold', 'no_change'):
        append_snapshot(args.output, result)
    print(json.dumps(result, sort_keys=True))

if __name__ == '__main__':
    main()
