// test_case_model_size_analysis.js
// This file provides functions to analyze the relationship between model size and ASR for each test case and AI lab

import Papa from 'papaparse';

/**
 * Extract company/lab from model name
 * @param {string} modelName - The full model name
 * @return {string} The company/lab name
 */
const extractCompany = (modelName) => {
  if (!modelName) return 'unknown';
  
  const modelLower = modelName.toLowerCase();
  
  if (modelLower.includes('meta') || modelLower.includes('llama')) return 'Meta';
  if (modelLower.includes('anthropic') || modelLower.includes('claude')) return 'Anthropic';
  if (modelLower.includes('google') || modelLower.includes('gemini') || modelLower.includes('gemma')) return 'Google';
  if (modelLower.includes('mistral')) return 'Mistral AI';
  if (modelLower.includes('deepseek')) return 'DeepSeek';
  if (modelLower.includes('qwen')) return 'Alibaba';
  if (modelLower.includes('gpt') || modelLower.includes('openai')) return 'OpenAI';
  if (modelLower.includes('x-ai') || modelLower.includes('grok')) return 'xAI';
  
  // Extract from prefix if it contains a slash
  if (modelLower.includes('/')) {
    return modelLower.split('/')[0];
  }
  
  return 'unknown';
};

/**
 * Calculate linear regression for a set of points
 * @param {Array} points - Array of points [x, y]
 * @return {Object} Regression results including slope, intercept, and r-squared
 */
const calculateLinearRegression = (points) => {
  if (points.length < 2) {
    return { slope: 0, intercept: 0, r2: 0 };
  }

  // Calculate the means of x and y
  let sumX = 0;
  let sumY = 0;
  points.forEach(point => {
    sumX += point[0];
    sumY += point[1];
  });
  const meanX = sumX / points.length;
  const meanY = sumY / points.length;

  // Calculate the slope and intercept
  let numerator = 0;
  let denominator = 0;
  points.forEach(point => {
    numerator += (point[0] - meanX) * (point[1] - meanY);
    denominator += Math.pow(point[0] - meanX, 2);
  });

  // Avoid division by zero
  if (denominator === 0) {
    return { slope: 0, intercept: meanY, r2: 0 };
  }

  const slope = numerator / denominator;
  const intercept = meanY - slope * meanX;

  // Calculate r-squared
  let totalSumSquares = 0;
  let residualSumSquares = 0;
  points.forEach(point => {
    const predicted = slope * point[0] + intercept;
    totalSumSquares += Math.pow(point[1] - meanY, 2);
    residualSumSquares += Math.pow(point[1] - predicted, 2);
  });
  
  let r2 = 0;
  if (totalSumSquares !== 0) {
    r2 = 1 - (residualSumSquares / totalSumSquares);
  }

  return { slope, intercept, r2 };
};

/**
 * Process the enhanced master data to calculate the slopes
 * @param {Array} enhancedData - The enhanced master data
 * @param {Array} modelComparisonData - Model comparison data with sizes
 * @return {Object} Analysis results with slopes for each test case and lab
 */
