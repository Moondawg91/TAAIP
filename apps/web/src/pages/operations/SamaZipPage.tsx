import React, { useEffect, useState } from 'react'
import api from '../../api/client'

export default function SamaZipPage(){
  const [rows, setRows] = useState([])
  const [missing, setMissing] = useState([])

  useEffect(()=>{
    let mounted = true
    api.listMarketZips().then(res=>{
      if(!mounted) return
      setRows(res.rows || [])
      setMissing(res.missing_data || [])
    }).catch(()=>{})
    return ()=>{ mounted = false }
  },[])

  return (
    <div style={{background:'#121212', color:'#fff', padding:12, borderRadius:4}}>
      <h2>SAMA — ZIP-level</h2>
      {missing && missing.length>0 && (<div style={{background:'#2b2b2b',padding:8,borderRadius:4}}>Dataset not loaded: {missing.join(', ')}</div>)}
      <div style={{marginTop:8}}>
        <table style={{width:'100%',borderCollapse:'collapse'}}>
          <thead>
            <tr style={{textAlign:'left'}}>
              <th>ZIP</th><th>Category</th><th>Army Pot</th><th>DoD Pot</th><th>Contracts</th><th>Remaining</th><th>P2P</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(r=> (
              <tr key={r.id} style={{borderTop:'1px solid #2a2a2a'}}>
                <td>{r.zip_code || r.zip}</td>
                <td>{r.zip_category}</td>
                <td>{r.army_potential}</td>
                <td>{r.dod_potential}</td>
                <td>{r.contracts}</td>
                <td>{r.potential_remaining}</td>
                <td>{r.p2p}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
