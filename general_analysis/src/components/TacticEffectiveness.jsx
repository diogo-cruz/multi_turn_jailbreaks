import React, { useState, useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, LabelList, LineChart, Line
} from 'recharts';
import { calculateTurnTypeMetrics } from '../utils/dataProcessing';

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
        // Check if we have separate single/multi tactics or need to filter by turn count
        const hasSeparateTactics = model.tactics && (model.tactics.single || model.tactics.multi);
        
        if (hasSeparateTactics) {
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
                roundSum: 0,
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
            
            if (!tacticGroups[tactic.name].models[model.name]) {
              tacticGroups[tactic.name].models[model.name] = {
                successRate: tactic.successRate,
                refusalRate: tactic.refusalRate,
                roundCount: tactic.roundCount,
                rows: tactic.rows || [],
                singleTurnRows: [],
                multiTurnRows: []
              };
            }
            
            // Add rows to appropriate collections
            if (tactic.rows) {
              const rows = tactic.rows;
              tacticGroups[tactic.name].totalRows += rows.length;
              tacticGroups[tactic.name].singleTurnCount += rows.length;
              tacticGroups[tactic.name].singleTurnRows.push(...rows);
              tacticGroups[tactic.name].models[model.name].singleTurnRows.push(...rows);
              
              // Count successes and refusals
              const successfulRows = rows.filter(row => 
                row.success !== undefined ? Boolean(row.success) : 
                row.jailbreak_success !== undefined ? Boolean(row.jailbreak_success) :
                row.asr !== undefined ? row.asr > 0 : false
              );
              
              const refusalRows = rows.filter(row => 
                row.refused !== undefined ? Boolean(row.refused) : 
                row.refusal !== undefined ? Boolean(row.refusal) :
                row.rejection !== undefined ? Boolean(row.rejection) : false
              );
              
              tacticGroups[tactic.name].successCount += successfulRows.length;
              tacticGroups[tactic.name].refusalCount += refusalRows.length;
              tacticGroups[tactic.name].singleTurnSuccessCount += successfulRows.length;
              tacticGroups[tactic.name].singleTurnRefusalCount += refusalRows.length;
              
              // Sum rounds
              const roundSum = rows.reduce((sum, row) => 
                sum + (row.num_turns || row.rounds || row.turn_count || 1), 0);
              tacticGroups[tactic.name].roundSum += roundSum;
            }
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
                roundSum: 0,
                singleTurnRows: [],
                multiTurnRows: [],
                singleTurnSuccessCount: 0,
                singleTurnRefusalCount: 0,
                singleTurnCount: 0,
                multiTurnSuccessCount: 0,
                multiTurnRefusalCount: 0,
                multiTurnCount: 0
              };
            } else if (tacticGroups[tactic.name].turnType === 'single') {
              tacticGroups[tactic.name].turnType = 'both';
            }
            
            if (!tacticGroups[tactic.name].models[model.name]) {
              tacticGroups[tactic.name].models[model.name] = {
                successRate: tactic.successRate,
                refusalRate: tactic.refusalRate,
                roundCount: tactic.roundCount,
                rows: tactic.rows || [],
                singleTurnRows: [],
                multiTurnRows: []
              };
            }
            
            // Add rows to appropriate collections
            if (tactic.rows) {
              const rows = tactic.rows;
              tacticGroups[tactic.name].totalRows += rows.length;
              tacticGroups[tactic.name].multiTurnCount += rows.length;
              tacticGroups[tactic.name].multiTurnRows.push(...rows);
              tacticGroups[tactic.name].models[model.name].multiTurnRows.push(...rows);
              
              // Count successes and refusals
              const successfulRows = rows.filter(row => 
                row.success !== undefined ? Boolean(row.success) : 
                row.jailbreak_success !== undefined ? Boolean(row.jailbreak_success) :
                row.asr !== undefined ? row.asr > 0 : false
              );
              
              const refusalRows = rows.filter(row => 
                row.refused !== undefined ? Boolean(row.refused) : 
                row.refusal !== undefined ? Boolean(row.refusal) :
                row.rejection !== undefined ? Boolean(row.rejection) : false
              );
              
              tacticGroups[tactic.name].successCount += successfulRows.length;
              tacticGroups[tactic.name].refusalCount += refusalRows.length;
              tacticGroups[tactic.name].multiTurnSuccessCount += successfulRows.length;
              tacticGroups[tactic.name].multiTurnRefusalCount += refusalRows.length;
              
              // Sum rounds
              const roundSum = rows.reduce((sum, row) => 
                sum + (row.num_turns || row.rounds || row.turn_count || 1), 0);
              tacticGroups[tactic.name].roundSum += roundSum;
            }
          }
        } else if (model.tactics) {
          // Handle case where tactics are not split into single/multi
          for (const tactic of model.tactics) {
            if (!tacticGroups[tactic.name]) {
              tacticGroups[tactic.name] = {
                models: {},
                turnType: 'both',
                totalRows: 0,
                successCount: 0,
                refusalCount: 0,
                roundSum: 0,
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
            
            if (!tacticGroups[tactic.name].models[model.name]) {
              tacticGroups[tactic.name].models[model.name] = {
                successRate: tactic.successRate,
                refusalRate: tactic.refusalRate,
                roundCount: tactic.roundCount,
                rows: tactic.rows || [],
                singleTurnRows: [],
                multiTurnRows: []
              };
            }
            
            // Filter and categorize rows by turn count
            if (tactic.rows) {
              const rows = tactic.rows;
              const singleTurnRows = rows.filter(row => row.num_turns === 1 || !row.num_turns);
              const multiTurnRows = rows.filter(row => row.num_turns && row.num_turns > 1);
              
              // Add to overall counters
              tacticGroups[tactic.name].totalRows += rows.length;
              tacticGroups[tactic.name].singleTurnCount += singleTurnRows.length;
              tacticGroups[tactic.name].multiTurnCount += multiTurnRows.length;
              
              // Add rows to appropriate collections
              tacticGroups[tactic.name].singleTurnRows.push(...singleTurnRows);
              tacticGroups[tactic.name].multiTurnRows.push(...multiTurnRows);
              tacticGroups[tactic.name].models[model.name].singleTurnRows.push(...singleTurnRows);
              tacticGroups[tactic.name].models[model.name].multiTurnRows.push(...multiTurnRows);
              
              // Count single-turn successes and refusals
              const singleTurnSuccessful = singleTurnRows.filter(row => 
                row.success !== undefined ? Boolean(row.success) : 
                row.jailbreak_success !== undefined ? Boolean(row.jailbreak_success) :
                row.asr !== undefined ? row.asr > 0 : false
              );
              
              const singleTurnRefusal = singleTurnRows.filter(row => 
                row.refused !== undefined ? Boolean(row.refused) : 
                row.refusal !== undefined ? Boolean(row.refusal) :
                row.rejection !== undefined ? Boolean(row.rejection) : false
              );
              
              tacticGroups[tactic.name].singleTurnSuccessCount += singleTurnSuccessful.length;
              tacticGroups[tactic.name].singleTurnRefusalCount += singleTurnRefusal.length;
              
              // Count multi-turn successes and refusals
              const multiTurnSuccessful = multiTurnRows.filter(row => 
                row.success !== undefined ? Boolean(row.success) : 
                row.jailbreak_success !== undefined ? Boolean(row.jailbreak_success) :
                row.asr !== undefined ? row.asr > 0 : false
              );
              
              const multiTurnRefusal = multiTurnRows.filter(row => 
                row.refused !== undefined ? Boolean(row.refused) : 
                row.refusal !== undefined ? Boolean(row.refusal) :
                row.rejection !== undefined ? Boolean(row.rejection) : false
              );
              
              tacticGroups[tactic.name].multiTurnSuccessCount += multiTurnSuccessful.length;
              tacticGroups[tactic.name].multiTurnRefusalCount += multiTurnRefusal.length;
              
              // Count overall successes and refusals
              const successfulRows = rows.filter(row => 
                row.success !== undefined ? Boolean(row.success) : 
                row.jailbreak_success !== undefined ? Boolean(row.jailbreak_success) :
                row.asr !== undefined ? row.asr > 0 : false
              );
              
              const refusalRows = rows.filter(row => 
                row.refused !== undefined ? Boolean(row.refused) : 
                row.refusal !== undefined ? Boolean(row.refusal) :
                row.rejection !== undefined ? Boolean(row.rejection) : false
              );
              
              tacticGroups[tactic.name].successCount += successfulRows.length;
              tacticGroups[tactic.name].refusalCount += refusalRows.length;
              
              // Sum rounds
              const roundSum = rows.reduce((sum, row) => 
                sum + (row.num_turns || row.rounds || row.turn_count || 1), 0);
              tacticGroups[tactic.name].roundSum += roundSum;
            }
          }
        }
      }
      
      // Compute per-model metrics for each tactic
      for (const tacticName in tacticGroups) {
        const tactic = tacticGroups[tacticName];
        
        for (const modelName in tactic.models) {
          const model = tactic.models[modelName];
          
          // Calculate single-turn rates
          const singleTurnRows = model.singleTurnRows;
          if (singleTurnRows.length > 0) {
            const singleTurnSuccessful = singleTurnRows.filter(row => 
              row.success !== undefined ? Boolean(row.success) : 
              row.jailbreak_success !== undefined ? Boolean(row.jailbreak_success) :
              row.asr !== undefined ? row.asr > 0 : false
            );
            
            const singleTurnRefusal = singleTurnRows.filter(row => 
              row.refused !== undefined ? Boolean(row.refused) : 
              row.refusal !== undefined ? Boolean(row.refusal) :
              row.rejection !== undefined ? Boolean(row.rejection) : false
            );
            
            model.singleTurnSuccessRate = (singleTurnSuccessful.length / singleTurnRows.length) * 100;
            model.singleTurnRefusalRate = (singleTurnRefusal.length / singleTurnRows.length) * 100;
            model.singleTurnCount = singleTurnRows.length;
          } else {
            model.singleTurnSuccessRate = 0;
            model.singleTurnRefusalRate = 0;
            model.singleTurnCount = 0;
          }
          
          // Calculate multi-turn rates
          const multiTurnRows = model.multiTurnRows;
          if (multiTurnRows.length > 0) {
            const multiTurnSuccessful = multiTurnRows.filter(row => 
              row.success !== undefined ? Boolean(row.success) : 
              row.jailbreak_success !== undefined ? Boolean(row.jailbreak_success) :
              row.asr !== undefined ? row.asr > 0 : false
            );
            
            const multiTurnRefusal = multiTurnRows.filter(row => 
              row.refused !== undefined ? Boolean(row.refused) : 
              row.refusal !== undefined ? Boolean(row.refusal) :
              row.rejection !== undefined ? Boolean(row.rejection) : false
            );
            
            model.multiTurnSuccessRate = (multiTurnSuccessful.length / multiTurnRows.length) * 100;
            model.multiTurnRefusalRate = (multiTurnRefusal.length / multiTurnRows.length) * 100;
            model.multiTurnCount = multiTurnRows.length;
          } else {
            model.multiTurnSuccessRate = 0;
            model.multiTurnRefusalRate = 0;
            model.multiTurnCount = 0;
          }
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
            roundSum: 0,
            singleTurnRows: [],
            multiTurnRows: []
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
        
        // Add to appropriate turn type collection
        if (isSingleTurn) {
          tacticGroups[tacticName].singleTurnRows.push(row);
        } else {
          tacticGroups[tacticName].multiTurnRows.push(row);
        }
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
      
      // Calculate single-turn metrics
      const singleTurnSuccessRate = data.singleTurnCount > 0
        ? (data.singleTurnSuccessCount / data.singleTurnCount) * 100
        : 0;
        
      const singleTurnRefusalRate = data.singleTurnCount > 0
        ? (data.singleTurnRefusalCount / data.singleTurnCount) * 100
        : 0;
      
      // Calculate multi-turn metrics
      const multiTurnSuccessRate = data.multiTurnCount > 0
        ? (data.multiTurnSuccessCount / data.multiTurnCount) * 100
        : 0;
        
      const multiTurnRefusalRate = data.multiTurnCount > 0
        ? (data.multiTurnRefusalCount / data.multiTurnCount) * 100
        : 0;
      
      // Format model data for this tactic
      const modelData = Object.entries(data.models).map(([modelName, metrics]) => ({
        modelName,
        successRate: metrics.successRate,
        refusalRate: metrics.refusalRate,
        roundCount: metrics.roundCount,
        count: metrics.rows?.length || 0,
        singleTurnCount: metrics.singleTurnCount || 0,
        multiTurnCount: metrics.multiTurnCount || 0,
        singleTurnSuccessRate: metrics.singleTurnSuccessRate || 0,
        singleTurnRefusalRate: metrics.singleTurnRefusalRate || 0,
        multiTurnSuccessRate: metrics.multiTurnSuccessRate || 0,
        multiTurnRefusalRate: metrics.multiTurnRefusalRate || 0
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
        modelCount: modelData.length,
        singleTurnCount: data.singleTurnCount,
        multiTurnCount: data.multiTurnCount,
        singleTurnSuccessRate,
        singleTurnRefusalRate,
        multiTurnSuccessRate,
        multiTurnRefusalRate
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
      if (turnType === 'single') return tactic.singleTurnCount > 0;
      if (turnType === 'multi') return tactic.multiTurnCount > 0;
      return true;
    });
  }, [processedData.tacticData, turnType]);
  
  // Sort tactics by the selected metric
  const sortedTactics = useMemo(() => {
    if (!filteredTactics || filteredTactics.length === 0) return [];
    
    const metricMap = {
      'success': (tactic) => {
        if (turnType === 'single') return tactic.singleTurnSuccessRate; 
        if (turnType === 'multi') return tactic.multiTurnSuccessRate;
        return tactic.avgSuccessRate;
      },
      'refusal': (tactic) => {
        if (turnType === 'single') return tactic.singleTurnRefusalRate;
        if (turnType === 'multi') return tactic.multiTurnRefusalRate;
        return tactic.avgRefusalRate;
      },
      'rounds': 'avgRounds'
    };
    
    const getMetricValue = metricMap[metric];
    
    return [...filteredTactics].sort((a, b) => {
      // Primary sort by the metric
      const aValue = typeof getMetricValue === 'function' ? getMetricValue(a) : a[getMetricValue];
      const bValue = typeof getMetricValue === 'function' ? getMetricValue(b) : b[getMetricValue];
      
      if (bValue !== aValue) {
        return bValue - aValue;
      }
      // Secondary sort by name
      return a.name.localeCompare(b.name);
    });
  }, [filteredTactics, metric, turnType]);
  
  // Get data for selected tactic
  const selectedTacticData = useMemo(() => {
    if (!selectedTactic || !processedData.tacticData || processedData.tacticData.length === 0) {
      return null;
    }
    
    const tacticData = processedData.tacticData.find(t => t.name === selectedTactic) || null;
    
    // Add debugging log
    if (tacticData) {
      console.log("Selected Tactic Data:", tacticData);
      console.log("Tactic Turn Type:", turnType);
      
      // Log specific turn type metrics
      console.log("Single Turn Success Rate:", tacticData.singleTurnSuccessRate);
      console.log("Multi Turn Success Rate:", tacticData.multiTurnSuccessRate);
      console.log("Single Turn Count:", tacticData.singleTurnCount);
      console.log("Multi Turn Count:", tacticData.multiTurnCount);
      
      // Log model-specific data
      if (tacticData.models && tacticData.models.length > 0) {
        tacticData.models.forEach(model => {
          console.log(`Model ${model.modelName}:`, {
            successRate: model.successRate,
            singleTurnSuccessRate: model.singleTurnSuccessRate, 
            multiTurnSuccessRate: model.multiTurnSuccessRate,
            singleTurnCount: model.singleTurnCount,
            multiTurnCount: model.multiTurnCount
          });
        });
      }
    }
    
    return tacticData;
  }, [selectedTactic, processedData]);
  
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
          Avg. Rounds
        </label>
      </div>
    </div>
  );
  
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
          All
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
  
  const renderTacticComparison = () => {
    if (!sortedTactics || sortedTactics.length === 0) {
      return <p>No tactic data available for the selected turn type.</p>;
    }
    
    // Prepare single-turn data
    const singleTurnTactics = sortedTactics.filter(tactic => tactic.singleTurnCount > 0);
    const singleTurnChartData = singleTurnTactics.map(tactic => ({
      name: tactic.name,
      successRate: tactic.singleTurnSuccessRate,
      refusalRate: tactic.singleTurnRefusalRate,
      count: tactic.singleTurnCount
    }));
    
    // Prepare multi-turn data
    const multiTurnTactics = sortedTactics.filter(tactic => tactic.multiTurnCount > 0);
    const multiTurnChartData = multiTurnTactics.map(tactic => ({
      name: tactic.name,
      successRate: tactic.multiTurnSuccessRate,
      refusalRate: tactic.multiTurnRefusalRate,
      count: tactic.multiTurnCount
    }));
    
    return (
      <div>
        {(turnType === 'all' || turnType === 'single') && singleTurnChartData.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-semibold mb-2">Single-Turn Tactic Effectiveness</h2>
            <p className="text-sm text-gray-500 mb-2">
              Success and refusal rates for single-turn tactics
            </p>
            
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={singleTurnChartData}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 200, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" domain={[0, 100]} />
                  <YAxis type="category" dataKey="name" width={180} />
                  <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
                  <Legend />
                  <Bar 
                    dataKey="successRate" 
                    name="Success Rate (%)" 
                    fill="#82ca9d"
                    label={{ 
                      position: 'right', 
                      formatter: (value) => `${value.toFixed(1)}%`, 
                      fontSize: 12 
                    }}
                  />
                  <Bar 
                    dataKey="refusalRate" 
                    name="Refusal Rate (%)" 
                    fill="#8884d8"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
        
        {(turnType === 'all' || turnType === 'multi') && multiTurnChartData.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-semibold mb-2">Multi-Turn Tactic Effectiveness</h2>
            <p className="text-sm text-gray-500 mb-2">
              Success and refusal rates for multi-turn tactics
            </p>
            
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={multiTurnChartData}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 200, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" domain={[0, 100]} />
                  <YAxis type="category" dataKey="name" width={180} />
                  <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
                  <Legend />
                  <Bar 
                    dataKey="successRate" 
                    name="Success Rate (%)" 
                    fill="#ffc658"
                    label={{ 
                      position: 'right', 
                      formatter: (value) => `${value.toFixed(1)}%`, 
                      fontSize: 12 
                    }}
                  />
                  <Bar 
                    dataKey="refusalRate" 
                    name="Refusal Rate (%)" 
                    fill="#ff8042"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>
    );
  };
  
  const renderModelPerformance = () => {
    if (!selectedTacticData) {
      return <p>Please select a tactic to view model performance.</p>;
    }
    
    // Get models sorted by success rate
    const allModels = selectedTacticData.models;
    
    console.log("Tactic models before filtering:", allModels);
    
    // Calculate turn-specific metrics on the fly
    const modelsWithMetrics = allModels.map(model => {
      let value = 0;
      
      if (turnType === 'single') {
        // Get rows for this tactic and model
        const tacticRows = selectedTacticData?.singleTurnRows || [];
        const modelRows = tacticRows.filter(row => 
          (row.target_model || row.model) === model.modelName
        );
        
        console.log(`Found ${modelRows.length} single-turn rows for model ${model.modelName}`);
        
        // Calculate metrics if we have rows
        if (modelRows.length > 0) {
          const turnMetrics = calculateTurnTypeMetrics(modelRows);
          
          // Store for reference and debugging
          model.calculatedSingleTurnSuccessRate = turnMetrics.singleTurnSuccessRate;
          model.calculatedSingleTurnRefusalRate = turnMetrics.singleTurnRefusalRate;
          model.calculatedSingleTurnCount = turnMetrics.singleTurnCount;
          
          value = metric === 'success' ? turnMetrics.singleTurnSuccessRate :
                 metric === 'refusal' ? turnMetrics.singleTurnRefusalRate :
                 model.roundCount;
        }
      } else if (turnType === 'multi') {
        // Get rows for this tactic and model
        const tacticRows = selectedTacticData?.multiTurnRows || [];
        const modelRows = tacticRows.filter(row => 
          (row.target_model || row.model) === model.modelName
        );
        
        console.log(`Found ${modelRows.length} multi-turn rows for model ${model.modelName}`);
        
        // Calculate metrics if we have rows
        if (modelRows.length > 0) {
          const turnMetrics = calculateTurnTypeMetrics(modelRows);
          
          // Store for reference and debugging
          model.calculatedMultiTurnSuccessRate = turnMetrics.multiTurnSuccessRate;
          model.calculatedMultiTurnRefusalRate = turnMetrics.multiTurnRefusalRate;
          model.calculatedMultiTurnCount = turnMetrics.multiTurnCount;
          
          value = metric === 'success' ? turnMetrics.multiTurnSuccessRate :
                 metric === 'refusal' ? turnMetrics.multiTurnRefusalRate :
                 model.roundCount;
        }
      } else {
        // All turns case
        value = metric === 'success' ? model.successRate :
               metric === 'refusal' ? model.refusalRate :
               model.roundCount;
      }
      
      // Log for debugging
      console.log(`Model ${model.modelName} calculated metrics:`, {
        successRate: model.successRate,
        singleTurnCount: model.singleTurnCount,
        multiTurnCount: model.multiTurnCount,
        calculatedSingleTurnSuccessRate: model.calculatedSingleTurnSuccessRate,
        calculatedMultiTurnSuccessRate: model.calculatedMultiTurnSuccessRate,
        value: value
      });
      
      return {
        ...model,
        value: value
      };
    });
    
    // Filter out models with no data for selected turn type
    const filteredModels = modelsWithMetrics.filter(model => {
      if (turnType === 'single') {
        return model.calculatedSingleTurnCount > 0;
      }
      if (turnType === 'multi') {
        return model.calculatedMultiTurnCount > 0;
      }
      return true;
    });
    
    console.log("Filtered models:", filteredModels);
    
    // Prepare data for visualization
    const chartData = filteredModels.map((model, index) => ({
      name: model.modelName,
      value: model.value,
      fill: COLORS[index % COLORS.length]
    }));
    
    // Set up labels
    const metricLabel = metric === 'success' ? 'Success Rate (%)' : 
                       metric === 'refusal' ? 'Refusal Rate (%)' : 'Avg. Rounds';
    
    return (
      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-2">
          Model Performance with {selectedTacticData.name}
          {turnType === 'single' ? ' (Single-Turn Only)' : 
           turnType === 'multi' ? ' (Multi-Turn Only)' : ''}
        </h2>
        <p className="text-sm text-gray-500 mb-2">
          {metricLabel} across all models
        </p>
        
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 220, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 'auto']} />
              <YAxis type="category" dataKey="name" width={200} />
              <Tooltip formatter={(value) => `${value.toFixed(2)}`} />
              <Bar 
                dataKey="value" 
                label={{ 
                  position: 'right', 
                  formatter: (value) => `${value.toFixed(1)}`, 
                  fontSize: 12 
                }}
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  };
  
  const renderTacticDetails = () => {
    if (!selectedTacticData) {
      return <p>Please select a tactic to view details.</p>;
    }
    
    return (
      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-2">
          Details for {selectedTacticData.name}
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="bg-gray-100 p-4 rounded">
            <h3 className="font-semibold mb-1">Success Rate</h3>
            <p className="text-2xl">{selectedTacticData.avgSuccessRate.toFixed(2)}%</p>
            
            {selectedTacticData.singleTurnCount > 0 && (
              <p className="text-sm mt-2">Single-Turn: {selectedTacticData.singleTurnSuccessRate.toFixed(2)}%</p>
            )}
            {selectedTacticData.multiTurnCount > 0 && (
              <p className="text-sm">Multi-Turn: {selectedTacticData.multiTurnSuccessRate.toFixed(2)}%</p>
            )}
          </div>
          
          <div className="bg-gray-100 p-4 rounded">
            <h3 className="font-semibold mb-1">Refusal Rate</h3>
            <p className="text-2xl">{selectedTacticData.avgRefusalRate.toFixed(2)}%</p>
            
            {selectedTacticData.singleTurnCount > 0 && (
              <p className="text-sm mt-2">Single-Turn: {selectedTacticData.singleTurnRefusalRate.toFixed(2)}%</p>
            )}
            {selectedTacticData.multiTurnCount > 0 && (
              <p className="text-sm">Multi-Turn: {selectedTacticData.multiTurnRefusalRate.toFixed(2)}%</p>
            )}
          </div>
          
          <div className="bg-gray-100 p-4 rounded">
            <h3 className="font-semibold mb-1">Sample Count</h3>
            <p className="text-2xl">{selectedTacticData.totalSamples}</p>
            
            {selectedTacticData.singleTurnCount > 0 && (
              <p className="text-sm mt-2">Single-Turn: {selectedTacticData.singleTurnCount}</p>
            )}
            {selectedTacticData.multiTurnCount > 0 && (
              <p className="text-sm">Multi-Turn: {selectedTacticData.multiTurnCount}</p>
            )}
          </div>
        </div>
      </div>
    );
  };
  
  return (
    <div className="pb-8">
      <h1 className="text-2xl font-bold mb-4">Tactic Effectiveness Analysis</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          {renderTacticSelector()}
          {renderMetricSelector()}
        </div>
        <div>
          {renderTurnTypeSelector()}
        </div>
      </div>
      
      {!selectedTactic && renderTacticComparison()}
      
      {selectedTactic && (
        <>
          {renderTacticDetails()}
          {renderModelPerformance()}
        </>
      )}
    </div>
  );
};

export default TacticEffectiveness; 