export const analyzeModelSizeVsASR = (enhancedData, modelComparisonData) => {
  if (!enhancedData || enhancedData.length === 0) {
    console.error("No enhanced data available");
    return { testCases: [], labs: [], data: [] };
  }
  
  // Extract model field name
  const modelField = enhancedData[0] && 'target_model' in enhancedData[0] ? 'target_model' : 'model';
  
  // Get model sizes from model comparison data
  const modelSizes = {};
  if (modelComparisonData && modelComparisonData.length > 0) {
    modelComparisonData.forEach(model => {
      if (model.Model && model.Parameters) {
        modelSizes[model.Model] = parseFloat(model.Parameters);
      }
    });
  }
  
  // Fallback model sizes for common models
  const fallbackSizes = {
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
  
  // Extract unique test cases and labs
  const testCases = [...new Set(enhancedData.map(row => row.test_case))].sort();
  const modelNames = [...new Set(enhancedData.map(row => row[modelField]))];
  const labs = [...new Set(modelNames.map(model => extractCompany(model)))].sort();
  
  // Helper function to get model size
  const getModelSize = (modelName) => {
    // First try direct match in model comparison data
    if (modelSizes[modelName]) {
      return modelSizes[modelName];
    }
    
    // Try fallback sizes
    if (fallbackSizes[modelName]) {
      return fallbackSizes[modelName];
    }
    
    // Try to match by name pattern
    for (const [key, size] of Object.entries(fallbackSizes)) {
      if (modelName.includes(key) || key.includes(modelName)) {
        return size;
      }
    }
    
    // Try to extract size from name (common pattern: model-Xb)
    const sizeMatch = modelName.match(/-(\d+)b/i);
    if (sizeMatch && !isNaN(parseInt(sizeMatch[1]))) {
      return parseInt(sizeMatch[1]);
    }
    
    console.warn(`Could not determine size for model: ${modelName}`);
    return null;
  };
  
  // Helper function to calculate success rate (ASR)
  const calculateASR = (subset) => {
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
  
  // Group data by test case, lab, and model
  const groupedData = {};
  
  enhancedData.forEach(row => {
    const model = row[modelField];
    if (!model) return;
    
    const testCase = row.test_case;
    const lab = extractCompany(model);
    
    const key = `${testCase}|${lab}|${model}`;
    
    if (!groupedData[key]) {
      groupedData[key] = {
        testCase,
        lab,
        model,
        samples: []
      };
    }
    
    groupedData[key].samples.push(row);
  });
  
  // Calculate ASR for each group and prepare data for regression
  const regressionData = {};
  
  Object.values(groupedData).forEach(group => {
    // Need at least 3 samples for a meaningful ASR calculation
    if (group.samples.length < 3) return;
    
    const testCase = group.testCase;
    const lab = group.lab;
    const model = group.model;
    const size = getModelSize(model);
    
    // Skip if we couldn't determine the model size
    if (size === null) return;
    
    const asr = calculateASR(group.samples);
    
    const key = `${testCase}|${lab}`;
    if (!regressionData[key]) {
      regressionData[key] = {
        testCase,
        lab,
        points: []
      };
    }
    
    regressionData[key].points.push([size, asr]);
  });
  
  // Calculate regression for each test case and lab
  const regressionResults = {};
  
  Object.values(regressionData).forEach(data => {
    const key = `${data.testCase}|${data.lab}`;
    
    // Need at least 2 points for linear regression
    if (data.points.length < 2) {
      regressionResults[key] = {
        testCase: data.testCase,
        lab: data.lab,
        slope: 0,
        intercept: 0,
        r2: 0,
        numPoints: data.points.length
      };
      return;
    }
    
    const { slope, intercept, r2 } = calculateLinearRegression(data.points);
    
    regressionResults[key] = {
      testCase: data.testCase,
      lab: data.lab,
      slope,
      intercept,
      r2,
      numPoints: data.points.length
    };
  });
  
  // Prepare heatmap data
  const heatmapData = [];
  
  testCases.forEach(testCase => {
    const row = {
      testCase
    };
    
    labs.forEach(lab => {
      const key = `${testCase}|${lab}`;
      const result = regressionResults[key];
      
      // Default to null if no data
      row[lab] = result ? result.slope : null;
    });
    
    heatmapData.push(row);
  });
  
  return {
    testCases,
    labs,
    data: heatmapData,
    regressionResults: Object.values(regressionResults)
  };
};

/**
 * Load and analyze the enhanced master data from a CSV file
 * @param {string} csvFilePath - Path to the enhanced master data CSV
 * @param {string} modelComparisonFilePath - Path to the model comparison CSV
 * @return {Promise<Object>} The analysis results
 */
export const loadAndAnalyzeData = async (csvFilePath, modelComparisonFilePath) => {
  try {
    // Load enhanced master data
    const enhancedResponse = await fetch(csvFilePath);
    if (!enhancedResponse.ok) {
      throw new Error(`Failed to fetch ${csvFilePath}: ${enhancedResponse.status} ${enhancedResponse.statusText}`);
    }
    
    const enhancedContent = await enhancedResponse.text();
    const enhancedData = Papa.parse(enhancedContent, {
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true
    }).data;
    
    // Load model comparison data
    const comparisonResponse = await fetch(modelComparisonFilePath);
    if (!comparisonResponse.ok) {
      throw new Error(`Failed to fetch ${modelComparisonFilePath}: ${comparisonResponse.status} ${comparisonResponse.statusText}`);
    }
    
    const comparisonContent = await comparisonResponse.text();
    const modelComparisonData = Papa.parse(comparisonContent, {
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true
    }).data;
    
    // Run the analysis
    return analyzeModelSizeVsASR(enhancedData, modelComparisonData);
  } catch (error) {
    console.error("Error loading and analyzing data:", error);
    throw error;
  }
}; 