import React, { useEffect, useState } from 'react';
import { useUnitFilter } from '../../contexts/UnitFilterContext'
import { getOrgUnitsSummary } from '../../api/client'

// This selector uses the backend "units-summary" endpoint when available and
// falls back to legacy shapes. It prefers human-friendly display names and
// emits compact rsid-like values (1..4 char prefixes) so older consumers keep
// working.

const ECHELONS = [
  { code: 'USAREC', label: 'USAREC' },
  { code: 'BDE', label: 'Brigade' },
  { code: 'BN', label: 'Battalion' },
  { code: 'CO', label: 'Company' },
  { code: 'STN', label: 'Station' },
];

function parseUnitsSummary(js){
  if(!js || (!js.data && !js.brigades)) return { brigades:[], battalions:[], companies:[], stations:[] }
  const payload = js.data || js
  return {
    brigades: payload.brigades || payload.brigade || [],
    battalions: payload.battalions || payload.battalion || [],
    companies: payload.companies || payload.company || [],
    stations: payload.stations || payload.station || []
  }
}

export default function CascadingUnitSelector({ value, onChange, onApply, mode='filter', initialScope='USAREC', initialValue='' }){
  const [echelon, setEchelon] = useState((value && value.echelon) || initialScope || 'USAREC');
  const [bde, setBde] = useState((value && value.bde) || null);
  const [bn, setBn] = useState((value && value.bn) || null);
  const [co, setCo] = useState((value && value.co) || null);
  const [stn, setStn] = useState((value && value.stn) || initialValue || null);

  const [bdeOptions, setBdeOptions] = useState([]);
  const [bnOptions, setBnOptions] = useState([]);
  const [coOptions, setCoOptions] = useState([]);
  const [stnOptions, setStnOptions] = useState([]);
  const [bdeAll, setBdeAll] = useState([]);
  const [bnAll, setBnAll] = useState([]);
  const [coAll, setCoAll] = useState([]);
  const [stnAll, setStnAll] = useState([]);
  const [orgNotLoaded, setOrgNotLoaded] = useState(false);

  const { setFilter } = useUnitFilter()

  useEffect(()=>{
    // Try the v2 units summary which provides labeled lists; fall back to
    // legacy /api/org shapes by attempting both endpoints.
    async function load(){
      try{
        const js = await getOrgUnitsSummary()
        const parsed = parseUnitsSummary(js)
        const mapItem = (b) => ({ id: b.id, rsid: b.rsid, unit_key: b.unit_key || b.value || b.scope || String(b.id), parent_key: b.parent_key || null, display_name: b.display_name || b.label || b.name || String(b.id), echelon: b.echelon })
        const bdes = (parsed.brigades || []).map(mapItem)
        const bns = (parsed.battalions || []).map(mapItem)
        const cos = (parsed.companies || []).map(mapItem)
        const stns = (parsed.stations || []).map(mapItem)
        setBdeOptions(bdes);
        setBnOptions(bns);
        setCoOptions(cos);
        setStnOptions(stns);
        setBdeAll(bdes);
        setBnAll(bns);
        setCoAll(cos);
        setStnAll(stns);
      }catch(e){
        // graceful fallback: mark org not loaded so UI shows import hint
        setOrgNotLoaded(true)
      }
    }
    load()
  },[])

  // When a parent changes, filter the dependent lists by the parent prefix.
  useEffect(()=>{
    if (!bde){ setBn(null); setCo(null); setStn(null); setBnOptions(bnAll); setCoOptions(coAll); setStnOptions(stnAll); return }
    // bde is stored as an object; filter children by rsid
    setBnOptions(bnAll.filter(x => x.parent_key === (bde.rsid || bde.unit_key)))
    setCoOptions([])
    setStnOptions([])
    setBn(null); setCo(null); setStn(null)
  },[bde, bnAll, coAll, stnAll])

  useEffect(()=>{
    if (!bn){ setCo(null); setStn(null); setCoOptions(coAll); setStnOptions(stnAll); return }
    setCoOptions(coAll.filter(x => x.parent_key === (bn.rsid || bn.unit_key)))
    setStnOptions([])
    setCo(null); setStn(null)
  },[bn, coAll, stnAll])

  useEffect(()=>{
    if (!co){ setStn(null); setStnOptions(stnAll); return }
    setStnOptions(stnAll.filter(x => x.parent_key === (co.rsid || co.unit_key)))
    setStn(null)
  },[co, stnAll])

  useEffect(()=>{ if(onChange) onChange({echelon,bde,bn,co,stn}) }, [echelon,bde,bn,co,stn])

  function doApply(){
    if (onApply){
      let scopeCode = echelon;
      let scopeValue = null;
      if (echelon === 'BDE') scopeValue = bde ? bde.unit_key : null;
      if (echelon === 'BN') scopeValue = bn ? bn.unit_key : (bde ? bde.unit_key : null);
      if (echelon === 'CO') scopeValue = co ? co.unit_key : (bn ? bn.unit_key : (bde ? bde.unit_key : null));
      if (echelon === 'STN') scopeValue = stn ? stn.unit_key : (co ? co.unit_key : (bn ? bn.unit_key : (bde ? bde.unit_key : null)));
      onApply(scopeCode, scopeValue);
    }
  }

  function doApplyAndPersist(){
    if (onApply){ doApply() }
    // persist selected unit_key
    const selected_unit_key = (stn && stn.unit_key) || (co && co.unit_key) || (bn && bn.unit_key) || (bde && bde.unit_key) || null
    const uf = { echelon, unit_key: selected_unit_key }
    try{ setFilter(uf) }catch(e){}

    // update URL query params so other pages (dashboard filters) pick up selection
    try{
      const u = new URL(window.location.href)
      if (selected_unit_key) u.searchParams.set('unit_key', selected_unit_key)
      else u.searchParams.delete('unit_key')
      if (echelon) u.searchParams.set('echelon', echelon)
      else u.searchParams.delete('echelon')
      window.history.replaceState({}, '', u.toString())
    }catch(e){}
  }

  const compact = mode === 'filter';
  const containerStyle = { display:'flex', gap:8, alignItems:'center', background:'transparent', padding: compact ? 6 : 10, borderRadius:4 };
  const selectStyle = { background:'#FFFFFF', color:'#0F1724', borderRadius:4, padding:'6px 8px', border:'1px solid rgba(15,23,36,0.06)' };

  if (orgNotLoaded) {
    return (<div style={containerStyle}><div style={{color:'#0F1724'}}>Org data not loaded — <a href="/data-hub" style={{color:'#FFB900'}}>Go to Data Hub</a></div></div>)
  }

  return (
    <div style={containerStyle}>
      <select style={selectStyle} value={echelon} onChange={e=>{ setEchelon(e.target.value); setBde(null); setBn(null); setCo(null); setStn(null); }}>
        {ECHELONS.map(ec=> <option key={ec.code} value={ec.code}>{ec.label}</option>)}
      </select>

      {(echelon === 'BDE' || echelon === 'BN' || echelon === 'CO' || echelon === 'STN') && (
        <select style={selectStyle} value={bde?JSON.stringify(bde):''} onChange={e=>setBde(e.target.value?JSON.parse(e.target.value):null)}>
          <option value=''>Select Brigade</option>
          {bdeOptions.map(b=> <option key={b.id} value={JSON.stringify(b)}>{b.display_name}</option>)}
        </select>
      )}

      {(echelon === 'BN' || echelon === 'CO' || echelon === 'STN') && (
        <select style={selectStyle} value={bn?JSON.stringify(bn):''} onChange={e=>setBn(e.target.value?JSON.parse(e.target.value):null)}>
          <option value=''>Select Battalion</option>
          {bnOptions.map(b=> <option key={b.id} value={JSON.stringify(b)}>{b.display_name}</option>)}
        </select>
      )}

      {(echelon === 'CO' || echelon === 'STN') && (
        <select style={selectStyle} value={co?JSON.stringify(co):''} onChange={e=>setCo(e.target.value?JSON.parse(e.target.value):null)}>
          <option value=''>Select Company</option>
          {coOptions.map(c=> <option key={c.id} value={JSON.stringify(c)}>{c.display_name}</option>)}
        </select>
      )}

      {echelon === 'STN' && (
        <select style={selectStyle} value={stn?JSON.stringify(stn):''} onChange={e=>setStn(e.target.value?JSON.parse(e.target.value):null)}>
          <option value=''>Select Station</option>
          {stnOptions.map(s=> <option key={s.id} value={JSON.stringify(s)}>{s.display_name}</option>)}
        </select>
      )}

      <button onClick={doApplyAndPersist} style={{marginLeft:8, padding:'6px 10px', borderRadius:4}}>Apply</button>
    </div>
  )
}
