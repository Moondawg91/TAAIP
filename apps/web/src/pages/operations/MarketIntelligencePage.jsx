import React, {useEffect, useState} from 'react'
import { Box, Container, Grid, Paper, Typography, Select, MenuItem, Button } from '@mui/material'
import { getMarketIntelSummary, getMarketIntelZipRankings, getMarketIntelCbsaRollup, getMarketIntelTargets, getMarketIntelImportTemplates, getMarketIntelDemographics, getMarketIntelCategories, getMarketIntelReadiness, exportMarketIntelTargetsCsv, exportCommanderTargetsCsv } from '../../api/client'
import { previewMiImport, commitMiImport } from '../../api/client'
import MarketIntelKpiStrip from '../../components/operations/MarketIntelKpiStrip'
import MarketIntelZipTable from '../../components/operations/MarketIntelZipTable'
import MarketIntelCbsaTable from '../../components/operations/MarketIntelCbsaTable'
import MarketIntelTargetsPanel from '../../components/operations/MarketIntelTargetsPanel'
import MarketIntelDatasetBanner from '../../components/operations/MarketIntelDatasetBanner'
import MarketIntelImportTemplates from '../../components/operations/MarketIntelImportTemplates'
import MarketIntelDemographicsTable from '../../components/operations/MarketIntelDemographicsTable'
import MarketIntelCategoriesStrip from '../../components/operations/MarketIntelCategoriesStrip'

import { useFilters } from '../../contexts/FilterContext'

