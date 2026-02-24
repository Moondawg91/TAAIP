import { apiFetch } from './client'

export async function searchPhonetics(query){
  const qs = new URLSearchParams()
  qs.set('query', query)
  return apiFetch(`/api/phonetics/search?${qs.toString()}`)
}

export async function exportPhoneticsCsv(type){
  const url = type ? `/api/phonetics/export.csv?type=${encodeURIComponent(type)}` : '/api/phonetics/export.csv'
  const res = await fetch((process.env.REACT_APP_API_BASE || 'http://localhost:8000') + url, { headers: {} })
  if(!res.ok) throw new Error('export failed')
  return res.text()
}

export async function phoneticsImportPreview(body){
  return apiFetch('/api/phonetics/import/preview', { method: 'POST', body: JSON.stringify(body), headers: {'Content-Type':'application/json'} })
}

export async function phoneticsImportCommit(body){
  return apiFetch('/api/phonetics/import/commit', { method: 'POST', body: JSON.stringify(body), headers: {'Content-Type':'application/json'} })
}
