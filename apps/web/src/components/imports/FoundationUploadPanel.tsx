import React, { useState } from 'react'
import { Box, Paper, Typography, Button, Table, TableHead, TableRow, TableCell, TableBody, FormControl, InputLabel, Select, MenuItem, TextField } from '@mui/material'
import { previewFoundationImport, commitFoundationImport } from '../../api/client'

export default function FoundationUploadPanel(){
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<any>(null)
  const [status, setStatus] = useState('')
  const [mode, setMode] = useState<'append'|'replace'>('append')
  const [datasetKey, setDatasetKey] = useState<string>('school_program_fact')
  const [mapping, setMapping] = useState<Record<string,string>>({})

  async function onFileChange(e:any){
    const f = e.target.files && e.target.files[0]
    setFile(f)
    setPreview(null)
    setStatus('')
  }

  async function doPreview(){
    if(!file) return
    const fd = new FormData()
    fd.append('file', file)
    fd.append('dataset_key', datasetKey)
    // include mapping (optional) so UI can show what will be applied
    try{ fd.append('mapping', JSON.stringify(mapping)) }catch(e){}
    setStatus('previewing')
    try{
      const res = await previewFoundationImport(fd)
      // expected: { detected_columns:[], missing_required:[], sample:[], row_count: N }
      setPreview(res || {})
      // compute suggested mapping when preview returns detected columns
      if(res && res.detected_columns){
        const sugg = suggestMapping(datasetKey, res.detected_columns || [])
        setMapping(sugg)
      }
      setStatus('previewed')
    }catch(e){ setStatus('preview failed'); console.error(e) }
  }

  async function doCommit(){
    if(!file) return
    const fd = new FormData()
    fd.append('file', file)
    fd.append('mode', mode)
    fd.append('dataset_key', datasetKey)
    try{ fd.append('mapping', JSON.stringify(mapping)) }catch(e){}
    setStatus('committing')
    try{
      const res = await commitFoundationImport(fd)
      setStatus(`committed: ${res.inserted||0}`)
      // refresh preview to show new state
      setPreview(null)
    }catch(e){ setStatus('commit failed'); console.error(e) }
  }

  const sampleRows = (preview && (preview.sample || preview.sample_rows || [])) || []
  const detected = (preview && preview.detected_columns) || []
  const missing = (preview && preview.missing_required) || []
  const rowCount = (preview && (preview.row_count || preview.rows_count)) || null

  return (
    <Paper sx={{ p:2, mb:2, bgcolor:'background.paper', borderRadius:'4px' }}>
      <Typography variant="h6">Foundation Datasets (420T)</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary' }}>Upload foundation CSVs (school program, enlistments, MI ZIPs). Preview shows detected columns, sample rows, and missing required fields.</Typography>

      <Box sx={{ mt:2 }}>
        <Typography variant="body2">Foundation dataset uploads are now handled by the Data Hub imports workflow. Please use the centralized Data Hub imports page to upload foundation CSVs.</Typography>
        <Box sx={{ mt:2 }}>
          <Button variant="contained" onClick={()=>{ window.location.href = '/data-hub/imports' }}>Open Data Hub Imports</Button>
        </Box>
      </Box>

      {status && <Typography variant="caption" sx={{ display:'block', mt:1 }}>{status}</Typography>}

      {preview && (
        <Box sx={{ mt:2 }}>
          <Typography variant="subtitle2">Preview</Typography>
          <Typography variant="caption" sx={{ display:'block', color:'text.secondary' }}>Detected columns: {detected.join(', ') || '(none)'}</Typography>
          {missing.length>0 && (
            <Typography variant="caption" sx={{ display:'block', color:'warning.main', mt:0.5 }}>Missing required columns: {missing.join(', ')}</Typography>
          )}
          {rowCount !== null && (
            <Typography variant="caption" sx={{ display:'block', color:'text.secondary', mt:0.5 }}>Rows: {rowCount}</Typography>
          )}

          {sampleRows.length>0 ? (
            <Table size="small" sx={{ mt:1 }}>
              <TableHead>
                <TableRow>
                  {Object.keys(sampleRows[0]).map(c => <TableCell key={c}>{c}</TableCell>)}
                </TableRow>
              </TableHead>
              <TableBody>
                {sampleRows.slice(0,5).map((r:any, i:number) => (
                  <TableRow key={i}>
                    {Object.keys(sampleRows[0]).map((c)=> <TableCell key={c}>{String(r[c] ?? '')}</TableCell>)}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>No sample rows available.</Typography>
          )}

          {/* Mapping suggestions UI */}
          {detected.length>0 && (
            <Box sx={{ mt:2 }}>
              <Typography variant="subtitle2">Suggested Mappings</Typography>
              <Typography variant="caption" sx={{ display:'block', color:'text.secondary' }}>Adjust mapping from source columns to dataset required columns before committing.</Typography>
              <Table size="small" sx={{ mt:1 }}>
                <TableHead>
                  <TableRow>
                    <TableCell>Required Field</TableCell>
                    <TableCell>Suggested Source Column</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {requiredFieldsFor(datasetKey).map((req) => (
                    <TableRow key={req}>
                      <TableCell>{req}</TableCell>
                      <TableCell>
                        <FormControl size="small" fullWidth>
                          <Select value={mapping[req] || ''} onChange={(e)=>setMapping(Object.assign({}, mapping, {[req]: e.target.value as string}))}>
                            <MenuItem value={''}>(none)</MenuItem>
                            {detected.map((d:string)=> <MenuItem key={d} value={d}>{d}</MenuItem>)}
                          </Select>
                        </FormControl>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          )}
        </Box>
      )}
    </Paper>
  )
}

// simple heuristics for required fields per dataset (kept client-side for UX)
function requiredFieldsFor(datasetKey:string){
  const map:any = {
    'school_program_fact': ['bde','bn','co','rsid_prefix','population','available'],
    'mi_zip_fact': ['zip5','market_category','army_potential','dod_potential','potential_remaining'],
    'mi_cbsa_fact': ['cbsa_code','market_category','potential_remaining'],
    'mi_mission_category_ref': ['mission_category','education_tier'],
    'mi_enlistments_bde': ['bde','enlistments'],
    'mi_enlistments_bn': ['rsid_prefix','enlistments']
  }
  return map[datasetKey] || []
}

function normalizeColName(s:any){
  if(!s) return ''
  return String(s).toLowerCase().replace(/[^a-z0-9]/g,'')
}

function suggestMapping(datasetKey:string, detected:string[]){
  const required = requiredFieldsFor(datasetKey)
  const detNorm = (detected||[]).map(d=>({raw:d, norm:normalizeColName(d)}))
  const out:any = {}
  required.forEach((r:string)=>{
    const rnorm = normalizeColName(r)
    // exact match
    let found = detNorm.find(d=>d.norm === rnorm)
    if(!found){
      // substring/synonym
      found = detNorm.find(d=>d.norm.includes(rnorm) || rnorm.includes(d.norm))
    }
    if(!found){
      // fuzzy via levenshtein distance
      let best:any = null
      let bestScore = Infinity
      detNorm.forEach(d=>{
        const score = levenshteinDistance(rnorm, d.norm)
        if(score < bestScore){ bestScore = score; best = d }
      })
      // accept if reasonably close (distance less than a fraction)
      if(best && bestScore <= Math.max(1, Math.floor(rnorm.length * 0.35))){
        found = best
      }
    }
    if(!found){
      // soundex-like: compare initial consonant clusters
      const sreq = soundex(rnorm)
      found = detNorm.find(d=>soundex(d.norm) === sreq)
    }
    if(!found){
      // handle zip vs zip5
      if(rnorm === 'zip5') found = detNorm.find(d=>d.norm.includes('zip'))
    }
    out[r] = found ? found.raw : ''
  })
  return out
}

function levenshteinDistance(a:string, b:string){
  const m = a.length, n = b.length
  const dp = Array.from({length: m+1}, ()=> new Array(n+1).fill(0))
  for(let i=0;i<=m;i++) dp[i][0] = i
  for(let j=0;j<=n;j++) dp[0][j] = j
  for(let i=1;i<=m;i++){
    for(let j=1;j<=n;j++){
      const cost = a[i-1] === b[j-1] ? 0 : 1
      dp[i][j] = Math.min(dp[i-1][j] + 1, dp[i][j-1] + 1, dp[i-1][j-1] + cost)
    }
  }
  return dp[m][n]
}

function soundex(s:string){
  if(!s) return ''
  // simple soundex-ish: keep first char + map consonant groups
  const map:any = {b:1,f:1,p:1,v:1, c:2,g:2,j:2,k:2,q:2,s:2,x:2,z:2, d:3,t:3, l:4, m:5,n:5, r:6}
  const first = s[0] || ''
  let prev = map[first] || 0
  let out = first
  for(let i=1;i<s.length && out.length<4;i++){
    const ch = s[i]
    const code = map[ch] || 0
    if(code !== prev){ if(code !== 0) out += String(code); prev = code }
  }
  return out.padEnd(4,'0').slice(0,4)
}
