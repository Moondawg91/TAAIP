import React, {useEffect, useState} from 'react'
import { Box, Typography, Paper, Button, TextField } from '@mui/material'
import api from '../../api/client'

export default function GeoTargetingPage(){
  const [zones, setZones] = useState<any[]>([])
  const [name, setName] = useState('')
  const [zoneType, setZoneType] = useState('zip_set')
  const [members, setMembers] = useState('')

  useEffect(()=>{ let mounted=true; api.listGeoZones().then(r=>{ if(mounted) setZones(r.zones || []) }).catch(()=>{}); return ()=>{ mounted=false } }, [])

  async function handleCreate(){
    const payload = { id: name.toLowerCase().replace(/\s+/g,'-'), name, zone_type: zoneType, members: members.split('\n').filter(Boolean).map(l=>{ const parts = l.split(':'); return { member_type: parts[0], member_value: parts[1] } }) }
    await api.createGeoZone(payload)
    const r = await api.listGeoZones()
    setZones(r.zones || [])
    setName(''); setMembers('')
  }

  return (
    <Box sx={{p:3, bgcolor:'background.default', color:'text.primary', minHeight:'100vh'}}>
      <Typography variant="h4">Geo Targeting</Typography>
      <Box sx={{display:'flex', gap:2, mt:2}}>
        <Paper sx={{p:2, bgcolor:'transparent', borderRadius:1}}>
          <Typography variant="subtitle1">Create Zone</Typography>
          <TextField label="Name" value={name} onChange={(e)=>setName(e.target.value)} fullWidth sx={{mt:1}} />
          <TextField label="Zone Type" value={zoneType} onChange={(e)=>setZoneType(e.target.value)} fullWidth sx={{mt:1}} />
          <TextField label="Members (one per line, e.g. zip:98052)" value={members} onChange={(e)=>setMembers(e.target.value)} multiline rows={4} fullWidth sx={{mt:1}} />
          <Box sx={{mt:1}}><Button variant="contained" onClick={handleCreate}>Create Zone</Button></Box>
        </Paper>

        <Paper sx={{p:2, bgcolor:'transparent', borderRadius:1}}>
          <Typography variant="subtitle1">Zones</Typography>
          {zones.length===0 ? <Typography sx={{color:'text.secondary'}}>No zones defined</Typography> : (
            <ul>
              {zones.map(z=> <li key={z.id}>{z.name} — {z.zone_type} ({z.member_count} members)</li>)}
            </ul>
          )}
        </Paper>
      </Box>
    </Box>
  )
}
