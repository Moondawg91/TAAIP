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
        setError('Unable to fetch Power BI embed token. Ensure server credentials are configured.');
      }
    }
    fetchToken();
    return () => { mounted = false; };
  }, [reportId]);

  if (error) {
    return <div className="rounded-md border border-red-200 bg-red-50 p-4 text-red-700">{error}</div>;
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
