import React, { useState } from 'react'
import { Box, Button, TextField, Typography, Table, TableBody, TableCell, TableHead, TableRow, Paper } from '@mui/material'
import { searchPhonetics, exportPhoneticsCsv, phoneticsImportPreview, phoneticsImportCommit } from '../../api/phoneticsClient'

export default function PhoneticsPage(){
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [csvText, setCsvText] = useState('')
  const [preview, setPreview] = useState(null)
  const [errors, setErrors] = useState([])

  const doSearch = async ()=>{
    try{
      const r = await searchPhonetics(query)
      setResults(r.results || [])
    }catch(e){ setResults([]) }
  }

  const doPreview = async ()=>{
    try{
      const r = await phoneticsImportPreview({ csv_text: csvText })
      setPreview(r.preview)
      setErrors(r.errors)
    }catch(e){ setPreview(null); setErrors([{error: e.message||'preview failed'}]) }
  }

  const doCommit = async ()=>{
    try{
      const r = await phoneticsImportCommit({ csv_text: csvText })
      setPreview(null)
      setErrors([])
      alert(`Inserted ${r.inserted} rows`) 
    }catch(e){ alert('commit failed') }
  }

  const doExport = async ()=>{
    try{
      const csv = await exportPhoneticsCsv()
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'phonetics.csv'
      a.click()
      URL.revokeObjectURL(url)
    }catch(e){ alert('export failed') }
  }

  return (
    <Box sx={{ p:2 }}>
      <Typography variant="h5" sx={{ mb:2 }}>Phonetics</Typography>
      <Box sx={{ display:'flex', gap:2, mb:2 }}>
        <TextField size="small" label="Search" value={query} onChange={(e)=>setQuery(e.target.value)} />
        <Button variant="contained" onClick={doSearch}>Search</Button>
        <Button variant="outlined" onClick={doExport}>Export CSV</Button>
      </Box>

      <Paper sx={{ bgcolor:'background.paper', p:1, borderRadius:1 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Term</TableCell>
              <TableCell>Phonetic</TableCell>
              <TableCell>Type</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {results.map(r=> (
              <TableRow key={r.id}>
                <TableCell>{r.term}</TableCell>
                <TableCell>{r.phonetic}</TableCell>
                <TableCell>{r.type}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Box sx={{ mt:3 }}>
        <Typography variant="h6">Import CSV</Typography>
        <Typography variant="caption">Expect columns: term, phonetic, type (optional)</Typography>
        <TextField multiline rows={8} fullWidth value={csvText} onChange={(e)=>setCsvText(e.target.value)} sx={{ mt:1, bgcolor:'background.default', borderRadius:1 }} />
        <Box sx={{ display:'flex', gap:2, mt:1 }}>
          <Button variant="contained" onClick={doPreview}>Preview</Button>
          <Button variant="contained" color="success" onClick={doCommit}>Commit</Button>
        </Box>
        {preview && (
          <Paper sx={{ mt:2, p:1 }}>
            <Typography variant="subtitle2">Preview ({preview.length} rows)</Typography>
            <Table size="small">
              <TableHead>
                <TableRow><TableCell>Term</TableCell><TableCell>Phonetic</TableCell><TableCell>Type</TableCell></TableRow>
              </TableHead>
              <TableBody>
                {preview.map(p=> (
                  <TableRow key={p.row}><TableCell>{p.term}</TableCell><TableCell>{p.phonetic}</TableCell><TableCell>{p.type}</TableCell></TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        )}
      </Box>
    </Box>
  )
}
