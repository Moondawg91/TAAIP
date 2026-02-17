import React, { useMemo, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, AreaChart, Area, CartesianGrid, Legend, PieChart, Pie, Cell } from 'recharts'
import MapRenderer from './MapRenderer' // TODO: if MapRenderer is not present add a stub to avoid build break

type Datum = Record<string, unknown>

type ChartSpec = {
  type?: 'auto' | 'bar' | 'line' | 'pie' | 'kpi' | 'map' | 'heatmap'
  data: Datum[]
  xKey?: string
  yKey?: string
  color?: string
  name?: string
  // visual decision hints
  isSingleMetric?: boolean
  measureCount?: number
  measureFields?: string[]
  timeField?: string
  geoFields?: string[]
  densityMode?: boolean
  typeHint?: string
  deltaField?: string
  dimensionField?: string
}

type Props = {
  spec: ChartSpec
  height?: number
  onDrilldown?: (payload: { dimension?: string; value?: any; filtersToApply?: Record<string, any> }) => void
}

function isNumericArray(arr: Datum[], key?: string): boolean {
  if (!arr || arr.length === 0) return false
  return arr.every((d) => {
    const v = key ? (d as any)[key] : d
    return v === null || v === undefined ? true : !Number.isNaN(Number(v))
  })
}

function isTimeDimension(arr: Datum[], key?: string): boolean {
  if (!arr || arr.length === 0 || !key) return false
  let count = 0
  for (let i = 0; i < Math.min(arr.length, 20); i++) {
    const v = (arr[i] as any)[key]
    if (!v) continue
    const parsed = Date.parse(String(v))
    if (!Number.isNaN(parsed)) count++
  }
  return count >= Math.min(3, arr.length)
}

function isGeoDimension(arr: Datum[], geoFields?: string[]): boolean {
  if (geoFields && geoFields.length) {
    const normalized = geoFields.map((s) => s.toLowerCase())
    const geoHints = ['zip', 'zipcode', 'cbsa', 'state', 'city', 'lat', 'lng', 'latitude', 'longitude']
    if (normalized.some((f) => geoHints.includes(f))) return true
  }
  if (!arr || arr.length === 0) return false
  const keys = Object.keys(arr[0] || {}).map((k) => k.toLowerCase())
  return keys.includes('lat') || keys.includes('lng') || keys.includes('zipcode') || keys.includes('zip') || keys.includes('cbsa') || keys.includes('state') || keys.includes('city')
}

function categoryCount(arr: Datum[], key?: string): number {
  if (!arr || arr.length === 0 || !key) return 0
  const s = new Set<string>()
  arr.forEach((d) => {
    const v = (d as any)[key]
    if (v !== null && v !== undefined) s.add(String(v))
  })
  return s.size
}

