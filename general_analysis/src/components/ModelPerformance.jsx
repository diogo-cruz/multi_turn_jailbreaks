import React, { useState, useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, LabelList, LineChart, Line, ScatterChart, Scatter, ZAxis
} from 'recharts';
import { calculateStandardError } from '../utils/dataProcessing';

// Color constants
const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE', 
  '#00C49F', '#FFBB28', '#FF8042', '#a4de6c', '#d0ed57'
];

const ModelPerformance = ({ data, selectedModel, onModelSelect, uniqueModels }) => {
  const [chartType, setChartType] = useState("bar");
  const [metric, setMetric] = useState("success");
  
  // Process data for visualization
  const processedData = useMemo(() => {
    if (!data || (Array.isArray(data) && data.length === 0)) {
      return [];
    }
    
    // Check if data is already processed (models array)
    if (Array.isArray(data) && data[0] && data[0].name) {
      return data;
    }
    
    // Group by model
    const modelData = {};
    for (const row of data) {
      const modelName = row.target_model || row.model || 'unknown';
      
      if (!modelData[modelName]) {
        modelData[modelName] = [];
      }
      
      modelData[modelName].push(row);
    }
    
    // Calculate metrics for each model
    return Object.entries(modelData).map(([modelName, rows]) => {
      // Calculate success rate
      const successfulRows = rows.filter(row => 
        row.success !== undefined ? Boolean(row.success) : 
        row.jailbreak_success !== undefined ? Boolean(row.jailbreak_success) :
        row.asr !== undefined ? row.asr > 0 : false
      );
      const successRate = rows.length > 0 ? (successfulRows.length / rows.length) * 100 : 0;
      
      // Calculate refusal rate
      const refusalRows = rows.filter(row => 
        row.refused !== undefined ? Boolean(row.refused) : 
        row.refusal !== undefined ? Boolean(row.refusal) :
        row.rejection !== undefined ? Boolean(row.rejection) : false
      );
      const refusalRate = rows.length > 0 ? (refusalRows.length / rows.length) * 100 : 0;
      
      // Calculate average rounds
      const roundsData = rows
        .filter(row => row.num_turns || row.rounds || row.turn_count)
        .map(row => row.num_turns || row.rounds || row.turn_count || 0);
      
      const avgRounds = roundsData.length > 0 
        ? roundsData.reduce((sum, val) => sum + val, 0) / roundsData.length 
        : 0;
      
      // Calculate standard errors
      const successValues = rows.map(row => 
        row.success !== undefined ? (row.success ? 100 : 0) : 
        row.jailbreak_success !== undefined ? (row.jailbreak_success ? 100 : 0) :
        row.asr !== undefined ? row.asr * 100 : 0
      );
      
      const successStdErr = calculateStandardError(successValues);
      const roundsStdErr = calculateStandardError(roundsData);
      
      return {
        name: modelName,
        successRate,
        refusalRate,
        avgRounds,
        successStdErr,
        roundsStdErr,
        count: rows.length
      };
    });
  }, [data]);
  
  // Sort data by the selected metric
  const sortedData = useMemo(() => {
    if (!processedData || processedData.length === 0) return [];
    
    const metricMap = {
      'success': 'successRate',
      'refusal': 'refusalRate',
      'rounds': 'avgRounds'
    };
    
    const field = metricMap[metric] || 'successRate';
    
    return [...processedData].sort((a, b) => {
      // Primary sort by the metric
      if (b[field] !== a[field]) {
        return b[field] - a[field];
      }
      // Secondary sort by name for stable ordering
      return a.name.localeCompare(b.name);
    });
  }, [processedData, metric]);
  
  // Extract data for selected model
  const selectedModelData = useMemo(() => {
    if (!selectedModel || !processedData || processedData.length === 0) {
      return null;
    }
    
    return processedData.find(m => m.name === selectedModel) || null;
  }, [selectedModel, processedData]);
  
  // Render the model selector
  const renderModelSelector = () => (
    <div className="mb-4">
      <label className="block text-sm font-medium mb-1">Select Model:</label>
      <select 
        className="w-full p-2 border rounded"
        value={selectedModel || ''}
        onChange={(e) => onModelSelect(e.target.value)}
      >
        {(uniqueModels || []).map(model => (
          <option key={model} value={model}>{model}</option>
        ))}
      </select>
    </div>
  );
  
  // Render the chart type selector
  const renderChartTypeSelector = () => (
    <div className="mb-4">
      <label className="block text-sm font-medium mb-1">Chart Type:</label>
      <div className="flex space-x-4">
        <label className="inline-flex items-center">
          <input 
            type="radio" 
            value="bar" 
            checked={chartType === "bar"} 
            onChange={() => setChartType("bar")}
            className="mr-1"
          />
          Bar Chart
        </label>
        <label className="inline-flex items-center">
          <input 
            type="radio" 
            value="line" 
            checked={chartType === "line"} 
            onChange={() => setChartType("line")}
            className="mr-1"
          />
          Line Chart
        </label>
        <label className="inline-flex items-center">
          <input 
            type="radio" 
            value="scatter" 
            checked={chartType === "scatter"} 
            onChange={() => setChartType("scatter")}
            className="mr-1"
          />
          Scatter Plot
        </label>
      </div>
    </div>
  );
  
  // Render the metric selector
  const renderMetricSelector = () => (
    <div className="mb-4">
      <label className="block text-sm font-medium mb-1">Metric:</label>
      <div className="flex space-x-4">
        <label className="inline-flex items-center">
          <input 
            type="radio" 
            value="success" 
            checked={metric === "success"} 
            onChange={() => setMetric("success")}
            className="mr-1"
          />
          Success Rate
        </label>
        <label className="inline-flex items-center">
          <input 
            type="radio" 
            value="refusal" 
            checked={metric === "refusal"} 
            onChange={() => setMetric("refusal")}
            className="mr-1"
          />
          Refusal Rate
        </label>
        <label className="inline-flex items-center">
          <input 
            type="radio" 
            value="rounds" 
            checked={metric === "rounds"} 
            onChange={() => setMetric("rounds")}
            className="mr-1"
          />
          Average Rounds
        </label>
      </div>
    </div>
  );
  
  // Render a bar chart for model comparison
  const renderBarChart = () => {
    if (!sortedData || sortedData.length === 0) {
      return <div>No data available</div>;
    }
    
    // Get data series based on selected metric
    const dataKey = metric === 'success' ? 'successRate' : 
                    metric === 'refusal' ? 'refusalRate' : 'avgRounds';
    
    const errorKey = metric === 'success' ? 'successStdErr' : 
                     metric === 'refusal' ? 'refusalStdErr' : 'roundsStdErr';
    
    // Create chart data with error bars
    const chartData = sortedData.map(model => ({
      name: model.name,
      value: model[dataKey],
      error: model[errorKey] || 0
    }));
    
    return (
      <div className="chart-container">
        <h3 className="text-lg font-medium mb-2">
          {metric === 'success' ? 'Success Rate' : 
           metric === 'refusal' ? 'Refusal Rate' : 'Average Rounds'} by Model
        </h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart
            data={chartData}
            margin={{ top: 20, right: 30, left: 30, bottom: 100 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="name" 
              angle={-45} 
              textAnchor="end"
              height={100}
              interval={0}
            />
            <YAxis 
              label={{ 
                value: metric === 'success' ? 'Success Rate (%)' : 
                       metric === 'refusal' ? 'Refusal Rate (%)' : 'Average Rounds',
                angle: -90, 
                position: 'insideLeft' 
              }} 
            />
            <Tooltip formatter={(value) => [
              `${value.toFixed(2)}${metric !== 'rounds' ? '%' : ''}`,
              metric === 'success' ? 'Success Rate' : 
              metric === 'refusal' ? 'Refusal Rate' : 'Average Rounds'
            ]} />
            <Legend />
            <Bar 
              dataKey="value" 
              fill="#8884d8"
              name={metric === 'success' ? 'Success Rate' : 
                   metric === 'refusal' ? 'Refusal Rate' : 'Average Rounds'}
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
              <LabelList dataKey="value" position="top" formatter={(value) => `${value.toFixed(1)}${metric !== 'rounds' ? '%' : ''}`} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };
  
  // Render a line chart for model comparison
  const renderLineChart = () => {
    if (!sortedData || sortedData.length === 0) {
      return <div>No data available</div>;
    }
    
    // Get data series based on selected metric
    const dataKey = metric === 'success' ? 'successRate' : 
                    metric === 'refusal' ? 'refusalRate' : 'avgRounds';
    
    return (
      <div className="chart-container">
        <h3 className="text-lg font-medium mb-2">
          {metric === 'success' ? 'Success Rate' : 
           metric === 'refusal' ? 'Refusal Rate' : 'Average Rounds'} by Model
        </h3>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart
            data={sortedData}
            margin={{ top: 20, right: 30, left: 30, bottom: 100 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="name" 
              angle={-45} 
              textAnchor="end"
              height={100}
              interval={0}
            />
            <YAxis 
              label={{ 
                value: metric === 'success' ? 'Success Rate (%)' : 
                       metric === 'refusal' ? 'Refusal Rate (%)' : 'Average Rounds',
                angle: -90, 
                position: 'insideLeft' 
              }} 
            />
            <Tooltip formatter={(value) => [
              `${value.toFixed(2)}${metric !== 'rounds' ? '%' : ''}`,
              metric === 'success' ? 'Success Rate' : 
              metric === 'refusal' ? 'Refusal Rate' : 'Average Rounds'
            ]} />
            <Legend />
            <Line 
              type="monotone" 
              dataKey={dataKey} 
              stroke="#8884d8" 
              name={metric === 'success' ? 'Success Rate' : 
                    metric === 'refusal' ? 'Refusal Rate' : 'Average Rounds'}
              activeDot={{ r: 8 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  };
  
  // Render a scatter plot for model comparison
  const renderScatterPlot = () => {
    if (!sortedData || sortedData.length === 0) {
      return <div>No data available</div>;
    }
    
    return (
      <div className="chart-container">
        <h3 className="text-lg font-medium mb-2">
          Success Rate vs. Refusal Rate by Model
        </h3>
        <ResponsiveContainer width="100%" height={400}>
          <ScatterChart
            margin={{ top: 20, right: 30, left: 30, bottom: 100 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              type="number" 
              dataKey="successRate" 
              name="Success Rate" 
              label={{ 
                value: 'Success Rate (%)', 
                position: 'insideBottom', 
                offset: -10 
              }}
            />
            <YAxis 
              type="number" 
              dataKey="refusalRate" 
              name="Refusal Rate"
              label={{ 
                value: 'Refusal Rate (%)', 
                angle: -90, 
                position: 'insideLeft' 
              }}
            />
            <ZAxis 
              type="number" 
              dataKey="avgRounds" 
              range={[40, 400]} 
              name="Average Rounds"
            />
            <Tooltip 
              cursor={{ strokeDasharray: '3 3' }}
              formatter={(value, name) => [
                `${value.toFixed(2)}${name === 'Average Rounds' ? '' : '%'}`,
                name
              ]}
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const model = payload[0].payload;
                  return (
                    <div className="bg-white p-2 border rounded shadow">
                      <p className="font-medium">{model.name}</p>
                      <p>Success Rate: {model.successRate.toFixed(2)}%</p>
                      <p>Refusal Rate: {model.refusalRate.toFixed(2)}%</p>
                      <p>Average Rounds: {model.avgRounds.toFixed(2)}</p>
                      <p>Sample Count: {model.count}</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend />
            <Scatter 
              name="Models" 
              data={sortedData} 
              fill="#8884d8"
            >
              {sortedData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    );
  };
  
  // Render details for selected model
  const renderModelDetails = () => {
    if (!selectedModelData) {
      return <div>Select a model to view details</div>;
    }
    
    return (
      <div className="mt-8 p-4 border rounded">
        <h3 className="text-xl font-medium mb-2">{selectedModelData.name}</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-3 rounded">
            <p className="text-sm text-gray-600">Success Rate</p>
            <p className="text-2xl font-bold">{selectedModelData.successRate.toFixed(2)}%</p>
          </div>
          <div className="bg-red-50 p-3 rounded">
            <p className="text-sm text-gray-600">Refusal Rate</p>
            <p className="text-2xl font-bold">{selectedModelData.refusalRate.toFixed(2)}%</p>
          </div>
          <div className="bg-green-50 p-3 rounded">
            <p className="text-sm text-gray-600">Average Rounds</p>
            <p className="text-2xl font-bold">{selectedModelData.avgRounds.toFixed(2)}</p>
          </div>
        </div>
        <div className="mt-4">
          <p className="text-sm">
            Sample Count: <span className="font-medium">{selectedModelData.count}</span>
          </p>
        </div>
      </div>
    );
  };
  
  // Render the appropriate chart based on selected chart type
  const renderChart = () => {
    switch (chartType) {
      case "bar":
        return renderBarChart();
      case "line":
        return renderLineChart();
      case "scatter":
        return renderScatterPlot();
      default:
        return renderBarChart();
    }
  };
  
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">Model Performance Analysis</h2>
        <p className="text-gray-600">
          Compare performance metrics across different language models, 
          including success rates, refusal rates, and average conversation rounds.
        </p>
      </div>
      
      <div className="flex flex-wrap -mx-2">
        <div className="w-full md:w-1/4 px-2">
          {renderModelSelector()}
          {renderChartTypeSelector()}
          {renderMetricSelector()}
        </div>
        
        <div className="w-full md:w-3/4 px-2">
          {renderChart()}
          {renderModelDetails()}
        </div>
      </div>
    </div>
  );
};

export default ModelPerformance; 