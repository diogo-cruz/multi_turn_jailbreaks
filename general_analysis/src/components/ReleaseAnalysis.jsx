import React, { useState, useMemo } from 'react';
import { 
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, ZAxis, Label
} from 'recharts';

// Color constants
const COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE', 
  '#00C49F', '#FFBB28', '#FF8042', '#a4de6c', '#d0ed57'
];

const ReleaseAnalysis = ({ data, modelComparisonData }) => {
  const [metric, setMetric] = useState("success");
  
  // Process data for visualization
  const processedData = useMemo(() => {
    if (!data || !modelComparisonData || modelComparisonData.length === 0) {
      return { models: [], familyGroups: {} };
    }
    
    // Map model names to release dates from modelComparisonData
    const modelDates = {};
    const modelFamilies = {};
    
    // Parse date string into timestamp
    const parseReleaseDate = (dateStr) => {
      if (!dateStr) return null;
      
      // Check if it's already a timestamp
      if (typeof dateStr === 'number') return dateStr;
      
      try {
        // Try to parse month and year format (e.g., "May 2024")
        const monthYearMatch = dateStr.match(/([A-Za-z]+)\s+(\d{4})/);
        if (monthYearMatch) {
          const month = new Date(Date.parse(monthYearMatch[1] + " 1, 2000")).getMonth();
          const year = parseInt(monthYearMatch[2]);
          return new Date(year, month, 15).getTime(); // Middle of the month
        }
        
        // Otherwise try standard date parsing
        return new Date(dateStr).getTime();
      } catch (e) {
        console.warn("Could not parse date:", dateStr);
        return null;
      }
    };
    
    // First pass: collect release dates with exact matching
    for (const model of modelComparisonData) {
      if (model.model_name && model["Release Date"]) {
        const timestamp = parseReleaseDate(model["Release Date"]);
        if (timestamp) {
          modelDates[model.model_name] = timestamp;
          
          // Extract model family
          const nameParts = model.model_name.toLowerCase().split(/[-\s]/);
          if (nameParts.length > 0) {
            const family = nameParts[0];
            modelFamilies[model.model_name] = family;
          }
        }
      } else if (model.Model && model["Release Date"]) {
        // Handle the CSV format from model_comparison.csv
        const modelName = model.Model;
        const timestamp = parseReleaseDate(model["Release Date"]);
        
        if (timestamp) {
          modelDates[modelName] = timestamp;
          
          const nameParts = modelName.toLowerCase().split(/[-\s\/]/);
          if (nameParts.length > 0) {
            const family = nameParts[0];
            modelFamilies[modelName] = family;
          }
        }
      }
    }
    
    // Calculate aggregated metrics for each model
    const modelData = {};
    
    // Check data format
    if (Array.isArray(data) && data[0] && data[0].name) {
      // Process model objects
      for (const modelObject of data) {
        const modelName = modelObject.name;
        let releaseDate = modelDates[modelName];
        
        if (!releaseDate) continue; // Skip if no exact match
        
        // Calculate overall metrics
        const successRate = modelObject.testCases 
          ? modelObject.testCases.reduce((sum, tc) => sum + tc.successRate, 0) / modelObject.testCases.length
          : 0;
        
        const refusalRate = modelObject.testCases 
          ? modelObject.testCases.reduce((sum, tc) => sum + tc.refusalRate, 0) / modelObject.testCases.length
          : 0;
        
        const avgRounds = modelObject.testCases 
          ? modelObject.testCases.reduce((sum, tc) => sum + tc.roundCount, 0) / modelObject.testCases.length
          : 0;
        
        modelData[modelName] = {
          name: modelName,
          releaseDate,
          releaseDateStr: new Date(releaseDate).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short'
          }),
          family: modelFamilies[modelName] || 'unknown',
          successRate,
          refusalRate,
          avgRounds,
          count: modelObject.testCases?.length || 0
        };
      }
    } else {
      // Process raw data rows
      for (const row of data) {
        const modelName = row.target_model || row.model || 'unknown';
        let releaseDate = modelDates[modelName];
        
        if (!releaseDate) continue; // Skip if no exact match
        
        if (!modelData[modelName]) {
          modelData[modelName] = {
            name: modelName,
            releaseDate,
            releaseDateStr: new Date(releaseDate).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'short'
            }),
            family: modelFamilies[modelName] || 'unknown',
            successCount: 0,
            refusalCount: 0,
            roundSum: 0,
            totalCount: 0
          };
        }
        
        modelData[modelName].totalCount++;
        
        // Count success/refusal/rounds
        const isSuccess = row.success !== undefined ? Boolean(row.success) : 
                         row.jailbreak_success !== undefined ? Boolean(row.jailbreak_success) :
                         row.asr !== undefined ? row.asr > 0 : false;
        
        const isRefusal = row.refused !== undefined ? Boolean(row.refused) : 
                         row.refusal !== undefined ? Boolean(row.refusal) :
                         row.rejection !== undefined ? Boolean(row.rejection) : false;
        
        if (isSuccess) modelData[modelName].successCount++;
        if (isRefusal) modelData[modelName].refusalCount++;
        
        const rounds = row.num_turns || row.rounds || row.turn_count || 0;
        modelData[modelName].roundSum += rounds;
      }
      
      // Calculate rates
      for (const modelName in modelData) {
        const model = modelData[modelName];
        if (model.totalCount > 0) {
          model.successRate = (model.successCount / model.totalCount) * 100;
          model.refusalRate = (model.refusalCount / model.totalCount) * 100;
          model.avgRounds = model.roundSum / model.totalCount;
          model.count = model.totalCount;
        }
      }
    }
    
    // Convert to array and group by family
    const families = {};
    const result = [];
    
    for (const modelName in modelData) {
      const model = modelData[modelName];
      
      if (!families[model.family]) {
        families[model.family] = [];
      }
      
      families[model.family].push(model);
      result.push(model);
    }
    
    // Sort result by release date
    result.sort((a, b) => a.releaseDate - b.releaseDate);
    
    // Group by family
    Object.keys(families).forEach(family => {
      families[family].sort((a, b) => a.releaseDate - b.releaseDate);
    });
    
    return {
      models: result,
      familyGroups: families
    };
  }, [data, modelComparisonData, metric]);
  
  // Get chart data based on selected metric
  const chartData = useMemo(() => {
    if (!processedData.models || processedData.models.length === 0) {
      return [];
    }
    
    const metricKey = metric === 'success' ? 'successRate' : 
                      metric === 'refusal' ? 'refusalRate' : 'avgRounds';
    
    return processedData.models.map(model => ({
      ...model,
      value: model[metricKey]
    }));
  }, [processedData, metric]);
  
  // Group models by family for coloring
  const familyColors = useMemo(() => {
    const families = Object.keys(processedData.familyGroups || {});
    const colorMap = {};
    
    families.forEach((family, index) => {
      colorMap[family] = COLORS[index % COLORS.length];
    });
    
    return colorMap;
  }, [processedData]);
  
  // Render metric selector
  const renderMetricSelector = () => (
    <div className="mb-4">
      <label className="block text-sm font-medium mb-1">Metric:</label>
      <div className="flex space-x-4">
        <label className="inline-flex items-center">
          <input 
            type="radio" 
            value="success" 
            checked={metric === "success"} 
            onChange={() => setMetric("success")}
            className="mr-1"
          />
          Success Rate
        </label>
        <label className="inline-flex items-center">
          <input 
            type="radio" 
            value="refusal" 
            checked={metric === "refusal"} 
            onChange={() => setMetric("refusal")}
            className="mr-1"
          />
          Refusal Rate
        </label>
        <label className="inline-flex items-center">
          <input 
            type="radio" 
            value="rounds" 
            checked={metric === "rounds"} 
            onChange={() => setMetric("rounds")}
            className="mr-1"
          />
          Average Rounds
        </label>
      </div>
    </div>
  );
  
  // Format date for display
  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short'
    });
  };
  
  // Render the scatter plot
  const renderScatterPlot = () => {
    if (!chartData || chartData.length === 0) {
      return (
        <div className="p-4 bg-gray-100 rounded-md text-center">
          <p className="text-gray-700 mb-2">Model release date data is not available.</p>
          <p className="text-gray-600 text-sm">Please ensure that model_comparison.csv contains release dates and model names match those in your data source.</p>
        </div>
      );
    }
    
    // Get min and max dates for domain
    const minDate = Math.min(...chartData.map(m => m.releaseDate));
    const maxDate = Math.max(...chartData.map(m => m.releaseDate));
    
    // Add some padding to the domain
    const oneMonthMs = 30 * 24 * 60 * 60 * 1000;
    const domain = [minDate - oneMonthMs, maxDate + oneMonthMs];
    
    return (
      <div className="chart-container">
        <h3 className="text-lg font-medium mb-2">
          {metric === 'success' ? 'Success Rate' : 
           metric === 'refusal' ? 'Refusal Rate' : 'Average Rounds'} vs. Release Timeline
        </h3>
        
        <ResponsiveContainer width="100%" height={500}>
          <ScatterChart
            margin={{ top: 20, right: 30, left: 30, bottom: 60 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              type="number" 
              dataKey="releaseDate" 
              name="Release Date" 
              domain={domain}
              tickFormatter={formatDate}
              tick={{ fontSize: 12, angle: -45, textAnchor: 'end' }}
            >
              <Label value="Model Release Date" offset={-20} position="insideBottom" />
            </XAxis>
            <YAxis 
              type="number" 
              dataKey="value" 
              name="Value"
              domain={metric === 'rounds' ? ['auto', 'auto'] : [0, 100]}
            >
              <Label 
                value={metric === 'success' ? 'Success Rate (%)' : 
                       metric === 'refusal' ? 'Refusal Rate (%)' : 'Average Rounds'} 
                angle={-90} 
                position="insideLeft" 
                offset={-10}
              />
            </YAxis>
            <ZAxis 
              type="number" 
              dataKey="count" 
              range={[40, 400]} 
              name="Sample Count"
            />
            <Tooltip 
              cursor={{ strokeDasharray: '3 3' }}
              formatter={(value, name) => {
                if (name === 'Release Date') return [formatDate(value), name];
                if (name === 'Sample Count') return [value, name];
                return [`${value.toFixed(2)}${metric !== 'rounds' ? '%' : ''}`, name];
              }}
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const model = payload[0].payload;
                  
                  return (
                    <div className="bg-white p-2 border rounded shadow">
                      <p className="font-medium">{model.name}</p>
                      <p>Release Date: {model.releaseDateStr}</p>
                      <p>
                        {metric === 'success' ? 'Success Rate' : 
                         metric === 'refusal' ? 'Refusal Rate' : 'Average Rounds'}: 
                        {' '}{model.value.toFixed(2)}{metric !== 'rounds' ? '%' : ''}
                      </p>
                      <p>Sample Count: {model.count}</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend 
              payload={
                Object.entries(familyColors).map(([family, color]) => ({
                  value: family,
                  type: 'circle',
                  color
                }))
              }
            />
            {Object.entries(processedData.familyGroups || {}).map(([family, models]) => (
              <Scatter 
                key={family}
                name={family} 
                data={models.map(model => ({
                  ...model,
                  value: model[metric === 'success' ? 'successRate' : 
                               metric === 'refusal' ? 'refusalRate' : 'avgRounds']
                }))} 
                fill={familyColors[family]}
              />
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    );
  };
  
  // Check if there's data for analysis
  const hasModelReleaseData = useMemo(() => {
    return chartData && chartData.length > 0;
  }, [chartData]);

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">Model Release Timeline Analysis</h2>
        <p className="text-gray-600">
          Analyze the relationship between model release date and jailbreak resistance over time.
        </p>
      </div>
      
      {!hasModelReleaseData ? (
        <div className="p-6 bg-gray-100 rounded text-center">
          <p className="text-lg">
            Model release date data is not available. Please ensure that model_comparison.csv contains release dates.
          </p>
        </div>
      ) : (
        <div className="flex flex-wrap -mx-2">
          <div className="w-full md:w-1/4 px-2">
            {renderMetricSelector()}
            
            <div className="mt-6 p-4 bg-blue-50 rounded">
              <h3 className="text-md font-medium mb-2">Key Insights</h3>
              <ul className="list-disc pl-5 text-sm space-y-2">
                <li>Track how jailbreak resistance evolves over time</li>
                <li>Compare effectiveness across different model release dates</li>
                <li>Points are colored by model family</li>
                <li>Larger points indicate more samples</li>
              </ul>
            </div>
          </div>
          
          <div className="w-full md:w-3/4 px-2">
            {renderScatterPlot()}
          </div>
        </div>
      )}
    </div>
  );
};

export default ReleaseAnalysis; 