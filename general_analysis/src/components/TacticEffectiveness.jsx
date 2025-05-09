import React, { useState, useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, LabelList, LineChart, Line
} from 'recharts';

// Color constants
const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE', 
  '#00C49F', '#FFBB28', '#FF8042', '#a4de6c', '#d0ed57'
];

const TacticEffectiveness = ({ data, selectedTactic, onTacticSelect, uniqueTactics }) => {
  const [metric, setMetric] = useState("success");
  const [turnType, setTurnType] = useState("all"); // "single", "multi", or "all"
  
  // Process data for visualization
  const processedData = useMemo(() => {
    if (!data || (Array.isArray(data) && data.length === 0)) {
      return { tacticData: [], modelData: [] };
    }
    
    // Group by tactic
    const tacticGroups = {};
    
    // Process data based on format
    if (Array.isArray(data) && data[0] && data[0].name) {
      // Already processed models array
      for (const model of data) {
        const singleTurnTactics = model.tactics?.single || [];
        const multiTurnTactics = model.tactics?.multi || [];
        
        // Process single-turn tactics
        for (const tactic of singleTurnTactics) {
          if (!tacticGroups[tactic.name]) {
            tacticGroups[tactic.name] = {
              models: {},
              turnType: 'single',
              totalRows: 0,
              successCount: 0,
              refusalCount: 0,
              roundSum: 0
            };
          }
          
          tacticGroups[tactic.name].models[model.name] = {
            successRate: tactic.successRate,
            refusalRate: tactic.refusalRate,
            roundCount: tactic.roundCount,
            rows: tactic.rows
          };
          
          tacticGroups[tactic.name].totalRows += tactic.rows?.length || 0;
          tacticGroups[tactic.name].successCount += ((tactic.successRate / 100) * (tactic.rows?.length || 0));
          tacticGroups[tactic.name].refusalCount += ((tactic.refusalRate / 100) * (tactic.rows?.length || 0));
          tacticGroups[tactic.name].roundSum += (tactic.roundCount * (tactic.rows?.length || 0));
        }
        
        // Process multi-turn tactics
        for (const tactic of multiTurnTactics) {
          if (!tacticGroups[tactic.name]) {
            tacticGroups[tactic.name] = {
              models: {},
              turnType: 'multi',
              totalRows: 0,
              successCount: 0,
              refusalCount: 0,
              roundSum: 0
            };
          } else if (tacticGroups[tactic.name].turnType === 'single') {
            tacticGroups[tactic.name].turnType = 'both';
          }
          
          tacticGroups[tactic.name].models[model.name] = {
            successRate: tactic.successRate,
            refusalRate: tactic.refusalRate,
            roundCount: tactic.roundCount,
            rows: tactic.rows
          };
          
          tacticGroups[tactic.name].totalRows += tactic.rows?.length || 0;
          tacticGroups[tactic.name].successCount += ((tactic.successRate / 100) * (tactic.rows?.length || 0));
          tacticGroups[tactic.name].refusalCount += ((tactic.refusalRate / 100) * (tactic.rows?.length || 0));
          tacticGroups[tactic.name].roundSum += (tactic.roundCount * (tactic.rows?.length || 0));
        }
      }
    } else {
      // Raw data rows
      for (const row of data) {
        const tacticName = row.jailbreak || 'unknown';
        const modelName = row.target_model || row.model || 'unknown';
        const isSingleTurn = row.num_turns === 1 || !row.num_turns;
        
        if (!tacticGroups[tacticName]) {
          tacticGroups[tacticName] = {
            models: {},
            turnType: isSingleTurn ? 'single' : 'multi',
            totalRows: 0,
            successCount: 0,
            refusalCount: 0,
            roundSum: 0
          };
        } else if (
          (isSingleTurn && tacticGroups[tacticName].turnType === 'multi') ||
          (!isSingleTurn && tacticGroups[tacticName].turnType === 'single')
        ) {
          tacticGroups[tacticName].turnType = 'both';
        }
        
        if (!tacticGroups[tacticName].models[modelName]) {
          tacticGroups[tacticName].models[modelName] = {
            rows: []
          };
        }
        
        tacticGroups[tacticName].models[modelName].rows.push(row);
        tacticGroups[tacticName].totalRows += 1;
        
        // Track success/refusal/rounds
        const isSuccess = row.success !== undefined ? Boolean(row.success) : 
                         row.jailbreak_success !== undefined ? Boolean(row.jailbreak_success) :
                         row.asr !== undefined ? row.asr > 0 : false;
        
        const isRefusal = row.refused !== undefined ? Boolean(row.refused) : 
                         row.refusal !== undefined ? Boolean(row.refusal) :
                         row.rejection !== undefined ? Boolean(row.rejection) : false;
        
        if (isSuccess) tacticGroups[tacticName].successCount += 1;
        if (isRefusal) tacticGroups[tacticName].refusalCount += 1;
        
        const rounds = row.num_turns || row.rounds || row.turn_count || 0;
        tacticGroups[tacticName].roundSum += rounds;
      }
      
      // Calculate metrics for each model within each tactic
      for (const tacticName in tacticGroups) {
        for (const modelName in tacticGroups[tacticName].models) {
          const rows = tacticGroups[tacticName].models[modelName].rows;
          
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
          
          const roundCount = roundsData.length > 0 
            ? roundsData.reduce((sum, val) => sum + val, 0) / roundsData.length 
            : 0;
          
          tacticGroups[tacticName].models[modelName].successRate = successRate;
          tacticGroups[tacticName].models[modelName].refusalRate = refusalRate;
          tacticGroups[tacticName].models[modelName].roundCount = roundCount;
        }
      }
    }
    
    // Format the data for each tactic
    const tacticData = Object.entries(tacticGroups).map(([tacticName, data]) => {
      // Calculate overall metrics
      const avgSuccessRate = data.totalRows > 0 ? (data.successCount / data.totalRows) * 100 : 0;
      const avgRefusalRate = data.totalRows > 0 ? (data.refusalCount / data.totalRows) * 100 : 0;
      const avgRounds = data.totalRows > 0 ? data.roundSum / data.totalRows : 0;
      
      // Format model data for this tactic
      const modelData = Object.entries(data.models).map(([modelName, metrics]) => ({
        modelName,
        successRate: metrics.successRate,
        refusalRate: metrics.refusalRate,
        roundCount: metrics.roundCount,
        count: metrics.rows?.length || 0
      }));
      
      // Sort models by success rate
      const sortedModels = [...modelData].sort((a, b) => b.successRate - a.successRate);
      
      return {
        name: tacticName,
        turnType: data.turnType,
        avgSuccessRate,
        avgRefusalRate,
        avgRounds,
        totalSamples: data.totalRows,
        models: sortedModels,
        modelCount: modelData.length
      };
    });
    
    return {
      tacticData,
      modelData: [] // We'll populate this later if needed
    };
  }, [data]);
  
  // Filter tactics by turn type
  const filteredTactics = useMemo(() => {
    if (!processedData.tacticData) return [];
    
    return processedData.tacticData.filter(tactic => {
      if (turnType === 'all') return true;
      if (turnType === 'single') return tactic.turnType === 'single' || tactic.turnType === 'both';
      if (turnType === 'multi') return tactic.turnType === 'multi' || tactic.turnType === 'both';
      return true;
    });
  }, [processedData.tacticData, turnType]);
  
  // Sort tactics by the selected metric
  const sortedTactics = useMemo(() => {
    if (!filteredTactics || filteredTactics.length === 0) return [];
    
    const metricMap = {
      'success': 'avgSuccessRate',
      'refusal': 'avgRefusalRate',
      'rounds': 'avgRounds'
    };
    
    const field = metricMap[metric] || 'avgSuccessRate';
    
    return [...filteredTactics].sort((a, b) => {
      // Primary sort by the metric
      if (b[field] !== a[field]) {
        return b[field] - a[field];
      }
      // Secondary sort by name
      return a.name.localeCompare(b.name);
    });
  }, [filteredTactics, metric]);
  
  // Get data for selected tactic
  const selectedTacticData = useMemo(() => {
    if (!selectedTactic || !processedData.tacticData || processedData.tacticData.length === 0) {
      return null;
    }
    
    return processedData.tacticData.find(t => t.name === selectedTactic) || null;
  }, [selectedTactic, processedData]);
  
  // Render tactic selector
  const renderTacticSelector = () => (
    <div className="mb-4">
      <label className="block text-sm font-medium mb-1">Select Tactic:</label>
      <select 
        className="w-full p-2 border rounded"
        value={selectedTactic || ''}
        onChange={(e) => onTacticSelect(e.target.value)}
      >
        {(uniqueTactics || []).map(tactic => (
          <option key={tactic} value={tactic}>{tactic}</option>
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
  
  // Render turn type selector
  const renderTurnTypeSelector = () => (
    <div className="mb-4">
      <label className="block text-sm font-medium mb-1">Turn Type:</label>
      <div className="flex space-x-4">
        <label className="inline-flex items-center">
          <input 
            type="radio" 
            value="all" 
            checked={turnType === "all"} 
            onChange={() => setTurnType("all")}
            className="mr-1"
          />
          All Tactics
        </label>
        <label className="inline-flex items-center">
          <input 
            type="radio" 
            value="single" 
            checked={turnType === "single"} 
            onChange={() => setTurnType("single")}
            className="mr-1"
          />
          Single-Turn
        </label>
        <label className="inline-flex items-center">
          <input 
            type="radio" 
            value="multi" 
            checked={turnType === "multi"} 
            onChange={() => setTurnType("multi")}
            className="mr-1"
          />
          Multi-Turn
        </label>
      </div>
    </div>
  );
  
  // Render tactic comparison chart
  const renderTacticComparison = () => {
    if (!sortedTactics || sortedTactics.length === 0) {
      return <div>No tactic data available</div>;
    }
    
    // Get data key based on selected metric
    const dataKey = metric === 'success' ? 'avgSuccessRate' : 
                  metric === 'refusal' ? 'avgRefusalRate' : 'avgRounds';
    
    return (
      <div className="chart-container">
        <h3 className="text-lg font-medium mb-2">
          {metric === 'success' ? 'Success Rate' : 
           metric === 'refusal' ? 'Refusal Rate' : 'Average Rounds'} by Tactic
        </h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart
            data={sortedTactics}
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
              dataKey={dataKey} 
              fill="#8884d8"
              name={metric === 'success' ? 'Success Rate' : 
                    metric === 'refusal' ? 'Refusal Rate' : 'Average Rounds'}
            >
              {sortedTactics.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
              <LabelList dataKey={dataKey} position="top" formatter={(value) => `${value.toFixed(1)}${metric !== 'rounds' ? '%' : ''}`} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };
  
  // Render model performance for selected tactic
  const renderModelPerformance = () => {
    if (!selectedTacticData || !selectedTacticData.models || selectedTacticData.models.length === 0) {
      return <div>Select a tactic to view model performance</div>;
    }
    
    // Get data key based on selected metric
    const dataKey = metric === 'success' ? 'successRate' : 
                    metric === 'refusal' ? 'refusalRate' : 'roundCount';
    
    // Sort models by the selected metric
    const sortedModels = [...selectedTacticData.models].sort((a, b) => b[dataKey] - a[dataKey]);
    
    // Limit to top 15 models for readability
    const displayModels = sortedModels.slice(0, 15);
    
    return (
      <div className="chart-container">
        <h3 className="text-lg font-medium mb-2">
          Model Performance with {selectedTacticData.name} Tactic
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
              dataKey={dataKey} 
              fill="#82ca9d"
              name={metric === 'success' ? 'Success Rate' : 
                    metric === 'refusal' ? 'Refusal Rate' : 'Average Rounds'}
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
  
  // Render details for selected tactic
  const renderTacticDetails = () => {
    if (!selectedTacticData) {
      return <div>Select a tactic to view details</div>;
    }
    
    return (
      <div className="mt-8 p-4 border rounded">
        <h3 className="text-xl font-medium mb-2">{selectedTacticData.name}</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-3 rounded">
            <p className="text-sm text-gray-600">Average Success Rate</p>
            <p className="text-2xl font-bold">{selectedTacticData.avgSuccessRate.toFixed(2)}%</p>
          </div>
          <div className="bg-red-50 p-3 rounded">
            <p className="text-sm text-gray-600">Average Refusal Rate</p>
            <p className="text-2xl font-bold">{selectedTacticData.avgRefusalRate.toFixed(2)}%</p>
          </div>
          <div className="bg-green-50 p-3 rounded">
            <p className="text-sm text-gray-600">Average Rounds</p>
            <p className="text-2xl font-bold">{selectedTacticData.avgRounds.toFixed(2)}</p>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm">
              Models tested: <span className="font-medium">{selectedTacticData.modelCount}</span>
            </p>
          </div>
          <div>
            <p className="text-sm">
              Total samples: <span className="font-medium">{selectedTacticData.totalSamples}</span>
            </p>
          </div>
          <div>
            <p className="text-sm">
              Turn type: <span className="font-medium">
                {selectedTacticData.turnType === 'single' ? 'Single-turn' : 
                 selectedTacticData.turnType === 'multi' ? 'Multi-turn' : 'Both'}
              </span>
            </p>
          </div>
        </div>
      </div>
    );
  };
  
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">Tactic Effectiveness Analysis</h2>
        <p className="text-gray-600">
          Compare effectiveness of different jailbreak tactics across models, 
          analyzing single-turn and multi-turn strategies.
        </p>
      </div>
      
      <div className="flex flex-wrap -mx-2">
        <div className="w-full md:w-1/4 px-2">
          {renderTacticSelector()}
          {renderMetricSelector()}
          {renderTurnTypeSelector()}
        </div>
        
        <div className="w-full md:w-3/4 px-2">
          {renderTacticComparison()}
          {renderTacticDetails()}
          {renderModelPerformance()}
        </div>
      </div>
    </div>
  );
};

export default TacticEffectiveness; 