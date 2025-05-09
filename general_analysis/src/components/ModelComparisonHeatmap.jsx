import React, { useState, useMemo } from 'react';
import { ResponsiveContainer, Tooltip } from 'recharts';

// Custom heatmap implementation since Recharts doesn't have a built-in heatmap
const CustomHeatmap = ({ data, xLabels, yLabels, colorScale }) => {
  if (!data || !xLabels || !yLabels) return null;
  
  const cellWidth = 100 / xLabels.length;
  const cellHeight = 100 / yLabels.length;
  
  return (
    <div className="relative w-full h-full">
      {/* X-axis labels */}
      <div className="absolute top-0 left-10 right-0 flex">
        {xLabels.map((label, i) => (
          <div 
            key={`x-${i}`} 
            className="transform -rotate-45 origin-bottom-left text-xs font-medium"
            style={{ 
              width: `${cellWidth}%`, 
              height: '80px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              paddingLeft: '5px'
            }}
          >
            {label}
          </div>
        ))}
      </div>
      
      {/* Y-axis labels and heatmap cells */}
      <div className="absolute top-20 bottom-0 left-0 right-0">
        {yLabels.map((yLabel, y) => (
          <div key={`row-${y}`} className="flex" style={{ height: `${cellHeight}%` }}>
            {/* Y-axis label */}
            <div 
              className="flex items-center justify-end pr-2 text-xs font-medium"
              style={{ width: '150px', minWidth: '150px', maxWidth: '150px' }}
            >
              {yLabel}
            </div>
            
            {/* Heatmap cells for this row */}
            <div className="flex-1 flex">
              {xLabels.map((xLabel, x) => {
                const cellData = data.find(d => d.x === xLabel && d.y === yLabel);
                const value = cellData ? cellData.value : 0;
                const backgroundColor = colorScale(value);
                
                return (
                  <div
                    key={`cell-${x}-${y}`}
                    className="border border-gray-200 flex items-center justify-center text-xs"
                    style={{ 
                      width: `${cellWidth}%`,
                      height: '100%',
                      backgroundColor,
                      color: value > 50 ? 'white' : 'black'
                    }}
                    title={`${xLabel} vs ${yLabel}: ${value.toFixed(1)}%`}
                  >
                    {value.toFixed(1)}%
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const ModelComparisonHeatmap = ({ data, modelComparisonData }) => {
  const [comparisonType, setComparisonType] = useState("tactic");
  const [metric, setMetric] = useState("success");
  
  // Get color for heatmap cell based on value
  const getColorScale = (value) => {
    // Normalize value between 0 and 1 for a red-to-green gradient
    const normalized = Math.max(0, Math.min(1, value / 100));
    
    // RGB components for gradient
    const r = Math.round(255 * (1 - normalized));
    const g = Math.round(255 * normalized);
    const b = 100;
    
    return `rgb(${r}, ${g}, ${b})`;
  };
  
  // Process data for model vs tactic heatmap
  const modelTacticData = useMemo(() => {
    if (!data || (Array.isArray(data) && data.length === 0)) {
      return { heatmapData: [], models: [], tactics: [] };
    }
    
    const models = new Set();
    const tactics = new Set();
    const resultMap = new Map();
    
    // Process data based on format
    if (Array.isArray(data) && data[0] && data[0].name) {
      // Process model objects
      for (const model of data) {
        models.add(model.name);
        
        // Process single-turn tactics
        const singleTurnTactics = model.tactics?.single || [];
        for (const tactic of singleTurnTactics) {
          tactics.add(tactic.name);
          
          const key = `${model.name}|${tactic.name}`;
          resultMap.set(key, {
            model: model.name,
            tactic: tactic.name,
            successRate: tactic.successRate,
            refusalRate: tactic.refusalRate,
            roundCount: tactic.roundCount
          });
        }
        
        // Process multi-turn tactics
        const multiTurnTactics = model.tactics?.multi || [];
        for (const tactic of multiTurnTactics) {
          tactics.add(tactic.name);
          
          const key = `${model.name}|${tactic.name}`;
          resultMap.set(key, {
            model: model.name,
            tactic: tactic.name,
            successRate: tactic.successRate,
            refusalRate: tactic.refusalRate,
            roundCount: tactic.roundCount
          });
        }
      }
    } else {
      // Process raw data rows
      for (const row of data) {
        const modelName = row.target_model || row.model || 'unknown';
        const tacticName = row.jailbreak || 'unknown';
        
        models.add(modelName);
        tactics.add(tacticName);
        
        const key = `${modelName}|${tacticName}`;
        if (!resultMap.has(key)) {
          resultMap.set(key, {
            model: modelName,
            tactic: tacticName,
            successCount: 0,
            refusalCount: 0,
            totalCount: 0,
            roundSum: 0
          });
        }
        
        const result = resultMap.get(key);
        result.totalCount++;
        
        // Track success/refusal/rounds
        const isSuccess = row.success !== undefined ? Boolean(row.success) : 
                         row.jailbreak_success !== undefined ? Boolean(row.jailbreak_success) :
                         row.asr !== undefined ? row.asr > 0 : false;
        
        const isRefusal = row.refused !== undefined ? Boolean(row.refused) : 
                         row.refusal !== undefined ? Boolean(row.refusal) :
                         row.rejection !== undefined ? Boolean(row.rejection) : false;
        
        if (isSuccess) result.successCount++;
        if (isRefusal) result.refusalCount++;
        
        const rounds = row.num_turns || row.rounds || row.turn_count || 0;
        result.roundSum += rounds;
      }
      
      // Calculate rates
      for (const [key, result] of resultMap.entries()) {
        if (result.totalCount > 0) {
          result.successRate = (result.successCount / result.totalCount) * 100;
          result.refusalRate = (result.refusalCount / result.totalCount) * 100;
          result.roundCount = result.roundSum / result.totalCount;
        }
      }
    }
    
    // Convert to array format for heatmap
    const heatmapData = Array.from(resultMap.values()).map(result => ({
      x: result.model,
      y: result.tactic,
      value: metric === 'success' ? result.successRate : 
             metric === 'refusal' ? result.refusalRate : 
             result.roundCount
    }));
    
    return {
      heatmapData,
      models: Array.from(models),
      tactics: Array.from(tactics)
    };
  }, [data, metric]);
  
  // Process data for model vs test case heatmap
  const modelTestCaseData = useMemo(() => {
    if (!data || (Array.isArray(data) && data.length === 0)) {
      return { heatmapData: [], models: [], testCases: [] };
    }
    
    const models = new Set();
    const testCases = new Set();
    const resultMap = new Map();
    
    // Process data based on format
    if (Array.isArray(data) && data[0] && data[0].name) {
      // Process model objects
      for (const model of data) {
        models.add(model.name);
        
        // Process test cases
        for (const testCase of model.testCases || []) {
          testCases.add(testCase.name);
          
          const key = `${model.name}|${testCase.name}`;
          resultMap.set(key, {
            model: model.name,
            testCase: testCase.name,
            successRate: testCase.successRate,
            refusalRate: testCase.refusalRate,
            roundCount: testCase.roundCount
          });
        }
      }
    } else {
      // Process raw data rows
      for (const row of data) {
        const modelName = row.target_model || row.model || 'unknown';
        const testCaseName = row.test_case || 'unknown';
        
        models.add(modelName);
        testCases.add(testCaseName);
        
        const key = `${modelName}|${testCaseName}`;
        if (!resultMap.has(key)) {
          resultMap.set(key, {
            model: modelName,
            testCase: testCaseName,
            successCount: 0,
            refusalCount: 0,
            totalCount: 0,
            roundSum: 0
          });
        }
        
        const result = resultMap.get(key);
        result.totalCount++;
        
        // Track success/refusal/rounds
        const isSuccess = row.success !== undefined ? Boolean(row.success) : 
                         row.jailbreak_success !== undefined ? Boolean(row.jailbreak_success) :
                         row.asr !== undefined ? row.asr > 0 : false;
        
        const isRefusal = row.refused !== undefined ? Boolean(row.refused) : 
                         row.refusal !== undefined ? Boolean(row.refusal) :
                         row.rejection !== undefined ? Boolean(row.rejection) : false;
        
        if (isSuccess) result.successCount++;
        if (isRefusal) result.refusalCount++;
        
        const rounds = row.num_turns || row.rounds || row.turn_count || 0;
        result.roundSum += rounds;
      }
      
      // Calculate rates
      for (const [key, result] of resultMap.entries()) {
        if (result.totalCount > 0) {
          result.successRate = (result.successCount / result.totalCount) * 100;
          result.refusalRate = (result.refusalCount / result.totalCount) * 100;
          result.roundCount = result.roundSum / result.totalCount;
        }
      }
    }
    
    // Convert to array format for heatmap
    const heatmapData = Array.from(resultMap.values()).map(result => ({
      x: result.model,
      y: result.testCase,
      value: metric === 'success' ? result.successRate : 
             metric === 'refusal' ? result.refusalRate : 
             result.roundCount
    }));
    
    return {
      heatmapData,
      models: Array.from(models),
      testCases: Array.from(testCases)
    };
  }, [data, metric]);
  
  // Render comparison type selector
  const renderComparisonTypeSelector = () => (
    <div className="mb-4">
      <label className="block text-sm font-medium mb-1">Comparison Type:</label>
      <div className="flex space-x-4">
        <label className="inline-flex items-center">
          <input 
            type="radio" 
            value="tactic" 
            checked={comparisonType === "tactic"} 
            onChange={() => setComparisonType("tactic")}
            className="mr-1"
          />
          Model vs. Tactic
        </label>
        <label className="inline-flex items-center">
          <input 
            type="radio" 
            value="testcase" 
            checked={comparisonType === "testcase"} 
            onChange={() => setComparisonType("testcase")}
            className="mr-1"
          />
          Model vs. Test Case
        </label>
      </div>
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
  
  // Render model vs tactic heatmap
  const renderModelTacticHeatmap = () => {
    if (!modelTacticData.heatmapData || modelTacticData.heatmapData.length === 0) {
      return <div>No data available for model vs. tactic comparison</div>;
    }
    
    return (
      <div className="chart-container">
        <h3 className="text-lg font-medium mb-2">
          {metric === 'success' ? 'Success Rate' : 
           metric === 'refusal' ? 'Refusal Rate' : 'Average Rounds'} by Model and Tactic
        </h3>
        
        <div className="bg-white p-4 border rounded" style={{ height: '600px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <div className="w-full h-full">
              <CustomHeatmap
                data={modelTacticData.heatmapData}
                xLabels={modelTacticData.models}
                yLabels={modelTacticData.tactics}
                colorScale={getColorScale}
              />
            </div>
          </ResponsiveContainer>
        </div>
      </div>
    );
  };
  
  // Render model vs test case heatmap
  const renderModelTestCaseHeatmap = () => {
    if (!modelTestCaseData.heatmapData || modelTestCaseData.heatmapData.length === 0) {
      return <div>No data available for model vs. test case comparison</div>;
    }
    
    return (
      <div className="chart-container">
        <h3 className="text-lg font-medium mb-2">
          {metric === 'success' ? 'Success Rate' : 
           metric === 'refusal' ? 'Refusal Rate' : 'Average Rounds'} by Model and Test Case
        </h3>
        
        <div className="bg-white p-4 border rounded" style={{ height: '600px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <div className="w-full h-full">
              <CustomHeatmap
                data={modelTestCaseData.heatmapData}
                xLabels={modelTestCaseData.models}
                yLabels={modelTestCaseData.testCases}
                colorScale={getColorScale}
              />
            </div>
          </ResponsiveContainer>
        </div>
      </div>
    );
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">Model Comparison Heatmap</h2>
        <p className="text-gray-600">
          Compare model performance across different test cases and tactics using heatmaps.
        </p>
      </div>
      
      <div className="flex flex-wrap -mx-2">
        <div className="w-full md:w-1/4 px-2">
          {renderComparisonTypeSelector()}
          {renderMetricSelector()}
        </div>
        
        <div className="w-full md:w-3/4 px-2">
          {comparisonType === "tactic" ? renderModelTacticHeatmap() : renderModelTestCaseHeatmap()}
        </div>
      </div>
    </div>
  );
};

export default ModelComparisonHeatmap; 