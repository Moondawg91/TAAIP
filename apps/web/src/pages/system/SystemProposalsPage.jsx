import React, {useEffect, useState} from 'react'
import {Box, Typography, Paper, List, ListItem, ListItemText, Button, TextField} from '@mui/material'
import {useTheme} from '@mui/material/styles'
import {listProposals, createProposal, decideProposal, markProposalApplied} from '../../api/client'

export default function SystemProposalsPage(){
  const theme = useTheme()
  const [proposals, setProposals] = useState([])
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  async function load(){
    try{ const res = await listProposals(); setProposals(res || []) }catch(e){ setProposals([]) }
  }
  useEffect(()=>{ load() },[])

  async function doCreate(){
    try{
      await createProposal({title, description})
      setTitle(''); setDescription('')
      load()
    }catch(e){ alert('create failed') }
  }

  async function doDecide(id, decision){
    try{ await decideProposal(id, {decision}); load() }catch(e){ alert('decision failed') }
  }

  async function doMarkApplied(id){
    try{ await markProposalApplied(id); load() }catch(e){ alert('mark failed') }
  }

  const cardBg = theme.palette.background.default

  return (
    <Box sx={{p:2}}>
      <Typography variant="h5" sx={{mb:2,color:'text.primary'}}>Change Proposals</Typography>
      <Paper sx={{p:2, mb:2, bgcolor: cardBg, borderRadius: '4px'}}>
        <Typography variant="subtitle2" sx={{color:'text.secondary'}}>Create</Typography>
        <TextField label="Title" size="small" fullWidth value={title} onChange={e=>setTitle(e.target.value)} sx={{mb:1, bgcolor:'transparent'}} />
        <TextField label="Description" size="small" fullWidth multiline minRows={2} value={description} onChange={e=>setDescription(e.target.value)} sx={{mb:1, bgcolor:'transparent'}} />
        <Button variant="contained" onClick={doCreate} sx={{borderRadius:'4px'}}>Submit</Button>
      </Paper>

      <Paper sx={{p:2, bgcolor: cardBg, borderRadius: '4px'}}>
        <List>
          {proposals.map(p=> (
            <ListItem key={p.id} divider sx={{borderRadius:'4px'}}>
              <ListItemText primary={`${p.title} (${p.status})`} secondary={p.description} sx={{color:'text.primary'}} />
              <Button size="small" onClick={()=>doDecide(p.id, 'approve')} sx={{mr:1, borderRadius:'4px'}}>Approve</Button>
              <Button size="small" onClick={()=>doDecide(p.id, 'reject')} sx={{mr:1, borderRadius:'4px'}}>Reject</Button>
              <Button size="small" onClick={()=>doMarkApplied(p.id)} sx={{borderRadius:'4px'}}>Mark Applied</Button>
            </ListItem>
          ))}
        </List>
      </Paper>
    </Box>
  )
}
