import React, { useMemo, useState } from 'react';
import { Card, Table } from '../../components/shared/ui';

type HomeSection = 'Flash Updates' | 'TAWO of the Month' | 'WOPD Updates' | 'Proponent Updates';

type HomeItem = {
	id: string;
	section: HomeSection;
	title: string;
	date: string;
	source: string;
	summary: string;
	related: string;
	affectedProcesses: string;
};

const HOME_ITEMS: HomeItem[] = [
	{
		id: 'flash-1',
		section: 'Flash Updates',
		title: 'EMM lead capture schema update',
		date: '2026-05-10',
		source: 'EMM',
		summary: 'Lead event payload now includes extended QR attribution fields.',
		related: 'EMM Integration Notice 26-05',
		affectedProcesses: 'Field Activities, Funnel Analysis, ROI Analysis',
	},
	{
		id: 'tawo-1',
		section: 'TAWO of the Month',
		title: 'SFC Morgan - BN 1A',
		date: '2026-05-01',
		source: 'BN Command Team',
		summary: 'Recognized for sustained mission pacing and doctrinal product quality.',
		related: 'Command Recognition Memo',
		affectedProcesses: 'Command Center, Performance',
	},
	{
		id: 'wopd-1',
		section: 'WOPD Updates',
		title: 'WOPD Session: Funnel bottleneck diagnostics',
		date: '2026-05-15',
		source: '420T Development Cell',
		summary: 'Session on qualification-stage delay analysis and corrective actions.',
		related: 'WOPD Calendar Entry',
		affectedProcesses: 'Funnel Analysis, TWG',
	},
	{
		id: 'prop-1',
		section: 'Proponent Updates',
		title: 'SRP synchronization guidance revision',
		date: '2026-05-08',
		source: 'USAREC Proponent',
		summary: 'Updated SRP alignment language for BN and BDE uploaded plan checks.',
		related: 'USAREC Message 26-117',
		affectedProcesses: 'School Intelligence, TWG, Targeting Board',
	},
];

interface Props { onNavigate: (tab: string) => void }

export const HomePage: React.FC<Props> = () => {
	const [selectedId, setSelectedId] = useState<string>('flash-1');

	const selected = useMemo(
		() => HOME_ITEMS.find((x) => x.id === selectedId) ?? null,
		[selectedId],
	);

	return (
		<div className="space-y-6">
			<Card title="Home">
				<p className="text-sm text-slate-300">
					Central command hub for essential updates only. Select any item to open full details, source reference, notes, and affected workflows.
				</p>
			</Card>

			<div className="grid grid-cols-1 xl:grid-cols-[2fr_1fr] gap-6">
				<Card title="Operational Updates">
					<Table
						rows={HOME_ITEMS}
						columns={[
							{ key: 'section', header: 'Section' },
							{ key: 'title', header: 'Title' },
							{ key: 'date', header: 'Date' },
							{ key: 'source', header: 'Source' },
						]}
						getRowId={(row) => row.id}
						onRowClick={(row) => setSelectedId(row.id)}
						selectedRow={selected ?? undefined}
					/>
				</Card>

				<Card title="Detail Drawer">
					{selected ? (
						<div className="space-y-3 text-sm text-slate-300">
							<div><span className="text-slate-500">Section:</span> {selected.section}</div>
							<div><span className="text-slate-500">Title:</span> {selected.title}</div>
							<div><span className="text-slate-500">Date:</span> {selected.date}</div>
							<div><span className="text-slate-500">Source:</span> {selected.source}</div>
							<div><span className="text-slate-500">Summary:</span> {selected.summary}</div>
							<div><span className="text-slate-500">Related Document:</span> {selected.related}</div>
							<div><span className="text-slate-500">Affected Processes:</span> {selected.affectedProcesses}</div>
						</div>
					) : (
						<p className="text-sm text-slate-500">Select an item for full details.</p>
					)}
				</Card>
			</div>
		</div>
	);
};

export default HomePage;
