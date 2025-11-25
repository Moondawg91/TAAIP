import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { PowerBIEmbed } from 'powerbi-client-react';
import { models } from 'powerbi-client';

interface PowerBIReportEmbedProps {
  reportId: string;
  title?: string;
  className?: string;
}

export const PowerBIReportEmbed: React.FC<PowerBIReportEmbedProps> = ({ reportId, title, className }) => {
  const [embedToken, setEmbedToken] = useState<string | null>(null);
  const [embedUrl, setEmbedUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function fetchToken() {
      try {
        setError(null);
        const resp = await axios.post('/api/powerbi/embedToken', { reportId });
        if (!mounted) return;
        setEmbedToken(resp.data.embedToken);
        setEmbedUrl(resp.data.embedUrl);
      } catch (e: any) {
        console.error('Power BI embed error', e?.response?.data || e.message);
        // Show informational message instead of error - Power BI requires GCC credentials
        setError('Power BI integration requires Government Community Cloud (GCC) credentials. Contact your system administrator to configure Power BI access for live reports.');
      }
    }
    fetchToken();
    return () => { mounted = false; };
  }, [reportId]);

  if (error) {
    return (
      <div className="rounded-xl border-2 border-blue-200 bg-blue-50 p-8">
        <div className="max-w-2xl mx-auto text-center">
          <div className="bg-blue-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-blue-900 mb-2">Power BI Configuration Required</h3>
          <p className="text-blue-700 mb-4">{error}</p>
          <div className="bg-white rounded-lg p-4 text-left border border-blue-200">
            <p className="text-sm text-gray-700 font-semibold mb-2">To enable Power BI reports:</p>
            <ol className="text-sm text-gray-600 space-y-1 list-decimal list-inside">
              <li>Configure Azure AD App Registration for Power BI Embedded</li>
              <li>Add GCC tenant credentials to backend server</li>
              <li>Grant Power BI workspace permissions</li>
              <li>Restart application to load embedded reports</li>
            </ol>
          </div>
          <p className="text-xs text-gray-500 mt-4">Alternative: Use Universal Data Import to manually upload Power BI data exports</p>
        </div>
      </div>
    );
  }

  if (!embedToken || !embedUrl) {
    return <div className="p-6 text-gray-600">Loading Power BI report...</div>;
  }

  const config: models.IEmbedConfiguration = {
    type: 'report',
    id: reportId,
    embedUrl,
    accessToken: embedToken,
    tokenType: models.TokenType.Embed,
    settings: {
      panes: { filters: { expanded: false, visible: false } },
      navContentPaneEnabled: true,
    }
  };

  return (
    <div className={className}>
      {title && <h3 className="text-lg font-bold mb-3">{title}</h3>}
      <div className="w-full h-[720px] border rounded-lg overflow-hidden bg-white">
        <PowerBIEmbed
          embedConfig={config}
          eventHandlers={new Map<string, any>([
            ['loaded', () => console.log('Power BI report loaded')],
            ['error', (e: any) => console.error('Power BI error', e)]
          ])}
        />
      </div>
    </div>
  );
};

interface PowerBIBundleProps {
  reportIds: string[];
}

export const PowerBIBundle: React.FC<PowerBIBundleProps> = ({ reportIds }) => {
  return (
    <div className="space-y-8">
      {reportIds.map((id, idx) => (
        <PowerBIReportEmbed key={id} reportId={id} title={`Power BI Report ${idx + 1}`} />
      ))}
    </div>
  );
};

export default PowerBIBundle;
