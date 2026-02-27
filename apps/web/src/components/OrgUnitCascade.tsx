import React, { useEffect, useState } from 'react'
import type { Echelon, OrgUnitSelection, UnitOption } from '../types/org'

type Props = {
  value: OrgUnitSelection;
  onChange: (next: OrgUnitSelection) => void;
  fetchChildren: (parent_key: string, echelon: Echelon) => Promise<UnitOption[]>;
  showRSIDSecondary?: boolean;
}

function sortOptions(a: UnitOption, b: UnitOption) {
  const ao = a.sort_order ?? 9999
  const bo = b.sort_order ?? 9999
  if (ao !== bo) return ao - bo
  return (a.display_name || '').localeCompare(b.display_name || '')
}

export default function OrgUnitCascade({ value, onChange, fetchChildren, showRSIDSecondary = true }: Props){
  const cmdKey = value.cmd.unit_key
  const [bdes, setBdes] = useState<UnitOption[]>([])
  const [bns, setBns] = useState<UnitOption[]>([])
  const [cos, setCos] = useState<UnitOption[]>([])
  const [stns, setStns] = useState<UnitOption[]>([])
  const [loading, setLoading] = useState<Record<string,boolean>>({})

  useEffect(()=>{
    let alive = true
    ;(async ()=>{
      setLoading(s=>({ ...s, BDE: true }))
      try{
        const data = await fetchChildren(cmdKey, 'BDE')
        if (!alive) return
        setBdes([...data].sort(sortOptions))
      }finally{ if (alive) setLoading(s=>({ ...s, BDE: false })) }
    })()
    return ()=>{ alive = false }
  }, [cmdKey, fetchChildren])

  useEffect(()=>{
    const bdeKey = value.bde?.unit_key
    setBns([]); setCos([]); setStns([])
    if (!bdeKey) return
    let alive = true
    ;(async ()=>{
      setLoading(s=>({ ...s, BN: true }))
      try{
        const data = await fetchChildren(bdeKey, 'BN')
        if (!alive) return
        setBns([...data].sort(sortOptions))
      }finally{ if (alive) setLoading(s=>({ ...s, BN: false })) }
    })()
    return ()=>{ alive = false }
  }, [value.bde?.unit_key, fetchChildren])

  useEffect(()=>{
    const bnKey = value.bn?.unit_key
    setCos([]); setStns([])
    if (!bnKey) return
    let alive = true
    ;(async ()=>{
      setLoading(s=>({ ...s, CO: true }))
      try{
        const data = await fetchChildren(bnKey, 'CO')
        if (!alive) return
        setCos([...data].sort(sortOptions))
      }finally{ if (alive) setLoading(s=>({ ...s, CO: false })) }
    })()
    return ()=>{ alive = false }
  }, [value.bn?.unit_key, fetchChildren])

  useEffect(()=>{
    const coKey = value.co?.unit_key
    setStns([])
    if (!coKey) return
    let alive = true
    ;(async ()=>{
      setLoading(s=>({ ...s, STN: true }))
      try{
        const data = await fetchChildren(coKey, 'STN')
        if (!alive) return
        setStns([...data].sort(sortOptions))
      }finally{ if (alive) setLoading(s=>({ ...s, STN: false })) }
    })()
    return ()=>{ alive = false }
  }, [value.co?.unit_key, fetchChildren])

  const label = (u?: UnitOption | null) => {
    if (!u) return ''
    return showRSIDSecondary && u.rsid ? `${u.display_name} (${u.rsid})` : u.display_name
  }

  const setBde = (unit_key: string) => {
    const next = bdes.find(x=>x.unit_key===unit_key) || null
    onChange({ ...value, bde: next, bn: null, co: null, stn: null })
  }
  const setBn = (unit_key: string) => {
    const next = bns.find(x=>x.unit_key===unit_key) || null
    onChange({ ...value, bn: next, co: null, stn: null })
  }
  const setCo = (unit_key: string) => {
    const next = cos.find(x=>x.unit_key===unit_key) || null
    onChange({ ...value, co: next, stn: null })
  }
  const setStn = (unit_key: string) => {
    const next = stns.find(x=>x.unit_key===unit_key) || null
    onChange({ ...value, stn: next })
  }

  return (
    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
      <div>
        <div style={{ fontSize: 12, opacity: 0.7 }}>Command</div>
        <div style={{ fontWeight: 600 }}>{value.cmd.display_name}</div>
      </div>

      <div>
        <div style={{ fontSize: 12, opacity: 0.7 }}>BDE</div>
        <select value={value.bde?.unit_key ?? ''} onChange={(e)=>setBde(e.target.value)}>
          <option value="">{loading.BDE ? 'Loading...' : 'Select brigade'}</option>
          {bdes.map(o => <option key={o.unit_key} value={o.unit_key}>{o.display_name}</option>)}
        </select>
      </div>

      <div>
        <div style={{ fontSize: 12, opacity: 0.7 }}>BN</div>
        <select value={value.bn?.unit_key ?? ''} onChange={(e)=>setBn(e.target.value)} disabled={!value.bde}>
          <option value="">{loading.BN ? 'Loading...' : (value.bde ? 'Select battalion' : 'Select BDE first')}</option>
          {bns.map(o => <option key={o.unit_key} value={o.unit_key}>{o.display_name}</option>)}
        </select>
      </div>

      <div>
        <div style={{ fontSize: 12, opacity: 0.7 }}>CO</div>
        <select value={value.co?.unit_key ?? ''} onChange={(e)=>setCo(e.target.value)} disabled={!value.bn}>
          <option value="">{loading.CO ? 'Loading...' : (value.bn ? 'Select company' : 'Select BN first')}</option>
          {cos.map(o => <option key={o.unit_key} value={o.unit_key}>{o.display_name}</option>)}
        </select>
      </div>

      <div>
        <div style={{ fontSize: 12, opacity: 0.7 }}>Station</div>
        <select value={value.stn?.unit_key ?? ''} onChange={(e)=>setStn(e.target.value)} disabled={!value.co}>
          <option value="">{loading.STN ? 'Loading...' : (value.co ? 'Select station' : 'Select CO first')}</option>
          {stns.map(o => <option key={o.unit_key} value={o.unit_key}>{o.display_name}</option>)}
        </select>
      </div>

      <div style={{ marginLeft: 'auto', fontSize: 12, opacity: 0.8 }}>
        <span style={{ fontWeight: 600 }}>Active:</span>{' '}
        {value.stn?.display_name || value.co?.display_name || value.bn?.display_name || value.bde?.display_name || value.cmd.display_name}
      </div>
    </div>
  )
}
