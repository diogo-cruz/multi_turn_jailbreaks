// Simple script to check data formats in CSV files
const fs = require('fs');
const Papa = require('papaparse');

async function checkDataFormat() {
  try {
    console.log("Checking data formats...");
    
    // Load enhanced_master_data.csv
    console.log("\n--- LOADING ENHANCED MASTER DATA ---");
    const enhancedContent = await fs.promises.readFile('public/enhanced_master_data.csv', { encoding: 'utf8' });
    console.log(`File size: ${enhancedContent.length} bytes`);
    
    const enhancedData = Papa.parse(enhancedContent, {
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true
    }).data;
    
    console.log(`Parsed ${enhancedData.length} rows`);
    
    if (enhancedData.length > 0) {
      console.log("Sample headers:", Object.keys(enhancedData[0]));
      console.log("Sample row:", enhancedData[0]);
      
      // Check for target_model field
      if ('target_model' in enhancedData[0]) {
        console.log("\nTarget model exists and sample values:");
        console.log(enhancedData.slice(0, 5).map(row => row.target_model));
      } else {
        console.error("WARNING: target_model field not found!");
      }
      
      // Check for scores field
      if ('scores' in enhancedData[0]) {
        console.log("\nScores exist and sample values:");
        console.log(enhancedData.slice(0, 5).map(row => row.scores));
        
        // Check scores format
        console.log("\nScores data types:");
        enhancedData.slice(0, 5).forEach((row, idx) => {
          console.log(`Row ${idx}: ${typeof row.scores}, ${Array.isArray(row.scores) ? 'array' : 'not array'}`);
          
          // Try to parse if string
          if (typeof row.scores === 'string') {
            try {
              const parsed = JSON.parse(row.scores.replace(/'/g, '"'));
              console.log(`  - Can parse as JSON: ${Array.isArray(parsed)}`);
            } catch (e) {
              console.log(`  - Cannot parse as JSON: ${e.message}`);
            }
          }
        });
      } else {
        console.error("WARNING: scores field not found!");
      }
    }
    
    // Load model_comparison.csv
    console.log("\n--- LOADING MODEL COMPARISON DATA ---");
    const comparisonContent = await fs.promises.readFile('public/model_comparison.csv', { encoding: 'utf8' });
    console.log(`File size: ${comparisonContent.length} bytes`);
    
    const comparisonData = Papa.parse(comparisonContent, {
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true
    }).data;
    
    console.log(`Parsed ${comparisonData.length} rows`);
    
    if (comparisonData.length > 0) {
      console.log("Sample headers:", Object.keys(comparisonData[0]));
      console.log("Sample row:", comparisonData[0]);
      
      // Check for Model field
      if ('Model' in comparisonData[0]) {
        console.log("\nModel names exist and sample values:");
        console.log(comparisonData.slice(0, 5).map(row => row.Model));
      } else {
        console.error("WARNING: Model field not found!");
      }
      
      // Check for Company field
      if ('Company' in comparisonData[0]) {
        console.log("\nCompanies exist and sample values:");
        console.log(comparisonData.slice(0, 5).map(row => row.Company));
      } else {
        console.error("WARNING: Company field not found!");
      }
      
      // Check for Parameters field
      if ('Parameters' in comparisonData[0]) {
        console.log("\nParameters exist and sample values:");
        console.log(comparisonData.slice(0, 5).map(row => row.Parameters));
      } else {
        console.error("WARNING: Parameters field not found!");
      }
    }
    
    // Check for matches between the datasets
    if (enhancedData.length > 0 && comparisonData.length > 0 && 'target_model' in enhancedData[0] && 'Model' in comparisonData[0]) {
      console.log("\n--- CHECKING FOR MATCHES BETWEEN DATASETS ---");
      
      let matchCount = 0;
      const uniqueTargetModels = [...new Set(enhancedData.map(row => row.target_model))];
      
      console.log(`Found ${uniqueTargetModels.length} unique target models`);
      
      uniqueTargetModels.forEach(targetModel => {
        // Try direct match
        let match = comparisonData.find(row => 
          row.Model && targetModel.toLowerCase().includes(row.Model.toLowerCase())
        );
        
        if (!match) {
          // Try reverse match
          match = comparisonData.find(row => 
            row.Model && row.Model.toLowerCase().includes(targetModel.toLowerCase())
          );
        }
        
        if (match) {
          matchCount++;
          console.log(`Match found: ${targetModel} => ${match.Model} (${match.Company}, ${match.Parameters}B)`);
        } else {
          console.error(`No match found for: ${targetModel}`);
        }
      });
      
      console.log(`\nMatched ${matchCount} out of ${uniqueTargetModels.length} models (${Math.round(matchCount / uniqueTargetModels.length * 100)}%)`);
    }
    
  } catch (err) {
    console.error("Error checking data:", err);
  }
}

// Run the check
checkDataFormat().catch(err => {
  console.error("Fatal error:", err);
}); 