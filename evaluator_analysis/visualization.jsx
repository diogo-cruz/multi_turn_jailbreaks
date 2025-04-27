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

// Main component for evaluator visualization
const EvaluatorViz = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uniqueModels, setUniqueModels] = useState([]);
  const [uniqueTestCases, setUniqueTestCases] = useState([]);
  const [uniquePrompts, setUniquePrompts] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [selectedTestCase, setSelectedTestCase] = useState(null);
  const [selectedPrompt, setSelectedPrompt] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [chartType, setChartType] = useState("bar");
  const [sortBy, setSortBy] = useState("success");
  const [showDetails, setShowDetails] = useState(false);

  // Load and process the data
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        
        // Fetch the CSV file
        const response = await fetch('/master_results.csv');
        const fileContent = await response.text();
        
        // Parse the CSV file
        const parsedData = Papa.parse(fileContent, {
          header: true,
          dynamicTyping: true,
          skipEmptyLines: true,
          complete: function(results) {
            console.log("Parsing complete:", results.data.length, "rows");
            console.log("Sample row:", results.data[0]);
          },
          error: function(error) {
            console.error("Error parsing CSV:", error);
          }
        }).data;
        
        setData(parsedData);
        
        // Extract unique values
        const models = [...new Set(parsedData.map(row => row.model))].filter(Boolean);
        const testCases = [...new Set(parsedData.map(row => row.test_case))].filter(Boolean);
        const prompts = [...new Set(parsedData.map(row => row.prompt_path))].filter(Boolean);
        
        setUniqueModels(models);
        setUniqueTestCases(testCases);
        setUniquePrompts(prompts);
        
        // Set default selections
        if (models.length > 0) setSelectedModel(models[0]);
        if (testCases.length > 0) setSelectedTestCase(testCases[0]);
        if (prompts.length > 0) setSelectedPrompt(prompts[0]);
        
        console.log("Data loaded successfully");
        console.log("Models:", models.length);
        console.log("Test Cases:", testCases.length);
        console.log("Prompts:", prompts.length);
        
        setLoading(false);
      } catch (err) {
        console.error("Error loading data:", err);
        setError("Failed to load data. Please try again.");
        setLoading(false);
      }
    };
    
    loadData();
  }, []);

  // Filter data based on selections
  const filteredData = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    return data.filter(row => {
      const modelMatch = !selectedModel || row.model === selectedModel;
      const testCaseMatch = !selectedTestCase || row.test_case === selectedTestCase;
      const promptMatch = !selectedPrompt || row.prompt_path === selectedPrompt;
      
      return modelMatch && testCaseMatch && promptMatch;
    });
  }, [data, selectedModel, selectedTestCase, selectedPrompt]);

  // Calculate success rate by model
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

  // Calculate standard error for a set of values
  const calculateStandardError = (values) => {
    if (!values || values.length <= 1) return 0;
    
    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const squaredDiffs = values.map(val => Math.pow(val - mean, 2));
    const variance = squaredDiffs.reduce((sum, val) => sum + val, 0) / (values.length - 1);
    const stdDev = Math.sqrt(variance);
    const standardError = stdDev / Math.sqrt(values.length);
    
    return standardError * 100; // Convert to percentage
  };

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

  // Calculate success rate by prompt
  const promptSuccessRates = useMemo(() => {
    if (!data || data.length === 0 || !selectedTestCase) return [];
    
    const promptData = {};
    
    // Filter by selected model and test case
    const filteredData = data.filter(row => {
      const modelMatch = !selectedModel || row.model === selectedModel;
      const testCaseMatch = row.test_case === selectedTestCase;
      return modelMatch && testCaseMatch;
    });
    
    // Group by prompt
    filteredData.forEach(row => {
      const prompt = row.prompt_path;
      if (!prompt) return;
      
      if (!promptData[prompt]) {
        promptData[prompt] = {
          success: 0,
          fail: 0,
          total: 0,
          name: prompt
        };
      }
      
      promptData[prompt].total += 1;
      if (row.success === true || row.success === 1) {
        promptData[prompt].success += 1;
      } else {
        promptData[prompt].fail += 1;
      }
    });
    
    // Calculate rates and format for chart
    return Object.values(promptData).map(prompt => ({
      name: prompt.name,
      successRate: prompt.total > 0 
        ? (prompt.success / prompt.total) * 100 
        : 0,
      failRate: prompt.total > 0 
        ? (prompt.fail / prompt.total) * 100 
        : 0,
      success: prompt.success,
      fail: prompt.fail,
      total: prompt.total,
      // Add standard error calculation
      standardError: calculateStandardError([...Array(prompt.success).fill(1), ...Array(prompt.fail).fill(0)])
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
      
      {/* Navigation Tabs */}
      <div className="tabs" style={{ display: 'flex', marginBottom: '1rem', borderBottom: '1px solid #e5e7eb' }}>
        {['overview', 'models', 'testCases', 'prompts'].map(tab => (
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
        
        {activeTab === 'prompts' && (
          <div style={styles.filterItem}>
            <label>Prompt:</label>
            <select
              value={selectedPrompt || ''}
              onChange={(e) => setSelectedPrompt(e.target.value || null)}
              style={styles.select}
            >
              <option value="">All Prompts</option>
              {uniquePrompts.map(prompt => (
                <option key={prompt} value={prompt}>{prompt}</option>
              ))}
            </select>
          </div>
        )}
        
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
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb' }}>Prompts:</td>
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid #e5e7eb', fontWeight: 'bold' }}>{uniquePrompts.length}</td>
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
                  <Tooltip formatter={(value, name, props) => {
                    const dataItem = testCaseSuccessRates.find(item => item.name === props.payload.name);
                    return [`${dataItem.successRate.toFixed(2)}% (${value} successes)`, props.payload.name];
                  }} />
                  <Legend />
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
                  <Tooltip formatter={(value, name) => {
                    if (name === 'successRate') return [`${value.toFixed(2)}%`, 'Success Rate'];
                    if (name === 'failRate') return [`${value.toFixed(2)}%`, 'Fail Rate'];
                    if (name === 'total') return [value, 'Total Evaluations'];
                    return [value, name];
                  }} />
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
            <h3>Prompts by Success Rate {selectedPrompt && `(Selected: ${selectedPrompt})`}</h3>
            <ResponsiveContainer width="100%" height={400}>
              {chartType === 'bar' ? (
                <BarChart
                  data={promptSuccessRates
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
                    {promptSuccessRates.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={entry.name === selectedPrompt ? '#ff7300' : COLORS[(index + 4) % COLORS.length]}
                        stroke={entry.name === selectedPrompt ? '#000000' : undefined}
                        strokeWidth={entry.name === selectedPrompt ? 1 : 0}
                      />
                    ))}
                    {showDetails && <ErrorBar dataKey="standardError" width={4} strokeWidth={2} stroke="#ffc658" />}
                    <LabelList dataKey="total" position="insideTop" formatter={(value) => `n=${value}`} />
                  </Bar>
                </BarChart>
              ) : chartType === 'pie' ? (
                <PieChart>
                  <Pie
                    data={promptSuccessRates}
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
                    {promptSuccessRates.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={entry.name === selectedPrompt ? '#ff7300' : COLORS[(index + 4) % COLORS.length]}
                        stroke={entry.name === selectedPrompt ? '#000000' : undefined}
                        strokeWidth={entry.name === selectedPrompt ? 2 : 0}
                      />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value, name, props) => {
                      const dataItem = promptSuccessRates.find(item => item.name === props.payload.name);
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
                  data={promptSuccessRates
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
                  <Area yAxisId="left" dataKey="successRate" name="Success Rate" fill="#ffc658" stroke="#ffc658" />
                  <Line yAxisId="right" type="monotone" dataKey="total" name="Total" stroke="#8884d8" />
                </ComposedChart>
              )}
            </ResponsiveContainer>
          </div>
          
          {/* Details for selected prompt */}
          {selectedPrompt && (
            <div style={styles.chartContainer}>
              <h3>Details for Prompt: {selectedPrompt.split('/').pop()}</h3>
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
                      .filter(row => row.prompt_path === selectedPrompt)
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
              <h3>Detailed Prompt Statistics</h3>
              <div style={{ maxHeight: '400px', overflow: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f3f4f6' }}>
                      <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Prompt</th>
                      <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Success Rate</th>
                      <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Success</th>
                      <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Fail</th>
                      <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {promptSuccessRates
                      .sort((a, b) => sortBy === 'success' ? b.successRate - a.successRate :
                           sortBy === 'fail' ? b.failRate - a.failRate :
                           sortBy === 'total' ? b.total - a.total :
                           a.name.localeCompare(b.name))
                      .map((prompt, index) => {
                        const parts = prompt.name.split('/');
                        const shortName = parts[parts.length - 1];
                        
                        return (
                          <tr 
                            key={index} 
                            style={{ 
                              backgroundColor: prompt.name === selectedPrompt ? '#f0f9ff' : index % 2 ? '#f9f9f9' : 'white'
                            }}
                          >
                            <td style={{ 
                              border: '1px solid #ddd', 
                              padding: '8px',
                              fontWeight: prompt.name === selectedPrompt ? 'bold' : 'normal'
                            }}>
                              {shortName}
                            </td>
                            <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                              {prompt.successRate.toFixed(2)}%
                            </td>
                            <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                              {prompt.success}
                            </td>
                            <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                              {prompt.fail}
                            </td>
                            <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                              {prompt.total}
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
                <td style={{ padding: '0.5rem' }}>Prompts:</td>
                <td style={{ padding: '0.5rem', fontWeight: 'bold' }}>
                  {new Set(filteredData.map(row => row.prompt_path)).size}
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
    </div>
  );
};

export default EvaluatorViz; 