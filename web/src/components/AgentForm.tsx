import React, { useState } from 'react';
import type { Agent } from '../types';
import { Trash2, File, FolderOpen, Upload } from 'lucide-react';
import { AutoResizeTextarea } from './AutoResizeTextarea';
import { handleFileUpload, saveFileToKnownLocation } from '../utils/fileHandler';

interface AgentFormProps {
  agent: Agent;
  onChange: (agent: Agent) => void;
  onDelete: () => void;
  availableTools: string[];
}

export const AgentForm: React.FC<AgentFormProps> = ({
  agent,
  onChange,
  onDelete,
  availableTools
}) => {
  const [showManualPathInput, setShowManualPathInput] = useState(false);
  const [manualPath, setManualPath] = useState('');
  const handleInputChange = (field: keyof Agent, value: any) => {
    onChange({ ...agent, [field]: value });
  };

  const handleFileSelect = async () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    // Accept all file types
    input.accept = '*/*';
    
    input.onchange = async (e) => {
      const files = (e.target as HTMLInputElement).files;
      if (files) {
        const existingFiles = agent.input_files || [];
        const newInputFiles = [];
        
        for (const file of Array.from(files)) {
          try {
            const inputFile = await handleFileUpload(file, agent.name);
            await saveFileToKnownLocation(inputFile);
            newInputFiles.push(inputFile);
          } catch (error) {
            console.error(`Failed to process file ${file.name}:`, error);
            alert(`Failed to process file ${file.name}: ${error}`);
          }
        }
        
        if (newInputFiles.length > 0) {
          const updatedFiles = [...existingFiles, ...newInputFiles];
          handleInputChange('input_files', updatedFiles);
        }
      }
    };
    input.click();
  };

  const removeFile = (index: number) => {
    const files = agent.input_files || [];
    const newFiles = files.filter((_, i) => i !== index);
    handleInputChange('input_files', newFiles);
  };

  const handleManualPathAdd = () => {
    if (manualPath.trim()) {
      const newFile = {
        input_path: manualPath.trim(),
        input_type: 'text',
        target_agent: [agent.name]
      };
      
      const existingFiles = agent.input_files || [];
      handleInputChange('input_files', [...existingFiles, newFile]);
      setManualPath('');
      setShowManualPathInput(false);
    }
  };

  const toggleTool = (tool: string) => {
    const currentTools = agent.tools || [];
    const newTools = currentTools.includes(tool)
      ? currentTools.filter(t => t !== tool)
      : [...currentTools, tool];
    handleInputChange('tools', newTools);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div className="border border-blue-200 rounded-xl bg-gradient-to-br from-white to-blue-50 shadow-md hover:shadow-lg transition-shadow" style={{ padding: '3%' }}>
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
            <span className="text-blue-600 font-bold text-lg">•</span>
          </div>
          <h3 className="text-lg font-bold text-blue-700">Base Agent</h3>
        </div>
        <button
          onClick={onDelete}
          className="text-red-400 hover:text-red-600 p-2 rounded-lg hover:bg-red-50 transition-colors"
          title="Delete Agent"
        >
          <Trash2 size={18} />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-6" style={{ padding: '3%' }}>
        <div>
          <label className="block text-sm font-semibold text-gray-800 mb-2">
            Agent Name *
          </label>
          <textarea
            value={agent.name}
            onChange={(e) => handleInputChange('name', e.target.value)}
            className="min-w-32 max-w-md p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white shadow-sm resize-none overflow-hidden"
            style={{ 
              width: `${Math.max(12, Math.min(40, (agent.name?.length || 12) + 4))}ch`,
              minHeight: '3rem',
              height: `${Math.max(3, (agent.name || '').split('\n').length * 1.5)}rem`
            }}
            placeholder="Enter agent name"
            required
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement;
              target.style.height = 'auto';
              target.style.height = `${Math.max(48, target.scrollHeight)}px`;
            }}
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-800 mb-2">
            Model
          </label>
          <select
            value={agent.model}
            onChange={(e) => handleInputChange('model', e.target.value)}
            className="max-w-md p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white shadow-sm"
          >
            <option value="gpt-4o">gpt-4o</option>
            <option value="gpt-4.1">gpt-4.1</option>
          </select>
        </div>

        <div className="col-span-2">
          <label className="block text-sm font-semibold text-gray-800 mb-2">
            Description *
          </label>
          <textarea
            value={agent.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white shadow-sm resize-none overflow-hidden"
            style={{ 
              width: '70%',
              minHeight: '3rem',
              height: `${Math.max(3, (agent.description || '').split('\n').length * 1.5)}rem`
            }}
            placeholder="Brief description of the agent"
            required
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement;
              target.style.height = 'auto';
              target.style.height = `${Math.max(48, target.scrollHeight)}px`;
            }}
          />
        </div>

        <div className="col-span-2">
          <label className="block text-sm font-semibold text-gray-800 mb-2">
            Instruction *
          </label>
          <AutoResizeTextarea
            value={agent.instruction}
            onChange={(value) => handleInputChange('instruction', value)}
            placeholder="Enter the prompt/instruction for this agent"
            className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white shadow-sm font-mono text-sm"
            style={{ width: '70%' }}
            minRows={3}
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-800 mb-2">
            Output Key
          </label>
          <textarea
            value={agent.output_key || ''}
            onChange={(e) => handleInputChange('output_key', e.target.value)}
            className="min-w-32 max-w-md p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white shadow-sm resize-none overflow-hidden"
            style={{ 
              width: `${Math.max(12, Math.min(40, ((agent.output_key?.length || agent.name?.length) || 12) + 4))}ch`,
              minHeight: '3rem',
              height: `${Math.max(3, (agent.output_key || '').split('\n').length * 1.5)}rem`
            }}
            placeholder={`Default: ${agent.name}`}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement;
              target.style.height = 'auto';
              target.style.height = `${Math.max(48, target.scrollHeight)}px`;
            }}
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-800 mb-2">
            Tools
          </label>
          <div className="space-y-3 bg-gray-50 rounded-lg" style={{ padding: '3%' }}>
            {availableTools.map(tool => (
              <label key={tool} className="flex items-center cursor-pointer hover:bg-white rounded p-2 transition-colors">
                <input
                  type="checkbox"
                  checked={(agent.tools || []).includes(tool)}
                  onChange={() => toggleTool(tool)}
                  className="mr-3 w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700">{tool}</span>
              </label>
            ))}
            {availableTools.length === 0 && (
              <p className="text-sm text-gray-500 italic">No tools available</p>
            )}
          </div>
        </div>

        <div className="col-span-2">
          <label className="block text-sm font-semibold text-gray-800 mb-2">
            Input Files
          </label>
          <div className="space-y-2">
            <div className="flex gap-3">
              <button
                onClick={handleFileSelect}
                className="flex items-center gap-2 px-4 py-2 border border-blue-300 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 hover:border-blue-400 transition-colors font-medium"
              >
                <Upload size={16} />
                Upload & Read Files
              </button>
              <button
                onClick={() => setShowManualPathInput(!showManualPathInput)}
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-colors font-medium"
              >
                <FolderOpen size={16} />
                Add Path
              </button>
            </div>
            
            {showManualPathInput && (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={manualPath}
                  onChange={(e) => setManualPath(e.target.value)}
                  placeholder="Enter absolute file path (e.g., /Users/user/project/file.py)"
                  className="flex-1 p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  onKeyDown={(e) => e.key === 'Enter' && handleManualPathAdd()}
                />
                <button
                  onClick={handleManualPathAdd}
                  className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Add
                </button>
                <button
                  onClick={() => {
                    setShowManualPathInput(false);
                    setManualPath('');
                  }}
                  className="px-3 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            )}
            
            {(agent.input_files || []).map((file, index) => (
              <div key={index} className="flex items-start gap-3 bg-gray-50 rounded-lg border" style={{ padding: '3%' }}>
                <File size={18} className="text-gray-500 mt-1" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-semibold text-gray-800">
                      {file.original_name || file.input_path.split('/').pop()}
                    </span>
                    <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                      {file.input_type}
                    </span>
                    {file.is_binary && (
                      <span className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded">
                        binary
                      </span>
                    )}
                    {file.file_size && (
                      <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                        {formatFileSize(file.file_size)}
                      </span>
                    )}
                  </div>
                  <div className="text-xs font-mono text-gray-600 break-all">
                    {file.input_path}
                  </div>
                  {file.file_content && file.file_content.length > 0 && (
                    <div className="text-xs text-gray-500 mt-1">
                      Content loaded ({Math.round(file.file_content.length / 1024)}KB base64)
                    </div>
                  )}
                  {(!file.file_content || file.file_content.length === 0) && (
                    <div className="text-xs text-orange-600 mt-1">
                      Referenced file - content not loaded
                    </div>
                  )}
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="text-red-400 hover:text-red-600 p-2 rounded-lg hover:bg-red-50 transition-colors flex-shrink-0"
                  title="Remove file"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
            
            {(agent.input_files || []).length === 0 && (
              <p className="text-sm text-gray-500 italic">No input files added</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};