import React from 'react';
import { EventPerformanceDashboard } from '../../components/EventPerformanceDashboard';
import { Card } from '../../components/shared/ui';
import { runRoiCostToEffectEngine } from '../../lib/engines';

export const ROIAnalysisPage: React.FC = () => {
	const roi = runRoiCostToEffectEngine({ spend: 132000, contracts: 147, qualifiedLeads: 610 });

	return (
		<div className="space-y-6">
			<Card title="ROI Cost-to-Effect Engine">
				<div className="grid grid-cols-1 md:grid-cols-3 gap-3">
					{roi.summaries.map((summary) => (
						<div key={summary.label} className="rounded border border-slate-700 bg-slate-900/40 px-3 py-2 text-xs text-slate-300">
							{summary.label}: {summary.value}
						</div>
					))}
				</div>
			</Card>
			<EventPerformanceDashboard />
		</div>
	);
};

export default ROIAnalysisPage;
