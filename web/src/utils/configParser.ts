import type { WorkflowConfig, AgentType, WorkflowRequest, InputFile } from '../types';

/**
 * Convert a JSON workflow request back to the UI's WorkflowConfig format
 */
export const parseWorkflowRequest = (jsonData: WorkflowRequest): WorkflowConfig => {
  // Extract input files from job_config
  const inputFiles = jsonData.job_config?.input_config?.input_files || [];
  
  // The main agent config contains the root agents as sub_agents
  // If it's a wrapper agent (MainWorkflow), extract its sub_agents
  let rootAgents: AgentType[];
  
  if (jsonData.agent_config.name === 'MainWorkflow' && (jsonData.agent_config as any).sub_agents) {
    // Extract sub_agents as root agents
    rootAgents = (jsonData.agent_config as any).sub_agents.map((agent: any) => 
      parseAgentConfig(agent, inputFiles)
    );
  } else {
    // Single root agent
    rootAgents = [parseAgentConfig(jsonData.agent_config, inputFiles)];
  }

  return {
    systemPrompt: jsonData.template_config.template_content,
    agents: rootAgents
  };
};

/**
 * Parse a single agent configuration from JSON format
 */
export const parseAgentConfig = (agentData: any, allInputFiles: any[] = []): AgentType => {
  const baseAgent = {
    id: `${agentData.name}_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`,
    name: agentData.name,
    module: agentData.module || 'google.adk.agents',
    description: agentData.description || '',
  };

  switch (agentData.class) {
    case 'Agent':
      // Find input files that target this agent
      const agentInputFiles = allInputFiles
        .filter(file => file.target_agent && file.target_agent.includes(agentData.name))
        .map(file => convertToUIInputFile(file));

      return {
        ...baseAgent,
        class: 'Agent' as const,
        model: (agentData.model?.includes('gpt-4.1') ? 'gpt-4.1' : 'gpt-4o') as 'gpt-4o' | 'gpt-4.1',
        instruction: agentData.instruction || '',
        output_key: agentData.output_key || agentData.name,
        input_files: agentInputFiles,
        tools: agentData.tools || []
      };

    case 'SequentialAgent':
      return {
        ...baseAgent,
        class: 'SequentialAgent' as const,
        sub_agents: (agentData.sub_agents || []).map((agent: any) => parseAgentConfig(agent, allInputFiles))
      };

    case 'LoopAgent':
      return {
        ...baseAgent,
        class: 'LoopAgent' as const,
        max_iterations: agentData.max_iterations || 1,
        sub_agents: (agentData.sub_agents || []).map((agent: any) => parseAgentConfig(agent, allInputFiles))
      };

    case 'ParallelAgent':
      return {
        ...baseAgent,
        class: 'ParallelAgent' as const,
        sub_agents: (agentData.sub_agents || []).map((agent: any) => parseAgentConfig(agent, allInputFiles))
      };

    default:
      throw new Error(`Unknown agent class: ${agentData.class}`);
  }
};

/**
 * Convert API input file format to UI input file format
 */
const convertToUIInputFile = (apiFile: any): InputFile => {
  return {
    input_path: apiFile.input_path,
    input_type: apiFile.input_type,
    target_agent: apiFile.target_agent,
    file_content: '', // Content not stored in the JSON format
    original_name: apiFile.input_path.split('/').pop() || apiFile.input_path,
    file_size: undefined, // Size not available in stored config
    is_binary: undefined // Binary flag not available in stored config
  };
};

/**
 * Parse a configuration JSON string back to WorkflowConfig
 */
export const parseConfigurationData = (configData: string): WorkflowConfig => {
  try {
    const jsonData = JSON.parse(configData);
    return parseWorkflowRequest(jsonData);
  } catch (error) {
    throw new Error(`Failed to parse configuration data: ${error instanceof Error ? error.message : 'Invalid JSON'}`);
  }
};