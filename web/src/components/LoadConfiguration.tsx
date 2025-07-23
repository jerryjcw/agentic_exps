import React, { useState, useEffect } from 'react';
import type { WorkflowConfig } from '../types';
import type { SavedConfiguration } from '../types/database';
import { getAllConfigurations, deleteConfiguration, getConfigurationById } from '../utils/database';
import { parseConfigurationData } from '../utils/configParser';

interface LoadConfigurationProps {
  onConfigurationLoad: (config: WorkflowConfig) => void;
}

const LoadConfiguration: React.FC<LoadConfigurationProps> = ({ onConfigurationLoad }) => {
  const [configurations, setConfigurations] = useState<SavedConfiguration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedConfig, setSelectedConfig] = useState<SavedConfiguration | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<number | null>(null);

  useEffect(() => {
    loadConfigurations();
  }, []);

  const loadConfigurations = async () => {
    try {
      setLoading(true);
      const configs = await getAllConfigurations();
      setConfigurations(configs);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load configurations');
    } finally {
      setLoading(false);
    }
  };

  const handleConfigurationClick = async (config: SavedConfiguration) => {
    try {
      const fullConfig = await getConfigurationById(config.id!);
      if (!fullConfig) {
        setError('Configuration not found');
        return;
      }

      setSelectedConfig(fullConfig);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load configuration details');
    }
  };

  const handleLoadConfiguration = () => {
    if (!selectedConfig) return;

    try {
      const workflowConfig = parseConfigurationData(selectedConfig.configuration_data);
      onConfigurationLoad(workflowConfig);
    } catch (err) {
      console.error('Failed to parse configuration:', err);
      setError(err instanceof Error ? err.message : 'Failed to parse configuration data');
    }
  };

  const handleDeleteConfiguration = async (id: number) => {
    try {
      const success = await deleteConfiguration(id);
      if (success) {
        setConfigurations(prev => prev.filter(config => config.id !== id));
        setShowDeleteConfirm(null);
        if (selectedConfig && selectedConfig.id === id) {
          setSelectedConfig(null);
        }
      } else {
        setError('Failed to delete configuration');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete configuration');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="text-center py-8">
          <p className="text-gray-500">Loading configurations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">Load Configuration</h2>
          <p className="text-gray-600 mt-1">Select a saved configuration to load into the editor</p>
        </div>

        {error && (
          <div className="m-6 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
          {/* Configuration List */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Saved Configurations</h3>
            
            {configurations.length === 0 ? (
              <div className="text-center py-8 bg-gray-50 border border-gray-200 rounded-md">
                <p className="text-gray-500">No saved configurations found</p>
                <p className="text-gray-400 text-sm mt-1">Create and save a configuration first</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {configurations.map((config) => (
                  <div
                    key={config.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedConfig?.id === config.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                    onClick={() => handleConfigurationClick(config)}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{config.name}</h4>
                        {config.description && (
                          <p className="text-sm text-gray-600 mt-1">{config.description}</p>
                        )}
                        <div className="text-xs text-gray-500 mt-2 space-y-1">
                          <p>Author: {config.author}</p>
                          <p>Created: {formatDate(config.creation_date)}</p>
                          <p>Modified: {formatDate(config.last_modified)}</p>
                          <p>Version: {config.version}</p>
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowDeleteConfirm(config.id!);
                        }}
                        className="ml-2 p-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                        title="Delete configuration"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Configuration Details */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Configuration Details</h3>
            
            {selectedConfig ? (
              <div className="space-y-4">
                <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
                  <h4 className="font-medium text-gray-900 mb-2">{selectedConfig.name}</h4>
                  {selectedConfig.description && (
                    <p className="text-gray-700 mb-3">{selectedConfig.description}</p>
                  )}
                  
                  <div className="text-sm text-gray-600 space-y-1">
                    <p><strong>Author:</strong> {selectedConfig.author}</p>
                    <p><strong>Version:</strong> {selectedConfig.version}</p>
                    <p><strong>Created:</strong> {formatDate(selectedConfig.creation_date)}</p>
                    <p><strong>Last Modified:</strong> {formatDate(selectedConfig.last_modified)}</p>
                  </div>

                  <div className="mt-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">System Prompt:</p>
                    <div className="bg-white border border-gray-200 rounded p-3 text-sm text-gray-700 max-h-32 overflow-y-auto">
                      {selectedConfig.system_prompt || 'No system prompt'}
                    </div>
                  </div>
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => setSelectedConfig(null)}
                    className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleLoadConfiguration}
                    className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
                  >
                    Load Configuration
                  </button>
                </div>

                <div className="mt-6">
                  <details className="bg-gray-50 border border-gray-200 rounded-md">
                    <summary className="px-4 py-3 cursor-pointer font-medium text-gray-700 hover:bg-gray-100">
                      View Full Configuration JSON
                    </summary>
                    <div className="p-4 border-t border-gray-200">
                      <pre className="text-xs text-gray-700 whitespace-pre-wrap overflow-x-auto bg-white p-3 rounded border">
                        {JSON.stringify(JSON.parse(selectedConfig.configuration_data), null, 2)}
                      </pre>
                    </div>
                  </details>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 bg-gray-50 border border-gray-200 rounded-md">
                <p className="text-gray-500">Select a configuration to view details</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Confirm Delete</h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete this configuration? This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteConfiguration(showDeleteConfirm)}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LoadConfiguration;