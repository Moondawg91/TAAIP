import React from 'react';
import { ScoreboardPage } from '../../components/ScoreboardPage';
import { Card, Table } from '../../components/shared/ui';
import { runPerformanceForecastingEngine } from '../../lib/engines';

export const PerformancePage: React.FC = () => {
	const forecast = runPerformanceForecastingEngine([
		{ period: 'FY26-Q1', contracts: 122 },
		{ period: 'FY26-Q2', contracts: 131 },
		{ period: 'FY26-Q3', contracts: 139 },
	]);

	return (
		<div className="space-y-6">
			<Card title="Performance Forecasting Engine">
				<div className="grid grid-cols-2 gap-3 mb-3">
					{forecast.summaries.map((summary) => (
						<div key={summary.label} className="rounded border border-slate-700 bg-slate-900/40 px-3 py-2 text-xs text-slate-300">
							{summary.label}: {summary.value}
						</div>
					))}
				</div>
				<Table
					rows={forecast.forecast}
					columns={[
						{ key: 'period', header: 'Forecast Period' },
						{ key: 'projectedContracts', header: 'Projected Contracts' },
					]}
					getRowId={(row) => row.period}
				/>
			</Card>
			<ScoreboardPage />
		</div>
	);
};

export default PerformancePage;
