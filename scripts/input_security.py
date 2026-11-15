"""Strict intake validation. Passing these checks is not a malware scan."""
import csv
import hashlib
import io
import re
import unicodedata
from urllib.parse import urlsplit

MAX_UPLOAD = 10 * 1024 * 1024


def clean_text(value, limit=500):
    if not isinstance(value, str):
        raise ValueError('Text required')
    value = unicodedata.normalize('NFC', value).strip()
    if not value or len(value) > limit or any(unicodedata.category(c).startswith('C') for c in value):
        raise ValueError('Invalid text length or control characters')
    return value


def source_url(value):
    value = clean_text(value, 2048)
    parsed = urlsplit(value)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Public HTTPS source URL required')
    # This is a citation only. Intake never fetches a submitted URL (SSRF prevention).
    return value


def validate_upload(filename, body):
    if not isinstance(body, bytes) or not 0 < len(body) <= MAX_UPLOAD:
        raise ValueError('Upload must be between 1 byte and 10 MiB')
    name = clean_text(filename, 150)
    if '/' in name or '\\' in name or ':' in name or name.startswith('.'):
        raise ValueError('Unsafe filename')
    extension = name.rsplit('.', 1)[-1].lower()
    if extension == 'pdf':
        if not body.startswith(b'%PDF-') or b'%%EOF' not in body[-2048:]:
            raise ValueError('Invalid PDF signature')
        # Conservatively refuse obvious active PDF content. Obfuscation still requires a malware scanner.
        if re.search(rb'/(?:JavaScript|JS|Launch|EmbeddedFile|OpenAction|AA)\b', body):
            raise ValueError('Active or embedded PDF content rejected')
    elif extension == 'csv':
        text = body.decode('utf-8-sig')
        if '\x00' in text:
            raise ValueError('Binary CSV rejected')
        rows = csv.reader(io.StringIO(text))
        width = None
        for index, row in enumerate(rows):
            if index > 100000 or len(row) > 200:
                raise ValueError('CSV exceeds row/column limits')
            if width is None:
                width = len(row)
            if len(row) != width:
                raise ValueError('Inconsistent CSV columns')
            if any(cell.lstrip().startswith(('=', '+', '-', '@')) for cell in row):
                raise ValueError('Formula-like CSV cells rejected; use plain values')
        if not width:
            raise ValueError('Empty CSV')
    else:
        raise ValueError('Only PDF and UTF-8 CSV are accepted')
    return {'sha256': hashlib.sha256(body).hexdigest(), 'size_bytes': len(body),
            'extension': extension, 'review_state': 'quarantined', 'scan_state': 'not_scanned'}
