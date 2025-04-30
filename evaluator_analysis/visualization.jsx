import React, { useState, useEffect, useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, LabelList, LineChart, Line, ScatterChart, Scatter, ZAxis, ErrorBar,
  PieChart, Pie, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ComposedChart, Area
} from 'recharts';
import Papa from 'papaparse';

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
    ':hover': {
      color: '#374151',
    }
  },
  filterContainer: {
    display: 'flex', 
    flexWrap: 'wrap', 
    gap: '1rem', 
    marginBottom: '1.5rem',
    padding: '1rem',
    backgroundColor: '#f9fafb',
    borderRadius: '0.5rem',
    boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)'
  },
  filterItem: {
    display: 'flex',
    flexDirection: 'column',
    minWidth: '200px'
  },
  select: {
    padding: '0.5rem',
    borderRadius: '0.25rem',
    border: '1px solid #d1d5db',
    marginTop: '0.25rem'
  },
  chartContainer: {
    marginTop: '2rem',
    padding: '1rem',
    backgroundColor: 'white',
    borderRadius: '0.5rem',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
  }
};

// Color schemes similar to interactive_analysis
const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE', 
  '#00C49F', '#FFBB28', '#FF8042', '#a4de6c', '#d0ed57'
];

// Model parameter sizes (in billions) - similar to interactive_analysis
const MODEL_SIZES = {
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
  'anthropic/claude-3.5-sonnet': 18,
  'anthropic/claude-3.7-sonnet': 45,
  'openai/gpt-4o': 300,
  'openai/gpt-4.1': 240,
  'openai/gpt-4.1-mini': 24,
  'openai/gpt-4.1-nano': 8,
  'google/gemini-2.5-pro-preview-03-25': 120,
  'google/gemini-2.5-flash-preview': 35,
  'qwen/qwen-2.5-7b-instruct': 7,
  'qwen/qwen-2.5-72b-instruct': 72,
  'mistralai/mistral-7b-instruct-v0.3': 7,
  'mistralai/mistral-small-3.1-24b-instruct': 24,
  'mistralai/mistral-tiny': 3,
  'mistralai/mistral-nemo': 12,
  'meta-llama/llama-4-scout': 8,
  'meta-llama/llama-4-maverick': 44,
  'deepseek/deepseek-chat-v3-0324': 16,
  'mistral-large-latest': 42,
  'claude-3-sonnet': 45,
  'claude-3-opus': 145
};

