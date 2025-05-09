import React, { useState, useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, LabelList, ScatterChart, Scatter, ZAxis, Label
} from 'recharts';

// Color constants
const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE', 
  '#00C49F', '#FFBB28', '#FF8042', '#a4de6c', '#d0ed57'
];

// Model parameter sizes (in billions) for reference sizing
const MODEL_SIZES = {
  'meta-llama/llama-3.1-70b-instruct': 70,
  'meta-llama/llama-3.1-8b-instruct': 8,
  'meta-llama/llama-3.2-1b-instruct': 1,
  'meta-llama/llama-3.2-3b-instruct': 3,
  'meta-llama/llama-3.3-70b-instruct': 70,
  'gpt-4o-mini-2024-07-18': 25,
  'google/gemini-2.0-flash-001': 35,
  'google/gemini-2.0-flash-lite-001': 15,
  'google/gemini-flash-1.5': 10,
  'google/gemma-2-9b-it': 9,
  'google/gemma-3-12b-it': 12,
  'google/gemma-3-27b-it': 27,
  'anthropic/claude-3-haiku': 8,
  'anthropic/claude-3.5-sonnet': 18,
  'anthropic/claude-3.7-sonnet': 45,
  'openai/gpt-4o': 300,
  'openai/gpt-4.1': 240,
  'openai/gpt-4.1-mini': 24,
  'openai/gpt-4.1-nano': 8,
  'google/gemini-2.5-pro-preview-03-25': 120,
  'google/gemini-2.5-flash-preview': 35,
  'qwen/qwen-2.5-7b-instruct': 7,
  'qwen/qwen-2.5-72b-instruct': 72,
  'mistralai/mistral-7b-instruct-v0.3': 7,
  'mistralai/mistral-small-3.1-24b-instruct': 24,
  'mistralai/mistral-tiny': 3,
  'mistralai/mistral-nemo': 12,
  'meta-llama/llama-4-scout': 8,
  'meta-llama/llama-4-maverick': 44,
  'deepseek/deepseek-chat-v3-0324': 16,
  'mistral-large-latest': 42,
  'claude-3-sonnet': 45,
  'claude-3-opus': 145
};

