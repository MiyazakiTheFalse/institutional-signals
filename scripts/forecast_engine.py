"""First-pass baseline inference, append-only snapshots and outcome evaluation.

No model is trained or public forecast issued merely by importing this module.
"""
import hashlib
import json
import math
import re
from pathlib import Path
from knowledge_graph import utc
from probability import beta_binomial_base_rate, brier_score

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def eligible_outcomes(rows, as_of):
    cutoff = utc(as_of)
    groups, selected = set(), []
    for row in sorted(rows, key=lambda r: (r['resolved_at'], r['id'])):
        if type(row['outcome']) is not int or row['outcome'] not in (0, 1): raise ValueError('Binary outcomes required')
        if utc(row['resolved_at']) > cutoff or utc(row['available_at']) > cutoff: continue
        if row['independence_group'] in groups: continue
        groups.add(row['independence_group']); selected.append(row)
    return selected

def baseline_snapshot(case, gate, outcomes, evidence, as_of, *, minimum_outcomes=20, prior_id=None):
    cutoff = utc(as_of)
    if utc(case['horizon_end']) <= cutoff: raise ValueError('Forecast horizon must be in the future')
    for key in ('case_id', 'question', 'resolution_rule', 'model_version'):
        if not case.get(key): raise ValueError('Missing case ' + key)
    if not gate['can_update_forecast'] or utc(gate['evaluated_at']) > cutoff or (cutoff - utc(gate['evaluated_at'])).total_seconds() > 90 * 60:
        return {'status': 'hold', 'reason': 'missing_or_stale_verified_evidence'}
    if not evidence or any(e['review_state'] != 'verified' or utc(e['available_at']) > cutoff or utc(e['reviewed_at']) > cutoff for e in evidence):
        raise ValueError('Evidence was not verified and available as of inference')
    selected = eligible_outcomes(outcomes, as_of)
    if len(selected) < minimum_outcomes: return {'status': 'hold', 'reason': 'insufficient_independent_outcomes', 'outcome_count': len(selected)}
    p = beta_binomial_base_rate(events=sum(r['outcome'] for r in selected), observations=len(selected))
    snapshot = {**case, 'as_of': as_of, 'issued_at': as_of, 'status': 'experimental_baseline', 'probability': p,
                'baseline_probability': p, 'prior_forecast_id': prior_id, 'outcome_count': len(selected),
                'evidence_ids': sorted(e['id'] for e in evidence), 'training_outcome_ids': [r['id'] for r in selected],
                'feature_snapshot_hash': hashlib.sha256(canonical(evidence)).hexdigest(),
                'method': 'Beta(1,1) smoothed base rate; exchangeable binary outcomes only'}
    snapshot['id'] = hashlib.sha256(canonical(snapshot)).hexdigest()
    return snapshot

def append_snapshot(directory, snapshot):
    """Exclusive creation prevents silently replacing an issued forecast."""
    if snapshot.get('status') == 'hold': raise ValueError('Hold is not an issued forecast')
    identifier = snapshot['id']
    payload = {k: v for k, v in snapshot.items() if k != 'id'}
    if not re.fullmatch('[0-9a-f]{64}', identifier) or hashlib.sha256(canonical(payload)).hexdigest() != identifier: raise ValueError('Snapshot identity mismatch')
    root = Path(directory); root.mkdir(parents=True, exist_ok=True)
    target = root / (identifier + '.json')
    with target.open('xb') as f: f.write(canonical(snapshot))
    return target

def evaluate_predictions(rows):
    if not rows: return {'status': 'insufficient_outcomes', 'count': 0}
    if len({r['independence_group'] for r in rows}) != len(rows): raise ValueError('Correlated outcomes must be grouped before scoring')
    for r in rows:
        if utc(r['as_of']) >= utc(r['resolved_at']): raise ValueError('Outcome leakage')
    pairs = [(r['probability'], r['outcome']) for r in rows]
    base = [(r['baseline_probability'], r['outcome']) for r in rows]
    score, baseline = brier_score(pairs), brier_score(base)
    eps = 1e-15
    loss = -sum(y * math.log(max(eps, p)) + (1-y) * math.log(max(eps, 1-p)) for p,y in pairs) / len(pairs)
    return {'count': len(rows), 'brier': score, 'baseline_brier': baseline, 'log_loss': loss,
            'promotion_eligible': len(rows) >= 100 and score < baseline,
            'notice': 'Eligibility is a screening check, not automatic model promotion. Segment and calibration review are required.'}
