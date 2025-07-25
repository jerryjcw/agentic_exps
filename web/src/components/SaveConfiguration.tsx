import React, { useState } from 'react';
import type { WorkflowConfig } from '../types';
import { saveConfiguration } from '../utils/database';
import { convertToJSON } from '../utils/configConverter';
import { AutoResizeTextarea } from './AutoResizeTextarea';
import { Save, User, FileText, Code, CheckCircle, AlertCircle } from 'lucide-react';

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
      // Save the original config structure (not the converted JSON) to preserve templates
      const now = new Date().toISOString();
      const configToSave = {
        name: formData.name.trim(),
        description: formData.description.trim() || null,
        author: formData.author.trim(),
        creation_date: now,
        last_modified: now,
        version: 1,
        configuration_data: JSON.stringify(config, null, 2), // Save original config, not converted JSON
        system_prompt: config.systemPrompt,
        global_attributes: JSON.stringify(config.globalAttributes)
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
    <div className="py-8 px-6">
      <div className="w-3/5 mx-auto">
        {/* Header */}
        <div className="text-center mb-8 animate-fade-in">
          <h1 className="text-4xl font-bold text-gray-900 mb-3">Save Configuration</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Preserve your workflow configuration for future use and sharing
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Save Form */}
          <div className="bg-white rounded-2xl shadow-lg animate-slide-up" style={{ padding: '3%' }}>
            <div className="flex items-center mb-6">
              <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg flex items-center justify-center mr-3">
                <Save className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Configuration Details</h2>
                <p className="text-sm text-gray-500">Fill in the metadata for your workflow</p>
              </div>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-gray-800 mb-2 flex items-center">
                  <FileText className="w-4 h-4 mr-2" />
                  Configuration Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 hover:border-gray-400"
                  placeholder="Enter a unique name for this configuration"
                  disabled={saving}
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-800 mb-2">
                  Description
                </label>
                <AutoResizeTextarea
                  value={formData.description}
                  onChange={(value: string) => handleInputChange('description', value)}
                  placeholder="Optional description of what this configuration does"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 hover:border-gray-400"
                  minRows={3}
                  maxRows={6}
                  disabled={saving}
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-800 mb-2 flex items-center">
                  <User className="w-4 h-4 mr-2" />
                  Author *
                </label>
                <input
                  type="text"
                  value={formData.author}
                  onChange={(e) => handleInputChange('author', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 hover:border-gray-400"
                  placeholder="Enter author name"
                  disabled={saving}
                />
              </div>
            </div>

            {/* Error/Success Messages */}
            {error && (
              <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-xl animate-shake">
                <div className="flex items-center">
                  <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
                  <p className="text-red-700">{error}</p>
                </div>
              </div>
            )}

            {success && (
              <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-xl animate-fade-in">
                <div className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                  <p className="text-green-700">{success}</p>
                </div>
              </div>
            )}

            {/* Save Button */}
            <div className="mt-8">
              <button
                onClick={handleSave}
                disabled={saving || config.agents.length === 0}
                className={`w-full py-3 px-4 rounded-xl font-medium transition-all duration-200 flex items-center justify-center ${
                  saving || config.agents.length === 0
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-gradient-to-r from-green-600 to-emerald-600 text-white hover:from-green-700 hover:to-emerald-700 shadow-md hover:shadow-lg'
                }`}
              >
                {saving ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Save Configuration
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Configuration Preview */}
          <div className="bg-white rounded-2xl shadow-lg animate-slide-up" style={{ animationDelay: '0.1s', padding: '3%' }}>
            <div className="flex items-center mb-6">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center mr-3">
                <Code className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Preview</h2>
                <p className="text-sm text-gray-500">Current configuration overview</p>
              </div>
            </div>

            {config.agents.length === 0 ? (
              <div className="text-center py-16">
                <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <Code className="w-10 h-10 text-gray-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No Configuration to Save</h3>
                <p className="text-gray-500">Please create a configuration first by adding agents in the Create tab.</p>
              </div>
            ) : (
              <>
                {/* Configuration Stats */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="bg-blue-50 rounded-lg" style={{ padding: '3%' }}>
                    <div className="text-2xl font-bold text-blue-600">{config.agents.length}</div>
                    <div className="text-sm text-blue-700">Root Agent{config.agents.length !== 1 ? 's' : ''}</div>
                  </div>
                  <div className="bg-purple-50 rounded-lg" style={{ padding: '3%' }}>
                    <div className="text-2xl font-bold text-purple-600">
                      {config.systemPrompt ? '✓' : '○'}
                    </div>
                    <div className="text-sm text-purple-700">System Prompt</div>
                  </div>
                </div>

                {/* JSON Preview */}
                {configPreview && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">JSON Preview</h3>
                    <div className="bg-gray-50 border border-gray-200 rounded-xl max-h-96 overflow-y-auto" style={{ padding: '3%' }}>
                      <pre className="text-xs text-gray-700 whitespace-pre-wrap overflow-x-auto font-mono leading-relaxed">
                        {JSON.stringify(configPreview, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SaveConfiguration;