"""Run gated baseline inference for explicitly preregistered cases only."""
import argparse
import gzip
import json
from datetime import datetime, timezone
from pathlib import Path
from collect import LocalStore, R2Store, packed
from forecast_engine import baseline_snapshot
ROOT=Path(__file__).resolve().parents[1]

def run(store, cases, outcomes, reviewed, as_of):
    raw=store.get('status/case-readiness.json.gz')
    gates=json.loads(gzip.decompress(raw)) if raw else {}
    results=[]
    for case in cases:
        gate=gates.get(case['case_id'], {'can_update_forecast':False})
        eligible=[r for r in outcomes if r['case_family']==case['case_family']]
        evidence=[r for r in reviewed if r['id'] in case['evidence_ids']]
        if len(evidence) != len(set(case['evidence_ids'])):
            result={'status':'hold','reason':'missing_registered_evidence'}
        else:
            result=baseline_snapshot(case,gate,eligible,evidence,as_of)
        if result['status'] != 'hold': store.put('forecasts/'+result['id']+'.json.gz',packed(result),immutable=True)
        results.append({'case_id':case['case_id'],**result})
    report={'as_of':as_of,'cases':results,'notice':'No registered targets means no forecasts. Experimental baseline only.'}
    store.put('status/forecast-readiness.json.gz',packed(report))
    return report

def main():
    p=argparse.ArgumentParser(); p.add_argument('--store',choices=['local','r2'],default='local'); p.add_argument('--local-dir',default=str(ROOT/'.collection')); args=p.parse_args()
    store=R2Store() if args.store=='r2' else LocalStore(args.local_dir)
    cases=json.loads((ROOT/'config/forecast_cases.json').read_text())
    outcomes=json.loads((ROOT/'data/resolved_outcomes.json').read_text())
    reviewed=json.loads((ROOT/'data/reviewed_evidence.json').read_text())
    if args.store=='r2': reviewed.extend(store.reviewed_manual())
    report=run(store,cases,outcomes,reviewed,datetime.now(timezone.utc).isoformat())
    print(json.dumps({'registered_cases':len(report['cases']),'status':[r['status'] for r in report['cases']]}))
if __name__=='__main__': main()
