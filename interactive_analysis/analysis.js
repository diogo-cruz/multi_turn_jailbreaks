// Import required libraries
import fs from 'fs';
import Papa from 'papaparse';
import path from 'path';
import { fileURLToPath } from 'url';

// Command line argument for the CSV file to analyze
const csvFilename = process.argv[2] || 'results_test_runs.csv';

// Read the contents of the specified file
async function analyzeCSV(csvFilename) {
  try {
    console.log(`Analyzing ${csvFilename}...`);
    const fileContent = await fs.promises.readFile(csvFilename, { encoding: 'utf8' });

    // Parse the CSV data
    const parsedData = Papa.parse(fileContent, {
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true
    });
    
    // Special case for enhanced_master_data.csv
    if (csvFilename === 'enhanced_master_data.csv') {
      await analyzeEnhancedData(parsedData.data);
      return [];
    }

    // Process the data
    const models = processJailbreakData(parsedData.data);
    
    // Display summary
    console.log(`Processed ${models.length} models`);
    if (models.length > 0) {
      const firstModel = models[0];
      console.log(`First model: ${firstModel.name}`);
      console.log(`Test cases: ${firstModel.testCases.length}`);
      console.log(`Multi-turn tactics: ${firstModel.tactics.multi.length}`);
      console.log(`Single-turn tactics: ${firstModel.tactics.single.length}`);
      
      // Print a few example test cases with their ASRs
      console.log("\nExample test cases with ASRs:");
      firstModel.testCases.slice(0, 3).forEach(tc => {
        console.log(`- ${tc.name}: Multi=${tc.multi}%, Single=${tc.single}%`);
      });
      
      // Print a few example tactics with their ASRs
      console.log("\nExample tactics with ASRs:");
      firstModel.tactics.multi.slice(0, 3).forEach(tactic => {
        console.log(`- ${tactic.name} (multi): ${tactic.asr}%`);
      });
    }

    // Get all common tactics across models
    if (models.length > 0) {
      const commonTactics = models.reduce((common, model) => {
        const multiTacticNames = model.tactics.multi.map(t => t.name);
        const singleTacticNames = model.tactics.single.map(t => t.name);
        
        // Find tactics that appear in both multi and single
        return common.filter(tactic => 
          multiTacticNames.includes(tactic) && singleTacticNames.includes(tactic)
        );
      }, models[0].tactics.multi.map(t => t.name));

      console.log("\nCommon tactics (in both multi and single):", commonTactics);
    }

    // Output model performance comparison
    console.log("\nModel Performance Comparison (Average ASR%):");
    models.forEach(model => {
      const multiAvg = model.testCases.reduce((sum, tc) => sum + tc.multi, 0) / model.testCases.length;
      const singleAvg = model.testCases.reduce((sum, tc) => sum + tc.single, 0) / model.testCases.length;
      console.log(`- ${model.name}: Multi=${multiAvg.toFixed(1)}%, Single=${singleAvg.toFixed(1)}%`);
    });

    return models;
  } catch (error) {
    console.error("Error analyzing CSV file:", error);
    return [];
  }
}

// Function to analyze enhanced master data with model comparison information
async function analyzeEnhancedData(enhancedData) {
  try {
    console.log("Analyzing enhanced master data with model comparison information...");
    
    // Try to load the model_comparison.csv file for additional metadata
    let modelComparisonData = [];
    try {
      const comparisonContent = await fs.promises.readFile('model_comparison.csv', { encoding: 'utf8' });
      modelComparisonData = Papa.parse(comparisonContent, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true
      }).data;
      console.log(`Loaded model comparison data: ${modelComparisonData.length} models`);
    } catch (err) {
      console.warn("Could not load model_comparison.csv. Analysis will be limited.");
    }
    
    // Get unique models
    const modelNames = [...new Set(enhancedData.map(row => row.target_model))];
    console.log(`Found ${modelNames.length} unique models in the dataset`);
    
    // Calculate ASR for each model
    const modelASRs = modelNames.map(modelName => {
      const modelRows = enhancedData.filter(row => row.target_model === modelName);
      
      // Calculate average ASR
      let totalASR = 0;
      let validRows = 0;
      
      modelRows.forEach(row => {
        let asr = row.asr;
        if (typeof asr !== 'number' && row.scores) {
          // Parse scores and calculate ASR
          try {
            const scores = typeof row.scores === 'string' 
              ? JSON.parse(row.scores.replace(/'/g, '"')) 
              : row.scores;
              
            if (Array.isArray(scores)) {
              asr = scores.filter(score => score === 1).length / scores.length * 100;
              totalASR += asr;
              validRows++;
            }
          } catch (e) {
            console.warn(`Could not parse scores for ${modelName}`);
          }
        } else if (typeof asr === 'number') {
          totalASR += asr;
          validRows++;
        }
      });
      
      const avgASR = validRows > 0 ? totalASR / validRows : 0;
      
      // Find model in comparison data
      const modelInfo = modelComparisonData.find(model => 
        model.Model && modelName.includes(model.Model.toLowerCase())
      );
      
      return {
        name: modelName,
        asr: avgASR.toFixed(1),
        company: modelInfo ? modelInfo.Company : "Unknown",
        size: modelInfo ? modelInfo.Parameters : "Unknown",
        releaseDate: modelInfo ? modelInfo["Release Date"] : "Unknown"
      };
    });
    
    // Output by company
    console.log("\nASR by Company:");
    const companies = [...new Set(modelASRs.filter(m => m.company !== "Unknown").map(m => m.company))];
    companies.forEach(company => {
      const companyModels = modelASRs.filter(m => m.company === company);
      console.log(`\n${company}:`);
      companyModels.forEach(model => {
        console.log(`  - ${model.name}: ASR=${model.asr}%, Size=${model.size}B, Released: ${model.releaseDate}`);
      });
    });
    
    // Output by size range
    console.log("\nASR by Model Size:");
    const sizeRanges = [
      { name: "Small (<10B)", min: 0, max: 10 },
      { name: "Medium (10-30B)", min: 10, max: 30 },
      { name: "Large (30-100B)", min: 30, max: 100 },
      { name: "X-Large (>100B)", min: 100, max: Infinity }
    ];
    
    sizeRanges.forEach(range => {
      const rangeModels = modelASRs.filter(m => {
        const size = parseFloat(m.size);
        return !isNaN(size) && size >= range.min && size < range.max;
      });
      
      if (rangeModels.length > 0) {
        console.log(`\n${range.name}:`);
        rangeModels.forEach(model => {
          console.log(`  - ${model.name}: ASR=${model.asr}%, Company=${model.company}`);
        });
      }
    });
    
    // Output sorted by ASR
    console.log("\nModels Sorted by ASR (highest to lowest):");
    modelASRs
      .sort((a, b) => parseFloat(b.asr) - parseFloat(a.asr))
      .forEach((model, index) => {
        console.log(`${index + 1}. ${model.name} (${model.company}): ${model.asr}%`);
      });
  } catch (error) {
    console.error("Error analyzing enhanced data:", error);
  }
}

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

// Run the analysis
analyzeCSV(csvFilename).catch(error => {
  console.error("Fatal error:", error);
  process.exit(1);
});

// Export the analysis function for potential use by other modules
export { analyzeCSV };