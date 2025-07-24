import React, { useState } from 'react';
import type { AgentType, Agent, SequentialAgent, LoopAgent, ParallelAgent } from '../types';
import { Plus, ChevronDown } from 'lucide-react';
import { AgentForm } from './AgentForm';
import { ContainerAgentForm } from './ContainerAgentForm';
import { v4 as uuidv4 } from 'uuid';

interface AgentListProps {
  agents: AgentType[];
  onChange: (agents: AgentType[]) => void;
  availableTools: string[];
  canAddContainerAgents: boolean;
}

export const AgentList: React.FC<AgentListProps> = ({
  agents,
  onChange,
  availableTools,
  canAddContainerAgents
}) => {
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set());
  const [showAddMenu, setShowAddMenu] = useState(false);

  // Auto-expand container agents when they are loaded/created
  React.useEffect(() => {
    const newExpanded = new Set<string>();
    const expandContainerAgents = (agentList: AgentType[]) => {
      agentList.forEach(agent => {
        if (agent.class !== 'Agent') {
          newExpanded.add(agent.id);
          // Recursively expand nested container agents
          if ('sub_agents' in agent && agent.sub_agents) {
            expandContainerAgents(agent.sub_agents);
          }
        }
      });
    };
    expandContainerAgents(agents);
    
    // Only update if there are new agents to expand
    if (newExpanded.size > 0) {
      setExpandedAgents(prev => new Set([...prev, ...newExpanded]));
    }
  }, [agents]);

  const toggleExpanded = (agentId: string) => {
    const newExpanded = new Set(expandedAgents);
    if (newExpanded.has(agentId)) {
      newExpanded.delete(agentId);
    } else {
      newExpanded.add(agentId);
    }
    setExpandedAgents(newExpanded);
  };

  const createNewAgent = (type: string) => {
    const baseAgent = {
      id: uuidv4(),
      module: 'google.adk.agents',
    };

    let newAgent: AgentType;

    switch (type) {
      case 'Agent':
        newAgent = {
          ...baseAgent,
          name: '',
          class: 'Agent' as const,
          model: 'gpt-4o' as const,
          instruction: '',
          description: '',
          tools: [],
          input_files: []
        };
        break;
      case 'SequentialAgent':
        newAgent = {
          ...baseAgent,
          name: '',
          class: 'SequentialAgent' as const,
          description: '',
          sub_agents: []
        };
        break;
      case 'LoopAgent':
        newAgent = {
          ...baseAgent,
          name: '',
          class: 'LoopAgent' as const,
          description: '',
          max_iterations: 1,
          sub_agents: []
        };
        break;
      case 'ParallelAgent':
        newAgent = {
          ...baseAgent,
          name: '',
          class: 'ParallelAgent' as const,
          description: '',
          sub_agents: []
        };
        break;
      default:
        return;
    }

    onChange([...agents, newAgent]);
    setShowAddMenu(false);
    
    // Auto-expand new container agents
    if (type !== 'Agent') {
      setExpandedAgents(prev => new Set([...prev, newAgent.id]));
    }
  };

  const updateAgent = (index: number, updatedAgent: AgentType) => {
    const newAgents = [...agents];
    newAgents[index] = updatedAgent;
    onChange(newAgents);
  };

  const deleteAgent = (index: number) => {
    const newAgents = agents.filter((_, i) => i !== index);
    onChange(newAgents);
  };

  return (
    <div className="space-y-4">
      {agents.map((agent, index) => (
        <div key={agent.id}>
          {agent.class === 'Agent' ? (
            <AgentForm
              agent={agent as Agent}
              onChange={(updatedAgent) => updateAgent(index, updatedAgent)}
              onDelete={() => deleteAgent(index)}
              availableTools={availableTools}
            />
          ) : (
            <ContainerAgentForm
              agent={agent as SequentialAgent | LoopAgent | ParallelAgent}
              onChange={(updatedAgent) => updateAgent(index, updatedAgent)}
              onDelete={() => deleteAgent(index)}
              availableTools={availableTools}
              isExpanded={expandedAgents.has(agent.id)}
              onToggleExpand={() => toggleExpanded(agent.id)}
            />
          )}
        </div>
      ))}

      <div className="relative">
        <button
          onClick={() => setShowAddMenu(!showAddMenu)}
          className="flex items-center gap-2 px-4 py-2 border border-dashed border-gray-300 rounded-lg hover:border-gray-400 hover:bg-gray-50 w-full justify-center min-h-[30px]"
        >
          <Plus size={16} />
          Add Agent
          <ChevronDown size={16} className={`transition-transform ${showAddMenu ? 'rotate-180' : ''}`} />
        </button>

        {showAddMenu && (
          <div className="absolute top-full left-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-xl z-50 w-[30%]">
            <div className="p-4">
              <button
                onClick={() => createNewAgent('Agent')}
                className="w-full text-left px-6 py-4 hover:bg-gray-100 rounded-lg flex items-center gap-4 min-h-[30px]"
              >
                <span className="text-blue-600 font-bold text-lg">•</span>
                <span className="font-medium">Agent</span>
              </button>
              
              {canAddContainerAgents && (
                <>
                  <button
                    onClick={() => createNewAgent('SequentialAgent')}
                    className="w-full text-left px-6 py-4 hover:bg-gray-100 rounded-lg flex items-center gap-4 min-h-[30px]"
                  >
                    <span className="text-green-600 font-bold text-lg">→</span>
                    <span className="font-medium">SequentialAgent</span>
                  </button>
                  
                  <button
                    onClick={() => createNewAgent('LoopAgent')}
                    className="w-full text-left px-6 py-4 hover:bg-gray-100 rounded-lg flex items-center gap-4 min-h-[30px]"
                  >
                    <span className="text-orange-600 font-bold text-lg">↻</span>
                    <span className="font-medium">LoopAgent</span>
                  </button>
                  
                  <button
                    onClick={() => createNewAgent('ParallelAgent')}
                    className="w-full text-left px-6 py-4 hover:bg-gray-100 rounded-lg flex items-center gap-4 min-h-[30px]"
                  >
                    <span className="text-purple-600 font-bold text-lg">‖</span>
                    <span className="font-medium">ParallelAgent</span>
                  </button>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};