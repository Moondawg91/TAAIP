import React, { useEffect, useState } from 'react'
import {Typography} from '@mui/material'
import { getMarketIntelZipRankings, getMarketIntelCbsaRollup } from '../api/client'
import ChartRenderer from './ChartRenderer'
import DashboardCard from './ui/DashboardCard'

const COLORS = ['#2b7bff','#7b61ff','#00b07a','#ffb84d','#9aa0a6']

export default function CoverageCharts({counts, onDrilldown}){
  const [zipData, setZipData] = useState([])
  const [zipLoading, setZipLoading] = useState(false)
  const [cbsaData, setCbsaData] = useState([])
  const [cbsaLoading, setCbsaLoading] = useState(false)

  useEffect(() => {
    let canceled = false
    setZipLoading(true)
    setCbsaLoading(true)
    Promise.all([
      getMarketIntelZipRankings().catch(()=>[]),
      getMarketIntelCbsaRollup().catch(()=>[])
    ]).then(([zipJ, cbsaJ]) => {
      if (canceled) return
      setZipData(Array.isArray(zipJ) ? zipJ : [])
      setCbsaData(Array.isArray(cbsaJ) ? cbsaJ : [])
    }).catch(() => { setZipData([]); setCbsaData([]) }).finally(() => { if(!canceled){ setZipLoading(false); setCbsaLoading(false) } })
    return ()=>{ canceled = true }
  }, [])
  // counts: {MK: n, MW: n, MO: n, SU: n, UNK: n}
  const categories = ['MK','MW','MO','SU','UNK']
  const total = categories.reduce((s,c)=> s + (counts && counts[c] ? counts[c] : 0), 0)
  const barData = categories.map((c,i) => ({ category: c, value: counts && counts[c] ? counts[c] : 0, color: COLORS[i] }))
  const pieData = categories.map((c,i)=> ({ name: c, value: counts && counts[c] ? counts[c] : 0, color: COLORS[i]}))

  const hasAny = total > 0

  return (
    <>
      <DashboardCard>
        <Typography variant="subtitle1">ZIP Coverage by Category</Typography>
        {!hasAny ? <Typography variant="body2" color="text.secondary">No ZIP coverage loaded. Import Zip Codes in USAREC.xlsx.</Typography> : (
          <div style={{height:260}}>
            <ChartRenderer spec={{ type: 'auto', data: barData, xKey: 'category', yKey: 'value', dimensionField: 'category', measureCount: 1, measureFields: ['value'], geoFields: ['zip','ZIP','cbsa','CBSA','state','STATE','city','CITY'], name: 'ZIP Coverage by Category' }} height={220} onDrilldown={onDrilldown} />
          </div>
        )}
      </DashboardCard>

      <DashboardCard sx={{mt:2}}>
        <Typography variant="subtitle1">ZIP Coverage Map</Typography>
        {!zipData || zipData.length === 0 ? (
          <Typography variant="body2" color="text.secondary">{zipLoading ? 'Loading ZIP coverage...' : 'No ZIP geo data available.'}</Typography>
        ) : (
          <div style={{height:320}}>
            <ChartRenderer spec={{ type: 'auto', data: zipData, dimensionField: 'zip', measureFields: ['value'], measureCount: 1, geoFields: ['zip'], xKey: 'zip', yKey: 'value', name: 'ZIP Coverage Map' }} height={300} onDrilldown={onDrilldown} />
          </div>
        )}
      </DashboardCard>

      <DashboardCard sx={{mt:2}}>
        <Typography variant="subtitle1">CBSA Coverage Map</Typography>
        {!cbsaData || cbsaData.length === 0 ? (
          <Typography variant="body2" color="text.secondary">{cbsaLoading ? 'Loading CBSA coverage...' : 'No CBSA geo data available.'}</Typography>
        ) : (
          <div style={{height:320}}>
            <ChartRenderer spec={{ type: 'auto', data: cbsaData, dimensionField: 'cbsa', measureFields: ['value'], measureCount: 1, geoFields: ['cbsa'], xKey: 'cbsa', yKey: 'value', name: 'CBSA Coverage Map' }} height={300} onDrilldown={onDrilldown} />
          </div>
        )}
      </DashboardCard>

      <DashboardCard sx={{mt:2}}>
        <Typography variant="subtitle1">Category Distribution</Typography>
        {!hasAny ? <Typography variant="body2" color="text.secondary">No ZIP coverage to display distribution.</Typography> : (
          <div style={{height:220}}>
            <ChartRenderer spec={{ type: 'auto', data: pieData, xKey: 'name', yKey: 'value', dimensionField: 'name', measureCount: 1, measureFields: ['value'], typeHint: 'pie', geoFields: ['zip','ZIP','cbsa','CBSA','state','STATE','city','CITY'], name: 'Category Distribution' }} height={200} onDrilldown={onDrilldown} />
          </div>
        )}
      </DashboardCard>
    </>
  )
}
