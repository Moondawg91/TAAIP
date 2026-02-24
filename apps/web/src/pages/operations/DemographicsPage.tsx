import React, { useEffect, useState } from 'react'
import api from '../../api/client'

export default function DemographicsPage(){
  const [rows, setRows] = useState([])
  const [missing, setMissing] = useState([])

  useEffect(()=>{
    let mounted = true
    api.listMarketDemographics().then(res=>{
      if(!mounted) return
      setRows(res.rows || [])
      setMissing(res.missing_data || [])
    }).catch(()=>{})
    return ()=>{ mounted = false }
  },[])

  return (
    <div style={{background:'#121212', color:'#fff', padding:12, borderRadius:4}}>
      <h2>Demographics & Representation</h2>
      {missing && missing.length>0 && (<div style={{background:'#2b2b2b',padding:8,borderRadius:4}}>Dataset not loaded: {missing.join(', ')}</div>)}
      <div style={{marginTop:8}}>
        <table style={{width:'100%',borderCollapse:'collapse'}}>
          <thead>
            <tr>
              <th>Geo</th><th>Race/Eth</th><th>Gender</th><th>Pop Type</th><th>Population</th><th>Production</th><th>P2P</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(r=> (
              <tr key={r.id} style={{borderTop:'1px solid #2a2a2a'}}>
                <td>{r.geo_id}</td>
                <td>{r.race_ethnicity}</td>
                <td>{r.gender}</td>
                <td>{r.population_type}</td>
                <td>{r.population_value}</td>
                <td>{r.production_value}</td>
                <td>{r.p2p}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
