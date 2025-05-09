import React, { useState, useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, LabelList, ScatterChart, Scatter, ZAxis
} from 'recharts';

// Color constants
const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE', 
  '#00C49F', '#FFBB28', '#FF8042', '#a4de6c', '#d0ed57'
];

const EvaluatorCorrelationAnalysis = ({ data }) => {
  const [correlationData, setCorrelationData] = useState([]);
  const [hasMultipleEvaluators, setHasMultipleEvaluators] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  
  // Extract and process evaluator data
  const processedData = useMemo(() => {
    if (!data || (Array.isArray(data) && data.length === 0)) {
      return { uniqueEvaluators: [], hasData: false };
    }
    
    // Extract unique evaluator models
    const evaluatorSet = new Set();
    
    // Process data based on format
    if (Array.isArray(data) && data[0] && data[0].name) {
      // Already processed models array with evaluator data
      for (const model of data) {
        if (model.evaluators) {
          for (const evaluator of model.evaluators) {
            if (evaluator.name) {
              evaluatorSet.add(evaluator.name);
            }
          }
        }
      }
    } else {
      // Raw data rows
      for (const row of data) {
        if (row.evaluator_model) {
          // Extract the actual model name from file paths or full names
          let modelName = row.evaluator_model;
          
          // Handle paths like "command_X_gpt-4o-mini..." or "eval_gpt-4.1-nano"
          if (modelName.includes('gpt-') || modelName.includes('claude-') || 
              modelName.includes('openai/') || modelName.includes('anthropic/')) {
            
            // Extract model name if it's in a filename
            if (modelName.includes('.jsonl')) {
              // Look for common model prefixes in the filename
              const modelPrefixes = ['gpt-', 'claude-', 'openai/', 'anthropic/'];
              for (const prefix of modelPrefixes) {
                if (modelName.includes(prefix)) {
                  const startIdx = modelName.indexOf(prefix);
                  let endIdx = modelName.indexOf('_', startIdx);
                  if (endIdx === -1) {
                    endIdx = modelName.indexOf('.', startIdx);
                  }
                  if (endIdx === -1) {
                    endIdx = modelName.length;
                  }
                  modelName = modelName.substring(startIdx, endIdx);
                  break;
                }
              }
              
              // If there's an "eval_" marker, extract the evaluator model instead
              if (modelName.includes('eval_')) {
                const evalPart = modelName.split('eval_')[1];
                modelName = evalPart;
              }
            }
            
            evaluatorSet.add(modelName);
          } else {
            evaluatorSet.add(modelName);
          }
        }
      }
    }
    
    const uniqueEvaluators = [...evaluatorSet];
    
    if (uniqueEvaluators.length >= 2) {
      // Find experiment runs that differ only by evaluator model
      const runsByParameters = {};
      
      if (Array.isArray(data) && data[0] && data[0].name) {
        // Process structured data 
        // This would require more context about how evaluators are structured in the processed data
        // For now, focus on the raw data format which is more straightforward
      } else {
        // Process raw data rows
        data.forEach(row => {
          if (!row.evaluator_model) return;
          
          // Create a key based only on the specified parameters
          const key = `${row.jailbreak_tactic || ''}_${row.test_case || ''}_${row.turn_type || ''}_${row.target_model || row.model || ''}_${row.target_temp || ''}_${row.max_round || ''}_${row.attacker_model || ''}`;
          
          // Normalize the evaluator model name for the sub-key
          let evalKey = row.evaluator_model || 'unknown';
          
          // Extract the actual model name from file paths or full names
          if (evalKey.includes('gpt-') || evalKey.includes('claude-') || 
              evalKey.includes('openai/') || evalKey.includes('anthropic/')) {
            
            // Extract model name if it's in a filename
            if (evalKey.includes('.jsonl')) {
              // Look for common model prefixes in the filename
              const modelPrefixes = ['gpt-', 'claude-', 'openai/', 'anthropic/'];
              for (const prefix of modelPrefixes) {
                if (evalKey.includes(prefix)) {
                  const startIdx = evalKey.indexOf(prefix);
                  let endIdx = evalKey.indexOf('_', startIdx);
                  if (endIdx === -1) {
                    endIdx = evalKey.indexOf('.', startIdx);
                  }
                  if (endIdx === -1) {
                    endIdx = evalKey.length;
                  }
                  evalKey = evalKey.substring(startIdx, endIdx);
                  break;
                }
              }
              
              // If there's an "eval_" marker, extract the evaluator model instead
              if (evalKey.includes('eval_')) {
                const evalPart = evalKey.split('eval_')[1];
                evalKey = evalPart;
              }
            }
          }
          
          if (!runsByParameters[key]) {
            runsByParameters[key] = {};
          }
          
          // Only store the first row for each evaluator
          if (!runsByParameters[key][evalKey]) {
            runsByParameters[key][evalKey] = row;
          }
        });
      }
      
      // Filter for parameter sets that have multiple evaluators
      const multiEvaluatorRuns = Object.entries(runsByParameters)
        .filter(([_, evaluatorMap]) => Object.keys(evaluatorMap).length > 1)
        .map(([_, evaluatorMap]) => Object.values(evaluatorMap));
      
      if (multiEvaluatorRuns.length > 0) {
        // Calculate correlation data between pairs of evaluators
        const evaluatorPairs = {};
        const totalPairs = {};
        const agreementCounts = {};
        
        multiEvaluatorRuns.forEach(runs => {
          // Group by evaluator
          const evaluatorResults = {};
          
          runs.forEach(run => {
            // Primary: Use the last score from the scores array if available
            let scoreValue = null;
            
            // Normalize the evaluator model name for consistent keys
            let evalKey = run.evaluator_model || 'unknown';
            
            // Extract the actual model name from file paths or full names
            if (evalKey.includes('gpt-') || evalKey.includes('claude-') || 
                evalKey.includes('openai/') || evalKey.includes('anthropic/')) {
              
              // Extract model name if it's in a filename
              if (evalKey.includes('.jsonl')) {
                // Look for common model prefixes in the filename
                const modelPrefixes = ['gpt-', 'claude-', 'openai/', 'anthropic/'];
                for (const prefix of modelPrefixes) {
                  if (evalKey.includes(prefix)) {
                    const startIdx = evalKey.indexOf(prefix);
                    let endIdx = evalKey.indexOf('_', startIdx);
                    if (endIdx === -1) {
                      endIdx = evalKey.indexOf('.', startIdx);
                    }
                    if (endIdx === -1) {
                      endIdx = evalKey.length;
                    }
                    evalKey = evalKey.substring(startIdx, endIdx);
                    break;
                  }
                }
                
                // If there's an "eval_" marker, extract the evaluator model instead
                if (evalKey.includes('eval_')) {
                  const evalPart = evalKey.split('eval_')[1];
                  evalKey = evalPart;
                }
              }
            }
            
            if (run.scores) {
              let scoresList = [];
              
              // Handle scores that might be stored as a string
              if (typeof run.scores === 'string') {
                try {
                  // Remove any surrounding quotes and clean the string
                  const cleanedScores = run.scores.replace(/^['"]|['"]$/g, '')
                    .replace(/\\/g, '')
                    .trim();
                  
                  // Try to parse as JSON
                  scoresList = JSON.parse(cleanedScores);
                } catch (e) {
                  // If parsing fails, check for comma-separated format
                  const commaSeparated = run.scores.split(',').map(s => parseFloat(s.trim()));
                  if (!isNaN(commaSeparated[0])) {
                    scoresList = commaSeparated;
                  }
                }
              } else if (Array.isArray(run.scores)) {
                scoresList = run.scores;
              }
              
              // Get the last non-zero score if available
              for (let i = scoresList.length - 1; i >= 0; i--) {
                if (scoresList[i] && !isNaN(scoresList[i]) && scoresList[i] > 0) {
                  scoreValue = scoresList[i];
                  break;
                }
              }
              
              // If no non-zero score found, use the last score
              if (scoreValue === null && scoresList.length > 0) {
                scoreValue = scoresList[scoresList.length - 1];
              }
              
              // Store the entire score progression for more detailed analysis
              evaluatorResults[evalKey] = {
                finalScore: scoreValue,
                scoreProgression: scoresList,
                // Also keep binary success as a fallback
                binarySuccess: run.goal_achieved === true || 
                  run.goal_achieved === 'true' || run.goal_achieved === 1 || 
                  run.success === true || run.success === 'true' || run.success === 1
              };
            } else {
              // Fallback to binary if no scores are available
              evaluatorResults[evalKey] = {
                finalScore: null,
                scoreProgression: [],
                binarySuccess: run.goal_achieved === true || 
                  run.goal_achieved === 'true' || run.goal_achieved === 1 || 
                  run.success === true || run.success === 'true' || run.success === 1
              };
            }
          });
          
          // Compare each pair of evaluators
          const evaluators = Object.keys(evaluatorResults);
          for (let i = 0; i < evaluators.length; i++) {
            for (let j = i + 1; j < evaluators.length; j++) {
              const evalA = evaluators[i];
              const evalB = evaluators[j];
              const pairKey = [evalA, evalB].sort().join('_vs_');
              
              if (!totalPairs[pairKey]) {
                totalPairs[pairKey] = 0;
                agreementCounts[pairKey] = 0;
                evaluatorPairs[pairKey] = { 
                  evalA, 
                  evalB,
                  scoreDiffs: [], // Track score differences for statistical analysis
                  binaryAgreements: 0,
                  binaryTotal: 0
                };
              }
              
              totalPairs[pairKey]++;
              
              const resultA = evaluatorResults[evalA];
              const resultB = evaluatorResults[evalB];
              
              // Track binary agreement as a secondary metric
              evaluatorPairs[pairKey].binaryTotal++;
              if (resultA.binarySuccess === resultB.binarySuccess) {
                evaluatorPairs[pairKey].binaryAgreements++;
              }
              
              // If both have valid scores, compare the score values
              if (resultA.finalScore !== null && resultB.finalScore !== null) {
                // Calculate absolute difference between scores
                const scoreDiff = Math.abs(resultA.finalScore - resultB.finalScore);
                
                // Store the difference for later analysis
                evaluatorPairs[pairKey].scoreDiffs.push(scoreDiff);
                
                // Consider scores "in agreement" if they're within 0.2 of each other
                if (scoreDiff <= 0.2) {
                  agreementCounts[pairKey]++;
                }
              } else {
                // If scores aren't available, fall back to binary success
                if (resultA.binarySuccess === resultB.binarySuccess) {
                  agreementCounts[pairKey]++;
                }
              }
            }
          }
        });
        
        // Calculate correlation percentages and prepare chart data
        const correlationResults = Object.keys(totalPairs).map(pairKey => {
          const { evalA, evalB, scoreDiffs, binaryAgreements, binaryTotal } = evaluatorPairs[pairKey];
          const total = totalPairs[pairKey];
          const agreements = agreementCounts[pairKey];
          
          // Calculate agreement percentage
          const agreementPct = total > 0 ? (agreements / total) * 100 : 0;
          
          // Calculate binary agreement percentage as a fallback/additional metric
          const binaryAgreementPct = binaryTotal > 0 ? (binaryAgreements / binaryTotal) * 100 : 0;
          
          // Calculate mean score difference if score data is available
          const meanScoreDiff = scoreDiffs.length > 0 
            ? scoreDiffs.reduce((sum, diff) => sum + diff, 0) / scoreDiffs.length 
            : null;
          
          return {
            pairKey,
            evalA,
            evalB,
            agreementPct,
            binaryAgreementPct,
            meanScoreDiff,
            sampleCount: total,
            label: `${evalA} vs ${evalB}`
          };
        });
        
        // Sort by agreement percentage
        correlationResults.sort((a, b) => b.agreementPct - a.agreementPct);
        
        setCorrelationData(correlationResults);
        setHasMultipleEvaluators(true);
      } else {
        setHasMultipleEvaluators(false);
      }
    } else {
      setHasMultipleEvaluators(false);
    }
    
    return { 
      uniqueEvaluators, 
      hasData: uniqueEvaluators.length > 0 
    };
  }, [data]);
  
  // Toggle showing detailed data
  const toggleDetails = () => {
    setShowDetails(!showDetails);
  };
  
  // Render evaluator correlation chart
  const renderCorrelationChart = () => {
    if (!hasMultipleEvaluators || correlationData.length === 0) {
      return (
        <div className="p-4 bg-yellow-50 text-yellow-800 rounded">
          No correlation data available. This analysis requires multiple evaluator models judging the same examples.
        </div>
      );
    }
    
    return (
      <div className="chart-container">
        <h3 className="text-lg font-medium mb-2">Evaluator Agreement Rates</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart
            data={correlationData}
            margin={{ top: 20, right: 30, left: 30, bottom: 100 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="label" 
              angle={-45} 
              textAnchor="end"
              height={100}
              interval={0}
            />
            <YAxis 
              label={{ value: 'Agreement Rate (%)', angle: -90, position: 'insideLeft' }}
              domain={[0, 100]}
            />
            <Tooltip 
              formatter={(value, name) => {
                if (name === 'agreementPct') return [`${value.toFixed(2)}%`, 'Agreement Rate'];
                return [value, name];
              }}
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white p-2 border rounded shadow">
                      <p className="font-medium">{data.evalA} vs {data.evalB}</p>
                      <p>Agreement Rate: {data.agreementPct.toFixed(2)}%</p>
                      <p>Binary Agreement: {data.binaryAgreementPct.toFixed(2)}%</p>
                      {data.meanScoreDiff !== null && (
                        <p>Mean Score Difference: {data.meanScoreDiff.toFixed(3)}</p>
                      )}
                      <p>Sample Count: {data.sampleCount}</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend />
            <Bar dataKey="agreementPct" fill="#8884d8" name="Agreement Rate (%)">
              <LabelList 
                dataKey="sampleCount" 
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
              {correlationData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };
  
  // Render detailed data table
  const renderDetailedTable = () => {
    if (!showDetails || !hasMultipleEvaluators || correlationData.length === 0) {
      return null;
    }
    
    return (
      <div className="mt-6 overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Evaluator Pair
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Agreement Rate
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Binary Agreement
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Mean Score Diff
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Sample Count
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {correlationData.map((item, index) => (
              <tr key={item.pairKey} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {item.evalA} vs {item.evalB}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {item.agreementPct.toFixed(2)}%
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {item.binaryAgreementPct.toFixed(2)}%
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {item.meanScoreDiff !== null ? item.meanScoreDiff.toFixed(3) : 'N/A'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {item.sampleCount}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };
  
  // Render key insights
  const renderKeyInsights = () => {
    if (!hasMultipleEvaluators || correlationData.length === 0) {
      return null;
    }
    
    // Find highest and lowest agreement pairs
    const highestAgreement = correlationData[0];
    const lowestAgreement = correlationData[correlationData.length - 1];
    
    // Calculate average agreement rate
    const avgAgreement = correlationData.reduce((sum, item) => sum + item.agreementPct, 0) / correlationData.length;
    
    return (
      <div className="mt-6 p-4 bg-blue-50 rounded">
        <h3 className="text-md font-medium mb-2">Key Insights</h3>
        <ul className="list-disc pl-5 text-sm space-y-2">
          <li>This analysis examines how different evaluator models assess the same prompts.</li>
          <li>Higher agreement rates indicate similar judgments between evaluators.</li>
          <li>Average agreement rate across all evaluator pairs: <strong>{avgAgreement.toFixed(1)}%</strong></li>
          {highestAgreement && (
            <li>Highest agreement: <strong>{highestAgreement.evalA}</strong> vs <strong>{highestAgreement.evalB}</strong> ({highestAgreement.agreementPct.toFixed(1)}%)</li>
          )}
          {lowestAgreement && (
            <li>Lowest agreement: <strong>{lowestAgreement.evalA}</strong> vs <strong>{lowestAgreement.evalB}</strong> ({lowestAgreement.agreementPct.toFixed(1)}%)</li>
          )}
          <li>Click "Show Detailed Data" for more information about each evaluator pair.</li>
        </ul>
      </div>
    );
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">Evaluator Correlation Analysis</h2>
        <p className="text-gray-600">
          This section analyzes how different evaluator models judge the same experiments.
          Higher correlation values indicate similar judgments.
        </p>
      </div>
      
      {!processedData.hasData ? (
        <div className="p-6 bg-gray-100 rounded text-center">
          <p className="text-lg">
            No evaluator data available. This analysis requires data with an 'evaluator_model' column.
          </p>
        </div>
      ) : !hasMultipleEvaluators ? (
        <div className="p-6 bg-yellow-100 rounded border-l-4 border-yellow-500 pl-4">
          <h3 className="text-lg font-medium mb-2">Insufficient Data</h3>
          <p>
            At least two different evaluator models are required for correlation analysis. 
            The current dataset contains only {processedData.uniqueEvaluators.length} evaluator model(s).
          </p>
          <p className="mt-2">
            Available evaluator(s): {processedData.uniqueEvaluators.map(e => e || 'Unknown').join(', ')}
          </p>
        </div>
      ) : (
        <div className="flex flex-wrap -mx-2">
          <div className="w-full md:w-1/4 px-2">
            <div className="mb-4">
              <button
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                onClick={toggleDetails}
              >
                {showDetails ? 'Hide Detailed Data' : 'Show Detailed Data'}
              </button>
            </div>
            {renderKeyInsights()}
          </div>
          
          <div className="w-full md:w-3/4 px-2">
            {renderCorrelationChart()}
            {renderDetailedTable()}
          </div>
        </div>
      )}
    </div>
  );
};

export default EvaluatorCorrelationAnalysis; 