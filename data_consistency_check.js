const fs = require('fs');
const Papa = require('papaparse');

// Read and parse the CSV file
console.log('Reading master_results.csv...');
const csvFile = fs.readFileSync('./general_analysis/public/data/master_results.csv', 'utf8');

// Parse CSV
const parseResult = Papa.parse(csvFile, {
  header: true,
  dynamicTyping: true,
  skipEmptyLines: true
});

const data = parseResult.data;
console.log(`Parsed ${data.length} rows from master_results.csv`);

// Count rows with and without turn_type field
const rowsWithTurnType = data.filter(row => row.turn_type).length;
const rowsWithoutTurnType = data.length - rowsWithTurnType;
console.log(`Rows with turn_type: ${rowsWithTurnType} (${(rowsWithTurnType / data.length * 100).toFixed(2)}%)`);
console.log(`Rows without turn_type: ${rowsWithoutTurnType} (${(rowsWithoutTurnType / data.length * 100).toFixed(2)}%)`);

// Count rows with num_turns field
const rowsWithNumTurns = data.filter(row => row.num_turns).length;
const rowsWithSingleNumTurns = data.filter(row => row.num_turns === 1).length;
const rowsWithMultiNumTurns = data.filter(row => row.num_turns > 1).length;
console.log(`\nRows with num_turns: ${rowsWithNumTurns} (${(rowsWithNumTurns / data.length * 100).toFixed(2)}%)`);
console.log(`Rows with num_turns=1: ${rowsWithSingleNumTurns} (${(rowsWithSingleNumTurns / rowsWithNumTurns * 100).toFixed(2)}% of rows with num_turns)`);
console.log(`Rows with num_turns>1: ${rowsWithMultiNumTurns} (${(rowsWithMultiNumTurns / rowsWithNumTurns * 100).toFixed(2)}% of rows with num_turns)`);

// Check consistency between turn_type and num_turns
const rowsWithBothFields = data.filter(row => row.turn_type && row.num_turns);
console.log(`\nRows with both turn_type and num_turns: ${rowsWithBothFields.length}`);

// Analyze consistency
const consistentRows = rowsWithBothFields.filter(row => 
  (row.turn_type === 'single' && row.num_turns === 1) || 
  (row.turn_type === 'multi' && row.num_turns > 1)
);
const inconsistentRows = rowsWithBothFields.filter(row => 
  (row.turn_type === 'single' && row.num_turns > 1) || 
  (row.turn_type === 'multi' && row.num_turns === 1)
);

console.log(`Consistent rows: ${consistentRows.length} (${(consistentRows.length / rowsWithBothFields.length * 100).toFixed(2)}%)`);
console.log(`Inconsistent rows: ${inconsistentRows.length} (${(inconsistentRows.length / rowsWithBothFields.length * 100).toFixed(2)}%)`);

// Analyze by model
const modelStats = {};
data.forEach(row => {
  const modelName = row.target_model || row.model || 'unknown';
  
  if (!modelStats[modelName]) {
    modelStats[modelName] = {
      total: 0,
      withTurnType: 0,
      withNumTurns: 0,
      singleTurn: 0,
      multiTurn: 0,
      inconsistent: 0
    };
  }
  
  modelStats[modelName].total++;
  
  if (row.turn_type) {
    modelStats[modelName].withTurnType++;
    if (row.turn_type === 'single') {
      modelStats[modelName].singleTurn++;
    } else if (row.turn_type === 'multi') {
      modelStats[modelName].multiTurn++;
    }
  }
  
  if (row.num_turns) {
    modelStats[modelName].withNumTurns++;
  }
  
  // Check for inconsistency
  if (row.turn_type && row.num_turns) {
    if ((row.turn_type === 'single' && row.num_turns > 1) || 
        (row.turn_type === 'multi' && row.num_turns === 1)) {
      modelStats[modelName].inconsistent++;
    }
  }
});

// Display model-specific stats for models with issues
console.log('\n=== Model-specific Statistics ===');
console.log('Models with inconsistencies or missing data:');

Object.entries(modelStats)
  .filter(([_, stats]) => stats.inconsistent > 0 || stats.withTurnType === 0)
  .sort((a, b) => b[1].inconsistent - a[1].inconsistent)
  .forEach(([model, stats]) => {
    console.log(`\nModel: ${model}`);
    console.log(`  Total rows: ${stats.total}`);
    console.log(`  With turn_type: ${stats.withTurnType} (${(stats.withTurnType / stats.total * 100).toFixed(2)}%)`);
    console.log(`  With num_turns: ${stats.withNumTurns} (${(stats.withNumTurns / stats.total * 100).toFixed(2)}%)`);
    console.log(`  Single-turn: ${stats.singleTurn} (${(stats.singleTurn / stats.total * 100).toFixed(2)}%)`);
    console.log(`  Multi-turn: ${stats.multiTurn} (${(stats.multiTurn / stats.total * 100).toFixed(2)}%)`);
    console.log(`  Inconsistent: ${stats.inconsistent} (${(stats.inconsistent / stats.total * 100).toFixed(2)}%)`);
  });

// Analyze data usage patterns in components
console.log('\n=== Recommendations ===');
console.log(`1. ${rowsWithTurnType < data.length * 0.5 ? 'Many' : 'Some'} rows are missing turn_type. Consider inferring turn_type from num_turns when missing.`);
console.log(`2. ${inconsistentRows.length > 0 ? 'There are inconsistencies' : 'No inconsistencies'} between turn_type and num_turns fields.`);
console.log(`3. When filtering by turn type, prioritize using the turn_type field but fall back to num_turns for compatibility.`);
console.log('4. Debug your visualization components with the new debug tab to verify correct turn type filtering.'); 