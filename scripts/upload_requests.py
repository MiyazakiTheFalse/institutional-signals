"""Explain evidence gaps without inventing documents or requesting unrelated data."""


def requests_for(cases, gates):
    output = []
    for case in cases:
        gate = gates[case['case_id']]
        missing = {r['id'] for r in gate['requirements'] if not r['met'] and r['essential']}
        for requirement in case['requirements']:
            if requirement['id'] not in missing:
                continue
            output.append({'request_id': case['case_id'] + ':' + requirement['id'],
                           'case_id': case['case_id'], 'requirement_id': requirement['id'],
                           'document': requirement['label'],
                           'why': 'Required before this case can issue or update a forecast.',
                           'capability': requirement['capability'],
                           'source_ids': [r['source_id'] for r in requirement['routes']],
                           'accepted_formats': ['pdf', 'csv'] if 'dataset' in requirement['capability'] else ['pdf'],
                           'instructions': 'Download the original from its publisher. Include the original source URL and publication date. Do not include unrelated personal information.',
                           'max_size_bytes': 10485760,
                           'status': 'awaiting_reviewed_current_content'})
    return output
