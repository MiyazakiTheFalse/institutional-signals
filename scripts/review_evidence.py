"""Trusted operator promotion of scanned, manually verified evidence.

This command requires bucket credentials. End-user invitation keys cannot invoke it.
"""
import argparse
import gzip
import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collect import R2Store
from knowledge_graph import utc
ROOT=Path(__file__).resolve().parents[1]

def reviewed_record(manifest, scan, requirement, source, reviewer, primary_document_id, now):
    if scan['scan_state'] != 'clean' or scan['sha256'] != manifest['sha256']: raise ValueError('A clean scan of the exact content is required')
    if utc(scan['scanned_at']) > now or (now-utc(scan['scanned_at'])).total_seconds() > 86400: raise ValueError('A recent scan is required')
    if utc(manifest['published_at']) > now or utc(manifest['received_at']) > now: raise ValueError('Future evidence refused')
    if source['source_id'] not in [r['source_id'] for r in requirement['routes']]: raise ValueError('Source does not satisfy this requirement')
    if not reviewer.strip() or not primary_document_id.strip(): raise ValueError('Reviewer and underlying document identity required')
    return {'id':manifest['id'], 'source_id':source['source_id'], 'sha256':manifest['sha256'], 'review_state':'verified',
            'reviewed_at':now.isoformat(), 'available_at':manifest['received_at'], 'published_at':manifest['published_at'],
            'primary_document_id':primary_document_id, 'capabilities':[requirement['capability']], 'reviewer':reviewer,
            'origin':'manual', 'scan_state':'clean', 'scan_sha256':scan['sha256'],
            'valid_until':(now+timedelta(minutes=min(1440, source['poll_target_minutes']*3))).isoformat(),
            'notice':'Human verification; manual freshness expires and requires revalidation.'}

def main():
    p=argparse.ArgumentParser()
    for name in ('owner','submission','scan-key','source','reviewer','primary-document-id'): p.add_argument('--'+name,required=True)
    p.add_argument('--confirm-content-verified',action='store_true',required=True)
    args=p.parse_args()
    if not re.fullmatch('[a-zA-Z0-9_-]{1,64}',args.owner) or not re.fullmatch('[0-9a-f-]{36}',args.submission): raise ValueError('Invalid identity')
    prefix=f'{args.owner}/{args.submission}'
    if not re.fullmatch(r'scans/'+re.escape(prefix)+r'/[0-9a-f]{64}\.json\.gz',args.scan_key): raise ValueError('Invalid scan reference')
    store=R2Store(); manifest=json.loads(store.get('submissions/'+prefix+'/manifest.json'))
    scan=json.loads(gzip.decompress(store.get(args.scan_key)))
    cases=json.loads((ROOT/'config/case_dependencies.json').read_text())
    requirement=next(r for c in cases for r in c['requirements'] if c['case_id']+':'+r['id']==manifest['request_id'])
    sources=json.loads((ROOT/'config/collection.json').read_text())
    source=next(s for s in sources if s['source_id']==args.source)
    record=reviewed_record(manifest,scan,requirement,source,args.reviewer,args.primary_document_id,datetime.now(timezone.utc))
    record['scan_key']=args.scan_key
    encoded=json.dumps(record,sort_keys=True).encode(); key=hashlib.sha256(encoded).hexdigest()
    store.put('reviewed/manual/'+key+'.json.gz',gzip.compress(encoded,mtime=0),immutable=True)
    print(json.dumps({'review_record':key,'valid_until':record['valid_until']}))

if __name__=='__main__': main()