// Main component for evaluator visualization
const EvaluatorViz = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uniqueModels, setUniqueModels] = useState([]);
  const [uniqueTestCases, setUniqueTestCases] = useState([]);
  const [uniqueTactics, setUniqueTactics] = useState([]);
  const [uniqueAttackers, setUniqueAttackers] = useState([]);
  const [uniqueEvaluators, setUniqueEvaluators] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [selectedTestCase, setSelectedTestCase] = useState(null);
  const [selectedTactic, setSelectedTactic] = useState(null);
  const [selectedAttacker, setSelectedAttacker] = useState(null);
  const [selectedEvaluator, setSelectedEvaluator] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [chartType, setChartType] = useState("bar");
  const [sortBy, setSortBy] = useState("success");
  const [showDetails, setShowDetails] = useState(false);
  const [heatmapData, setHeatmapData] = useState(null);
  const [dataLoadingStatus, setDataLoadingStatus] = useState('pending');

  // Load and process the data
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setDataLoadingStatus('loading');
        console.log("Starting data loading process...");
        
        // Fetch the CSV file
        const response = await fetch('/master_results.csv');
        if (!response.ok) {
          // If master_results.csv fails, try the sample file
          const sampleResponse = await fetch('/sample_results.csv');
          if (!sampleResponse.ok) {
            throw new Error(`Failed to fetch CSV files. Master: ${response.status}, Sample: ${sampleResponse.status}`);
          }
          console.log("Using sample_results.csv for testing");
          return await processCSV(sampleResponse);
        }
        
        console.log("Using master_results.csv");
        return await processCSV(response);
        
      } catch (error) {
        console.error("Error loading data:", error);
        setError(error.message);
        setDataLoadingStatus('error');
        setLoading(false);
      }
    };
    
    const processCSV = async (response) => {
      try {
        const fileContent = await response.text();
        console.log(`CSV content fetched, length: ${fileContent.length} bytes`);
        
        if (!fileContent || fileContent.length === 0) {
          throw new Error('Empty CSV file or failed to load');
        }
        
        setDataLoadingStatus('parsing');
        
        // Parse the CSV file with more options for the complex format
        let parsedData = [];
        try {
          parsedData = Papa.parse(fileContent, {
            header: true,
            dynamicTyping: true,
            skipEmptyLines: true,
            comments: "#",
            delimitersToGuess: [',', '\t', '|', ';'],
            complete: function(results) {
              console.log("Parsing complete:", results.data.length, "rows");
              if (results.data.length > 0) {
                console.log("Sample row:", results.data[0]);
                console.log("Column names:", results.meta.fields);
              } else {
                console.warn("No data rows found in CSV");
              }
              
              if (results.errors && results.errors.length > 0) {
                console.warn("CSV parsing had some errors:", results.errors);
              }
            },
            error: function(error) {
              console.error("Error parsing CSV:", error);
              setError("CSV parsing error: " + error.message);
            }
          }).data;
        } catch (parseError) {
          console.error("Exception during CSV parsing:", parseError);
          throw new Error(`CSV parsing failed: ${parseError.message}`);
        }
        
        console.log("Parsed data rows:", parsedData.length);
        setDataLoadingStatus('processing');
        
        // Clean up the data and handle any inconsistencies
        const cleanedData = parsedData
          .filter(row => {
            const isValid = row && 
                          ((row.target_model && row.test_case) || 
                           (row.model && row.test_case) ||
                           (row["Unnamed: 0"] !== undefined)); // Handle special case with unnamed column
            
            if (!isValid) {
              console.warn("Filtered out incomplete row:", row);
            }
            return isValid;
          })
          .map(row => {
            try {
              // Handle the case where we have "Unnamed: 0" as the first column
              if (row["Unnamed: 0"] !== undefined) {
                // Make sure required fields exist
                row.target_model = row.target_model || "Unknown Model";
                row.test_case = row.test_case || "Unknown Test Case";
                row.jailbreak_tactic = row.jailbreak_tactic || "Unknown Tactic";
              }
              
              // Parse scores if they're stored as a string
              if (row.scores && typeof row.scores === 'string') {
                try {
                  // Handle various formats of the scores field
                  const scoresStr = row.scores
                    .replace(/'/g, '"')
                    .replace(/\n/g, ' '); // Remove newlines that might break JSON parsing
                  
                  row.scores = JSON.parse(scoresStr);
                } catch (e) {
                  console.error("Error parsing scores:", e, "Original value:", row.scores);
                  row.scores = [];
                }
              }
              
              // Convert goal_achieved to boolean if necessary
              if (row.goal_achieved !== undefined) {
                if (typeof row.goal_achieved === 'string') {
                  row.goal_achieved = row.goal_achieved.toLowerCase() === 'true';
                } else {
                  row.goal_achieved = Boolean(row.goal_achieved);
                }
              }
              
              // Set success property for consistency
              row.success = row.goal_achieved;
              
              // Handle various data formats - set model field for consistent access
              row.model = row.target_model || row.model;
              row.prompt_path = row.source_file || row.batch || '';
              
              return row;
            } catch (rowError) {
              console.error("Error processing row:", row, rowError);
              return row; // Return original row to avoid filtering
            }
          });
        
        console.log("Cleaned data:", cleanedData.length, "rows");
        setData(cleanedData);
        
        setDataLoadingStatus('extracting_values');
        
        // Extract unique values 
        const models = [...new Set(cleanedData.map(row => row.model))].filter(Boolean);
        const testCases = [...new Set(cleanedData.map(row => row.test_case))].filter(Boolean);
        const tactics = [...new Set(cleanedData.map(row => row.jailbreak_tactic))].filter(Boolean);
        const attackers = [...new Set(cleanedData.map(row => row.attacker_model))].filter(Boolean);
        const evaluators = [...new Set(cleanedData.map(row => row.evaluator_model))].filter(Boolean);
        
        console.log("Unique values extracted:", {
          models: models.length,
          testCases: testCases.length,
          tactics: tactics.length,
          attackers: attackers.length,
          evaluators: evaluators.length
        });
        
        setUniqueModels(models);
        setUniqueTestCases(testCases);
        setUniqueTactics(tactics);
        setUniqueAttackers(attackers);
        setUniqueEvaluators(evaluators);
        
        setDataLoadingStatus('complete');
        setLoading(false);
        console.log("Data loading complete");
      } catch (error) {
        console.error("Error processing CSV:", error);
        throw error;
      }
    };
    
    loadData();
  }, []);
  
  // Generate heatmap data when data changes
  useEffect(() => {
    try {
      if (data.length > 0 && uniqueTestCases.length > 0 && uniqueTactics.length > 0) {
        console.log("Generating heatmap data...");
        console.log("Data points:", data.length);
        console.log("Test cases:", uniqueTestCases.length);
        console.log("Tactics:", uniqueTactics.length);
        
        const heatmapResult = generateHeatmapData(data, uniqueTestCases, uniqueTactics);
        if (heatmapResult) {
          console.log("Heatmap data generated:", heatmapResult.length, "data points");
          setHeatmapData(heatmapResult);
        } else {
          console.error("Failed to generate heatmap data: result is null or undefined");
        }
      } else {
        console.warn("Not generating heatmap data: missing data, test cases, or tactics");
        console.log("Data points:", data.length);
        console.log("Test cases:", uniqueTestCases.length);
        console.log("Tactics:", uniqueTactics.length);
      }
    } catch (error) {
      console.error("Error generating heatmap data:", error);
    }
  }, [data, uniqueTestCases, uniqueTactics]);

  // Generate heatmap data for test cases and tactics
  const generateHeatmapData = (data, testCases, tactics) => {
    if (!data || data.length === 0 || !testCases || !tactics) {
      console.warn("Missing data for heatmap generation", { 
        dataLength: data?.length, 
        testCasesLength: testCases?.length, 
        tacticsLength: tactics?.length 
      });
      return [];
    }
    
    console.log("Starting heatmap data generation with:", {
      dataPoints: data.length,
      testCases: testCases.length,
      tactics: tactics.length
    });
    
    const heatmapData = [];
    
    // Check for required fields in the data
    const sampleData = data.slice(0, 5);
    console.log("Sample data for heatmap:", sampleData);
    
    // Iterate over all test cases and tactics
    testCases.forEach(testCase => {
      if (!testCase) {
        console.warn("Skipping undefined or null test case");
        return;
      }
      
      tactics.forEach(tactic => {
        if (!tactic) {
          console.warn("Skipping undefined or null tactic");
          return;
        }
        
        try {
          // Filter data for this test case and tactic
          const filteredData = data.filter(row => {
            return row && 
                  row.test_case === testCase && 
                  row.jailbreak_tactic === tactic;
          });
          
          if (filteredData.length > 0) {
            // Calculate success rate
            const successCount = filteredData.filter(row => {
              // Handle different success field formats
              return row.success === true || 
                    row.success === 1 || 
                    row.goal_achieved === true || 
                    row.goal_achieved === 1;
            }).length;
            
            const successRate = (successCount / filteredData.length) * 100;
            
            heatmapData.push({
              testCase,
              tactic,
              count: filteredData.length,
              successRate: Number(successRate.toFixed(2)),
              successCount
            });
          } else {
            // No data for this combination
            heatmapData.push({
              testCase,
              tactic,
              count: 0,
              successRate: 0,
              successCount: 0
            });
          }
        } catch (error) {
          console.error(`Error processing heatmap data for ${testCase}/${tactic}:`, error);
          // Add empty data to prevent visualization errors
          heatmapData.push({
            testCase,
            tactic,
            count: 0,
            successRate: 0,
            successCount: 0
          });
        }
      });
    });
    
    console.log(`Heatmap data generated with ${heatmapData.length} entries`);
    if (heatmapData.length > 0) {
      console.log("Sample heatmap entry:", heatmapData[0]);
    }
    
    return heatmapData;
  };

  // Filter data based on selections
  const filteredData = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    return data.filter(row => {
      const modelMatch = !selectedModel || row.model === selectedModel;
      const testCaseMatch = !selectedTestCase || row.test_case === selectedTestCase;
      const tacticMatch = !selectedTactic || row.jailbreak_tactic === selectedTactic;
      
      return modelMatch && testCaseMatch && tacticMatch;
    });
  }, [data, selectedModel, selectedTestCase, selectedTactic]);

  // Heatmap color scale component
  const ColorScale = ({ title, min, max, colorRamp }) => {
    const gradientId = `${title.replace(/\s+/g, '')}-gradient`;
    
    return (
      <div style={{ marginBottom: '20px' }}>
        <h4 style={{ margin: '0 0 5px' }}>{title}</h4>
        <div style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          <div style={{ width: '200px', height: '20px', position: 'relative' }}>
            <svg width="200" height="20">
              <defs>
                <linearGradient id={gradientId} x1="0%" x2="100%" y1="0%" y2="0%">
                  {colorRamp.map((color, i) => (
                    <stop 
                      key={i} 
                      offset={`${(i/(colorRamp.length-1))*100}%`} 
                      stopColor={color} 
                    />
                  ))}
                </linearGradient>
              </defs>
              <rect x="0" y="0" width="200" height="20" fill={`url(#${gradientId})`} />
            </svg>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', width: '200px', marginLeft: '5px' }}>
            <span>{min}</span>
            <span>{max}</span>
          </div>
        </div>
      </div>
    );
  };

  // HeatMap component
  const HeatMap = ({ data, testCases, tactics, title, colorRamp }) => {
    if (!data || !Array.isArray(data) || data.length === 0 || 
        !testCases || !Array.isArray(testCases) || testCases.length === 0 || 
        !tactics || !Array.isArray(tactics) || tactics.length === 0) {
      return (
        <div style={{ 
          padding: '2rem', 
          backgroundColor: '#f9fafb', 
          borderRadius: '0.5rem',
          textAlign: 'center' 
        }}>
          <p>No data available for heatmap visualization</p>
          <p style={{ fontSize: '0.875rem', color: '#6b7280' }}>
            Ensure that test cases and tactics are present in the dataset
          </p>
        </div>
      );
    }
    
    // Get color scale function
    const getColor = (value, min, max) => {
      if (value === 0 || isNaN(value)) return '#f0f0f0'; // No data
      
      // Default color ramp
      const colors = colorRamp || [
        '#e6f0ff', '#b3d1ff', '#80b3ff', '#4d94ff', '#1a75ff', 
        '#0066ff', '#0047b3', '#003366', '#002147', '#001429'
      ];
      
      try {
        const normalizedValue = Math.min(Math.max((value - min) / (max - min), 0), 1);
        const index = Math.floor(normalizedValue * (colors.length - 1));
        return colors[Math.max(0, Math.min(index, colors.length - 1))];
      } catch (error) {
        console.error("Error calculating color:", error);
        return '#f0f0f0'; // Fallback color
      }
    };
    
    // Find min and max success rates
    const values = data
      .map(item => item.successRate)
      .filter(rate => !isNaN(rate) && rate > 0);
    
    if (values.length === 0) {
      return (
        <div style={{ 
          padding: '2rem', 
          backgroundColor: '#f9fafb', 
          borderRadius: '0.5rem',
          textAlign: 'center' 
        }}>
          <p>Cannot generate heatmap: no success rate data available</p>
        </div>
      );
    }
    
    const min = Math.min(...values, 10);
    const max = Math.max(...values, 100);
    
    // Calculate cell dimensions
    const maxCellWidth = 50;
    const cellWidth = Math.min(maxCellWidth, Math.floor(800 / (tactics.length + 1)));
    const cellHeight = 40;
    const totalWidth = (tactics.length + 1) * cellWidth;
    const totalHeight = (testCases.length + 1) * cellHeight;

    return (
      <div style={{ overflowX: 'auto' }}>
        <h3>{title || 'Success Rate by Test Case and Tactic'}</h3>
        
        <ColorScale 
          title="Success Rate (%)" 
          min={`${min.toFixed(0)}%`} 
          max={`${max.toFixed(0)}%`} 
          colorRamp={colorRamp || [
            '#e6f0ff', '#b3d1ff', '#80b3ff', '#4d94ff', '#1a75ff', 
            '#0066ff', '#0047b3', '#003366', '#002147', '#001429'
          ]}
        />
        
        <div style={{ position: 'relative', width: totalWidth, height: totalHeight, marginBottom: '2rem' }}>
          {/* Column headers (tactics) */}
          {tactics.map((tactic, colIndex) => (
            <div 
              key={`col-${colIndex}`}
              style={{
                position: 'absolute',
                top: 0,
                left: cellWidth * (colIndex + 1),
                width: cellWidth,
                height: cellHeight,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: '#f8f9fa',
                border: '1px solid #ddd',
                fontWeight: 'bold',
                fontSize: '12px',
                transform: 'rotate(-45deg)',
                transformOrigin: 'bottom left',
                overflow: 'hidden',
                paddingLeft: '5px',
                textAlign: 'left',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}
              title={tactic}
            >
              {tactic}
            </div>
          ))}
          
          {/* Row headers (test cases) */}
          {testCases.map((testCase, rowIndex) => (
            <div 
              key={`row-${rowIndex}`}
              style={{
                position: 'absolute',
                top: cellHeight * (rowIndex + 1),
                left: 0,
                width: cellWidth,
                height: cellHeight,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'left',
                backgroundColor: '#f8f9fa',
                border: '1px solid #ddd',
                fontWeight: 'bold',
                fontSize: '12px',
                padding: '0 5px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}
              title={testCase}
            >
              {testCase}
            </div>
          ))}
          
          {/* Data cells */}
          {data.map((item, index) => {
            try {
              const rowIndex = testCases.indexOf(item.testCase);
              const colIndex = tactics.indexOf(item.tactic);
              
              if (rowIndex === -1 || colIndex === -1) return null;
              
              return (
                <div 
                  key={`cell-${index}`}
                  style={{
                    position: 'absolute',
                    top: cellHeight * (rowIndex + 1),
                    left: cellWidth * (colIndex + 1),
                    width: cellWidth,
                    height: cellHeight,
                    backgroundColor: getColor(item.successRate, min, max),
                    border: '1px solid #ddd',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexDirection: 'column',
                    fontSize: '12px',
                    cursor: 'pointer'
                  }}
                  title={`${item.testCase} - ${item.tactic}: ${item.successRate.toFixed(1)}% (${item.successCount}/${item.count})`}
                >
                  <div>{item.successRate ? item.successRate.toFixed(0) : 0}%</div>
                  <div style={{ fontSize: '9px', opacity: 0.7 }}>(n={item.count || 0})</div>
                </div>
              );
            } catch (error) {
              console.error("Error rendering heatmap cell:", error);
              return null;
            }
          })}
        </div>
      </div>
    );
  };

  // Calculate standard error of the mean for bootstrap confidence intervals
  const calculateStandardError = (values) => {
    if (!values || values.length === 0) return 0;
    
    // Sample mean
    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    
    // Sum of squared differences from mean
    const sumSquaredDiff = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0);
    
    // Sample variance
    const variance = sumSquaredDiff / (values.length - 1);
    
    // Standard error of the mean
    return Math.sqrt(variance / values.length);
  };

  // Calculate model success rates 
  const modelSuccessRates = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    const modelData = {};
    
    // Group by model
    data.forEach(row => {
      const model = row.model;
      if (!model) return;
      
      if (!modelData[model]) {
        modelData[model] = {
          success: 0,
          fail: 0,
          total: 0,
          name: model
        };
      }
      
      modelData[model].total += 1;
      if (row.success === true || row.success === 1) {
        modelData[model].success += 1;
      } else {
        modelData[model].fail += 1;
      }
    });
    
    // Calculate rates and format for chart
    return Object.values(modelData).map(model => ({
      name: model.name,
      successRate: (model.success / model.total) * 100,
      failRate: (model.fail / model.total) * 100,
      success: model.success,
      fail: model.fail,
      total: model.total,
      // Add standard error calculation
      standardError: calculateStandardError([...Array(model.success).fill(1), ...Array(model.fail).fill(0)])
    }));
  }, [data]);

  // Calculate success rate by test case
  const testCaseSuccessRates = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    const testCaseData = {};
    
    // Filter by selected model if applicable
    const modelFilteredData = selectedModel 
      ? data.filter(row => row.model === selectedModel)
      : data;
    
    // Group by test case
    modelFilteredData.forEach(row => {
      const testCase = row.test_case;
      if (!testCase) return;
      
      if (!testCaseData[testCase]) {
        testCaseData[testCase] = {
          success: 0,
          fail: 0,
          total: 0,
          name: testCase
        };
      }
      
      testCaseData[testCase].total += 1;
      if (row.success === true || row.success === 1) {
        testCaseData[testCase].success += 1;
      } else {
        testCaseData[testCase].fail += 1;
      }
    });
    
    // Calculate rates and format for chart
    return Object.values(testCaseData).map(tc => ({
      name: tc.name,
      successRate: (tc.success / tc.total) * 100,
      failRate: (tc.fail / tc.total) * 100,
      success: tc.success,
      fail: tc.fail,
      total: tc.total,
      // Add standard error calculation
      standardError: calculateStandardError([...Array(tc.success).fill(1), ...Array(tc.fail).fill(0)])
    })).sort((a, b) => b.successRate - a.successRate);  // Sort by success rate
  }, [data, selectedModel]);

  // Calculate success rate by tactic
  const tacticSuccessRates = useMemo(() => {
    if (!data || data.length === 0 || !selectedTestCase) return [];
    
    const tacticData = {};
    
    // Filter by selected model and test case
    const filteredData = data.filter(row => {
      const modelMatch = !selectedModel || row.model === selectedModel;
      const testCaseMatch = row.test_case === selectedTestCase;
      return modelMatch && testCaseMatch;
    });
    
    // Group by tactic
    filteredData.forEach(row => {
      const tactic = row.jailbreak_tactic;
      if (!tactic) return;
      
      if (!tacticData[tactic]) {
        tacticData[tactic] = {
          success: 0,
          fail: 0,
          total: 0,
          name: tactic
        };
      }
      
      tacticData[tactic].total += 1;
      if (row.success === true || row.success === 1) {
        tacticData[tactic].success += 1;
      } else {
        tacticData[tactic].fail += 1;
      }
    });
    
    // Calculate rates and format for chart
    return Object.values(tacticData).map(tactic => ({
      name: tactic.name,
      successRate: tactic.total > 0 
        ? (tactic.success / tactic.total) * 100 
        : 0,
      failRate: tactic.total > 0 
        ? (tactic.fail / tactic.total) * 100 
        : 0,
      success: tactic.success,
      fail: tactic.fail,
      total: tactic.total,
      // Add standard error calculation
      standardError: calculateStandardError([...Array(tactic.success).fill(1), ...Array(tactic.fail).fill(0)])
    })).sort((a, b) => b.successRate - a.successRate); // Sort by success rate
  }, [data, selectedModel, selectedTestCase]);

  // Render loading state
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        flexDirection: 'column',
        gap: '1rem'
      }}>
        <h2>Loading evaluator data...</h2>
        <div style={{ width: '50px', height: '50px', border: '5px solid #f3f3f3', borderTop: '5px solid #3498db', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        flexDirection: 'column',
        color: '#e53e3e'
      }}>
        <h2>Error Loading Data</h2>
        <p>{error}</p>
        <button 
          onClick={() => window.location.reload()}
          style={{
            marginTop: '1rem',
            padding: '0.5rem 1rem',
            backgroundColor: '#3B82F6',
            color: 'white',
            border: 'none',
            borderRadius: '0.25rem',
            cursor: 'pointer'
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  const renderSortOptions = () => (
    <div style={styles.filterItem}>
      <label>Sort By:</label>
      <select
        value={sortBy}
        onChange={(e) => setSortBy(e.target.value)}
        style={styles.select}
      >
        <option value="success">Success Rate (High to Low)</option>
        <option value="fail">Failure Rate (High to Low)</option>
        <option value="total">Sample Count (High to Low)</option>
        <option value="name">Name (A-Z)</option>
      </select>
    </div>
  );

  return (
    <div className="evaluator-viz" style={{ padding: '1rem' }}>
      <h1 style={{ borderBottom: '2px solid #e5e7eb', paddingBottom: '0.5rem' }}>Evaluator Analysis</h1>
      
      {/* Error display */}
      {error && (
        <div style={{ 
          padding: '1rem',
          margin: '1rem 0',
          backgroundColor: '#FFEBEE',
          color: '#B71C1C',
          borderRadius: '0.5rem',
          borderLeft: '4px solid #B71C1C'
        }}>
          <h3 style={{ margin: '0 0 0.5rem' }}>Error Loading Data</h3>
          <p>{error}</p>
          <p>Loading status: {dataLoadingStatus}</p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#B71C1C',
              color: 'white',
              border: 'none',
              borderRadius: '0.25rem',
              cursor: 'pointer',
              marginTop: '0.5rem'
            }}
          >
            Retry
          </button>
        </div>
      )}
      
      {/* Loading indicator */}
      {loading && !error && (
        <div style={{ 
          padding: '2rem',
          margin: '2rem 0', 
          textAlign: 'center',
          backgroundColor: '#f9fafb',
          borderRadius: '0.5rem'
        }}>
          <div>Loading data... ({dataLoadingStatus})</div>
          <div style={{ 
            width: '50%', 
            margin: '1rem auto', 
            height: '4px', 
            backgroundColor: '#e5e7eb',
            borderRadius: '2px',
            overflow: 'hidden',
            position: 'relative'
          }}>
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              height: '100%',
              width: '30%',
              backgroundColor: '#3B82F6',
              borderRadius: '2px',
              animation: 'loading 1.5s infinite ease-in-out'
            }}></div>
          </div>
          <style>{`
            @keyframes loading {
              0% { left: -30%; }
              100% { left: 100%; }
            }
          `}</style>
        </div>
      )}
      
      {/* Main content only shown when data is loaded and no errors */}
      {!loading && !error && data.length > 0 && (
        <>
          {/* Navigation Tabs */}
          <div className="tabs" style={{ display: 'flex', marginBottom: '1rem', borderBottom: '1px solid #e5e7eb' }}>
            {['overview', 'models', 'testCases', 'prompts', 'tacticAnalysis', 'evaluatorAnalysis'].map(tab => (
              <div 
                key={tab}
                className={`tab ${activeTab === tab ? 'active' : ''}`}
                style={{ 
                  padding: '0.75rem 1.25rem', 
                  cursor: 'pointer',
                  borderBottom: activeTab === tab ? '2px solid #3B82F6' : '2px solid transparent',
                  color: activeTab === tab ? '#3B82F6' : '#6B7280',
                  fontWeight: activeTab === tab ? '600' : '400',
                  transition: 'all 0.2s'
                }}
                onClick={() => setActiveTab(tab)}
              >
                {tab === 'overview' ? 'Overview' :
                 tab === 'models' ? 'Models' :
                 tab === 'testCases' ? 'Test Cases' :
                 tab === 'tacticAnalysis' ? 'Tactic Analysis' :
                 tab === 'evaluatorAnalysis' ? 'Evaluator Analysis' :
                 'Prompts'}
              </div>
            ))}
          </div>
          
          {/* Chart Type Selection */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ marginRight: '0.5rem', fontWeight: '500' }}>Chart Type:</label>
            <select
              value={chartType}
              onChange={(e) => setChartType(e.target.value)}
              style={{
                padding: '0.25rem 0.5rem',
                borderRadius: '0.25rem',
                border: '1px solid #d1d5db'
              }}
            >
              <option value="bar">Bar Chart</option>
              <option value="line">Line Chart</option>
              <option value="scatter">Scatter Plot</option>
              <option value="pie">Pie Chart</option>
              <option value="radar">Radar Chart</option>
              <option value="composed">Composed Chart</option>
            </select>
            
            <label style={{ marginLeft: '1rem', marginRight: '0.5rem', fontWeight: '500' }}>Show Details:</label>
            <input
              type="checkbox"
              checked={showDetails}
              onChange={(e) => setShowDetails(e.target.checked)}
              style={{ transform: 'scale(1.2)' }}
            />
          </div>
          
          {/* Filters */}
          <div className="filters" style={styles.filterContainer}>
            <div style={styles.filterItem}>
              <label>Model:</label>
              <select
                value={selectedModel || ''}
                onChange={(e) => setSelectedModel(e.target.value || null)}
                style={styles.select}
              >
                <option value="">All Models</option>
                {uniqueModels.map(model => (
                  <option key={model} value={model}>{model}</option>
                ))}
              </select>
            </div>
            
            <div style={styles.filterItem}>
              <label>Test Case:</label>
              <select
                value={selectedTestCase || ''}
                onChange={(e) => setSelectedTestCase(e.target.value || null)}
                style={styles.select}
              >
                <option value="">All Test Cases</option>
                {uniqueTestCases.map(testCase => (
                  <option key={testCase} value={testCase}>{testCase}</option>
                ))}
              </select>
            </div>
            
            <div style={styles.filterItem}>
              <label>Tactic:</label>
              <select
                value={selectedTactic || ''}
                onChange={(e) => setSelectedTactic(e.target.value || null)}
                style={styles.select}
              >
                <option value="">All Tactics</option>
                {uniqueTactics.map(tactic => (
                  <option key={tactic} value={tactic}>{tactic}</option>
                ))}
              </select>
            </div>
            
            {renderSortOptions()}
          </div>
          
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div>
              <h2 style={{ borderBottom: '1px solid #e5e7eb', paddingBottom: '0.5rem' }}>Overview</h2>
              
              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                <div style={{ 
                  flex: 1, 
                  minWidth: '300px', 
                  backgroundColor: 'white', 
                  padding: '1rem', 
                  borderRadius: '0.5rem',
                  boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                }}>
                  <h3>Dataset Summary</h3>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <tbody>
                      <tr>
                        <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb' }}>Total Evaluations:</td>
                        <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb', fontWeight: 'bold' }}>{data.length}</td>
                      </tr>
                      <tr>
                        <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb' }}>Models:</td>
                        <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb', fontWeight: 'bold' }}>{uniqueModels.length}</td>
                      </tr>
                      <tr>
                        <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb' }}>Test Cases:</td>
                        <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb', fontWeight: 'bold' }}>{uniqueTestCases.length}</td>
                      </tr>
                      <tr>
                        <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb' }}>Tactics:</td>
                        <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb', fontWeight: 'bold' }}>{uniqueTactics.length}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                
                <div style={{ 
                  flex: 1, 
                  minWidth: '300px', 
                  backgroundColor: 'white', 
                  padding: '1rem', 
                  borderRadius: '0.5rem',
                  boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                }}>
                  <h3>Overall Success Rate</h3>
                  {data.length > 0 && (
                    <>
                      <div style={{ 
                        textAlign: 'center', 
                        padding: '1rem', 
                        fontSize: '2.5rem', 
                        fontWeight: 'bold',
                        color: '#3B82F6'
                      }}>
                        {((data.filter(row => row.success === true || row.success === 1).length / data.length) * 100).toFixed(1)}%
                      </div>
                      <ResponsiveContainer width="100%" height={150}>
                        <PieChart>
                          <Pie
                            data={[
                              { name: 'Success', value: data.filter(row => row.success === true || row.success === 1).length, fill: '#82ca9d' },
                              { name: 'Failure', value: data.filter(row => row.success !== true && row.success !== 1).length, fill: '#ff6b6b' }
                            ]}
                            cx="50%"
                            cy="50%"
                            outerRadius={60}
                            dataKey="value"
                            label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
                          />
                          <Tooltip formatter={(value) => [`${value} evaluations`, ""]} />
                          <Legend />
                        </PieChart>
                      </ResponsiveContainer>
                    </>
                  )}
                </div>
              </div>
              
              <div style={styles.chartContainer}>
                <h3>Top 10 Models by Success Rate</h3>
                <ResponsiveContainer width="100%" height={400}>
                  {chartType === 'bar' ? (
                    <BarChart
                      data={modelSuccessRates
                        .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate :
                             sortBy === 'fail' ? b.failRate - a.failRate :
                             sortBy === 'total' ? b.total - a.total :
                             a.name.localeCompare(b.name))
                        .slice(0, 10)}
                      margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="name" 
                        angle={-45} 
                        textAnchor="end" 
                        height={100} 
                        interval={0}
                      />
                      <YAxis label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
                      <Legend />
                      <Bar dataKey="successRate" name="Success Rate" fill="#8884d8">
                        {modelSuccessRates.slice(0, 10).map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={COLORS[index % COLORS.length]} 
                          />
                        ))}
                        {showDetails && <ErrorBar dataKey="standardError" width={4} strokeWidth={2} stroke="#8884d8" />}
                        <LabelList dataKey="total" position="insideTop" formatter={(value) => `n=${value}`} />
                      </Bar>
                    </BarChart>
                  ) : chartType === 'line' ? (
                    // Line chart implementation
                    <LineChart
                      data={modelSuccessRates
                        .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate : 
                                      sortBy === 'fail' ? b.failRate - a.failRate : 
                                      sortBy === 'total' ? b.total - a.total : 
                                      a.name.localeCompare(b.name))
                        .slice(0, 10)}
                      margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="name" 
                        angle={-45} 
                        textAnchor="end" 
                        height={100} 
                        interval={0}
                      />
                      <YAxis label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
                      <Legend />
                      <Line type="monotone" dataKey="successRate" name="Success Rate" stroke="#8884d8" />
                    </LineChart>
                  ) : (
                    // Default to bar chart
                    <BarChart
                      data={modelSuccessRates
                        .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate :
                             sortBy === 'fail' ? b.failRate - a.failRate :
                             sortBy === 'total' ? b.total - a.total :
                             a.name.localeCompare(b.name))
                        .slice(0, 10)}
                      margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="name" 
                        angle={-45} 
                        textAnchor="end" 
                        height={100} 
                        interval={0}
                      />
                      <YAxis label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
                      <Legend />
                      <Bar dataKey="successRate" name="Success Rate" fill="#8884d8">
                        {modelSuccessRates.slice(0, 10).map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={COLORS[index % COLORS.length]} 
                          />
                        ))}
                        {showDetails && <ErrorBar dataKey="standardError" width={4} strokeWidth={2} stroke="#8884d8" />}
                        <LabelList dataKey="total" position="insideTop" formatter={(value) => `n=${value}`} />
                      </Bar>
                    </BarChart>
                  )}
                </ResponsiveContainer>
              </div>
              
              {/* Heatmap visualization */}
              {heatmapData && (
                <div style={styles.chartContainer}>
                  <h3>Test Case vs Tactic Success Rate Heatmap</h3>
                  <HeatMap 
                    data={heatmapData}
                    testCases={uniqueTestCases}
                    tactics={uniqueTactics} 
                    title="Success Rate by Test Case and Tactic" 
                    colorRamp={[
                      '#e6f0ff', '#b3d1ff', '#80b3ff', '#4d94ff', '#1a75ff', 
                      '#0066ff', '#0047b3', '#003366', '#002147', '#001429'
                    ]}
                  />
                </div>
              )}
              
              <div style={styles.chartContainer}>
                <h3>Top 10 Models by Success Rate</h3>
                <ResponsiveContainer width="100%" height={400}>
                  {chartType === 'bar' ? (
                    <BarChart
                      data={modelSuccessRates
                        .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate :
                             sortBy === 'fail' ? b.failRate - a.failRate :
                             sortBy === 'total' ? b.total - a.total :
                             a.name.localeCompare(b.name))
                        .slice(0, 10)}
                      margin={{ top: 20, right: 30, left: 20, bottom: 70 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="name" 
                        angle={-45} 
                        textAnchor="end" 
                        height={80} 
                      />
                      <YAxis label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip 
                        formatter={(value, name) => {
                          if (name === 'successRate') return [`${value.toFixed(2)}%`, 'Success Rate'];
                          if (name === 'standardError') return [`±${value.toFixed(2)}%`, 'Standard Error'];
                          return [value, name];
                        }} 
                      />
                      <Legend />
                      <Bar dataKey="successRate" name="Success Rate" fill="#8884d8">
                        {showDetails && <ErrorBar dataKey="standardError" width={4} strokeWidth={2} stroke="#8884d8" />}
                        <LabelList dataKey="successRate" position="top" formatter={(value) => `${value.toFixed(1)}%`} />
                      </Bar>
                    </BarChart>
                  ) : chartType === 'line' ? (
                    <LineChart
                      data={modelSuccessRates
                        .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate :
                             sortBy === 'fail' ? b.failRate - a.failRate :
                             sortBy === 'total' ? b.total - a.total :
                             a.name.localeCompare(b.name))
                        .slice(0, 10)}
                      margin={{ top: 20, right: 30, left: 20, bottom: 70 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="name" 
                        angle={-45} 
                        textAnchor="end" 
                        height={80} 
                      />
                      <YAxis label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
                      <Legend />
                      <Line type="monotone" dataKey="successRate" name="Success Rate" stroke="#8884d8" strokeWidth={2} dot={{ r: 6 }} />
                    </LineChart>
                  ) : chartType === 'pie' ? (
                    <PieChart>
                      <Pie
                        data={modelSuccessRates
                          .sort((a, b) => b.successRate - a.successRate)
                          .slice(0, 10)}
                        cx="50%"
                        cy="50%"
                        outerRadius={130}
                        dataKey="success"
                        nameKey="name"
                        label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      >
                        {modelSuccessRates.slice(0, 10).map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value, name, props) => {
                        const dataItem = modelSuccessRates.find(item => item.name === props.payload.name);
                        return [`${dataItem?.successRate.toFixed(2)}% (${value} successes)`, props.payload.name];
                      }} />
                      <Legend />
                    </PieChart>
                  ) : chartType === 'radar' ? (
                    <RadarChart 
                      cx="50%" 
                      cy="50%" 
                      outerRadius="80%" 
                      data={modelSuccessRates.sort((a, b) => b.successRate - a.successRate).slice(0, 10)}
                    >
                      <PolarGrid />
                      <PolarAngleAxis dataKey="name" />
                      <PolarRadiusAxis angle={30} domain={[0, 100]} />
                      <Radar name="Success Rate" dataKey="successRate" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
                      <Legend />
                      <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
                    </RadarChart>
                  ) : chartType === 'scatter' ? (
                    <ScatterChart
                      margin={{ top: 20, right: 30, left: 20, bottom: 70 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        type="number" 
                        dataKey="total" 
                        name="Total Evaluations" 
                        label={{ value: 'Total Evaluations', position: 'insideBottomRight', offset: -5 }} 
                      />
                      <YAxis 
                        type="number" 
                        dataKey="successRate" 
                        name="Success Rate" 
                        label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} 
                      />
                      <Tooltip 
                        cursor={{ strokeDasharray: '3 3' }} 
                        formatter={(value, name, props) => {
                          if (name === 'successRate') return [`${value.toFixed(2)}%`, 'Success Rate'];
                          return [value, name];
                        }}
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            return (
                              <div style={{ backgroundColor: 'white', padding: '10px', border: '1px solid #ccc' }}>
                                <p>{payload[0].payload.name}</p>
                                <p>{`Success Rate: ${payload[0].payload.successRate.toFixed(2)}%`}</p>
                                <p>{`Total: ${payload[0].payload.total}`}</p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Legend />
                      <Scatter 
                        name="Models" 
                        data={modelSuccessRates} 
                        fill="#8884d8"
                      />
                    </ScatterChart>
                  ) : (
                    <ComposedChart
                      data={modelSuccessRates
                        .sort((a, b) => b.successRate - a.successRate)
                        .slice(0, 10)}
                      margin={{ top: 20, right: 30, left: 20, bottom: 70 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="name" 
                        angle={-45} 
                        textAnchor="end" 
                        height={80} 
                      />
                      <YAxis yAxisId="left" label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} />
                      <YAxis yAxisId="right" orientation="right" label={{ value: 'Total Evaluations', angle: 90, position: 'insideRight' }} />
                      <Tooltip formatter={(value, name) => {
                        if (name === 'successRate') return [`${value.toFixed(2)}%`, 'Success Rate'];
                        if (name === 'total') return [value, 'Total Evaluations'];
                        return [value, name];
                      }} />
                      <Legend />
                      <Bar yAxisId="left" dataKey="successRate" name="Success Rate" fill="#8884d8" />
                      <Line yAxisId="right" type="monotone" dataKey="total" name="Total Evaluations" stroke="#ff7300" />
                    </ComposedChart>
                  )}
                </ResponsiveContainer>
              </div>
              
              <div style={styles.chartContainer}>
                <h3>Top 10 Test Cases by Success Rate</h3>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart
                    data={testCaseSuccessRates
                      .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate :
                           sortBy === 'fail' ? b.failRate - a.failRate :
                           sortBy === 'total' ? b.total - a.total :
                           a.name.localeCompare(b.name))
                      .slice(0, 10)}
                    margin={{ top: 20, right: 30, left: 20, bottom: 70 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="name" 
                      angle={-45} 
                      textAnchor="end" 
                      height={80} 
                    />
                    <YAxis label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
                    <Legend />
                    <Bar dataKey="successRate" name="Success Rate" fill="#82ca9d">
                      {showDetails && <ErrorBar dataKey="standardError" width={4} strokeWidth={2} stroke="#82ca9d" />}
                      <LabelList dataKey={(entry) => `${entry.successRate.toFixed(1)}% (n=${entry.total})`} position="top" />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
          
          {/* Models Tab */}
          {activeTab === 'models' && (
            <div>
              <h2 style={{ borderBottom: '1px solid #e5e7eb', paddingBottom: '0.5rem' }}>Model Analysis</h2>
              
              <div style={styles.chartContainer}>
                <h3>Models by Success Rate {selectedModel && `(Selected: ${selectedModel})`}</h3>
                <ResponsiveContainer width="100%" height={500}>
                  {chartType === 'bar' ? (
                    <BarChart
                      data={modelSuccessRates
                        .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate :
                             sortBy === 'fail' ? b.failRate - a.failRate :
                             sortBy === 'total' ? b.total - a.total :
                             a.name.localeCompare(b.name))}
                      margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="name" 
                        angle={-45} 
                        textAnchor="end" 
                        height={100}
                        interval={0}
                      />
                      <YAxis label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip 
                        formatter={(value, name) => {
                          if (name === 'successRate') return [`${value.toFixed(2)}%`, 'Success Rate'];
                          if (name === 'standardError') return [`±${value.toFixed(2)}%`, 'Standard Error'];
                          return [value, name];
                        }}
                      />
                      <Legend />
                      <Bar dataKey="successRate" name="Success Rate" fill="#8884d8">
                        {modelSuccessRates.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={entry.name === selectedModel ? '#ff7300' : COLORS[index % COLORS.length]}
                            stroke={entry.name === selectedModel ? '#000000' : undefined}
                            strokeWidth={entry.name === selectedModel ? 1 : 0}
                          />
                        ))}
                        {showDetails && <ErrorBar dataKey="standardError" width={4} strokeWidth={2} stroke="#8884d8" />}
                        <LabelList dataKey="total" position="insideTop" formatter={(value) => `n=${value}`} />
                      </Bar>
                    </BarChart>
                  ) : chartType === 'scatter' ? (
                    <ScatterChart
                      margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        type="number" 
                        dataKey="total" 
                        name="Total Evaluations" 
                        label={{ value: 'Total Evaluations', position: 'insideBottomRight', offset: -5 }} 
                      />
                      <YAxis 
                        type="number" 
                        dataKey="successRate" 
                        name="Success Rate" 
                        label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} 
                      />
                      <ZAxis range={[50, 400]} />
                      <Tooltip 
                        cursor={{ strokeDasharray: '3 3' }} 
                        formatter={(value, name, props) => {
                          if (name === 'successRate') return [`${value.toFixed(2)}%`, 'Success Rate'];
                          return [value, name];
                        }}
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            return (
                              <div style={{ backgroundColor: 'white', padding: '10px', border: '1px solid #ccc' }}>
                                <p style={{ fontWeight: 'bold' }}>{payload[0].payload.name}</p>
                                <p>{`Success Rate: ${payload[0].payload.successRate.toFixed(2)}%`}</p>
                                <p>{`Total: ${payload[0].payload.total}`}</p>
                                <p>{`Success: ${payload[0].payload.success}`}</p>
                                <p>{`Fail: ${payload[0].payload.fail}`}</p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Legend />
                      <Scatter 
                        name="Models" 
                        data={modelSuccessRates} 
                        fill="#8884d8"
                        shape={(props) => {
                          const { cx, cy, r, payload } = props;
                          const isSelected = payload.name === selectedModel;
                          
                          return (
                            <circle 
                              cx={cx} 
                              cy={cy} 
                              r={isSelected ? r * 1.5 : r} 
                              fill={isSelected ? '#ff7300' : '#8884d8'} 
                              stroke={isSelected ? '#000' : 'none'}
                              strokeWidth={isSelected ? 2 : 0}
                            />
                          );
                        }}
                      />
                    </ScatterChart>
                  ) : chartType === 'pie' ? (
                    <PieChart>
                      <Pie
                        data={modelSuccessRates}
                        cx="50%"
                        cy="50%"
                        outerRadius={160}
                        innerRadius={80}
                        dataKey="success"
                        nameKey="name"
                        label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      >
                        {modelSuccessRates.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={entry.name === selectedModel ? '#ff7300' : COLORS[index % COLORS.length]}
                            stroke={entry.name === selectedModel ? '#000000' : undefined}
                            strokeWidth={entry.name === selectedModel ? 2 : 0}
                          />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value, name, props) => {
                        const dataItem = modelSuccessRates.find(item => item.name === props.payload.name);
                        return [`${dataItem.successRate.toFixed(2)}% (${value} successes)`, props.payload.name];
                      }} />
                      <Legend />
                    </PieChart>
                  ) : (
                    <ComposedChart
                      data={modelSuccessRates
                        .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate :
                             sortBy === 'fail' ? b.failRate - a.failRate :
                             sortBy === 'total' ? b.total - a.total :
                             a.name.localeCompare(b.name))}
                      margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="name" 
                        angle={-45} 
                        textAnchor="end" 
                        height={100}
                        interval={0}
                      />
                      <YAxis yAxisId="left" label={{ value: 'Rate (%)', angle: -90, position: 'insideLeft' }} />
                      <YAxis yAxisId="right" orientation="right" label={{ value: 'Count', angle: 90, position: 'insideRight' }} />
                      <Tooltip formatter={(value, name) => {
                        if (name === 'successRate') return [`${value.toFixed(2)}%`, 'Success Rate'];
                        if (name === 'failRate') return [`${value.toFixed(2)}%`, 'Fail Rate'];
                        if (name === 'total') return [value, 'Total Evaluations'];
                        return [value, name];
                      }} />
                      <Legend />
                      <Bar yAxisId="left" dataKey="successRate" name="Success Rate" fill="#82ca9d" stackId="a">
                        {modelSuccessRates.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={entry.name === selectedModel ? '#7CB342' : '#82ca9d'}
                            stroke={entry.name === selectedModel ? '#000000' : undefined}
                            strokeWidth={entry.name === selectedModel ? 1 : 0}
                          />
                        ))}
                      </Bar>
                      <Bar yAxisId="left" dataKey="failRate" name="Fail Rate" fill="#ff8042" stackId="a">
                        {modelSuccessRates.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={entry.name === selectedModel ? '#E65100' : '#ff8042'}
                            stroke={entry.name === selectedModel ? '#000000' : undefined}
                            strokeWidth={entry.name === selectedModel ? 1 : 0}
                          />
                        ))}
                      </Bar>
                      <Line yAxisId="right" type="monotone" dataKey="total" name="Total" stroke="#8884d8" />
                    </ComposedChart>
                  )}
                </ResponsiveContainer>
              </div>
              
              {selectedModel && (
                <div style={styles.chartContainer}>
                  <h3>Test Case Success Rates for {selectedModel}</h3>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart
                      data={testCaseSuccessRates
                        .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate :
                             sortBy === 'fail' ? b.failRate - a.failRate :
                             sortBy === 'total' ? b.total - a.total :
                             a.name.localeCompare(b.name))}
                      margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="name" 
                        angle={-45} 
                        textAnchor="end" 
                        height={100} 
                      />
                      <YAxis label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
                      <Legend />
                      <Bar dataKey="successRate" name="Success Rate" fill="#82ca9d">
                        {testCaseSuccessRates.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                        {showDetails && <ErrorBar dataKey="standardError" width={4} strokeWidth={2} stroke="#82ca9d" />}
                        <LabelList dataKey="total" position="insideTop" formatter={(value) => `n=${value}`} />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
              
              {showDetails && (
                <div style={styles.chartContainer}>
                  <h3>Detailed Model Statistics</h3>
                  <div style={{ maxHeight: '400px', overflow: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr style={{ backgroundColor: '#f3f4f6' }}>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Model</th>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Success Rate</th>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Success</th>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Fail</th>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Total</th>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Standard Error</th>
                        </tr>
                      </thead>
                      <tbody>
                        {modelSuccessRates
                          .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate :
                               sortBy === 'fail' ? b.failRate - a.failRate :
                               sortBy === 'total' ? b.total - a.total :
                               a.name.localeCompare(b.name))
                          .map((model, index) => (
                            <tr 
                              key={index} 
                              style={{ 
                                backgroundColor: model.name === selectedModel ? '#f0f9ff' : index % 2 ? '#f9f9f9' : 'white'
                              }}
                            >
                              <td style={{ 
                                border: '1px solid #ddd', 
                                padding: '8px',
                                fontWeight: model.name === selectedModel ? 'bold' : 'normal'
                              }}>
                                {model.name}
                              </td>
                              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                                {model.successRate.toFixed(2)}%
                              </td>
                              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                                {model.success}
                              </td>
                              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                                {model.fail}
                              </td>
                              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                                {model.total}
                              </td>
                              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                                ±{model.standardError.toFixed(2)}%
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Test Cases Tab */}
          {activeTab === 'testCases' && (
            <div>
              <h2 style={{ borderBottom: '1px solid #e5e7eb', paddingBottom: '0.5rem' }}>Test Case Analysis</h2>
              
              <div style={styles.chartContainer}>
                <h3>Test Cases by Success Rate {selectedTestCase && `(Selected: ${selectedTestCase})`}</h3>
                <ResponsiveContainer width="100%" height={500}>
                  {chartType === 'bar' ? (
                    <BarChart
                      data={testCaseSuccessRates
                        .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate :
                             sortBy === 'fail' ? b.failRate - a.failRate :
                             sortBy === 'total' ? b.total - a.total :
                             a.name.localeCompare(b.name))}
                      margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="name" 
                        angle={-45} 
                        textAnchor="end" 
                        height={100} 
                      />
                      <YAxis label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
                      <Legend />
                      <Bar dataKey="successRate" name="Success Rate" fill="#82ca9d">
                        {testCaseSuccessRates.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={entry.name === selectedTestCase ? '#ff7300' : COLORS[(index + 2) % COLORS.length]}
                            stroke={entry.name === selectedTestCase ? '#000000' : undefined}
                            strokeWidth={entry.name === selectedTestCase ? 1 : 0}
                          />
                        ))}
                        {showDetails && <ErrorBar dataKey="standardError" width={4} strokeWidth={2} stroke="#82ca9d" />}
                        <LabelList dataKey="total" position="insideTop" formatter={(value) => `n=${value}`} />
                      </Bar>
                    </BarChart>
                  ) : chartType === 'line' ? (
                    <LineChart
                      data={testCaseSuccessRates
                        .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate :
                             sortBy === 'fail' ? b.failRate - a.failRate :
                             sortBy === 'total' ? b.total - a.total :
                             a.name.localeCompare(b.name))}
                      margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="name" 
                        angle={-45} 
                        textAnchor="end" 
                        height={100} 
                      />
                      <YAxis label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
                      <Legend />
                      <Line type="monotone" dataKey="successRate" name="Success Rate" stroke="#82ca9d" strokeWidth={2} dot={{ r: 6 }} />
                    </LineChart>
                  ) : chartType === 'pie' ? (
                    <PieChart>
                      <Pie
                        data={testCaseSuccessRates}
                        cx="50%"
                        cy="50%"
                        outerRadius={160}
                        innerRadius={80}
                        dataKey="success"
                        nameKey="name"
                        label={({name, percent}) => `${name.substring(0, 15)}${name.length > 15 ? '...' : ''}: ${(percent * 100).toFixed(0)}%`}
                      >
                        {testCaseSuccessRates.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={entry.name === selectedTestCase ? '#ff7300' : COLORS[(index + 2) % COLORS.length]}
                            stroke={entry.name === selectedTestCase ? '#000000' : undefined}
                            strokeWidth={entry.name === selectedTestCase ? 2 : 0}
                          />
                        ))}
                      </Pie>
                      <Tooltip 
                        formatter={(value, name, props) => {
                          const dataItem = testCaseSuccessRates.find(item => item.name === props.payload.name);
                          return [`${dataItem.successRate.toFixed(2)}% (${value} successes)`, props.payload.name];
                        }}
                        labelFormatter={(label) => {
                          const parts = label.split('/');
                          return parts[parts.length - 1];
                        }}
                      />
                      <Legend 
                        formatter={(value) => {
                          const parts = value.split('/');
                          return parts[parts.length - 1];
                        }}
                      />
                    </PieChart>
                  ) : (
                    <ComposedChart
                      data={testCaseSuccessRates
                        .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate :
                             sortBy === 'fail' ? b.failRate - a.failRate :
                             sortBy === 'total' ? b.total - a.total :
                             a.name.localeCompare(b.name))}
                      margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="name" 
                        angle={-45} 
                        textAnchor="end" 
                        height={100} 
                      />
                      <YAxis yAxisId="left" label={{ value: 'Rate (%)', angle: -90, position: 'insideLeft' }} />
                      <YAxis yAxisId="right" orientation="right" label={{ value: 'Count', angle: 90, position: 'insideRight' }} />
                      <Tooltip 
                        formatter={(value, name) => {
                          if (name === 'successRate') return [`${value.toFixed(2)}%`, 'Success Rate'];
                          if (name === 'failRate') return [`${value.toFixed(2)}%`, 'Fail Rate'];
                          if (name === 'total') return [value, 'Total Evaluations'];
                          return [value, name];
                        }}
                        labelFormatter={(label) => {
                          const parts = label.split('/');
                          return parts[parts.length - 1];
                        }}
                      />
                      <Legend />
                      <Bar yAxisId="left" dataKey="successRate" name="Success Rate" fill="#82ca9d" stackId="a">
                        {testCaseSuccessRates.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={entry.name === selectedTestCase ? '#7CB342' : '#82ca9d'}
                            stroke={entry.name === selectedTestCase ? '#000000' : undefined}
                            strokeWidth={entry.name === selectedTestCase ? 1 : 0}
                          />
                        ))}
                      </Bar>
                      <Bar yAxisId="left" dataKey="failRate" name="Fail Rate" fill="#ff8042" stackId="a">
                        {testCaseSuccessRates.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={entry.name === selectedTestCase ? '#E65100' : '#ff8042'}
                            stroke={entry.name === selectedTestCase ? '#000000' : undefined}
                            strokeWidth={entry.name === selectedTestCase ? 1 : 0}
                          />
                        ))}
                      </Bar>
                      <Line yAxisId="right" type="monotone" dataKey="total" name="Total" stroke="#8884d8" />
                    </ComposedChart>
                  )}
                </ResponsiveContainer>
              </div>
              
              {selectedTestCase && (
                <div style={styles.chartContainer}>
                  <h3>Model Success Rates for {selectedTestCase}</h3>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart
                      data={modelSuccessRates
                        .filter(model => {
                          const relevantData = data.filter(row => 
                            row.model === model.name && 
                            row.test_case === selectedTestCase
                          );
                          return relevantData.length > 0;
                        })
                        .map(model => {
                          const relevantData = data.filter(row => 
                            row.model === model.name && 
                            row.test_case === selectedTestCase
                          );
                          const success = relevantData.filter(row => 
                            row.success === true || row.success === 1
                          ).length;
                          return {
                            name: model.name,
                            successRate: (success / relevantData.length) * 100,
                            total: relevantData.length,
                            success,
                            fail: relevantData.length - success,
                            standardError: calculateStandardError([...Array(success).fill(1), ...Array(relevantData.length - success).fill(0)])
                          };
                        })
                        .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate :
                             sortBy === 'fail' ? (100 - b.successRate) - (100 - a.successRate) :
                             sortBy === 'total' ? b.total - a.total :
                             a.name.localeCompare(b.name))
                      }
                      margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="name" 
                        angle={-45} 
                        textAnchor="end" 
                        height={100} 
                      />
                      <YAxis label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
                      <Legend />
                      <Bar dataKey="successRate" name="Success Rate" fill="#8884d8">
                        {modelSuccessRates.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                        {showDetails && <ErrorBar dataKey="standardError" width={4} strokeWidth={2} stroke="#8884d8" />}
                        <LabelList dataKey="total" position="insideTop" formatter={(value) => `n=${value}`} />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
              
              {showDetails && (
                <div style={styles.chartContainer}>
                  <h3>Detailed Test Case Statistics</h3>
                  <div style={{ maxHeight: '400px', overflow: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr style={{ backgroundColor: '#f3f4f6' }}>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Test Case</th>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Success Rate</th>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Success</th>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Fail</th>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Total</th>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Standard Error</th>
                        </tr>
                      </thead>
                      <tbody>
                        {testCaseSuccessRates
                          .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate :
                               sortBy === 'fail' ? b.failRate - a.failRate :
                               sortBy === 'total' ? b.total - a.total :
                               a.name.localeCompare(b.name))
                          .map((testCase, index) => (
                            <tr 
                              key={index} 
                              style={{ 
                                backgroundColor: testCase.name === selectedTestCase ? '#f0f9ff' : index % 2 ? '#f9f9f9' : 'white'
                              }}
                            >
                              <td style={{ 
                                border: '1px solid #ddd', 
                                padding: '8px',
                                fontWeight: testCase.name === selectedTestCase ? 'bold' : 'normal'
                              }}>
                                {testCase.name}
                              </td>
                              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                                {testCase.successRate.toFixed(2)}%
                              </td>
                              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                                {testCase.success}
                              </td>
                              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                                {testCase.fail}
                              </td>
                              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                                {testCase.total}
                              </td>
                              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                                ±{testCase.standardError.toFixed(2)}%
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Prompts Tab */}
          {activeTab === 'prompts' && selectedTestCase && (
            <div>
              <h2 style={{ borderBottom: '1px solid #e5e7eb', paddingBottom: '0.5rem' }}>Prompt Analysis for {selectedTestCase}</h2>
              
              <div style={styles.chartContainer}>
                <h3>Prompts by Success Rate {selectedTactic && `(Selected: ${selectedTactic})`}</h3>
                <ResponsiveContainer width="100%" height={400}>
                  {chartType === 'bar' ? (
                    <BarChart
                      data={tacticSuccessRates
                        .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate :
                             sortBy === 'fail' ? b.failRate - a.failRate :
                             sortBy === 'total' ? b.total - a.total :
                             a.name.localeCompare(b.name))}
                      margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="name" 
                        angle={-45} 
                        textAnchor="end" 
                        height={100} 
                        tickFormatter={(value) => {
                          const parts = value.split('/');
                          return parts[parts.length - 1];
                        }}
                      />
                      <YAxis label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip 
                        formatter={(value) => `${value.toFixed(2)}%`}
                        labelFormatter={(label) => {
                          const parts = label.split('/');
                          return parts[parts.length - 1];
                        }}
                      />
                      <Legend />
                      <Bar dataKey="successRate" name="Success Rate" fill="#ffc658">
                        {tacticSuccessRates.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={entry.name === selectedTactic ? '#ff7300' : COLORS[(index + 4) % COLORS.length]}
                            stroke={entry.name === selectedTactic ? '#000000' : undefined}
                            strokeWidth={entry.name === selectedTactic ? 1 : 0}
                          />
                        ))}
                        {showDetails && <ErrorBar dataKey="standardError" width={4} strokeWidth={2} stroke="#ffc658" />}
                        <LabelList dataKey="total" position="insideTop" formatter={(value) => `n=${value}`} />
                      </Bar>
                    </BarChart>
                  ) : chartType === 'pie' ? (
                    <PieChart>
                      <Pie
                        data={tacticSuccessRates}
                        cx="50%"
                        cy="50%"
                        outerRadius={140}
                        dataKey="success"
                        nameKey="name"
                        label={({name, percent}) => {
                          const parts = name.split('/');
                          const shortName = parts[parts.length - 1];
                          return `${shortName.substring(0, 10)}${shortName.length > 10 ? '...' : ''}: ${(percent * 100).toFixed(0)}%`;
                        }}
                      >
                        {tacticSuccessRates.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={entry.name === selectedTactic ? '#ff7300' : COLORS[(index + 4) % COLORS.length]}
                            stroke={entry.name === selectedTactic ? '#000000' : undefined}
                            strokeWidth={entry.name === selectedTactic ? 2 : 0}
                          />
                        ))}
                      </Pie>
                      <Tooltip 
                        formatter={(value, name, props) => {
                          const dataItem = tacticSuccessRates.find(item => item.name === props.payload.name);
                          return [`${dataItem.successRate.toFixed(2)}% (${value} successes)`, props.payload.name];
                        }}
                        labelFormatter={(label) => {
                          const parts = label.split('/');
                          return parts[parts.length - 1];
                        }}
                      />
                      <Legend 
                        formatter={(value) => {
                          const parts = value.split('/');
                          return parts[parts.length - 1];
                        }}
                      />
                    </PieChart>
                  ) : (
                    <ComposedChart
                      data={tacticSuccessRates
                        .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate :
                             sortBy === 'fail' ? b.failRate - a.failRate :
                             sortBy === 'total' ? b.total - a.total :
                             a.name.localeCompare(b.name))}
                      margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="name" 
                        angle={-45} 
                        textAnchor="end" 
                        height={100}
                        tickFormatter={(value) => {
                          const parts = value.split('/');
                          return parts[parts.length - 1];
                        }}
                      />
                      <YAxis yAxisId="left" label={{ value: 'Rate (%)', angle: -90, position: 'insideLeft' }} />
                      <YAxis yAxisId="right" orientation="right" label={{ value: 'Count', angle: 90, position: 'insideRight' }} />
                      <Tooltip 
                        formatter={(value, name) => {
                          if (name === 'successRate') return [`${value.toFixed(2)}%`, 'Success Rate'];
                          if (name === 'failRate') return [`${value.toFixed(2)}%`, 'Fail Rate'];
                          if (name === 'total') return [value, 'Total Evaluations'];
                          return [value, name];
                        }}
                        labelFormatter={(label) => {
                          const parts = label.split('/');
                          return parts[parts.length - 1];
                        }}
                      />
                      <Legend />
                      <Bar yAxisId="left" dataKey="successRate" name="Success Rate" fill="#ffc658" stackId="a">
                        {tacticSuccessRates.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={entry.name === selectedTactic ? '#7CB342' : '#82ca9d'}
                            stroke={entry.name === selectedTactic ? '#000000' : undefined}
                            strokeWidth={entry.name === selectedTactic ? 1 : 0}
                          />
                        ))}
                      </Bar>
                      <Bar yAxisId="left" dataKey="failRate" name="Fail Rate" fill="#ff8042" stackId="a">
                        {tacticSuccessRates.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={entry.name === selectedTactic ? '#E65100' : '#ff8042'}
                            stroke={entry.name === selectedTactic ? '#000000' : undefined}
                            strokeWidth={entry.name === selectedTactic ? 1 : 0}
                          />
                        ))}
                      </Bar>
                      <Line yAxisId="right" type="monotone" dataKey="total" name="Total" stroke="#8884d8" />
                    </ComposedChart>
                  )}
                </ResponsiveContainer>
              </div>
              
              {/* Details for selected tactic */}
              {selectedTactic && (
                <div style={styles.chartContainer}>
                  <h3>Details for Tactic: {selectedTactic.split('/').pop()}</h3>
                  <div style={{ maxHeight: '400px', overflow: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr style={{ backgroundColor: '#f3f4f6' }}>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Model</th>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Success</th>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Response</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredData
                          .filter(row => row.jailbreak_tactic === selectedTactic)
                          .map((row, index) => (
                            <tr key={index} style={{ backgroundColor: index % 2 ? '#f9f9f9' : 'white' }}>
                              <td style={{ border: '1px solid #ddd', padding: '8px' }}>{row.model}</td>
                              <td style={{ 
                                border: '1px solid #ddd', 
                                padding: '8px',
                                backgroundColor: row.success ? '#d4edda' : '#f8d7da',
                                color: row.success ? '#155724' : '#721c24'
                              }}>
                                {row.success ? '✓ Success' : '✗ Failure'}
                              </td>
                              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                                <div style={{ maxHeight: '100px', overflow: 'auto' }}>
                                  {row.response && typeof row.response === 'string' 
                                    ? row.response.substring(0, 200) + (row.response.length > 200 ? '...' : '') 
                                    : 'N/A'}
                                </div>
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
              
              {showDetails && (
                <div style={styles.chartContainer}>
                  <h3>Detailed Tactic Statistics</h3>
                  <div style={{ maxHeight: '400px', overflow: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr style={{ backgroundColor: '#f3f4f6' }}>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Tactic</th>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Success Rate</th>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Success</th>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Fail</th>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {tacticSuccessRates
                          .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate :
                               sortBy === 'fail' ? b.failRate - a.failRate :
                               sortBy === 'total' ? b.total - a.total :
                               a.name.localeCompare(b.name))
                          .map((tactic, index) => {
                            const parts = tactic.name.split('/');
                            const shortName = parts[parts.length - 1];
                            
                            return (
                              <tr 
                                key={index} 
                                style={{ 
                                  backgroundColor: tactic.name === selectedTactic ? '#f0f9ff' : index % 2 ? '#f9f9f9' : 'white'
                                }}
                              >
                                <td style={{ 
                                  border: '1px solid #ddd', 
                                  padding: '8px',
                                  fontWeight: tactic.name === selectedTactic ? 'bold' : 'normal'
                                }}>
                                  {shortName}
                                </td>
                                <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                                  {tactic.successRate.toFixed(2)}%
                                </td>
                                <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                                  {tactic.success}
                                </td>
                                <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                                  {tactic.fail}
                                </td>
                                <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                                  {tactic.total}
                                </td>
                              </tr>
                            );
                          })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Tactic Analysis Tab */}
          {activeTab === 'tacticAnalysis' && (
            <div>
              <h2 style={{ borderBottom: '1px solid #e5e7eb', paddingBottom: '0.5rem' }}>Tactic vs Test Case Analysis</h2>
              
              <div style={styles.chartContainer}>
                <h3>Tactic vs Test Case Success Rate Heatmap</h3>
                <p>This heatmap shows the success rate of each tactic against each test case.</p>
                
                {heatmapData ? (
                  <HeatMap 
                    data={heatmapData}
                    testCases={uniqueTestCases}
                    tactics={uniqueTactics} 
                    title="Success Rate (%)" 
                    colorRamp={[
                      '#e6f0ff', '#b3d1ff', '#80b3ff', '#4d94ff', '#1a75ff', 
                      '#0066ff', '#0047b3', '#003366', '#002147', '#001429'
                    ]}
                  />
                ) : (
                  <div>Loading heatmap data...</div>
                )}
              </div>
              
              {selectedTactic && (
                <div style={styles.chartContainer}>
                  <h3>Test Case Success Rates for {selectedTactic}</h3>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart
                      data={uniqueTestCases.map(testCase => {
                        const testCaseData = data.filter(row => 
                          row.jailbreak_tactic === selectedTactic && 
                          row.test_case === testCase
                        );
                        const success = testCaseData.filter(row => 
                          row.success === true || row.success === 1
                        ).length;
                        return {
                          name: testCase,
                          successRate: testCaseData.length > 0 ? (success / testCaseData.length) * 100 : 0,
                          total: testCaseData.length,
                          success,
                          fail: testCaseData.length - success,
                          standardError: testCaseData.length > 0 ? 
                            calculateStandardError([...Array(success).fill(1), ...Array(testCaseData.length - success).fill(0)]) : 0
                        };
                      })
                      .filter(item => item.total > 0)
                      .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate :
                           sortBy === 'fail' ? (100 - b.successRate) - (100 - a.successRate) :
                           sortBy === 'total' ? b.total - a.total :
                           a.name.localeCompare(b.name))
                      }
                      margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="name" 
                        angle={-45} 
                        textAnchor="end" 
                        height={100} 
                        interval={0}
                      />
                      <YAxis label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
                      <Legend />
                      <Bar dataKey="successRate" name="Success Rate" fill="#8884d8">
                        {uniqueTestCases.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                        {showDetails && <ErrorBar dataKey="standardError" width={4} strokeWidth={2} stroke="#8884d8" />}
                        <LabelList dataKey="total" position="insideTop" formatter={(value) => `n=${value}`} />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
              
              {selectedTestCase && (
                <div style={styles.chartContainer}>
                  <h3>Tactic Success Rates for {selectedTestCase}</h3>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart
                      data={uniqueTactics.map(tactic => {
                        const tacticData = data.filter(row => 
                          row.jailbreak_tactic === tactic && 
                          row.test_case === selectedTestCase
                        );
                        const success = tacticData.filter(row => 
                          row.success === true || row.success === 1
                        ).length;
                        return {
                          name: tactic,
                          successRate: tacticData.length > 0 ? (success / tacticData.length) * 100 : 0,
                          total: tacticData.length,
                          success,
                          fail: tacticData.length - success,
                          standardError: tacticData.length > 0 ? 
                            calculateStandardError([...Array(success).fill(1), ...Array(tacticData.length - success).fill(0)]) : 0
                        };
                      })
                      .filter(item => item.total > 0)
                      .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate :
                           sortBy === 'fail' ? (100 - b.successRate) - (100 - a.successRate) :
                           sortBy === 'total' ? b.total - a.total :
                           a.name.localeCompare(b.name))
                      }
                      margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="name" 
                        angle={-45} 
                        textAnchor="end" 
                        height={100} 
                        interval={0}
                      />
                      <YAxis label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
                      <Legend />
                      <Bar dataKey="successRate" name="Success Rate" fill="#8884d8">
                        {uniqueTactics.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                        {showDetails && <ErrorBar dataKey="standardError" width={4} strokeWidth={2} stroke="#8884d8" />}
                        <LabelList dataKey="total" position="insideTop" formatter={(value) => `n=${value}`} />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
              
              {showDetails && (
                <div style={styles.chartContainer}>
                  <h3>Detailed Success Rates by Tactic and Test Case</h3>
                  <div style={{ maxHeight: '400px', overflow: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr style={{ backgroundColor: '#f3f4f6' }}>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Tactic</th>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Test Case</th>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Success Rate</th>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Success</th>
                          <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {heatmapData && heatmapData
                          .sort((a, b) => {
                            if (sortBy === 'success') return b.successRate - a.successRate;
                            if (sortBy === 'fail') return a.successRate - b.successRate;
                            if (sortBy === 'total') return b.count - a.count;
                            return a.tactic.localeCompare(b.tactic) || a.testCase.localeCompare(b.testCase);
                          })
                          .filter(item => item.count > 0)
                          .map((item, index) => (
                            <tr 
                              key={index} 
                              style={{ 
                                backgroundColor: (item.tactic === selectedTactic && item.testCase === selectedTestCase) ? 
                                  '#f0f9ff' : index % 2 ? '#f9f9f9' : 'white'
                              }}
                            >
                              <td style={{ 
                                border: '1px solid #ddd', 
                                padding: '8px',
                                fontWeight: item.tactic === selectedTactic ? 'bold' : 'normal'
                              }}>
                                {item.tactic}
                              </td>
                              <td style={{ 
                                border: '1px solid #ddd', 
                                padding: '8px',
                                fontWeight: item.testCase === selectedTestCase ? 'bold' : 'normal'
                              }}>
                                {item.testCase}
                              </td>
                              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                                {item.successRate.toFixed(2)}%
                              </td>
                              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                                {item.successCount}
                              </td>
                              <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                                {item.count}
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Evaluator Analysis Tab */}
          {activeTab === 'evaluatorAnalysis' && (
            <div style={{ marginTop: '20px' }}>
              <h2>Evaluator Correlation Analysis</h2>
              <p>This section analyzes how different evaluator models judge the same experiments.</p>
              
              {uniqueEvaluators.length < 2 ? (
                <div style={{ 
                  padding: '20px', 
                  backgroundColor: '#fff9f0', 
                  borderRadius: '5px', 
                  borderLeft: '4px solid #ff9800',
                  marginBottom: '20px'
                }}>
                  <h3>Insufficient Data</h3>
                  <p>At least two different evaluator models are required for correlation analysis. The current dataset contains only {uniqueEvaluators.length} evaluator model(s).</p>
                  <p>Available evaluator(s): {uniqueEvaluators.map(e => e || 'Unknown').join(', ')}</p>
                </div>
              ) : (
                <div>
                  <div style={{ 
                    margin: '20px 0', 
                    padding: '20px', 
                    backgroundColor: 'white', 
                    borderRadius: '8px',
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                  }}>
                    <h3>Evaluator Pairs Correlation Analysis</h3>
                    <p>This analysis examines how different evaluator models assess the same prompts. Higher correlation values indicate similar judgments.</p>
                    
                    {(() => {
                      // Find experiment runs that differ only by evaluator model
                      const runsByParameters = {};
                      
                      data.forEach(row => {
                        if (!row.evaluator_model) return;
                        
                        // Create a key based only on the specified parameters
                        const key = `${row.jailbreak_tactic || ''}_${row.test_case || ''}_${row.turn_type || ''}_${row.target_model || ''}_${row.target_temp || ''}_${row.max_round || ''}_${row.attacker_model || ''}`;
                        
                        // Create a sub-key for the evaluator to handle duplicates
                        const evalKey = row.evaluator_model || 'unknown';
                        
                        if (!runsByParameters[key]) {
                          runsByParameters[key] = {};
                        }
                        
                        // Only store the first row for each evaluator
                        if (!runsByParameters[key][evalKey]) {
                          runsByParameters[key][evalKey] = row;
                        }
                      });
                      
                      // Filter for parameter sets that have multiple evaluators
                      const multiEvaluatorRuns = Object.entries(runsByParameters)
                        .filter(([_, evaluatorMap]) => Object.keys(evaluatorMap).length > 1)
                        .map(([_, evaluatorMap]) => Object.values(evaluatorMap));
                      
                      if (multiEvaluatorRuns.length === 0) {
                        return (
                          <div style={{ 
                            padding: '15px', 
                            backgroundColor: '#f0f4ff', 
                            borderRadius: '5px', 
                            borderLeft: '4px solid #4285f4',
                            marginBottom: '20px'
                          }}>
                            <p>No matching experiment runs with different evaluators found in the dataset.</p>
                          </div>
                        );
                      }
                      
                      // Calculate correlation data between pairs of evaluators
                      const evaluatorPairs = {};
                      const totalPairs = {};
                      const agreementCounts = {};
                      
                      multiEvaluatorRuns.forEach(runs => {
                        // Group by evaluator
                        const evaluatorResults = {};
                        runs.forEach(run => {
                          evaluatorResults[run.evaluator_model] = run.goal_achieved === true || 
                            run.goal_achieved === 'true' || run.goal_achieved === 1 || 
                            run.success === true || run.success === 'true' || run.success === 1;
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
                              evaluatorPairs[pairKey] = { evalA, evalB };
                            }
                            
                            totalPairs[pairKey]++;
                            
                            // Check if they agree
                            if (evaluatorResults[evalA] === evaluatorResults[evalB]) {
                              agreementCounts[pairKey]++;
                            }
                          }
                        }
                      });
                      
                      // Calculate correlation percentages
                      const correlationData = Object.keys(totalPairs).map(pairKey => {
                        const { evalA, evalB } = evaluatorPairs[pairKey];
                        const total = totalPairs[pairKey];
                        const agreements = agreementCounts[pairKey];
                        const correlation = (agreements / total) * 100;
                        
                        return {
                          pairKey,
                          evalA: evalA || 'Unknown',
                          evalB: evalB || 'Unknown',
                          total,
                          agreements,
                          correlation,
                          disagreements: total - agreements
                        };
                      }).sort((a, b) => b.correlation - a.correlation);
                      
                      return (
                        <>
                          <div style={{ 
                            padding: '15px', 
                            backgroundColor: '#e6f7ff', 
                            borderRadius: '5px', 
                            borderLeft: '4px solid #1890ff',
                            marginBottom: '20px'
                          }}>
                            <p><strong>Parameters used for matching:</strong> jailbreak_tactic, test_case, turn_type, target_model, target_temp, max_round, attacker_model</p>
                            <p>Found {multiEvaluatorRuns.length} experiment runs with multiple evaluators.</p>
                          </div>
                          
                          {/* Show a sample of the data for transparency */}
                          {multiEvaluatorRuns.length > 0 && (
                            <div style={{ marginTop: '20px', marginBottom: '20px' }}>
                              <h4>Sample Matching Run:</h4>
                              <div style={{ backgroundColor: '#f8f9fa', padding: '15px', borderRadius: '5px', fontSize: '0.9em' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                  <tbody>
                                    {['jailbreak_tactic', 'test_case', 'turn_type', 'target_model', 'target_temp', 'max_round', 'attacker_model'].map(key => (
                                      <tr key={key}>
                                        <td style={{ padding: '4px 10px', fontWeight: 'bold', width: '150px' }}>{key}:</td>
                                        <td style={{ padding: '4px 10px' }}>{multiEvaluatorRuns[0][0][key] || "N/A"}</td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                              
                              <h4 style={{ marginTop: '15px' }}>Evaluator Results:</h4>
                              <div style={{ overflowX: 'auto' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                  <thead>
                                    <tr>
                                      <th style={{ padding: '8px', borderBottom: '2px solid #ddd', textAlign: 'left' }}>Evaluator Model</th>
                                      <th style={{ padding: '8px', borderBottom: '2px solid #ddd', textAlign: 'center' }}>Goal Achieved</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {multiEvaluatorRuns[0].map((run, index) => {
                                      const isSuccess = run.goal_achieved === true || 
                                        run.goal_achieved === 'true' || run.goal_achieved === 1 || 
                                        run.success === true || run.success === 'true' || run.success === 1;
                                      
                                      return (
                                        <tr key={index}>
                                          <td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>
                                            {run.evaluator_model || "Unknown"}
                                          </td>
                                          <td style={{ 
                                            padding: '8px', 
                                            borderBottom: '1px solid #ddd',
                                            textAlign: 'center',
                                            backgroundColor: isSuccess ? 'rgba(40, 167, 69, 0.1)' : 'rgba(220, 53, 69, 0.1)',
                                            color: isSuccess ? '#28a745' : '#dc3545',
                                            fontWeight: 'bold'
                                          }}>
                                            {isSuccess ? 'Success' : 'Failure'}
                                          </td>
                                        </tr>
                                      );
                                    })}
                                  </tbody>
                                </table>
                              </div>
                            </div>
                          )}
                          
                          <div style={{ overflowX: 'auto', marginTop: '20px' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                              <thead>
                                <tr>
                                  <th style={{ padding: '10px', borderBottom: '2px solid #ddd', textAlign: 'left' }}>Evaluator Pair</th>
                                  <th style={{ padding: '10px', borderBottom: '2px solid #ddd', textAlign: 'center' }}>Correlation</th>
                                  <th style={{ padding: '10px', borderBottom: '2px solid #ddd', textAlign: 'center' }}>Agreements</th>
                                  <th style={{ padding: '10px', borderBottom: '2px solid #ddd', textAlign: 'center' }}>Disagreements</th>
                                  <th style={{ padding: '10px', borderBottom: '2px solid #ddd', textAlign: 'center' }}>Total Comparisons</th>
                                </tr>
                              </thead>
                              <tbody>
                                {correlationData.map((data, index) => (
                                  <tr key={index}>
                                    <td style={{ padding: '10px', borderBottom: '1px solid #ddd' }}>
                                      <strong>{data.evalA}</strong> vs <strong>{data.evalB}</strong>
                                    </td>
                                    <td style={{ 
                                      padding: '10px', 
                                      borderBottom: '1px solid #ddd', 
                                      textAlign: 'center',
                                      backgroundColor: `rgba(${255 - Math.round(data.correlation * 2.55)}, ${Math.round(data.correlation * 2.55)}, 100, 0.2)`,
                                      fontWeight: 'bold'
                                    }}>
                                      {data.correlation.toFixed(1)}%
                                    </td>
                                    <td style={{ padding: '10px', borderBottom: '1px solid #ddd', textAlign: 'center' }}>
                                      {data.agreements}
                                    </td>
                                    <td style={{ padding: '10px', borderBottom: '1px solid #ddd', textAlign: 'center' }}>
                                      {data.disagreements}
                                    </td>
                                    <td style={{ padding: '10px', borderBottom: '1px solid #ddd', textAlign: 'center' }}>
                                      {data.total}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                          
                          <div style={{ marginTop: '30px' }}>
                            <h3>Evaluator Correlation Visualization</h3>
                            
                            <ResponsiveContainer width="100%" height={400}>
                              <BarChart
                                data={correlationData}
                                margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                              >
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis 
                                  dataKey="pairKey" 
                                  angle={-45} 
                                  textAnchor="end" 
                                  height={100} 
                                  interval={0}
                                  tick={{ fontSize: 12 }}
                                  tickFormatter={(value) => value.replace('_vs_', ' vs ')}
                                />
                                <YAxis 
                                  label={{ value: 'Correlation (%)', angle: -90, position: 'insideLeft' }} 
                                  domain={[0, 100]}
                                />
                                <Tooltip 
                                  formatter={(value, name) => {
                                    if (name === 'correlation') return [`${value.toFixed(1)}%`, 'Correlation'];
                                    return [value, name];
                                  }}
                                />
                                <Legend />
                                <Bar dataKey="correlation" name="Correlation" fill="#8884d8" />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                          
                          <div style={{ marginTop: '30px' }}>
                            <h3>Agreements vs Disagreements</h3>
                            
                            <ResponsiveContainer width="100%" height={400}>
                              <BarChart
                                data={correlationData}
                                margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                                stackOffset="expand"
                                layout="vertical"
                              >
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis 
                                  type="number" 
                                  tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                                />
                                <YAxis 
                                  type="category"
                                  dataKey="pairKey"
                                  width={150}
                                  tickFormatter={(value) => value.replace('_vs_', ' vs ')}
                                />
                                <Tooltip 
                                  formatter={(value, name, props) => {
                                    const percent = (value / props.payload.total) * 100;
                                    return [`${value} (${percent.toFixed(1)}%)`, name === 'agreements' ? 'Agreements' : 'Disagreements'];
                                  }}
                                />
                                <Legend />
                                <Bar dataKey="agreements" name="Agreements" stackId="a" fill="#82ca9d" />
                                <Bar dataKey="disagreements" name="Disagreements" stackId="a" fill="#ff8042" />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </>
                      );
                    })()}
                  </div>
                  
                  <div style={{ 
                    margin: '20px 0', 
                    padding: '20px', 
                    backgroundColor: 'white', 
                    borderRadius: '8px',
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                  }}>
                    <h3>Evaluator Comparison by Model/Test Case</h3>
                    <p>This analysis shows how evaluator judgments vary across models and test cases.</p>
                    
                    <div style={{ marginBottom: '20px' }}>
                      <select
                        value={selectedEvaluator || ''}
                        onChange={(e) => setSelectedEvaluator(e.target.value || null)}
                        style={{
                          padding: '8px 12px',
                          borderRadius: '4px',
                          border: '1px solid #d1d5db',
                          marginRight: '10px'
                        }}
                      >
                        <option value="">Select Primary Evaluator</option>
                        {uniqueEvaluators.map(evaluator => (
                          <option key={evaluator} value={evaluator}>{evaluator || 'Unknown'}</option>
                        ))}
                      </select>
                    </div>
                    
                    {selectedEvaluator && (() => {
                      // Get data for the selected evaluator
                      const evaluatorData = data.filter(row => row.evaluator_model === selectedEvaluator);
                      
                      if (evaluatorData.length === 0) {
                        return <p>No data found for the selected evaluator.</p>;
                      }
                      
                      // Analyze by model
                      const modelAnalysis = uniqueModels
                        .map(model => {
                          const modelData = evaluatorData.filter(row => row.model === model);
                          if (modelData.length === 0) return null;
                          
                          const successCount = modelData.filter(row => 
                            row.goal_achieved === true || row.goal_achieved === 'true' || 
                            row.goal_achieved === 1 || row.success === true || 
                            row.success === 'true' || row.success === 1
                          ).length;
                          
                          return {
                            model,
                            total: modelData.length,
                            successCount,
                            successRate: (successCount / modelData.length) * 100
                          };
                        })
                        .filter(Boolean)
                        .sort((a, b) => b.successRate - a.successRate);
                      
                      // Analyze by test case
                      const testCaseAnalysis = uniqueTestCases
                        .map(testCase => {
                          const testCaseData = evaluatorData.filter(row => row.test_case === testCase);
                          if (testCaseData.length === 0) return null;
                          
                          const successCount = testCaseData.filter(row => 
                            row.goal_achieved === true || row.goal_achieved === 'true' || 
                            row.goal_achieved === 1 || row.success === true || 
                            row.success === 'true' || row.success === 1
                          ).length;
                          
                          return {
                            testCase,
                            total: testCaseData.length,
                            successCount,
                            successRate: (successCount / testCaseData.length) * 100
                          };
                        })
                        .filter(Boolean)
                        .sort((a, b) => b.successRate - a.successRate);
                      
                      return (
                        <>
                          <h3>Success Rates by Model for {selectedEvaluator}</h3>
                          <ResponsiveContainer width="100%" height={400}>
                            <BarChart
                              data={modelAnalysis}
                              margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                            >
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis 
                                dataKey="model" 
                                angle={-45} 
                                textAnchor="end" 
                                height={100} 
                                interval={0}
                              />
                              <YAxis 
                                label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} 
                                domain={[0, 100]}
                              />
                              <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
                              <Legend />
                              <Bar dataKey="successRate" name="Success Rate" fill="#8884d8">
                                {modelAnalysis.map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                              </Bar>
                            </BarChart>
                          </ResponsiveContainer>
                          
                          <h3 style={{ marginTop: '30px' }}>Success Rates by Test Case for {selectedEvaluator}</h3>
                          <ResponsiveContainer width="100%" height={400}>
                            <BarChart
                              data={testCaseAnalysis}
                              margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
                            >
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis 
                                dataKey="testCase" 
                                angle={-45} 
                                textAnchor="end" 
                                height={100} 
                                interval={0}
                              />
                              <YAxis 
                                label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft' }} 
                                domain={[0, 100]}
                              />
                              <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
                              <Legend />
                              <Bar dataKey="successRate" name="Success Rate" fill="#82ca9d">
                                {testCaseAnalysis.map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                              </Bar>
                            </BarChart>
                          </ResponsiveContainer>
                        </>
                      );
                    })()}
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Data summary when no specific tab is active or at the bottom of the page */}
          <div style={{
            marginTop: '2rem',
            padding: '1rem',
            backgroundColor: '#f8fafc',
            borderRadius: '0.5rem',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            display: 'flex',
            flexWrap: 'wrap',
            gap: '2rem'
          }}>
            <div>
              <h3 style={{ borderBottom: '1px solid #e5e7eb', paddingBottom: '0.5rem' }}>Filtered Data Summary</h3>
              <table style={{ borderCollapse: 'collapse' }}>
                <tbody>
                  <tr>
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb' }}>Showing:</td>
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb', fontWeight: 'bold' }}>
                      {filteredData.length} of {data.length} evaluations 
                      ({((filteredData.length / data.length) * 100).toFixed(1)}%)
                    </td>
                  </tr>
                  <tr>
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb' }}>Success Rate:</td>
                    <td style={{ 
                      padding: '0.5rem', 
                      borderBottom: '1px solid #e5e7eb', 
                      fontWeight: 'bold',
                      color: filteredData.length > 0 
                        ? ((filteredData.filter(row => row.success === true || row.success === 1).length / filteredData.length) * 100) > 50
                          ? '#047857'  // green for higher success rates
                          : '#b91c1c'  // red for lower success rates
                        : 'inherit'
                    }}>
                      {filteredData.length > 0 
                        ? ((filteredData.filter(row => row.success === true || row.success === 1).length / filteredData.length) * 100).toFixed(2) 
                        : 0}%
                    </td>
                  </tr>
                  <tr>
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb' }}>Models:</td>
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb', fontWeight: 'bold' }}>
                      {new Set(filteredData.map(row => row.model)).size}
                    </td>
                  </tr>
                  <tr>
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb' }}>Test Cases:</td>
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb', fontWeight: 'bold' }}>
                      {new Set(filteredData.map(row => row.test_case)).size}
                    </td>
                  </tr>
                  <tr>
                    <td style={{ padding: '0.5rem' }}>Tactics:</td>
                    <td style={{ padding: '0.5rem', fontWeight: 'bold' }}>
                      {new Set(filteredData.map(row => row.jailbreak_tactic)).size}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            {filteredData.length > 0 && (
              <div style={{ flex: 1, minWidth: '300px' }}>
                <h3 style={{ borderBottom: '1px solid #e5e7eb', paddingBottom: '0.5rem' }}>Success Breakdown</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Success', value: filteredData.filter(row => row.success === true || row.success === 1).length, fill: '#82ca9d' },
                        { name: 'Failure', value: filteredData.filter(row => row.success !== true && row.success !== 1).length, fill: '#ff6b6b' }
                      ]}
                      cx="50%"
                      cy="50%"
                      outerRadius={60}
                      dataKey="value"
                      label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    />
                    <Tooltip formatter={(value) => [`${value} evaluations`, ""]} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </>
      )}
      
      {/* Fallback when no data is available */}
      {!loading && !error && data.length === 0 && (
        <div style={{ 
          padding: '2rem',
          margin: '2rem 0', 
          textAlign: 'center',
          backgroundColor: '#f9fafb',
          borderRadius: '0.5rem'
        }}>
          <h3>No Data Available</h3>
          <p>No evaluation data found. Please make sure the CSV file is properly formatted and contains data.</p>
          <p>Try placing master_results.csv in the public directory.</p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#3B82F6',
              color: 'white',
              border: 'none',
              borderRadius: '0.25rem',
              cursor: 'pointer',
              marginTop: '0.5rem'
            }}
          >
            Refresh
          </button>
        </div>
      )}
    </div>
  );
};

export default EvaluatorViz; 