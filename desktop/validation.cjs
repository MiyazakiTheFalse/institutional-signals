const { TextDecoder } = require('node:util')
function validateFile(name, body, allowed) {
  if (!Buffer.isBuffer(body) || !body.length || body.length > 10 * 1024 * 1024) throw new Error('File must be 1 byte to 10 MiB')
  if (name.length > 150 || /[\\/:\x00-\x1f\x7f]/.test(name) || name.startsWith('.')) throw new Error('Invalid filename')
  const ext = name.split('.').pop().toLowerCase()
  if (!['pdf', 'csv'].includes(ext) || !allowed.includes(ext)) throw new Error('Unsupported file type')
  if (ext === 'pdf') {
    if (!body.subarray(0, 5).equals(Buffer.from('%PDF-')) || !body.subarray(-2048).includes(Buffer.from('%%EOF'))) throw new Error('Invalid PDF')
    if (/\/(JavaScript|JS|Launch|EmbeddedFile|OpenAction|AA)\b/.test(body.toString('latin1'))) throw new Error('Active PDF content rejected')
  } else {
    const text = new TextDecoder('utf-8', { fatal: true }).decode(body)
    if (text.includes('\0') || text.split('\n').length > 100001) throw new Error('Invalid CSV')
    // Real CSV parser handles quoted/newline cells before checking formulas.
    const rows = require('csv-parse/sync').parse(text, { bom: true, max_record_size: 100000 })
    if (!rows.length || rows.some(r => r.length > 200 || r.some(c => /^[=+\-@]/.test(c.trimStart())))) throw new Error('CSV contains unsafe cells or too many columns')
  }
}
module.exports = { validateFile }
