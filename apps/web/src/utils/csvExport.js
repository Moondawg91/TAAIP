export function exportToCsv(filename, items = [], headers = []){
  const cols = (headers && headers.length) ? headers : (items.length ? Object.keys(items[0]) : [])
  const rows = items.map(item => cols.map(c => {
    const v = item[c]
    if (v === null || v === undefined) return ''
    const s = typeof v === 'object' ? JSON.stringify(v) : String(v)
    return s.replace(/"/g,'""')
  }))
  const csvLines = []
  csvLines.push(cols.join(','))
  for(const r of rows){
    csvLines.push(r.map(cell => `"${cell}"`).join(','))
  }
  const csv = csvLines.join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', filename)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export default exportToCsv
