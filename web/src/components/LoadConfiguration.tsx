import React, { useState, useEffect, useMemo } from 'react';
import type { WorkflowConfig } from '../types';
import type { SavedConfiguration } from '../types/database';
import { getAllConfigurations, deleteConfiguration, getConfigurationById } from '../utils/database';
import { parseConfigurationData } from '../utils/configParser';
import { Search, Calendar, User, Eye, Trash2, X } from 'lucide-react';

interface LoadConfigurationProps {
  onConfigurationLoad: (config: WorkflowConfig) => void;
}

const LoadConfiguration: React.FC<LoadConfigurationProps> = ({ onConfigurationLoad }) => {
  const [configurations, setConfigurations] = useState<SavedConfiguration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedConfig, setSelectedConfig] = useState<SavedConfiguration | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

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
      // Close the modal after successful load
      setSelectedConfig(null);
    } catch (err) {
      console.error('Failed to parse configuration:', err);
      setError(err instanceof Error ? err.message : 'Failed to parse configuration data');
    }
  };

  const handleDeleteConfiguration = async (id: number) => {
    try {
      console.log(`🗑️ Attempting to delete configuration with ID: ${id}`);
      const success = await deleteConfiguration(id);
      console.log(`🗑️ Delete result: ${success}`);
      
      if (success) {
        console.log(`✅ Successfully deleted configuration ${id}, updating UI state`);
        
        // Update configurations list by removing the deleted item
        setConfigurations(prev => {
          const filtered = prev.filter(config => config.id !== id);
          console.log(`📋 Updated configurations list: ${filtered.length} items remaining`);
          return filtered;
        });
        
        // Close delete confirmation modal
        setShowDeleteConfirm(null);
        
        // Clear selected config if it was the deleted one
        if (selectedConfig && selectedConfig.id === id) {
          console.log(`🔄 Clearing selected config as it was deleted`);
          setSelectedConfig(null);
        }
        
        // Clear any existing errors
        setError(null);
        
        console.log(`✅ Configuration ${id} deleted successfully`);
      } else {
        console.error(`❌ Delete failed for configuration ${id}`);
        setError('Failed to delete configuration');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete configuration';
      console.error(`❌ Error deleting configuration ${id}:`, errorMessage);
      setError(errorMessage);
    }
  };

  // Filter configurations based on search query
  const filteredConfigurations = useMemo(() => {
    if (!searchQuery.trim()) return configurations;
    
    const query = searchQuery.toLowerCase();
    return configurations.filter(config => 
      config.name.toLowerCase().includes(query) ||
      config.description?.toLowerCase().includes(query) ||
      config.author.toLowerCase().includes(query)
    );
  }, [configurations, searchQuery]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return `${Math.floor(diffDays / 30)} months ago`;
  };

  if (loading) {
    return (
      <div className="py-8 px-6">
        <div className="w-3/5 mx-auto">
          <div className="text-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600 text-lg">Loading configurations...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="py-8 px-6">
      <div className="w-3/5 mx-auto relative">
        {/* Header */}
        <div className="text-center mb-8 animate-fade-in">
          <h1 className="text-4xl font-bold text-gray-900 mb-3">Configuration Library</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Browse and manage your saved workflow configurations. Select one to load into the editor.
          </p>
        </div>

        {/* Search Bar */}
        <div className="max-w-md mx-auto mb-8 animate-slide-up" style={{ animationDelay: '0.1s' }}>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search configurations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white shadow-sm transition-all duration-200 hover:shadow-md"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="max-w-2xl mx-auto mb-6 animate-shake">
            <div className="bg-red-50 border border-red-200 rounded-xl" style={{ padding: '3%' }}>
              <p className="text-red-700 text-center">{error}</p>
            </div>
          </div>
        )}

        {/* Configurations Grid */}
        {configurations.length === 0 ? (
          <div className="text-center py-16 animate-fade-in" style={{ animationDelay: '0.2s' }}>
            <div className="bg-white rounded-2xl shadow-lg p-12 max-w-md mx-auto">
              <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <Search className="w-10 h-10 text-gray-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No Configurations Found</h3>
              <p className="text-gray-500">Create and save your first workflow configuration to get started.</p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredConfigurations.map((config, index) => (
              <div
                key={config.id}
                className="group bg-white rounded-2xl shadow-md hover:shadow-xl transition-all duration-300 hover:scale-105 cursor-pointer overflow-hidden animate-slide-up"
                style={{ animationDelay: `${0.1 * index}s` }}
                onClick={() => handleConfigurationClick(config)}
              >
                <div className="p-6">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-semibold text-gray-900 truncate group-hover:text-blue-600 transition-colors">
                        {config.name}
                      </h3>
                      {config.description && (
                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                          {config.description}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center space-x-1 ml-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleConfigurationClick(config);
                        }}
                        className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all duration-200"
                        title="View details"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowDeleteConfirm(config.id!);
                        }}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all duration-200"
                        title="Delete configuration"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Metadata */}
                  <div className="space-y-3">
                    <div className="flex items-center text-sm text-gray-500">
                      <User className="w-4 h-4 mr-2" />
                      <span>By {config.author}</span>
                    </div>
                    <div className="flex items-center text-sm text-gray-500">
                      <Calendar className="w-4 h-4 mr-2" />
                      <span>{formatRelativeTime(config.last_modified)}</span>
                    </div>
                  </div>

                  {/* Footer */}
                  <div className="mt-4 flex items-center justify-between pt-4 border-t border-gray-100">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      v{config.version}
                    </span>
                    <span className="text-xs text-gray-400">
                      {formatDate(config.creation_date)}
                    </span>
                  </div>
                </div>

                {/* Hover overlay */}
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/0 to-purple-500/0 group-hover:from-blue-500/5 group-hover:to-purple-500/5 transition-all duration-300 pointer-events-none" />
              </div>
            ))}
          </div>
        )}

        {/* Show message when no search results */}
        {searchQuery && filteredConfigurations.length === 0 && configurations.length > 0 && (
          <div className="text-center py-16 animate-fade-in">
            <div className="bg-white rounded-2xl shadow-lg p-12 max-w-md mx-auto">
              <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <Search className="w-10 h-10 text-gray-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No Results Found</h3>
              <p className="text-gray-500">
                No configurations match your search for "{searchQuery}". Try a different search term.
              </p>
              <button
                onClick={() => setSearchQuery('')}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Clear Search
              </button>
            </div>
          </div>
        )}

        {/* Configuration Details Modal */}
        {selectedConfig && (
          <div 
            className="absolute inset-0 bg-black bg-opacity-50 z-[9999] overflow-y-auto"
            onClick={() => setSelectedConfig(null)}
          >
            <div 
              className="flex min-h-full items-center justify-center p-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full my-8 flex flex-col animate-slide-up" style={{ maxHeight: 'calc(100vh - 4rem)' }}>
              <div className="flex-shrink-0 p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-bold text-gray-900">{selectedConfig.name}</h2>
                  <button
                    onClick={() => setSelectedConfig(null)}
                    className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <X className="w-6 h-6" />
                  </button>
                </div>
                {selectedConfig.description && (
                  <p className="text-gray-600 mt-2">{selectedConfig.description}</p>
                )}
              </div>

              <div 
                className="flex-1 overflow-y-scroll custom-scrollbar" 
                style={{ padding: '3%' }}
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <div className="space-y-4">
                    <div className="flex items-center text-sm text-gray-600">
                      <User className="w-4 h-4 mr-2" />
                      <span className="font-medium">Author:</span>
                      <span className="ml-2">{selectedConfig.author}</span>
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <span className="font-medium">Version:</span>
                      <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                        v{selectedConfig.version}
                      </span>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div className="flex items-center text-sm text-gray-600">
                      <Calendar className="w-4 h-4 mr-2" />
                      <span className="font-medium">Created:</span>
                      <span className="ml-2">{formatDate(selectedConfig.creation_date)}</span>
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <Calendar className="w-4 h-4 mr-2" />
                      <span className="font-medium">Modified:</span>
                      <span className="ml-2">{formatDate(selectedConfig.last_modified)}</span>
                    </div>
                  </div>
                </div>

                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">System Prompt</h3>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <div className="text-sm text-gray-700 max-h-32 overflow-y-auto">
                      {selectedConfig.system_prompt || 'No system prompt'}
                    </div>
                  </div>
                </div>

                <div className="mb-6">
                  <details className="bg-gray-50 border border-gray-200 rounded-lg">
                    <summary className="px-4 py-3 cursor-pointer font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
                      View Full Configuration JSON
                    </summary>
                    <div className="p-4 border-t border-gray-200">
                      <pre className="text-xs text-gray-700 whitespace-pre-wrap overflow-x-auto bg-white p-3 rounded border max-h-64 overflow-y-auto">
                        {JSON.stringify(JSON.parse(selectedConfig.configuration_data), null, 2)}
                      </pre>
                    </div>
                  </details>
                </div>
              </div>

              <div className="flex-shrink-0 p-6 border-t border-gray-200 bg-gray-50">
                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => setSelectedConfig(null)}
                    className="px-6 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleLoadConfiguration}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                  >
                    Load Configuration
                  </button>
                </div>
              </div>
              </div>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && (
          <div 
            className="absolute inset-0 bg-black bg-opacity-50 z-[9999] overflow-y-auto"
            onClick={() => setShowDeleteConfirm(null)}
          >
            <div 
              className="flex min-h-full items-center justify-center p-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full animate-slide-up">
                <div className="p-6">
                  <h3 className="text-xl font-semibold text-gray-900 mb-4">Confirm Delete</h3>
                  <p className="text-gray-600 mb-6">
                    Are you sure you want to delete this configuration? This action cannot be undone.
                  </p>
                  <div className="flex justify-end space-x-3">
                    <button
                      onClick={() => setShowDeleteConfirm(null)}
                      className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => handleDeleteConfiguration(showDeleteConfirm)}
                      className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LoadConfiguration;