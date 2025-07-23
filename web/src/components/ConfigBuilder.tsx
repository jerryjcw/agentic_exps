import React, { useState, useEffect } from 'react';
import type { WorkflowConfig, AgentType } from '../types';
import { AgentList } from './AgentList';
import { AutoResizeTextarea } from './AutoResizeTextarea';
import { convertToWorkflowRequest, loadAvailableTools } from '../utils/configConverter';
import { uploadFilesToServer, createFileManifest } from '../utils/fileStorage';
import { Download, Play, Settings } from 'lucide-react';

interface ConfigBuilderProps {
  config: WorkflowConfig;
  onChange: (config: WorkflowConfig) => void;
}

export const ConfigBuilder: React.FC<ConfigBuilderProps> = ({
  config,
  onChange
}) => {
  const [availableTools, setAvailableTools] = useState<string[]>([]);
  const [showJsonOutput, setShowJsonOutput] = useState(false);
  const [jsonConfig, setJsonConfig] = useState<string>('');

  useEffect(() => {
    loadAvailableTools().then(setAvailableTools);
  }, []);


  const handleSystemPromptChange = (systemPrompt: string) => {
    onChange({ ...config, systemPrompt });
  };

  const handleAgentsChange = (agents: AgentType[]) => {
    onChange({ ...config, agents });
  };

  const handleConvertToConfig = async () => {
    try {
      // First, collect all files from all agents
      const allFiles: any[] = [];
      const extractFiles = (agents: AgentType[]) => {
        agents.forEach(agent => {
          if (agent.class === 'Agent' && (agent as any).input_files) {
            allFiles.push(...(agent as any).input_files);
          } else if (agent.class !== 'Agent' && (agent as any).sub_agents) {
            extractFiles((agent as any).sub_agents);
          }
        });
      };
      
      extractFiles(config.agents);
      
      // Upload files to server/storage if any exist
      if (allFiles.length > 0) {
        console.log(`📂 Processing ${allFiles.length} files...`);
        await uploadFilesToServer(allFiles);
        
        // Create file manifest
        const manifest = createFileManifest(allFiles);
        console.log('📋 File Manifest:', manifest);
      }
      
      console.log('🔍 Converting config with agents:', config.agents.length);
      console.log('🔍 Total files to process:', allFiles.length);
      
      const workflowRequest = convertToWorkflowRequest(config);
      console.log('✅ Config converted successfully');
      
      const formattedJson = JSON.stringify(workflowRequest, null, 2);
      console.log('✅ JSON serialization successful');
      setJsonConfig(formattedJson);
      setShowJsonOutput(true);
      
      // Success - no dialog needed, user can see the generated JSON
    } catch (error) {
      console.error('Error converting config:', error);
      alert('Error converting configuration. Please check that all required fields are filled.');
    }
  };

  const handleDownloadConfig = () => {
    if (!jsonConfig) {
      handleConvertToConfig();
      return;
    }

    const blob = new Blob([jsonConfig], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `workflow-config-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleExecuteWorkflow = async () => {
    if (!jsonConfig) {
      handleConvertToConfig();
      if (!jsonConfig) return;
    }

    try {
      // This would call the actual API endpoint
      const response = await fetch('/api/workflow/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonConfig
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Workflow executed successfully! Status: ${result.status}`);
      } else {
        alert('Failed to execute workflow. Please check the server connection.');
      }
    } catch (error) {
      console.error('Error executing workflow:', error);
      alert('Error executing workflow. Server may be unavailable.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-8">
      <div className="w-full max-w-none mx-auto px-6 space-y-8" style={{ maxWidth: '70vw' }}>
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-3">
              Agent Workflow Builder
            </h1>
            <p className="text-gray-600 text-lg">
              Design and orchestrate complex AI agent workflows with ease
            </p>
          </div>
          
          <div className="mb-8">
            <label className="block text-sm font-semibold text-gray-800 mb-3">
              🎯 System Prompt
            </label>
            <AutoResizeTextarea
              value={config.systemPrompt}
              onChange={handleSystemPromptChange}
              placeholder="Enter the system prompt to orchestrate this workflow..."
              className="w-full p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-50 font-mono text-sm leading-relaxed"
              minRows={3}
            />
            <p className="text-sm text-gray-500 mt-2 flex items-center gap-2">
              <Settings size={14} />
              This will be used as the template_content in the generated configuration.
            </p>
          </div>

          <div className="mb-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-semibold text-gray-800 flex items-center gap-3">
                🔧 Workflow Agents
              </h2>
              <div className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                {config.agents.length} root agent{config.agents.length !== 1 ? 's' : ''}
              </div>
            </div>
            
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6 mb-6">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Settings className="text-blue-600" size={16} />
                </div>
                <div className="text-sm text-blue-900">
                  <p className="font-semibold mb-3">Root Level Agents</p>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="bg-white/70 rounded-lg p-3 border border-green-200">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-green-600 font-bold text-lg">→</span>
                        <span className="font-medium text-green-700">SequentialAgent</span>
                      </div>
                      <p className="text-xs text-green-600">Execute in sequence</p>
                    </div>
                    <div className="bg-white/70 rounded-lg p-3 border border-orange-200">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-orange-600 font-bold text-lg">↻</span>
                        <span className="font-medium text-orange-700">LoopAgent</span>
                      </div>
                      <p className="text-xs text-orange-600">Execute with iterations</p>
                    </div>
                    <div className="bg-white/70 rounded-lg p-3 border border-purple-200">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-purple-600 font-bold text-lg">‖</span>
                        <span className="font-medium text-purple-700">ParallelAgent</span>
                      </div>
                      <p className="text-xs text-purple-600">Execute in parallel</p>
                    </div>
                  </div>
                  <p className="mt-3 text-xs text-blue-700 bg-blue-100/50 rounded p-2">
                    💡 Inside container agents, you can add any type including base Agents
                  </p>
                </div>
              </div>
            </div>

            <AgentList
              agents={config.agents}
              onChange={handleAgentsChange}
              availableTools={availableTools}
              canAddContainerAgents={true}
            />
          </div>

          <div className="flex flex-wrap gap-4 pt-6 border-t border-gray-200">
            <button
              onClick={handleConvertToConfig}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-700 hover:to-blue-800 transition-all duration-200 shadow-lg hover:shadow-xl font-medium"
            >
              <Settings size={18} />
              Convert to Config
            </button>
            
            <button
              onClick={handleDownloadConfig}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-xl hover:from-green-700 hover:to-green-800 transition-all duration-200 shadow-lg hover:shadow-xl font-medium"
            >
              <Download size={18} />
              Download JSON
            </button>
            
            <button
              onClick={handleExecuteWorkflow}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-xl hover:from-purple-700 hover:to-purple-800 transition-all duration-200 shadow-lg hover:shadow-xl font-medium"
            >
              <Play size={18} />
              Execute Workflow
            </button>
          </div>
        </div>

        {showJsonOutput && (
          <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-semibold text-gray-800 flex items-center gap-3">
                📄 Generated Configuration
              </h2>
              <button
                onClick={() => setShowJsonOutput(false)}
                className="text-gray-400 hover:text-gray-600 p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                ✕
              </button>
            </div>
            
            <div className="bg-gray-50 rounded-xl p-6 max-h-96 overflow-auto border border-gray-200">
              <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono leading-relaxed">
                {jsonConfig}
              </pre>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => navigator.clipboard.writeText(jsonConfig)}
                className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
              >
                📋 Copy to Clipboard
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};