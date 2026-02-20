import React, {useEffect, useState} from 'react'
import {Box, Typography, Paper, List, ListItem, ListItemText, Button, TextField} from '@mui/material'
import {listProposals, createProposal, decideProposal, markProposalApplied} from '../../api/client'

export default function SystemProposalsPage(){
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

  return (
    <Box>
      <Typography variant="h5" sx={{mb:2}}>Change Proposals</Typography>
      <Paper sx={{p:2, mb:2, bgcolor:'background.paper', borderRadius:1}}>
        <Typography variant="subtitle2">Create</Typography>
        <TextField label="Title" size="small" fullWidth value={title} onChange={e=>setTitle(e.target.value)} sx={{mb:1}} />
        <TextField label="Description" size="small" fullWidth multiline minRows={2} value={description} onChange={e=>setDescription(e.target.value)} sx={{mb:1}} />
        <Button variant="contained" onClick={doCreate} sx={{borderRadius:1}}>Submit</Button>
      </Paper>

      <Paper sx={{p:2, bgcolor:'background.paper', borderRadius:1}}>
        <List>
          {proposals.map(p=> (
            <ListItem key={p.id} divider>
              <ListItemText primary={`${p.title} (${p.status})`} secondary={p.description} />
              <Button size="small" onClick={()=>doDecide(p.id, 'approve')} sx={{mr:1}}>Approve</Button>
              <Button size="small" onClick={()=>doDecide(p.id, 'reject')} sx={{mr:1}}>Reject</Button>
              <Button size="small" onClick={()=>doMarkApplied(p.id)}>Mark Applied</Button>
            </ListItem>
          ))}
        </List>
      </Paper>
    </Box>
  )
}
