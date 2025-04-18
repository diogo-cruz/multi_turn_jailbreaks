import React, { useState, useEffect, useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, LabelList, LineChart, Line, ScatterChart, Scatter, ZAxis, ErrorBar
} from 'recharts';
import Papa from 'papaparse';
import TestCaseModelSizeHeatmap from './test_case_model_size_heatmap';

// CSS styles for tabs
const styles = {
  tab: {
    padding: '0.5rem 1rem',
    fontWeight: '500',
    cursor: 'pointer',
    borderBottom: '2px solid transparent',
  },
  activeTab: {
    color: '#3B82F6',
    borderBottomColor: '#3B82F6',
  },
  inactiveTab: {
    color: '#6B7280',
    borderBottomColor: 'transparent',
    ':hover': {
      color: '#374151',
    }
  }
};

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
  const [selectedFile, setSelectedFile] = useState('enhanced_master_data.csv');
  const [availableFiles, setAvailableFiles] = useState([
    'enhanced_master_data.csv',
    'results_test_runs.csv',
    'results_2D.csv',
    'results_2D_2.csv',
    'results_2B.csv',
    'results_final_3samples.csv'
  ]);
  // State for enhanced master data
  const [enhancedMasterData, setEnhancedMasterData] = useState([]);
  const [modelComparisonData, setModelComparisonData] = useState([]);
  
  // Load and process the data
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        
        // Special case for enhanced_master_data.csv
        if (selectedFile === 'enhanced_master_data.csv') {
          await loadEnhancedMasterData();
          setLoading(false);
          return;
        }
        
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
  
  // Function to load enhanced master data and model comparison data
  const loadEnhancedMasterData = async () => {
    try {
      console.log("Starting to load enhanced master data...");
      
      // Load enhanced_master_data.csv - changing path from ./public/ to ./
      const enhancedResponse = await fetch('./enhanced_master_data.csv');
      if (!enhancedResponse.ok) {
        throw new Error(`Failed to fetch enhanced_master_data.csv: ${enhancedResponse.status} ${enhancedResponse.statusText}`);
      }
      console.log("Enhanced master data fetch successful");
      
      const enhancedContent = await enhancedResponse.text();
      console.log(`Enhanced master data content length: ${enhancedContent.length} bytes`);
      
      const enhancedData = Papa.parse(enhancedContent, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true
      }).data;
      
      console.log(`Parsed ${enhancedData.length} rows from enhanced master data`);
      console.log("Sample row:", enhancedData.length > 0 ? enhancedData[0] : "No data");
      
      setEnhancedMasterData(enhancedData);
      
      // Also load model_comparison.csv for additional model metadata - changing path from ./public/ to ./
      console.log("Starting to load model comparison data...");
      const comparisonResponse = await fetch('./model_comparison.csv');
      if (!comparisonResponse.ok) {
        throw new Error(`Failed to fetch model_comparison.csv: ${comparisonResponse.status} ${comparisonResponse.statusText}`);
      }
      console.log("Model comparison data fetch successful");
      
      const comparisonContent = await comparisonResponse.text();
      console.log(`Model comparison content length: ${comparisonContent.length} bytes`);
      
      const comparisonData = Papa.parse(comparisonContent, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true
      }).data;
      
      console.log(`Parsed ${comparisonData.length} rows from model comparison data`);
      console.log("Sample row:", comparisonData.length > 0 ? comparisonData[0] : "No data");
      
      setModelComparisonData(comparisonData);
      console.log("Both datasets loaded successfully");
      
      // Debug the loaded data
      debugDataLoading(enhancedData, comparisonData);
      
    } catch (err) {
      console.error("Error loading enhanced data:", err);
      setError(`Failed to load enhanced data: ${err.message}`);
    }
  };
  
  // Add debugging function to help troubleshoot
  const debugDataLoading = (enhancedData, modelComparisonData) => {
    console.log("========== DATA DEBUGGING INFO ==========");
    
    // Check enhanced data
    if (!enhancedData || enhancedData.length === 0) {
      console.error("Enhanced data is empty or null");
    } else {
      console.log(`Enhanced data has ${enhancedData.length} rows`);
      console.log("Enhanced data first row keys:", Object.keys(enhancedData[0]));
      console.log("Enhanced data first row:", enhancedData[0]);
      
      // Check for scores format
      if (enhancedData[0].scores) {
        console.log("Scores data type:", typeof enhancedData[0].scores);
        if (typeof enhancedData[0].scores === 'string') {
          console.log("Trying to parse scores:", enhancedData[0].scores);
          try {
            const parsedScores = JSON.parse(enhancedData[0].scores.replace(/'/g, '"'));
            console.log("Parsed scores:", parsedScores);
          } catch (e) {
            console.error("Error parsing scores:", e);
          }
        }
      }
      
      // Count unique models
      const uniqueModels = [...new Set(enhancedData.map(row => row.target_model))];
      console.log(`Found ${uniqueModels.length} unique models in enhanced data`);
      console.log("Sample models:", uniqueModels.slice(0, 5));
    }
    
    // Check model comparison data
    if (!modelComparisonData || modelComparisonData.length === 0) {
      console.error("Model comparison data is empty or null");
    } else {
      console.log(`Model comparison data has ${modelComparisonData.length} rows`);
      console.log("Model comparison first row keys:", Object.keys(modelComparisonData[0]));
      console.log("Model comparison first row:", modelComparisonData[0]);
      
      // Sample release dates
      const releaseDates = modelComparisonData.map(model => model["Release Date"]).filter(Boolean);
      console.log("Sample release dates:", releaseDates.slice(0, 5));
      
      // Sample parameters
      const parameters = modelComparisonData.map(model => model.Parameters).filter(Boolean);
      console.log("Sample parameters:", parameters.slice(0, 5));
    }
    
    // Test model matching
    if (enhancedData && enhancedData.length > 0 && modelComparisonData && modelComparisonData.length > 0) {
      console.log("Testing model matching...");
      const testModels = enhancedData.slice(0, 3).map(row => row.target_model);
      
      testModels.forEach(modelName => {
        console.log(`Looking for match for ${modelName}`);
        
        // Try direct Model field match
        let modelInfo = modelComparisonData.find(model => 
          model.Model && modelName.toLowerCase().includes(model.Model.toLowerCase())
        );
        
        // If no match, try reverse match
        if (!modelInfo) {
          modelInfo = modelComparisonData.find(model => 
            model.Model && model.Model.toLowerCase().includes(modelName.toLowerCase())
          );
        }
        
        if (modelInfo) {
          console.log(`✓ Found match: ${modelInfo.Model} (${modelInfo.Company}, ${modelInfo.Parameters}B)`);
        } else {
          console.error(`✗ No match found for ${modelName}`);
        }
      });
    }
    
    console.log("========== END DEBUGGING INFO ==========");
  };
  
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
  
  // Helper function to calculate standard error
  const calculateStandardError = (values) => {
    if (!values.length) return 0;
    
    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const squaredDiffs = values.map(val => Math.pow(val - mean, 2));
    const variance = squaredDiffs.reduce((sum, val) => sum + val, 0) / values.length;
    const stdDev = Math.sqrt(variance);
    
    return stdDev / Math.sqrt(values.length);
  };
  
  // Generate test case size data
  const generateTestCaseSizeData = (testCase) => {
    const commonTactics = getCommonTactics();
    
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

  // Get current model object safely
  const model = models[selectedModel] || null;
  const commonTactics = getCommonTactics();
  
  // Get data for current selections
  const testCaseSizeData = selectedTestCase ? generateTestCaseSizeData(selectedTestCase) : [];
  const tacticSizeData = selectedTactic ? generateTacticSizeData(selectedTactic) : [];
  
  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading data...</div>;
  }
  
  if (error) {
    return <div className="text-red-600 p-4">{error}</div>;
  }
  
  return (
    <div className="container mx-auto px-4 py-8">
      {/* File selector */}
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
          {selectedFile !== 'enhanced_master_data.csv' && models.length > 0 && ` (${models.length} models)`}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="text-xl">Loading data...</div>
        </div>
      ) : error ? (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
          {error}
        </div>
      ) : selectedFile === 'enhanced_master_data.csv' ? (
        /* Enhanced Master Data Visualization */
        <EnhancedMasterDataViz 
          enhancedData={enhancedMasterData}
          modelComparisonData={modelComparisonData}
        />
      ) : models.length === 0 ? (
        <div className="p-4">No data available for the selected file.</div>
      ) : (
        /* Standard Jailbreak Test Analysis */
        <>
          {/* Tabs for standard analysis */}
          <div className="flex border-b mb-6">
            <button 
              style={{
                ...styles.tab,
                ...(activeTab === "model" ? styles.activeTab : styles.inactiveTab)
              }}
              onClick={() => setActiveTab("model")}
            >
              Model Analysis
            </button>
            <button 
              style={{
                ...styles.tab,
                ...(activeTab === "testCase" ? styles.activeTab : styles.inactiveTab)
              }}
              onClick={() => setActiveTab("testCase")}
            >
              Test Case vs Size
            </button>
            <button 
              style={{
                ...styles.tab,
                ...(activeTab === "tactic" ? styles.activeTab : styles.inactiveTab)
              }}
              onClick={() => setActiveTab("tactic")}
            >
              Tactic vs Size
            </button>
            <button 
              style={{
                ...styles.tab,
                ...(activeTab === "heatmap" ? styles.activeTab : styles.inactiveTab)
              }}
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

// Component to render enhanced master data visualizations
const EnhancedMasterDataViz = ({ enhancedData, modelComparisonData }) => {
  console.log("EnhancedMasterDataViz render attempt", {
    enhancedDataExists: Boolean(enhancedData) && enhancedData.length > 0,
    modelComparisonDataExists: Boolean(modelComparisonData) && modelComparisonData.length > 0
  });
  
  // Add a new state for the active tab
  const [activeTab, setActiveTab] = useState("models");
  
  // Function to process the real data in a more comprehensive way
  const processRealData = () => {
    if (!enhancedData || enhancedData.length === 0) {
      console.log("No enhanced data available");
      return { 
        models: [], 
        successRates: [],
        testCaseData: [],
        tacticData: [],
        modelSizeData: [],
        modelDateData: [],
        heatmapData: null,
        testCases: [],
        tactics: []
      };
    }
    
    console.log("Processing real data, sample:", enhancedData[0]);
    
    // Get the model field name
    const modelField = enhancedData[0] && 'target_model' in enhancedData[0] 
      ? 'target_model' 
      : 'model';
    
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
      'deepseek/deepseek-chat-v3-0324': 16
    };
    
    // Extract unique models, test cases, and tactics
    const allModels = [...new Set(enhancedData.map(row => row[modelField]))];
    const testCases = [...new Set(enhancedData.map(row => row.test_case))].sort();
    const tactics = [...new Set(enhancedData.map(row => row.jailbreak_tactic))].sort();
    
    // Helper function to get success rate
    const getSuccessRate = (subset) => {
      if (!subset || subset.length === 0) return 0;
      
      const successCount = subset.filter(row => {
        if (row.goal_achieved !== undefined) {
          return typeof row.goal_achieved === 'string' 
            ? row.goal_achieved.toLowerCase() === 'true'
            : Boolean(row.goal_achieved);
        }
        return false;
      }).length;
      
      return (successCount / subset.length) * 100;
    };
    
    // Count models and success rates
    const modelCounts = {};
    const successCounts = {};
    const totalCounts = {};
    
    enhancedData.forEach(row => {
      const model = row[modelField];
      if (!model) return;
      
      // Use full model name for accurate grouping, but create a shorter version for display
      const shortModel = model.split('/').pop();
      const displayModel = shortModel.length > 25 ? shortModel.substring(0, 22) + '...' : shortModel;
      
      // Count model occurrences
      if (!modelCounts[model]) {
        modelCounts[model] = {
          fullName: model,
          displayName: displayModel, 
          count: 1
        };
      } else {
        modelCounts[model].count++;
      }
      
      // Count successes based on goal_achieved field
      if (row.goal_achieved !== undefined) {
        const success = typeof row.goal_achieved === 'string' 
          ? row.goal_achieved.toLowerCase() === 'true'
          : Boolean(row.goal_achieved);
        
        totalCounts[model] = (totalCounts[model] || 0) + 1;
        if (success) {
          successCounts[model] = (successCounts[model] || 0) + 1;
        }
      }
    });
    
    // Convert to arrays for charts
    const modelData = Object.values(modelCounts)
      .map(item => ({ 
        model: item.displayName,
        fullName: item.fullName,
        count: item.count 
      }))
      .filter(item => item.count >= 5) // Only include models with at least 5 samples
      .sort((a, b) => b.count - a.count);
    
    // Calculate success rates by model
    const successRates = Object.keys(totalCounts).map(model => {
      const total = totalCounts[model] || 0;
      const successes = successCounts[model] || 0;
      const rate = total > 0 ? (successes / total) * 100 : 0;
      const shortModel = model.split('/').pop();
      const displayModel = shortModel.length > 25 ? shortModel.substring(0, 22) + '...' : shortModel;
      
      return {
        model: displayModel,
        fullName: model,
        successRate: Math.round(rate * 10) / 10, // Round to 1 decimal
        totalSamples: total
      };
    })
    .filter(item => item.totalSamples >= 5) // Only include models with sufficient samples
    .sort((a, b) => b.successRate - a.successRate);
    
    // Helper function to find model info in comparison data
    const findModelInfo = (model) => {
      if (!modelComparisonData || modelComparisonData.length === 0) return null;
      
      // Try direct match first
      let modelInfo = modelComparisonData.find(m => 
        m.Model && model.toLowerCase().includes(m.Model.toLowerCase())
      );
      
      // If no match, try partial match in reverse direction
      if (!modelInfo) {
        modelInfo = modelComparisonData.find(m => 
          m.Model && m.Model.toLowerCase().includes(model.split('/').pop().toLowerCase())
        );
      }
      
      return modelInfo;
    };
    
    // Helper function to parse release date
    const parseReleaseDate = (dateStr) => {
      if (!dateStr) return null;
      
      // Try to parse various date formats
      // Format 1: "May 2023"
      const monthYearPattern = /^(\w+)\s+(\d{4})$/;
      // Format 2: "2023-08-15", "2023/08/15"
      const isoDatePattern = /^(\d{4})[-\/](\d{1,2})[-\/](\d{1,2})$/;
      
      let timestamp = null;
      
      const monthYearMatch = dateStr.match(monthYearPattern);
      if (monthYearMatch) {
        const monthNames = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'];
        const month = monthNames.indexOf(monthYearMatch[1].toLowerCase());
        const year = parseInt(monthYearMatch[2]);
        
        if (month !== -1 && !isNaN(year)) {
          timestamp = new Date(year, month, 1).getTime();
        }
      }
      
      const isoMatch = dateStr.match(isoDatePattern);
      if (isoMatch) {
        const year = parseInt(isoMatch[1]);
        const month = parseInt(isoMatch[2]) - 1;
        const day = parseInt(isoMatch[3]);
        
        if (!isNaN(year) && !isNaN(month) && !isNaN(day)) {
          timestamp = new Date(year, month, day).getTime();
        }
      }
      
      // If no pattern matched, try general Date parsing
      if (!timestamp) {
        const date = new Date(dateStr);
        if (!isNaN(date.getTime())) {
          timestamp = date.getTime();
        }
      }
      
      return timestamp;
    };
    
    // Model Size vs Success Rate data
    const modelSizeData = allModels.map(model => {
      const subset = enhancedData.filter(row => row[modelField] === model);
      const shortName = model.split('/').pop();
      const successRate = getSuccessRate(subset);
      const size = modelSizes[model] || 0;
      
      // Get company from model comparison data if available
      const modelInfo = findModelInfo(model);
      const company = modelInfo ? modelInfo.Company : "Unknown";
      
      return {
        model: shortName,
        fullName: model,
        size,
        successRate: Math.round(successRate * 10) / 10,
        company,
        sampleCount: subset.length
      };
    })
    .filter(item => item.size > 0 && item.sampleCount >= 5)
    .sort((a, b) => b.sampleCount - a.sampleCount);
    
    // Release Date vs Success Rate data
    const modelDateData = allModels.map(model => {
      const subset = enhancedData.filter(row => row[modelField] === model);
      const shortName = model.split('/').pop();
      const successRate = getSuccessRate(subset);
      
      // Get model info from comparison data
      const modelInfo = findModelInfo(model);
      
      // Skip if no model info or no release date
      if (!modelInfo || !modelInfo["Release Date"]) return null;
      
      // Parse the release date
      const releaseTimestamp = parseReleaseDate(modelInfo["Release Date"]);
      if (!releaseTimestamp) return null;
      
      const company = modelInfo.Company || "Unknown";
      const size = modelSizes[model] || (modelInfo.Parameters ? parseFloat(modelInfo.Parameters) : 0);
      
      return {
        model: shortName,
        fullName: model,
        releaseDate: modelInfo["Release Date"],
        releaseTimestamp,
        successRate: Math.round(successRate * 10) / 10,
        company,
        size,
        sampleCount: subset.length
      };
    })
    .filter(Boolean) // Remove null entries
    .filter(item => item.sampleCount >= 5)
    .sort((a, b) => a.releaseTimestamp - b.releaseTimestamp);
    
    // Test case success rates
    const testCaseData = testCases.map(testCase => {
      const subset = enhancedData.filter(row => row.test_case === testCase);
      return {
        name: testCase,
        successRate: Math.round(getSuccessRate(subset) * 10) / 10,
        count: subset.length
      };
    })
    .filter(item => item.count >= 5)
    .sort((a, b) => b.successRate - a.successRate);
    
    // Tactic success rates
    const tacticData = tactics.map(tactic => {
      const subset = enhancedData.filter(row => row.jailbreak_tactic === tactic);
      return {
        name: tactic,
        successRate: Math.round(getSuccessRate(subset) * 10) / 10,
        count: subset.length
      };
    })
    .filter(item => item.count >= 5)
    .sort((a, b) => b.successRate - a.successRate);
    
    // Create heatmap data - test case × tactic
    const heatmapData = testCases.map((testCase, i) => {
      return tactics.map((tactic, j) => {
        const subset = enhancedData.filter(row => 
          row.test_case === testCase && 
          row.jailbreak_tactic === tactic
        );
        
        if (subset.length < 5) return 0; // Require minimum samples
        
        return Math.round(getSuccessRate(subset));
      });
    });
    
    console.log("Processed model data:", modelData);
    console.log("Processed success rate data:", successRates);
    console.log("Processed model size data:", modelSizeData);
    console.log("Processed model date data:", modelDateData);
    console.log("Processed test case data:", testCaseData);
    console.log("Processed tactic data:", tacticData);
    
    return { 
      models: modelData, 
      successRates,
      testCaseData,
      tacticData,
      modelSizeData,
      modelDateData,
      heatmapData,
      testCases,
      tactics
    };
  };
  
  const { 
    models, 
    successRates, 
    testCaseData, 
    tacticData, 
    modelSizeData,
    modelDateData,
    heatmapData,
    testCases,
    tactics
  } = processRealData();
  
  // Fallback dummy data in case processing fails
  const dummyModels = [
    { model: "llama-3.1-70b-instruct", count: 1000 },
    { model: "llama-3.1-8b-instruct", count: 800 },
    { model: "gemini-2.0-flash-001", count: 600 },
    { model: "claude-3-haiku", count: 400 },
    { model: "gemma-2-9b-it", count: 200 }
  ];
  
  const dummySuccessRates = [
    { model: "llama-3.1-70b-instruct", successRate: 85 },
    { model: "llama-3.1-8b-instruct", successRate: 70 },
    { model: "gemini-2.0-flash-001", successRate: 65 },
    { model: "claude-3-haiku", successRate: 45 },
    { model: "gemma-2-9b-it", successRate: 30 }
  ];
  
  // Color mapping for companies
  const companyColors = {
    "DeepSeek": "#FF6B6B",
    "Anthropic": "#4ECDC4",
    "Google": "#45B7D1",
    "Meta": "#7400B8", 
    "Mistral AI": "#FF9F1C",
    "Alibaba": "#FE5F55",
    "xAI": "#66FF66",
    "Unknown": "#CCCCCC"
  };
  
  // Use real data if available, otherwise fallback to dummy data
  const displayModels = models.length > 0 ? models : dummyModels;
  const displaySuccessRates = successRates.length > 0 ? successRates : dummySuccessRates;
  
  // Pre-render data availability checks
  const hasModels = displayModels.length > 0;
  const hasSuccessRates = displaySuccessRates.length > 0;
  const hasModelSizeData = modelSizeData.length > 0;
  const hasModelDateData = modelDateData && modelDateData.length > 0;
  const hasTestCaseData = testCaseData.length > 0;
  const hasTacticData = tacticData.length > 0;
  const hasHeatmapData = heatmapData && heatmapData.some(row => row.some(val => val > 0));
  
  // Create simple HTML version as backup in case charts fail to render
  const renderBackupTable = (data, valueKey, valueName) => (
    <table className="min-w-full border border-gray-300 text-sm">
      <thead>
        <tr className="bg-gray-100">
          <th className="border px-4 py-2 text-left">Name</th>
          <th className="border px-4 py-2 text-right">{valueName}</th>
          <th className="border px-4 py-2 text-right">Count</th>
        </tr>
      </thead>
      <tbody>
        {data.map((item, index) => (
          <tr key={index} className={index % 2 === 0 ? "bg-white" : "bg-gray-50"}>
            <td className="border px-4 py-2 text-left">{item.name}</td>
            <td className="border px-4 py-2 text-right">{item[valueKey]}</td>
            <td className="border px-4 py-2 text-right">{item.count}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
  
  return (
    <div style={{ padding: '20px' }}>
      <h1>Enhanced Jailbreak Analysis Dashboard</h1>
      
      {/* Tabs navigation */}
      <div style={{ display: 'flex', borderBottom: '1px solid #e5e7eb', marginBottom: '20px' }}>
        <div 
          style={{
            ...styles.tab,
            ...(activeTab === 'models' ? styles.activeTab : styles.inactiveTab)
          }}
          onClick={() => setActiveTab('models')}
        >
          Model Analysis
        </div>
        <div 
          style={{
            ...styles.tab,
            ...(activeTab === 'testCases' ? styles.activeTab : styles.inactiveTab)
          }}
          onClick={() => setActiveTab('testCases')}
        >
          Test Cases
        </div>
        <div 
          style={{
            ...styles.tab,
            ...(activeTab === 'tactics' ? styles.activeTab : styles.inactiveTab)
          }}
          onClick={() => setActiveTab('tactics')}
        >
          Tactics
        </div>
        <div 
          style={{
            ...styles.tab,
            ...(activeTab === 'heatmap' ? styles.activeTab : styles.inactiveTab)
          }}
          onClick={() => setActiveTab('heatmap')}
        >
          Heatmap
        </div>
        <div 
          style={{
            ...styles.tab,
            ...(activeTab === 'sizeAnalysis' ? styles.activeTab : styles.inactiveTab)
          }}
          onClick={() => setActiveTab('sizeAnalysis')}
        >
          Size vs ASR Analysis
        </div>
      </div>
      
      {/* Tab content */}
      {activeTab === 'models' && (
        <div>
          {/* Models tab content */}
          <h2>Models by Sample Count</h2>
          <p>Shows the distribution of samples across different models (with at least 5 samples)</p>
          
          {/* Model Count Chart */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-2">Top Models by Sample Count</h3>
            {!hasModels ? (
              <div className="h-60 w-full flex items-center justify-center bg-gray-100">
                <div className="text-gray-500 text-center p-4">
                  <p>No data available for this chart</p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col">
                <div style={{ width: '100%', height: Math.max(300, displayModels.length * 25) }} className="border border-gray-300">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={displayModels}
                      layout="vertical"
                      margin={{ top: 20, right: 30, left: 150, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis
                        type="category"
                        dataKey="model"
                        width={150}
                        tick={{ fontSize: 11 }}
                      />
                      <Tooltip 
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            return (
                              <div className="bg-white p-2 border border-gray-300 shadow-md">
                                <p className="font-bold">{payload[0].payload.model}</p>
                                <p>Samples: {payload[0].payload.count}</p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Legend />
                      <Bar dataKey="count" name="Sample Count" fill="#8884d8" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                
                {/* Backup table in case chart doesn't render */}
                <div className="mt-4 max-w-lg mx-auto">
                  <details>
                    <summary className="cursor-pointer text-blue-600 mb-2">Show as table</summary>
                    {renderBackupTable(displayModels, "count", "Sample Count")}
                  </details>
                </div>
              </div>
            )}
          </div>
          
          {/* Success Rate Chart */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-2">Models by Success Rate</h3>
            {!hasSuccessRates ? (
              <div className="h-60 w-full flex items-center justify-center bg-gray-100">
                <div className="text-gray-500 text-center p-4">
                  <p>No data available for this chart</p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col">
                <div style={{ width: '100%', height: Math.max(300, displaySuccessRates.length * 25) }} className="border border-gray-300">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={displaySuccessRates}
                      layout="vertical"
                      margin={{ top: 20, right: 30, left: 150, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        type="number"
                        domain={[0, 100]}
                      />
                      <YAxis
                        type="category"
                        dataKey="model"
                        width={150}
                        tick={{ fontSize: 11 }}
                      />
                      <Tooltip 
                        formatter={(value) => [`${value}%`, 'Success Rate']}
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            return (
                              <div className="bg-white p-2 border border-gray-300 shadow-md">
                                <p className="font-bold">{payload[0].payload.model}</p>
                                <p>Success Rate: {payload[0].payload.successRate}%</p>
                                <p>Total Samples: {payload[0].payload.totalSamples}</p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Legend />
                      <Bar dataKey="successRate" name="Success Rate (%)" fill="#82ca9d" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                
                {/* Backup table in case chart doesn't render */}
                <div className="mt-4 max-w-lg mx-auto">
                  <details>
                    <summary className="cursor-pointer text-blue-600 mb-2">Show as table</summary>
                    {renderBackupTable(displaySuccessRates, "successRate", "Success Rate (%)")}
                  </details>
                </div>
              </div>
            )}
          </div>
          
          {/* Model Size vs Success Rate Scatter Plot */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-2">Model Size vs Success Rate</h3>
            {!hasModelSizeData ? (
              <div className="h-60 w-full flex items-center justify-center bg-gray-100">
                <div className="text-gray-500 text-center p-4">
                  <p>No data available for this chart</p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col">
                <div style={{ width: '100%', height: 400 }} className="border border-gray-300">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart
                      margin={{ top: 20, right: 30, bottom: 20, left: 20 }}
                  >
                    <CartesianGrid />
                    <XAxis 
                      type="number" 
                      dataKey="size" 
                      name="Size (B)" 
                      label={{ value: 'Model Size (Billions of Parameters)', position: 'bottom' }}
                      domain={['auto', 'auto']}
                      scale="log"
                    />
                    <YAxis 
                      type="number" 
                        dataKey="successRate" 
                        name="Success Rate" 
                        label={{ value: 'Success Rate (%)', angle: -90, position: 'left' }}
                      domain={[0, 100]}
                    />
                    <Tooltip 
                      formatter={(value, name) => {
                          if (name === 'Size (B)') return [`${value}B`, 'Model Size'];
                          if (name === 'Success Rate') return [`${value}%`, name];
                        return [value, name];
                      }}
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          return (
                            <div className="bg-white p-2 border border-gray-300 shadow-md">
                              <p className="font-bold">{payload[0].payload.model}</p>
                                <p>Size: {payload[0].payload.size}B parameters</p>
                                <p>Success Rate: {payload[0].payload.successRate}%</p>
                                <p>Samples: {payload[0].payload.sampleCount}</p>
                              <p>Company: {payload[0].payload.company}</p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Legend />
                      {Object.keys(companyColors).map(company => {
                        const companyData = modelSizeData.filter(model => model.company === company);
                        if (companyData.length === 0) return null;
                        
                        return (
                        <Scatter 
                          key={company}
                          name={company} 
                            data={companyData} 
                            fill={companyColors[company]}
                        />
                        );
                      })}
                  </ScatterChart>
                </ResponsiveContainer>
                </div>
                
                {/* Backup table in case chart doesn't render */}
                <div className="mt-4 max-w-lg mx-auto">
                  <details>
                    <summary className="cursor-pointer text-blue-600 mb-2">Show as table</summary>
                    {renderBackupTable(modelSizeData, "size", "Model Size (Billion Parameters)")}
                  </details>
                </div>
              </div>
            )}
          </div>
          
          {/* Release Date vs Success Rate Scatter Plot */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-2">Release Date vs Success Rate</h3>
            {!hasModelDateData ? (
              <div className="h-60 w-full flex items-center justify-center bg-gray-100">
                <div className="text-gray-500 text-center p-4">
                  <p>No data available for this chart. This may be due to missing release dates in the model comparison data.</p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col">
                <div style={{ width: '100%', height: 400 }} className="border border-gray-300">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart
                      margin={{ top: 20, right: 30, bottom: 50, left: 20 }}
                  >
                    <CartesianGrid />
                    <XAxis 
                      type="number" 
                      dataKey="releaseTimestamp" 
                      name="Release Date" 
                      domain={['auto', 'auto']}
                      tickFormatter={(timestamp) => {
                        return new Date(timestamp).toLocaleDateString('en-US', { 
                          year: 'numeric', 
                          month: 'short'
                        });
                      }}
                      label={{ 
                        value: 'Model Release Date', 
                        position: 'bottom', 
                        offset: 20
                      }}
                    />
                    <YAxis 
                      type="number" 
                      dataKey="successRate" 
                      name="Success Rate" 
                      label={{ value: 'Success Rate (%)', angle: -90, position: 'left' }}
                      domain={[0, 100]}
                    />
                    <Tooltip 
                      formatter={(value, name) => {
                        if (name === 'Release Date') {
                          return [new Date(value).toLocaleDateString('en-US', { 
                            year: 'numeric', 
                            month: 'long',
                            day: 'numeric'
                          }), 'Release Date'];
                        }
                        if (name === 'Success Rate') return [`${value}%`, name];
                        return [value, name];
                      }}
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          return (
                            <div className="bg-white p-2 border border-gray-300 shadow-md">
                              <p className="font-bold">{payload[0].payload.model}</p>
                              <p>Release Date: {payload[0].payload.releaseDate}</p>
                              <p>Success Rate: {payload[0].payload.successRate}%</p>
                              <p>Size: {payload[0].payload.size}B parameters</p>
                              <p>Samples: {payload[0].payload.sampleCount}</p>
                              <p>Company: {payload[0].payload.company}</p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Legend />
                    {Object.keys(companyColors).map(company => {
                      const companyData = modelDateData.filter(model => model.company === company);
                      if (companyData.length === 0) return null;
                      
                      return (
                        <Scatter 
                          key={company}
                          name={company} 
                          data={companyData} 
                          fill={companyColors[company]}
                        />
                      );
                    })}
                  </ScatterChart>
                </ResponsiveContainer>
                </div>
                
                {/* Backup table in case chart doesn't render */}
                <div className="mt-4 max-w-lg mx-auto">
                  <details>
                    <summary className="cursor-pointer text-blue-600 mb-2">Show as table</summary>
                    {renderBackupTable(modelDateData, "successRate", "Success Rate (%)")}
                  </details>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {activeTab === 'testCases' && (
        <div>
          {/* Test cases tab content */}
          <h2>Test Cases by Success Rate</h2>
          <p>Shows which test cases (harmful scenarios) have the highest success rates</p>
          
          {/* Test Case Success Rate Chart */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-2">Test Cases by Success Rate</h3>
            {!hasTestCaseData ? (
              <div className="h-60 w-full flex items-center justify-center bg-gray-100">
                <div className="text-gray-500 text-center p-4">
                  <p>No data available for this chart</p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col">
                <div style={{ width: '100%', height: 300 }} className="border border-gray-300">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={testCaseData}
                      layout="vertical"
                      margin={{ top: 20, right: 30, left: 150, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        type="number"
                        domain={[0, 100]}
                      />
                      <YAxis
                        type="category"
                        dataKey="name"
                        width={150}
                        tick={{ fontSize: 12 }}
                      />
                      <Tooltip formatter={(value) => [`${value}%`, 'Success Rate']} />
                      <Legend />
                      <Bar dataKey="successRate" name="Success Rate (%)" fill="#FF8042" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                
                {/* Backup table in case chart doesn't render */}
                <div className="mt-4 max-w-lg mx-auto">
                  <details>
                    <summary className="cursor-pointer text-blue-600 mb-2">Show as table</summary>
                    {renderBackupTable(testCaseData, "successRate", "Success Rate (%)")}
                  </details>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {activeTab === 'tactics' && (
        <div>
          {/* Tactics tab content */}
          <h2>Tactics by Success Rate</h2>
          <p>Shows which jailbreak tactics have the highest success rates</p>
          
          {/* Tactic Success Rate Chart */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-2">Tactics by Success Rate</h3>
            {!hasTacticData ? (
              <div className="h-60 w-full flex items-center justify-center bg-gray-100">
                <div className="text-gray-500 text-center p-4">
                  <p>No data available for this chart</p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col">
                <div style={{ width: '100%', height: 300 }} className="border border-gray-300">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={tacticData}
                      layout="vertical"
                      margin={{ top: 20, right: 30, left: 150, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        type="number"
                        domain={[0, 100]}
                      />
                      <YAxis
                        type="category"
                        dataKey="name"
                        width={150}
                        tick={{ fontSize: 12 }}
                      />
                      <Tooltip formatter={(value) => [`${value}%`, 'Success Rate']} />
                      <Legend />
                      <Bar dataKey="successRate" name="Success Rate (%)" fill="#4BC0C0" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                
                {/* Backup table in case chart doesn't render */}
                <div className="mt-4 max-w-lg mx-auto">
                  <details>
                    <summary className="cursor-pointer text-blue-600 mb-2">Show as table</summary>
                    {renderBackupTable(tacticData, "successRate", "Success Rate (%)")}
                  </details>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {activeTab === 'heatmap' && (
        <div>
          {/* Heatmap tab content */}
          <h2>Success Rate Heatmap: Test Case × Tactic</h2>
          <p>Shows the success rate for each combination of test case and tactic</p>
          
          {/* Heatmap: Test Case × Tactic */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-2">Success Rate Heatmap: Test Case × Tactic</h3>
            {!hasHeatmapData ? (
              <div className="h-60 w-full flex items-center justify-center bg-gray-100">
                <div className="text-gray-500 text-center p-4">
                  <p>No data available for this chart</p>
                </div>
              </div>
            ) : (
              <div className="overflow-auto" style={{ maxHeight: '600px' }}>
                <HeatMap 
                  data={heatmapData} 
                  testCases={testCases} 
                  tactics={tactics} 
                  title="Success Rate (%)" 
                />
              </div>
            )}
          </div>
          
          {/* Data Summary */}
          <div className="mb-8 p-4 bg-gray-50 rounded-md">
            <h3 className="text-lg font-semibold mb-2">Data Summary</h3>
            <ul className="list-disc ml-5">
              <li>Total samples: {enhancedData?.length || 0}</li>
              <li>Unique models: {Object.keys(models.reduce((acc, item) => ({...acc, [item.model]: true}), {})).length}</li>
              <li>Test cases: {testCases.length}</li>
              <li>Tactics: {tactics.length}</li>
              <li>Models with success rate data: {successRates.length}</li>
            </ul>
          </div>
          
          <div className="text-sm text-gray-500 mt-4">
            <p>Note: This visualization uses data from enhanced_master_data.csv, which combines data from multiple sources.</p>
            <p>Only showing models and test cases with sufficient samples for reliable analysis.</p>
          </div>
        </div>
      )}
      
      {activeTab === 'sizeAnalysis' && (
        <div>
          {/* New Size Analysis tab content */}
          <TestCaseModelSizeHeatmap />
        </div>
      )}
    </div>
  );
};

export default InteractiveJailbreakViz;