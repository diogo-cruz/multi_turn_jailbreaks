import React, { useState, useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, LabelList, ScatterChart, Scatter, ZAxis
} from 'recharts';

// Color constants
const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE', 
  '#00C49F', '#FFBB28', '#FF8042', '#a4de6c', '#d0ed57'
];

const EvaluatorAnalysis = ({ data, selectedEvaluator, onEvaluatorSelect, uniqueEvaluators }) => {
  const [metric, setMetric] = useState("success");
  
  // Process data for visualization
  const processedData = useMemo(() => {
    if (!data || (Array.isArray(data) && data.length === 0) || !uniqueEvaluators || uniqueEvaluators.length === 0) {
      return [];
    }
    
    // Group by evaluator
    const evaluatorData = {};
    
    // Check data format
    if (Array.isArray(data) && data[0] && data[0].name) {
      // Already processed models array
      for (const model of data) {
        for (const evaluator of model.evaluators || []) {
          if (!evaluatorData[evaluator.name]) {
            evaluatorData[evaluator.name] = {
              totalSuccessRate: 0,
              totalRefusalRate: 0,
              models: {},
              modelCount: 0,
              totalSamples: 0
            };
          }
          
          evaluatorData[evaluator.name].models[model.name] = {
            successRate: evaluator.successRate,
            refusalRate: evaluator.refusalRate,
            rows: evaluator.rows
          };
          
          evaluatorData[evaluator.name].totalSuccessRate += evaluator.successRate;
          evaluatorData[evaluator.name].totalRefusalRate += evaluator.refusalRate;
          evaluatorData[evaluator.name].modelCount += 1;
          evaluatorData[evaluator.name].totalSamples += (evaluator.rows?.length || 0);
        }
      }
      
      // Calculate averages
      for (const evalName in evaluatorData) {
        if (evaluatorData[evalName].modelCount > 0) {
          evaluatorData[evalName].avgSuccessRate = 
            evaluatorData[evalName].totalSuccessRate / evaluatorData[evalName].modelCount;
          evaluatorData[evalName].avgRefusalRate = 
            evaluatorData[evalName].totalRefusalRate / evaluatorData[evalName].modelCount;
        }
      }
    } else {
      // Raw data rows
      for (const row of data) {
        const evalName = row.evaluator_model;
        if (!evalName) continue;
        
        const modelName = row.target_model || row.model || 'unknown';
        
        if (!evaluatorData[evalName]) {
          evaluatorData[evalName] = {
            models: {},
            modelCount: 0,
            totalSamples: 0,
            successCount: 0,
            refusalCount: 0
          };
        }
        
        if (!evaluatorData[evalName].models[modelName]) {
          evaluatorData[evalName].models[modelName] = {
            rows: []
          };
          evaluatorData[evalName].modelCount += 1;
        }
        
        evaluatorData[evalName].models[modelName].rows.push(row);
        evaluatorData[evalName].totalSamples += 1;
        
        // Count successes and refusals
        const isSuccess = row.success !== undefined ? Boolean(row.success) : 
                         row.jailbreak_success !== undefined ? Boolean(row.jailbreak_success) :
                         row.asr !== undefined ? row.asr > 0 : false;
        
        const isRefusal = row.refused !== undefined ? Boolean(row.refused) : 
                         row.refusal !== undefined ? Boolean(row.refusal) :
                         row.rejection !== undefined ? Boolean(row.rejection) : false;
        
        if (isSuccess) evaluatorData[evalName].successCount += 1;
        if (isRefusal) evaluatorData[evalName].refusalCount += 1;
      }
      
      // Calculate rates
      for (const evalName in evaluatorData) {
        const totalSamples = evaluatorData[evalName].totalSamples;
        if (totalSamples > 0) {
          evaluatorData[evalName].avgSuccessRate = 
            (evaluatorData[evalName].successCount / totalSamples) * 100;
          evaluatorData[evalName].avgRefusalRate = 
            (evaluatorData[evalName].refusalCount / totalSamples) * 100;
        }
        
        // Calculate rates per model
        for (const modelName in evaluatorData[evalName].models) {
          const rows = evaluatorData[evalName].models[modelName].rows;
          
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
          
          evaluatorData[evalName].models[modelName].successRate = successRate;
          evaluatorData[evalName].models[modelName].refusalRate = refusalRate;
        }
      }
    }
    
    // Format the results
    return Object.entries(evaluatorData).map(([evalName, data]) => {
      const modelEntries = Object.entries(data.models).map(([modelName, metrics]) => ({
        modelName,
        successRate: metrics.successRate,
        refusalRate: metrics.refusalRate,
        count: metrics.rows?.length || 0
      }));
      
      // Sort models by success rate
      const sortedModels = [...modelEntries].sort((a, b) => b.successRate - a.successRate);
      
      return {
        name: evalName,
        avgSuccessRate: data.avgSuccessRate || 0,
        avgRefusalRate: data.avgRefusalRate || 0,
        totalSamples: data.totalSamples || 0,
        modelCount: data.modelCount || 0,
        models: sortedModels
      };
    });
  }, [data, uniqueEvaluators]);
  
  // Sort evaluators by the selected metric
  const sortedEvaluators = useMemo(() => {
    if (!processedData || processedData.length === 0) return [];
    
    const metricMap = {
      'success': 'avgSuccessRate',
      'refusal': 'avgRefusalRate'
    };
    
    const field = metricMap[metric] || 'avgSuccessRate';
    
    return [...processedData].sort((a, b) => {
      // Primary sort by the metric
      if (b[field] !== a[field]) {
        return b[field] - a[field];
      }
      // Secondary sort by name
      return a.name.localeCompare(b.name);
    });
  }, [processedData, metric]);
  
  // Get data for selected evaluator
  const selectedEvaluatorData = useMemo(() => {
    if (!selectedEvaluator || !processedData || processedData.length === 0) {
      return null;
    }
    
    return processedData.find(e => e.name === selectedEvaluator) || null;
  }, [selectedEvaluator, processedData]);
  
  // Render evaluator selector
  const renderEvaluatorSelector = () => (
    <div className="mb-4">
      <label className="block text-sm font-medium mb-1">Select Evaluator:</label>
      <select 
        className="w-full p-2 border rounded"
        value={selectedEvaluator || ''}
        onChange={(e) => onEvaluatorSelect(e.target.value)}
      >
        {(uniqueEvaluators || []).filter(Boolean).map(evaluator => (
          <option key={evaluator} value={evaluator}>{evaluator}</option>
        ))}
      </select>
    </div>
  );
  
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
      </div>
    </div>
  );
  
  // Render evaluator comparison chart
  const renderEvaluatorComparison = () => {
    if (!sortedEvaluators || sortedEvaluators.length === 0) {
      return <div>No evaluator data available</div>;
    }
    
    // Get data key based on selected metric
    const dataKey = metric === 'success' ? 'avgSuccessRate' : 'avgRefusalRate';
    
    return (
      <div className="chart-container">
        <h3 className="text-lg font-medium mb-2">
          {metric === 'success' ? 'Success Rate' : 'Refusal Rate'} by Evaluator
        </h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart
            data={sortedEvaluators}
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
                value: metric === 'success' ? 'Success Rate (%)' : 'Refusal Rate (%)',
                angle: -90, 
                position: 'insideLeft' 
              }} 
            />
            <Tooltip formatter={(value) => [
              `${value.toFixed(2)}%`,
              metric === 'success' ? 'Success Rate' : 'Refusal Rate'
            ]} />
            <Legend />
            <Bar 
              dataKey={dataKey} 
              fill="#8884d8"
              name={metric === 'success' ? 'Success Rate' : 'Refusal Rate'}
            >
              {sortedEvaluators.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
              <LabelList dataKey={dataKey} position="top" formatter={(value) => `${value.toFixed(1)}%`} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };
  
  // Render model performance for selected evaluator
  const renderModelPerformance = () => {
    if (!selectedEvaluatorData || !selectedEvaluatorData.models || selectedEvaluatorData.models.length === 0) {
      return <div>No model data available for this evaluator</div>;
    }
    
    // Get data key based on selected metric
    const dataKey = metric === 'success' ? 'successRate' : 'refusalRate';
    
    // Limit to top 15 models for readability
    const displayModels = selectedEvaluatorData.models.slice(0, 15);
    
    return (
      <div className="chart-container mt-6">
        <h3 className="text-lg font-medium mb-2">
          Model Performance with {selectedEvaluatorData.name} Evaluator
        </h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart
            data={displayModels}
            margin={{ top: 20, right: 30, left: 30, bottom: 100 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="modelName" 
              angle={-45} 
              textAnchor="end"
              height={100}
              interval={0}
            />
            <YAxis 
              label={{ 
                value: metric === 'success' ? 'Success Rate (%)' : 'Refusal Rate (%)',
                angle: -90, 
                position: 'insideLeft' 
              }} 
            />
            <Tooltip formatter={(value) => [
              `${value.toFixed(2)}%`,
              metric === 'success' ? 'Success Rate' : 'Refusal Rate'
            ]} />
            <Legend />
            <Bar 
              dataKey={dataKey} 
              fill="#82ca9d"
              name={metric === 'success' ? 'Success Rate' : 'Refusal Rate'}
            >
              {displayModels.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };
  
  // Render scatter plot of success vs refusal
  const renderScatterPlot = () => {
    if (!processedData || processedData.length === 0) {
      return null;
    }
    
    return (
      <div className="chart-container mt-6">
        <h3 className="text-lg font-medium mb-2">
          Success Rate vs. Refusal Rate by Evaluator
        </h3>
        <ResponsiveContainer width="100%" height={400}>
          <ScatterChart
            margin={{ top: 20, right: 30, left: 30, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              type="number" 
              dataKey="avgSuccessRate" 
              name="Success Rate" 
              label={{ 
                value: 'Success Rate (%)', 
                position: 'insideBottom', 
                offset: -10 
              }}
            />
            <YAxis 
              type="number" 
              dataKey="avgRefusalRate" 
              name="Refusal Rate"
              label={{ 
                value: 'Refusal Rate (%)', 
                angle: -90, 
                position: 'insideLeft' 
              }}
            />
            <ZAxis 
              type="number" 
              dataKey="totalSamples" 
              range={[40, 400]} 
              name="Total Samples"
            />
            <Tooltip 
              cursor={{ strokeDasharray: '3 3' }}
              formatter={(value, name) => [
                `${value.toFixed(2)}${name === 'Total Samples' ? '' : '%'}`,
                name
              ]}
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const evaluator = payload[0].payload;
                  return (
                    <div className="bg-white p-2 border rounded shadow">
                      <p className="font-medium">{evaluator.name}</p>
                      <p>Success Rate: {evaluator.avgSuccessRate.toFixed(2)}%</p>
                      <p>Refusal Rate: {evaluator.avgRefusalRate.toFixed(2)}%</p>
                      <p>Models: {evaluator.modelCount}</p>
                      <p>Total Samples: {evaluator.totalSamples}</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend />
            <Scatter 
              name="Evaluators" 
              data={processedData} 
              fill="#8884d8"
            >
              {processedData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    );
  };
  
  // Render details for selected evaluator
  const renderEvaluatorDetails = () => {
    if (!selectedEvaluatorData) {
      return <div>Select an evaluator to view details</div>;
    }
    
    return (
      <div className="mt-8 p-4 border rounded">
        <h3 className="text-xl font-medium mb-2">{selectedEvaluatorData.name}</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-blue-50 p-3 rounded">
            <p className="text-sm text-gray-600">Average Success Rate</p>
            <p className="text-2xl font-bold">{selectedEvaluatorData.avgSuccessRate.toFixed(2)}%</p>
          </div>
          <div className="bg-red-50 p-3 rounded">
            <p className="text-sm text-gray-600">Average Refusal Rate</p>
            <p className="text-2xl font-bold">{selectedEvaluatorData.avgRefusalRate.toFixed(2)}%</p>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm">
              Models evaluated: <span className="font-medium">{selectedEvaluatorData.modelCount}</span>
            </p>
          </div>
          <div>
            <p className="text-sm">
              Total samples: <span className="font-medium">{selectedEvaluatorData.totalSamples}</span>
            </p>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">Evaluator Analysis</h2>
        <p className="text-gray-600">
          Compare different evaluator models and their assessment of jailbreak attempts.
        </p>
      </div>
      
      <div className="flex flex-wrap -mx-2">
        <div className="w-full md:w-1/4 px-2">
          {renderEvaluatorSelector()}
          {renderMetricSelector()}
        </div>
        
        <div className="w-full md:w-3/4 px-2">
          {renderEvaluatorComparison()}
          {renderEvaluatorDetails()}
          {renderModelPerformance()}
          {renderScatterPlot()}
        </div>
      </div>
    </div>
  );
};

export default EvaluatorAnalysis; 