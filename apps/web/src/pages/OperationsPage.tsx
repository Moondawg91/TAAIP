import React, { useState } from 'react'
import { Box, Container } from '@mui/material'
import OpsTabs from '../components/ops/OpsTabs'
import PlanningEventsPanel from '../components/ops/PlanningEventsPanel'
import OpsDetailTray from '../components/ops/OpsDetailTray'

type OpsTab = 'planning'

export default function OperationsPage(){
  const [active, setActive] = useState<OpsTab>('planning')
  const [detailState, setDetailState] = useState<any>({ open: false })

  const openDetail = (s:any)=> setDetailState(Object.assign({ open: true }, s))
  const closeDetail = ()=> setDetailState({ open: false })

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ px:2, pt:2 }}>
        <OpsTabs active={active} onChange={(t:OpsTab)=>setActive(t)} />
      </Box>
      <Box sx={{ flex:1, overflow:'auto', p:2 }}>
        {active === 'planning' && (
          <PlanningEventsPanel quarter={'Q1'} onQuarterChange={()=>{}} events={[]} tasks={[]} onCreateEvent={()=>{}} onSelectEvent={()=>{}} onSelectTask={()=>{}} openDetail={openDetail} />
        )}
      </Box>
      <OpsDetailTray state={detailState} onClose={closeDetail} />
    </Box>
  )
}
