import React, { useState, useEffect } from 'react';
import Papa from 'papaparse';
import ModelPerformance from './components/ModelPerformance';
import TestCaseAnalysis from './components/TestCaseAnalysis';
import TacticEffectiveness from './components/TacticEffectiveness';
import EvaluatorAnalysis from './components/EvaluatorAnalysis';
import ModelComparisonHeatmap from './components/ModelComparisonHeatmap';
import SizeAnalysis from './components/SizeAnalysis';
import ReleaseAnalysis from './components/ReleaseAnalysis';
import ReasoningAnalysis from './components/ReasoningAnalysis';
import EvaluatorCorrelationAnalysis from './components/EvaluatorCorrelationAnalysis';
import DebugTurnTypeData from './components/debug/DebugTurnTypeData';
import { processJailbreakData, loadMasterResultsData } from './utils/dataProcessing';

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
  }
};

// The main component
const CombinedVisualization = () => {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [enhancedMasterData, setEnhancedMasterData] = useState([]);
  const [modelComparisonData, setModelComparisonData] = useState([]);
  const [activeTab, setActiveTab] = useState("model");
  const [selectedFile, setSelectedFile] = useState('master_results.csv');
  const [availableFiles, setAvailableFiles] = useState([
    'master_results.csv',
    'enhanced_master_data.csv',
    'results_test_runs.csv',
    'batch_4A_results.csv',
    'batch_4B_results.csv',
    'batch_4B_fixed_20250501_results.csv',
    'batch_thinking_results.csv',
    'model_comparison.csv',
    'sample_results.csv',
    'results_final_3samples.csv'
  ]);
  
  // Filter states
  const [selectedModel, setSelectedModel] = useState(null);
  const [selectedTestCase, setSelectedTestCase] = useState(null);
  const [selectedTactic, setSelectedTactic] = useState(null);
  const [selectedEvaluator, setSelectedEvaluator] = useState(null);
  
  // Unique values for filters
  const [uniqueModels, setUniqueModels] = useState([]);
  const [uniqueTestCases, setUniqueTestCases] = useState([]);
  const [uniqueTactics, setUniqueTactics] = useState([]);
  const [uniqueEvaluators, setUniqueEvaluators] = useState([]);
  
  // Load and process data
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        console.log("Starting to load data from:", selectedFile);
        
        // Load model comparison data for size analysis
        let comparisonData = [];
        try {
          const comparisonResponse = await fetch('/data/model_comparison.csv');
          const comparisonContent = await comparisonResponse.text();
          comparisonData = Papa.parse(comparisonContent, {
            header: true,
            dynamicTyping: true,
            skipEmptyLines: true
          }).data;
        } catch (err) {
          console.warn("Could not load model_comparison.csv:", err);
        }
        
        if (selectedFile === 'master_results.csv') {
          // Use dedicated function for master_results.csv
          try {
            console.log("Loading master_results.csv with dedicated function");
            const { processedModels, comparisonData: modelCompData } = await loadMasterResultsData();
            
            console.log("Loaded and processed models:", processedModels.length);
            if (processedModels.length > 0) {
              // Add detailed debugging for the first model's ASR values
              const firstModel = processedModels[0];
              console.log(`Model ${firstModel.name} detailed metrics:`, {
                name: firstModel.name,
                singleTurnASR: firstModel.singleTurnASR,
                multiTurnASR: firstModel.multiTurnASR,
                singleTurnTestCases: firstModel.singleTurnTestCases,
                multiTurnTestCases: firstModel.multiTurnTestCases,
                singleTurnType: typeof firstModel.singleTurnASR,
                multiTurnType: typeof firstModel.multiTurnASR
              });
              
              // Debug test cases and tactics to ensure they're properly calculated
              if (firstModel.testCases && firstModel.testCases.length > 0) {
                console.log(`First model has ${firstModel.testCases.length} test cases`);
              }
              
              if (firstModel.tactics) {
                console.log(`First model has ${firstModel.tactics.single.length} single-turn tactics and ${firstModel.tactics.multi.length} multi-turn tactics`);
              }
            }
            
            setModels(processedModels);
            setModelComparisonData(modelCompData || comparisonData);
            
            // Extract unique values for filters
            if (processedModels.length > 0) {
              setUniqueModels(processedModels.map(model => model.name));
              
              // Collect unique test cases across all models
              const testCases = new Set();
              const tactics = new Set();
              const evaluators = new Set();
              
              processedModels.forEach(model => {
                model.testCases.forEach(tc => testCases.add(tc.name));
                
                // Add tactics from both single and multi
                model.tactics.single.forEach(t => tactics.add(t.name));
                model.tactics.multi.forEach(t => tactics.add(t.name));
                
                // Add evaluators
                model.evaluators.forEach(e => evaluators.add(e.name));
              });
              
              setUniqueTestCases([...testCases]);
              setUniqueTactics([...tactics]);
              setUniqueEvaluators([...evaluators].filter(Boolean));
              
              // Set initial selections
              setSelectedModel(processedModels[0].name);
              if (testCases.size > 0) setSelectedTestCase([...testCases][0]);
              if (tactics.size > 0) setSelectedTactic([...tactics][0]);
              if (evaluators.size > 0) setSelectedEvaluator([...evaluators][0]);
            }
          } catch (err) {
            console.error("Error using dedicated loading function, falling back to generic method:", err);
            
            // Fall back to generic loading method
            const response = await fetch(`/data/${selectedFile}`);
            const fileContent = await response.text();
            
            const parsedData = Papa.parse(fileContent, {
              header: true,
              dynamicTyping: true,
              skipEmptyLines: true
            }).data;
            
            const processedModels = processJailbreakData(parsedData);
            setModels(processedModels);
            setModelComparisonData(comparisonData);
            
            // Extract unique values for filters (same as in the else branch)
            if (parsedData.length > 0) {
              setUniqueModels([...new Set(parsedData.map(d => d.target_model || d.model))]);
              setUniqueTestCases([...new Set(parsedData.map(d => d.test_case))]);
              setUniqueTactics([...new Set(parsedData.map(d => d.jailbreak))]);
              setUniqueEvaluators([...new Set(parsedData.map(d => d.evaluator_model))].filter(Boolean));
              
              // Set initial selections
              setSelectedModel(parsedData[0].target_model || parsedData[0].model);
              setSelectedTestCase(parsedData[0].test_case);
              setSelectedTactic(parsedData[0].jailbreak);
              setSelectedEvaluator(parsedData[0].evaluator_model || null);
            }
          }
        } else if (selectedFile === 'enhanced_master_data.csv') {
          // Load enhanced master data
          const response = await fetch(`/data/${selectedFile}`);
          const fileContent = await response.text();
          
          const enhancedData = Papa.parse(fileContent, {
            header: true,
            dynamicTyping: true,
            skipEmptyLines: true
          }).data;
          
          setEnhancedMasterData(enhancedData);
          setModelComparisonData(comparisonData);
          
          // Extract unique values for filters
          setUniqueModels([...new Set(enhancedData.map(d => d.target_model))]);
          setUniqueTestCases([...new Set(enhancedData.map(d => d.test_case))]);
          setUniqueTactics([...new Set(enhancedData.map(d => d.jailbreak))]);
          setUniqueEvaluators([...new Set(enhancedData.map(d => d.evaluator_model))].filter(Boolean));
          
          // Set initial selections
          if (enhancedData.length > 0) {
            setSelectedModel(enhancedData[0].target_model);
            setSelectedTestCase(enhancedData[0].test_case);
            setSelectedTactic(enhancedData[0].jailbreak);
            setSelectedEvaluator(enhancedData[0].evaluator_model || null);
          }
        } else {
          // Handle other CSV files
          const response = await fetch(`/data/${selectedFile}`);
          const fileContent = await response.text();
          
          const parsedData = Papa.parse(fileContent, {
            header: true,
            dynamicTyping: true,
            skipEmptyLines: true
          }).data;
          
          const processedModels = processJailbreakData(parsedData);
          setModels(processedModels);
          setModelComparisonData(comparisonData);
          
          // Extract unique values for filters
          if (parsedData.length > 0) {
            setUniqueModels([...new Set(parsedData.map(d => d.target_model || d.model))]);
            setUniqueTestCases([...new Set(parsedData.map(d => d.test_case))]);
            setUniqueTactics([...new Set(parsedData.map(d => d.jailbreak))]);
            setUniqueEvaluators([...new Set(parsedData.map(d => d.evaluator_model))].filter(Boolean));
            
            // Set initial selections
            setSelectedModel(parsedData[0].target_model || parsedData[0].model);
            setSelectedTestCase(parsedData[0].test_case);
            setSelectedTactic(parsedData[0].jailbreak);
            setSelectedEvaluator(parsedData[0].evaluator_model || null);
          }
        }
        
        setLoading(false);
      } catch (err) {
        console.error("Error loading data:", err);
        setError("Failed to load data. Please try again.");
        setLoading(false);
      }
    };
    
    loadData();
  }, [selectedFile]);
  
  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };
  
  const renderTab = (id, label) => (
    <div
      key={id}
      className={`cursor-pointer px-4 py-2 ${activeTab === id ? 'border-b-2 border-blue-500 font-medium' : ''}`}
      style={activeTab === id ? styles.activeTab : styles.inactiveTab}
      onClick={() => handleTabChange(id)}
    >
      {label}
    </div>
  );
  
  const renderContent = () => {
    if (loading) {
      return <div className="flex justify-center p-8">Loading data...</div>;
    }
    
    if (error) {
      return <div className="text-red-500 p-6">Error: {error}</div>;
    }
    
    const isEnhancedData = selectedFile === 'enhanced_master_data.csv';
    const currentData = isEnhancedData ? enhancedMasterData : models;
    
    switch (activeTab) {
      case "model":
        return <ModelPerformance 
                 data={currentData} 
                 selectedModel={selectedModel}
                 onModelSelect={setSelectedModel}
                 uniqueModels={uniqueModels}
               />;
      case "testcase":
        return <TestCaseAnalysis 
                 data={currentData}
                 selectedTestCase={selectedTestCase}
                 onTestCaseSelect={setSelectedTestCase}
                 uniqueTestCases={uniqueTestCases}
               />;
      case "tactic":
        return <TacticEffectiveness 
                 data={currentData}
                 selectedTactic={selectedTactic}
                 onTacticSelect={setSelectedTactic}
                 uniqueTactics={uniqueTactics}
               />;
      case "evaluator":
        return <EvaluatorAnalysis 
                 data={currentData}
                 selectedEvaluator={selectedEvaluator}
                 onEvaluatorSelect={setSelectedEvaluator}
                 uniqueEvaluators={uniqueEvaluators}
               />;
      case "evaluator-correlation":
        return <EvaluatorCorrelationAnalysis 
                 data={currentData}
               />;
      case "reasoning":
        return <ReasoningAnalysis 
                 data={currentData}
                 modelComparisonData={modelComparisonData}
               />;
      case "heatmap":
        return <ModelComparisonHeatmap 
                 data={currentData}
                 modelComparisonData={modelComparisonData}
               />;
      case "size":
        return <SizeAnalysis 
                 data={currentData}
                 modelComparisonData={modelComparisonData}
               />;
      case "release":
        return <ReleaseAnalysis 
                 data={currentData}
                 modelComparisonData={modelComparisonData}
               />;
      case "debug":
        return <DebugTurnTypeData 
                 data={currentData}
               />;
      default:
        return <div>Select a tab to view analysis</div>;
    }
  };
  
  const renderFileSelector = () => (
    <div className="mb-4">
      <label className="block text-sm font-medium mb-1">Data Source:</label>
      <select 
        className="w-full p-2 border rounded"
        value={selectedFile}
        onChange={(e) => setSelectedFile(e.target.value)}
      >
        {availableFiles.map(file => (
          <option key={file} value={file}>{file}</option>
        ))}
      </select>
    </div>
  );
  
  return (
    <div className="w-full">
      {renderFileSelector()}
      
      <div className="flex mb-4 border-b overflow-x-auto">
        {renderTab("model", "Model Performance")}
        {renderTab("testcase", "Test Case Analysis")}
        {renderTab("tactic", "Tactic Effectiveness")}
        {renderTab("evaluator", "Evaluator Analysis")}
        {renderTab("evaluator-correlation", "Evaluator Correlation")}
        {renderTab("reasoning", "Reasoning Analysis")}
        {renderTab("heatmap", "Model Comparison")}
        {renderTab("size", "Size Analysis")}
        {renderTab("release", "Release Analysis")}
        {renderTab("debug", "Debug Turn Data")}
      </div>
      
      {renderContent()}
    </div>
  );
};

export default CombinedVisualization; 