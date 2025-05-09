import Papa from 'papaparse';

// Function to load enhanced master data and model comparison data
export const loadEnhancedMasterData = async () => {
  try {
    console.log("Starting to load enhanced master data...");
    
    // Load enhanced_master_data.csv
    const enhancedResponse = await fetch('/data/enhanced_master_data.csv');
    if (!enhancedResponse.ok) {
      throw new Error(`Failed to fetch enhanced_master_data.csv: ${enhancedResponse.status} ${enhancedResponse.statusText}`);
    }
    
    const enhancedContent = await enhancedResponse.text();
    
    const enhancedData = Papa.parse(enhancedContent, {
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true
    }).data;
    
    // Also load model_comparison.csv for additional model metadata
    console.log("Starting to load model comparison data...");
    const comparisonResponse = await fetch('/data/model_comparison.csv');
    if (!comparisonResponse.ok) {
      throw new Error(`Failed to fetch model_comparison.csv: ${comparisonResponse.status} ${comparisonResponse.statusText}`);
    }
    
    const comparisonContent = await comparisonResponse.text();
    
    const comparisonData = Papa.parse(comparisonContent, {
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true
    }).data;
    
    // Process score fields that might be strings
    const processedData = enhancedData.map(row => {
      if (row.scores && typeof row.scores === 'string') {
        try {
          row.scores = JSON.parse(row.scores.replace(/'/g, '"'));
        } catch (e) {
          // Keep original if parsing fails
          console.error("Error parsing scores:", e);
        }
      }
      return row;
    });
    
    return { 
      enhancedData: processedData,
      comparisonData
    };
  } catch (err) {
    console.error("Error loading enhanced data:", err);
    throw err;
  }
};

// Process jailbreak data from various formats
export const processJailbreakData = (data) => {
  // Group data by model
  const modelGroups = {};
  
  for (const row of data) {
    const modelName = row.target_model || row.model || 'unknown';
    
    if (!modelGroups[modelName]) {
      modelGroups[modelName] = [];
    }
    
    modelGroups[modelName].push(row);
  }
  
  // Process each model's data
  const processedModels = Object.entries(modelGroups).map(([modelName, rows]) => {
    // Group by test case
    const testCaseGroups = {};
    
    for (const row of rows) {
      const testCaseName = row.test_case || 'unknown';
      
      if (!testCaseGroups[testCaseName]) {
        testCaseGroups[testCaseName] = [];
      }
      
      testCaseGroups[testCaseName].push(row);
    }
    
    // Process test cases
    const testCases = Object.entries(testCaseGroups).map(([testCaseName, testRows]) => {
      // Calculate metrics for this test case
      const successRate = calculateSuccessRate(testRows);
      const refusalRate = calculateRefusalRate(testRows);
      const roundCount = calculateAverageRounds(testRows);
      
      return {
        name: testCaseName,
        successRate,
        refusalRate,
        roundCount,
        rows: testRows
      };
    });
    
    // Group by tactic (jailbreak)
    const tacticRows = {
      single: {},
      multi: {}
    };
    
    for (const row of rows) {
      const tacticName = row.jailbreak || 'unknown';
      
      // Determine if it's a single or multi-turn
      const isSingleTurn = row.num_turns === 1 || !row.num_turns;
      const tacticType = isSingleTurn ? 'single' : 'multi';
      
      if (!tacticRows[tacticType][tacticName]) {
        tacticRows[tacticType][tacticName] = [];
      }
      
      tacticRows[tacticType][tacticName].push(row);
    }
    
    // Process tactics
    const tactics = {
      single: [],
      multi: []
    };
    
    // Process single-turn tactics
    for (const [tacticName, tactRows] of Object.entries(tacticRows.single)) {
      tactics.single.push({
        name: tacticName,
        successRate: calculateSuccessRate(tactRows),
        refusalRate: calculateRefusalRate(tactRows),
        roundCount: calculateAverageRounds(tactRows),
        rows: tactRows
      });
    }
    
    // Process multi-turn tactics
    for (const [tacticName, tactRows] of Object.entries(tacticRows.multi)) {
      tactics.multi.push({
        name: tacticName,
        successRate: calculateSuccessRate(tactRows),
        refusalRate: calculateRefusalRate(tactRows),
        roundCount: calculateAverageRounds(tactRows),
        rows: tactRows
      });
    }
    
    // Sort tactics by success rate
    tactics.single.sort((a, b) => b.successRate - a.successRate);
    tactics.multi.sort((a, b) => b.successRate - a.successRate);
    
    // Process evaluator data if available
    const evaluators = {};
    for (const row of rows) {
      if (row.evaluator_model) {
        if (!evaluators[row.evaluator_model]) {
          evaluators[row.evaluator_model] = [];
        }
        evaluators[row.evaluator_model].push(row);
      }
    }
    
    const evaluatorData = Object.entries(evaluators).map(([evalName, evalRows]) => ({
      name: evalName,
      successRate: calculateSuccessRate(evalRows),
      refusalRate: calculateRefusalRate(evalRows),
      rows: evalRows
    }));
    
    return {
      name: modelName,
      testCases,
      tactics,
      evaluators: evaluatorData,
      rows
    };
  });
  
  return processedModels;
};

// Helper functions for calculating metrics
function calculateSuccessRate(rows) {
  if (!rows || rows.length === 0) return 0;
  
  const successful = rows.filter(row => {
    // Different data formats may store success differently
    if (row.success !== undefined) return Boolean(row.success);
    if (row.jailbreak_success !== undefined) return Boolean(row.jailbreak_success);
    if (row.asr !== undefined) return row.asr > 0;
    return false;
  });
  
  return (successful.length / rows.length) * 100;
}

function calculateRefusalRate(rows) {
  if (!rows || rows.length === 0) return 0;
  
  const refusals = rows.filter(row => {
    // Different data formats may store refusal differently
    if (row.refused !== undefined) return Boolean(row.refused);
    if (row.refusal !== undefined) return Boolean(row.refusal);
    if (row.rejection !== undefined) return Boolean(row.rejection);
    return false;
  });
  
  return (refusals.length / rows.length) * 100;
}

function calculateAverageRounds(rows) {
  if (!rows || rows.length === 0) return 0;
  
  const validRows = rows.filter(row => {
    // Different data formats may store rounds differently
    return row.num_turns !== undefined || 
           row.rounds !== undefined || 
           row.turn_count !== undefined;
  });
  
  if (validRows.length === 0) return 0;
  
  const sum = validRows.reduce((total, row) => {
    const rounds = row.num_turns || row.rounds || row.turn_count || 0;
    return total + rounds;
  }, 0);
  
  return sum / validRows.length;
}

// Calculate standard error for a set of values
export const calculateStandardError = (values) => {
  if (!values || values.length <= 1) return 0;
  
  const n = values.length;
  const mean = values.reduce((sum, val) => sum + val, 0) / n;
  const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / n;
  const standardDeviation = Math.sqrt(variance);
  return standardDeviation / Math.sqrt(n);
};

// Get color scale for values
export const getColorScale = (value, min, max) => {
  // Normalize value between 0 and 1
  const normalized = Math.max(0, Math.min(1, (value - min) / (max - min)));
  
  // Use a color scale: blue to red
  const r = Math.round(normalized * 255);
  const b = Math.round((1 - normalized) * 255);
  const g = 100;
  
  return `rgb(${r}, ${g}, ${b})`;
}; 