import React, { useState } from 'react';
import type { WorkflowConfig } from '../types';
import { convertToJSON } from '../utils/configConverter';
import { Play, Settings, Eye, EyeOff, CheckCircle, AlertCircle, Terminal, Zap, Copy, Download } from 'lucide-react';

interface ExecuteConfigurationProps {
  config: WorkflowConfig;
}

const ExecuteConfiguration: React.FC<ExecuteConfigurationProps> = ({ config }) => {
  const [apiEndpoint, setApiEndpoint] = useState('http://localhost:8000/workflow/run');
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showFullConfig, setShowFullConfig] = useState(false);

  const handleExecute = async () => {
    if (!apiEndpoint.trim()) {
      setError('API endpoint is required');
      return;
    }

    if (config.agents.length === 0) {
      setError('Cannot execute empty configuration. Please add at least one agent.');
      return;
    }

    setExecuting(true);
    setError(null);
    setResult(null);

    try {
      // Convert workflow config to JSON format
      const jsonConfig = convertToJSON(config);
      
      const response = await fetch(apiEndpoint.trim(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(jsonConfig),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const responseData = await response.text();
      // Try to parse as JSON, fall back to plain text
      try {
        const jsonData = JSON.parse(responseData);
        setResult(JSON.stringify(jsonData, null, 2));
      } catch {
        setResult(responseData);
      }
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred during execution');
      }
    } finally {
      setExecuting(false);
    }
  };

  const configJson = config.agents.length > 0 ? convertToJSON(config) : null;

  return (
    <div className="py-8 px-6">
      <div className="w-3/5 mx-auto">
        {/* Header */}
        <div className="text-center mb-8 animate-fade-in">
          <h1 className="text-4xl font-bold text-gray-900 mb-3">Execute Workflow</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Send your workflow configuration to the backend for execution and monitor results
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Execution Settings */}
          <div className="space-y-6">
            {/* API Configuration Card */}
            <div className="bg-white rounded-2xl shadow-lg animate-slide-up" style={{ padding: '3%' }}>
              <div className="flex items-center mb-6">
                <div className="w-10 h-10 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg flex items-center justify-center mr-3">
                  <Settings className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">API Configuration</h2>
                  <p className="text-sm text-gray-500">Configure the backend endpoint</p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-800 mb-2 flex items-center">
                  <Terminal className="w-4 h-4 mr-2" />
                  API Endpoint *
                </label>
                <input
                  type="url"
                  value={apiEndpoint}
                  onChange={(e) => {
                    setApiEndpoint(e.target.value);
                    setError(null);
                    setResult(null);
                  }}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 hover:border-gray-400 font-mono text-sm"
                  placeholder="http://localhost:8000/workflow/run"
                  disabled={executing}
                />
                <p className="text-xs text-gray-500 mt-2">
                  Enter the backend API endpoint URL for workflow execution
                </p>
              </div>
            </div>

            {/* Configuration Summary Card */}
            {configJson && (
              <div className="bg-white rounded-2xl shadow-lg p-6 animate-slide-up" style={{ animationDelay: '0.1s' }}>
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center mr-3">
                      <Zap className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h2 className="text-xl font-semibold text-gray-900">Configuration Summary</h2>
                      <p className="text-sm text-gray-500">Overview of your workflow</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setShowFullConfig(!showFullConfig)}
                    className="flex items-center px-3 py-1 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
                  >
                    {showFullConfig ? <EyeOff className="w-4 h-4 mr-1" /> : <Eye className="w-4 h-4 mr-1" />}
                    {showFullConfig ? 'Hide' : 'Show'} JSON
                  </button>
                </div>
                
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="bg-blue-50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-blue-600">{config.agents.length}</div>
                    <div className="text-sm text-blue-700">Root Agent{config.agents.length !== 1 ? 's' : ''}</div>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-purple-600">
                      {config.systemPrompt ? '✓' : '○'}
                    </div>
                    <div className="text-sm text-purple-700">System Prompt</div>
                  </div>
                </div>

                <div className="space-y-3">
                  <div>
                    <span className="text-sm font-semibold text-gray-700">System Prompt:</span>
                    <p className="text-sm text-gray-600 mt-1 line-clamp-2 bg-gray-50 rounded-lg p-2">
                      {config.systemPrompt || 'None specified'}
                    </p>
                  </div>
                </div>

                {showFullConfig && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="bg-gray-50 rounded-xl p-4 max-h-64 overflow-y-auto">
                      <pre className="text-xs text-gray-700 whitespace-pre-wrap overflow-x-auto font-mono leading-relaxed">
                        {JSON.stringify(configJson, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Execute Button */}
            <div className="animate-slide-up" style={{ animationDelay: '0.2s' }}>
              <button
                onClick={handleExecute}
                disabled={executing || config.agents.length === 0 || !apiEndpoint.trim()}
                className={`w-full py-4 px-6 rounded-xl font-semibold text-lg transition-all duration-200 flex items-center justify-center ${
                  executing || config.agents.length === 0 || !apiEndpoint.trim()
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-gradient-to-r from-orange-600 to-red-600 text-white hover:from-orange-700 hover:to-red-700 shadow-lg hover:shadow-xl transform hover:scale-105'
                }`}
              >
                {executing ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                    Executing Workflow...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5 mr-3" />
                    Execute Configuration
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Results Panel */}
          <div className="space-y-6">
            {/* Empty State */}
            {config.agents.length === 0 && (
              <div className="bg-white rounded-2xl shadow-lg p-6 animate-slide-up" style={{ animationDelay: '0.1s' }}>
                <div className="text-center py-16">
                  <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Play className="w-10 h-10 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">No Configuration to Execute</h3>
                  <p className="text-gray-500">Please create a configuration first by adding agents in the Create tab.</p>
                </div>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="bg-white rounded-2xl shadow-lg animate-slide-up" style={{ padding: '3%' }}>
                <div className="p-4 bg-red-50 border border-red-200 rounded-xl">
                  <div className="flex items-center mb-3">
                    <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
                    <h4 className="font-semibold text-red-800">Execution Error</h4>
                  </div>
                  <p className="text-red-700 text-sm">{error}</p>
                </div>
              </div>
            )}

            {/* Success Result */}
            {result && (
              <div className="bg-white rounded-2xl shadow-lg animate-slide-up" style={{ padding: '3%' }}>
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center">
                      <CheckCircle className="w-6 h-6 text-green-600 mr-3" />
                      <h4 className="text-lg font-semibold text-green-800">Execution Completed Successfully</h4>
                    </div>
                    <div className="text-sm text-green-600 bg-green-100 px-3 py-1 rounded-full">
                      ✓ Success
                    </div>
                  </div>
                  
                  {/* Result Content */}
                  <div className="space-y-4">
                    {(() => {
                      try {
                        const jsonData = JSON.parse(result);
                        return (
                          <div className="bg-white border border-green-200 rounded-lg overflow-hidden">
                            <div className="bg-green-100 px-4 py-2 border-b border-green-200">
                              <h5 className="font-medium text-green-800 flex items-center">
                                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                                Workflow Result (JSON)
                              </h5>
                            </div>
                            <div className="p-4 max-h-96 overflow-y-auto custom-scrollbar">
                              <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono leading-relaxed">
                                {JSON.stringify(jsonData, null, 2)}
                              </pre>
                            </div>
                          </div>
                        );
                      } catch {
                        return (
                          <div className="bg-white border border-green-200 rounded-lg overflow-hidden">
                            <div className="bg-green-100 px-4 py-2 border-b border-green-200">
                              <h5 className="font-medium text-green-800 flex items-center">
                                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                                Workflow Result (Text)
                              </h5>
                            </div>
                            <div className="p-4 max-h-96 overflow-y-auto custom-scrollbar">
                              <div className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                                {result}
                              </div>
                            </div>
                          </div>
                        );
                      }
                    })()}
                    
                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-2">
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(result);
                          alert('Result copied to clipboard!');
                        }}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
                      >
                        <Copy className="w-4 h-4" />
                        Copy Result
                      </button>
                      <button
                        onClick={() => {
                          const blob = new Blob([result], { type: 'application/json' });
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = `workflow-result-${Date.now()}.json`;
                          document.body.appendChild(a);
                          a.click();
                          document.body.removeChild(a);
                          URL.revokeObjectURL(url);
                        }}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                      >
                        <Download className="w-4 h-4" />
                        Download Result
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Instructions Card */}
            <div className="bg-white rounded-2xl shadow-lg p-6 animate-slide-up" style={{ animationDelay: '0.3s' }}>
              <div className="flex items-center mb-4">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                  <Settings className="w-4 h-4 text-blue-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">Execution Instructions</h3>
              </div>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-start">
                  <span className="text-blue-600 mr-2">•</span>
                  Make sure your backend server is running at the specified endpoint
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-2">•</span>
                  The configuration will be sent as a POST request with JSON payload
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-2">•</span>
                  Results will be displayed here once execution completes
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-2">•</span>
                  Large responses may be truncated for display purposes
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExecuteConfiguration;