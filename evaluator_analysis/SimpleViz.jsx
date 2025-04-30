import React, { useState, useEffect } from 'react';
import Papa from 'papaparse';

const SimpleViz = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState('Starting');

  useEffect(() => {
    const loadData = async () => {
      try {
        setStatus('Trying to load sample data...');
        // First try to load the sample data
        let response = await fetch('/sample_results.csv');
        
        // If sample data fails, try to load the master results
        if (!response.ok) {
          setStatus('Sample data not found, trying master_results.csv...');
          response = await fetch('/master_results.csv');
          
          if (!response.ok) {
            throw new Error(`Failed to fetch data: Sample: ${response.status}`);
          }
          
          setStatus('Master results data found');
        } else {
          setStatus('Sample data found');
        }
        
        setStatus('Reading data...');
        const text = await response.text();
        console.log("Data content preview:", text.substring(0, 100) + "...");
        
        setStatus('Parsing data...');
        const result = Papa.parse(text, {
          header: true,
          skipEmptyLines: true,
          comments: "#",
          error: function(error) {
            console.error("Parse error:", error);
          },
          complete: function(results) {
            console.log("Parse complete:", results.data.length, "rows");
            if (results.errors && results.errors.length > 0) {
              console.warn("Parse errors:", results.errors);
            }
          }
        });
        
        if (!result.data || result.data.length === 0) {
          throw new Error("No data rows found after parsing CSV");
        }
        
        console.log("First row:", result.data[0]);
        
        // Clean the data - handle different formats
        const cleanedData = result.data.map(row => {
          // Ensure goal_achieved is consistently formatted
          if (typeof row.goal_achieved === 'string') {
            row.goal_achieved = row.goal_achieved.toLowerCase() === 'true';
          }
          return row;
        });
        
        setData(cleanedData);
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

  if (loading) {
    return (
      <div style={{ padding: '20px', margin: '20px', border: '1px solid #ccc' }}>
        <h2>Simple Visualization (Loading)</h2>
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
        <h2>Simple Visualization (Error)</h2>
        <p>Error: {error}</p>
        <p>Status: {status}</p>
        <button onClick={() => window.location.reload()}>Reload</button>
      </div>
    );
  }

  // Some helper functions to make the component more resilient
  const getModelField = (row) => {
    // Try different potential model field names
    return row.target_model || row.model || "Unknown Model";
  };
  
  const getTestCaseField = (row) => {
    return row.test_case || "Unknown Test Case";
  };
  
  const getTacticField = (row) => {
    return row.jailbreak_tactic || row.tactic || "Unknown Tactic";
  };
  
  const isSuccessful = (row) => {
    if (row.goal_achieved !== undefined) {
      return row.goal_achieved === true || row.goal_achieved === 'true' || row.goal_achieved === 1;
    } else if (row.success !== undefined) {
      return row.success === true || row.success === 'true' || row.success === 1;
    }
    return false;
  };

  return (
    <div style={{ padding: '20px', margin: '20px', border: '1px solid #ccc' }}>
      <h2>Simple Visualization</h2>
      <p>Successfully loaded {data.length} rows of data.</p>
      <p>Status: {status}</p>
      
      <h3>Raw Data (First 5 rows)</h3>
      <table style={{ borderCollapse: 'collapse', width: '100%' }}>
        <thead>
          <tr>
            {data.length > 0 && Object.keys(data[0]).map((key) => (
              <th key={key} style={{ border: '1px solid #ddd', padding: '8px', backgroundColor: '#f2f2f2' }}>
                {key}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.slice(0, 5).map((row, index) => (
            <tr key={index}>
              {Object.values(row).map((value, i) => (
                <td key={i} style={{ border: '1px solid #ddd', padding: '8px' }}>
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      
      <h3>Data Summary</h3>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
        <div style={{ flex: '1', minWidth: '200px', border: '1px solid #ddd', padding: '15px', borderRadius: '5px' }}>
          <h4>Models</h4>
          <ul>
            {[...new Set(data.map(getModelField))].map((model, index) => (
              <li key={index}>{model}</li>
            ))}
          </ul>
        </div>
        <div style={{ flex: '1', minWidth: '200px', border: '1px solid #ddd', padding: '15px', borderRadius: '5px' }}>
          <h4>Test Cases</h4>
          <ul>
            {[...new Set(data.map(getTestCaseField))].map((testCase, index) => (
              <li key={index}>{testCase}</li>
            ))}
          </ul>
        </div>
        <div style={{ flex: '1', minWidth: '200px', border: '1px solid #ddd', padding: '15px', borderRadius: '5px' }}>
          <h4>Tactics</h4>
          <ul>
            {[...new Set(data.map(getTacticField))].map((tactic, index) => (
              <li key={index}>{tactic}</li>
            ))}
          </ul>
        </div>
      </div>
      
      <h3>Simple Success Rate Visualization</h3>
      {data.length > 0 && (
        <div>
          <div style={{ marginBottom: '20px' }}>
            <h4>Overall Success Rate</h4>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ 
                width: '300px', 
                height: '30px', 
                backgroundColor: '#eee', 
                borderRadius: '5px',
                overflow: 'hidden' 
              }}>
                {(() => {
                  const successCount = data.filter(isSuccessful).length;
                  const successRate = (successCount / data.length) * 100;
                  return (
                    <div style={{ 
                      width: `${successRate}%`, 
                      height: '100%', 
                      backgroundColor: '#4CAF50',
                      transition: 'width 1s'
                    }}></div>
                  );
                })()}
              </div>
              <span>
                {(() => {
                  const successCount = data.filter(isSuccessful).length;
                  return `${(successCount / data.length * 100).toFixed(1)}% (${successCount}/${data.length})`;
                })()}
              </span>
            </div>
          </div>
          
          <div>
            <h4>Success Rate by Model</h4>
            {[...new Set(data.map(getModelField))].map((model, index) => {
              const modelData = data.filter(row => getModelField(row) === model);
              const successCount = modelData.filter(isSuccessful).length;
              const successRate = (successCount / modelData.length) * 100;
              
              return (
                <div key={index} style={{ marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ width: '100px', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                    {model}:
                  </div>
                  <div style={{ 
                    width: '200px', 
                    height: '20px', 
                    backgroundColor: '#eee', 
                    borderRadius: '5px',
                    overflow: 'hidden' 
                  }}>
                    <div style={{ 
                      width: `${successRate}%`, 
                      height: '100%', 
                      backgroundColor: COLORS[index % COLORS.length],
                      transition: 'width 1s'
                    }}></div>
                  </div>
                  <span>{successRate.toFixed(1)}% ({successCount}/{modelData.length})</span>
                </div>
              );
            })}
          </div>
          
          <div style={{ marginTop: '30px' }}>
            <h4>Simple Tactic vs Test Case Heatmap</h4>
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
        
        <div style={{ marginBottom: '10px' }}>
          <h4>Browser Information</h4>
          <ul style={{ fontSize: '14px' }}>
            <li>User Agent: {navigator.userAgent}</li>
            <li>Window Size: {window.innerWidth}x{window.innerHeight}</li>
            <li>Protocol: {window.location.protocol}</li>
            <li>Host: {window.location.host}</li>
          </ul>
        </div>
        
        <div style={{ marginBottom: '10px' }}>
          <h4>Data Information</h4>
          <ul style={{ fontSize: '14px' }}>
            <li>Data Rows: {data.length}</li>
            <li>Unique Models: {[...new Set(data.map(getModelField))].length}</li>
            <li>Unique Test Cases: {[...new Set(data.map(getTestCaseField))].length}</li>
            <li>Unique Tactics: {[...new Set(data.map(getTacticField))].length}</li>
            <li>Field Names: {data.length > 0 ? Object.keys(data[0]).join(', ') : 'No data'}</li>
          </ul>
        </div>
        
        <div>
          <button 
            onClick={() => console.log('Full data:', data)} 
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
            Log Data to Console
          </button>
          
          <button 
            onClick={() => window.location.reload()} 
            style={{
              padding: '5px 10px',
              backgroundColor: '#2196F3',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Refresh Page
          </button>
        </div>
      </div>
    </div>
  );
};

// Simple color palette
const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE', 
  '#00C49F', '#FFBB28', '#FF8042', '#a4de6c', '#d0ed57'
];

export default SimpleViz; 