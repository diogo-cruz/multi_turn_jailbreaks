import React from 'react';

const DebugTurnTypeData = ({ data }) => {
  if (!data || !Array.isArray(data)) {
    return <div>No data to analyze</div>;
  }

  // Analyze each model's data
  const analysis = data.map(model => {
    // Count overall data
    const totalRows = model.rows?.length || 0;
    
    // Get single-turn data
    const singleTurnRows = model.rows?.filter(row => row.turn_type === 'single') || [];
    const singleTurnCount = singleTurnRows.length;
    
    // Get multi-turn data
    const multiTurnRows = model.rows?.filter(row => row.turn_type === 'multi') || [];
    const multiTurnCount = multiTurnRows.length;
    
    // Get success counts
    const singleTurnSuccessCount = singleTurnRows.filter(row => {
      if (typeof row.goal_achieved === 'boolean') {
        return row.goal_achieved === true;
      } else if (typeof row.goal_achieved === 'string') {
        return row.goal_achieved.toLowerCase() === 'true';
      }
      return false;
    }).length;
    
    const multiTurnSuccessCount = multiTurnRows.filter(row => {
      if (typeof row.goal_achieved === 'boolean') {
        return row.goal_achieved === true;
      } else if (typeof row.goal_achieved === 'string') {
        return row.goal_achieved.toLowerCase() === 'true';
      }
      return false;
    }).length;
    
    // Calculate success rates
    const singleTurnSuccessRate = singleTurnCount > 0 
      ? (singleTurnSuccessCount / singleTurnCount) * 100 
      : 0;
    
    const multiTurnSuccessRate = multiTurnCount > 0 
      ? (multiTurnSuccessCount / multiTurnCount) * 100 
      : 0;
    
    // Get values stored on model object for comparison
    const modelSingleTurnSuccessRate = model.singleTurnSuccessRate;
    const modelMultiTurnSuccessRate = model.multiTurnSuccessRate;
    
    // Check row data consistency
    const turnTypeConsistency = model.rows?.every(row => row.turn_type === 'single' || row.turn_type === 'multi');
    const rowsWithoutTurnType = model.rows?.filter(row => !row.turn_type).length || 0;
    
    // Check data in processed components
    const hasTurnTypeData = {
      singleTurn: {
        testCaseRates: model.singleTurn?.testCaseRates?.length > 0,
        rows: model.singleTurnRows?.length > 0
      },
      multiTurn: {
        testCaseRates: model.multiTurn?.testCaseRates?.length > 0,
        rows: model.multiTurnRows?.length > 0
      }
    };

    return {
      name: model.name,
      totalRows,
      singleTurnCount,
      multiTurnCount,
      singleTurnSuccessRate,
      multiTurnSuccessRate,
      modelSingleTurnSuccessRate,
      modelMultiTurnSuccessRate,
      turnTypeConsistency,
      rowsWithoutTurnType,
      hasTurnTypeData
    };
  });

  return (
    <div className="bg-white p-4 mb-8 border rounded shadow-sm">
      <h2 className="text-xl font-semibold mb-4">Turn Type Data Debug</h2>
      <p className="mb-4 text-sm">
        This component helps debug why turn type filtering isn't working properly.
        It analyzes each model's data to check for turn type information and consistency.
      </p>
      
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="p-2 text-left">Model</th>
              <th className="p-2 text-right">Total Rows</th>
              <th className="p-2 text-right">Single-Turn</th>
              <th className="p-2 text-right">Multi-Turn</th>
              <th className="p-2 text-right">Single %</th>
              <th className="p-2 text-right">Model Single %</th>
              <th className="p-2 text-right">Multi %</th>
              <th className="p-2 text-right">Model Multi %</th>
              <th className="p-2 text-center">Type Consistency</th>
              <th className="p-2 text-right">Missing Type</th>
            </tr>
          </thead>
          <tbody>
            {analysis.map(model => (
              <tr key={model.name} className="border-t hover:bg-gray-50">
                <td className="p-2">{model.name}</td>
                <td className="p-2 text-right">{model.totalRows}</td>
                <td className="p-2 text-right">{model.singleTurnCount}</td>
                <td className="p-2 text-right">{model.multiTurnCount}</td>
                <td className="p-2 text-right">{model.singleTurnSuccessRate.toFixed(1)}%</td>
                <td className={`p-2 text-right ${model.modelSingleTurnSuccessRate ? (Math.abs(model.singleTurnSuccessRate - model.modelSingleTurnSuccessRate) < 0.1 ? 'text-green-600' : 'text-red-600 font-bold') : 'text-gray-400'}`}>
                  {model.modelSingleTurnSuccessRate?.toFixed(1) || 'N/A'}%
                </td>
                <td className="p-2 text-right">{model.multiTurnSuccessRate.toFixed(1)}%</td>
                <td className={`p-2 text-right ${model.modelMultiTurnSuccessRate ? (Math.abs(model.multiTurnSuccessRate - model.modelMultiTurnSuccessRate) < 0.1 ? 'text-green-600' : 'text-red-600 font-bold') : 'text-gray-400'}`}>
                  {model.modelMultiTurnSuccessRate?.toFixed(1) || 'N/A'}%
                </td>
                <td className={`p-2 text-center ${model.turnTypeConsistency ? 'text-green-600' : 'text-red-600 font-bold'}`}>
                  {model.turnTypeConsistency ? '✓' : '✗'}
                </td>
                <td className={`p-2 text-right ${model.rowsWithoutTurnType > 0 ? 'text-red-600 font-bold' : 'text-green-600'}`}>
                  {model.rowsWithoutTurnType}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div className="mt-6 text-sm text-gray-600">
        <p><strong>Notes:</strong></p>
        <ul className="list-disc ml-6 space-y-1">
          <li>Red values indicate discrepancies between calculated and stored values</li>
          <li>Missing turn_type field in rows will prevent proper filtering</li>
          <li>Check if original data has turn_type field or if it needs to be inferred from other fields</li>
        </ul>
      </div>
    </div>
  );
};

export default DebugTurnTypeData; 