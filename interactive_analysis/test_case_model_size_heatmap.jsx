import React, { useState, useEffect } from 'react';
import { loadAndAnalyzeData } from './test_case_model_size_analysis';

// Define a color scale for the heatmap
const getColor = (value, minValue, maxValue) => {
  if (value === null) return '#f0f0f0'; // Light gray for missing data
  
  // Use a diverging color scale (blue to white to red)
  // Negative slopes (blue): model size increases, ASR decreases
  // Positive slopes (red): model size increases, ASR increases
  
  if (value < 0) {
    // Negative values: blue scale
    const intensity = Math.min(1, Math.abs(value / minValue));
    return `rgb(${Math.round(255 * (1 - intensity))}, ${Math.round(255 * (1 - intensity))}, 255)`;
  } else {
    // Positive values: red scale
    const intensity = Math.min(1, value / maxValue);
    return `rgb(255, ${Math.round(255 * (1 - intensity))}, ${Math.round(255 * (1 - intensity))})`;
  }
};

// Utility function to format the slope value for display
const formatSlope = (value) => {
  if (value === null) return 'N/A';
  return value.toFixed(2);
};

// Helper component for the color legend
const ColorLegend = ({ minValue, maxValue }) => {
  const steps = 10;
  const legendItems = [];
  
  // Create gradient steps
  for (let i = 0; i <= steps; i++) {
    const value = minValue + (i / steps) * (maxValue - minValue);
    legendItems.push({
      value,
      color: getColor(value, minValue, maxValue)
    });
  }
  
  return (
    <div style={{ display: 'flex', flexDirection: 'column', marginLeft: '20px', alignItems: 'center' }}>
      <div style={{ fontSize: '14px', marginBottom: '5px' }}>Slope Legend</div>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '5px' }}>
        <div style={{ width: '20px', height: '20px', backgroundColor: getColor(minValue, minValue, maxValue) }}></div>
        <span style={{ marginLeft: '5px' }}>{minValue.toFixed(2)}</span>
      </div>
      <div style={{ width: '20px', height: '100px', background: `linear-gradient(to bottom, ${getColor(minValue, minValue, maxValue)}, white, ${getColor(maxValue, minValue, maxValue)})` }}></div>
      <div style={{ display: 'flex', alignItems: 'center', marginTop: '5px' }}>
        <div style={{ width: '20px', height: '20px', backgroundColor: getColor(maxValue, minValue, maxValue) }}></div>
        <span style={{ marginLeft: '5px' }}>{maxValue.toFixed(2)}</span>
      </div>
      <div style={{ fontSize: '12px', marginTop: '10px', textAlign: 'center', maxWidth: '150px' }}>
        <p><strong>Negative slope:</strong> ASR decreases as model size increases</p>
        <p><strong>Positive slope:</strong> ASR increases as model size increases</p>
      </div>
    </div>
  );
};

