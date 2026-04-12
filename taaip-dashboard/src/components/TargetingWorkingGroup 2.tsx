import React, { useState, useEffect } from 'react';

type AARReport = {
  event_id: string;
  event_name: string;
  date: string;
  status: string;
  due_date?: string;
  hours_since_event?: number;
  submitted_by?: string | null;
}

export const TargetingWorkingGroup: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [aarReports, setAARReports] = useState<AARReport[]>([]);
  const [dataAsOf, setDataAsOf] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [missionRes] = await Promise.all([
          fetch('/api/rollups/command/mission-assessment').then(r => r.ok ? r.json() : {})
        ]) as any;

        const priorities = (missionRes && (missionRes as any).priorities) ? (missionRes as any).priorities : [];
        const asOf = (missionRes && (missionRes as any).data_as_of) ? (missionRes as any).data_as_of : null;
        const aar = priorities.map((p: any, i: number) => ({
          event_id: p.id || `p${i}`,
          event_name: p.title || p.id || 'priority',
          date: asOf || new Date().toISOString(),
          status: p.status || 'unknown',
          due_date: '',
          hours_since_event: 0,
          submitted_by: null
        }));
        setAARReports(aar);
        setDataAsOf(asOf);
      } catch (e) {
        console.error('TWG load error', e);
        setAARReports([]);
        setDataAsOf(null);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div className="twg-root p-4">
      <h2 className="text-lg font-semibold">Targeting Working Group (Live)</h2>
      <div className="text-sm text-gray-500">Data as of: {dataAsOf || 'n/a'}</div>
      {loading ? (
        <div className="mt-4">Loading...</div>
      ) : (
        <div className="mt-4">
          {aarReports.length === 0 ? (
            <div>No live priorities found.</div>
          ) : (
            <ul>
              {aarReports.map(a => (
                <li key={a.event_id} className="py-2 border-b">
                  <div className="font-medium">{a.event_name}</div>
                  <div className="text-xs text-gray-600">{a.date} • {a.status}</div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
