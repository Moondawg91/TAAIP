const fs = require('fs')
const path = require('path')

const NAV = fs.readFileSync(path.join(__dirname, '..', 'apps', 'web', 'src', 'nav', 'navConfig.ts'), 'utf8')

// extract paths like path: '/foo/bar'
const pathRegex = /path:\s*'([^']+)'/g
let m
const paths = new Set()
while((m = pathRegex.exec(NAV)) !== null){ paths.add(m[1]) }

function toPascal(s){
  return s.split(/[-_\/]/g).filter(Boolean).map(p=> p.charAt(0).toUpperCase()+p.slice(1)).join('')
}

function ensureDir(p){ if(!fs.existsSync(p)) fs.mkdirSync(p, { recursive:true }) }

const pagesRoot = path.join(__dirname, '..', 'apps', 'web', 'src', 'pages')
let created = []
paths.forEach(p => {
  if(!p || p === '/' ) return
  const segs = p.replace(/^\//,'').split('/')
  const dir = path.join(pagesRoot, segs.slice(0,-1).join('/'))
  const name = segs[segs.length-1]
  const fileName = toPascal(name) + 'Page.jsx'
  const filePath = path.join(dir, fileName)
  if(fs.existsSync(filePath)) return
  ensureDir(dir)
  const title = toPascal(name).replace(/([A-Z])/g,' $1').trim()
  const content = `import React from 'react'
import { Box, Typography, Button } from '@mui/material'

export default function ${toPascal(name)}Page(){
  return (
    <Box sx={{ p:2 }}>
      <Typography variant="h5">${title}</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary' }}>Placeholder page scaffolded by create_page_shells.cjs — add content as needed.</Typography>
      <Box sx={{ mt:2 }}>
        <Button variant="contained" onClick={()=>{ window.location.href = '/data-hub/imports' }}>Open Data Hub Imports</Button>
      </Box>
    </Box>
  )
}
`
  fs.writeFileSync(filePath, content, 'utf8')
  created.push(path.relative(process.cwd(), filePath))
})

console.log('Created', created.length, 'page shells')
created.forEach(c=> console.log(' -', c))

if(created.length===0) console.log('No missing page shells found')
