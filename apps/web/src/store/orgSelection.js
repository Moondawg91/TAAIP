// Helper to load/save normalized unit selection to localStorage
// Primary storage contract: 'taaip.unitSelection.v1' (new canonical key)
// Legacy keys kept for backwards compatibility: 'taaip_org_selection_v1', 'taaip:selected_unit'
const LS_KEY = 'taaip.unitSelection.v1'
const LEGACY_LS_KEY = 'taaip:selected_unit'
const ALT_LEGACY_KEY = 'taaip_org_selection_v1'

function defaultSelection(){
  return {
    root_rsid: 'USAREC',
    bde: null,
    bn: null,
    co: null,
    stn: null,
    // `active` is the deepest selected level object { rsid, display_name, echelon }
    active: { rsid: 'USAREC', display_name: 'USAREC', echelon: 'CMD' },
    // legacy compatibility
    effective_rsid: 'USAREC'
  }
}

export function normalizeOrgSelection(sel) {
  if (!sel || typeof sel !== 'object') return defaultSelection()
  const out = Object.assign(defaultSelection(), sel)
  // ensure hierarchical consistency
  if (!out.bde) { out.bn = null; out.co = null; out.stn = null }
  if (!out.bn) { out.co = null; out.stn = null }
  if (!out.co) { out.stn = null }
  // ensure root
  if (!out.root_rsid) out.root_rsid = 'USAREC'

  // compute active as deepest
  out.active = out.stn || out.co || out.bn || out.bde || { rsid: out.root_rsid, display_name: out.root_rsid, echelon: 'CMD' }
  out.effective_rsid = out.active && out.active.rsid ? out.active.rsid : out.root_rsid
  return out
}

export function loadOrgSelection() {
  try {
    let raw = localStorage.getItem(LS_KEY)
    if (!raw) raw = localStorage.getItem(ALT_LEGACY_KEY)
    if (!raw) raw = localStorage.getItem(LEGACY_LS_KEY)
    if (!raw) return normalizeOrgSelection(null)
    const parsed = JSON.parse(raw)
    return normalizeOrgSelection(parsed)
  } catch (e) {
    return normalizeOrgSelection(null)
  }
}

export function saveOrgSelection(sel) {
  try {
    const normalized = normalizeOrgSelection(sel)
    const serialized = JSON.stringify(normalized)
    // write new key and update legacy key for backward compatibility
    try { localStorage.setItem(LS_KEY, serialized) } catch(e) {}
    try { localStorage.setItem(ALT_LEGACY_KEY, serialized) } catch(e) {}
    try { localStorage.setItem(LEGACY_LS_KEY, serialized) } catch(e) {}
    return normalized
  } catch (e) {
    return normalizeOrgSelection(sel)
  }
}

export function getSelection(){
  return loadOrgSelection()
}

export function setSelection(next){
  return saveOrgSelection(next)
}

// Clear dependent lower levels when a selection at `level` changes.
// level: one of 'bde','bn','co','stn'
export function clearLowerLevels(sel, level){
  const out = Object.assign({}, sel)
  if (level === 'bde') { out.bn = null; out.co = null; out.stn = null }
  if (level === 'bn') { out.co = null; out.stn = null }
  if (level === 'co') { out.stn = null }
  // recompute active
  const normalized = normalizeOrgSelection(out)
  saveOrgSelection(normalized)
  return normalized
}

export function getMostSpecificRsid(sel){
  if (!sel) sel = loadOrgSelection()
  return (sel.active && sel.active.rsid) || sel.root_rsid || 'USAREC'
}

export default { loadOrgSelection, saveOrgSelection, normalizeOrgSelection, getSelection, setSelection, clearLowerLevels, getMostSpecificRsid }
