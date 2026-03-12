import React, { useState, useEffect } from 'react'
import { Box, Paper, Typography, Button, TextField, Table, TableHead, TableRow, TableCell, TableBody } from '@mui/material'
import { uploadDocumentForm, listDocuments, documentDownloadUrl } from '../../api/client'

export default function DocumentUploadPanel(){
  const [file, setFile] = useState<File | null>(null)
  const [description, setDescription] = useState('')
  const [tags, setTags] = useState('')
  const [status, setStatus] = useState('')
  const [docs, setDocs] = useState<Array<any>>([])

  useEffect(()=>{ load() }, [])

  async function load(){
    try{ const list = await listDocuments(); setDocs(list || []) }catch(e){ console.error(e) }
  }

  function onFileChange(e:any){
    const f = e.target.files && e.target.files[0]
    setFile(f)
    setStatus('')
  }

  async function doUpload(){
    if(!file) return
    const fd = new FormData()
    fd.append('file', file)
    if(description) fd.append('description', description)
    if(tags) fd.append('tags', tags)
    setStatus('uploading')
    try{
      const res = await uploadDocumentForm(fd)
      setStatus('uploaded')
      setFile(null)
      setDescription('')
      setTags('')
      // refresh list
      await load()
    }catch(e){ setStatus('upload failed'); console.error(e) }
  }

  return (
    <Paper sx={{ p:2, mb:2, bgcolor:'background.paper', borderRadius:'4px' }}>
      <Typography variant="h6">Documents</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary' }}>Upload manuals, regulations or dataset files for traceability.</Typography>
      <Box sx={{ mt:2 }}>
        <Typography variant="body2">Document uploads have been centralized in the Data Hub. Use the Data Hub imports page to upload new documents and datasets.</Typography>
        <Box sx={{ mt:2 }}>
          <Button variant="contained" onClick={()=>{ window.location.href = '/data-hub/imports' }}>Open Data Hub Imports</Button>
        </Box>
      </Box>
      {status && <Typography variant="caption" sx={{ display:'block', mt:1 }}>{status}</Typography>}

      <Box sx={{ mt:2 }}>
        <Typography variant="subtitle2">Uploaded Documents</Typography>
        <Table size="small" sx={{ mt:1 }}>
          <TableHead>
            <TableRow><TableCell>File</TableCell><TableCell>Uploaded</TableCell><TableCell>Size</TableCell><TableCell>Tags</TableCell><TableCell>Action</TableCell></TableRow>
          </TableHead>
          <TableBody>
            {docs.map(d=> (
              <TableRow key={d.id}>
                <TableCell>{d.filename}</TableCell>
                <TableCell>{d.uploaded_at}</TableCell>
                <TableCell>{d.size}</TableCell>
                <TableCell>{d.tags}</TableCell>
                <TableCell>
                  <a href={documentDownloadUrl(d.id)} target="_blank" rel="noreferrer">Download</a>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Box>
    </Paper>
  )
}
