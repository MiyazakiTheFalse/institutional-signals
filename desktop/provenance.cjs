function validateProvenance(value, now = new Date()) {
  if (!value || typeof value !== 'object') throw new Error('Provenance is required')
  const { source_url, published_at } = value
  if (typeof source_url !== 'string' || source_url.length > 2000 || /[\x00-\x20\x7f]/.test(source_url)) throw new Error('Invalid publisher URL')
  const url = new URL(source_url)
  if (url.protocol !== 'https:' || url.username || url.password) throw new Error('Use an HTTPS publisher URL')
  if (typeof published_at !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(published_at)) throw new Error('Publication date is required')
  const date = new Date(published_at + 'T00:00:00Z')
  if (!Number.isFinite(date.getTime()) || date.toISOString().slice(0, 10) !== published_at || date > now) throw new Error('Invalid or future publication date')
  return { source_url: url.href, published_at: date.toISOString() }
}
module.exports = { validateProvenance }
