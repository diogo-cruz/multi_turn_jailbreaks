import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, LabelList, LineChart, Line, ScatterChart, Scatter, ZAxis, ErrorBar
} from 'recharts';
import Papa from 'papaparse';

// The main component
const InteractiveJailbreakViz = () => {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedModel, setSelectedModel] = useState(0);
  const [selectedTestCase, setSelectedTestCase] = useState('');
  const [selectedTactic, setSelectedTactic] = useState('');
  const [activeTab, setActiveTab] = useState("model");
  // Add state for CSV file selection
  const [selectedFile, setSelectedFile] = useState('results_test_runs.csv');
  const [availableFiles, setAvailableFiles] = useState([
    'results_test_runs.csv',
    'results_2D.csv',
    'results_2B.csv',
    'results_batch2D_2.csv',
    'results_final_3samples.csv'
  ]);
  
  // Load and process the data
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        
        // Read and parse the selected CSV file
        const response = await fetch(`/${selectedFile}`);
        const fileContent = await response.text();
        
        const parsedData = Papa.parse(fileContent, {
          header: true,
          dynamicTyping: true,
          skipEmptyLines: true
        }).data;
        
        // Process the data
        const processedModels = processJailbreakData(parsedData);
        setModels(processedModels);
        
        // Set initial selections
        if (processedModels.length > 0) {
          const firstModel = processedModels[0];
          setSelectedTestCase(firstModel.testCases[0]?.name || '');
          
          // Find common tactics across models
          const commonTactics = processedModels.reduce((common, model) => {
            const multiTacticNames = model.tactics.multi.map(t => t.name);
            const singleTacticNames = model.tactics.single.map(t => t.name);
            
            return common.filter(tactic => 
              multiTacticNames.includes(tactic) && singleTacticNames.includes(tactic)
            );
          }, processedModels[0].tactics.multi.map(t => t.name));
          
          setSelectedTactic(commonTactics[0] || '');
        }
        
        setLoading(false);
      } catch (err) {
        console.error("Error loading data:", err);
        setError("Failed to load data. Please try again.");
        setLoading(false);
      }
    };
    
    loadData();
  }, [selectedFile]); // Add selectedFile as dependency to reload when file changes
  
  // Function to process the jailbreak test data
  function processJailbreakData(data) {
    // Model parameter sizes (in billions)
    const modelSizes = {
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
      'qwen/qwen-2.5-7b-instruct': 7,
      'qwen/qwen-2.5-72b-instruct': 72,
      'mistralai/mistral-7b-instruct-v0.3': 7,
      'mistralai/mistral-small-3.1-24b-instruct': 24,
      'mistralai/mistral-tiny': 3,
      'mistralai/mistral-nemo': 12,
      'meta-llama/llama-4-scout': 8,
      'meta-llama/llama-4-maverick': 44,
      'deepseek/deepseek-chat-v3-0324': 16,
      'x-ai/grok-3-mini-beta': 10
    };

    // Get unique models and sort them
    const models = [...new Set(data.map(row => row.target_model))].sort();
    
    // Function to parse score strings
    function parseScores(scoresStr) {
      if (!scoresStr) return [];
      try {
        return JSON.parse(scoresStr);
      } catch (e) {
        if (typeof scoresStr === 'string') {
          return scoresStr.split(',').map(s => {
            const num = parseFloat(s.trim());
            return isNaN(num) ? 0 : num;
          });
        }
        return [];
      }
    }
    
    // Calculate ASR (Attack Success Rate) - percentage of attempts with score = 1.0
    function calculateASR(subset) {
      if (subset.length === 0) return 0;
      
      const successfulAttacks = subset.filter(row => {
        const scores = parseScores(row.scores);
        return scores.some(score => score === 1.0);
      });
      
      return (successfulAttacks.length / subset.length) * 100;
    }
    
    // Calculate average value for a property
    function calculateAverage(subset, property) {
      if (subset.length === 0) return 0;
      const sum = subset.reduce((acc, row) => acc + (row[property] || 0), 0);
      return sum / subset.length;
    }
    
    // Process each model
    return models.map(modelName => {
      const modelData = data.filter(row => row.target_model === modelName);
      
      // Get unique test cases and tactics for this model
      const testCases = [...new Set(modelData.map(row => row.test_case))].sort();
      const multiTactics = [...new Set(modelData.filter(row => row.turn_type === 'multi').map(row => row.jailbreak_tactic))].sort();
      const singleTactics = [...new Set(modelData.filter(row => row.turn_type === 'single').map(row => row.jailbreak_tactic))].sort();
      
      // Process test cases - calculate ASR for multi and single turn types
      const testCasesData = testCases.map(testCase => {
        const multiTests = modelData.filter(row => row.test_case === testCase && row.turn_type === 'multi');
        const singleTests = modelData.filter(row => row.test_case === testCase && row.turn_type === 'single');
        
        return {
          name: testCase,
          multi: Math.round(calculateASR(multiTests) * 10) / 10,
          single: Math.round(calculateASR(singleTests) * 10) / 10
        };
      });
      
      // Process tactics - calculate ASR for each tactic
      const tacticsData = {
        multi: multiTactics.map(tactic => {
          const tacticTests = modelData.filter(row => row.jailbreak_tactic === tactic && row.turn_type === 'multi');
          return {
            name: tactic,
            asr: Math.round(calculateASR(tacticTests) * 10) / 10
          };
        }),
        single: singleTactics.map(tactic => {
          const tacticTests = modelData.filter(row => row.jailbreak_tactic === tactic && row.turn_type === 'single');
          return {
            name: tactic,
            asr: Math.round(calculateASR(tacticTests) * 10) / 10
          };
        })
      };
      
      // Build heatmaps - test case × tactic success rates
      const heatmapsData = {
        multi: testCases.map(testCase => 
          multiTactics.map(tactic => {
            const subset = modelData.filter(row => 
              row.test_case === testCase && 
              row.jailbreak_tactic === tactic && 
              row.turn_type === 'multi'
            );
            return Math.round(calculateASR(subset));
          })
        ),
        single: testCases.map(testCase => 
          singleTactics.map(tactic => {
            const subset = modelData.filter(row => 
              row.test_case === testCase && 
              row.jailbreak_tactic === tactic && 
              row.turn_type === 'single'
            );
            return Math.round(calculateASR(subset));
          })
        )
      };
      
      // Build refusal counts
      const refusalCountsData = {
        multi: testCases.map(testCase => 
          multiTactics.map(tactic => {
            const subset = modelData.filter(row => 
              row.test_case === testCase && 
              row.jailbreak_tactic === tactic && 
              row.turn_type === 'multi'
            );
            return Math.round(calculateAverage(subset, 'refused'));
          })
        ),
        single: testCases.map(testCase => 
          singleTactics.map(tactic => {
            const subset = modelData.filter(row => 
              row.test_case === testCase && 
              row.jailbreak_tactic === tactic && 
              row.turn_type === 'single'
            );
            return Math.round(calculateAverage(subset, 'refused'));
          })
        )
      };
      
      // Build round counts
      const roundCountsData = {
        multi: testCases.map(testCase => 
          multiTactics.map(tactic => {
            const subset = modelData.filter(row => 
              row.test_case === testCase && 
              row.jailbreak_tactic === tactic && 
              row.turn_type === 'multi'
            );
            return Math.round(calculateAverage(subset, 'max_round'));
          })
        ),
        single: testCases.map(testCase => 
          singleTactics.map(tactic => {
            const subset = modelData.filter(row => 
              row.test_case === testCase && 
              row.jailbreak_tactic === tactic && 
              row.turn_type === 'single'
            );
            return Math.round(calculateAverage(subset, 'max_round'));
          })
        )
      };
      
      // Return the complete model data
      return {
        name: modelName,
        paramSize: modelSizes[modelName] || 10, // Default if not found
        testCases: testCasesData,
        tactics: tacticsData,
        heatmaps: heatmapsData,
        refusalCounts: refusalCountsData,
        roundCounts: roundCountsData
      };
    });
  }
  
  // Function to get all common tactics across models (for both multi and single turn)
  const getCommonTactics = () => {
    if (!models.length) return [];
    
    return models.reduce((common, model) => {
      const multiTacticNames = model.tactics.multi.map(t => t.name);
      const singleTacticNames = model.tactics.single.map(t => t.name);
      
      return common.filter(tactic => 
        multiTacticNames.includes(tactic) && singleTacticNames.includes(tactic)
      );
    }, models[0].tactics.multi.map(t => t.name));
  };
  
  // Get the current model data
  const model = models[selectedModel] || null;
  const commonTactics = getCommonTactics();
  
  // Generate test case size data
  const generateTestCaseSizeData = (testCase) => {
    return models.map(model => {
      // Find the test case data
      const testCaseData = model.testCases.find(tc => tc.name === testCase);
      if (!testCaseData) return null;
      
      // Find maximum ASR for the test case across common tactics
      const testCaseIndex = model.testCases.findIndex(tc => tc.name === testCase);
      if (testCaseIndex === -1) return null;
      
      const multiTacticIndices = commonTactics.map(tacticName => 
        model.tactics.multi.findIndex(t => t.name === tacticName)
      ).filter(idx => idx !== -1);
      
      const singleTacticIndices = commonTactics.map(tacticName => 
        model.tactics.single.findIndex(t => t.name === tacticName)
      ).filter(idx => idx !== -1);
      
      const multiMaxASR = multiTacticIndices.length ? 
        Math.max(...multiTacticIndices.map(idx => 
          model.heatmaps.multi[testCaseIndex]?.[idx] || 0
        )) : 0;
      
      const singleMaxASR = singleTacticIndices.length ? 
        Math.max(...singleTacticIndices.map(idx => 
          model.heatmaps.single[testCaseIndex]?.[idx] || 0
        )) : 0;
      
      // Calculate standard error across tactics
      const multiValues = multiTacticIndices.map(idx => 
        model.heatmaps.multi[testCaseIndex]?.[idx] || 0
      );
      
      const singleValues = singleTacticIndices.map(idx => 
        model.heatmaps.single[testCaseIndex]?.[idx] || 0
      );
      
      const multiSE = calculateStandardError(multiValues);
      const singleSE = calculateStandardError(singleValues);
      
      return {
        modelName: model.name.split('/').pop(),
        paramSize: model.paramSize,
        multi: testCaseData.multi,
        single: testCaseData.single,
        multiMax: multiMaxASR,
        singleMax: singleMaxASR,
        multiSE,
        singleSE
      };
    }).filter(Boolean).sort((a, b) => a.paramSize - b.paramSize);
  };
  
  // Generate tactic ASR vs model size data
  const generateTacticSizeData = (tactic) => {
    return models.map(model => {
      // Find the tactic in multi-turn data
      const multiTactic = model.tactics.multi.find(t => t.name === tactic);
      
      // Find the tactic in single-turn data
      const singleTactic = model.tactics.single.find(t => t.name === tactic);
      
      if (!multiTactic && !singleTactic) return null;
      
      // Calculate standard error across test cases
      const multiTacticIndex = model.tactics.multi.findIndex(t => t.name === tactic);
      const singleTacticIndex = model.tactics.single.findIndex(t => t.name === tactic);
      
      const multiValues = multiTacticIndex !== -1 ? 
        model.testCases.map((_, idx) => model.heatmaps.multi[idx]?.[multiTacticIndex] || 0) : [];
      
      const singleValues = singleTacticIndex !== -1 ? 
        model.testCases.map((_, idx) => model.heatmaps.single[idx]?.[singleTacticIndex] || 0) : [];
      
      const multiSE = calculateStandardError(multiValues);
      const singleSE = calculateStandardError(singleValues);
      
      return {
        modelName: model.name.split('/').pop(),
        paramSize: model.paramSize,
        multi: multiTactic ? multiTactic.asr : 0,
        single: singleTactic ? singleTactic.asr : 0,
        multiSE,
        singleSE
      };
    }).filter(Boolean).sort((a, b) => a.paramSize - b.paramSize);
  };
  
  // Helper function to calculate standard error
  const calculateStandardError = (values) => {
    if (!values.length) return 0;
    
    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const squaredDiffs = values.map(val => Math.pow(val - mean, 2));
    const variance = squaredDiffs.reduce((sum, val) => sum + val, 0) / values.length;
    const stdDev = Math.sqrt(variance);
    
    return stdDev / Math.sqrt(values.length);
  };
  
  // Get data for current selections
  const testCaseSizeData = selectedTestCase ? generateTestCaseSizeData(selectedTestCase) : [];
  const tacticSizeData = selectedTactic ? generateTacticSizeData(selectedTactic) : [];
  
  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading data...</div>;
  }
  
  if (error) {
    return <div className="text-red-600 p-4">{error}</div>;
  }
  
  if (!models.length) {
    return <div className="p-4">No data available.</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="text-xl">Loading data...</div>
        </div>
      ) : error ? (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
          {error}
        </div>
      ) : (
        <>
          {/* Add file selector */}
          <div className="mb-6 bg-gray-100 p-4 rounded-lg">
            <h2 className="text-xl font-bold mb-3">Dataset Selection</h2>
            <div className="flex items-center">
              <label htmlFor="fileSelect" className="mr-2 font-medium">Choose dataset:</label>
              <select 
                id="fileSelect" 
                value={selectedFile} 
                onChange={(e) => setSelectedFile(e.target.value)}
                className="border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {availableFiles.map(file => (
                  <option key={file} value={file}>{file}</option>
                ))}
              </select>
            </div>
            <div className="mt-2 text-sm text-gray-600">
              Currently analyzing: <span className="font-medium">{selectedFile}</span>
              {models.length > 0 && ` (${models.length} models)`}
            </div>
          </div>

          {/* Rest of the UI */}
          <div className="tabs mb-6">
            <button 
              className={`tab ${activeTab === "model" ? "active" : ""}`}
              onClick={() => setActiveTab("model")}
            >
              Model Analysis
            </button>
            <button 
              className={`tab ${activeTab === "testCase" ? "active" : ""}`}
              onClick={() => setActiveTab("testCase")}
            >
              Test Case vs Size
            </button>
            <button 
              className={`tab ${activeTab === "tactic" ? "active" : ""}`}
              onClick={() => setActiveTab("tactic")}
            >
              Tactic vs Size
            </button>
            <button 
              className={`tab ${activeTab === "heatmap" ? "active" : ""}`}
              onClick={() => setActiveTab("heatmap")}
            >
              Heatmaps
            </button>
          </div>
          
          {/* Model Analysis Tab */}
          {activeTab === 'model' && model && (
            <div>
              <div className="mb-6">
                <div className="flex flex-col">
                  <label className="mb-1 font-medium">Select Model:</label>
                  <select 
                    className="p-2 border rounded w-full md:w-96"
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(parseInt(e.target.value))}
                  >
                    {models.map((model, idx) => (
                      <option key={idx} value={idx}>{model.name}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              {/* Test Case Comparison Chart */}
              <div className="border p-4 rounded shadow-sm mt-6">
                <div className="font-semibold mb-4 text-center">{`Test Case Success Rates (ASR%) - ${model.name}`}</div>
                <ResponsiveContainer width="100%" height={1750}>
                  <BarChart
                    data={model.testCases}
                    layout="vertical"
                    margin={{ top: 20, right: 30, left: 160, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" domain={[0, 100]} />
                    <YAxis type="category" dataKey="name" width={160} tick={{ fontSize: 12 }} interval={0} />
                    <Tooltip />
                    <Legend verticalAlign="top" height={36} />
                    <Bar name="Multi-Turn ASR" dataKey="multi" fill="#8884d8" barSize={12} />
                    <Bar name="Single-Turn ASR" dataKey="single" fill="#82ca9d" barSize={12} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              
              {/* Tactics Comparison Chart */}
              <div className="border p-4 rounded shadow-sm mt-6">
                <div className="font-semibold mb-4 text-center">{`Jailbreak Tactic Success Rates (ASR%) - ${model.name}`}</div>
                <ResponsiveContainer width="100%" height={350}>
                  <BarChart
                    data={[...model.tactics.multi.map(t => ({ name: t.name, multi: t.asr, single: 0 }))].map(item => {
                      const singleTactic = model.tactics.single.find(t => t.name === item.name);
                      return {
                        ...item,
                        single: singleTactic ? singleTactic.asr : 0
                      };
                    })}
                    margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="name" 
                      angle={-45} 
                      textAnchor="end" 
                      height={100}
                    />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Legend verticalAlign="top" height={36} />
                    <Bar name="Multi-Turn ASR" dataKey="multi" fill="#8884d8" />
                    <Bar name="Single-Turn ASR" dataKey="single" fill="#82ca9d" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              
              {/* Model Comparison Chart */}
              <div className="border p-4 rounded shadow-sm mt-8">
                <h2 className="text-xl font-semibold mb-4 text-center">Model Comparison</h2>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart
                    data={models.map(model => ({
                      name: model.name.split('/').pop(),
                      multiAvg: model.testCases.reduce((sum, tc) => sum + tc.multi, 0) / model.testCases.length,
                      singleAvg: model.testCases.reduce((sum, tc) => sum + tc.single, 0) / model.testCases.length
                    }))}
                    margin={{ top: 20, right: 30, left: 20, bottom: 70 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="name" 
                      angle={-45} 
                      textAnchor="end" 
                      height={70}
                      interval={0}
                    />
                    <YAxis domain={[0, 100]} label={{ value: 'Average ASR (%)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Legend verticalAlign="top" height={36} />
                    <Bar name="Multi-Turn Average ASR" dataKey="multiAvg" fill="#8884d8" />
                    <Bar name="Single-Turn Average ASR" dataKey="singleAvg" fill="#82ca9d" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
          
          {/* Test Case vs Size Tab */}
          {activeTab === 'testCase' && (
            <div>
              <div className="mb-6">
                <div className="flex flex-col">
                  <label className="mb-1 font-medium">Select Test Case:</label>
                  <select 
                    className="p-2 border rounded w-full md:w-96"
                    value={selectedTestCase}
                    onChange={(e) => setSelectedTestCase(e.target.value)}
                  >
                    {models[0]?.testCases.map((testCase, idx) => (
                      <option key={idx} value={testCase.name}>{testCase.name}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div className="border p-4 rounded shadow-sm mt-8">
                <div className="font-semibold mb-4 text-center">
                  {`Test Case "${selectedTestCase}" ASR vs Model Parameter Size`}
                </div>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart
                    margin={{ top: 20, right: 30, left: 20, bottom: 10 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      type="number" 
                      dataKey="paramSize" 
                      name="Model Size" 
                      label={{ value: 'Model Size (Billion Parameters)', position: 'bottom', offset: 0 }}
                      scale="log"
                      domain={[1, 100]}
                      ticks={[1, 8, 70]}
                      allowDataOverflow={true}
                    />
                    <YAxis 
                      type="number"
                      name="ASR" 
                      label={{ value: 'ASR (%)', angle: -90, position: 'insideLeft' }}
                      domain={[0, 100]}
                    />
                    <Tooltip />
                    <Legend verticalAlign="top" height={36} />
                    
                    {/* Multi ASR Line */}
                    <Line
                      name="Multi-Turn ASR"
                      data={testCaseSizeData}
                      dataKey="multi"
                      stroke="#8884d8"
                      dot={{ r: 6 }}
                      activeDot={{ r: 8 }}
                    >
                      <ErrorBar dataKey="multiSE" width={4} strokeWidth={2} stroke="#8884d8" />
                    </Line>
                    
                    {/* Single ASR Line */}
                    <Line
                      name="Single-Turn ASR"
                      data={testCaseSizeData}
                      dataKey="single"
                      stroke="#82ca9d"
                      dot={{ r: 6 }}
                      activeDot={{ r: 8 }}
                    >
                      <ErrorBar dataKey="singleSE" width={4} strokeWidth={2} stroke="#82ca9d" />
                    </Line>
                    
                    {/* Multi Max ASR Line */}
                    <Line
                      name="Multi-Turn Max ASR"
                      data={testCaseSizeData}
                      dataKey="multiMax"
                      stroke="#ff7300"
                      strokeDasharray="5 5"
                      dot={{ r: 6 }}
                      activeDot={{ r: 8 }}
                    />
                    
                    {/* Single Max ASR Line */}
                    <Line
                      name="Single-Turn Max ASR"
                      data={testCaseSizeData}
                      dataKey="singleMax"
                      stroke="#ff00ff"
                      strokeDasharray="5 5"
                      dot={{ r: 6 }}
                      activeDot={{ r: 8 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              
              <div className="mt-4 text-sm text-gray-600">
                <p><strong>Note:</strong> This chart shows the relationship between model parameter size and ASR for the selected test case.</p>
                <p><strong>Multi/Single ASR:</strong> The average ASR across all tests for this test case.</p>
                <p><strong>Multi/Single Max ASR:</strong> The maximum ASR across tactics that have both multi and single turn implementations.</p>
                <p><strong>Error bars:</strong> Standard error across different tactics.</p>
                <p><strong>Log Scale:</strong> X-axis uses a logarithmic scale to better visualize the range of model sizes.</p>
              </div>
            </div>
          )}
          
          {/* Tactic vs Size Tab */}
          {activeTab === 'tactic' && (
            <div>
              <div className="mb-6">
                <div className="flex flex-col">
                  <label className="mb-1 font-medium">Select Tactic:</label>
                  <select 
                    className="p-2 border rounded w-full md:w-96"
                    value={selectedTactic}
                    onChange={(e) => setSelectedTactic(e.target.value)}
                  >
                    {commonTactics.map((tactic, idx) => (
                      <option key={idx} value={tactic}>{tactic}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div className="border p-4 rounded shadow-sm mt-8">
                <div className="font-semibold mb-4 text-center">
                  {`Tactic "${selectedTactic}" ASR vs Model Parameter Size`}
                </div>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart
                    margin={{ top: 20, right: 30, left: 20, bottom: 10 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      type="number" 
                      dataKey="paramSize" 
                      name="Model Size" 
                      label={{ value: 'Model Size (Billion Parameters)', position: 'bottom', offset: 0 }}
                      scale="log"
                      domain={[1, 100]}
                      ticks={[1, 8, 70]}
                      allowDataOverflow={true}
                    />
                    <YAxis 
                      type="number"
                      name="ASR" 
                      label={{ value: 'ASR (%)', angle: -90, position: 'insideLeft' }}
                      domain={[0, 100]}
                    />
                    <Tooltip />
                    <Legend verticalAlign="top" height={36} />
                    
                    {/* Multi ASR Line */}
                    <Line
                      name="Multi-Turn ASR"
                      data={tacticSizeData}
                      dataKey="multi"
                      stroke="#8884d8"
                      dot={{ r: 6 }}
                      activeDot={{ r: 8 }}
                    >
                      <ErrorBar dataKey="multiSE" width={4} strokeWidth={2} stroke="#8884d8" />
                    </Line>
                    
                    {/* Single ASR Line */}
                    <Line
                      name="Single-Turn ASR"
                      data={tacticSizeData}
                      dataKey="single"
                      stroke="#82ca9d"
                      dot={{ r: 6 }}
                      activeDot={{ r: 8 }}
                    >
                      <ErrorBar dataKey="singleSE" width={4} strokeWidth={2} stroke="#82ca9d" />
                    </Line>
                  </LineChart>
                </ResponsiveContainer>
              </div>
              
              <div className="mt-4 text-sm text-gray-600">
                <p><strong>Note:</strong> This chart shows the relationship between model parameter size and ASR for the selected tactic.</p>
                <p><strong>Multi-Turn ASR:</strong> The ASR for multi-turn conversations using this tactic.</p>
                <p><strong>Single-Turn ASR:</strong> The ASR for single-turn conversations using this tactic.</p>
                <p><strong>Error bars:</strong> Standard error across different test cases.</p>
                <p><strong>Log Scale:</strong> X-axis uses a logarithmic scale to better visualize the range of model sizes.</p>
              </div>
            </div>
          )}
          
          {/* Heatmaps Tab */}
          {activeTab === 'heatmap' && model && (
            <div>
              <div className="mb-6">
                <div className="flex flex-col">
                  <label className="mb-1 font-medium">Select Model:</label>
                  <select 
                    className="p-2 border rounded w-full md:w-96"
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(parseInt(e.target.value))}
                  >
                    {models.map((model, idx) => (
                      <option key={idx} value={idx}>{model.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* ASR Heatmaps */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-6">
                <div className="border p-4 rounded shadow-sm">
                  <h2 className="text-xl font-semibold mb-2 text-center">Multi-Turn ASR Heatmap</h2>
                  <HeatMap 
                    data={model.heatmaps.multi} 
                    testCases={model.testCases.map(tc => tc.name)}
                    tactics={model.tactics.multi.map(t => t.name)}
                    title="Success Rate (%) by Tactic and Test Case - Multi-Turn"
                    isMulti={true}
                  />
                  <ColorScale />
                </div>
                
                <div className="border p-4 rounded shadow-sm">
                  <h2 className="text-xl font-semibold mb-2 text-center">Single-Turn ASR Heatmap</h2>
                  <HeatMap 
                    data={model.heatmaps.single} 
                    testCases={model.testCases.map(tc => tc.name)}
                    tactics={model.tactics.single.map(t => t.name)}
                    title="Success Rate (%) by Tactic and Test Case - Single-Turn"
                    isMulti={false}
                  />
                  <ColorScale />
                </div>
              </div>
              
              {/* Refusal Count Heatmaps */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-6">
                <div className="border p-4 rounded shadow-sm">
                  <h2 className="text-xl font-semibold mb-2 text-center">Multi-Turn Refusal Count Heatmap</h2>
                  <CountHeatMap 
                    data={model.refusalCounts.multi} 
                    testCases={model.testCases.map(tc => tc.name)}
                    tactics={model.tactics.multi.map(t => t.name)}
                    title="Refusal Count by Tactic and Test Case - Multi-Turn"
                    colorRamp="refusal"
                  />
                  <div className="flex justify-center mt-4">
                    <div className="flex items-center">
                      <div style={{ backgroundColor: '#4575b4', width: '20px', height: '20px' }}></div>
                      <span className="ml-2 mr-4 text-xs">Low Refusals</span>
                      <div style={{ backgroundColor: '#d73027', width: '20px', height: '20px' }}></div>
                      <span className="ml-2 text-xs">High Refusals</span>
                    </div>
                  </div>
                </div>
                
                <div className="border p-4 rounded shadow-sm">
                  <h2 className="text-xl font-semibold mb-2 text-center">Single-Turn Refusal Count Heatmap</h2>
                  <CountHeatMap 
                    data={model.refusalCounts.single} 
                    testCases={model.testCases.map(tc => tc.name)}
                    tactics={model.tactics.single.map(t => t.name)}
                    title="Refusal Count by Tactic and Test Case - Single-Turn"
                    colorRamp="refusal"
                  />
                  <div className="flex justify-center mt-4">
                    <div className="flex items-center">
                      <div style={{ backgroundColor: '#4575b4', width: '20px', height: '20px' }}></div>
                      <span className="ml-2 mr-4 text-xs">Low Refusals</span>
                      <div style={{ backgroundColor: '#d73027', width: '20px', height: '20px' }}></div>
                      <span className="ml-2 text-xs">High Refusals</span>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Round Count Heatmaps */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-6">
                <div className="border p-4 rounded shadow-sm">
                  <h2 className="text-xl font-semibold mb-2 text-center">Multi-Turn Round Count Heatmap</h2>
                  <CountHeatMap 
                    data={model.roundCounts.multi} 
                    testCases={model.testCases.map(tc => tc.name)}
                    tactics={model.tactics.multi.map(t => t.name)}
                    title="Number of Rounds by Tactic and Test Case - Multi-Turn"
                    colorRamp="rounds"
                  />
                  <div className="flex justify-center mt-4">
                    <div className="flex items-center">
                      <div style={{ backgroundColor: '#4575b4', width: '20px', height: '20px' }}></div>
                      <span className="ml-2 mr-4 text-xs">Fewer Rounds</span>
                      <div style={{ backgroundColor: '#d73027', width: '20px', height: '20px' }}></div>
                      <span className="ml-2 text-xs">More Rounds</span>
                    </div>
                  </div>
                </div>
                
                <div className="border p-4 rounded shadow-sm">
                  <h2 className="text-xl font-semibold mb-2 text-center">Single-Turn Round Count Heatmap</h2>
                  <CountHeatMap 
                    data={model.roundCounts.single} 
                    testCases={model.testCases.map(tc => tc.name)}
                    tactics={model.tactics.single.map(t => t.name)}
                    title="Number of Rounds by Tactic and Test Case - Single-Turn"
                    colorRamp="rounds"
                  />
                  <div className="flex justify-center mt-4">
                    <div className="flex items-center">
                      <div style={{ backgroundColor: '#4575b4', width: '20px', height: '20px' }}></div>
                      <span className="ml-2 mr-4 text-xs">Fewer Rounds</span>
                      <div style={{ backgroundColor: '#d73027', width: '20px', height: '20px' }}></div>
                      <span className="ml-2 text-xs">More Rounds</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div className="mt-8 text-sm text-gray-600">
            <p><strong>ASR:</strong> Attack Success Rate - percentage of successful jailbreak attempts where at least one score is equal to 1.0 (indicating a successful attack)</p>
            <p><strong>Test Cases:</strong> Various harmful scenarios that models should reject</p>
            <p><strong>Jailbreak Tactics:</strong> Different techniques used to try to bypass model safeguards</p>
            <p><strong>Data Source:</strong> Values extracted from CSV file data using max score = 1.0 as the success criterion</p>
          </div>
        </>
      )}
    </div>
  );
};

// ColorScale component for the heatmap
const ColorScale = () => {
  const colors = ['#f7fbff', '#ffedbc', '#ffbf6d', '#fd8e3c', '#e44c3a', '#9e2043', '#7a0e45'];
  const values = ['0', '20', '40', '60', '80', '100'];
  
  return (
    <div className="flex flex-col items-end mt-4">
      <div className="text-sm font-semibold mb-1">Success Rate (%)</div>
      <div className="flex items-center">
        {colors.map((color, i) => (
          <div key={i} className="flex flex-col items-center">
            <div style={{ backgroundColor: color, width: '20px', height: '20px' }}></div>
            {i < values.length && <div className="text-xs mt-1">{values[i]}</div>}
          </div>
        ))}
      </div>
    </div>
  );
};

// HeatMap component
const HeatMap = ({ data, testCases, tactics, title }) => {
  // Limit display to a reasonable number to prevent overcrowding
  const maxDisplayItems = 20;
  const displayTestCases = testCases.slice(0, maxDisplayItems);
  const displayTactics = tactics.slice(0, maxDisplayItems);
  const displayData = data.slice(0, maxDisplayItems).map(row => row.slice(0, maxDisplayItems));
  
  return (
    <div className="mt-4">
      <div className="font-semibold mb-2 text-center">{title}</div>
      <div className="overflow-x-auto">
        <div style={{ 
          display: 'grid',
          gridTemplateColumns: `minmax(150px, auto) repeat(${displayTactics.length}, minmax(60px, 1fr))`,
          gap: '1px',
          backgroundColor: '#e5e7eb'
        }}>
          {/* Header row */}
          <div className="bg-gray-100 p-2 font-semibold text-sm">Test Case</div>
          {displayTactics.map((tactic, i) => (
            <div 
              key={i} 
              className="bg-gray-100 p-2 font-semibold text-sm"
              style={{
                writingMode: 'vertical-rl',
                textOrientation: 'mixed',
                transform: 'rotate(180deg)',
                height: '120px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              {typeof tactic === 'object' ? tactic.name : tactic}
            </div>
          ))}
          
          {/* Data rows */}
          {displayTestCases.map((testCase, rowIndex) => (
            <React.Fragment key={rowIndex}>
              <div className="bg-white p-2 text-sm border-t border-gray-200">
                {typeof testCase === 'object' ? testCase.name : testCase}
              </div>
              {displayData[rowIndex]?.map((value, colIndex) => {
                // Color scale from light yellow to dark red
                let color = '#f7fbff'; // white/very light blue for 0
                if (value > 0) {
                  if (value <= 20) color = '#ffedbc';
                  else if (value <= 40) color = '#ffbf6d';
                  else if (value <= 60) color = '#fd8e3c';
                  else if (value <= 80) color = '#e44c3a';
                  else if (value <= 90) color = '#9e2043';
                  else color = '#7a0e45'; // very dark red for 100
                }
                
                return (
                  <div 
                    key={colIndex}
                    className="bg-white p-2 text-sm text-center border-t border-gray-200"
                    style={{ backgroundColor: color }}
                  >
                    {value > 0 ? value : ''}
                  </div>
                );
              })}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
};

// HeatMap component for refusal counts and round counts
const CountHeatMap = ({ data, testCases, tactics, title, colorRamp }) => {
  // Limit display to a reasonable number to prevent overcrowding
  const maxDisplayItems = 20;
  const displayTestCases = testCases.slice(0, maxDisplayItems);
  const displayTactics = tactics.slice(0, maxDisplayItems);
  const displayData = data.slice(0, maxDisplayItems).map(row => row.slice(0, maxDisplayItems));
  
  // Choose color ramp based on data type
  const getColor = (value) => {
    if (value === 0) return '#f7fbff'; // white/very light blue for 0
    
    if (colorRamp === 'refusal') {
      // Refusal count: red (more refusals) to blue (less refusals)
      if (value <= 1) return '#4575b4'; // dark blue (fewer refusals)
      else if (value <= 2) return '#74add1';
      else if (value <= 3) return '#abd9e9';
      else if (value <= 4) return '#fdae61';
      else return '#d73027'; // dark red (more refusals)
    } else {
      // Round count: blue (fewer rounds) to red (more rounds)
      if (value === 1) return '#4575b4'; // dark blue (single turn)
      else if (value <= 3) return '#74add1';
      else if (value <= 5) return '#abd9e9';
      else if (value <= 7) return '#fdae61';
      else return '#d73027'; // dark red (more rounds)
    }
  };
  
  return (
    <div className="mt-4">
      <div className="font-semibold mb-2 text-center">{title}</div>
      <div className="overflow-x-auto">
        <div style={{ 
          display: 'grid',
          gridTemplateColumns: `minmax(150px, auto) repeat(${displayTactics.length}, minmax(60px, 1fr))`,
          gap: '1px',
          backgroundColor: '#e5e7eb'
        }}>
          {/* Header row */}
          <div className="bg-gray-100 p-2 font-semibold text-sm">Test Case</div>
          {displayTactics.map((tactic, i) => (
            <div 
              key={i} 
              className="bg-gray-100 p-2 font-semibold text-sm"
              style={{
                writingMode: 'vertical-rl',
                textOrientation: 'mixed',
                transform: 'rotate(180deg)',
                height: '120px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              {typeof tactic === 'object' ? tactic.name : tactic}
            </div>
          ))}
          
          {/* Data rows */}
          {displayTestCases.map((testCase, rowIndex) => (
            <React.Fragment key={rowIndex}>
              <div className="bg-white p-2 text-sm border-t border-gray-200">
                {typeof testCase === 'object' ? testCase.name : testCase}
              </div>
              {displayData[rowIndex]?.map((value, colIndex) => (
                <div 
                  key={colIndex}
                  className="bg-white p-2 text-sm text-center border-t border-gray-200"
                  style={{ backgroundColor: getColor(value) }}
                >
                  {value}
                </div>
              ))}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
};

export default InteractiveJailbreakViz;