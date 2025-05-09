import React, { useState, useMemo, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, LabelList, ScatterChart, Scatter, ZAxis, Label
} from 'recharts';

// Color constants
const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE', 
  '#00C49F', '#FFBB28', '#FF8042', '#a4de6c', '#d0ed57'
];

const ReasoningAnalysis = ({ data, modelComparisonData }) => {
  const [chartType, setChartType] = useState("bar");
  const [selectedModel, setSelectedModel] = useState(null);
  
  // Debug logging for incoming data
  useEffect(() => {
    console.log("=== ReasoningAnalysis Component Received Data ===");
    console.log("Data type:", typeof data);
    console.log("Is array:", Array.isArray(data));
    console.log("Data length:", Array.isArray(data) ? data.length : "N/A");
    
    if (Array.isArray(data) && data.length > 0) {
      console.log("First data item:", data[0]);
      
      // Check type of first item
      if (data[0] && data[0].name) {
        console.log("Processing as processed models array");
        // Look for sample rows with reasoning data
        let foundReasoningRows = 0;
        let reasoningSamples = [];
        
        for (const model of data.slice(0, 3)) {
          if (!model.testCases) continue;
          
          for (const testCase of model.testCases) {
            if (!testCase.rows) continue;
            
            for (const row of testCase.rows.slice(0, 5)) {
              console.log(`Examining row from ${model.name} - ${testCase.name}:`, {
                reasoning: row.reasoning,
                source_file: row.source_file,
                batch: row.batch,
                timestamp: row.timestamp,
                target_model: row.target_model
              });
              
              if (row.reasoning || 
                  (row.source_file && row.source_file.includes("reasoning_")) ||
                  (row.target_model && row.target_model.includes("thinking"))) {
                foundReasoningRows++;
                if (reasoningSamples.length < 3) {
                  reasoningSamples.push(row);
                }
              }
            }
          }
        }
        
        console.log(`Found ${foundReasoningRows} rows with reasoning data in processed models`);
        console.log("Reasoning data samples:", reasoningSamples);
      } else {
        console.log("Processing as raw data rows");
        // Look for sample rows with reasoning data
        let foundReasoningRows = 0;
        let reasoningSamples = [];
        
        for (const row of data.slice(0, 50)) {
          if (row.reasoning || 
              (row.source_file && row.source_file.includes("reasoning_")) ||
              (row.target_model && row.target_model.includes("thinking"))) {
            foundReasoningRows++;
            if (reasoningSamples.length < 5) {
              reasoningSamples.push({
                reasoning: row.reasoning,
                source_file: row.source_file,
                target_model: row.target_model,
                batch: row.batch,
                timestamp: row.timestamp
              });
            }
          }
        }
        
        console.log(`Found ${foundReasoningRows} rows with reasoning data in raw data`);
        console.log("Reasoning data samples:", reasoningSamples);
      }
    }
  }, [data]);
  
  // Process data for visualization
  const processedData = useMemo(() => {
    console.log("Processing reasoning data...");
    if (!data || (Array.isArray(data) && data.length === 0)) {
      console.log("No data available for reasoning analysis");
      return { 
        overviewData: [], 
        modelData: [], 
        relationshipData: [],
        hasReasoningData: false,
        uniqueModels: []
      };
    }
    
    // Debug: Check what types of goal_achieved values exist in the data
    if (Array.isArray(data)) {
      const goalAchievedValues = new Set();
      const goalAchievedTypes = new Set();
      
      // Loop through first 100 items to check goal_achieved values
      const sampleSize = Math.min(data.length, 100);
      for (let i = 0; i < sampleSize; i++) {
        if (data[i].rows) {
          // It's a processed model
          for (const testCase of data[i].testCases || []) {
            for (const row of testCase.rows || []) {
              goalAchievedValues.add(String(row.goal_achieved));
              goalAchievedTypes.add(typeof row.goal_achieved);
            }
          }
        } else {
          // It's raw data
          goalAchievedValues.add(String(data[i].goal_achieved));
          goalAchievedTypes.add(typeof data[i].goal_achieved);
        }
      }
      
      console.log("DEBUG goal_achieved types:", [...goalAchievedTypes]);
      console.log("DEBUG goal_achieved values:", [...goalAchievedValues]);
    }
    
    // Create model size map from modelComparisonData
    const modelSizes = {};
    
    if (modelComparisonData && modelComparisonData.length > 0) {
      for (const model of modelComparisonData) {
        if (model.Model && model.Parameters) {
          const modelName = model.Model;
          const size = parseFloat(model.Parameters);
          
          // Only store the exact model name
          modelSizes[modelName] = size;
        } else if (model.model_name && model.parameters) {
          modelSizes[model.model_name] = parseFloat(model.parameters);
        }
      }
    }
    
    // Function to get model size
    const getModelSize = (modelName) => {
      if (!modelName) return null;
      
      // Try direct match only
      if (modelSizes[modelName]) {
        return modelSizes[modelName];
      }
      
      return null;
    };
    
    // Reasoning levels mapping
    const reasoningLevels = ["none", "low", "medium", "high"];
    const reasoningOrder = { "none": 0, "low": 1, "medium": 2, "high": 3 };
    
    // Extract reasoning data
    let reasoningData = [];
    
    console.log("DEBUG: Data type:", typeof data);
    console.log("DEBUG: Data length:", Array.isArray(data) ? data.length : "N/A");
    console.log("DEBUG: First few data items:", Array.isArray(data) ? data.slice(0, 3) : data);
    
    // Process data based on format
    if (Array.isArray(data) && data[0] && data[0].name) {
      // Already processed models array
      console.log("Processing model array data for reasoning");
      for (const model of data) {
        if (!model.testCases) continue;
        
        for (const testCase of model.testCases) {
          if (!testCase.rows) continue;
          
          for (const row of testCase.rows) {
            // Check for reasoning data in various places
            let reasoningValue = null;
            
            // Direct reasoning field (case insensitive match)
            if (row.reasoning && typeof row.reasoning === 'string') {
              const lowerCaseReasoning = row.reasoning.toLowerCase().trim();
              if (["none", "low", "medium", "high"].includes(lowerCaseReasoning)) {
                reasoningValue = lowerCaseReasoning;
                console.log(`Found direct reasoning value: ${reasoningValue}`);
              }
            }
            // Check source_file for reasoning level
            if (!reasoningValue && row.source_file && typeof row.source_file === 'string') {
              const reasoningMatch = row.source_file.match(/reasoning_(none|low|medium|high)/i);
              if (reasoningMatch) {
                reasoningValue = reasoningMatch[1].toLowerCase();
                console.log(`Found reasoning in source_file: ${reasoningValue}`);
              }
            }
            // Check in timestamp or batch fields
            if (!reasoningValue && row.timestamp && typeof row.timestamp === 'string') {
              const reasoningMatch = row.timestamp.match(/reasoning_(none|low|medium|high)/i);
              if (reasoningMatch) {
                reasoningValue = reasoningMatch[1].toLowerCase();
                console.log(`Found reasoning in timestamp: ${reasoningValue}`);
              }
            }
            if (!reasoningValue && row.batch && typeof row.batch === 'string') {
              const reasoningMatch = row.batch.match(/reasoning_(none|low|medium|high)/i);
              if (reasoningMatch) {
                reasoningValue = reasoningMatch[1].toLowerCase();
                console.log(`Found reasoning in batch: ${reasoningValue}`);
              }
            }
            // Check in target_model field for thinking variants
            if (!reasoningValue && row.target_model && typeof row.target_model === 'string' && 
                    row.target_model.toLowerCase().includes('thinking')) {
              reasoningValue = 'high';
              console.log(`Assigned 'high' reasoning to thinking model: ${row.target_model}`);
            }
            
            // If we found reasoning data, add it to our collection
            if (reasoningValue) {
              // Determine if this was a successful attempt
              const isSuccessful = row.goal_achieved === true || 
                                   (typeof row.goal_achieved === 'string' && row.goal_achieved.toLowerCase() === 'true') || 
                                   row.success === true ||
                                   (typeof row.success === 'string' && row.success.toLowerCase() === 'true') ||
                                   row.jailbreak_success === true || 
                                   (typeof row.jailbreak_success === 'string' && row.jailbreak_success.toLowerCase() === 'true') ||
                                   (row.asr !== undefined && row.asr > 0);
                                   
              // Log details of this determination for debugging             
              if (Math.random() < 0.1) { // Log ~10% of rows to avoid flooding console
                console.log(`Success determination for ${model.name}, reasoning=${reasoningValue}:`, {
                  goal_achieved: row.goal_achieved,
                  goal_achieved_type: typeof row.goal_achieved,
                  success: row.success,
                  jailbreak_success: row.jailbreak_success,
                  asr: row.asr,
                  isSuccessful: isSuccessful
                });
              }
              
              reasoningData.push({
                model: model.name,
                reasoning: reasoningValue,
                success: isSuccessful,
                test_case: testCase.name,
                jailbreak: row.jailbreak || row.jailbreak_tactic || 'unknown'
              });
            }
          }
        }
      }
    } else {
      // Raw data rows
      console.log("Processing raw data rows for reasoning");
      let processedCount = 0;
      
      for (const row of data) {
        // Check for reasoning data in various places
        let reasoningValue = null;
        
        // Direct reasoning field - it could be in any format
        if (row.reasoning !== undefined) {
          const rawValue = String(row.reasoning).toLowerCase().trim();
          if (["none", "low", "medium", "high"].includes(rawValue)) {
            reasoningValue = rawValue;
            console.log(`Row ${processedCount}: Found direct reasoning value: ${reasoningValue}`);
          }
        }
        
        // Check source_file for reasoning level
        if (!reasoningValue && row.source_file && typeof row.source_file === 'string') {
          const reasoningMatch = row.source_file.match(/reasoning_(none|low|medium|high)/i);
          if (reasoningMatch) {
            reasoningValue = reasoningMatch[1].toLowerCase();
            console.log(`Row ${processedCount}: Found reasoning in source_file: ${reasoningValue}`);
          }
        }
        
        // Check in timestamp or batch fields
        if (!reasoningValue && row.timestamp && typeof row.timestamp === 'string') {
          const reasoningMatch = row.timestamp.match(/reasoning_(none|low|medium|high)/i);
          if (reasoningMatch) {
            reasoningValue = reasoningMatch[1].toLowerCase();
            console.log(`Row ${processedCount}: Found reasoning in timestamp: ${reasoningValue}`);
          }
        }
        
        if (!reasoningValue && row.batch && typeof row.batch === 'string') {
          const reasoningMatch = row.batch.match(/reasoning_(none|low|medium|high)/i);
          if (reasoningMatch) {
            reasoningValue = reasoningMatch[1].toLowerCase();
            console.log(`Row ${processedCount}: Found reasoning in batch: ${reasoningValue}`);
          }
        }
        
        // Check in target_model field for thinking variants
        if (!reasoningValue && row.target_model && typeof row.target_model === 'string' && 
                row.target_model.toLowerCase().includes('thinking')) {
          reasoningValue = 'high';
          console.log(`Row ${processedCount}: Assigned 'high' reasoning to thinking model: ${row.target_model}`);
        }
        
        // If we found reasoning data, add it to our collection
        if (reasoningValue) {
          // Determine if this was a successful attempt
          const isSuccessful = row.goal_achieved === true || 
                               (typeof row.goal_achieved === 'string' && row.goal_achieved.toLowerCase() === 'true') || 
                               row.success === true ||
                               (typeof row.success === 'string' && row.success.toLowerCase() === 'true') ||
                               row.jailbreak_success === true || 
                               (typeof row.jailbreak_success === 'string' && row.jailbreak_success.toLowerCase() === 'true') ||
                               (row.asr !== undefined && row.asr > 0);
                               
          // Log details of this determination for debugging             
          if (Math.random() < 0.05) { // Log ~5% of rows to avoid flooding console
            console.log(`Success determination for raw data row, reasoning=${reasoningValue}:`, {
              goal_achieved: row.goal_achieved,
              goal_achieved_type: typeof row.goal_achieved,
              success: row.success,
              jailbreak_success: row.jailbreak_success,
              asr: row.asr,
              isSuccessful: isSuccessful
            });
          }
          
          reasoningData.push({
            model: row.target_model || row.model || 'unknown',
            reasoning: reasoningValue,
            success: isSuccessful,
            test_case: row.test_case || 'unknown',
            jailbreak: row.jailbreak || row.jailbreak_tactic || 'unknown'
          });
        }
        
        processedCount++;
        if (processedCount <= 10 || processedCount % 1000 === 0) {
          console.log(`Processed ${processedCount}/${data.length} rows, found ${reasoningData.length} reasoning rows`);
        }
      }
    }
    
    // Debug info
    console.log(`Extracted ${reasoningData.length} rows with reasoning data`);
    if (reasoningData.length > 0) {
      console.log('Sample reasoning data:', reasoningData.slice(0, 3));
      
      // Count success rates by reasoning level for additional debugging
      const successByReasoning = {}; 
      reasoningLevels.forEach(level => {
        const rowsWithLevel = reasoningData.filter(row => row.reasoning === level);
        const successCount = rowsWithLevel.filter(row => row.success).length;
        const totalCount = rowsWithLevel.length;
        
        successByReasoning[level] = {
          successful: successCount,
          total: totalCount,
          rate: totalCount > 0 ? (successCount / totalCount) * 100 : 0
        };
      });
      
      console.log("DEBUG: Pre-calculation success rates by reasoning level:", successByReasoning);
    } else {
      console.warn('No reasoning data was found! Check data format and reasoning column values.');
      
      // Debugging - check a sample of the data to see what fields are available
      if (Array.isArray(data) && data.length > 0) {
        console.log("DEBUG: Checking field availability in sample rows");
        const sampleRows = data.slice(0, 5);
        
        for (let i = 0; i < sampleRows.length; i++) {
          const row = sampleRows[i];
          console.log(`DEBUG: Sample row ${i}:`, {
            hasReasoning: row.reasoning !== undefined,
            reasoningValue: row.reasoning,
            hasSourceFile: row.source_file !== undefined,
            sourceFileValue: row.source_file,
            hasBatch: row.batch !== undefined, 
            batchValue: row.batch,
            hasTargetModel: row.target_model !== undefined,
            targetModelValue: row.target_model
          });
        }
        
        // Look for any fields that might contain reasoning information
        const potentialFields = Object.keys(data[0]);
        console.log("DEBUG: All available fields:", potentialFields);
        
        // Check for any fields containing 'reason' in their name
        const reasoningRelatedFields = potentialFields.filter(field => 
          field.toLowerCase().includes('reason') || 
          field.toLowerCase().includes('think')
        );
        
        if (reasoningRelatedFields.length > 0) {
          console.log("DEBUG: Potential reasoning-related fields:", reasoningRelatedFields);
        }
      }
    }
    
    if (reasoningData.length === 0) {
      return { 
        overviewData: [], 
        modelData: [], 
        relationshipData: [],
        hasReasoningData: false,
        uniqueModels: []
      };
    }
    
    // 1. Group by model and reasoning level
    const dataByModelAndReasoning = {};
    const uniqueModels = new Set();
    
    reasoningData.forEach(row => {
      const model = row.model;
      uniqueModels.add(model);
      const reasoning = row.reasoning;
      
      if (!dataByModelAndReasoning[model]) {
        dataByModelAndReasoning[model] = {};
      }
      
      if (!dataByModelAndReasoning[model][reasoning]) {
        dataByModelAndReasoning[model][reasoning] = {
          totalTests: 0,
          successfulTests: 0,
          asr: 0
        };
      }
      
      dataByModelAndReasoning[model][reasoning].totalTests += 1;
      if (row.success) {
        dataByModelAndReasoning[model][reasoning].successfulTests += 1;
      }
    });
    
    // 2. Calculate ASR for each model and reasoning level
    Object.keys(dataByModelAndReasoning).forEach(model => {
      reasoningLevels.forEach(reasoning => {
        if (dataByModelAndReasoning[model][reasoning]) {
          const { totalTests, successfulTests } = dataByModelAndReasoning[model][reasoning];
          dataByModelAndReasoning[model][reasoning].asr = 
            totalTests > 0 ? (successfulTests / totalTests) * 100 : 0;
        }
      });
    });
    
    console.log("DEBUG: Model and reasoning level ASR calculations:", dataByModelAndReasoning);
    
    // 3. Create chart data for each model
    const modelChartData = [];
    
    [...uniqueModels].forEach((model, index) => {
      const modelData = reasoningLevels.map(reasoning => {
        const data = dataByModelAndReasoning[model]?.[reasoning] || {
          totalTests: 0,
          successfulTests: 0,
          asr: 0
        };
        
        return {
          model,
          reasoning,
          reasoningValue: reasoningOrder[reasoning],
          asr: data.asr,
          totalTests: data.totalTests,
          color: COLORS[index % COLORS.length]
        };
      }).filter(d => d.totalTests > 0);
      
      if (modelData.length > 0) {
        modelChartData.push({
          model,
          data: modelData
        });
      }
    });
    
    // 4. Aggregate data for overview chart
    const aggregatedByReasoning = {};
    reasoningLevels.forEach(level => {
      aggregatedByReasoning[level] = { totalTests: 0, successfulTests: 0, asr: 0 };
    });
    
    reasoningData.forEach(row => {
      const reasoning = row.reasoning;
      aggregatedByReasoning[reasoning].totalTests += 1;
      if (row.success) {
        aggregatedByReasoning[reasoning].successfulTests += 1;
      }
    });
    
    reasoningLevels.forEach(level => {
      const { totalTests, successfulTests } = aggregatedByReasoning[level];
      aggregatedByReasoning[level].asr = 
        totalTests > 0 ? (successfulTests / totalTests) * 100 : 0;
    });
    
    const overviewData = reasoningLevels.map(level => ({
      reasoning: level,
      reasoningValue: reasoningOrder[level],
      asr: aggregatedByReasoning[level].asr,
      totalTests: aggregatedByReasoning[level].totalTests
    })).filter(d => d.totalTests > 0);
    
    console.log("DEBUG: Overview data for chart:", overviewData);
    
    // 5. Create data for model/reasoning relationship scatter plot
    const relationshipData = [];
    
    [...uniqueModels].forEach((model, index) => {
      const modelSize = getModelSize(model) || 0;
      
      reasoningLevels.forEach(reasoning => {
        if (dataByModelAndReasoning[model]?.[reasoning]?.totalTests > 0) {
          relationshipData.push({
            model,
            reasoning,
            reasoningValue: reasoningOrder[reasoning],
            asr: dataByModelAndReasoning[model][reasoning].asr,
            totalTests: dataByModelAndReasoning[model][reasoning].totalTests,
            modelSize,
            color: COLORS[index % COLORS.length]
          });
        }
      });
    });
    
    return {
      overviewData,
      modelData: modelChartData,
      relationshipData,
      hasReasoningData: true,
      uniqueModels: [...uniqueModels]
    };
  }, [data, modelComparisonData]);
  
  // Render chart type selector
  const renderChartTypeSelector = () => (
    <div className="mb-4">
      <label className="block text-sm font-medium mb-1">Chart Type:</label>
      <div className="flex space-x-4">
        <label className="inline-flex items-center">
          <input 
            type="radio" 
            value="bar" 
            checked={chartType === "bar"} 
            onChange={() => setChartType("bar")}
            className="mr-1"
          />
          Bar Chart
        </label>
        <label className="inline-flex items-center">
          <input 
            type="radio" 
            value="scatter" 
            checked={chartType === "scatter"} 
            onChange={() => setChartType("scatter")}
            className="mr-1"
          />
          Scatter Plot
        </label>
      </div>
    </div>
  );
  
  // Render model selector
  const renderModelSelector = () => (
    <div className="mb-4">
      <label className="block text-sm font-medium mb-1">Select Model:</label>
      <select 
        className="w-full p-2 border rounded"
        value={selectedModel || ''}
        onChange={(e) => setSelectedModel(e.target.value)}
      >
        <option value="">All Models (Overview)</option>
        {processedData.uniqueModels.map(model => (
          <option key={model} value={model}>{model}</option>
        ))}
      </select>
    </div>
  );
  
  // Render overview bar chart
  const renderOverviewChart = () => {
    if (!processedData.hasReasoningData || processedData.overviewData.length === 0) {
      return (
        <div className="p-4 bg-yellow-50 text-yellow-800 rounded">
          No reasoning data available. The dataset should include a 'reasoning' column with values: "none", "low", "medium", or "high".
        </div>
      );
    }
    
    return (
      <div className="chart-container">
        <h3 className="text-lg font-medium mb-2">Overall Attack Success Rate by Reasoning Effort</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart
            data={processedData.overviewData}
            margin={{ top: 20, right: 30, left: 20, bottom: 50 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="reasoning" 
              label={{ value: 'Reasoning Effort', position: 'bottom', offset: 20 }}
            />
            <YAxis 
              label={{ value: 'Attack Success Rate (%)', angle: -90, position: 'insideLeft' }}
              domain={[0, 100]}
            />
            <Tooltip 
              formatter={(value, name) => {
                if (name === 'asr') return [`${value.toFixed(2)}%`, 'Success Rate'];
                return [value, name];
              }}
              labelFormatter={(value) => `Reasoning: ${value}`}
            />
            <Legend />
            <Bar dataKey="asr" fill="#8884d8" name="ASR (%)">
              <LabelList 
                dataKey="totalTests" 
                position="top" 
                content={(props) => {
                  const { x, y, width, value } = props;
                  return (
                    <text 
                      x={x + width / 2} 
                      y={y - 10} 
                      fill="#666" 
                      textAnchor="middle"
                      fontSize="12"
                    >
                      {`n=${value}`}
                    </text>
                  );
                }}
              />
              {processedData.overviewData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };
  
  // Render model-specific bar chart
  const renderModelChart = () => {
    if (!selectedModel || !processedData.hasReasoningData) return null;
    
    const modelData = processedData.modelData.find(m => m.model === selectedModel);
    if (!modelData || modelData.data.length === 0) {
      return (
        <div className="p-4 bg-yellow-50 text-yellow-800 rounded">
          No reasoning data available for the selected model.
        </div>
      );
    }
    
    return (
      <div className="chart-container mt-6">
        <h3 className="text-lg font-medium mb-2">Attack Success Rate by Reasoning Effort for {selectedModel}</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart
            data={modelData.data}
            margin={{ top: 20, right: 30, left: 20, bottom: 50 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="reasoning" 
              label={{ value: 'Reasoning Effort', position: 'bottom', offset: 20 }}
            />
            <YAxis 
              label={{ value: 'Attack Success Rate (%)', angle: -90, position: 'insideLeft' }}
              domain={[0, 100]}
            />
            <Tooltip 
              formatter={(value, name) => {
                if (name === 'asr') return [`${value.toFixed(2)}%`, 'Success Rate'];
                return [value, name];
              }}
              labelFormatter={(value) => `Reasoning: ${value}`}
            />
            <Legend />
            <Bar dataKey="asr" fill={modelData.data[0].color} name="ASR (%)">
              <LabelList 
                dataKey="totalTests" 
                position="top" 
                content={(props) => {
                  const { x, y, width, value } = props;
                  return (
                    <text 
                      x={x + width / 2} 
                      y={y - 10} 
                      fill="#666" 
                      textAnchor="middle"
                      fontSize="12"
                    >
                      {`n=${value}`}
                    </text>
                  );
                }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };
  
  // Render scatter plot
  const renderScatterPlot = () => {
    if (!processedData.hasReasoningData || processedData.relationshipData.length === 0) {
      return null;
    }
    
    return (
      <div className="chart-container mt-6">
        <h3 className="text-lg font-medium mb-2">Relationship Between Reasoning Effort and Attack Success</h3>
        <ResponsiveContainer width="100%" height={500}>
          <ScatterChart
            margin={{ top: 20, right: 30, left: 20, bottom: 50 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="reasoningValue" 
              type="number"
              domain={[0, 3]}
              tickCount={4}
              tickFormatter={(value) => {
                const labels = ["none", "low", "medium", "high"];
                return labels[value] || '';
              }}
              label={{ value: 'Reasoning Effort', position: 'bottom', offset: 20 }}
            />
            <YAxis 
              dataKey="asr"
              label={{ value: 'Attack Success Rate (%)', angle: -90, position: 'insideLeft' }}
              domain={[0, 100]}
            />
            <ZAxis 
              dataKey="totalTests" 
              range={[40, 400]} 
              name="Sample Count"
            />
            <Tooltip 
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white p-2 border rounded shadow">
                      <p className="font-medium">{data.model}</p>
                      <p>Reasoning: {data.reasoning}</p>
                      <p>Success Rate: {data.asr.toFixed(2)}%</p>
                      <p>Sample Count: {data.totalTests}</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend 
              payload={
                [...new Set(processedData.relationshipData.map(d => d.model))].map((model, index) => ({
                  value: model,
                  type: 'circle',
                  color: COLORS[index % COLORS.length]
                }))
              }
            />
            {processedData.uniqueModels.map((model, index) => {
              const modelData = processedData.relationshipData.filter(d => d.model === model);
              return (
                <Scatter 
                  key={model}
                  name={model}
                  data={modelData}
                  fill={COLORS[index % COLORS.length]}
                />
              );
            })}
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    );
  };
  
  // Render key insights
  const renderKeyInsights = () => {
    if (!processedData.hasReasoningData) return null;
    
    // Calculate average ASR across reasoning levels
    const avgByReasoning = {};
    
    processedData.overviewData.forEach(data => {
      avgByReasoning[data.reasoning] = data.asr;
    });
    
    // Find best reasoning level
    let bestReasoning = null;
    let bestASR = -1;
    
    Object.entries(avgByReasoning).forEach(([reasoning, asr]) => {
      if (asr > bestASR) {
        bestASR = asr;
        bestReasoning = reasoning;
      }
    });
    
    return (
      <div className="mt-6 p-4 bg-blue-50 rounded">
        <h3 className="text-md font-medium mb-2">Key Insights</h3>
        <ul className="list-disc pl-5 text-sm space-y-2">
          <li>This analysis shows how reasoning effort affects attack success rate (ASR).</li>
          {bestReasoning && (
            <li>Overall, <strong>{bestReasoning}</strong> reasoning shows the highest success rate at <strong>{bestASR.toFixed(1)}%</strong>.</li>
          )}
          <li>Different models may respond differently to varying levels of reasoning.</li>
          <li>Select a specific model from the dropdown to see its reasoning profile.</li>
        </ul>
      </div>
    );
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">Reasoning Analysis</h2>
        <p className="text-gray-600">
          This analysis explores the relationship between reasoning effort and attack success rate.
          Data includes examples with reasoning values: "none", "low", "medium", or "high".
        </p>
      </div>
      
      {!processedData.hasReasoningData ? (
        <div className="p-6 bg-gray-100 rounded text-center">
          <p className="text-lg">
            No reasoning data available. This analysis requires a 'reasoning' column
            with values: "none", "low", "medium", or "high".
          </p>
        </div>
      ) : (
        <div className="flex flex-wrap -mx-2">
          <div className="w-full md:w-1/4 px-2">
            {renderModelSelector()}
            {renderChartTypeSelector()}
            {renderKeyInsights()}
          </div>
          
          <div className="w-full md:w-3/4 px-2">
            {chartType === "bar" ? (
              <>
                {!selectedModel && renderOverviewChart()}
                {selectedModel && renderModelChart()}
              </>
            ) : (
              renderScatterPlot()
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ReasoningAnalysis; 