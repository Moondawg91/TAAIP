/* © 2026 TAAIP. Copyright pending. */
import React, {useState} from 'react';

const SCOPES = ['USAREC','BDE','BN','CO','STN'];

export default function ScopePicker({onApply, initialScope='USAREC', initialValue=''}){
  const [scope, setScope] = useState(initialScope);
  const [value, setValue] = useState(initialValue);

  return (
    <div className="scope-picker">
      <select value={scope} onChange={e=>setScope(e.target.value)}>
        {SCOPES.map(s=> <option key={s} value={s}>{s}</option>)}
      </select>
      <input placeholder="value (prefix or rsid)" value={value} onChange={e=>setValue(e.target.value)} />
      <button onClick={()=>onApply(scope, value)}>Apply</button>
    </div>
  );
}
