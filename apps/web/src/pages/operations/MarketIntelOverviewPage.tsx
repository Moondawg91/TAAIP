import React, { useEffect, useState } from 'react'
import api from '../../api/client'

export default function MarketIntelOverviewPage(){
  const [kpis, setKpis] = useState(null)
  const [missing, setMissing] = useState([])

  useEffect(()=>{
    let mounted = true
    api.getMarketSummary().then(res => {
      if(!mounted) return
      setKpis(res.kpis || null)
      setMissing(res.missing_data || [])
    }).catch(()=>{
      setKpis(null)
    })
    return ()=>{ mounted = false }
  },[])

  return (
    <div style={{background:'#121212', color:'#fff', padding:12, borderRadius:4}}>
      <h2>Market Intelligence — Overview</h2>
      {missing && missing.length>0 && (
        <div style={{background:'#2b2b2b', padding:8, borderRadius:4, marginBottom:8}}>Dataset not loaded: {missing.join(', ')}</div>
      )}
      {kpis ? (
        <div style={{display:'flex',gap:12}}>
          <div style={{padding:8,background:'#1e1e1e',borderRadius:4}}>Potential: {kpis.total_army_potential}</div>
          <div style={{padding:8,background:'#1e1e1e',borderRadius:4}}>Contracts: {kpis.total_contracts}</div>
          <div style={{padding:8,background:'#1e1e1e',borderRadius:4}}>Remaining: {kpis.total_potential_remaining}</div>
          <div style={{padding:8,background:'#1e1e1e',borderRadius:4}}>Avg P2P: {kpis.avg_p2p}</div>
        </div>
      ) : (
        <div>No market KPIs available</div>
      )}
    </div>
  )
}
