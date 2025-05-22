import React, { useState, useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, LabelList, ComposedChart, Line, Area
} from 'recharts';
import { calculateStandardError, calculateTurnTypeMetrics } from '../utils/dataProcessing';

// Color constants
const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE', 
  '#00C49F', '#FFBB28', '#FF8042', '#a4de6c', '#d0ed57'
];

const TestCaseAnalysis = ({ data, selectedTestCase, onTestCaseSelect, uniqueTestCases }) => {
  const [metric, setMetric] = useState("success");
  const [showAllModels, setShowAllModels] = useState(false);
  const [topModelCount, setTopModelCount] = useState(10);
  const [turnType, setTurnType] = useState("all"); // "single", "multi", or "all"
  
  // Process data for visualization
  const processedData = useMemo(() => {
    if (!data || (Array.isArray(data) && data.length === 0)) {
      return [];
    }
    
    // Group by test case
    const testCaseData = {};
    
    // Handle different data formats
    if (Array.isArray(data) && data[0] && data[0].name) {
      // Already processed models array
      for (const model of data) {
        for (const testCase of model.testCases || []) {
          if (!testCaseData[testCase.name]) {
            testCaseData[testCase.name] = {
              models: {},
              tactics: {},
              singleTurnRows: [],
              multiTurnRows: []
            };
          }
          
          testCaseData[testCase.name].models[model.name] = {
            successRate: testCase.successRate,
            refusalRate: testCase.refusalRate,
            roundCount: testCase.roundCount,
            rows: testCase.rows
          };
          
          // Also collect tactic data for this test case
          for (const row of testCase.rows || []) {
            const tacticName = row.jailbreak || 'unknown';
            
            if (!testCaseData[testCase.name].tactics[tacticName]) {
              testCaseData[testCase.name].tactics[tacticName] = [];
            }
            
            testCaseData[testCase.name].tactics[tacticName].push(row);
            
            // Separate by turn type
            const isSingleTurn = row.num_turns === 1 || !row.num_turns;
            if (isSingleTurn) {
              testCaseData[testCase.name].singleTurnRows.push(row);
            } else {
              testCaseData[testCase.name].multiTurnRows.push(row);
            }
          }
        }
      }
      
      // Calculate single-turn and multi-turn metrics for each model
      for (const testCaseName in testCaseData) {
        const testCase = testCaseData[testCaseName];
        
        for (const modelName in testCase.models) {
          const modelData = testCase.models[modelName];
          const rows = modelData.rows || [];
          
          // Get single-turn rows for this model
          const singleTurnRows = rows.filter(row => row.num_turns === 1 || !row.num_turns);
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
          
          // Get multi-turn rows for this model
          const multiTurnRows = rows.filter(row => row.num_turns && row.num_turns > 1);
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
          
          // Calculate rates
          modelData.singleTurnCount = singleTurnRows.length;
          modelData.multiTurnCount = multiTurnRows.length;
          
          modelData.singleTurnSuccessRate = singleTurnRows.length > 0 
            ? (singleTurnSuccessful.length / singleTurnRows.length) * 100 
            : 0;
          modelData.singleTurnRefusalRate = singleTurnRows.length > 0 
            ? (singleTurnRefusal.length / singleTurnRows.length) * 100 
            : 0;
          
          modelData.multiTurnSuccessRate = multiTurnRows.length > 0 
            ? (multiTurnSuccessful.length / multiTurnRows.length) * 100 
            : 0;
          modelData.multiTurnRefusalRate = multiTurnRows.length > 0 
            ? (multiTurnRefusal.length / multiTurnRows.length) * 100 
            : 0;
        }
        
        // Calculate tactic metrics by turn type
        for (const tacticName in testCase.tactics) {
          const tacticRows = testCase.tactics[tacticName];
          
          // Single-turn metrics
          const singleTurnRows = tacticRows.filter(row => row.num_turns === 1 || !row.num_turns);
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
          
          // Multi-turn metrics
          const multiTurnRows = tacticRows.filter(row => row.num_turns && row.num_turns > 1);
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
          
          // Store metrics on the tactic array for later use
          testCase.tactics[tacticName] = {
            rows: tacticRows,
            singleTurnRows,
            multiTurnRows,
            singleTurnCount: singleTurnRows.length,
            multiTurnCount: multiTurnRows.length,
            singleTurnSuccessRate: singleTurnRows.length > 0 
              ? (singleTurnSuccessful.length / singleTurnRows.length) * 100 
              : 0,
            singleTurnRefusalRate: singleTurnRows.length > 0 
              ? (singleTurnRefusal.length / singleTurnRows.length) * 100 
              : 0,
            multiTurnSuccessRate: multiTurnRows.length > 0 
              ? (multiTurnSuccessful.length / multiTurnRows.length) * 100 
              : 0,
            multiTurnRefusalRate: multiTurnRows.length > 0 
              ? (multiTurnRefusal.length / multiTurnRows.length) * 100 
              : 0,
            tacticName: tacticName,
            successRate: tacticRows.length > 0 
              ? (tacticRows.filter(row => 
                  row.success !== undefined ? Boolean(row.success) : 
                  row.jailbreak_success !== undefined ? Boolean(row.jailbreak_success) :
                  row.asr !== undefined ? row.asr > 0 : false
                ).length / tacticRows.length) * 100 
              : 0,
            refusalRate: tacticRows.length > 0 
              ? (tacticRows.filter(row => 
                  row.refused !== undefined ? Boolean(row.refused) : 
                  row.refusal !== undefined ? Boolean(row.refusal) :
                  row.rejection !== undefined ? Boolean(row.rejection) : false
                ).length / tacticRows.length) * 100 
              : 0,
            avgRounds: tacticRows.length > 0
              ? tacticRows.reduce((sum, row) => sum + (row.num_turns || 1), 0) / tacticRows.length
              : 0,
            count: tacticRows.length
          };
        }
      }
    } else {
      // Raw data rows
      for (const row of data) {
        const testCaseName = row.test_case || 'unknown';
        const modelName = row.target_model || row.model || 'unknown';
        const tacticName = row.jailbreak || 'unknown';
        
        if (!testCaseData[testCaseName]) {
          testCaseData[testCaseName] = {
            models: {},
            tactics: {},
            singleTurnRows: [],
            multiTurnRows: []
          };
        }
        
        if (!testCaseData[testCaseName].models[modelName]) {
          testCaseData[testCaseName].models[modelName] = {
            rows: []
          };
        }
        
        testCaseData[testCaseName].models[modelName].rows.push(row);
        
        if (!testCaseData[testCaseName].tactics[tacticName]) {
          testCaseData[testCaseName].tactics[tacticName] = [];
        }
        
        testCaseData[testCaseName].tactics[tacticName].push(row);
        
        // Separate by turn type
        const isSingleTurn = row.num_turns === 1 || !row.num_turns;
        if (isSingleTurn) {
          testCaseData[testCaseName].singleTurnRows.push(row);
        } else {
          testCaseData[testCaseName].multiTurnRows.push(row);
        }
      }
      
      // Calculate metrics for each model within each test case
      for (const testCaseName in testCaseData) {
        for (const modelName in testCaseData[testCaseName].models) {
          const rows = testCaseData[testCaseName].models[modelName].rows;
          
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
          
          testCaseData[testCaseName].models[modelName].successRate = successRate;
          testCaseData[testCaseName].models[modelName].refusalRate = refusalRate;
          testCaseData[testCaseName].models[modelName].roundCount = roundCount;
        }
      }
    }
    
    // Format the processed data for each test case
    return Object.entries(testCaseData).map(([testCaseName, data]) => {
      // Calculate success rates across models
      const modelEntries = Object.entries(data.models).map(([modelName, metrics]) => ({
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
      const sortedModels = [...modelEntries].sort((a, b) => b.successRate - a.successRate);
      
      // Calculate average success rate for this test case
      const avgSuccessRate = modelEntries.length > 0 
        ? modelEntries.reduce((sum, model) => sum + model.successRate, 0) / modelEntries.length 
        : 0;
      
      // Calculate average refusal rate for this test case
      const avgRefusalRate = modelEntries.length > 0 
        ? modelEntries.reduce((sum, model) => sum + model.refusalRate, 0) / modelEntries.length 
        : 0;
      
      // Calculate average rounds for this test case
      const avgRounds = modelEntries.length > 0 
        ? modelEntries.reduce((sum, model) => sum + model.roundCount, 0) / modelEntries.length 
        : 0;
      
      // Process tactic effectiveness for this test case
      const tacticEntries = Object.values(data.tactics).map(tactic => ({
        tacticName: tactic.tacticName,
        successRate: tactic.successRate,
        refusalRate: tactic.refusalRate,
        avgRounds: tactic.avgRounds,
        count: tactic.rows.length,
        singleTurnCount: tactic.singleTurnCount,
        multiTurnCount: tactic.multiTurnCount,
        singleTurnSuccessRate: tactic.singleTurnSuccessRate,
        singleTurnRefusalRate: tactic.singleTurnRefusalRate,
        multiTurnSuccessRate: tactic.multiTurnSuccessRate,
        multiTurnRefusalRate: tactic.multiTurnRefusalRate
      }));
      
      // Sort tactics by success rate
      const sortedTactics = [...tacticEntries].sort((a, b) => b.successRate - a.successRate);
      
      // Process single turn data
      const singleTurnSuccessRate = data.singleTurnRows.length > 0
        ? (data.singleTurnRows.filter(row => 
            row.success !== undefined ? Boolean(row.success) : 
            row.jailbreak_success !== undefined ? Boolean(row.jailbreak_success) :
            row.asr !== undefined ? row.asr > 0 : false
          ).length / data.singleTurnRows.length) * 100
        : 0;
        
      const singleTurnRefusalRate = data.singleTurnRows.length > 0
        ? (data.singleTurnRows.filter(row => 
            row.refused !== undefined ? Boolean(row.refused) : 
            row.refusal !== undefined ? Boolean(row.refusal) :
            row.rejection !== undefined ? Boolean(row.rejection) : false
          ).length / data.singleTurnRows.length) * 100
        : 0;
      
      // Process multi turn data
      const multiTurnSuccessRate = data.multiTurnRows.length > 0
        ? (data.multiTurnRows.filter(row => 
            row.success !== undefined ? Boolean(row.success) : 
            row.jailbreak_success !== undefined ? Boolean(row.jailbreak_success) :
            row.asr !== undefined ? row.asr > 0 : false
          ).length / data.multiTurnRows.length) * 100
        : 0;
        
      const multiTurnRefusalRate = data.multiTurnRows.length > 0
        ? (data.multiTurnRows.filter(row => 
            row.refused !== undefined ? Boolean(row.refused) : 
            row.refusal !== undefined ? Boolean(row.refusal) :
            row.rejection !== undefined ? Boolean(row.rejection) : false
          ).length / data.multiTurnRows.length) * 100
        : 0;
      
      return {
        name: testCaseName,
        avgSuccessRate,
        avgRefusalRate,
        avgRounds,
        models: sortedModels,
        tactics: sortedTactics,
        modelCount: modelEntries.length,
        tacticCount: tacticEntries.length,
        singleTurnCount: data.singleTurnRows.length,
        multiTurnCount: data.multiTurnRows.length,
        singleTurnSuccessRate,
        singleTurnRefusalRate,
        multiTurnSuccessRate,
        multiTurnRefusalRate
      };
    });
  }, [data]);
  
  // Get the data for the selected test case
  const selectedTestCaseData = useMemo(() => {
    if (!selectedTestCase || !processedData || processedData.length === 0) {
      return null;
    }
    
    return processedData.find(tc => tc.name === selectedTestCase) || null;
  }, [selectedTestCase, processedData]);

  // Filter data by turn type
  const filteredProcessedData = useMemo(() => {
    if (!processedData || processedData.length === 0) {
      return [];
    }
    
    // Return all data but make sure the renderTurnTypeComparison function will filter data
    return processedData;
  }, [processedData]);
  
  // Render test case selector
  const renderTestCaseSelector = () => (
    <div className="mb-4">
      <label className="block text-sm font-medium mb-1">Select Test Case:</label>
      <select 
        className="w-full p-2 border rounded"
        value={selectedTestCase || ''}
        onChange={(e) => onTestCaseSelect(e.target.value)}
      >
        {(uniqueTestCases || []).map(testCase => (
          <option key={testCase} value={testCase}>{testCase}</option>
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
          Avg. Rounds
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
  
  // Render model display options
  const renderModelDisplayOptions = () => (
    <div className="mb-4">
      <label className="inline-flex items-center">
        <input 
          type="checkbox" 
          checked={showAllModels} 
          onChange={() => setShowAllModels(!showAllModels)}
          className="mr-1"
        />
        Show All Models
      </label>
      {!showAllModels && (
        <div className="mt-2">
          <label className="block text-sm font-medium mb-1">
            Top Models to Display: {topModelCount}
          </label>
          <input 
            type="range" 
            min="3" 
            max="20" 
            value={topModelCount} 
            onChange={(e) => setTopModelCount(parseInt(e.target.value))}
            className="w-full"
          />
        </div>
      )}
    </div>
  );
  
  // Render test case overview
  const renderTestCaseOverview = () => {
    if (!filteredProcessedData || filteredProcessedData.length === 0) {
      return <p>No test case data available.</p>;
    }
    
    // Get the metric field based on user selection
    const metricField = metric === 'success' ? 'avgSuccessRate' : 
                       metric === 'refusal' ? 'avgRefusalRate' : 'avgRounds';
    
    // Sort test cases by the selected metric
    const sortedTestCases = [...filteredProcessedData]
      .filter(tc => {
        if (turnType === 'single') return tc.singleTurnCount > 0;
        if (turnType === 'multi') return tc.multiTurnCount > 0;
        return true;
      })
      .sort((a, b) => b[metricField] - a[metricField]);
    
    // Prepare data for visualization
    const chartData = sortedTestCases.map(tc => ({
      name: tc.name,
      value: tc[metricField],
      fill: COLORS[0]
    }));
    
    // Set up labels
    const metricLabel = metric === 'success' ? 'Success Rate (%)' : 
                       metric === 'refusal' ? 'Refusal Rate (%)' : 'Avg. Rounds';
    
    return (
      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-2">Overview of Test Cases</h2>
        <p className="text-sm text-gray-500 mb-2">
          Comparison of {metricLabel} across all test cases
          {turnType === 'single' ? ' (Single-Turn Only)' : 
           turnType === 'multi' ? ' (Multi-Turn Only)' : ''}
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
                fill="#8884d8"
                label={{ 
                  position: 'right', 
                  formatter: (value) => `${value.toFixed(1)}`, 
                  fontSize: 12 
                }}
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  };
  
  // Render model performance for selected test case
  const renderModelPerformance = () => {
    if (!selectedTestCaseData) {
      return <p>Please select a test case to view model performance.</p>;
    }
    
    // Get models sorted by success rate
    const allModels = selectedTestCaseData.models;
    
    // Add debugging to check data
    console.log("Turn Type:", turnType);
    console.log("Selected Test Case Data:", selectedTestCaseData);
    console.log("All Models:", allModels);
    
    // Model data for the current turn type
    const filteredModels = allModels.map(model => {
      // Get the appropriate data for this model based on turn type
      let value = 0;
      
      if (turnType === 'single') {
        // Calculate on the fly for single turn
        const testCaseRows = selectedTestCaseData?.singleTurnRows || [];
        const modelRows = testCaseRows.filter(row => 
          (row.target_model || row.model) === model.modelName
        );
        
        // If we have rows for this model, calculate metrics
        if (modelRows.length > 0) {
          const turnMetrics = calculateTurnTypeMetrics(modelRows);
          
          // Store for logging/debugging
          model.calculatedSingleTurnSuccessRate = turnMetrics.singleTurnSuccessRate;
          model.calculatedSingleTurnRefusalRate = turnMetrics.singleTurnRefusalRate;
          model.calculatedSingleTurnCount = turnMetrics.singleTurnCount;
          
          value = metric === 'success' ? turnMetrics.singleTurnSuccessRate :
                 metric === 'refusal' ? turnMetrics.singleTurnRefusalRate :
                 model.roundCount;
        }
      } else if (turnType === 'multi') {
        // Calculate on the fly for multi turn
        const testCaseRows = selectedTestCaseData?.multiTurnRows || [];
        const modelRows = testCaseRows.filter(row => 
          (row.target_model || row.model) === model.modelName
        );
        
        // If we have rows for this model, calculate metrics
        if (modelRows.length > 0) {
          const turnMetrics = calculateTurnTypeMetrics(modelRows);
          
          // Store for logging/debugging
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
      
      // Log individual model properties
      console.log(`Model ${model.modelName}:`, {
        successRate: model.successRate,
        singleTurnSuccessRate: model.singleTurnSuccessRate,
        multiTurnSuccessRate: model.multiTurnSuccessRate,
        calculatedSingleTurnSuccessRate: model.calculatedSingleTurnSuccessRate,
        calculatedMultiTurnSuccessRate: model.calculatedMultiTurnSuccessRate,
        singleTurnCount: model.singleTurnCount,
        multiTurnCount: model.multiTurnCount,
        value: value
      });
      
      return { 
        ...model, 
        value: value 
      };
    });
    
    const modelsToDisplay = showAllModels 
      ? filteredModels 
      : filteredModels.slice(0, Math.min(topModelCount, filteredModels.length));
    
    // Prepare data for visualization
    const chartData = modelsToDisplay.map((model, index) => ({
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
          Model Performance for {selectedTestCaseData.name}
          {turnType === 'single' ? ' (Single-Turn Only)' : 
           turnType === 'multi' ? ' (Multi-Turn Only)' : ''}
        </h2>
        <p className="text-sm text-gray-500 mb-2">
          {metricLabel} across top {modelsToDisplay.length} models
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
  
  // Render turn type comparison
  const renderTurnTypeComparison = () => {
    if (!filteredProcessedData || filteredProcessedData.length === 0) {
      return <p>No test case data available.</p>;
    }
    
    // Filter out test cases with no single or multi-turn data based on selected turn type
    const filteredTestCases = filteredProcessedData.filter(tc => {
      if (turnType === 'single') return tc.singleTurnCount > 0;
      if (turnType === 'multi') return tc.multiTurnCount > 0;
      return tc.singleTurnCount > 0 || tc.multiTurnCount > 0;
    });
    
    // Sort test cases by success rate
    const sortedTestCases = [...filteredTestCases]
      .sort((a, b) => {
        if (turnType === 'single') return b.singleTurnSuccessRate - a.singleTurnSuccessRate;
        if (turnType === 'multi') return b.multiTurnSuccessRate - a.multiTurnSuccessRate;
        return b.avgSuccessRate - a.avgSuccessRate;
      });
    
    // Prepare chart data
    const singleTurnChartData = sortedTestCases
      .filter(tc => tc.singleTurnCount > 0)
      .map(tc => ({
        name: tc.name,
        successRate: tc.singleTurnSuccessRate,
        refusalRate: tc.singleTurnRefusalRate,
        sampleCount: tc.singleTurnCount
      }));
    
    const multiTurnChartData = sortedTestCases
      .filter(tc => tc.multiTurnCount > 0)
      .map(tc => ({
        name: tc.name,
        successRate: tc.multiTurnSuccessRate,
        refusalRate: tc.multiTurnRefusalRate,
        sampleCount: tc.multiTurnCount
      }));
    
    return (
      <div>
        {(turnType === 'all' || turnType === 'single') && singleTurnChartData.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-semibold mb-2">Single-Turn Test Case Performance</h2>
            <p className="text-sm text-gray-500 mb-2">
              Success and refusal rates for single-turn test cases
            </p>
            
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={singleTurnChartData}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 220, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" domain={[0, 100]} />
                  <YAxis type="category" dataKey="name" width={200} />
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
            <h2 className="text-lg font-semibold mb-2">Multi-Turn Test Case Performance</h2>
            <p className="text-sm text-gray-500 mb-2">
              Success and refusal rates for multi-turn test cases
            </p>
            
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={multiTurnChartData}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 220, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" domain={[0, 100]} />
                  <YAxis type="category" dataKey="name" width={200} />
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
  
  // Render tactic effectiveness for selected test case
  const renderTacticEffectiveness = () => {
    if (!selectedTestCaseData) {
      return <p>Please select a test case to view tactic effectiveness.</p>;
    }
    
    // Get tactics sorted by success rate
    const sortedTactics = selectedTestCaseData.tactics;
    
    // Get the metric field based on user selection and turn type
    const metricField = metric === 'success' ? 
      (turnType === 'single' ? 'singleTurnSuccessRate' : 
       turnType === 'multi' ? 'multiTurnSuccessRate' : 'successRate') :
      metric === 'refusal' ? 
      (turnType === 'single' ? 'singleTurnRefusalRate' : 
       turnType === 'multi' ? 'multiTurnRefusalRate' : 'refusalRate') : 
      'avgRounds';
    
    // Prepare data for visualization
    const chartData = sortedTactics
      .filter(tactic => {
        if (turnType === 'single') return tactic.singleTurnCount > 0;
        if (turnType === 'multi') return tactic.multiTurnCount > 0;
        return true;
      })
      .map((tactic, index) => ({
        name: tactic.tacticName,
        value: turnType === 'single' ? (tactic.singleTurnSuccessRate || 0) :
               turnType === 'multi' ? (tactic.multiTurnSuccessRate || 0) :
               tactic[metricField],
        fill: COLORS[index % COLORS.length]
      }));
    
    // Set up labels
    const metricLabel = metric === 'success' ? 'Success Rate (%)' : 
                      metric === 'refusal' ? 'Refusal Rate (%)' : 'Avg. Rounds';
    
    return (
      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-2">
          Tactic Effectiveness for {selectedTestCaseData.name}
          {turnType === 'single' ? ' (Single-Turn Only)' : 
           turnType === 'multi' ? ' (Multi-Turn Only)' : ''}
        </h2>
        <p className="text-sm text-gray-500 mb-2">
          {metricLabel} across all tactics
        </p>
        
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 180, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 'auto']} />
              <YAxis type="category" dataKey="name" width={160} />
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
  
  // Render details for selected test case
  const renderTestCaseDetails = () => {
    if (!selectedTestCaseData) {
      return <p>Please select a test case to view details.</p>;
    }
    
    return (
      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-2">
          Details for {selectedTestCaseData.name}
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="bg-gray-100 p-4 rounded">
            <h3 className="font-semibold mb-1">Success Rate</h3>
            <p className="text-2xl">{selectedTestCaseData.avgSuccessRate.toFixed(2)}%</p>
            {selectedTestCaseData.singleTurnCount > 0 && (
              <p className="text-sm mt-2">Single-Turn: {selectedTestCaseData.singleTurnSuccessRate.toFixed(2)}%</p>
            )}
            {selectedTestCaseData.multiTurnCount > 0 && (
              <p className="text-sm">Multi-Turn: {selectedTestCaseData.multiTurnSuccessRate.toFixed(2)}%</p>
            )}
          </div>
          
          <div className="bg-gray-100 p-4 rounded">
            <h3 className="font-semibold mb-1">Refusal Rate</h3>
            <p className="text-2xl">{selectedTestCaseData.avgRefusalRate.toFixed(2)}%</p>
            {selectedTestCaseData.singleTurnCount > 0 && (
              <p className="text-sm mt-2">Single-Turn: {selectedTestCaseData.singleTurnRefusalRate.toFixed(2)}%</p>
            )}
            {selectedTestCaseData.multiTurnCount > 0 && (
              <p className="text-sm">Multi-Turn: {selectedTestCaseData.multiTurnRefusalRate.toFixed(2)}%</p>
            )}
          </div>
          
          <div className="bg-gray-100 p-4 rounded">
            <h3 className="font-semibold mb-1">Sample Count</h3>
            <p className="text-2xl">{selectedTestCaseData.singleTurnCount + selectedTestCaseData.multiTurnCount}</p>
            {selectedTestCaseData.singleTurnCount > 0 && (
              <p className="text-sm mt-2">Single-Turn: {selectedTestCaseData.singleTurnCount}</p>
            )}
            {selectedTestCaseData.multiTurnCount > 0 && (
              <p className="text-sm">Multi-Turn: {selectedTestCaseData.multiTurnCount}</p>
            )}
          </div>
        </div>
      </div>
    );
  };
  
  return (
    <div className="pb-8">
      <h1 className="text-2xl font-bold mb-4">Test Case Analysis</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          {renderTestCaseSelector()}
          {renderMetricSelector()}
        </div>
        <div>
          {renderTurnTypeSelector()}
          {renderModelDisplayOptions()}
        </div>
      </div>
      
      {!selectedTestCase && (
        <>
          {renderTestCaseOverview()}
          {renderTurnTypeComparison()}
        </>
      )}
      
      {selectedTestCase && (
        <>
          {renderTestCaseDetails()}
          {renderModelPerformance()}
          {renderTacticEffectiveness()}
        </>
      )}
    </div>
  );
};

export default TestCaseAnalysis; 