const ReasoningAnalysis = ({ data, modelComparisonData }) => {
  const [chartType, setChartType] = useState("bar");
  const [selectedModel, setSelectedModel] = useState(null);
  
  // Process data for visualization
  const processedData = useMemo(() => {
    if (!data || (Array.isArray(data) && data.length === 0)) {
      return { 
        overviewData: [], 
        modelData: [], 
        relationshipData: [],
        hasReasoningData: false,
        uniqueModels: []
      };
    }
    
    // Reasoning levels mapping
    const reasoningLevels = ["none", "low", "medium", "high"];
    const reasoningOrder = { "none": 0, "low": 1, "medium": 2, "high": 3 };
    
    // Extract reasoning data
    let reasoningData = [];
    
    // Process data based on format
    if (Array.isArray(data) && data[0] && data[0].name) {
      // Already processed models array
      for (const model of data) {
        if (!model.testCases) continue;
        
        for (const testCase of model.testCases) {
          if (!testCase.rows) continue;
          
          for (const row of testCase.rows) {
            if (row.reasoning && 
                ["none", "low", "medium", "high"].includes(String(row.reasoning).toLowerCase())) {
              reasoningData.push({
                model: model.name,
                reasoning: String(row.reasoning).toLowerCase(),
                success: Boolean(row.success || row.jailbreak_success || (row.asr > 0)),
                test_case: testCase.name,
                jailbreak: row.jailbreak || 'unknown'
              });
            }
          }
        }
      }
    } else {
      // Raw data rows
      reasoningData = data.filter(row => 
        row.reasoning && ["none", "low", "medium", "high"].includes(String(row.reasoning).toLowerCase())
      ).map(row => ({
        model: row.target_model || row.model || 'unknown',
        reasoning: String(row.reasoning).toLowerCase(),
        success: Boolean(row.success || row.jailbreak_success || (row.asr > 0)),
        test_case: row.test_case || 'unknown',
        jailbreak: row.jailbreak || 'unknown'
      }));
    }
    
    if (reasoningData.length === 0) {
      return { 
        overviewData: [], 
        modelData: [], 
        relationshipData: [],
        hasReasoningData: false,
        uniqueModels: []
      };
    }
    
    // 1. Group by model and reasoning level
    const dataByModelAndReasoning = {};
    const uniqueModels = new Set();
    
    reasoningData.forEach(row => {
      const model = row.model;
      uniqueModels.add(model);
      const reasoning = row.reasoning;
      
      if (!dataByModelAndReasoning[model]) {
        dataByModelAndReasoning[model] = {};
      }
      
      if (!dataByModelAndReasoning[model][reasoning]) {
        dataByModelAndReasoning[model][reasoning] = {
          totalTests: 0,
          successfulTests: 0,
          asr: 0
        };
      }
      
      dataByModelAndReasoning[model][reasoning].totalTests += 1;
      if (row.success) {
        dataByModelAndReasoning[model][reasoning].successfulTests += 1;
      }
    });
    
    // 2. Calculate ASR for each model and reasoning level
    Object.keys(dataByModelAndReasoning).forEach(model => {
      reasoningLevels.forEach(reasoning => {
        if (dataByModelAndReasoning[model][reasoning]) {
          const { totalTests, successfulTests } = dataByModelAndReasoning[model][reasoning];
          dataByModelAndReasoning[model][reasoning].asr = 
            totalTests > 0 ? (successfulTests / totalTests) * 100 : 0;
        }
      });
    });
    
    // 3. Create chart data for each model
    const modelChartData = [];
    
    [...uniqueModels].forEach((model, index) => {
      const modelData = reasoningLevels.map(reasoning => {
        const data = dataByModelAndReasoning[model]?.[reasoning] || {
          totalTests: 0,
          successfulTests: 0,
          asr: 0
        };
        
        return {
          model,
          reasoning,
          reasoningValue: reasoningOrder[reasoning],
          asr: data.asr,
          totalTests: data.totalTests,
          color: COLORS[index % COLORS.length]
        };
      }).filter(d => d.totalTests > 0);
      
      if (modelData.length > 0) {
        modelChartData.push({
          model,
          data: modelData
        });
      }
    });
    
    // 4. Aggregate data for overview chart
    const aggregatedByReasoning = {};
    reasoningLevels.forEach(level => {
      aggregatedByReasoning[level] = { totalTests: 0, successfulTests: 0, asr: 0 };
    });
    
    reasoningData.forEach(row => {
      const reasoning = row.reasoning;
      aggregatedByReasoning[reasoning].totalTests += 1;
      if (row.success) {
        aggregatedByReasoning[reasoning].successfulTests += 1;
      }
    });
    
    reasoningLevels.forEach(level => {
      const { totalTests, successfulTests } = aggregatedByReasoning[level];
      aggregatedByReasoning[level].asr = 
        totalTests > 0 ? (successfulTests / totalTests) * 100 : 0;
    });
    
    const overviewData = reasoningLevels.map(level => ({
      reasoning: level,
      reasoningValue: reasoningOrder[level],
      asr: aggregatedByReasoning[level].asr,
      totalTests: aggregatedByReasoning[level].totalTests
    })).filter(d => d.totalTests > 0);
    
    // 5. Create data for model/reasoning relationship scatter plot
    const relationshipData = [];
    
    [...uniqueModels].forEach((model, index) => {
      const modelSize = MODEL_SIZES[model] || 0;
      
      reasoningLevels.forEach(reasoning => {
        if (dataByModelAndReasoning[model]?.[reasoning]?.totalTests > 0) {
          relationshipData.push({
            model,
            reasoning,
            reasoningValue: reasoningOrder[reasoning],
            asr: dataByModelAndReasoning[model][reasoning].asr,
            totalTests: dataByModelAndReasoning[model][reasoning].totalTests,
            modelSize,
            color: COLORS[index % COLORS.length]
          });
        }
      });
    });
    
    return {
      overviewData,
      modelData: modelChartData,
      relationshipData,
      hasReasoningData: true,
      uniqueModels: [...uniqueModels]
    };
  }, [data]);
  
  // Render chart type selector
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
  
  // Render model selector
  const renderModelSelector = () => (
    <div className="mb-4">
      <label className="block text-sm font-medium mb-1">Select Model:</label>
      <select 
        className="w-full p-2 border rounded"
        value={selectedModel || ''}
        onChange={(e) => setSelectedModel(e.target.value)}
      >
        <option value="">All Models (Overview)</option>
        {processedData.uniqueModels.map(model => (
          <option key={model} value={model}>{model}</option>
        ))}
      </select>
    </div>
  );
  
  // Render overview bar chart
  const renderOverviewChart = () => {
    if (!processedData.hasReasoningData || processedData.overviewData.length === 0) {
      return (
        <div className="p-4 bg-yellow-50 text-yellow-800 rounded">
          No reasoning data available. The dataset should include a 'reasoning' column with values: "none", "low", "medium", or "high".
        </div>
      );
    }
    
    return (
      <div className="chart-container">
        <h3 className="text-lg font-medium mb-2">Overall Attack Success Rate by Reasoning Effort</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart
            data={processedData.overviewData}
            margin={{ top: 20, right: 30, left: 20, bottom: 50 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="reasoning" 
              label={{ value: 'Reasoning Effort', position: 'bottom', offset: 20 }}
            />
            <YAxis 
              label={{ value: 'Attack Success Rate (%)', angle: -90, position: 'insideLeft' }}
              domain={[0, 100]}
            />
            <Tooltip 
              formatter={(value, name) => {
                if (name === 'asr') return [`${value.toFixed(2)}%`, 'Success Rate'];
                return [value, name];
              }}
              labelFormatter={(value) => `Reasoning: ${value}`}
            />
            <Legend />
            <Bar dataKey="asr" fill="#8884d8" name="ASR (%)">
              <LabelList 
                dataKey="totalTests" 
                position="top" 
                content={(props) => {
                  const { x, y, width, value } = props;
                  return (
                    <text 
                      x={x + width / 2} 
                      y={y - 10} 
                      fill="#666" 
                      textAnchor="middle"
                      fontSize="12"
                    >
                      {`n=${value}`}
                    </text>
                  );
                }}
              />
              {processedData.overviewData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };
  
  // Render model-specific bar chart
  const renderModelChart = () => {
    if (!selectedModel || !processedData.hasReasoningData) return null;
    
    const modelData = processedData.modelData.find(m => m.model === selectedModel);
    if (!modelData || modelData.data.length === 0) {
      return (
        <div className="p-4 bg-yellow-50 text-yellow-800 rounded">
          No reasoning data available for the selected model.
        </div>
      );
    }
    
    return (
      <div className="chart-container mt-6">
        <h3 className="text-lg font-medium mb-2">Attack Success Rate by Reasoning Effort for {selectedModel}</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart
            data={modelData.data}
            margin={{ top: 20, right: 30, left: 20, bottom: 50 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="reasoning" 
              label={{ value: 'Reasoning Effort', position: 'bottom', offset: 20 }}
            />
            <YAxis 
              label={{ value: 'Attack Success Rate (%)', angle: -90, position: 'insideLeft' }}
              domain={[0, 100]}
            />
            <Tooltip 
              formatter={(value, name) => {
                if (name === 'asr') return [`${value.toFixed(2)}%`, 'Success Rate'];
                return [value, name];
              }}
              labelFormatter={(value) => `Reasoning: ${value}`}
            />
            <Legend />
            <Bar dataKey="asr" fill={modelData.data[0].color} name="ASR (%)">
              <LabelList 
                dataKey="totalTests" 
                position="top" 
                content={(props) => {
                  const { x, y, width, value } = props;
                  return (
                    <text 
                      x={x + width / 2} 
                      y={y - 10} 
                      fill="#666" 
                      textAnchor="middle"
                      fontSize="12"
                    >
                      {`n=${value}`}
                    </text>
                  );
                }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };
  
  // Render scatter plot
  const renderScatterPlot = () => {
    if (!processedData.hasReasoningData || processedData.relationshipData.length === 0) {
      return null;
    }
    
    return (
      <div className="chart-container mt-6">
        <h3 className="text-lg font-medium mb-2">Relationship Between Reasoning Effort and Attack Success</h3>
        <ResponsiveContainer width="100%" height={500}>
          <ScatterChart
            margin={{ top: 20, right: 30, left: 20, bottom: 50 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="reasoningValue" 
              type="number"
              domain={[0, 3]}
              tickCount={4}
              tickFormatter={(value) => {
                const labels = ["none", "low", "medium", "high"];
                return labels[value] || '';
              }}
              label={{ value: 'Reasoning Effort', position: 'bottom', offset: 20 }}
            />
            <YAxis 
              dataKey="asr"
              label={{ value: 'Attack Success Rate (%)', angle: -90, position: 'insideLeft' }}
              domain={[0, 100]}
            />
            <ZAxis 
              dataKey="totalTests" 
              range={[40, 400]} 
              name="Sample Count"
            />
            <Tooltip 
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white p-2 border rounded shadow">
                      <p className="font-medium">{data.model}</p>
                      <p>Reasoning: {data.reasoning}</p>
                      <p>Success Rate: {data.asr.toFixed(2)}%</p>
                      <p>Sample Count: {data.totalTests}</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend 
              payload={
                [...new Set(processedData.relationshipData.map(d => d.model))].map((model, index) => ({
                  value: model,
                  type: 'circle',
                  color: COLORS[index % COLORS.length]
                }))
              }
            />
            {processedData.uniqueModels.map((model, index) => {
              const modelData = processedData.relationshipData.filter(d => d.model === model);
              return (
                <Scatter 
                  key={model}
                  name={model}
                  data={modelData}
                  fill={COLORS[index % COLORS.length]}
                />
              );
            })}
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    );
  };
  
  // Render key insights
  const renderKeyInsights = () => {
    if (!processedData.hasReasoningData) return null;
    
    // Calculate average ASR across reasoning levels
    const avgByReasoning = {};
    
    processedData.overviewData.forEach(data => {
      avgByReasoning[data.reasoning] = data.asr;
    });
    
    // Find best reasoning level
    let bestReasoning = null;
    let bestASR = -1;
    
    Object.entries(avgByReasoning).forEach(([reasoning, asr]) => {
      if (asr > bestASR) {
        bestASR = asr;
        bestReasoning = reasoning;
      }
    });
    
    return (
      <div className="mt-6 p-4 bg-blue-50 rounded">
        <h3 className="text-md font-medium mb-2">Key Insights</h3>
        <ul className="list-disc pl-5 text-sm space-y-2">
          <li>This analysis shows how reasoning effort affects attack success rate (ASR).</li>
          {bestReasoning && (
            <li>Overall, <strong>{bestReasoning}</strong> reasoning shows the highest success rate at <strong>{bestASR.toFixed(1)}%</strong>.</li>
          )}
          <li>Different models may respond differently to varying levels of reasoning.</li>
          <li>Select a specific model from the dropdown to see its reasoning profile.</li>
        </ul>
      </div>
    );
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">Reasoning Analysis</h2>
        <p className="text-gray-600">
          This analysis explores the relationship between reasoning effort and attack success rate.
          Data includes examples with reasoning values: "none", "low", "medium", or "high".
        </p>
      </div>
      
      {!processedData.hasReasoningData ? (
        <div className="p-6 bg-gray-100 rounded text-center">
          <p className="text-lg">
            No reasoning data available. This analysis requires a 'reasoning' column
            with values: "none", "low", "medium", or "high".
          </p>
        </div>
      ) : (
        <div className="flex flex-wrap -mx-2">
          <div className="w-full md:w-1/4 px-2">
            {renderModelSelector()}
            {renderChartTypeSelector()}
            {renderKeyInsights()}
          </div>
          
          <div className="w-full md:w-3/4 px-2">
            {chartType === "bar" ? (
              <>
                {!selectedModel && renderOverviewChart()}
                {selectedModel && renderModelChart()}
              </>
            ) : (
              renderScatterPlot()
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ReasoningAnalysis; 