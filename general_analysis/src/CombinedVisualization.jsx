import React, { useState, useEffect } from 'react';
import Papa from 'papaparse';
import ModelPerformance from './components/ModelPerformance';
import TestCaseAnalysis from './components/TestCaseAnalysis';
import TacticEffectiveness from './components/TacticEffectiveness';
import EvaluatorAnalysis from './components/EvaluatorAnalysis';
import ModelComparisonHeatmap from './components/ModelComparisonHeatmap';
import SizeAnalysis from './components/SizeAnalysis';
import ReasoningAnalysis from './components/ReasoningAnalysis';
import EvaluatorCorrelationAnalysis from './components/EvaluatorCorrelationAnalysis';
import { processJailbreakData, loadEnhancedMasterData } from './utils/dataProcessing';

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
  const [selectedFile, setSelectedFile] = useState('enhanced_master_data.csv');
  const [availableFiles, setAvailableFiles] = useState([
    'enhanced_master_data.csv',
    'results_test_runs.csv',
    'master_results.csv',
    'batch_4B_fixed_20250501_results.csv',
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
        
        if (selectedFile === 'enhanced_master_data.csv') {
          const { enhancedData, comparisonData } = await loadEnhancedMasterData();
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
    
    switch (activeTab) {
      case "model":
        return <ModelPerformance 
                 data={selectedFile === 'enhanced_master_data.csv' ? enhancedMasterData : models} 
                 selectedModel={selectedModel}
                 onModelSelect={setSelectedModel}
                 uniqueModels={uniqueModels}
               />;
      case "testcase":
        return <TestCaseAnalysis 
                 data={selectedFile === 'enhanced_master_data.csv' ? enhancedMasterData : models}
                 selectedTestCase={selectedTestCase}
                 onTestCaseSelect={setSelectedTestCase}
                 uniqueTestCases={uniqueTestCases}
               />;
      case "tactic":
        return <TacticEffectiveness 
                 data={selectedFile === 'enhanced_master_data.csv' ? enhancedMasterData : models}
                 selectedTactic={selectedTactic}
                 onTacticSelect={setSelectedTactic}
                 uniqueTactics={uniqueTactics}
               />;
      case "evaluator":
        return <EvaluatorAnalysis 
                 data={selectedFile === 'enhanced_master_data.csv' ? enhancedMasterData : models}
                 selectedEvaluator={selectedEvaluator}
                 onEvaluatorSelect={setSelectedEvaluator}
                 uniqueEvaluators={uniqueEvaluators}
               />;
      case "evaluator-correlation":
        return <EvaluatorCorrelationAnalysis 
                 data={selectedFile === 'enhanced_master_data.csv' ? enhancedMasterData : models}
               />;
      case "reasoning":
        return <ReasoningAnalysis 
                 data={selectedFile === 'enhanced_master_data.csv' ? enhancedMasterData : models}
                 modelComparisonData={modelComparisonData}
               />;
      case "heatmap":
        return <ModelComparisonHeatmap 
                 data={selectedFile === 'enhanced_master_data.csv' ? enhancedMasterData : models}
                 modelComparisonData={modelComparisonData}
               />;
      case "size":
        return <SizeAnalysis 
                 data={selectedFile === 'enhanced_master_data.csv' ? enhancedMasterData : models}
                 modelComparisonData={modelComparisonData}
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
      </div>
      
      {renderContent()}
    </div>
  );
};

export default CombinedVisualization; 