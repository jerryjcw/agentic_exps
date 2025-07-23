import React, { useState } from 'react';
import type { WorkflowConfig } from '../types';
import { saveConfiguration } from '../utils/database';
import { convertToJSON } from '../utils/configConverter';
import { AutoResizeTextarea } from './AutoResizeTextarea';

interface SaveConfigurationProps {
  config: WorkflowConfig;
  onSaveSuccess: (id: number, name: string) => void;
}

const SaveConfiguration: React.FC<SaveConfigurationProps> = ({ config, onSaveSuccess }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    author: 'default_user'
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(null);
    setSuccess(null);
  };

  const handleSave = async () => {
    if (!formData.name.trim()) {
      setError('Configuration name is required');
      return;
    }

    if (!formData.author.trim()) {
      setError('Author name is required');
      return;
    }

    if (config.agents.length === 0) {
      setError('Cannot save empty configuration. Please add at least one agent.');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      // Convert workflow config to JSON format
      const jsonConfig = convertToJSON(config);
      
      const now = new Date().toISOString();
      const configToSave = {
        name: formData.name.trim(),
        description: formData.description.trim() || null,
        author: formData.author.trim(),
        creation_date: now,
        last_modified: now,
        version: 1,
        configuration_data: JSON.stringify(jsonConfig, null, 2),
        system_prompt: config.systemPrompt
      };

      const id = await saveConfiguration(configToSave);
      setSuccess(`Configuration "${formData.name}" saved successfully!`);
      onSaveSuccess(id, formData.name);
      
      // Reset form
      setFormData({
        name: '',
        description: '',
        author: 'default_user'
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const configPreview = config.agents.length > 0 ? convertToJSON(config) : null;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">Save Configuration</h2>
          <p className="text-gray-600 mt-1">Save your workflow configuration to the database</p>
        </div>

        <div className="p-6">
          {/* Save Form */}
          <div className="grid grid-cols-1 gap-6 mb-8">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Configuration Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter a unique name for this configuration"
                disabled={saving}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <AutoResizeTextarea
                value={formData.description}
                onChange={(value: string) => handleInputChange('description', value)}
                placeholder="Optional description of what this configuration does"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                minRows={2}
                maxRows={4}
                disabled={saving}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Author *
              </label>
              <input
                type="text"
                value={formData.author}
                onChange={(e) => handleInputChange('author', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter author name"
                disabled={saving}
              />
            </div>
          </div>

          {/* Error/Success Messages */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {success && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
              <p className="text-green-700">{success}</p>
            </div>
          )}

          {/* Save Button */}
          <div className="flex justify-end mb-8">
            <button
              onClick={handleSave}
              disabled={saving || config.agents.length === 0}
              className={`px-6 py-2 rounded-md font-medium transition-colors ${
                saving || config.agents.length === 0
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {saving ? 'Saving...' : 'Save Configuration'}
            </button>
          </div>

          {/* Configuration Preview */}
          {configPreview && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Configuration Preview</h3>
              <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap overflow-x-auto">
                  {JSON.stringify(configPreview, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {config.agents.length === 0 && (
            <div className="text-center py-8">
              <p className="text-gray-500 text-lg">No configuration to save.</p>
              <p className="text-gray-400 text-sm mt-2">Please create a configuration first by adding agents.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SaveConfiguration;