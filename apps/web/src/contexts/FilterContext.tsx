import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import * as orgStore from '../store/orgSelection'

const STORAGE_KEY = 'taaip.filters.v1'

type Filters = {
  unit_rsid: string
  fy: string
  qtr: string
  station?: string
}

type FilterContextValue = {
  filters: Filters
  setUnit: (unit_rsid: string) => void
  setFy: (fy: string) => void
  setQtr: (qtr: string) => void
  setStation: (s?: string) => void
}

const defaultFy = String(new Date().getFullYear())
const getDefaultQtr = () => {
  const m = new Date().getMonth() + 1
  return `Q${Math.ceil(m / 3)}`
}

const defaultFilters: Filters = {
  unit_rsid: orgStore.getMostSpecificRsid(),
  fy: defaultFy,
  qtr: getDefaultQtr(),
}

const FilterContext = createContext<FilterContextValue | null>(null)

export function FilterProvider({ children }: { children?: React.ReactNode }){
  const [filters, setFilters] = useState<Filters>(() => {
    try{
      const raw = localStorage.getItem(STORAGE_KEY)
      if(raw) return { ...defaultFilters, ...JSON.parse(raw) }
    }catch(e){}
    return defaultFilters
  })

  useEffect(()=>{
    try{ localStorage.setItem(STORAGE_KEY, JSON.stringify(filters)) }catch(e){}
  }, [filters])

  const value = useMemo(()=>({
    filters,
    setUnit: (unit_rsid: string) => {
      try{ orgStore.saveOrgSelection({ active: { rsid: unit_rsid, display_name: unit_rsid } }) }catch(e){}
      setFilters(s => ({ ...s, unit_rsid }))
    },
    setFy: (fy: string) => setFilters(s => ({ ...s, fy })),
    setQtr: (qtr: string) => setFilters(s => ({ ...s, qtr })),
    setStation: (station?: string) => setFilters(s => ({ ...s, station }))
  }), [filters])

  return <FilterContext.Provider value={value}>{children}</FilterContext.Provider>
}

export function useFilters(){
  const ctx = useContext(FilterContext)
  if(!ctx) throw new Error('useFilters must be used within FilterProvider')
  return ctx
}

export default FilterContext
