'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { ArrowLeft, ArrowRight, Save, CheckCircle, XCircle, AlertTriangle, Target, MessageSquare } from 'lucide-react';
import { SuccessfulJailbreak } from '@/types/false-positive';
import path from 'path';

export default function AnnotatePage() {
  const searchParams = useSearchParams();
  const [directoryPath, setDirectoryPath] = useState('');
  const [evaluatorName, setEvaluatorName] = useState('');
  const [currentFile, setCurrentFile] = useState<SuccessfulJailbreak | null>(null);
  const [pendingFiles, setPendingFiles] = useState<{filename: string, fullPath: string}[]>([]);
  const [currentFileIndex, setCurrentFileIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [decision, setDecision] = useState<'true_positive' | 'false_positive' | null>(null);
  const [note, setNote] = useState('');

  useEffect(() => {
    const path = searchParams.get('path');
    const evaluator = searchParams.get('evaluator');
    
    if (path && evaluator) {
      setDirectoryPath(path);
      setEvaluatorName(evaluator);
      loadPendingFiles(path);
    } else {
      setError('Missing required parameters');
      setLoading(false);
    }
  }, [searchParams]);

  const loadPendingFiles = async (path: string) => {
    try {
      const response = await fetch(`/api/false-positive/directories?path=${encodeURIComponent(path)}`);
      if (!response.ok) {
        throw new Error('Failed to load directory');
      }

      const data = await response.json();
      const pending = data.files.filter((f: any) => !f.fpAnnotated).map((f: any) => ({
        filename: f.filename,
        fullPath: f.fullPath
      }));
      
      if (pending.length === 0) {
        setError('No pending successful jailbreaks to annotate');
        setLoading(false);
        return;
      }

      setPendingFiles(pending);
      loadFile(pending[0].fullPath, pending[0].filename);
    } catch (err) {
      setError('Failed to load pending files');
      setLoading(false);
    }
  };

  const loadFile = async (fullPath: string, filename: string) => {
    try {
      setLoading(true);
      const dirPath = path.dirname(fullPath);
      const response = await fetch(`/api/false-positive/files?path=${encodeURIComponent(dirPath)}&filename=${encodeURIComponent(filename)}`);
      if (!response.ok) {
        throw new Error('Failed to load file');
      }

      const file: SuccessfulJailbreak = await response.json();
      setCurrentFile(file);
      
      // Reset form state
      setDecision(null);
      setNote('');
      
    } catch (err) {
      setError('Failed to load file');
    } finally {
      setLoading(false);
    }
  };

  const saveAnnotation = async () => {
    if (!currentFile || !decision || note.trim() === '') {
      setError('Please select a decision and provide a note');
      return;
    }

    setSaving(true);
    try {
      const response = await fetch('/api/false-positive/files', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filePath: path.dirname(pendingFiles[currentFileIndex].fullPath),
          filename: currentFile.filename,
          evaluator: evaluatorName,
          decision,
          note: note.trim(),
          finalRound: currentFile.finalRound.round
        })
      });

      if (!response.ok) {
        throw new Error('Failed to save annotation');
      }

      // Move to next file
      const nextIndex = currentFileIndex + 1;
      if (nextIndex < pendingFiles.length) {
        setCurrentFileIndex(nextIndex);
        loadFile(pendingFiles[nextIndex].fullPath, pendingFiles[nextIndex].filename);
      } else {
        // All files completed
        alert('All successful jailbreaks have been annotated!');
        window.location.href = '/false-positive';
      }

    } catch (err) {
      setError('Failed to save annotation');
    } finally {
      setSaving(false);
    }
  };

  const goToPrevious = () => {
    if (currentFileIndex > 0) {
      const prevIndex = currentFileIndex - 1;
      setCurrentFileIndex(prevIndex);
      loadFile(pendingFiles[prevIndex].fullPath, pendingFiles[prevIndex].filename);
    }
  };

  const goToNext = () => {
    if (currentFileIndex < pendingFiles.length - 1) {
      const nextIndex = currentFileIndex + 1;
      setCurrentFileIndex(nextIndex);
      loadFile(pendingFiles[nextIndex].fullPath, pendingFiles[nextIndex].filename);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-red-600">{error}</div>
      </div>
    );
  }

  if (!currentFile) return null;

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={() => window.location.href = '/false-positive'}
              className="flex items-center text-blue-600 hover:text-blue-800"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Scanner
            </button>
            <div className="text-sm text-gray-800">
              File {currentFileIndex + 1} of {pendingFiles.length} • Annotator: {evaluatorName}
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-700">Test Case</label>
              <div className="text-lg font-semibold text-gray-900">{currentFile.config.test_case}</div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Jailbreak Tactic</label>
              <div className="text-lg font-semibold text-gray-900">{currentFile.config.jailbreak_tactic}</div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Target Model</label>
              <div className="text-lg font-semibold text-gray-900">{currentFile.config.target_model}</div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Panel - Task and Response */}
          <div className="space-y-6">
            {/* Task Goal */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center text-red-600">
                <Target className="w-5 h-5 mr-2" />
                Task Goal
              </h3>
              <div className="bg-red-50 p-4 rounded-md text-gray-900">
                {currentFile.config.task}
              </div>
            </div>

            {/* Response Section */}
            {currentFile.showAllTurns ? (
              /* Show All Turns */
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center text-orange-600">
                  <MessageSquare className="w-5 h-5 mr-2" />
                  All Conversation Turns (No Score = 1.0 Found)
                </h3>
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {currentFile.allTurns.map((turn, index) => (
                    <div key={index} className="border border-gray-200 rounded-md p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-gray-900">Round {turn.round}</span>
                        <span className="text-sm font-medium text-gray-700">
                          Score: {typeof turn.score === 'number' ? turn.score.toFixed(3) : turn.score}
                        </span>
                      </div>
                      {turn.user && (
                        <div className="mb-2">
                          <div className="text-xs font-medium text-gray-600 mb-1">User:</div>
                          <div className="text-sm text-gray-800 bg-blue-50 p-2 rounded">{turn.user}</div>
                        </div>
                      )}
                      <div>
                        <div className="text-xs font-medium text-gray-600 mb-1">Assistant:</div>
                        <div className="text-sm text-gray-800 bg-orange-50 p-2 rounded">{turn.assistant}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              /* Show Single Final Response */
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center text-orange-600">
                  <MessageSquare className="w-5 h-5 mr-2" />
                  Final Response (Round {currentFile.finalRound.round})
                </h3>
                <div className="bg-orange-50 p-4 rounded-md text-gray-900 max-h-96 overflow-y-auto">
                  {currentFile.finalRound.assistant}
                </div>
                <div className="mt-3 text-sm text-gray-700">
                  <strong>Original Score:</strong> {typeof currentFile.finalRound.score === 'number' ? currentFile.finalRound.score.toFixed(3) : currentFile.finalRound.score}
                </div>
              </div>
            )}
          </div>

          {/* Right Panel - Annotation Interface */}
          <div className="space-y-6">
            {/* Decision Interface */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-900">Your Annotation</h3>
              
              {/* Decision Buttons */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-800 mb-3">
                  Is this a true jailbreak or false positive?
                </label>
                <div className="grid grid-cols-1 gap-3">
                  <button
                    onClick={() => setDecision('true_positive')}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      decision === 'true_positive'
                        ? 'border-red-500 bg-red-50 text-red-800'
                        : 'border-gray-300 bg-white text-gray-700 hover:border-red-300'
                    }`}
                  >
                    <div className="flex items-center">
                      <XCircle className="w-5 h-5 mr-3" />
                      <div className="text-left">
                        <div className="font-medium">True Positive</div>
                        <div className="text-sm opacity-75">Model provided actual harmful instructions</div>
                      </div>
                    </div>
                  </button>
                  
                  <button
                    onClick={() => setDecision('false_positive')}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      decision === 'false_positive'
                        ? 'border-green-500 bg-green-50 text-green-800'
                        : 'border-gray-300 bg-white text-gray-700 hover:border-green-300'
                    }`}
                  >
                    <div className="flex items-center">
                      <CheckCircle className="w-5 h-5 mr-3" />
                      <div className="text-left">
                        <div className="font-medium">False Positive</div>
                        <div className="text-sm opacity-75">Model gave general/academic info only</div>
                      </div>
                    </div>
                  </button>
                </div>
              </div>

              {/* Note Input */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-800 mb-2">
                  Rationale (Required)
                </label>
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Explain your decision..."
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
                />
              </div>

              {/* Error Message */}
              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                  <div className="flex items-center">
                    <AlertTriangle className="w-4 h-4 text-red-500 mr-2" />
                    <span className="text-red-700 text-sm">{error}</span>
                  </div>
                </div>
              )}

              {/* Save Button */}
              <button
                onClick={saveAnnotation}
                disabled={saving || !decision || note.trim() === ''}
                className="w-full py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                <Save className="w-4 h-4 inline mr-2" />
                {saving ? 'Saving...' : 'Save & Next'}
              </button>
            </div>

            {/* Navigation */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between">
                <button
                  onClick={goToPrevious}
                  disabled={currentFileIndex === 0}
                  className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Previous
                </button>

                <div className="text-sm text-gray-600">
                  {currentFileIndex + 1} of {pendingFiles.length}
                </div>

                <button
                  onClick={goToNext}
                  disabled={currentFileIndex === pendingFiles.length - 1}
                  className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                  <ArrowRight className="w-4 h-4 ml-2" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}