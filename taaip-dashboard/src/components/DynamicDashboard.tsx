import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, 
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ScatterChart, Scatter, AreaChart, Area, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import { 
  TrendingUp, Calendar, MapPin, Users, DollarSign, Target,
  Grid, List, Map as MapIcon, Activity, AlertCircle, CheckCircle,
  Clock, Hash, Percent, Eye
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface DataField {
  name: string;
  type: 'number' | 'string' | 'date' | 'boolean';
  unique_count: number;
  sample_values: any[];
}

interface DynamicDashboardProps {
  dataType: 'events' | 'projects' | 'leads' | 'custom';
  tableName?: string;
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316'];

export const DynamicDashboard: React.FC<DynamicDashboardProps> = ({ dataType, tableName }) => {
  const [data, setData] = useState<any[]>([]);
  const [fields, setFields] = useState<DataField[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'cards'>('grid');
  const [selectedVisuals, setSelectedVisuals] = useState<string[]>([]);

  useEffect(() => {
    fetchData();
  }, [dataType, tableName]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const endpoint = tableName ? `/api/v2/custom/${tableName}` : `/api/v2/${dataType}`;
      const response = await fetch(`${API_BASE}${endpoint}`);
      const result = await response.json();
      
      setData(result.data || result);
      analyzeFields(result.data || result);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const analyzeFields = (data: any[]) => {
    if (!data || data.length === 0) return;
    
    const fieldAnalysis: DataField[] = Object.keys(data[0]).map(key => {
      const values = data.map(item => item[key]).filter(v => v !== null && v !== undefined);
      const uniqueValues = [...new Set(values)];
      
      // Determine field type
      let type: 'number' | 'string' | 'date' | 'boolean' = 'string';
      if (typeof values[0] === 'number') type = 'number';
      else if (typeof values[0] === 'boolean') type = 'boolean';
      else if (key.includes('date') || key.includes('_at')) type = 'date';
      
      return {
        name: key,
        type,
        unique_count: uniqueValues.length,
        sample_values: uniqueValues.slice(0, 5)
      };
    });
    
    setFields(fieldAnalysis);
  };

  // Auto-generate appropriate visualizations
  const generateVisualizations = () => {
    const visuals: JSX.Element[] = [];
    
    // Find numeric fields for charts
    const numericFields = fields.filter(f => f.type === 'number');
    const categoryFields = fields.filter(f => f.type === 'string' && f.unique_count < 20);
    const dateFields = fields.filter(f => f.type === 'date');
    
    // 1. KPI Cards for key metrics
    if (numericFields.length > 0) {
      visuals.push(
        <div key="kpi-cards" className="col-span-full grid grid-cols-2 md:grid-cols-4 gap-4">
          {numericFields.slice(0, 4).map((field, idx) => {
            const total = data.reduce((sum, item) => sum + (parseFloat(item[field.name]) || 0), 0);
            const avg = total / data.length;
            const max = Math.max(...data.map(item => parseFloat(item[field.name]) || 0));
            
            return (
              <div key={field.name} className="bg-white p-6 rounded-lg shadow-md border-l-4" 
                   style={{borderColor: COLORS[idx % COLORS.length]}}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-600 uppercase">{field.name.replace(/_/g, ' ')}</span>
                  <DollarSign className="w-5 h-5 text-gray-400" />
                </div>
                <div className="text-3xl font-bold text-gray-900">{total.toLocaleString()}</div>
                <div className="text-sm text-gray-500 mt-1">
                  Avg: {avg.toFixed(2)} | Max: {max.toLocaleString()}
                </div>
              </div>
            );
          })}
        </div>
      );
    }
    
    // 2. Bar Chart for categorical breakdown
    if (categoryFields.length > 0 && numericFields.length > 0) {
      const categoryField = categoryFields[0];
      const valueField = numericFields[0];
      
      const chartData = Object.entries(
        data.reduce((acc, item) => {
          const cat = item[categoryField.name] || 'Unknown';
          acc[cat] = (acc[cat] || 0) + (parseFloat(item[valueField.name]) || 0);
          return acc;
        }, {} as Record<string, number>)
      ).map(([name, value]) => ({ name, value }));
      
      visuals.push(
        <div key="bar-chart" className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
            <Activity className="w-5 h-5 mr-2 text-blue-600" />
            {valueField.name.replace(/_/g, ' ')} by {categoryField.name.replace(/_/g, ' ')}
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      );
    }
    
    // 3. Pie Chart for distribution
    if (categoryFields.length > 0) {
      const field = categoryFields[0];
      const pieData = Object.entries(
        data.reduce((acc, item) => {
          const cat = item[field.name] || 'Unknown';
          acc[cat] = (acc[cat] || 0) + 1;
          return acc;
        }, {} as Record<string, number>)
      ).map(([name, value]) => ({ name, value }));
      
      visuals.push(
        <div key="pie-chart" className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
            <Target className="w-5 h-5 mr-2 text-green-600" />
            Distribution by {field.name.replace(/_/g, ' ')}
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      );
    }
    
    // 4. Timeline view for date fields
    if (dateFields.length > 0 && numericFields.length > 0) {
      const dateField = dateFields[0];
      const valueField = numericFields[0];
      
      const timelineData = data
        .filter(item => item[dateField.name])
        .map(item => ({
          date: new Date(item[dateField.name]).toLocaleDateString(),
          value: parseFloat(item[valueField.name]) || 0,
          name: item.name || item.title || 'Item'
        }))
        .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
      
      visuals.push(
        <div key="timeline" className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
            <Calendar className="w-5 h-5 mr-2 text-purple-600" />
            Timeline - {valueField.name.replace(/_/g, ' ')}
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Area type="monotone" dataKey="value" stroke="#8B5CF6" fill="#8B5CF6" fillOpacity={0.3} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      );
    }
    
    // 5. Heatmap-style grid for patterns
    if (categoryFields.length >= 2) {
      const field1 = categoryFields[0];
      const field2 = categoryFields[1];
      
      const heatmapData = data.reduce((acc, item) => {
        const key = `${item[field1.name]}-${item[field2.name]}`;
        acc[key] = (acc[key] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);
      
      const uniqueVals1 = [...new Set(data.map(item => item[field1.name]))].slice(0, 5);
      const uniqueVals2 = [...new Set(data.map(item => item[field2.name]))].slice(0, 5);
      
      visuals.push(
        <div key="heatmap" className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
            <Grid className="w-5 h-5 mr-2 text-orange-600" />
            Pattern Analysis: {field1.name} × {field2.name}
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-semibold text-gray-600">
                    {field1.name}
                  </th>
                  {uniqueVals2.map(val2 => (
                    <th key={val2} className="px-3 py-2 text-center text-xs font-semibold text-gray-600">
                      {val2}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {uniqueVals1.map(val1 => (
                  <tr key={val1} className="border-t">
                    <td className="px-3 py-2 text-sm font-medium text-gray-700">{val1}</td>
                    {uniqueVals2.map(val2 => {
                      const count = heatmapData[`${val1}-${val2}`] || 0;
                      const intensity = Math.min(count / 5, 1);
                      return (
                        <td 
                          key={val2} 
                          className="px-3 py-2 text-center text-sm"
                          style={{
                            backgroundColor: `rgba(59, 130, 246, ${intensity * 0.7})`,
                            color: intensity > 0.5 ? 'white' : 'black'
                          }}
                        >
                          {count}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      );
    }
    
    // 6. Status/Progress Indicators
    if (categoryFields.some(f => f.name.includes('status') || f.name.includes('state'))) {
      const statusField = categoryFields.find(f => f.name.includes('status') || f.name.includes('state'));
      if (statusField) {
        const statusCounts = data.reduce((acc, item) => {
          const status = item[statusField.name] || 'Unknown';
          acc[status] = (acc[status] || 0) + 1;
          return acc;
        }, {} as Record<string, number>);
        
        visuals.push(
          <div key="status-board" className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
              <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
              Status Overview
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {Object.entries(statusCounts).map(([status, count], idx) => (
                <div key={status} className="p-4 rounded-lg border-2" style={{borderColor: COLORS[idx % COLORS.length]}}>
                  <div className="text-2xl font-bold" style={{color: COLORS[idx % COLORS.length]}}>{count as number}</div>
                  <div className="text-sm text-gray-600 mt-1">{status.toUpperCase()}</div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                    <div 
                      className="h-2 rounded-full" 
                      style={{
                        width: `${((count as number) / data.length) * 100}%`,
                        backgroundColor: COLORS[idx % COLORS.length]
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      }
    }
    
    // 7. Geographic Map (if location data exists)
    if (fields.some(f => f.name.includes('location') || f.name.includes('city') || f.name.includes('state'))) {
      const locationField = fields.find(f => f.name.includes('location') || f.name.includes('city') || f.name.includes('state'));
      if (locationField) {
        const locationData = Object.entries(
          data.reduce((acc, item) => {
            const loc = item[locationField.name] || 'Unknown';
            acc[loc] = (acc[loc] || 0) + 1;
            return acc;
          }, {} as Record<string, number>)
        ).map(([name, count]) => ({ name, count: count as number }))
         .sort((a, b) => (b.count as number) - (a.count as number))
         .slice(0, 10);
        
        visuals.push(
          <div key="map-view" className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
              <MapPin className="w-5 h-5 mr-2 text-red-600" />
              Top Locations
            </h3>
            <div className="space-y-3">
              {locationData.map((item, idx) => (
                <div key={item.name} className="flex items-center">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm"
                       style={{backgroundColor: COLORS[idx % COLORS.length]}}>
                    {idx + 1}
                  </div>
                  <div className="flex-1 ml-3">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-medium text-gray-700">{item.name}</span>
                      <span className="text-sm text-gray-500">{item.count as number} items</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="h-2 rounded-full"
                        style={{
                          width: `${((item.count as number) / (locationData[0].count as number)) * 100}%`,
                          backgroundColor: COLORS[idx % COLORS.length]
                        }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      }
    }
    
    return visuals;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Activity className="w-12 h-12 mx-auto mb-4 text-blue-600 animate-spin" />
          <p className="text-gray-600">Analyzing your data and generating visualizations...</p>
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
        <AlertCircle className="w-12 h-12 mx-auto mb-4 text-yellow-600" />
        <h3 className="text-lg font-bold text-yellow-900 mb-2">No Data Available</h3>
        <p className="text-yellow-800">Upload some data to see auto-generated visualizations!</p>
      </div>
    );
  }

  const visuals = generateVisualizations();

  return (
    <div className="p-4 md:p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-extrabold text-gray-900 flex items-center">
            <Eye className="w-8 h-8 mr-3 text-blue-600" />
            Auto-Generated Dashboard
          </h2>
          <p className="text-gray-600 mt-1">
            Analyzing {data.length} records with {fields.length} fields
          </p>
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded ${viewMode === 'grid' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}`}
          >
            <Grid className="w-5 h-5" />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded ${viewMode === 'list' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}`}
          >
            <List className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Visualizations Grid */}
      <div className={`grid gap-6 ${viewMode === 'grid' ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1'}`}>
        {visuals}
      </div>

      {/* Raw Data Table */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
          <List className="w-5 h-5 mr-2 text-gray-600" />
          Raw Data ({data.length} records)
        </h3>
        <div className="overflow-x-auto max-h-96">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                {fields.map(field => (
                  <th key={field.name} className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    {field.name.replace(/_/g, ' ')}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.slice(0, 50).map((row, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  {fields.map(field => (
                    <td key={field.name} className="px-4 py-3 text-sm text-gray-700 whitespace-nowrap">
                      {row[field.name]?.toString() || '-'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {data.length > 50 && (
            <div className="text-center py-3 text-sm text-gray-500 bg-gray-50">
              Showing first 50 of {data.length} records
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
