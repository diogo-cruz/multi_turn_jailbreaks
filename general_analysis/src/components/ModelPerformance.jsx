import React, { useState, useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, LabelList, ErrorBar
} from 'recharts';
import { calculateStandardError } from '../utils/dataProcessing';

// Color constants
const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE', 
  '#00C49F', '#FFBB28', '#FF8042', '#a4de6c', '#d0ed57'
];

const ModelPerformance = ({ data, selectedModel, onModelSelect, uniqueModels }) => {
  // Process data for visualization
  const processedData = useMemo(() => {
    if (!data || (Array.isArray(data) && data.length === 0)) {
      console.log("No data available");
      return [];
    }
    
    // Check if data is already processed (models array)
    if (Array.isArray(data) && data[0] && typeof data[0] === 'object' && 'name' in data[0] && 'rows' in data[0]) {
      console.log("Using pre-processed model data");
      
      // Return data as is if ASR metrics are already calculated
      if (data[0].singleTurnASR !== undefined && data[0].multiTurnASR !== undefined) {
        return data;
      }
      
      // Format data into the expected structure if needed
      return data.map(model => {
        // Calculate metrics if they don't exist
        if (!('successRate' in model)) {
          // Extract rows for calculation
          const rows = model.rows || [];
          
          // Success rate
          let successCount = 0;
          for (const row of rows) {
            if (row.goal_achieved === true || row.success === true || 
                row.jailbreak_success === true || 
                (row.asr !== undefined && row.asr > 0) ||
                row.attack_success === true ||
                row.is_success === true) {
              successCount++;
            }
          }
          const successRate = rows.length > 0 ? (successCount / rows.length) * 100 : 0;
          
          // Refusal rate
          let refusalCount = 0;
          for (const row of rows) {
            if (row.refused === true || 
                row.refusal === true || 
                row.rejection === true ||
                row.is_rejected === true) {
              refusalCount++;
            }
          }
          const refusalRate = rows.length > 0 ? (refusalCount / rows.length) * 100 : 0;
          
          // Calculate average rounds
          const roundsData = rows
            .filter(row => row.num_turns !== undefined || row.rounds !== undefined || row.turn_count !== undefined)
            .map(row => {
              const value = row.num_turns !== undefined ? row.num_turns : 
                          row.rounds !== undefined ? row.rounds :
                          row.turn_count !== undefined ? row.turn_count : 0;
              return typeof value === 'number' ? value : 0;
            });
          
          const avgRounds = roundsData.length > 0 
            ? roundsData.reduce((sum, val) => sum + val, 0) / roundsData.length 
            : 0;
          
          return {
            ...model,
            successRate,
            refusalRate,
            avgRounds,
            count: rows.length
          };
        }
        
        return model;
      });
    }
    
    console.log("Processing raw data, sample:", data.slice(0, 3)); // Debug log
    
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
    const result = Object.entries(modelData).map(([modelName, rows]) => {
      // For debugging
      if (modelName === Object.keys(modelData)[0]) {
        console.log(`Sample row for ${modelName}:`, rows[0]);
      }
      
      // Calculate success rate - check multiple possible field names
      let successCount = 0;
      for (const row of rows) {
        if (row.goal_achieved === true || row.success === true || 
            row.jailbreak_success === true || 
            (row.asr !== undefined && row.asr > 0) ||
            row.attack_success === true ||
            row.is_success === true) {
          successCount++;
        }
      }
      const successRate = rows.length > 0 ? (successCount / rows.length) * 100 : 0;
      
      // Calculate refusal rate - check multiple possible field names
      let refusalCount = 0;
      for (const row of rows) {
        if (row.refused === true || 
            row.refusal === true || 
            row.rejection === true ||
            row.is_rejected === true) {
          refusalCount++;
        }
      }
      const refusalRate = rows.length > 0 ? (refusalCount / rows.length) * 100 : 0;
      
      // Calculate average rounds - check multiple possible field names
      const roundsData = rows
        .filter(row => row.num_turns !== undefined || row.rounds !== undefined || row.turn_count !== undefined)
        .map(row => {
          const value = row.num_turns !== undefined ? row.num_turns : 
                       row.rounds !== undefined ? row.rounds :
                       row.turn_count !== undefined ? row.turn_count : 0;
          return typeof value === 'number' ? value : 0;
        });
      
      const avgRounds = roundsData.length > 0 
        ? roundsData.reduce((sum, val) => sum + val, 0) / roundsData.length 
        : 0;
      
      // Calculate standard errors
      const successStdErr = calculateStandardError(rows.map(() => successRate));
      const roundsStdErr = calculateStandardError(roundsData);
      
      // Calculate non-zero temperature entries for warning
      const nonZeroTempRows = rows.filter(row => 
        row.target_model_temperature && row.target_model_temperature !== 0
      );
      
      return {
        name: modelName,
        successRate,
        refusalRate,
        avgRounds,
        successStdErr,
        roundsStdErr,
        count: rows.length,
        skippedTemperatureEntries: nonZeroTempRows.length,
        rows // Keep the original rows for reference
      };
    });
    
    console.log("Processed data:", result.slice(0, 3)); // Debug log
    return result;
  }, [data]);
  
  // Sum up all skipped temperature entries
  const totalSkippedEntries = useMemo(() => {
    if (!processedData || processedData.length === 0) return 0;
    
    return processedData.reduce((total, model) => {
      return total + (model.skippedTemperatureEntries || 0);
    }, 0);
  }, [processedData]);
  
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
      
      {totalSkippedEntries > 0 && (
        <div className="mt-2 p-2 bg-yellow-100 border border-yellow-300 rounded text-sm">
          Warning: {totalSkippedEntries} entries with non-zero target model temperature were excluded from ASR calculations.
        </div>
      )}
    </div>
  );
  
  // Render a bar chart for model comparison
  const renderBarChart = () => {
    if (!processedData || processedData.length === 0) {
      return <div>No data available</div>;
    }
    
    // Sort models alphabetically
    const alphabeticallySorted = [...processedData].sort((a, b) => a.name.localeCompare(b.name));
    
    // Create chart data with both single-turn and multi-turn values and standard errors
    const chartData = alphabeticallySorted.map(model => {
      // Ensure values are valid numbers
      const singleTurn = typeof model.singleTurnASR === "number" ? model.singleTurnASR : 
                         Number(model.singleTurnASR || 0);
      const multiTurn = typeof model.multiTurnASR === "number" ? model.multiTurnASR : 
                        Number(model.multiTurnASR || 0);
      
      // Debug test case rates availability
      console.log(`Model ${model.name} data:`, {
        hasSingleTurn: !!model.singleTurn,
        hasMultiTurn: !!model.multiTurn,
        singleTurnRates: model.singleTurn ? model.singleTurn.testCaseRates : 'N/A',
        multiTurnRates: model.multiTurn ? model.multiTurn.testCaseRates : 'N/A'
      });
      
      // Calculate standard errors for ASR values - only if we have actual test case data
      let singleTurnError = null; // No default fallback value - will skip error bars if null
      let multiTurnError = null;  // No default fallback value - will skip error bars if null
      let hasInsufficientData = false; // Flag to indicate models with insufficient data
      
      // Try to get actual error values from test case rates if available
      if (model.singleTurn && Array.isArray(model.singleTurn.testCaseRates) && model.singleTurn.testCaseRates.length > 1) {
        singleTurnError = calculateStandardError(model.singleTurn.testCaseRates);
        console.log(`Calculated SE for ${model.name} single-turn: ${singleTurnError.toFixed(2)}% from ${model.singleTurn.testCaseRates.length} test cases`);
      } else if (singleTurn > 0) {
        hasInsufficientData = true;
        console.log(`Insufficient data for ${model.name} single-turn error bars`);
      }
      
      if (model.multiTurn && Array.isArray(model.multiTurn.testCaseRates) && model.multiTurn.testCaseRates.length > 1) {
        multiTurnError = calculateStandardError(model.multiTurn.testCaseRates);
        console.log(`Calculated SE for ${model.name} multi-turn: ${multiTurnError.toFixed(2)}% from ${model.multiTurn.testCaseRates.length} test cases`);
      } else if (multiTurn > 0) {
        hasInsufficientData = true;
        console.log(`Insufficient data for ${model.name} multi-turn error bars`);
      }
                          
      return {
        name: model.name,
        singleTurn: isNaN(singleTurn) ? 0 : singleTurn,
        multiTurn: isNaN(multiTurn) ? 0 : multiTurn,
        singleTurnError: singleTurnError,
        multiTurnError: multiTurnError,
        hasInsufficientData: hasInsufficientData
      };
    });
    
    // Debug chart data
    console.log("Chart data for side-by-side ASR comparison:");
    console.log("First 5 chart data points:", chartData.slice(0, 5));
    
    // Ensure there's actual data to display
    if (chartData.length === 0) {
      return <div>No data available for ASR comparison</div>;
    }
    
    // Find maximum value for domain scaling (max across both single and multi-turn)
    const maxSingleTurn = Math.max(...chartData.map(item => item.singleTurn));
    const maxMultiTurn = Math.max(...chartData.map(item => item.multiTurn));
    const maxValue = Math.max(maxSingleTurn, maxMultiTurn);
    console.log("Max values - Single:", maxSingleTurn, "Multi:", maxMultiTurn);
    
    // Set domain to max 100% for percentage data
    const domainMax = 100;
    
    return (
      <div className="chart-container">
        <h3 className="text-lg font-medium mb-2">
          Attack Success Rate (ASR) Comparison
        </h3>
        <ResponsiveContainer width="100%" height={Math.max(500, chartData.length * 40)}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 20, right: 120, left: 150, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              type="number"
              domain={[0, domainMax]}
              tickFormatter={(value) => `${value}%`}
              label={{ 
                value: 'Attack Success Rate (%)',
                position: 'insideBottom',
                offset: -10
              }}
            />
            <YAxis 
              dataKey="name"
              type="category"
              width={140}
              interval={0}
              tick={{ textAnchor: 'end' }}
            />
            <Tooltip 
              formatter={(value, name, props) => {
                // Safety check for undefined props
                if (!props || !props.payload) {
                  return [value.toFixed(2) + '%', name === 'singleTurn' ? 'Single-Turn ASR' : 'Multi-Turn ASR'];
                }
                
                // Get the error value based on which bar is hovered
                const errorValue = name === 'singleTurn' ? 
                  props.payload.singleTurnError : 
                  props.payload.multiTurnError;
                  
                // Return formatted value with standard error if available
                const formattedValue = `${value.toFixed(2)}%`;
                const displayName = name === 'singleTurn' ? 'Single-Turn ASR' : 'Multi-Turn ASR';
                
                if (errorValue !== null) {
                  return [`${formattedValue} ± ${errorValue.toFixed(2)}%`, displayName];
                } else if (value > 0) {
                  return [`${formattedValue} (no error bars*)`, displayName];
                } else {
                  return [formattedValue, displayName];
                }
              }}
            />
            <Legend />
            <Bar 
              dataKey="singleTurn" 
              name="Single-Turn ASR"
              fill="#8884d8"
            >
              <LabelList 
                dataKey="singleTurn" 
                position="right" 
                formatter={(value, entry) => {
                  // Add null check to prevent "entry is undefined" error
                  if (!entry || entry.payload === undefined) return `${value.toFixed(1)}%`;
                  const hasNoError = entry.payload.singleTurnError === null && entry.payload.singleTurn > 0;
                  return `${value.toFixed(1)}%${hasNoError ? ' *' : ''}`;
                }}
                style={{ fontWeight: 'bold' }}
              />
              {/* Only show error bars if we have actual error data */}
              <ErrorBar 
                dataKey="singleTurnError" 
                width={4} 
                strokeWidth={2} 
                stroke="#000000" 
                direction="x"
              />
            </Bar>
            <Bar 
              dataKey="multiTurn" 
              name="Multi-Turn ASR"
              fill="#82ca9d"
            >
              <LabelList 
                dataKey="multiTurn" 
                position="right" 
                formatter={(value, entry) => {
                  // Add null check to prevent "entry is undefined" error
                  if (!entry || entry.payload === undefined) return `${value.toFixed(1)}%`;
                  const hasNoError = entry.payload.multiTurnError === null && entry.payload.multiTurn > 0;
                  return `${value.toFixed(1)}%${hasNoError ? ' *' : ''}`;
                }}
                style={{ fontWeight: 'bold' }}
              />
              {/* Only show error bars if we have actual error data */}
              <ErrorBar 
                dataKey="multiTurnError" 
                width={4} 
                strokeWidth={2} 
                stroke="#000000" 
                direction="x"
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        {/* Add explanation for the * symbol if any model has insufficient data */}
        {chartData.some(item => item.hasInsufficientData) && (
          <div className="mt-2 text-xs text-red-600">
            * Models with insufficient test case data (fewer than 2 test cases) do not show error bars.
          </div>
        )}
      </div>
    );
  };
  
  // Render details for selected model
  const renderModelDetails = () => {
    if (!selectedModelData) {
      return <div>Select a model to view details</div>;
    }
    
    // Ensure we have all required properties or provide defaults
    const refusalRate = selectedModelData.refusalRate !== undefined ? selectedModelData.refusalRate : 0;
    const avgRounds = selectedModelData.avgRounds !== undefined ? selectedModelData.avgRounds : 0;
    const singleTurnASR = selectedModelData.singleTurnASR !== undefined ? selectedModelData.singleTurnASR : 0;
    const multiTurnASR = selectedModelData.multiTurnASR !== undefined ? selectedModelData.multiTurnASR : 0;
    const singleTurnTestCases = selectedModelData.singleTurnTestCases || 0;
    const multiTurnTestCases = selectedModelData.multiTurnTestCases || 0;
    const count = selectedModelData.count || 0;
    const skippedCount = selectedModelData.skippedTemperatureEntries || 0;
    
    // Calculate error bounds (standard error)
    let singleTurnError = null; // No default fallback value
    let multiTurnError = null;  // No default fallback value
    let hasInsufficientData = false;
    
    // Try to get actual error values from test case rates if available
    if (selectedModelData.singleTurn && Array.isArray(selectedModelData.singleTurn.testCaseRates) && 
        selectedModelData.singleTurn.testCaseRates.length > 1) {
      singleTurnError = calculateStandardError(selectedModelData.singleTurn.testCaseRates);
    } else if (singleTurnASR > 0) {
      hasInsufficientData = true;
    }
    
    if (selectedModelData.multiTurn && Array.isArray(selectedModelData.multiTurn.testCaseRates) && 
        selectedModelData.multiTurn.testCaseRates.length > 1) {
      multiTurnError = calculateStandardError(selectedModelData.multiTurn.testCaseRates);
    } else if (multiTurnASR > 0) {
      hasInsufficientData = true;
    }
    
    return (
      <div className="mt-8 p-4 border rounded">
        <h3 className="text-xl font-medium mb-4">{selectedModelData.name}</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-blue-50 p-4 rounded shadow">
            <h4 className="text-lg font-medium text-blue-800 mb-3">Single-Turn Performance</h4>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-600">Attack Success Rate:</span>
              <span className="text-xl font-bold">
                {singleTurnASR.toFixed(2)}%
                {singleTurnError !== null ? ` ± ${singleTurnError.toFixed(2)}%` : singleTurnASR > 0 ? ' *' : ''}
              </span>
            </div>
            <div className="text-xs text-gray-500 mb-2">{singleTurnTestCases} test cases</div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-blue-600 h-2.5 rounded-full" 
                style={{ width: `${Math.min(100, singleTurnASR)}%` }}
              ></div>
            </div>
          </div>
          
          <div className="bg-green-50 p-4 rounded shadow">
            <h4 className="text-lg font-medium text-green-800 mb-3">Multi-Turn Performance</h4>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-600">Attack Success Rate:</span>
              <span className="text-xl font-bold">
                {multiTurnASR.toFixed(2)}%
                {multiTurnError !== null ? ` ± ${multiTurnError.toFixed(2)}%` : multiTurnASR > 0 ? ' *' : ''}
              </span>
            </div>
            <div className="text-xs text-gray-500 mb-2">{multiTurnTestCases} test cases</div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-green-600 h-2.5 rounded-full" 
                style={{ width: `${Math.min(100, multiTurnASR)}%` }}
              ></div>
            </div>
          </div>
          
          <div className="bg-red-50 p-4 rounded shadow">
            <h4 className="text-lg font-medium text-red-800 mb-3">Refusal Rate</h4>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-600">Overall Refusal Rate:</span>
              <span className="text-xl font-bold">{refusalRate.toFixed(2)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-red-500 h-2.5 rounded-full" 
                style={{ width: `${Math.min(100, refusalRate)}%` }}
              ></div>
            </div>
          </div>
          
          <div className="bg-yellow-50 p-4 rounded shadow">
            <h4 className="text-lg font-medium text-yellow-800 mb-3">Conversation Data</h4>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-600">Average Rounds:</span>
              <span className="text-xl font-bold">{avgRounds.toFixed(2)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Sample Count:</span>
              <span className="text-xl font-bold">{count}</span>
            </div>
            {skippedCount > 0 && (
              <div className="mt-2 text-xs text-red-500">
                {skippedCount} entries with non-zero temperature excluded from ASR
              </div>
            )}
          </div>
        </div>
        
        {/* Add explanation for missing error bars if needed */}
        {hasInsufficientData && (
          <div className="mt-4 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-600">
            * Error ranges are not displayed when there are fewer than 2 test cases with available data.
          </div>
        )}
      </div>
    );
  };
  
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">Model Performance Analysis</h2>
        <p className="text-gray-600 mb-2">
          Compare performance metrics across different language models, 
          showing both single-turn and multi-turn Attack Success Rates (ASR) side by side.
        </p>
        <p className="text-sm text-gray-600 italic">
          ASR is calculated by taking the maximum success rate across all tactics for each test case, 
          then averaging these maximum success rates across all test cases. Single-turn and multi-turn 
          ASRs are calculated separately.
        </p>
        <p className="text-sm text-gray-600 italic mt-1">
          Error bars represent the standard error of the mean across test cases, showing the 
          statistical uncertainty in the ASR measurement. Error bars are only shown when data from 
          at least 2 test cases is available for calculation.
        </p>
      </div>
      
      <div className="flex flex-wrap -mx-2">
        <div className="w-full md:w-1/4 px-2">
          {renderModelSelector()}
        </div>
        
        <div className="w-full md:w-3/4 px-2">
          {renderBarChart()}
          {renderModelDetails()}
        </div>
      </div>
    </div>
  );
};

export default ModelPerformance; 