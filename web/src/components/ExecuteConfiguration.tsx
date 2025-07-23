import React, { useState } from 'react';
import type { WorkflowConfig } from '../types';
import { convertToJSON } from '../utils/configConverter';

interface ExecuteConfigurationProps {
  config: WorkflowConfig;
}

const ExecuteConfiguration: React.FC<ExecuteConfigurationProps> = ({ config }) => {
  const [apiEndpoint, setApiEndpoint] = useState('http://localhost:8000/api/workflow/execute');
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
      setResult(responseData);
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
    <div className="max-w-6xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">Execute Configuration</h2>
          <p className="text-gray-600 mt-1">Send your workflow configuration to the backend for execution</p>
        </div>

        <div className="p-6">
          {/* API Configuration */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">API Configuration</h3>
            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
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
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="http://localhost:8000/api/workflow/execute"
                  disabled={executing}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Enter the backend API endpoint URL for workflow execution
                </p>
              </div>
            </div>
          </div>

          {/* Configuration Summary */}
          {configJson && (
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Configuration Summary</h3>
                <button
                  onClick={() => setShowFullConfig(!showFullConfig)}
                  className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                >
                  {showFullConfig ? 'Hide' : 'Show'} Full Configuration
                </button>
              </div>
              
              <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">System Prompt:</span>
                    <p className="text-gray-600 mt-1 truncate">{config.systemPrompt || 'None'}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Total Agents:</span>
                    <p className="text-gray-600 mt-1">{config.agents.length}</p>
                  </div>
                </div>

                {showFullConfig && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <pre className="text-xs text-gray-700 whitespace-pre-wrap overflow-x-auto bg-white p-3 rounded border max-h-64 overflow-y-auto">
                      {JSON.stringify(configJson, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Error/Result Messages */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
              <h4 className="font-medium text-red-800 mb-2">Execution Error</h4>
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {result && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md">
              <h4 className="font-medium text-green-800 mb-2">Execution Result</h4>
              <div className="bg-white border border-green-200 rounded p-3 max-h-64 overflow-y-auto">
                <pre className="text-sm text-green-700 whitespace-pre-wrap">{result}</pre>
              </div>
            </div>
          )}

          {/* Execute Button */}
          <div className="flex justify-center">
            <button
              onClick={handleExecute}
              disabled={executing || config.agents.length === 0 || !apiEndpoint.trim()}
              className={`px-8 py-3 rounded-md font-medium text-lg transition-colors ${
                executing || config.agents.length === 0 || !apiEndpoint.trim()
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg hover:shadow-xl'
              }`}
            >
              {executing ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Executing...
                </span>
              ) : (
                '▶️ Execute Configuration'
              )}
            </button>
          </div>

          {/* Empty State */}
          {config.agents.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500 text-lg">No configuration to execute.</p>
              <p className="text-gray-400 text-sm mt-2">Please create a configuration first by adding agents.</p>
            </div>
          )}

          {/* Instructions */}
          <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-md">
            <h4 className="font-medium text-blue-800 mb-2">Instructions</h4>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• Make sure your backend server is running at the specified endpoint</li>
              <li>• The configuration will be sent as a POST request with JSON payload</li>
              <li>• Results will be displayed here once execution completes</li>
              <li>• Large responses may be truncated for display purposes</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExecuteConfiguration;