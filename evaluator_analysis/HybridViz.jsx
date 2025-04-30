import React, { useState, useEffect, useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, PieChart, Pie
} from 'recharts';
import Papa from 'papaparse';

// Color palette
const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE', 
  '#00C49F', '#FFBB28', '#FF8042', '#a4de6c', '#d0ed57'
];

// Default heatmap color ramp
const HEATMAP_COLORS = [
  '#e6f0ff', '#b3d1ff', '#80b3ff', '#4d94ff', '#1a75ff', 
  '#0066ff', '#0047b3', '#003366', '#002147', '#001429'
];

const HybridViz = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState('Starting');
  const [chartType, setChartType] = useState('bar');
  const [modelSuccessRates, setModelSuccessRates] = useState([]);
  const [tacticSuccessRates, setTacticSuccessRates] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [activeTab, setActiveTab] = useState("overview");
  const [selectedModel, setSelectedModel] = useState(null);
  const [selectedTestCase, setSelectedTestCase] = useState(null);
  const [selectedTactic, setSelectedTactic] = useState(null);
  const [sortBy, setSortBy] = useState("success");
  const [uniqueModels, setUniqueModels] = useState([]);
  const [uniqueTestCases, setUniqueTestCases] = useState([]);
  const [uniqueTactics, setUniqueTactics] = useState([]);
  const [heatmapData, setHeatmapData] = useState([]);

  useEffect(() => {
    const loadData = async () => {
      try {
        setStatus('Trying to load sample data...');
        let response = await fetch('/sample_results.csv');
        
        if (!response.ok) {
          setStatus('Sample data not found, trying master_results.csv...');
          response = await fetch('/master_results.csv');
          
          if (!response.ok) {
            throw new Error(`Failed to fetch data: ${response.status}`);
          }
          setStatus('Master results data found');
        } else {
          setStatus('Sample data found');
        }
        
        setStatus('Reading data...');
        const text = await response.text();
        
        setStatus('Parsing data...');
        const result = Papa.parse(text, {
          header: true,
          skipEmptyLines: true,
          comments: "#"
        });
        
        if (!result.data || result.data.length === 0) {
          throw new Error("No data rows found after parsing CSV");
        }
        
        // Clean the data - handle different formats
        const cleanedData = result.data.map(row => {
          // Ensure goal_achieved is consistently formatted
          if (typeof row.goal_achieved === 'string') {
            row.goal_achieved = row.goal_achieved.toLowerCase() === 'true';
          }
          
          // Set model field for consistent access
          row.model = row.target_model || row.model;
          row.success = row.goal_achieved;
          
          return row;
        });
        
        setData(cleanedData);
        setFilteredData(cleanedData);
        setStatus(`Data loaded successfully - ${cleanedData.length} rows`);
        setLoading(false);
      } catch (err) {
        console.error("Error loading data:", err);
        setError(err.message);
        setStatus('Error loading data');
        setLoading(false);
      }
    };
    
    loadData();
  }, []);

  // Calculate model success rates when data changes
  useEffect(() => {
    if (data.length > 0) {
      const modelData = {};
      
      // Group by model
      data.forEach(row => {
        const model = row.model || row.target_model;
        if (!model) return;
        
        if (!modelData[model]) {
          modelData[model] = {
            name: model,
            success: 0,
            fail: 0,
            total: 0
          };
        }
        
        modelData[model].total += 1;
        if (row.success === true || row.goal_achieved === true || row.success === 1 || row.goal_achieved === 1) {
          modelData[model].success += 1;
        } else {
          modelData[model].fail += 1;
        }
      });
      
      // Calculate success rates and convert to array
      const modelSuccessRatesArray = Object.values(modelData).map(model => {
        return {
          ...model,
          successRate: (model.success / model.total) * 100,
          failRate: (model.fail / model.total) * 100
        };
      });
      
      // Sort by success rate (high to low)
      modelSuccessRatesArray.sort((a, b) => b.successRate - a.successRate);
      
      setModelSuccessRates(modelSuccessRatesArray);
    }
  }, [data]);

  // Calculate tactic success rates
  useEffect(() => {
    if (data.length > 0) {
      const tacticData = {};
      
      // Group by tactic
      data.forEach(row => {
        const tactic = row.jailbreak_tactic;
        if (!tactic) return;
        
        if (!tacticData[tactic]) {
          tacticData[tactic] = {
            name: tactic,
            success: 0,
            fail: 0,
            total: 0
          };
        }
        
        tacticData[tactic].total += 1;
        if (row.success === true || row.goal_achieved === true || row.success === 1 || row.goal_achieved === 1) {
          tacticData[tactic].success += 1;
        } else {
          tacticData[tactic].fail += 1;
        }
      });
      
      // Calculate success rates and convert to array
      const tacticSuccessRatesArray = Object.values(tacticData).map(tactic => {
        return {
          ...tactic,
          successRate: (tactic.success / tactic.total) * 100,
          failRate: (tactic.fail / tactic.total) * 100
        };
      });
      
      // Sort by success rate (high to low)
      tacticSuccessRatesArray.sort((a, b) => b.successRate - a.successRate);
      
      setTacticSuccessRates(tacticSuccessRatesArray);
    }
  }, [data]);

  // Helper functions
  const getModelField = (row) => row.target_model || row.model || "Unknown Model";
  const getTestCaseField = (row) => row.test_case || "Unknown Test Case";
  const getTacticField = (row) => row.jailbreak_tactic || row.tactic || "Unknown Tactic";
  const isSuccessful = (row) => {
    if (row.goal_achieved !== undefined) {
      return row.goal_achieved === true || row.goal_achieved === 'true' || row.goal_achieved === 1;
    } else if (row.success !== undefined) {
      return row.success === true || row.success === 'true' || row.success === 1;
    }
    return false;
  };

  // After data loading
  useEffect(() => {
    if (data.length > 0) {
      // Extract unique values for filters
      setUniqueModels([...new Set(data.map(getModelField))].filter(Boolean));
      setUniqueTestCases([...new Set(data.map(getTestCaseField))].filter(Boolean));
      setUniqueTactics([...new Set(data.map(getTacticField))].filter(Boolean));
    }
  }, [data]);

  // Filter data based on selections
  useEffect(() => {
    if (data.length > 0) {
      const filtered = data.filter(row => {
        const modelMatch = !selectedModel || getModelField(row) === selectedModel;
        const testCaseMatch = !selectedTestCase || getTestCaseField(row) === selectedTestCase;
        const tacticMatch = !selectedTactic || getTacticField(row) === selectedTactic;
        
        return modelMatch && testCaseMatch && tacticMatch;
      });
      
      setFilteredData(filtered);
    }
  }, [data, selectedModel, selectedTestCase, selectedTactic]);

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
                  getTestCaseField(row) === testCase && 
                  getTacticField(row) === tactic;
          });
          
          if (filteredData.length > 0) {
            // Calculate success rate
            const successCount = filteredData.filter(isSuccessful).length;
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
    
    return heatmapData;
  };

  // Update heatmap data when test cases or tactics change
  useEffect(() => {
    if (data.length > 0 && uniqueTestCases.length > 0 && uniqueTactics.length > 0) {
      const newHeatmapData = generateHeatmapData(data, uniqueTestCases, uniqueTactics);
      setHeatmapData(newHeatmapData);
    }
  }, [data, uniqueTestCases, uniqueTactics]);

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

  // Advanced HeatMap component
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
      const colors = colorRamp || HEATMAP_COLORS;
      
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
          colorRamp={colorRamp || HEATMAP_COLORS}
        />
        
        <div style={{ position: 'relative', width: totalWidth, height: totalHeight, marginBottom: '2rem' }}>
          {/* Column headers (tactics) */}
          {tactics.map((tactic, colIndex) => (
            <div 
              key={`col-${colIndex}`}
              onClick={() => setSelectedTactic(tactic === selectedTactic ? null : tactic)}
              style={{
                position: 'absolute',
                top: 0,
                left: cellWidth * (colIndex + 1),
                width: cellWidth,
                height: cellHeight,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: tactic === selectedTactic ? '#e6f3ff' : '#f8f9fa',
                border: '1px solid #ddd',
                fontWeight: 'bold',
                fontSize: '12px',
                transform: 'rotate(-45deg)',
                transformOrigin: 'bottom left',
                overflow: 'hidden',
                paddingLeft: '5px',
                textAlign: 'left',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                cursor: 'pointer'
              }}
              title={tactic}
            >
              {tactic}
              {tactic === selectedTactic && ' ✓'}
            </div>
          ))}
          
          {/* Row headers (test cases) */}
          {testCases.map((testCase, rowIndex) => (
            <div 
              key={`row-${rowIndex}`}
              onClick={() => setSelectedTestCase(testCase === selectedTestCase ? null : testCase)}
              style={{
                position: 'absolute',
                top: cellHeight * (rowIndex + 1),
                left: 0,
                width: cellWidth,
                height: cellHeight,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'left',
                backgroundColor: testCase === selectedTestCase ? '#e6f3ff' : '#f8f9fa',
                border: '1px solid #ddd',
                fontWeight: 'bold',
                fontSize: '12px',
                padding: '0 5px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                cursor: 'pointer'
              }}
              title={testCase}
            >
              {testCase}
              {testCase === selectedTestCase && ' ✓'}
            </div>
          ))}
          
          {/* Data cells */}
          {data.map((item, index) => {
            try {
              const rowIndex = testCases.indexOf(item.testCase);
              const colIndex = tactics.indexOf(item.tactic);
              
              if (rowIndex === -1 || colIndex === -1) return null;
              
              const isSelected = item.tactic === selectedTactic && item.testCase === selectedTestCase;
              
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
                    border: isSelected ? '2px solid black' : '1px solid #ddd',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexDirection: 'column',
                    fontSize: '12px',
                    cursor: 'pointer'
                  }}
                  title={`${item.testCase} - ${item.tactic}: ${item.successRate.toFixed(1)}% (${item.successCount}/${item.count})`}
                  onClick={() => {
                    setSelectedTestCase(item.testCase);
                    setSelectedTactic(item.tactic);
                  }}
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

  // Render sort options
  const renderSortOptions = () => (
    <div style={{ flexBasis: '100%', marginTop: '10px' }}>
      <label style={{ marginRight: '0.5rem', fontWeight: '500' }}>Sort By:</label>
      <select
        value={sortBy}
        onChange={(e) => setSortBy(e.target.value)}
        style={{
          padding: '0.25rem 0.5rem',
          borderRadius: '0.25rem',
          border: '1px solid #d1d5db'
        }}
      >
        <option value="success">Success Rate (High to Low)</option>
        <option value="fail">Failure Rate (High to Low)</option>
        <option value="total">Sample Count (High to Low)</option>
        <option value="name">Name (A-Z)</option>
      </select>
    </div>
  );

  if (loading) {
    return (
      <div style={{ padding: '20px', margin: '20px', border: '1px solid #ccc' }}>
        <h2>Hybrid Visualization (Loading)</h2>
        <p>Status: {status}</p>
        <div style={{ 
          width: '100%', 
          height: '10px', 
          backgroundColor: '#eee',
          borderRadius: '5px',
          overflow: 'hidden'
        }}>
          <div style={{ 
            width: '30%', 
            height: '100%', 
            backgroundColor: 'blue',
            animation: 'loading 1s infinite alternate'
          }}></div>
        </div>
        <style>{`
          @keyframes loading {
            from { margin-left: 0; }
            to { margin-left: 70%; }
          }
        `}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', margin: '20px', border: '1px solid red', backgroundColor: '#ffeeee' }}>
        <h2>Hybrid Visualization (Error)</h2>
        <p>Error: {error}</p>
        <p>Status: {status}</p>
        <button onClick={() => window.location.reload()}>Reload</button>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', margin: '20px', border: '1px solid #ccc' }}>
      <h2>Hybrid Visualization</h2>
      <p>Successfully loaded {data.length} rows of data.</p>
      
      {/* Navigation Tabs */}
      <div className="tabs" style={{ display: 'flex', marginBottom: '1rem', borderBottom: '1px solid #e5e7eb' }}>
        {['overview', 'models', 'testCases', 'tactics', 'heatmap', 'tacticAnalysis'].map(tab => (
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
             tab === 'tactics' ? 'Tactics' :
             tab === 'heatmap' ? 'Heatmap' :
             'Advanced Analysis'}
          </div>
        ))}
      </div>
      
      {/* Chart Type & Filters */}
      <div style={{ 
        marginBottom: '1.5rem',
        padding: '1rem',
        backgroundColor: '#f9fafb',
        borderRadius: '0.5rem',
        boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          minWidth: '200px'
        }}>
          <label style={{ marginBottom: '0.25rem' }}>Chart Type:</label>
          <select
            value={chartType}
            onChange={(e) => setChartType(e.target.value)}
            style={{
              padding: '0.5rem',
              borderRadius: '0.25rem',
              border: '1px solid #d1d5db'
            }}
          >
            <option value="bar">Bar Chart</option>
            <option value="pie">Pie Chart</option>
          </select>
        </div>
        
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          minWidth: '200px'
        }}>
          <label style={{ marginBottom: '0.25rem' }}>Model:</label>
          <select
            value={selectedModel || ''}
            onChange={(e) => setSelectedModel(e.target.value || null)}
            style={{
              padding: '0.5rem',
              borderRadius: '0.25rem',
              border: '1px solid #d1d5db'
            }}
          >
            <option value="">All Models</option>
            {uniqueModels.map(model => (
              <option key={model} value={model}>{model}</option>
            ))}
          </select>
        </div>
        
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          minWidth: '200px'
        }}>
          <label style={{ marginBottom: '0.25rem' }}>Test Case:</label>
          <select
            value={selectedTestCase || ''}
            onChange={(e) => setSelectedTestCase(e.target.value || null)}
            style={{
              padding: '0.5rem',
              borderRadius: '0.25rem',
              border: '1px solid #d1d5db'
            }}
          >
            <option value="">All Test Cases</option>
            {uniqueTestCases.map(testCase => (
              <option key={testCase} value={testCase}>{testCase}</option>
            ))}
          </select>
        </div>
        
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          minWidth: '200px'
        }}>
          <label style={{ marginBottom: '0.25rem' }}>Tactic:</label>
          <select
            value={selectedTactic || ''}
            onChange={(e) => setSelectedTactic(e.target.value || null)}
            style={{
              padding: '0.5rem',
              borderRadius: '0.25rem',
              border: '1px solid #d1d5db'
            }}
          >
            <option value="">All Tactics</option>
            {uniqueTactics.map(tactic => (
              <option key={tactic} value={tactic}>{tactic}</option>
            ))}
          </select>
        </div>
        
        {renderSortOptions()}
      </div>
      
      {/* Display different content based on active tab */}
      {activeTab === 'overview' && (
        <>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', marginBottom: '30px' }}>
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
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb', fontWeight: 'bold' }}>
                      {[...new Set(data.map(getModelField))].length}
                    </td>
                  </tr>
                  <tr>
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb' }}>Test Cases:</td>
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb', fontWeight: 'bold' }}>
                      {[...new Set(data.map(getTestCaseField))].length}
                    </td>
                  </tr>
                  <tr>
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb' }}>Tactics:</td>
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb', fontWeight: 'bold' }}>
                      {[...new Set(data.map(getTacticField))].length}
                    </td>
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
                    {((data.filter(isSuccessful).length / data.length) * 100).toFixed(1)}%
                  </div>
                  
                  <ResponsiveContainer width="100%" height={150}>
                    <PieChart>
                      <Pie
                        data={[
                          { name: 'Success', value: data.filter(isSuccessful).length, fill: '#82ca9d' },
                          { name: 'Failure', value: data.length - data.filter(isSuccessful).length, fill: '#ff6b6b' }
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
          
          <div style={{ 
            margin: '20px 0', 
            padding: '20px', 
            backgroundColor: 'white', 
            borderRadius: '8px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
          }}>
            <h3>Top 10 Models by Success Rate</h3>
            <ResponsiveContainer width="100%" height={400}>
              {chartType === 'bar' ? (
                <BarChart
                  data={modelSuccessRates.slice(0, 10)}
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
                  </Bar>
                </BarChart>
              ) : (
                <PieChart>
                  <Pie
                    data={modelSuccessRates.slice(0, 10)}
                    cx="50%"
                    cy="50%"
                    outerRadius={150}
                    innerRadius={80}
                    dataKey="success"
                    nameKey="name"
                    label={({name, percent}) => `${name.split('/').pop()}: ${(percent * 100).toFixed(0)}%`}
                  >
                    {modelSuccessRates.slice(0, 10).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value, name, props) => {
                    const dataItem = modelSuccessRates.find(item => item.name === props.payload.name);
                    return [`${dataItem.successRate.toFixed(2)}% (${value} successes)`, props.payload.name];
                  }} />
                  <Legend 
                    formatter={(value) => value.length > 25 ? `${value.substring(0, 25)}...` : value}
                  />
                </PieChart>
              )}
            </ResponsiveContainer>
          </div>
                
          <div style={{ 
            margin: '20px 0', 
            padding: '20px', 
            backgroundColor: 'white', 
            borderRadius: '8px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
          }}>
            <h3>Tactics by Success Rate</h3>
            <ResponsiveContainer width="100%" height={400}>
              {chartType === 'bar' ? (
                <BarChart
                  data={tacticSuccessRates}
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
                  <Bar dataKey="successRate" name="Success Rate" fill="#82ca9d">
                    {tacticSuccessRates.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={COLORS[index % COLORS.length]} 
                      />
                    ))}
                  </Bar>
                </BarChart>
              ) : (
                <PieChart>
                  <Pie
                    data={tacticSuccessRates}
                    cx="50%"
                    cy="50%"
                    outerRadius={150}
                    innerRadius={80}
                    dataKey="success"
                    nameKey="name"
                    label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  >
                    {tacticSuccessRates.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value, name, props) => {
                    const dataItem = tacticSuccessRates.find(item => item.name === props.payload.name);
                    return [`${dataItem.successRate.toFixed(2)}% (${value} successes)`, props.payload.name];
                  }} />
                  <Legend />
                </PieChart>
              )}
            </ResponsiveContainer>
          </div>
          
          <div style={{ marginTop: '30px' }}>
            <h3>Simple Tactic vs Test Case Heatmap</h3>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ borderCollapse: 'collapse', minWidth: '100%' }}>
                <thead>
                  <tr>
                    <th style={{ border: '1px solid #ddd', padding: '8px', backgroundColor: '#f2f2f2' }}>Test Case / Tactic</th>
                    {[...new Set(data.map(getTacticField))].map((tactic, index) => (
                      <th key={index} style={{ border: '1px solid #ddd', padding: '8px', backgroundColor: '#f2f2f2' }}>
                        {tactic}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[...new Set(data.map(getTestCaseField))].map((testCase, rowIndex) => (
                    <tr key={rowIndex}>
                      <td style={{ border: '1px solid #ddd', padding: '8px', fontWeight: 'bold' }}>
                        {testCase}
                      </td>
                      {[...new Set(data.map(getTacticField))].map((tactic, colIndex) => {
                        const relevantData = data.filter(row => 
                          getTestCaseField(row) === testCase && 
                          getTacticField(row) === tactic
                        );
                        
                        if (relevantData.length === 0) {
                          return (
                            <td key={colIndex} style={{ border: '1px solid #ddd', padding: '8px', backgroundColor: '#f9f9f9', textAlign: 'center' }}>
                              N/A
                            </td>
                          );
                        }
                        
                        const successCount = relevantData.filter(isSuccessful).length;
                        const successRate = (successCount / relevantData.length) * 100;
                        
                        // Color gradient from red (0%) to green (100%)
                        const r = Math.round(255 * (1 - successRate / 100));
                        const g = Math.round(255 * (successRate / 100));
                        const color = `rgb(${r}, ${g}, 150)`;
                        
                        return (
                          <td 
                            key={colIndex} 
                            style={{ 
                              border: '1px solid #ddd', 
                              padding: '8px', 
                              backgroundColor: successRate > 0 ? color : '#f9f9f9',
                              color: successRate > 50 ? 'white' : 'black',
                              textAlign: 'center'
                            }}
                            title={`${testCase} - ${tactic}: ${successRate.toFixed(1)}% (${successCount}/${relevantData.length})`}
                          >
                            {successRate.toFixed(0)}%
                            <div style={{ fontSize: '9px' }}>({successCount}/{relevantData.length})</div>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
      
      {activeTab === 'models' && (
        <div style={{ 
          margin: '20px 0', 
          padding: '20px', 
          backgroundColor: 'white', 
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
        }}>
          <h3>Models by Success Rate {selectedModel && `(Selected: ${selectedModel})`}</h3>
          
          <ResponsiveContainer width="100%" height={500}>
            {chartType === 'bar' ? (
              <BarChart
                data={modelSuccessRates.sort((a, b) => 
                  sortBy === 'success' ? b.successRate - a.successRate :
                  sortBy === 'fail' ? b.failRate - a.failRate :
                  sortBy === 'total' ? b.total - a.total :
                  a.name.localeCompare(b.name)
                )}
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
                  {modelSuccessRates.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.name === selectedModel ? '#ff7300' : COLORS[index % COLORS.length]}
                      stroke={entry.name === selectedModel ? '#000000' : undefined}
                      strokeWidth={entry.name === selectedModel ? 1 : 0}
                    />
                  ))}
                </Bar>
              </BarChart>
            ) : (
              <PieChart>
                <Pie
                  data={modelSuccessRates}
                  cx="50%"
                  cy="50%"
                  outerRadius={160}
                  innerRadius={80}
                  dataKey="success"
                  nameKey="name"
                  label={({name, percent}) => `${name.split('/').pop()}: ${(percent * 100).toFixed(0)}%`}
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
                <Legend formatter={(value) => value.length > 25 ? `${value.substring(0, 25)}...` : value} />
              </PieChart>
            )}
          </ResponsiveContainer>
          
          {selectedModel && (
            <div style={{ marginTop: '30px' }}>
              <h3>Test Case Success Rates for {selectedModel}</h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart
                  data={uniqueTestCases.map(testCase => {
                    const testCaseData = data.filter(row => 
                      getModelField(row) === selectedModel && 
                      getTestCaseField(row) === testCase
                    );
                    const successCount = testCaseData.filter(isSuccessful).length;
                    return {
                      name: testCase,
                      successRate: testCaseData.length > 0 ? (successCount / testCaseData.length) * 100 : 0,
                      total: testCaseData.length,
                      success: successCount,
                      fail: testCaseData.length - successCount
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
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
      
      {activeTab === 'testCases' && (
        <div style={{ 
          margin: '20px 0', 
          padding: '20px', 
          backgroundColor: 'white', 
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
        }}>
          <h3>Test Cases Analysis {selectedTestCase && `(Selected: ${selectedTestCase})`}</h3>
          
          <div style={{ marginBottom: '20px' }}>
            <p>This section shows success rates for each test case across all tactics and models.</p>
          </div>
          
          <ResponsiveContainer width="100%" height={500}>
            {chartType === 'bar' ? (
              <BarChart
                data={uniqueTestCases.map(testCase => {
                  const testCaseData = data.filter(row => getTestCaseField(row) === testCase);
                  const successCount = testCaseData.filter(isSuccessful).length;
                  return {
                    name: testCase,
                    successRate: testCaseData.length > 0 ? (successCount / testCaseData.length) * 100 : 0,
                    total: testCaseData.length,
                    success: successCount,
                    fail: testCaseData.length - successCount
                  };
                })
                .sort((a, b) => 
                  sortBy === 'success' ? b.successRate - a.successRate :
                  sortBy === 'fail' ? (100 - b.successRate) - (100 - a.successRate) :
                  sortBy === 'total' ? b.total - a.total :
                  a.name.localeCompare(b.name)
                )}
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
                  formatter={(value, name) => [`${value.toFixed(2)}%`, name]} 
                  labelFormatter={(label) => `Test Case: ${label}`}
                />
                <Legend />
                <Bar dataKey="successRate" name="Success Rate" fill="#8884d8">
                  {uniqueTestCases.map((testCase, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={testCase === selectedTestCase ? '#ff7300' : COLORS[index % COLORS.length]}
                      stroke={testCase === selectedTestCase ? '#000000' : undefined}
                      strokeWidth={testCase === selectedTestCase ? 2 : 0}
                    />
                  ))}
                </Bar>
              </BarChart>
            ) : (
              <PieChart>
                <Pie
                  data={uniqueTestCases.map(testCase => {
                    const testCaseData = data.filter(row => getTestCaseField(row) === testCase);
                    const successCount = testCaseData.filter(isSuccessful).length;
                    return {
                      name: testCase,
                      value: testCaseData.filter(isSuccessful).length,
                      successRate: testCaseData.length > 0 ? (successCount / testCaseData.length) * 100 : 0,
                      total: testCaseData.length
                    };
                  })}
                  cx="50%"
                  cy="50%"
                  outerRadius={160}
                  innerRadius={80}
                  dataKey="value"
                  nameKey="name"
                  label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
                >
                  {uniqueTestCases.map((testCase, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={testCase === selectedTestCase ? '#ff7300' : COLORS[index % COLORS.length]}
                      stroke={testCase === selectedTestCase ? '#000000' : undefined}
                      strokeWidth={testCase === selectedTestCase ? 2 : 0}
                    />
                  ))}
                </Pie>
                <Tooltip formatter={(value, name, props) => {
                  return [`${props.payload.successRate.toFixed(2)}% (${value} successes)`, name];
                }} />
                <Legend />
              </PieChart>
            )}
          </ResponsiveContainer>
          
          {selectedTestCase && (
            <div style={{ marginTop: '30px' }}>
              <h3>Tactics for {selectedTestCase}</h3>
              <p>Success rates for different tactics against the selected test case.</p>
              
              <ResponsiveContainer width="100%" height={400}>
                <BarChart
                  data={uniqueTactics.map(tactic => {
                    const combinationData = data.filter(row => 
                      getTestCaseField(row) === selectedTestCase && 
                      getTacticField(row) === tactic
                    );
                    const successCount = combinationData.filter(isSuccessful).length;
                    return {
                      name: tactic,
                      successRate: combinationData.length > 0 ? (successCount / combinationData.length) * 100 : 0,
                      total: combinationData.length,
                      success: successCount,
                      fail: combinationData.length - successCount
                    };
                  })
                  .filter(item => item.total > 0)
                  .sort((a, b) => b.successRate - a.successRate)
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
                  <Bar dataKey="successRate" name="Success Rate" fill="#82ca9d">
                    {uniqueTactics.map((tactic, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={tactic === selectedTactic ? '#ff7300' : COLORS[index % COLORS.length]}
                        stroke={tactic === selectedTactic ? '#000000' : undefined}
                        strokeWidth={tactic === selectedTactic ? 2 : 0}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
      
      {activeTab === 'tactics' && (
        <div style={{ 
          margin: '20px 0', 
          padding: '20px', 
          backgroundColor: 'white', 
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
        }}>
          <h3>Tactics Analysis {selectedTactic && `(Selected: ${selectedTactic})`}</h3>
          
          <div style={{ marginBottom: '20px' }}>
            <p>This section shows success rates for each tactic across all test cases and models.</p>
          </div>
          
          <ResponsiveContainer width="100%" height={500}>
            {chartType === 'bar' ? (
              <BarChart
                data={tacticSuccessRates.sort((a, b) => 
                  sortBy === 'success' ? b.successRate - a.successRate :
                  sortBy === 'fail' ? b.failRate - a.failRate :
                  sortBy === 'total' ? b.total - a.total :
                  a.name.localeCompare(b.name)
                )}
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
                <Bar dataKey="successRate" name="Success Rate" fill="#82ca9d">
                  {tacticSuccessRates.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.name === selectedTactic ? '#ff7300' : COLORS[index % COLORS.length]}
                      stroke={entry.name === selectedTactic ? '#000000' : undefined}
                      strokeWidth={entry.name === selectedTactic ? 2 : 0}
                    />
                  ))}
                </Bar>
              </BarChart>
            ) : (
              <PieChart>
                <Pie
                  data={tacticSuccessRates}
                  cx="50%"
                  cy="50%"
                  outerRadius={160}
                  innerRadius={80}
                  dataKey="success"
                  nameKey="name"
                  label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
                >
                  {tacticSuccessRates.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.name === selectedTactic ? '#ff7300' : COLORS[index % COLORS.length]}
                      stroke={entry.name === selectedTactic ? '#000000' : undefined}
                      strokeWidth={entry.name === selectedTactic ? 2 : 0}
                    />
                  ))}
                </Pie>
                <Tooltip formatter={(value, name, props) => {
                  const dataItem = tacticSuccessRates.find(item => item.name === props.payload.name);
                  return [`${dataItem.successRate.toFixed(2)}% (${value} successes)`, props.payload.name];
                }} />
                <Legend />
              </PieChart>
            )}
          </ResponsiveContainer>
          
          {selectedTactic && (
            <div style={{ marginTop: '30px' }}>
              <h3>Test Cases with {selectedTactic}</h3>
              <p>Success rates for different test cases using the selected tactic.</p>
              
              <ResponsiveContainer width="100%" height={400}>
                <BarChart
                  data={uniqueTestCases.map(testCase => {
                    const combinationData = data.filter(row => 
                      getTestCaseField(row) === testCase && 
                      getTacticField(row) === selectedTactic
                    );
                    const successCount = combinationData.filter(isSuccessful).length;
                    return {
                      name: testCase,
                      successRate: combinationData.length > 0 ? (successCount / combinationData.length) * 100 : 0,
                      total: combinationData.length,
                      success: successCount,
                      fail: combinationData.length - successCount
                    };
                  })
                  .filter(item => item.total > 0)
                  .sort((a, b) => b.successRate - a.successRate)
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
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
      
      {activeTab === 'heatmap' && (
        <div style={{ 
          margin: '20px 0', 
          padding: '20px', 
          backgroundColor: 'white', 
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
        }}>
          <h3>Advanced Heatmap Visualization</h3>
          <p>This interactive heatmap provides a visual representation of success rates across test cases and tactics.</p>
          
          <HeatMap 
            data={heatmapData}
            testCases={uniqueTestCases}
            tactics={uniqueTactics}
            title="Success Rate by Test Case and Tactic"
            colorRamp={HEATMAP_COLORS}
          />
          
          {selectedTactic && selectedTestCase && (
            <div style={{
              marginTop: '30px',
              padding: '15px',
              backgroundColor: '#f0f9ff',
              border: '1px solid #bae6fd',
              borderRadius: '4px'
            }}>
              <h4>Selection Details: {selectedTestCase} + {selectedTactic}</h4>
              
              <div style={{ marginTop: '15px' }}>
                {(() => {
                  const selectedData = data.filter(row => 
                    getTestCaseField(row) === selectedTestCase && 
                    getTacticField(row) === selectedTactic
                  );
                  
                  if (selectedData.length === 0) {
                    return <p>No data available for this combination.</p>;
                  }
                  
                  const successCount = selectedData.filter(isSuccessful).length;
                  const successRate = (successCount / selectedData.length) * 100;
                  
                  return (
                    <>
                      <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
                        <div>
                          <div style={{ fontSize: '12px', color: '#6b7280' }}>Success Rate</div>
                          <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{successRate.toFixed(1)}%</div>
                        </div>
                        <div>
                          <div style={{ fontSize: '12px', color: '#6b7280' }}>Total Evaluations</div>
                          <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{selectedData.length}</div>
                        </div>
                        <div>
                          <div style={{ fontSize: '12px', color: '#6b7280' }}>Successes</div>
                          <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{successCount}</div>
                        </div>
                        <div>
                          <div style={{ fontSize: '12px', color: '#6b7280' }}>Failures</div>
                          <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{selectedData.length - successCount}</div>
                        </div>
                      </div>
                      
                      <h4 style={{ marginTop: '15px' }}>Models with this combination:</h4>
                      <div style={{ maxHeight: '150px', overflowY: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                          <thead>
                            <tr>
                              <th style={{ textAlign: 'left', padding: '8px', borderBottom: '1px solid #ddd' }}>Model</th>
                              <th style={{ textAlign: 'right', padding: '8px', borderBottom: '1px solid #ddd' }}>Success Rate</th>
                              <th style={{ textAlign: 'right', padding: '8px', borderBottom: '1px solid #ddd' }}>Count</th>
                            </tr>
                          </thead>
                          <tbody>
                            {uniqueModels
                              .map(model => {
                                const modelData = selectedData.filter(row => getModelField(row) === model);
                                if (modelData.length === 0) return null;
                                
                                const modelSuccessCount = modelData.filter(isSuccessful).length;
                                const modelSuccessRate = (modelSuccessCount / modelData.length) * 100;
                                
                                return {
                                  model,
                                  successRate: modelSuccessRate,
                                  count: modelData.length
                                };
                              })
                              .filter(Boolean)
                              .sort((a, b) => b.successRate - a.successRate)
                              .map((item, index) => (
                                <tr key={index}>
                                  <td style={{ padding: '4px 8px', borderBottom: '1px solid #eee' }}>{item.model}</td>
                                  <td style={{ textAlign: 'right', padding: '4px 8px', borderBottom: '1px solid #eee' }}>{item.successRate.toFixed(1)}%</td>
                                  <td style={{ textAlign: 'right', padding: '4px 8px', borderBottom: '1px solid #eee' }}>{item.count}</td>
                                </tr>
                              ))
                            }
                          </tbody>
                        </table>
                      </div>
                    </>
                  );
                })()}
              </div>
            </div>
          )}
        </div>
      )}
      
      {activeTab === 'tacticAnalysis' && (
        <div style={{ marginTop: '20px' }}>
          <h3>Tactic vs Test Case Analysis</h3>
          
          {/* Add the advanced HeatMap component */}
          <div style={{ 
            margin: '20px 0', 
            padding: '20px', 
            backgroundColor: 'white', 
            borderRadius: '8px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
          }}>
            <HeatMap 
              data={heatmapData}
              testCases={uniqueTestCases}
              tactics={uniqueTactics}
              title="Advanced Tactic vs Test Case Heatmap"
              colorRamp={HEATMAP_COLORS}
            />
          </div>
          
          <h3>Simple Tactic vs Test Case Heatmap</h3>
          <p>This heatmap shows the success rate of each tactic against each test case.</p>
          
          <div style={{ overflowX: 'auto', marginTop: '20px' }}>
            <table style={{ borderCollapse: 'collapse', minWidth: '100%' }}>
              <thead>
                <tr>
                  <th style={{ border: '1px solid #ddd', padding: '8px', backgroundColor: '#f2f2f2' }}>Test Case / Tactic</th>
                  {uniqueTactics.map((tactic, index) => (
                    <th 
                      key={index} 
                      style={{ 
                        border: '1px solid #ddd', 
                        padding: '8px', 
                        backgroundColor: tactic === selectedTactic ? '#e6f3ff' : '#f2f2f2',
                        cursor: 'pointer'
                      }}
                      onClick={() => setSelectedTactic(tactic === selectedTactic ? null : tactic)}
                    >
                      {tactic}
                      {tactic === selectedTactic && ' ✓'}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {uniqueTestCases.map((testCase, rowIndex) => (
                  <tr key={rowIndex}>
                    <td 
                      style={{ 
                        border: '1px solid #ddd', 
                        padding: '8px', 
                        fontWeight: 'bold',
                        backgroundColor: testCase === selectedTestCase ? '#e6f3ff' : 'white',
                        cursor: 'pointer'
                      }}
                      onClick={() => setSelectedTestCase(testCase === selectedTestCase ? null : testCase)}
                    >
                      {testCase}
                      {testCase === selectedTestCase && ' ✓'}
                    </td>
                    {uniqueTactics.map((tactic, colIndex) => {
                      const relevantData = data.filter(row => 
                        getTestCaseField(row) === testCase && 
                        getTacticField(row) === tactic
                      );
                      
                      if (relevantData.length === 0) {
                        return (
                          <td key={colIndex} style={{ border: '1px solid #ddd', padding: '8px', backgroundColor: '#f9f9f9', textAlign: 'center' }}>
                            N/A
                          </td>
                        );
                      }
                      
                      const successCount = relevantData.filter(isSuccessful).length;
                      const successRate = (successCount / relevantData.length) * 100;
                      
                      // Color gradient from red (0%) to green (100%)
                      const r = Math.round(255 * (1 - successRate / 100));
                      const g = Math.round(255 * (successRate / 100));
                      const color = `rgb(${r}, ${g}, 150)`;
                      
                      const isSelected = tactic === selectedTactic && testCase === selectedTestCase;
                      
                      return (
                        <td 
                          key={colIndex} 
                          style={{ 
                            border: isSelected ? '2px solid black' : '1px solid #ddd', 
                            padding: '8px', 
                            backgroundColor: successRate > 0 ? color : '#f9f9f9',
                            color: successRate > 50 ? 'white' : 'black',
                            textAlign: 'center',
                            cursor: 'pointer'
                          }}
                          title={`${testCase} - ${tactic}: ${successRate.toFixed(1)}% (${successCount}/${relevantData.length})`}
                          onClick={() => {
                            setSelectedTestCase(testCase);
                            setSelectedTactic(tactic);
                          }}
                        >
                          {successRate.toFixed(0)}%
                          <div style={{ fontSize: '9px' }}>({successCount}/{relevantData.length})</div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {selectedTactic && selectedTestCase && (
            <div style={{ 
              marginTop: '30px',
              padding: '20px',
              backgroundColor: 'white',
              borderRadius: '8px',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
            }}>
              <h3>Models for {selectedTestCase} with {selectedTactic}</h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart
                  data={uniqueModels.map(model => {
                    const modelData = data.filter(row => 
                      getModelField(row) === model && 
                      getTestCaseField(row) === selectedTestCase &&
                      getTacticField(row) === selectedTactic
                    );
                    const successCount = modelData.filter(isSuccessful).length;
                    return {
                      name: model,
                      successRate: modelData.length > 0 ? (successCount / modelData.length) * 100 : 0,
                      total: modelData.length,
                      success: successCount,
                      fail: modelData.length - successCount
                    };
                  })
                  .filter(item => item.total > 0)
                  .sort((a, b) => b.successRate - a.successRate)
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
                    {uniqueModels.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
      
      {/* Debug Information Section */}
      <div style={{ 
        marginTop: '30px', 
        padding: '15px', 
        border: '1px dashed #ccc', 
        backgroundColor: '#f9f9f9',
        borderRadius: '5px' 
      }}>
        <h3>Debug Information</h3>
        <p>This section shows technical information to help diagnose issues.</p>
        
        <div>
          <button 
            onClick={() => console.log('Models data:', modelSuccessRates)} 
            style={{
              padding: '5px 10px',
              backgroundColor: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              marginRight: '10px'
            }}
          >
            Log Models Data
          </button>
          
          <button 
            onClick={() => console.log('Tactics data:', tacticSuccessRates)} 
            style={{
              padding: '5px 10px',
              backgroundColor: '#2196F3',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              marginRight: '10px'
            }}
          >
            Log Tactics Data
          </button>
        </div>
      </div>
    </div>
  );
};

export default HybridViz; 