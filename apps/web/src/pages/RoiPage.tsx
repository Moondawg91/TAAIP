import React, { useEffect, useState } from 'react'
import { useOrgUnitStore } from '../state/orgUnitStore'
import { getRoiKpis, getRoiBreakdown, getRoiFunnel } from '../api/client'

export default function RoiPage(){
  const store = useOrgUnitStore()
  const [kpis, setKpis] = useState(null)
  const [breakdown, setBreakdown] = useState(null)
  const [funnel, setFunnel] = useState(null)

  useEffect(()=>{
    // initial load using persisted selection handled by client attach
    loadAll()
  }, [])

  async function loadAll(){
    try{
      const data = await getRoiKpis()
      setKpis(data)
    }catch(e){ setKpis({ error: String(e) }) }
    try{ const b = await getRoiBreakdown(); setBreakdown(b) }catch(e){ setBreakdown({error:String(e)}) }
    try{ const f = await getRoiFunnel(); setFunnel(f) }catch(e){ setFunnel({error:String(e)}) }
  }

  return (
    <div style={{padding:20}}>
      <h2>ROI Dashboard</h2>
      <p>Active unit: {store.pathLabel}</p>

      <section style={{marginTop:16}}>
        <h3>KPIs</h3>
        {kpis ? <pre style={{background:'#f6f6f6',padding:12}}>{JSON.stringify(kpis, null, 2)}</pre> : <div>Loading…</div>}
      </section>

      <section style={{marginTop:16}}>
        <h3>Breakdown</h3>
        {breakdown ? <pre style={{background:'#f6f6f6',padding:12}}>{JSON.stringify(breakdown, null, 2)}</pre> : <div>Loading…</div>}
      </section>

      <section style={{marginTop:16}}>
        <h3>Funnel</h3>
        {funnel ? <pre style={{background:'#f6f6f6',padding:12}}>{JSON.stringify(funnel, null, 2)}</pre> : <div>Loading…</div>}
      </section>
    </div>
  )
}
