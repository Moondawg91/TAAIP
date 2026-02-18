import React from 'react'
import { Box, Typography, Button } from '@mui/material'

type Datum = Record<string, any>

type Props = {
  mode: 'map' | 'heatmap'
  data: Datum[]
  geoKey?: string
  valueKey?: string
  title?: string
}

function fmt(n: number) {
  if (n === null || n === undefined || Number.isNaN(n)) return '-'
  return n.toLocaleString()
}

export default function MapRenderer({ mode, data, geoKey, valueKey, title }: Props) {
  const rows = (data || []).filter(Boolean)

  if (!rows.length || !geoKey) {
    return (
      <Box p={2}>
        <Typography variant="subtitle2">{title || 'Map'}</Typography>
        <Typography variant="body2" color="text.secondary">No geo data available</Typography>
      </Box>
    )
  }

  // aggregate by geoKey
  const groups: Record<string, { key: string; value: number }> = {}
  let maxVal = 0
  rows.forEach((r) => {
    const g = r[geoKey]
    if (g === null || g === undefined) return
    const key = String(g)
    const raw = Number(r[valueKey ?? 'value'] ?? 0) || 0
    const cur = groups[key] || { key, value: 0 }
    cur.value += raw
    groups[key] = cur
    if (cur.value > maxVal) maxVal = cur.value
  })

  const list = Object.values(groups).sort((a, b) => b.value - a.value)

  if (mode === 'map') {
    const [showAll, setShowAll] = React.useState(false)
    const visible = showAll ? list : list.slice(0, 25)
    return (
      <Box p={1}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
          <Typography variant="subtitle2">{title || 'Geo Ranking'}</Typography>
          {list.length > 25 && (
            <Button size="small" onClick={() => setShowAll(!showAll)}>{showAll ? 'Show less' : `Show ${list.length}`}</Button>
          )}
        </Box>
        <Box>
          {visible.map((row) => (
            <Box key={row.key} display="flex" alignItems="center" mb={1}>
              <Box flexBasis="40%">
                <Typography variant="body2">{row.key}</Typography>
              </Box>
              <Box flexGrow={1} mr={1} style={{ background: '#f0f0f0', borderRadius: 4, height: 14 }}>
                <Box style={{ width: `${maxVal ? (row.value / maxVal) * 100 : 0}%`, background: '#3182CE', height: '100%', borderRadius: 4 }} />
              </Box>
              <Box width={90} textAlign="right">
                <Typography variant="body2">{fmt(row.value)}</Typography>
              </Box>
            </Box>
          ))}
        </Box>
      </Box>
    )
  }

  // Heatmap
  // Determine columns: category field > time-like field > single "Value"
  const sample = rows[0] || {}
  const keys = Object.keys(sample)
  const candidates = keys.filter((k) => k !== geoKey && k !== valueKey)

  // category detection: field with <=12 unique small-string values
  let categoryField: string | undefined
  for (const k of candidates) {
    const vals = Array.from(new Set(rows.map((r) => r[k]).filter((v) => v !== null && v !== undefined))).slice(0, 50)
    if (vals.length > 0 && vals.length <= 12 && vals.every((v) => typeof v === 'string' || typeof v === 'number')) {
      categoryField = k
      break
    }
  }

  let timeField: string | undefined
  if (!categoryField) {
    for (const k of candidates) {
      const sampleVal = rows.find((r) => r[k] !== undefined && r[k] !== null)?.[k]
      if (sampleVal && !Number.isNaN(Date.parse(String(sampleVal)))) {
        timeField = k
        break
      }
    }
  }

  let columns: string[]
  if (categoryField) {
    columns = Array.from(new Set(rows.map((r) => String(r[categoryField])))).slice(0, 12)
  } else if (timeField) {
    // bucket to day/month string
    const buckets = new Set<string>()
    rows.forEach((r) => {
      const d = new Date(String(r[timeField]))
      if (!Number.isNaN(d.getTime())) buckets.add(d.toISOString().slice(0, 10))
    })
    columns = Array.from(buckets).sort()
  } else {
    columns = ['Value']
  }

  // build matrix
  const matrix: Record<string, Record<string, number>> = {}
  let globalMin = Number.POSITIVE_INFINITY
  let globalMax = 0
  rows.forEach((r) => {
    const g = String(r[geoKey])
    if (!matrix[g]) matrix[g] = {}
    let colKey = 'Value'
    if (categoryField) colKey = String(r[categoryField])
    else if (timeField) {
      const d = new Date(String(r[timeField]))
      colKey = Number.isNaN(d.getTime()) ? 'Value' : d.toISOString().slice(0, 10)
    }
    const v = Number(r[valueKey ?? 'value'] ?? 0) || 0
    matrix[g][colKey] = (matrix[g][colKey] || 0) + v
    if (matrix[g][colKey] < globalMin) globalMin = matrix[g][colKey]
    if (matrix[g][colKey] > globalMax) globalMax = matrix[g][colKey]
  })

  const geoRows = Object.keys(matrix).sort()

  const intensity = (v: number) => {
    if (globalMax === globalMin) return 0.2
    const norm = (v - globalMin) / (globalMax - globalMin)
    return 0.2 + norm * 0.8
  }

  return (
    <Box p={1}>
      <Typography variant="subtitle2" mb={1}>{title || 'Heatmap'}</Typography>
      <Box display="grid" gridTemplateColumns={`150px repeat(${columns.length}, 1fr)`} gap={1}>
        <Box />
        {columns.map((c) => (
          <Box key={`hdr-${c}`} textAlign="center"><Typography variant="caption">{c}</Typography></Box>
        ))}
        {geoRows.map((g) => (
          <React.Fragment key={`row-${g}`}>
            <Box display="flex" alignItems="center"><Typography variant="body2">{g}</Typography></Box>
            {columns.map((c) => {
              const v = matrix[g][c] || 0
              const a = intensity(v)
              return (
                <Box key={`${g}-${c}`} style={{ background: `rgba(49,130,206,${a})`, minHeight: 28, display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 4 }}>
                  <Typography variant="caption" style={{ color: a > 0.5 ? '#fff' : '#000' }}>{v ? v.toLocaleString() : ''}</Typography>
                </Box>
              )
            })}
          </React.Fragment>
        ))}
        </Box>
      </Box>
    )
  }
