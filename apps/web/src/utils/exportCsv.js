function escapeCell(v){
  if(v === null || v === undefined) return ''
  const s = typeof v === 'object' ? JSON.stringify(v) : String(v)
  if(/[",\n\r,]/.test(s)){
    return '"' + s.replace(/"/g,'""') + '"'
  }
  return s
}

function normalizeColumns(columns, rows){
  if(!columns || columns.length === 0){
    if(rows && rows.length) return Object.keys(rows[0]).map(k=>({ key:k, label:k }))
    return []
  }
  // columns can be array of strings or {key,label}
  return columns.map(c => typeof c === 'string' ? { key: c, label: c } : { key: c.key, label: c.label || c.key })
}

export function exportToCsv(filename, rows = [], columns = []){
  const cols = normalizeColumns(columns, rows)
  const headerLine = cols.length ? cols.map(c => escapeCell(c.label)).join(',') : ''
  const lines = []
  if(headerLine) lines.push(headerLine)
  for(const r of (rows || [])){
    const row = cols.length ? cols.map(c => escapeCell(r[c.key])) : Object.keys(r).map(k=>escapeCell(r[k]))
    lines.push(row.join(','))
  }

  const csv = lines.join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.style.visibility = 'hidden'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export default exportToCsv
