import React from 'react';
import type { SequentialAgent, LoopAgent, ParallelAgent, AgentType } from '../types';
import { Trash2, ChevronDown, ChevronRight } from 'lucide-react';
import { AgentList } from './AgentList';

interface ContainerAgentFormProps {
  agent: SequentialAgent | LoopAgent | ParallelAgent;
  onChange: (agent: SequentialAgent | LoopAgent | ParallelAgent) => void;
  onDelete: () => void;
  availableTools: string[];
  isExpanded: boolean;
  onToggleExpand: () => void;
}

export const ContainerAgentForm: React.FC<ContainerAgentFormProps> = ({
  agent,
  onChange,
  onDelete,
  availableTools,
  isExpanded,
  onToggleExpand
}) => {
  const handleInputChange = (field: string, value: any) => {
    onChange({ ...agent, [field]: value });
  };

  const handleSubAgentsChange = (subAgents: AgentType[]) => {
    onChange({ ...agent, sub_agents: subAgents });
  };

  const getAgentTypeColor = () => {
    switch (agent.class) {
      case 'SequentialAgent': return 'text-green-600 border-green-200 bg-green-50';
      case 'LoopAgent': return 'text-orange-600 border-orange-200 bg-orange-50';
      case 'ParallelAgent': return 'text-purple-600 border-purple-200 bg-purple-50';
      default: return 'text-gray-600 border-gray-200 bg-gray-50';
    }
  };

  const getAgentIcon = () => {
    switch (agent.class) {
      case 'SequentialAgent': return '→';
      case 'LoopAgent': return '↻';
      case 'ParallelAgent': return '‖';
      default: return '•';
    }
  };

  return (
    <div className={`border rounded-lg shadow-sm ${getAgentTypeColor()}`} style={{ padding: '3%' }}>
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-2">
          <button
            onClick={onToggleExpand}
            className="p-1 hover:bg-white/50 rounded"
          >
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <span className="text-xl">{getAgentIcon()}</span>
            {agent.class}
          </h3>
        </div>
        <button
          onClick={onDelete}
          className="text-red-500 hover:text-red-700 p-1"
          title={`Delete ${agent.class}`}
        >
          <Trash2 size={16} />
        </button>
      </div>

      {isExpanded && (
        <>
          <div className="grid grid-cols-1 gap-4 mb-4" style={{ padding: '3%' }}>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name *
              </label>
              <textarea
                value={agent.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className="min-w-32 max-w-md p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white resize-none overflow-hidden"
                style={{ 
                  width: `${Math.max(12, Math.min(40, (agent.name?.length || 12) + 4))}ch`,
                  minHeight: '2.5rem',
                  height: `${Math.max(2.5, (agent.name || '').split('\n').length * 1.5)}rem`
                }}
                placeholder="Enter agent name"
                required
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = 'auto';
                  target.style.height = `${Math.max(40, target.scrollHeight)}px`;
                }}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description *
              </label>
              <textarea
                value={agent.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                className="p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white resize-none overflow-hidden"
                style={{ 
                  width: '70%',
                  minHeight: '2.5rem',
                  height: `${Math.max(2.5, (agent.description || '').split('\n').length * 1.5)}rem`
                }}
                placeholder="Brief description of this agent"
                required
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = 'auto';
                  target.style.height = `${Math.max(40, target.scrollHeight)}px`;
                }}
              />
            </div>

            {agent.class === 'LoopAgent' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Iterations *
                </label>
                <input
                  type="number"
                  value={agent.max_iterations}
                  onChange={(e) => handleInputChange('max_iterations', parseInt(e.target.value))}
                  className="min-w-20 max-w-32 p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                  style={{ width: `${Math.max(4, Math.min(10, String(agent.max_iterations || 1).length + 2))}ch` }}
                  min="1"
                  required
                />
              </div>
            )}
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <h4 className="text-md font-medium text-gray-700">Sub Agents</h4>
              <div className="text-sm text-gray-500">
                {agent.sub_agents.length} agent{agent.sub_agents.length !== 1 ? 's' : ''}
              </div>
            </div>
            <AgentList
              agents={agent.sub_agents}
              onChange={handleSubAgentsChange}
              availableTools={availableTools}
              canAddContainerAgents={true}
            />
          </div>
        </>
      )}

      {!isExpanded && (
        <div className="text-sm text-gray-600">
          <div>{agent.name} - {agent.description}</div>
          {agent.class === 'LoopAgent' && (
            <div className="text-xs">Max iterations: {agent.max_iterations}</div>
          )}
          <div className="text-xs">
            {agent.sub_agents.length} sub-agent{agent.sub_agents.length !== 1 ? 's' : ''}
          </div>
        </div>
      )}
    </div>
  );
};