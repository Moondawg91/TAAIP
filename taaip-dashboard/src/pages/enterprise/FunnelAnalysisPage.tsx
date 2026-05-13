import React from 'react';
import { RecruitingFunnelDashboard } from '../../components/RecruitingFunnelDashboard';
import { Card, Table } from '../../components/shared/ui';
import { runFunnelProgressionEngine } from '../../lib/engines';

export const FunnelAnalysisPage: React.FC = () => {
	const output = runFunnelProgressionEngine({ leads: 420, appointments: 214, interviews: 119, contracts: 47 });

	return (
		<div className="space-y-6">
			<Card title="Funnel Progression Engine">
				<div className="grid grid-cols-2 gap-3 mb-3">
					{output.summaries.map((summary) => (
						<div key={summary.label} className="rounded border border-slate-700 bg-slate-900/40 px-3 py-2 text-xs text-slate-300">
							{summary.label}: {summary.value}
						</div>
					))}
				</div>
				<Table
					rows={output.conversionRates}
					columns={[
						{ key: 'stage', header: 'Stage' },
						{ key: 'rate', header: 'Conversion %' },
					]}
					getRowId={(row) => row.stage}
				/>
			</Card>
			<RecruitingFunnelDashboard />
		</div>
	);
};

export default FunnelAnalysisPage;
