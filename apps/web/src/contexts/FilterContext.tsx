import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import * as orgStore from '../store/orgSelection'

type Filters = {
  unit_rsid?: string
  fy?: number | string
  qtr?: string
  rsm_month?: string
  station?: string
  compare?: string
}

type FilterContextValue = {
  filters: Filters
  setUnit: (unit_rsid: string) => void
  setFy: (fy: number | string) => void
  setQtr: (qtr: string) => void
  setRsmMonth: (month:string) => void
  setStation: (s?: string) => void
}

import dateScopes from '../utils/dateScopes'

const STORAGE_KEY = 'taaip.filters.v1'

const defaultFyNum = dateScopes.getCurrentFY()
const defaultQ = dateScopes.getFYQuarter()

// Default global filters per requirements
const defaultFilters: Filters = {
  unit_rsid: 'USAREC',
  fy: defaultFyNum,
  qtr: `Q${String(defaultQ.qtr)}`,
  rsm_month: dateScopes.getCurrentRsmMonth(),
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

  // track whether user explicitly set month for the current fy/qtr
  const userSetKeyRef = React.useRef<string | null>(null)

  useEffect(()=>{
    try{ localStorage.setItem(STORAGE_KEY, JSON.stringify(filters)) }catch(e){}
  }, [filters])

  function currentUserSetKey(fy:any, qtr:any){ return `${fy || filters.fy}-${qtr || filters.qtr}` }

  const value = useMemo(()=>({
    filters,
    setUnit: (unit_rsid: string) => {
      try{ orgStore.saveOrgSelection({ active: { rsid: unit_rsid, display_name: unit_rsid } }) }catch(e){}
      setFilters(s => ({ ...s, unit_rsid }))
    },
    setFy: (fy: number | string) => {
      setFilters(s => {
        const newFy = Number(fy)
        // determine qtr default if missing or unchanged
        let newQtr = s.qtr
        if (!newQtr){
          const defaultForNow = dateScopes.getFYQuarter()
          newQtr = (defaultForNow.fy === newFy) ? `Q${defaultForNow.qtr}` : 'Q1'
        }
        const key = currentUserSetKey(newFy, newQtr)
        const userHadSet = userSetKeyRef.current === key
        const newRsm = userHadSet && s.rsm_month ? s.rsm_month : dateScopes.getQuarterStartMonth(Number(newFy), Number(String(newQtr).replace(/^Q/,'')) as 1|2|3|4)
        if (!userHadSet) userSetKeyRef.current = null
        return { ...s, fy: newFy, qtr: newQtr, rsm_month: newRsm }
      })
    },
    setQtr: (qtr: string) => {
      setFilters(s => {
        const newQ = qtr
        const fyNum = Number(s.fy || defaultFyNum)
        const key = currentUserSetKey(fyNum, newQ)
        const userHadSet = userSetKeyRef.current === key
        const newRsm = userHadSet && s.rsm_month ? s.rsm_month : dateScopes.getQuarterStartMonth(fyNum, Number(String(newQ).replace(/^Q/,'') ) as 1|2|3|4)
        if (!userHadSet) userSetKeyRef.current = null
        return { ...s, qtr: newQ, rsm_month: newRsm }
      })
    },
    setRsmMonth: (month:string) => {
      setFilters(s => {
        const key = currentUserSetKey(s.fy, s.qtr)
        userSetKeyRef.current = key
        return { ...s, rsm_month: month }
      })
    },
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
