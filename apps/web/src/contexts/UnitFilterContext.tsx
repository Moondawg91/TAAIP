import React, { createContext, useContext, useState, useEffect } from 'react'

type UnitFilter = {
  echelon?: string | null
  unit_code?: string | null
  rsid_prefix?: string | null
  station_rsid?: string | null
}

type UnitFilterCtx = { filter: UnitFilter; setFilter: (f: UnitFilter)=>void }
const Ctx = createContext<UnitFilterCtx>({ filter: {}, setFilter: ()=>{} })

export function UnitFilterProvider({ children }: { children: React.ReactNode }){
  const [filter, setFilter] = useState<UnitFilter>(()=>{
    try{ const raw = localStorage.getItem('taaip_unit_filter'); return raw ? JSON.parse(raw) : {} }catch{ return {} }
  })
  useEffect(()=>{ try{ localStorage.setItem('taaip_unit_filter', JSON.stringify(filter)) }catch{} }, [filter])
  return <Ctx.Provider value={{ filter, setFilter }}>{children}</Ctx.Provider>
}

export function useUnitFilter(){ return useContext(Ctx) }

export default Ctx
