const fs = require('fs')
const path = require('path')

const searchRoot = path.join(__dirname, '..', 'apps', 'web', 'src', 'pages')

function walk(dir, files = []) {
  fs.readdirSync(dir).forEach(f => {
    const p = path.join(dir, f)
    if (fs.statSync(p).isDirectory()) walk(p, files)
    else files.push(p)
  })
  return files
}

const files = walk(searchRoot).filter(f => f.endsWith('Page.jsx') || f.endsWith('Page.tsx'))
let updated = []
files.forEach(file => {
  const txt = fs.readFileSync(file, 'utf8')
  if (!txt.includes('Placeholder page scaffolded')) return
  const nameMatch = file.match(/([A-Za-z0-9]+)Page\.(jsx|tsx)$/)
  const compName = nameMatch ? nameMatch[1] : 'Page'
  const title = compName.replace(/([A-Z])/g, ' $1').trim()
  const newContent = `import React from 'react'
import { Box, Typography, Grid, Paper, Button } from '@mui/material'

export default function ${compName}(){
  return (
    <Box sx={{ p:3 }}>
      <Typography variant="h4" sx={{ mb:1 }}>${title}</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>This is a scaffolded TOR page. Replace KPIs and drilldowns with real data and components.</Typography>

      <Grid container spacing={2}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p:2 }}>
            <Typography variant="subtitle2">KPI: Metric A</Typography>
            <Typography variant="h5">—</Typography>
            <Typography variant="caption" sx={{ color:'text.secondary' }}>Placeholder value</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p:2 }}>
            <Typography variant="subtitle2">KPI: Metric B</Typography>
            <Typography variant="h5">—</Typography>
            <Typography variant="caption" sx={{ color:'text.secondary' }}>Placeholder value</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p:2 }}>
            <Typography variant="subtitle2">KPI: Metric C</Typography>
            <Typography variant="h5">—</Typography>
            <Typography variant="caption" sx={{ color:'text.secondary' }}>Placeholder value</Typography>
          </Paper>
        </Grid>
      </Grid>

      <Box sx={{ mt:3 }}>
        <Typography variant="h6">Drilldowns</Typography>
        <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Add charts, tables, and filters here to explore data for this TOR.</Typography>
        <Button variant="contained" onClick={()=>{ window.location.href = '/data-hub/imports' }}>Open Data Hub Imports</Button>
      </Box>
    </Box>
  )
}
`
  fs.writeFileSync(file, newContent, 'utf8')
  updated.push(path.relative(process.cwd(), file))
})

console.log('Updated', updated.length, 'pages')
updated.forEach(u=> console.log(' -', u))
if (updated.length === 0) console.log('No placeholder pages found')