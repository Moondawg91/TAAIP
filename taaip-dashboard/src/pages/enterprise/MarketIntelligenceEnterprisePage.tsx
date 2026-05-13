import React from 'react';
import { MarketIntelligencePage } from '../../components/MarketIntelligencePage';
import { Card } from '../../components/shared/ui';
import { PLACEHOLDER_MARKET_DATA, runMarketIntelligenceEngine } from '../../lib/engines';
import { usePageExport } from '../../lib/export';

interface Props {
	onNavigate: (tab: string) => void;
}

const MODULES = [
	{ id: 'market-intelligence', label: 'Market Intelligence Overview', detail: 'Operational environment baseline and alerts.' },
	{ id: 'dod-market-share', label: 'DoD Market Share', detail: 'Army vs component competitors across assigned markets.' },
	{ id: 'segmentation', label: 'Segmentation', detail: 'PRIZM, CBSA, D3AE, and F3A analysis.' },
	{ id: 'reserve-alignment', label: 'Reserve Alignment', detail: 'Reserve opportunity vs contract mix alignment.' },
	{ id: 'market-potential', label: 'Market Potential', detail: 'Potential remaining and achievable opportunities.' },
	{ id: 'out-of-area-analysis', label: 'Out-of-Area Analysis', detail: 'Leakage and displacement outside assigned AO.' },
	{ id: 'school-intelligence', label: 'School Intelligence', detail: 'SRP and school-level recruiting intelligence.' },
];

export const MarketIntelligenceEnterprisePage: React.FC<Props> = ({ onNavigate }) => {
	const engine = runMarketIntelligenceEngine(PLACEHOLDER_MARKET_DATA);
	const { exportCommanderBrief } = usePageExport('market-intelligence', 'Market Intelligence');

	return (
		<div className="space-y-6">
			<Card title="Market Intelligence Module Hub">
				<div className="mb-3 flex flex-wrap items-center gap-2">
					<button
						onClick={() => {
							void exportCommanderBrief({
								summary: 'Market intelligence operational posture generated for command review.',
								riskItems: ['Out-of-area leakage', 'Reserve vacancy mismatch'],
								actions: ['Rebalance targeting', 'Prioritize high-potential ZIP clusters'],
							});
						}}
						className="rounded border border-[#1D3A5C] bg-[#0B1F3A] px-3 py-1.5 text-xs text-slate-200 hover:bg-[#122A4A]"
					>
						Export Intelligence Brief
					</button>
					{engine.summaries.map((summary) => (
						<span key={summary.label} className="rounded border border-slate-700 bg-slate-900/40 px-2 py-1 text-xs text-slate-300">
							{summary.label}: {summary.value}
						</span>
					))}
				</div>
				<div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
					{MODULES.map((module) => (
						<button
							key={module.id}
							onClick={() => onNavigate(module.id)}
							className="text-left px-4 py-3 rounded border border-slate-700 hover:bg-slate-900/40"
						>
							<div className="text-sm font-semibold text-slate-200">{module.label}</div>
							<div className="text-xs text-slate-400 mt-1">{module.detail}</div>
						</button>
					))}
				</div>
			</Card>
			<MarketIntelligencePage />
		</div>
	);
};

export default MarketIntelligenceEnterprisePage;
