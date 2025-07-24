import React, { useState, useEffect } from 'react';
import type { WorkflowConfig, AgentType } from '../types';
import { AgentList } from './AgentList';
import { AutoResizeTextarea } from './AutoResizeTextarea';
import { loadAvailableTools } from '../utils/configConverter';
import { Settings, Users, Sparkles, Code } from 'lucide-react';

interface ConfigBuilderProps {
  config: WorkflowConfig;
  onChange: (config: WorkflowConfig) => void;
  jsonConfig?: string;
}

export const ConfigBuilder: React.FC<ConfigBuilderProps> = ({
  config,
  onChange,
  jsonConfig
}) => {
  const [availableTools, setAvailableTools] = useState<string[]>([]);
  const [useInternalModels, setUseInternalModels] = useState<boolean>(config.useInternalModels || false);

  const handleInternalModelsChange = (value: boolean) => {
    setUseInternalModels(value);
    onChange({ ...config, useInternalModels: value });
  };

  useEffect(() => {
    loadAvailableTools().then(setAvailableTools);
  }, []);

  const handleSystemPromptChange = (systemPrompt: string) => {
    onChange({ ...config, systemPrompt });
  };

  const handleAgentsChange = (agents: AgentType[]) => {
    onChange({ ...config, agents });
  };

  return (
    <div className="py-8 px-6">
      <div className="w-3/5 mx-auto space-y-8">
        {/* Internal Models Switch */}
        <div className="bg-white rounded-2xl shadow-lg" style={{ padding: '3%' }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-blue-500 rounded-lg flex items-center justify-center mr-3">
                <Settings className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Internal Models</h2>
                <p className="text-sm text-gray-500">Use internal model endpoints instead of OpenAI</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => handleInternalModelsChange(!useInternalModels)}
                className={`px-4 py-2 rounded-lg border font-medium transition-colors ${
                  useInternalModels 
                    ? 'bg-blue-600 text-white border-blue-600 hover:bg-blue-700' 
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                {useInternalModels ? 'Internal Models: ON' : 'Internal Models: OFF'}
              </button>
              <div className="text-sm text-gray-500">
                Current: <span className="font-medium">{useInternalModels ? 'internal/' : 'openai/'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* System Prompt Card */}
        <div className="bg-white rounded-2xl shadow-lg" style={{ padding: '3%' }}>
          <div className="flex items-center mb-4">
            <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center mr-3">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">System Prompt</h2>
              <p className="text-sm text-gray-500">Define the orchestration instructions</p>
            </div>
          </div>
          
          <AutoResizeTextarea
            value={config.systemPrompt}
            onChange={handleSystemPromptChange}
            placeholder="Enter the system prompt to orchestrate this workflow..."
            className="w-full p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-50 font-mono text-sm leading-relaxed transition-all duration-200 hover:border-gray-400"
            minRows={3}
          />
          <div className="flex items-center mt-3 text-sm text-gray-500">
            <Settings className="w-4 h-4 mr-2" />
            This will be used as the template_content in the generated configuration
          </div>
        </div>

        {/* Workflow Agents Card */}
        <div className="bg-white rounded-2xl shadow-lg" style={{ padding: '3%' }}>
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center mr-3">
                <Users className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Workflow Agents</h2>
                <p className="text-sm text-gray-500">Configure your agent hierarchy</p>
              </div>
            </div>
            <div className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
              {config.agents.length} root agent{config.agents.length !== 1 ? 's' : ''}
            </div>
          </div>
          
          {/* Root Level Agents Guide - Horizontal Labels */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl mb-6" style={{ padding: '3%' }}>
            <div className="flex justify-center items-center">
              <div className="text-center">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <span className="text-green-600 font-bold text-2xl">→</span>
                  <span className="font-semibold text-green-700">SequentialAgent</span>
                </div>
                <p className="text-xs text-green-600">Execute in sequence</p>
              </div>
              
              <div className="w-[5vw]"></div>
              
              <div className="text-center">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <span className="text-orange-600 font-bold text-2xl">↻</span>
                  <span className="font-semibold text-orange-700">LoopAgent</span>
                </div>
                <p className="text-xs text-orange-600">Repeat with iterations</p>
              </div>
              
              <div className="w-[5vw]"></div>
              
              <div className="text-center">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <span className="text-purple-600 font-bold text-2xl">‖</span>
                  <span className="font-semibold text-purple-700">ParallelAgent</span>
                </div>
                <p className="text-xs text-purple-600">Execute concurrently</p>
              </div>
              
              <div className="w-[5vw]"></div>
              
              <div className="text-center">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <span className="text-blue-600 font-bold text-2xl">•</span>
                  <span className="font-semibold text-blue-700">Agent</span>
                </div>
                <p className="text-xs text-blue-600">Base agent</p>
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

        {/* JSON Configuration Display */}
        {jsonConfig && (
          <div className="bg-white rounded-2xl shadow-lg" style={{ padding: '3%' }}>
            <div className="flex items-center mb-4">
              <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg flex items-center justify-center mr-3">
                <Code className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Generated JSON Configuration</h2>
                <p className="text-sm text-gray-500">Your workflow configuration in JSON format</p>
              </div>
            </div>
            
            <div className="bg-gray-50 rounded-xl border max-h-96 overflow-y-auto" style={{ padding: '3%' }}>
              <pre className="text-sm text-gray-800 whitespace-pre-wrap overflow-x-auto font-mono leading-relaxed">
                {jsonConfig}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};