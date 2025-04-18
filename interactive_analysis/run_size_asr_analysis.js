// run_size_asr_analysis.js
// Script to run the model size vs ASR analysis and save the results to a file

import fs from 'fs';
import Papa from 'papaparse';
import { analyzeModelSizeVsASR } from './test_case_model_size_analysis.js';

// Function to load CSV data
async function loadCSV(filePath) {
  try {
    const fileContent = fs.readFileSync(filePath, 'utf8');
    return new Promise((resolve, reject) => {
      Papa.parse(fileContent, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true,
        complete: (results) => {
          resolve(results.data);
        },
        error: (error) => {
          reject(error);
        }
      });
    });
  } catch (error) {
    console.error(`Error loading ${filePath}:`, error);
    throw error;
  }
}

// Main function
async function main() {
  try {
    console.log("Loading enhanced_master_data.csv...");
    const enhancedData = await loadCSV('./enhanced_master_data.csv');
    console.log(`Loaded ${enhancedData.length} rows from enhanced_master_data.csv`);

    console.log("Loading model_comparison.csv...");
    const modelComparisonData = await loadCSV('./model_comparison.csv');
    console.log(`Loaded ${modelComparisonData.length} rows from model_comparison.csv`);

    console.log("Running analysis...");
    const analysisResults = analyzeModelSizeVsASR(enhancedData, modelComparisonData);
    
    // Save the results
    console.log("Saving analysis results...");
    const outputPath = './size_asr_analysis_results.json';
    fs.writeFileSync(outputPath, JSON.stringify(analysisResults, null, 2));
    console.log(`Results saved to ${outputPath}`);

    // Print a summary of the findings
    console.log("\nAnalysis Summary:");
    console.log(`- Analyzed ${analysisResults.testCases.length} test cases`);
    console.log(`- Across ${analysisResults.labs.length} AI labs`);
    
    // Count how many have positive/negative correlations
    const correlations = {
      positive: 0,
      negative: 0,
      neutral: 0,
      missing: 0
    };
    
    let slopesFound = 0;
    let totalCells = 0;
    
    analysisResults.data.forEach(row => {
      analysisResults.labs.forEach(lab => {
        const value = row[lab];
        totalCells++;
        
        if (value === null) {
          correlations.missing++;
        } else if (value > 0.5) {
          correlations.positive++;
          slopesFound++;
        } else if (value < -0.5) {
          correlations.negative++;
          slopesFound++;
        } else {
          correlations.neutral++;
          slopesFound++;
        }
      });
    });
    
    console.log(`- Found slopes for ${slopesFound} out of ${totalCells} test case × lab combinations`);
    console.log(`- Strong negative correlations (larger models more resistant): ${correlations.negative}`);
    console.log(`- Strong positive correlations (larger models more vulnerable): ${correlations.positive}`);
    console.log(`- Neutral correlations (no clear trend): ${correlations.neutral}`);
    console.log(`- Missing data (not enough models to calculate): ${correlations.missing}`);
    
    // Find test cases with the strongest negative slopes (more resistant with size)
    const testCasesWithStrongestNegativeSlopes = [];
    analysisResults.data.forEach(row => {
      const slopes = [];
      analysisResults.labs.forEach(lab => {
        if (row[lab] !== null) {
          slopes.push(row[lab]);
        }
      });
      
      if (slopes.length > 0) {
        const avgSlope = slopes.reduce((sum, val) => sum + val, 0) / slopes.length;
        testCasesWithStrongestNegativeSlopes.push({
          testCase: row.testCase,
          avgSlope
        });
      }
    });
    
    // Sort by average slope (ascending to get most negative first)
    testCasesWithStrongestNegativeSlopes.sort((a, b) => a.avgSlope - b.avgSlope);
    
    console.log("\nTop 5 test cases where larger models show increased resistance:");
    testCasesWithStrongestNegativeSlopes.slice(0, 5).forEach((item, index) => {
      console.log(`${index + 1}. ${item.testCase} (Avg Slope: ${item.avgSlope.toFixed(2)})`);
    });
    
    console.log("\nTop 5 test cases where larger models show increased vulnerability:");
    testCasesWithStrongestNegativeSlopes.slice(-5).reverse().forEach((item, index) => {
      console.log(`${index + 1}. ${item.testCase} (Avg Slope: ${item.avgSlope.toFixed(2)})`);
    });
    
  } catch (error) {
    console.error("Error running analysis:", error);
  }
}

// Run the main function
main(); 