export default function MarketIntelligencePage(){
  const { filters: globalFilters } = useFilters()
  const [localFilters, setLocalFilters] = useState({ component:'', market_category:'' })
  const [summary, setSummary] = useState(null)
  const [zipData, setZipData] = useState([])
  const [cbsaData, setCbsaData] = useState([])
  const [targets, setTargets] = useState([])
  const [templates, setTemplates] = useState([])
  const [missing, setMissing] = useState([])
  const [demographics, setDemographics] = useState(null)
  const [categories, setCategories] = useState(null)
  const [readiness, setReadiness] = useState(null)
  const [miDataset, setMiDataset] = useState('mi_zip_fact')
  const [miFile, setMiFile] = useState(null)
  const [miPreview, setMiPreview] = useState(null)
  const [loading, setLoading] = useState(true)

  async function loadAll(){
    setLoading(true)
    const merged = {
      fy: globalFilters?.fy || '',
      qtr: globalFilters?.qtr || '',
      rsid_prefix: globalFilters?.unit_rsid || '',
      component: localFilters.component || '',
      market_category: localFilters.market_category || ''
    }
    try{
      const s = await getMarketIntelSummary(merged)
      setSummary(s)
      setMissing(s && s.missing_data ? s.missing_data : [])
    }catch(e){ setSummary(null); setMissing(['api_error']) }
    try{ const z = await getMarketIntelZipRankings(Object.assign({}, merged, {limit:25})); setZipData((z && (z.tables||z.breakdowns) && (z.tables?.zip_rankings||z.breakdowns?.zip_rankings)) || []) }catch(e){ setZipData([]) }
    try{ const c = await getMarketIntelCbsaRollup(Object.assign({}, merged, {limit:50})); setCbsaData((c && (c.tables||c.breakdowns) && (c.tables?.cbsa_rollup||c.breakdowns?.cbsa_rollup)) || []) }catch(e){ setCbsaData([]) }
    try{ const t = await getMarketIntelTargets(merged); setTargets((t && (t.tables||t.breakdowns) && (t.tables?.targets||t.breakdowns?.targets)) || []) }catch(e){ setTargets([]) }
    try{ const it = await getMarketIntelImportTemplates(); setTemplates(it.templates || []) }catch(e){ setTemplates([]) }
    try{ const d = await getMarketIntelDemographics(merged); setDemographics(d) }catch(e){ setDemographics(null) }
    try{ const c = await getMarketIntelCategories(Object.assign({}, merged, {limit:10})); setCategories(c) }catch(e){ setCategories(null) }
    try{ const r = await getMarketIntelReadiness(); setReadiness(r) }catch(e){ setReadiness(null) }
    setLoading(false)
  }

  useEffect(()=>{ loadAll() }, [globalFilters?.fy, globalFilters?.qtr, globalFilters?.unit_rsid, localFilters.component, localFilters.market_category])

  const handleFilterChange = (k, v)=> setLocalFilters(f=> ({...f, [k]: v}))

  return (
    <Container maxWidth="xl" sx={{py:2}}>
      <Typography variant="h5" sx={{mb:2}}>Market Intelligence</Typography>

      

      {/* Uploads are centralized in Data Hub - remove local upload UI */}

      {missing && missing.length>0 ? <MarketIntelDatasetBanner missing={missing} /> : null}

      <MarketIntelKpiStrip summary={summary} />
      <MarketIntelCategoriesStrip categories={categories} />
      {/* If ZIP missing, show blocking; CBSA is informational only */}
      {readiness && readiness.blocking && readiness.blocking.length>0 ? (
        <Paper sx={{p:1, mb:1, bgcolor:'transparent', borderRadius:'4px'}}>
          <Typography variant="body2" sx={{color:'warning.main'}}>Market Intelligence incomplete: load ZIP dataset to enable dashboards: {readiness.blocking.join(', ')}</Typography>
        </Paper>
      ) : null}

      {/* Readiness panel */}
      <Paper sx={{p:1, mb:2, bgcolor:'transparent', borderRadius:'4px'}}>
        <Typography variant="subtitle1" sx={{mb:1}}>Dataset Readiness</Typography>
        {readiness ? (
          <Box>
            {readiness.datasets.map((d, i)=> (
              <Box key={i} sx={{display:'flex', justifyContent:'space-between', alignItems:'center', py:0.5}}>
                <Typography variant="body2">{d.display_name || d.dataset_key}</Typography>
                <Typography variant="body2" sx={{color: d.loaded ? 'success.main' : 'text.secondary'}}>{d.loaded ? `Loaded (${d.row_count})` : (d.row_count>0 ? `Partial (${d.row_count})` : 'Missing')}</Typography>
              </Box>
            ))}
            <Box sx={{mt:1, display:'flex', gap:1}}>
              <Button size="small" variant="contained" onClick={async ()=>{
                    try{
                      const merged = { fy: globalFilters?.fy || '', qtr: globalFilters?.qtr || '', rsid_prefix: globalFilters?.unit_rsid || '', component: localFilters.component || '', market_category: localFilters.market_category || '' }
                      const csv = await exportMarketIntelTargetsCsv(merged)
                  const blob = new Blob([csv], {type:'text/csv'})
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement('a')
                  a.href = url
                  a.download = `market_targets_${Date.now()}.csv`
                  document.body.appendChild(a)
                  a.click()
                  a.remove()
                  URL.revokeObjectURL(url)
                }catch(e){ console.error(e) }
              }} sx={{borderRadius:'4px'}}>Export Targets CSV</Button>
              <Button size="small" variant="contained" onClick={async ()=>{
                try{
                  const qs = {}
                  if(globalFilters?.fy) qs.fy = globalFilters.fy
                  if(globalFilters?.qtr) qs.qtr = globalFilters.qtr
                  if(globalFilters?.unit_rsid) qs.rsid_prefix = globalFilters.unit_rsid
                  if(localFilters.component) qs.component = localFilters.component
                  if(localFilters.market_category) qs.market_category = localFilters.market_category
                  const csv = await exportCommanderTargetsCsv(qs)
                  const blob = new Blob([csv], {type:'text/csv'})
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement('a')
                  a.href = url
                  a.download = `commander_targets_${Date.now()}.csv`
                  document.body.appendChild(a)
                  a.click()
                  a.remove()
                  URL.revokeObjectURL(url)
                }catch(e){ console.error(e) }
              }} sx={{borderRadius:'4px'}}>Export Commander Targets (CSV)</Button>
            </Box>
          </Box>
        ) : (
          <Typography variant="body2">Readiness information unavailable.</Typography>
        )}
      </Paper>

      <Grid container spacing={2} sx={{mt:1}}>
        <Grid item xs={12} md={6}>
          <Paper sx={{p:1, bgcolor:'transparent', borderRadius:'4px'}}>
            {/* If CBSA not loaded, show compact note instead of full table */}
            {readiness && readiness.datasets && readiness.datasets.find(d=>d.dataset_key==='mi_cbsa_fact') && !readiness.datasets.find(d=>d.dataset_key==='mi_cbsa_fact').loaded ? (
              <Box sx={{p:1}}>
                <Typography variant="body2">CBSA rollups unavailable until CBSA dataset is loaded.</Typography>
              </Box>
            ) : (
              <MarketIntelCbsaTable data={cbsaData} loading={loading} />
            )}
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{p:1, bgcolor:'background.paper', borderRadius:'4px'}}>
            <MarketIntelZipTable data={zipData} loading={loading} />
          </Paper>
        </Grid>
      </Grid>

      <Box sx={{mt:2}}>
        <Paper sx={{p:1, bgcolor:'background.paper', borderRadius:'4px'}}>
          <MarketIntelTargetsPanel targets={targets} />
        </Paper>
      </Box>

      <Box sx={{mt:2}}>
        <Paper sx={{p:1, bgcolor:'background.paper', borderRadius:'4px'}}>
          <MarketIntelDemographicsTable data={demographics} loading={loading} />
        </Paper>
      </Box>

      <Box sx={{position:'fixed', right:16, top:100, width:320}}>
        <Paper sx={{p:1, bgcolor:'background.paper', borderRadius:'4px'}}>
          <MarketIntelImportTemplates templates={templates} />
        </Paper>
      </Box>
    </Container>
  )
}
