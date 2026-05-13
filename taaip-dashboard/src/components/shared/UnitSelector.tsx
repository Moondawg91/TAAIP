import React from 'react';
import { useRsidStore } from '../../state/rsidStore';
import { useUnitScope } from '../../hooks/useUnitScope';

export const UnitSelector: React.FC = () => {
  const { rsid, setRsid } = useRsidStore();
  const { isLoading, options } = useUnitScope(rsid);

  return (
    <div className="space-y-1">
      <label className="text-[10px] uppercase tracking-[0.08em] text-[#94A3B8]">Unit Scope</label>
      <select
        value={rsid}
        onChange={(event) => setRsid(event.target.value)}
        className="w-full rounded-md border border-[#1D3A5C] bg-[#081B33] px-2 py-1.5 text-xs text-[#F8FAFC]"
      >
        {isLoading ? <option value={rsid}>{rsid} (loading...)</option> : null}
        {(options.length > 0 ? options : [rsid]).map((option) => (
          <option key={option} value={option}>{option}</option>
        ))}
      </select>
    </div>
  );
};
