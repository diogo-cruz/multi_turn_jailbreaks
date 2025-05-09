import React, { useState, useMemo } from 'react';
import { 
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, ZAxis, Label
} from 'recharts';

// Color constants
const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE', 
  '#00C49F', '#FFBB28', '#FF8042', '#a4de6c', '#d0ed57'
];

const SizeAnalysis = ({ data, modelComparisonData }) => {
  const [metric, setMetric] = useState("success");
  const [logScale, setLogScale] = useState(true);
  
  // Process data for visualization
  const processedData = useMemo(() => {
    if (!data || !modelComparisonData || modelComparisonData.length === 0) {
      return [];
    }
    
    // Map model names to sizes from modelComparisonData
    const modelSizes = {};
    const modelFamilies = {};
    
    for (const model of modelComparisonData) {
      if (model.model_name && model.parameters) {
        modelSizes[model.model_name] = parseFloat(model.parameters);
        
        // Extract model family (e.g., "gpt-4", "claude", etc.)
        const nameParts = model.model_name.toLowerCase().split(/[-\s]/);
        if (nameParts.length > 0) {
          const family = nameParts[0];
          modelFamilies[model.model_name] = family;
        }
      }
    }
    
    // Calculate aggregated metrics for each model
    const modelData = {};
    
    // Check data format
    if (Array.isArray(data) && data[0] && data[0].name) {
      // Process model objects
      for (const modelObject of data) {
        const modelName = modelObject.name;
        const size = modelSizes[modelName];
        
        if (!size) continue; // Skip if no size data
        
        // Calculate overall metrics
        const successRate = modelObject.testCases 
          ? modelObject.testCases.reduce((sum, tc) => sum + tc.successRate, 0) / modelObject.testCases.length
          : 0;
        
        const refusalRate = modelObject.testCases 
          ? modelObject.testCases.reduce((sum, tc) => sum + tc.refusalRate, 0) / modelObject.testCases.length
          : 0;
        
        const avgRounds = modelObject.testCases 
          ? modelObject.testCases.reduce((sum, tc) => sum + tc.roundCount, 0) / modelObject.testCases.length
          : 0;
        
        modelData[modelName] = {
          name: modelName,
          size,
          family: modelFamilies[modelName] || 'unknown',
          successRate,
          refusalRate,
          avgRounds,
          count: modelObject.testCases?.length || 0
        };
      }
    } else {
      // Process raw data rows
      for (const row of data) {
        const modelName = row.target_model || row.model || 'unknown';
        const size = modelSizes[modelName];
        
        if (!size) continue; // Skip if no size data
        
        if (!modelData[modelName]) {
          modelData[modelName] = {
            name: modelName,
            size,
            family: modelFamilies[modelName] || 'unknown',
            successCount: 0,
            refusalCount: 0,
            roundSum: 0,
            totalCount: 0
          };
        }
        
        modelData[modelName].totalCount++;
        
        // Count success/refusal/rounds
        const isSuccess = row.success !== undefined ? Boolean(row.success) : 
                         row.jailbreak_success !== undefined ? Boolean(row.jailbreak_success) :
                         row.asr !== undefined ? row.asr > 0 : false;
        
        const isRefusal = row.refused !== undefined ? Boolean(row.refused) : 
                         row.refusal !== undefined ? Boolean(row.refusal) :
                         row.rejection !== undefined ? Boolean(row.rejection) : false;
        
        if (isSuccess) modelData[modelName].successCount++;
        if (isRefusal) modelData[modelName].refusalCount++;
        
        const rounds = row.num_turns || row.rounds || row.turn_count || 0;
        modelData[modelName].roundSum += rounds;
      }
      
      // Calculate rates
      for (const modelName in modelData) {
        const model = modelData[modelName];
        if (model.totalCount > 0) {
          model.successRate = (model.successCount / model.totalCount) * 100;
          model.refusalRate = (model.refusalCount / model.totalCount) * 100;
          model.avgRounds = model.roundSum / model.totalCount;
          model.count = model.totalCount;
        }
      }
    }
    
    // Convert to array and group by family
    const families = {};
    const result = [];
    
    for (const modelName in modelData) {
      const model = modelData[modelName];
      
      if (!families[model.family]) {
        families[model.family] = [];
      }
      
      families[model.family].push(model);
      result.push(model);
    }
    
    return { 
      models: result,
      familyGroups: families
    };
  }, [data, modelComparisonData]);
  
  // Get chart data based on selected metric
  const chartData = useMemo(() => {
    if (!processedData.models || processedData.models.length === 0) {
      return [];
    }
    
    const metricKey = metric === 'success' ? 'successRate' : 
                      metric === 'refusal' ? 'refusalRate' : 'avgRounds';
    
    return processedData.models.map(model => ({
      ...model,
      value: model[metricKey]
    }));
  }, [processedData, metric]);
  
  // Group models by family for coloring
  const familyColors = useMemo(() => {
    const families = Object.keys(processedData.familyGroups || {});
    const colorMap = {};
    
    families.forEach((family, index) => {
      colorMap[family] = COLORS[index % COLORS.length];
    });
    
    return colorMap;
  }, [processedData]);
  
  // Render metric selector
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
  
  // Render scale toggler
  const renderScaleToggler = () => (
    <div className="mb-4">
      <label className="block text-sm font-medium mb-1">X-Axis Scale:</label>
      <div className="flex space-x-4">
        <label className="inline-flex items-center">
          <input 
            type="checkbox" 
            checked={logScale} 
            onChange={(e) => setLogScale(e.target.checked)}
            className="mr-1"
          />
          Logarithmic Scale
        </label>
      </div>
    </div>
  );
  
  // Render the scatter plot
  const renderScatterPlot = () => {
    if (!chartData || chartData.length === 0) {
      return <div>No model size data available</div>;
    }
    
    // Format domain for x-axis (model size) based on scale type
    const domain = logScale 
      ? [Math.pow(10, Math.floor(Math.log10(Math.min(...chartData.map(m => m.size))))), 
         Math.pow(10, Math.ceil(Math.log10(Math.max(...chartData.map(m => m.size)))))]
      : [0, Math.max(...chartData.map(m => m.size)) * 1.1];
    
    return (
      <div className="chart-container">
        <h3 className="text-lg font-medium mb-2">
          {metric === 'success' ? 'Success Rate' : 
           metric === 'refusal' ? 'Refusal Rate' : 'Average Rounds'} vs. Model Size
        </h3>
        
        <ResponsiveContainer width="100%" height={500}>
          <ScatterChart
            margin={{ top: 20, right: 30, left: 30, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              type="number" 
              dataKey="size" 
              name="Model Size" 
              scale={logScale ? 'log' : 'linear'}
              domain={domain}
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => {
                if (value >= 1e9) return `${(value / 1e9).toFixed(0)}B`;
                if (value >= 1e6) return `${(value / 1e6).toFixed(0)}M`;
                return value;
              }}
            >
              <Label value="Model Size (Parameters)" offset={-10} position="insideBottom" />
            </XAxis>
            <YAxis 
              type="number" 
              dataKey="value" 
              name="Value"
              domain={metric === 'rounds' ? ['auto', 'auto'] : [0, 100]}
            >
              <Label 
                value={metric === 'success' ? 'Success Rate (%)' : 
                       metric === 'refusal' ? 'Refusal Rate (%)' : 'Average Rounds'} 
                angle={-90} 
                position="insideLeft" 
                offset={-10}
              />
            </YAxis>
            <ZAxis 
              type="number" 
              dataKey="count" 
              range={[40, 400]} 
              name="Sample Count"
            />
            <Tooltip 
              cursor={{ strokeDasharray: '3 3' }}
              formatter={(value, name, props) => {
                if (name === 'Model Size') {
                  if (value >= 1e9) return [`${(value / 1e9).toFixed(2)}B`, name];
                  if (value >= 1e6) return [`${(value / 1e6).toFixed(2)}M`, name];
                  return [value, name];
                }
                if (name === 'Sample Count') return [value, name];
                return [`${value.toFixed(2)}${metric !== 'rounds' ? '%' : ''}`, name];
              }}
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const model = payload[0].payload;
                  const sizeStr = model.size >= 1e9 
                    ? `${(model.size / 1e9).toFixed(2)}B` 
                    : model.size >= 1e6 
                      ? `${(model.size / 1e6).toFixed(2)}M` 
                      : model.size;
                  
                  return (
                    <div className="bg-white p-2 border rounded shadow">
                      <p className="font-medium">{model.name}</p>
                      <p>Size: {sizeStr} parameters</p>
                      <p>
                        {metric === 'success' ? 'Success Rate' : 
                         metric === 'refusal' ? 'Refusal Rate' : 'Average Rounds'}: 
                        {' '}{model.value.toFixed(2)}{metric !== 'rounds' ? '%' : ''}
                      </p>
                      <p>Sample Count: {model.count}</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend 
              payload={
                Object.entries(familyColors).map(([family, color]) => ({
                  value: family,
                  type: 'circle',
                  color
                }))
              }
            />
            {Object.entries(processedData.familyGroups || {}).map(([family, models]) => (
              <Scatter 
                key={family}
                name={family} 
                data={models.map(model => ({
                  ...model,
                  value: model[metric === 'success' ? 'successRate' : 
                               metric === 'refusal' ? 'refusalRate' : 'avgRounds']
                }))} 
                fill={familyColors[family]}
              />
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    );
  };
  
  // Check if there's data for analysis
  const hasModelSizeData = useMemo(() => {
    return chartData && chartData.length > 0;
  }, [chartData]);

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">Model Size Analysis</h2>
        <p className="text-gray-600">
          Analyze the relationship between model size (parameters) and jailbreak resistance.
        </p>
      </div>
      
      {!hasModelSizeData ? (
        <div className="p-6 bg-gray-100 rounded text-center">
          <p className="text-lg">
            Model size data is not available. Please ensure that model_comparison.csv contains parameter counts.
          </p>
        </div>
      ) : (
        <div className="flex flex-wrap -mx-2">
          <div className="w-full md:w-1/4 px-2">
            {renderMetricSelector()}
            {renderScaleToggler()}
            
            <div className="mt-6 p-4 bg-blue-50 rounded">
              <h3 className="text-md font-medium mb-2">Key Insights</h3>
              <ul className="list-disc pl-5 text-sm space-y-2">
                <li>Compare how model size correlates with jailbreak resistance</li>
                <li>Points are colored by model family</li>
                <li>Larger points indicate more samples</li>
                <li>Toggle between linear and logarithmic scales</li>
              </ul>
            </div>
          </div>
          
          <div className="w-full md:w-3/4 px-2">
            {renderScatterPlot()}
          </div>
        </div>
      )}
    </div>
  );
};

export default SizeAnalysis; 