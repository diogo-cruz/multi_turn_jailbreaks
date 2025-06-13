'use client';

import { useState, useEffect } from 'react';
import { FolderOpen, User, FileCheck, Clock, AlertCircle } from 'lucide-react';
import { DirectoryInfo } from '@/types/evaluation';

export default function Home() {
  const [evaluatorName, setEvaluatorName] = useState('');
  const [directoryPath, setDirectoryPath] = useState('');
  const [directoryInfo, setDirectoryInfo] = useState<DirectoryInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Load saved evaluator name from localStorage
  useEffect(() => {
    const savedName = localStorage.getItem('evaluatorName');
    if (savedName) {
      setEvaluatorName(savedName);
    }
  }, []);

  const handleEvaluatorNameChange = (name: string) => {
    setEvaluatorName(name);
    localStorage.setItem('evaluatorName', name);
  };

  const loadDirectory = async () => {
    if (!directoryPath.trim()) {
      setError('Please enter a directory path');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`/api/directories?path=${encodeURIComponent(directoryPath)}`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to load directory');
      }

      const data: DirectoryInfo = await response.json();
      setDirectoryInfo(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load directory');
      setDirectoryInfo(null);
    } finally {
      setLoading(false);
    }
  };

  const startEvaluation = () => {
    if (!evaluatorName.trim()) {
      setError('Please enter your name first');
      return;
    }
    if (!directoryInfo) {
      setError('Please load a directory first');
      return;
    }

    // Navigate to evaluation page
    const params = new URLSearchParams({
      path: directoryInfo.path,
      evaluator: evaluatorName
    });
    window.location.href = `/evaluate?${params.toString()}`;
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-md p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8 text-center">
            Jailbreak Human Evaluator
          </h1>

          {/* Evaluator Name Input */}
          <div className="mb-8">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <User className="inline w-4 h-4 mr-2" />
              Your Name (Evaluator)
            </label>
            <input
              type="text"
              value={evaluatorName}
              onChange={(e) => handleEvaluatorNameChange(e.target.value)}
              placeholder="Enter your name"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Directory Path Input */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <FolderOpen className="inline w-4 h-4 mr-2" />
              Results Directory Path
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={directoryPath}
                onChange={(e) => setDirectoryPath(e.target.value)}
                placeholder="/path/to/results/directory"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                onClick={loadDirectory}
                disabled={loading}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Loading...' : 'Load'}
              </button>
            </div>
            <p className="text-sm text-gray-500 mt-1">
              Enter the full path to the directory containing .jsonl result files
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                <span className="text-red-700">{error}</span>
              </div>
            </div>
          )}

          {/* Directory Info */}
          {directoryInfo && (
            <div className="mb-8 p-6 bg-gray-50 rounded-md">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Directory Overview
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="bg-white p-4 rounded-md border">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Total Files</span>
                    <span className="text-2xl font-bold text-gray-900">
                      {directoryInfo.totalFiles}
                    </span>
                  </div>
                </div>
                <div className="bg-white p-4 rounded-md border">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Evaluated</span>
                    <div className="flex items-center">
                      <FileCheck className="w-5 h-5 text-green-500 mr-1" />
                      <span className="text-2xl font-bold text-green-600">
                        {directoryInfo.evaluatedFiles}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="bg-white p-4 rounded-md border">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Pending</span>
                    <div className="flex items-center">
                      <Clock className="w-5 h-5 text-orange-500 mr-1" />
                      <span className="text-2xl font-bold text-orange-600">
                        {directoryInfo.pendingFiles}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="text-sm text-gray-800 mb-4">
                <strong>Path:</strong> {directoryInfo.path}
              </div>

              {directoryInfo.pendingFiles > 0 ? (
                <button
                  onClick={startEvaluation}
                  className="w-full py-3 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium"
                >
                  Start Evaluation ({directoryInfo.pendingFiles} files pending)
                </button>
              ) : (
                <div className="text-center py-3 text-green-600 font-medium">
                  ✓ All files in this directory have been evaluated!
                </div>
              )}
            </div>
          )}

          {/* Instructions */}
          <div className="text-sm text-gray-800 space-y-2">
            <h4 className="font-medium text-gray-900">Instructions:</h4>
            <ol className="list-decimal list-inside space-y-1">
              <li>Enter your name as the evaluator</li>
              <li>Provide the path to a directory containing .jsonl result files</li>
              <li>Click "Load" to scan the directory for files</li>
              <li>Click "Start Evaluation" to begin evaluating pending files</li>
              <li>The system will automatically skip files you've already evaluated</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}