// Main heatmap component
const TestCaseModelSizeHeatmap = () => {
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortBy, setSortBy] = useState('testCase'); // 'testCase' or 'avgSlope'
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await loadAndAnalyzeData('./enhanced_master_data.csv', './model_comparison.csv');
        setAnalysisData(data);
        setLoading(false);
      } catch (err) {
        console.error('Error loading data:', err);
        setError(`Failed to load data: ${err.message}`);
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  if (loading) {
    return <div style={{ padding: '20px' }}>Loading analysis data...</div>;
  }
  
  if (error) {
    return <div style={{ padding: '20px', color: 'red' }}>{error}</div>;
  }
  
  if (!analysisData || !analysisData.data || analysisData.data.length === 0) {
    return <div style={{ padding: '20px' }}>No analysis data available.</div>;
  }
  
  // Find min and max slope values for color scaling
  let minValue = 0, maxValue = 0;
  analysisData.data.forEach(row => {
    analysisData.labs.forEach(lab => {
      const value = row[lab];
      if (value !== null) {
        minValue = Math.min(minValue, value);
        maxValue = Math.max(maxValue, value);
      }
    });
  });
  
  // Sort the data if needed
  let sortedData = [...analysisData.data];
  if (sortBy === 'avgSlope') {
    // Calculate average slope for each test case
    sortedData.sort((a, b) => {
      const aValues = analysisData.labs.map(lab => a[lab]).filter(v => v !== null);
      const bValues = analysisData.labs.map(lab => b[lab]).filter(v => v !== null);
      
      const aAvg = aValues.length > 0 ? aValues.reduce((sum, v) => sum + v, 0) / aValues.length : 0;
      const bAvg = bValues.length > 0 ? bValues.reduce((sum, v) => sum + v, 0) / bValues.length : 0;
      
      return aAvg - bAvg;
    });
  }
  
  return (
    <div style={{ padding: '20px' }}>
      <h2>Test Case × AI Lab ASR/Size Relationship Analysis</h2>
      <p>
        This heatmap shows the slope of the linear regression line fitting ASR (Attack Success Rate) vs. model size 
        for each test case and AI lab combination. A negative slope (blue) indicates that larger models tend to be 
        more resistant to that test case, while a positive slope (red) indicates that larger models may be more 
        vulnerable.
      </p>
      
      <div style={{ marginBottom: '20px' }}>
        <label>
          Sort by: 
          <select 
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value)}
            style={{ marginLeft: '10px' }}
          >
            <option value="testCase">Test Case (A-Z)</option>
            <option value="avgSlope">Average Slope</option>
          </select>
        </label>
      </div>
      
      <div style={{ display: 'flex' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ borderCollapse: 'collapse', minWidth: '800px' }}>
            <thead>
              <tr>
                <th style={{ padding: '10px', borderBottom: '1px solid #ddd', textAlign: 'left', minWidth: '200px' }}>
                  Test Case
                </th>
                {analysisData.labs.map(lab => (
                  <th key={lab} style={{ padding: '10px', borderBottom: '1px solid #ddd', textAlign: 'center', minWidth: '120px' }}>
                    {lab}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedData.map((row, index) => (
                <tr key={index}>
                  <td style={{ padding: '10px', borderBottom: '1px solid #eee', fontWeight: 500 }}>
                    {row.testCase}
                  </td>
                  {analysisData.labs.map(lab => {
                    const value = row[lab];
                    const backgroundColor = getColor(value, minValue, maxValue);
                    const textColor = value === null ? '#666' : (Math.abs(value) > (maxValue - minValue) / 2 ? 'white' : 'black');
                    
                    return (
                      <td 
                        key={lab} 
                        style={{ 
                          padding: '10px', 
                          borderBottom: '1px solid #eee',
                          textAlign: 'center',
                          backgroundColor,
                          color: textColor
                        }}
                        title={`Slope: ${formatSlope(value)}`}
                      >
                        {formatSlope(value)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        <ColorLegend minValue={minValue} maxValue={maxValue} />
      </div>
      
      <div style={{ marginTop: '20px' }}>
        <h3>Understanding the Results</h3>
        <ul style={{ lineHeight: 1.6 }}>
          <li><strong>Negative slope (blue):</strong> As model size increases, jailbreak success rate decreases. This suggests that larger models from this lab are generally more resistant to this particular test case.</li>
          <li><strong>Positive slope (red):</strong> As model size increases, jailbreak success rate increases. This indicates that larger models from this lab may be more vulnerable to this test case.</li>
          <li><strong>Values near zero:</strong> No clear relationship between model size and jailbreak success for this test case and lab.</li>
          <li><strong>Missing values (N/A):</strong> Insufficient data points to calculate a meaningful slope (requires at least 2 models with different sizes).</li>
        </ul>
        <p>Note: The analysis requires multiple model sizes from the same AI lab for each test case to calculate a slope.</p>
      </div>
    </div>
  );
};

export default TestCaseModelSizeHeatmap; 