const ChartRenderer: React.FC<Props> = ({ spec, height = 300, onDrilldown }) => {
  if (!spec || !spec.data) return null

  const [override, setOverride] = useState<string>(spec.type || 'auto')

  const decision = useMemo(() => {
    const data = spec.data || []
    const x = spec.xKey
    const y = spec.yKey

    if (override && override !== 'auto') return override

    // KPI rules
    if (spec.isSingleMetric === true || data.length === 1 || (spec.measureCount === 1 && !spec.dimensionField)) return 'kpi'

    // Time-based
    if (spec.timeField || isTimeDimension(data, spec.timeField || x)) return 'line'

    // Geo-based
    if (isGeoDimension(data, spec.geoFields)) return 'map'

    // Density / heatmap
    if (spec.densityMode === true || spec.typeHint === 'heatmap') return 'heatmap'

    // Category-based bar chart when few categories (<10) and numeric measure
    if (spec.dimensionField && categoryCount(data, spec.dimensionField) > 0 && categoryCount(data, spec.dimensionField) < 10 && y && isNumericArray(data, y)) return 'bar'

    // default
    return 'bar'
  }, [spec, override])

  const triggerDrill = (d: any) => {
    if (!d || !onDrilldown) return
    const dim = spec.dimensionField || spec.xKey
    const val = (d && ((d[dim] !== undefined) ? d[dim] : (d[spec.yKey as string] ?? d.name ?? d.value)))
    const filters = dim ? { [dim]: val } : undefined
    onDrilldown({ dimension: dim, value: val, filtersToApply: filters })
  }

  const common = (
    <>
      <CartesianGrid strokeDasharray="3 3" />
      {spec.xKey && <XAxis dataKey={spec.xKey} />}
      <YAxis />
      <Tooltip />
      <Legend />
    </>
  )

  // KPI
  if (decision === 'kpi') {
    const row = spec.data[0]
    const rawValue = spec.yKey ? (row as any)[spec.yKey] : Object.values(row)[0]
    const displayValue: React.ReactNode = (rawValue === null || rawValue === undefined)
      ? 'N/A'
      : (typeof rawValue === 'number' ? (rawValue as number).toLocaleString() : String(rawValue))
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-lg p-4">
        <div className="flex justify-between items-start mb-2">
          <strong className="text-sm text-gray-500">{spec.name || spec.yKey || 'Metric'}</strong>
          <select value={override} onChange={(e) => setOverride(e.target.value)} className="ml-2 text-sm">
            <option value="auto">Auto</option>
            <option value="kpi">KPI</option>
            <option value="bar">Bar</option>
            <option value="line">Line</option>
            <option value="area">Area</option>
            <option value="map">Map</option>
            <option value="heatmap">Heatmap</option>
          </select>
        </div>
        <div className="text-3xl font-semibold">{displayValue}</div>
      </div>
    )
  }

  // Map / Heatmap
  if (decision === 'map' || decision === 'heatmap') {
    // determine geoKey
    const data = spec.data || []
    const sample = data[0] || {}
    const detectGeoKey = (): string | undefined => {
      const hints = (spec.geoFields && spec.geoFields.length ? spec.geoFields : ['zip','ZIP','cbsa','CBSA','state','STATE','city','CITY','zipcode','lat','lng','latitude','longitude'])
      for (const h of hints) {
        const found = Object.keys(sample).find((k) => k && k.toLowerCase() === String(h).toLowerCase())
        if (found) return found
      }
      // try approximate match
      const lowerKeys = Object.keys(sample).map((k) => k.toLowerCase())
      const fallbackHints = ['zip','zipcode','cbsa','state','city','lat','lng','latitude','longitude']
      for (const fh of fallbackHints) {
        const idx = lowerKeys.indexOf(fh)
        if (idx >= 0) return Object.keys(sample)[idx]
      }
      return undefined
    }

    const detectValueKey = (): string | undefined => {
      if (spec.measureFields && spec.measureFields.length) return spec.measureFields[0]
      const exclude = new Set<string>([spec.dimensionField || '', spec.timeField || ''])
      const keys = Object.keys(sample)
      for (const k of keys) {
        if (exclude.has(k)) continue
        if (isGeoField(k)) continue
        // prefer numeric-like
        const someVal = data.find((r) => (r as any)[k] !== undefined && (r as any)[k] !== null)?.[k]
        if (someVal !== undefined && someVal !== null && !Number.isNaN(Number(someVal))) return k
      }
      // fallback to yKey
      if (spec.yKey) return spec.yKey
      return undefined
    }

    const geoKey = detectGeoKey()
    const valueKey = detectValueKey()

    return (
      <div className="p-2">
        <div className="flex justify-between items-center mb-2">
          <strong className="text-sm">{spec.name || 'Map'}</strong>
          <select value={override} onChange={(e) => setOverride(e.target.value)} className="ml-2 text-sm">
            <option value="auto">Auto</option>
            <option value="kpi">KPI</option>
            <option value="bar">Bar</option>
            <option value="line">Line</option>
            <option value="area">Area</option>
            <option value="map">Map</option>
            <option value="heatmap">Heatmap</option>
          </select>
        </div>
        <MapRenderer mode={decision as 'map' | 'heatmap'} data={data} geoKey={geoKey} valueKey={valueKey} title={spec.name} />
      </div>
    )
  }

  // Charts (bar/line/area)
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-lg p-3">
      <div className="flex justify-between items-start mb-2">
        <strong className="text-sm text-gray-500">{spec.name || spec.yKey || 'Chart'}</strong>
        <select value={override} onChange={(e) => setOverride(e.target.value)} className="ml-2 text-sm">
          <option value="auto">Auto</option>
          <option value="kpi">KPI</option>
          <option value="bar">Bar</option>
          <option value="line">Line</option>
          <option value="area">Area</option>
          <option value="map">Map</option>
          <option value="heatmap">Heatmap</option>
        </select>
      </div>
      <ResponsiveContainer width="100%" height={height}>
        {(() => {
          if (decision === 'bar') {
            return (
              <BarChart data={spec.data}>
                {common}
                <Bar dataKey={spec.yKey} fill={spec.color || '#3182CE'} name={spec.name || spec.yKey} onClick={(data: any) => triggerDrill(data && data.payload ? data.payload : data)} />
              </BarChart>
            )
          }
          if (decision === 'line') {
            return (
              <LineChart data={spec.data}>
                {common}
                <Line type="monotone" dataKey={spec.yKey} stroke={spec.color || '#10B981'} activeDot={{ onClick: (e: any) => triggerDrill(e && e.payload ? e.payload : e) }} />
              </LineChart>
            )
          }
          if (decision === 'area') {
            return (
              <AreaChart data={spec.data}>
                {common}
                <Area type="monotone" dataKey={spec.yKey} stroke={spec.color || '#F59E0B'} fill={spec.color || '#F59E0B'} />
              </AreaChart>
            )
          }
          if (decision === 'pie') {
            return (
              <PieChart data={spec.data}>
                <Pie data={spec.data} dataKey={spec.yKey} nameKey={spec.xKey} outerRadius={80} onClick={(data: any) => triggerDrill(data && data.payload ? data.payload : data)}>
                  {spec.data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={(entry as any).color || spec.color || '#3182CE'} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            )
          }
          return null
        })()}
      </ResponsiveContainer>
    </div>
  )
}

// public-friendly detectors required by Visual Decision Engine
function isTimeField(fieldName?: string, sampleValue?: any): boolean {
  if (!fieldName) return false
  const low = fieldName.toLowerCase()
  if (low.includes('date') || low.includes('time') || low.includes('ts')) return true
  if (!sampleValue) return false
  return !Number.isNaN(Date.parse(String(sampleValue)))
}

function isGeoField(fieldName?: string): boolean {
  if (!fieldName) return false
  const low = fieldName.toLowerCase()
  const hints = ['zip', 'zipcode', 'cbsa', 'lat', 'lng', 'latitude', 'longitude', 'state', 'city']
  return hints.some((h) => low.includes(h))
}
export default ChartRenderer
