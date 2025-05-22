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

// Shape types for exact vs estimated values
const EXACT_SHAPE = 'circle';
const ESTIMATE_SHAPE = 'triangle';

const SizeAnalysis = ({ data, modelComparisonData }) => {
  const [metric, setMetric] = useState("success");
  const [logScale, setLogScale] = useState(true);
  const [turnType, setTurnType] = useState("all"); // "single", "multi", or "all"
  
  // Process data for visualization
  const processedData = useMemo(() => {
    if (!data || !modelComparisonData || modelComparisonData.length === 0) {
      return { models: [], familyGroups: {} };
    }
    
    // Map model names to sizes from modelComparisonData
    const modelSizes = {};
    const modelFamilies = {};
    const parameterAccuracy = {}; // Track if parameter is exact or estimated
    
    // First pass: exact matches only
    for (const model of modelComparisonData) {
      if (model.model_name && model.parameters) {
        modelSizes[model.model_name] = parseFloat(model.parameters);
        // Store parameter accuracy information
        parameterAccuracy[model.model_name] = model["Parameter Accuracy"] === "exact" ? "exact" : "estimate";
        
        // Extract model family
        const nameParts = model.model_name.toLowerCase().split(/[-\s]/);
        if (nameParts.length > 0) {
          const family = nameParts[0];
          modelFamilies[model.model_name] = family;
        }
      } else if (model.Model && model.Parameters) {
        // Handle the CSV format from model_comparison.csv
        const modelName = model.Model;
        modelSizes[modelName] = parseFloat(model.Parameters);
        // Store parameter accuracy information
        parameterAccuracy[modelName] = model["Parameter Accuracy"] === "exact" ? "exact" : "estimate";
        
        const nameParts = modelName.toLowerCase().split(/[-\s\/]/);
        if (nameParts.length > 0) {
          const family = nameParts[0];
          modelFamilies[modelName] = family;
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
        let size = modelSizes[modelName];
        
        if (!size) continue; // Skip if no exact match
        
        // Separate single/multi turn test cases
        const singleTurnTestCases = modelObject.testCases?.filter(tc => {
          // Check if any rows in the test case have turn_type === 'single'
          return tc.rows?.some(row => row.turn_type === 'single');
        }) || [];
        
        const multiTurnTestCases = modelObject.testCases?.filter(tc => {
          // Check if any rows in the test case have turn_type === 'multi'
          return tc.rows?.some(row => row.turn_type === 'multi');
        }) || [];
        
        // Calculate metrics for each turn type
        const singleTurnSuccessRate = singleTurnTestCases.length > 0
          ? singleTurnTestCases.reduce((sum, tc) => sum + tc.successRate, 0) / singleTurnTestCases.length
          : 0;
        
        const singleTurnRefusalRate = singleTurnTestCases.length > 0
          ? singleTurnTestCases.reduce((sum, tc) => sum + tc.refusalRate, 0) / singleTurnTestCases.length
          : 0;
          
        const multiTurnSuccessRate = multiTurnTestCases.length > 0
          ? multiTurnTestCases.reduce((sum, tc) => sum + tc.successRate, 0) / multiTurnTestCases.length
          : 0;
        
        const multiTurnRefusalRate = multiTurnTestCases.length > 0
          ? multiTurnTestCases.reduce((sum, tc) => sum + tc.refusalRate, 0) / multiTurnTestCases.length
          : 0;
        
        // Calculate overall metrics (all test cases)
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
          isExact: parameterAccuracy[modelName] === "exact", // Add flag for exact vs estimate
          family: modelFamilies[modelName] || 'unknown',
          successRate,
          refusalRate,
          avgRounds,
          count: modelObject.testCases?.length || 0,
          // Add turn type specific metrics
          singleTurnSuccessRate,
          singleTurnRefusalRate,
          singleTurnCount: singleTurnTestCases.length,
          multiTurnSuccessRate,
          multiTurnRefusalRate,
          multiTurnCount: multiTurnTestCases.length
        };
      }
    } else {
      // Process raw data rows
      for (const row of data) {
        const modelName = row.target_model || row.model || 'unknown';
        let size = modelSizes[modelName];
        
        if (!size) continue; // Skip if no exact match
        
        if (!modelData[modelName]) {
          modelData[modelName] = {
            name: modelName,
            size,
            isExact: parameterAccuracy[modelName] === "exact", // Add flag for exact vs estimate
            family: modelFamilies[modelName] || 'unknown',
            successCount: 0,
            refusalCount: 0,
            roundSum: 0,
            totalCount: 0,
            singleTurnRows: [],
            multiTurnRows: [],
            singleTurnSuccessCount: 0,
            singleTurnRefusalCount: 0,
            singleTurnCount: 0,
            multiTurnSuccessCount: 0,
            multiTurnRefusalCount: 0,
            multiTurnCount: 0
          };
        }
        
        modelData[modelName].totalCount++;
        
        // Count success/refusal/rounds
        const isSuccess = row.goal_achieved !== undefined ? Boolean(row.goal_achieved) : 
                         row.success !== undefined ? Boolean(row.success) : 
                         row.jailbreak_success !== undefined ? Boolean(row.jailbreak_success) :
                         row.asr !== undefined ? row.asr > 0 : false;
        
        const isRefusal = row.refused !== undefined ? Boolean(row.refused) : 
                         row.refusal !== undefined ? Boolean(row.refusal) :
                         row.rejection !== undefined ? Boolean(row.rejection) : false;
        
        // Determine if single or multi-turn - prioritize turn_type field, but also check num_turns
        const isSingleTurn = row.turn_type === 'single' || 
                            (row.turn_type === undefined && (row.num_turns === 1 || !row.num_turns));
        const isMultiTurn = row.turn_type === 'multi' ||
                           (row.turn_type === undefined && row.num_turns && row.num_turns > 1);
        
        if (isSingleTurn) {
          modelData[modelName].singleTurnRows.push(row);
          modelData[modelName].singleTurnCount++;
          if (isSuccess) modelData[modelName].singleTurnSuccessCount++;
          if (isRefusal) modelData[modelName].singleTurnRefusalCount++;
        } else if (isMultiTurn) {
          modelData[modelName].multiTurnRows.push(row);
          modelData[modelName].multiTurnCount++;
          if (isSuccess) modelData[modelName].multiTurnSuccessCount++;
          if (isRefusal) modelData[modelName].multiTurnRefusalCount++;
        }
        
        if (isSuccess) modelData[modelName].successCount++;
        if (isRefusal) modelData[modelName].refusalCount++;
        
        const rounds = row.num_turns || row.rounds || row.turn_count || 0;
        modelData[modelName].roundSum += rounds;
      }
      
      // Calculate rates
      for (const modelName in modelData) {
        const model = modelData[modelName];
        
        // Overall metrics
        if (model.totalCount > 0) {
          model.successRate = (model.successCount / model.totalCount) * 100;
          model.refusalRate = (model.refusalCount / model.totalCount) * 100;
          model.avgRounds = model.roundSum / model.totalCount;
          model.count = model.totalCount;
        }
        
        // Single-turn metrics
        if (model.singleTurnCount > 0) {
          model.singleTurnSuccessRate = (model.singleTurnSuccessCount / model.singleTurnCount) * 100;
          model.singleTurnRefusalRate = (model.singleTurnRefusalCount / model.singleTurnCount) * 100;
        } else {
          model.singleTurnSuccessRate = 0;
          model.singleTurnRefusalRate = 0;
        }
        
        // Multi-turn metrics
        if (model.multiTurnCount > 0) {
          model.multiTurnSuccessRate = (model.multiTurnSuccessCount / model.multiTurnCount) * 100;
          model.multiTurnRefusalRate = (model.multiTurnRefusalCount / model.multiTurnCount) * 100;
        } else {
          model.multiTurnSuccessRate = 0;
          model.multiTurnRefusalRate = 0;
        }
      }
    }
    
    // Convert to array and group by family
    const families = {};
    const result = [];
    
    for (const modelName in modelData) {
      const model = modelData[modelName];
      
      // Skip models with no data for selected turn type
      if (turnType === 'single' && model.singleTurnCount === 0) continue;
      if (turnType === 'multi' && model.multiTurnCount === 0) continue;
      
      if (!families[model.family]) {
        families[model.family] = [];
      }
      
      families[model.family].push(model);
      result.push(model);
    }
    
    // Sort result by size
    result.sort((a, b) => a.size - b.size);
    
    // Group by family
    Object.keys(families).forEach(family => {
      families[family].sort((a, b) => a.size - b.size);
    });
    
    return {
      models: result,
      familyGroups: families
    };
  }, [data, modelComparisonData, turnType]);
  
  // Choose which metric to display based on turnType and metric selection
  const getMetricValue = (model) => {
    if (metric === 'success') {
      if (turnType === 'single') return model.singleTurnSuccessRate || 0;
      if (turnType === 'multi') return model.multiTurnSuccessRate || 0;
      return model.successRate || 0;
    } else if (metric === 'refusal') {
      if (turnType === 'single') return model.singleTurnRefusalRate || 0;
      if (turnType === 'multi') return model.multiTurnRefusalRate || 0;
      return model.refusalRate || 0;
    } else {
      return model.avgRounds || 0;
    }
  };
  
  // Get chart data based on selected metric
  const chartData = useMemo(() => {
    if (!processedData.models || processedData.models.length === 0) {
      return [];
    }
    
    return processedData.models.map(model => ({
      ...model,
      value: getMetricValue(model),
      size: model.size
    }));
  }, [processedData, metric, turnType]);
  
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
      <h3 className="text-md font-semibold mb-2">Select Metric</h3>
      <div className="flex flex-wrap gap-2">
        <button
          className={`px-3 py-1 rounded ${metric === 'success' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => setMetric('success')}
        >
          Success Rate
        </button>
        <button
          className={`px-3 py-1 rounded ${metric === 'refusal' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => setMetric('refusal')}
        >
          Refusal Rate
        </button>
        <button
          className={`px-3 py-1 rounded ${metric === 'rounds' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => setMetric('rounds')}
        >
          Avg. Rounds
        </button>
      </div>
    </div>
  );
  
  // Render turn type selector
  const renderTurnTypeSelector = () => (
    <div className="mb-4">
      <h3 className="text-md font-semibold mb-2">Turn Type</h3>
      <div className="flex flex-wrap gap-2">
        <button
          className={`px-3 py-1 rounded ${turnType === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => setTurnType('all')}
        >
          All Turns
        </button>
        <button
          className={`px-3 py-1 rounded ${turnType === 'single' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => setTurnType('single')}
        >
          Single Turn
        </button>
        <button
          className={`px-3 py-1 rounded ${turnType === 'multi' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => setTurnType('multi')}
        >
          Multi Turn
        </button>
      </div>
    </div>
  );
  
  // Render scale toggler
  const renderScaleToggler = () => (
    <div className="mb-4">
      <h3 className="text-md font-semibold mb-2">X-Axis Scale</h3>
      <div className="flex flex-wrap gap-2">
        <button
          className={`px-3 py-1 rounded ${logScale ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => setLogScale(true)}
        >
          Log Scale
        </button>
        <button
          className={`px-3 py-1 rounded ${!logScale ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => setLogScale(false)}
        >
          Linear Scale
        </button>
      </div>
    </div>
  );
  
  // Render the scatter plot
  const renderScatterPlot = () => {
    if (!chartData || chartData.length === 0) {
      return (
        <div className="flex justify-center items-center h-96 bg-slate-50">
          <p className="text-slate-500">No data available</p>
        </div>
      );
    }

    // Separate models into exact and estimated size categories
    const exactSizeModels = {};
    const estimatedSizeModels = {};
    
    // Group models by family
    Object.keys(processedData.familyGroups).forEach(family => {
      exactSizeModels[family] = chartData.filter(model => 
        model.family === family && model.isExact && 
        (turnType === 'single' ? model.singleTurnCount > 0 : 
         turnType === 'multi' ? model.multiTurnCount > 0 : true));
         
      estimatedSizeModels[family] = chartData.filter(model => 
        model.family === family && !model.isExact && 
        (turnType === 'single' ? model.singleTurnCount > 0 : 
         turnType === 'multi' ? model.multiTurnCount > 0 : true));
    });
    
    // Get x-axis domain from all data
    const sizes = chartData.map(model => model.size).filter(size => size !== undefined && size !== null);
    const minSize = Math.min(...sizes);
    const maxSize = Math.max(...sizes);
    const xDomain = [Math.max(0.9, minSize * 0.9), maxSize * 1.1];
    
    // Get y-axis domain based on metric
    const values = chartData.map(model => model.value).filter(value => value !== undefined && value !== null);
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const yDomain = metric === 'rounds' 
      ? [Math.max(0, minValue * 0.9), maxValue * 1.1]
      : [0, 100];
    
    // Get the metric label with turn type indication
    let metricLabel = metric === 'success' ? 'Success Rate (%)' : 
                       metric === 'refusal' ? 'Refusal Rate (%)' : 'Avg. Rounds';
    
    // Add turn type to label when specific type is selected
    if (turnType === 'single') {
      metricLabel = `Single-Turn ${metricLabel}`;
    } else if (turnType === 'multi') {
      metricLabel = `Multi-Turn ${metricLabel}`;
    }
    
    // Format tooltip label
    const formatTooltip = (value, name, props) => {
      if (value === undefined || value === null) return 'N/A';
      
      if (metric === 'rounds') {
        return value.toFixed(1);
      } else {
        return `${value.toFixed(1)}%`;
      }
    };
    
    return (
      <div className="bg-white p-4 rounded">
        <ResponsiveContainer width="100%" height={500}>
          <ScatterChart
            margin={{ top: 20, right: 30, bottom: 10, left: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              type="number" 
              dataKey="size"
              name="Model Size"
              domain={xDomain}
              scale="log"
              allowDataOverflow={true}
              label={{ value: 'Model Size (billions)', position: 'bottom', offset: 0 }}
              tickFormatter={(size) => size === 1 ? '1B' : size < 10 ? `${size}B` : `${size}B`}
            />
            <YAxis 
              type="number" 
              dataKey="value"
              name={metricLabel}
              domain={yDomain}
              allowDataOverflow={true}
              label={{ value: metricLabel, angle: -90, position: 'insideLeft' }}
            />
            <Tooltip 
              formatter={formatTooltip}
              labelFormatter={(label) => {
                const model = chartData.find(m => m.size === label);
                if (model) {
                  return `${model.name} (${model.isExact ? 'Exact' : 'Estimated'} Size: ${model.size}B)`;
                }
                return `${label}B parameters`;
              }}
              cursor={{ strokeDasharray: '3 3' }}
            />
            <Legend />
            
            {/* Render exact size models by family */}
            {Object.entries(exactSizeModels).map(([family, models]) => {
              if (!models || models.length === 0) return null;
                           
              return (
                <Scatter 
                  key={`${family}-exact`} 
                  name={`${family} (Exact)`} 
                  data={models} 
                  fill={familyColors[family]}
                  shape={EXACT_SHAPE}
                >
                  {models.map((entry, index) => (
                    <Cell key={`cell-exact-${family}-${index}-${entry.name}`} fill={familyColors[entry.family]} />
                  ))}
                </Scatter>
              );
            })}
            
            {/* Render estimated size models by family */}
            {Object.entries(estimatedSizeModels).map(([family, models]) => {
              if (!models || models.length === 0) return null;
              
              return (
                <Scatter 
                  key={`${family}-estimated`} 
                  name={`${family} (Estimated)`} 
                  data={models}
                  fill={familyColors[family]}
                  shape={ESTIMATE_SHAPE}
                >
                  {models.map((entry, index) => (
                    <Cell key={`cell-estimated-${family}-${index}-${entry.name}`} fill={familyColors[entry.family]} />
                  ))}
                </Scatter>
              );
            })}
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    );
  };
  
  // Generate summary statistics
  const renderSummary = () => {
    if (!chartData || chartData.length === 0) {
      return (
        <div className="bg-white p-4 rounded mb-4">
          <h3 className="text-lg font-medium mb-2">Summary</h3>
          <p className="text-slate-500">No data available</p>
        </div>
      );
    }
    
    // Filter models with valid sizes
    const modelsWithSizes = chartData.filter(model => 
      model.size !== undefined && model.size !== null
    );
    
    if (modelsWithSizes.length === 0) {
      return (
        <div className="bg-white p-4 rounded mb-4">
          <h3 className="text-lg font-medium mb-2">Summary</h3>
          <p className="text-slate-500">No models with valid sizes</p>
        </div>
      );
    }
    
    // Group models by size range
    const smallModels = modelsWithSizes.filter(model => model.size < 10).length;
    const mediumModels = modelsWithSizes.filter(model => model.size >= 10 && model.size < 50).length;
    const largeModels = modelsWithSizes.filter(model => model.size >= 50).length;
    
    // Count exact vs estimated sizes
    const exactSizes = modelsWithSizes.filter(model => model.isExact).length;
    const estimatedSizes = modelsWithSizes.length - exactSizes;
    
    // Get the largest and smallest model
    modelsWithSizes.sort((a, b) => b.size - a.size);
    const largestModel = modelsWithSizes[0];
    const smallestModel = modelsWithSizes[modelsWithSizes.length - 1];
    
    return (
      <div className="bg-white p-4 rounded mb-4">
        <h3 className="text-lg font-medium mb-2">Summary</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="mb-1"><span className="font-medium">Total models:</span> {modelsWithSizes.length}</p>
            <p className="mb-1"><span className="font-medium">Small models (&lt;10B params):</span> {smallModels}</p>
            <p className="mb-1"><span className="font-medium">Medium models (10-50B params):</span> {mediumModels}</p>
            <p className="mb-1"><span className="font-medium">Large models (&gt;50B params):</span> {largeModels}</p>
          </div>
          <div>
            <p className="mb-1"><span className="font-medium">Models with exact sizes:</span> {exactSizes}</p>
            <p className="mb-1"><span className="font-medium">Models with estimated sizes:</span> {estimatedSizes}</p>
            {largestModel && (
              <p className="mb-1">
                <span className="font-medium">Largest model:</span> {largestModel.name} ({largestModel.size}B)
              </p>
            )}
            {smallestModel && (
              <p className="mb-1">
                <span className="font-medium">Smallest model:</span> {smallestModel.name} ({smallestModel.size}B)
              </p>
            )}
          </div>
        </div>
      </div>
    );
  };
  
  const renderTopModels = () => {
    if (!chartData || chartData.length === 0) {
      return (
        <div className="bg-white p-4 rounded">
          <h3 className="text-lg font-medium mb-2">Top Models</h3>
          <p className="text-slate-500">No data available</p>
        </div>
      );
    }
    
    // Filter out models with missing values
    const modelsWithValues = chartData.filter(model => 
      model.value !== undefined && model.value !== null
    );
    
    if (modelsWithValues.length === 0) {
      return (
        <div className="bg-white p-4 rounded">
          <h3 className="text-lg font-medium mb-2">Top Models</h3>
          <p className="text-slate-500">No models with valid values</p>
        </div>
      );
    }
    
    // Sort models by the selected metric (highest to lowest)
    // For refusal rate, lower is better so we reverse the order
    const sortedByMetric = [...modelsWithValues].sort((a, b) => 
      metric === 'refusal' ? a.value - b.value : b.value - a.value
    );
    
    // Get top 5 models
    const topModels = sortedByMetric.slice(0, 5);
    
    return (
      <div className="bg-white p-4 rounded">
        <h3 className="text-lg font-medium mb-2">Top Models by {
          metric === 'success' ? 'Success Rate' : 
          metric === 'refusal' ? 'Refusal Rate' : 'Avg. Rounds'
        }</h3>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Model</th>
                <th className="text-right py-2">Size</th>
                <th className="text-right py-2">
                  {metric === 'success' ? 'Success Rate' : 
                   metric === 'refusal' ? 'Refusal Rate' : 'Avg. Rounds'}
                </th>
              </tr>
            </thead>
            <tbody>
              {topModels.map(model => (
                <tr key={model.name} className="border-b border-gray-100">
                  <td className="py-1">{model.name}</td>
                  <td className="text-right py-1">
                    {model.size}B
                    {!model.isExact && '*'}
                  </td>
                  <td className="text-right py-1">
                    {metric === 'rounds' 
                      ? model.value.toFixed(1) 
                      : `${model.value.toFixed(1)}%`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        <div className="mt-3 text-xs text-gray-500">
          <p>* Estimated size</p>
          <p className="mt-1">
            <span className="font-medium">Size range:</span> 
            {modelsWithValues.length > 0 ? 
             ` ${Math.min(...modelsWithValues.map(m => m.size))}B - ${Math.max(...modelsWithValues.map(m => m.size))}B` : 
             ' No data'}
          </p>
          <p className="mt-1">
            <span className="font-medium">Models with exact size:</span> 
            {modelsWithValues.filter(m => m.isExact).length} of {modelsWithValues.length}
          </p>
        </div>
      </div>
    );
  };
  
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Size Analysis</h1>
      <p className="text-sm text-gray-500 mb-4">
        Explore the relationship between model size and performance metrics.
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div>
          {renderMetricSelector()}
        </div>
        <div>
          {renderTurnTypeSelector()}
        </div>
        <div>
          {renderScaleToggler()}
        </div>
      </div>
      
      {renderSummary()}
      {renderScatterPlot()}
      {renderTopModels()}
    </div>
  );
};

export default SizeAnalysis; 