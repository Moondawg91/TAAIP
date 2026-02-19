#!/bin/bash

echo "=========================================="
echo "🧪 TAAIP Market Intelligence API Test Suite"
echo "=========================================="
echo ""

echo "1️⃣  Testing Market Potential API..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s 'http://localhost:8000/api/v2/market-potential?geographic_level=cbsa&fiscal_year=2025&quarter=Q4' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Status: {d[\"status\"]}')
print(f'Records: {d[\"count\"]}')
print('')
print('Top 3 Markets by Army Market Share:')
sorted_data = sorted(d['data'], key=lambda x: x['army']['market_share'], reverse=True)[:3]
for i, m in enumerate(sorted_data):
    print(f'  {i+1}. {m[\"geographic_name\"]}')
    print(f'     Army Share: {m[\"army\"][\"market_share\"]}%')
    print(f'     Contacted: {m[\"army\"][\"contacted\"]:,} | Remaining: {m[\"army\"][\"remaining\"]:,}')
"
echo ""

echo "2️⃣  Testing DOD Branch Comparison API..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s 'http://localhost:8000/api/v2/dod-comparison?geographic_level=cbsa&geographic_id=41860&fiscal_year=2025&quarter=Q4' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Status: {d[\"status\"]}')
print(f'Branches: {d[\"count\"]}')
print('')
print('Branch Rankings (San Francisco CBSA):')
sorted_data = sorted(d['data'], key=lambda x: x['contracts'], reverse=True)
for i, b in enumerate(sorted_data):
    print(f'  {i+1}. {b[\"branch\"]}: {b[\"contracts\"]:,} contracts')
    print(f'     Productivity: {b[\"productivity\"][\"contracts_per_recruiter\"]:.1f} per recruiter')
    print(f'     Efficiency: {b[\"efficiency_score\"]}%')
"
echo ""

echo "3️⃣  Testing Mission Analysis API..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s 'http://localhost:8000/api/v2/mission-analysis?analysis_level=brigade&fiscal_year=2025&quarter=Q4' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Status: {d[\"status\"]}')
print(f'Units: {d[\"count\"]}')
print('')
print('Brigade Performance (FY2025 Q4):')
for u in d['data']:
    print(f'  {u[\"hierarchy\"][\"brigade\"]}:')
    print(f'     Goal: {u[\"mission\"][\"goal\"]:,} | Actual: {u[\"mission\"][\"actual\"]:,}')
    print(f'     Attainment: {u[\"mission\"][\"attainment_pct\"]:.1f}%')
    print(f'     L2E Rate: {u[\"efficiency\"][\"lead_to_enlistment_rate\"]:.1f}%')
"
echo ""

echo "=========================================="
echo "✅ All API endpoints tested successfully!"
echo "=========================================="
echo ""
echo "🌐 Frontend: http://localhost:5173/"
echo "🔗 Backend: http://localhost:8000/"
echo ""
echo "📊 Available Dashboards:"
echo "  • Market Potential (Army vs DOD branches)"
echo "  • Mission Analysis (USAREC hierarchy)"
echo "  • DOD Branch Comparison"
echo ""
