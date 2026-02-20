import React, {useEffect, useState} from 'react'
import { getCommandCenterOverview, getCommandCenterMissionAssessment } from '../../api/client'
import CommandPrioritiesPanel from '../../components/command/CommandPrioritiesPanel'
import LoeEditorPanel from '../../components/command/LoeEditorPanel'
import ZeroStatePanel from '../../components/command/ZeroStatePanel'
import ExportMenuButton from '../../components/command/ExportMenuButton'

export default function CommandCenterPage(){
  const [overview, setOverview] = useState(null)
  const [assessment, setAssessment] = useState(null)

  useEffect(()=>{
    let mounted = true
    getCommandCenterOverview().then(r=>{ if(mounted) setOverview(r) }).catch(()=>{})
    getCommandCenterMissionAssessment().then(r=>{ if(mounted) setAssessment(r) }).catch(()=>{})
    return ()=>{ mounted=false }
  }, [])

  return (
    <div style={{padding:20}}>
      <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:12}}>
        <h2 style={{color:'#fff', margin:0}}>Command Center</h2>
        <ExportMenuButton onExportCsv={()=>{ window.alert('CSV export not implemented yet') }} onExportJson={()=>{ window.alert('JSON export not implemented yet') }} />
      </div>

      <div style={{display:'grid', gridTemplateColumns:'1fr 320px', gap:16}}>
        <div>
          <section style={{marginBottom:12}}>
            <CommandPrioritiesPanel />
          </section>
          <section style={{marginBottom:12}}>
            <LoeEditorPanel />
          </section>
          <section>
            <h4 style={{color:'#fff'}}>Mission Assessment</h4>
            {assessment ? <pre style={{color:'#fff'}}>{JSON.stringify(assessment, null, 2)}</pre> : <ZeroStatePanel title='No assessment' message='Mission assessment not available yet.' />}
          </section>
        </div>

        <aside>
          <div style={{marginBottom:12}}>
            <h4 style={{color:'#fff'}}>Overview</h4>
            {overview ? <pre style={{color:'#fff'}}>{JSON.stringify(overview.summary || overview, null, 2)}</pre> : <ZeroStatePanel title='Overview empty' message='No summary data available.' />}
          </div>
        </aside>
      </div>
    </div>
  )
}
