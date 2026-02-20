/* © 2026 TAAIP. Copyright pending. */
import React, {useState} from 'react';

const SCOPES = ['USAREC','BDE','BN','CO','STN'];

export default function ScopePicker({onApply, initialScope='USAREC', initialValue=''}){
  const [scope, setScope] = useState(initialScope);
  const [value, setValue] = useState(initialValue);

  return (
    <div className="echelon-picker">
      <label style={{marginRight:8, color:'#EDEDF7'}}>Echelon</label>
      <select value={scope} onChange={e=>setScope(e.target.value)}>
        {SCOPES.map(s=> <option key={s} value={s}>{s}</option>)}
      </select>
      <input placeholder="unit (prefix or rsid)" value={value} onChange={e=>setValue(e.target.value)} style={{marginLeft:8}} />
      <button onClick={()=>onApply(scope, value)} style={{marginLeft:8}}>Apply</button>
    </div>
  );
}
