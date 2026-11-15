const { test } = require('node:test')
const assert = require('node:assert/strict')
const { validateProvenance } = require('./provenance.cjs')
const valid = { source_url: 'https://example.org/report', published_at: '2026-01-01' }
test('requires real publication date and keeps UTC provenance', () => assert.equal(validateProvenance(valid).published_at, '2026-01-01T00:00:00.000Z'))
for (const published_at of ['2026-02-30', '2999-01-01', 'today', '']) test('rejects date ' + published_at, () => assert.throws(() => validateProvenance({ ...valid, published_at })))
for (const source_url of ['javascript:alert(1)', 'https://user:secret@example.org/', 'https://example.org/\nheader']) test('rejects unsafe provenance URL', () => assert.throws(() => validateProvenance({ ...valid, source_url })))
