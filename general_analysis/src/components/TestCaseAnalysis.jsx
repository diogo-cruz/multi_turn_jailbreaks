import React, { useState, useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, LabelList, ComposedChart, Line, Area
} from 'recharts';
import { calculateStandardError } from '../utils/dataProcessing';

// Color constants
const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE', 
  '#00C49F', '#FFBB28', '#FF8042', '#a4de6c', '#d0ed57'
];

const TestCaseAnalysis = ({ data, selectedTestCase, onTestCaseSelect, uniqueTestCases }) => {
  const [metric, setMetric] = useState("success");
  const [showAllModels, setShowAllModels] = useState(false);
  const [topModelCount, setTopModelCount] = useState(10);
  
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
              tactics: {}
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
          }
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
            tactics: {}
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
        count: metrics.rows?.length || 0
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
      const tacticEntries = Object.entries(data.tactics).map(([tacticName, rows]) => {
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
          
        return {
          tacticName,
          successRate,
          refusalRate,
          avgRounds,
          count: rows.length
        };
      });
      
      // Sort tactics by success rate
      const sortedTactics = [...tacticEntries].sort((a, b) => b.successRate - a.successRate);
      
      return {
        name: testCaseName,
        avgSuccessRate,
        avgRefusalRate,
        avgRounds,
        models: sortedModels,
        tactics: sortedTactics,
        modelCount: modelEntries.length,
        tacticCount: tacticEntries.length
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
          Average Rounds
        </label>
      </div>
    </div>
  );
  
  // Render model display options
  const renderModelDisplayOptions = () => (
    <div className="mb-4">
      <label className="block text-sm font-medium mb-1">Model Display Options:</label>
      <div className="flex items-center space-x-4">
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
          <div className="flex items-center">
            <span className="mr-2">Top Models:</span>
            <input 
              type="number"
              min="1"
              max="50"
              value={topModelCount}
              onChange={(e) => setTopModelCount(Math.max(1, parseInt(e.target.value, 10) || 1))}
              className="w-16 p-1 border rounded"
            />
          </div>
        )}
      </div>
    </div>
  );
  
  // Render test case overview
  const renderTestCaseOverview = () => {
    if (!processedData || processedData.length === 0) {
      return <div>No data available</div>;
    }
    
    // Get data based on selected metric
    const dataKey = metric === 'success' ? 'avgSuccessRate' : 
                    metric === 'refusal' ? 'avgRefusalRate' : 'avgRounds';
    
    // Sort data by the selected metric
    const sortedData = [...processedData].sort((a, b) => b[dataKey] - a[dataKey]);
    
    return (
      <div className="chart-container">
        <h3 className="text-lg font-medium mb-2">
          {metric === 'success' ? 'Average Success Rate' : 
           metric === 'refusal' ? 'Average Refusal Rate' : 'Average Rounds'} by Test Case
        </h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart
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
              metric === 'success' ? 'Average Success Rate' : 
              metric === 'refusal' ? 'Average Refusal Rate' : 'Average Rounds'
            ]} />
            <Legend />
            <Bar 
              dataKey={dataKey} 
              fill="#8884d8"
              name={metric === 'success' ? 'Average Success Rate' : 
                    metric === 'refusal' ? 'Average Refusal Rate' : 'Average Rounds'}
            >
              {sortedData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
              <LabelList dataKey={dataKey} position="top" formatter={(value) => `${value.toFixed(1)}${metric !== 'rounds' ? '%' : ''}`} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };
  
  // Render model performance for selected test case
  const renderModelPerformance = () => {
    if (!selectedTestCaseData) {
      return <div>Select a test case to view model performance</div>;
    }
    
    // Get data key based on selected metric
    const dataKey = metric === 'success' ? 'successRate' : 
                    metric === 'refusal' ? 'refusalRate' : 'roundCount';
    
    // Get models to display (all or top N)
    const displayModels = showAllModels 
      ? selectedTestCaseData.models 
      : selectedTestCaseData.models.slice(0, topModelCount);
    
    return (
      <div className="chart-container">
        <h3 className="text-lg font-medium mb-2">
          Model Performance for {selectedTestCaseData.name}
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
              fill="#8884d8"
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
  
  // Render tactic effectiveness for selected test case
  const renderTacticEffectiveness = () => {
    if (!selectedTestCaseData || !selectedTestCaseData.tactics || selectedTestCaseData.tactics.length === 0) {
      return <div>No tactic data available for this test case</div>;
    }
    
    // Get data key based on selected metric
    const dataKey = metric === 'success' ? 'successRate' : 
                    metric === 'refusal' ? 'refusalRate' : 'avgRounds';
    
    return (
      <div className="chart-container">
        <h3 className="text-lg font-medium mb-2">
          Tactic Effectiveness for {selectedTestCaseData.name}
        </h3>
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart
            data={selectedTestCaseData.tactics}
            margin={{ top: 20, right: 30, left: 30, bottom: 100 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="tacticName" 
              angle={-45} 
              textAnchor="end"
              height={100}
              interval={0}
            />
            <YAxis 
              yAxisId="left"
              label={{ 
                value: metric === 'success' ? 'Success Rate (%)' : 
                       metric === 'refusal' ? 'Refusal Rate (%)' : 'Average Rounds',
                angle: -90, 
                position: 'insideLeft' 
              }} 
            />
            <YAxis 
              yAxisId="right"
              orientation="right"
              label={{ 
                value: 'Sample Count', 
                angle: 90, 
                position: 'insideRight' 
              }}
            />
            <Tooltip formatter={(value, name) => {
              if (name === "Sample Count") return [value, name];
              return [
                `${value.toFixed(2)}${metric !== 'rounds' ? '%' : ''}`,
                metric === 'success' ? 'Success Rate' : 
                metric === 'refusal' ? 'Refusal Rate' : 'Average Rounds'
              ];
            }} />
            <Legend />
            <Bar 
              yAxisId="left"
              dataKey={dataKey} 
              fill="#8884d8"
              name={metric === 'success' ? 'Success Rate' : 
                    metric === 'refusal' ? 'Refusal Rate' : 'Average Rounds'}
            >
              {selectedTestCaseData.tactics.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
            <Line 
              type="monotone" 
              dataKey="count" 
              stroke="#ff7300" 
              name="Sample Count"
              yAxisId="right"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    );
  };
  
  // Render details for selected test case
  const renderTestCaseDetails = () => {
    if (!selectedTestCaseData) {
      return <div>Select a test case to view details</div>;
    }
    
    return (
      <div className="mt-8 p-4 border rounded">
        <h3 className="text-xl font-medium mb-2">{selectedTestCaseData.name}</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-3 rounded">
            <p className="text-sm text-gray-600">Average Success Rate</p>
            <p className="text-2xl font-bold">{selectedTestCaseData.avgSuccessRate.toFixed(2)}%</p>
          </div>
          <div className="bg-red-50 p-3 rounded">
            <p className="text-sm text-gray-600">Average Refusal Rate</p>
            <p className="text-2xl font-bold">{selectedTestCaseData.avgRefusalRate.toFixed(2)}%</p>
          </div>
          <div className="bg-green-50 p-3 rounded">
            <p className="text-sm text-gray-600">Average Rounds</p>
            <p className="text-2xl font-bold">{selectedTestCaseData.avgRounds.toFixed(2)}</p>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm">
              Models tested: <span className="font-medium">{selectedTestCaseData.modelCount}</span>
            </p>
          </div>
          <div>
            <p className="text-sm">
              Tactics used: <span className="font-medium">{selectedTestCaseData.tacticCount}</span>
            </p>
          </div>
        </div>
      </div>
    );
  };
  
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">Test Case Analysis</h2>
        <p className="text-gray-600">
          Analyze performance across different test cases, 
          comparing model effectiveness and tactics for each test scenario.
        </p>
      </div>
      
      <div className="flex flex-wrap -mx-2">
        <div className="w-full md:w-1/4 px-2">
          {renderTestCaseSelector()}
          {renderMetricSelector()}
          {renderModelDisplayOptions()}
        </div>
        
        <div className="w-full md:w-3/4 px-2">
          {renderTestCaseOverview()}
          {renderTestCaseDetails()}
          {renderModelPerformance()}
          {renderTacticEffectiveness()}
        </div>
      </div>
    </div>
  );
};

export default TestCaseAnalysis; 