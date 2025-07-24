import type { WorkflowConfig, AgentType, Agent, WorkflowRequest, JobConfig, TemplateConfig, ToolInfo } from '../types';

export const convertToJSON = async (config: WorkflowConfig): Promise<WorkflowRequest> => {
  return await convertToWorkflowRequest(config);
};

export const convertToWorkflowRequest = async (config: WorkflowConfig): Promise<WorkflowRequest> => {

  // Get first agent info for job naming
  const firstAgent = config.agents[0];
  const defaultJobName = firstAgent ? firstAgent.name || 'WebUIWorkflow' : 'WebUIWorkflow';
  const defaultJobDescription = firstAgent ? firstAgent.description || 'Workflow created from Web UI' : 'Workflow created from Web UI';

  // Create job config with defaults
  const jobConfig: JobConfig = {
    job_name: defaultJobName,
    job_description: defaultJobDescription,
    job_type: 'workflow_execution',
    runner_config: {
      app_name: 'WebUIWorkflow',
      session_config: {
        user_id: 'web_user',
        session_id: `session_${Date.now()}`
      }
    },
    input_config: {
      input_files: extractAllInputFiles(config.agents),
      preview_length: 500
    },
    output_config: {
      output_directory: 'output',
      output_format: ['txt', 'json'],
      file_naming: 'workflow_output_{timestamp}',
      timestamp_format: '%Y%m%d_%H%M%S',
      include_metadata: true
    },
    execution_config: {
      track_execution_steps: true,
      display_progress: true,
      log_level: 'INFO',
      error_handling: 'continue_on_agent_failure',
      timeout_seconds: 300
    },
    report_config: {
      include_final_responses: true,
      include_code_preview: true,
      include_execution_summary: true,
      display_results_summary: true
    }
  };

  // Create template config
  const templateConfig: TemplateConfig = {
    template_name: 'Web UI Workflow Template',
    template_description: 'Template for workflows created through the web UI',
    template_version: '1.0',
    template_engine: 'jinja2',
    template_content: config.systemPrompt || 'Please execute the following workflow.',
    template_variables: {
      language: {
        description: 'Programming language',
        type: 'string',
        default: 'Python'
      },
      file_name: {
        description: 'Array of file names being analyzed',
        type: 'array',
        default: ['workflow_file']
      },
      file_type: {
        description: 'Array of file types',
        type: 'array',
        default: ['text']
      },
      file_content: {
        description: 'Array of file contents',
        type: 'array',
        default: ['']
      }
    }
  };

  // Handle agent config based on number of root agents
  let agentConfig: any;
  
  if (config.agents.length === 1) {
    // Single root agent - use it directly
    agentConfig = await cleanAgentForExport(config.agents[0], config.useInternalModels);
  } else if (config.agents.length > 1) {
    // Multiple root agents - create minimal sequential wrapper
    agentConfig = {
      name: 'RootWorkflow',
      class: 'SequentialAgent',
      module: 'google.adk.agents',
      description: 'Root workflow',
      sub_agents: await Promise.all(config.agents.map(agent => cleanAgentForExport(agent, config.useInternalModels)))
    };
  } else {
    // No agents - create empty sequential agent
    agentConfig = {
      name: 'EmptyWorkflow',
      class: 'SequentialAgent',
      module: 'google.adk.agents',
      description: 'Empty workflow',
      sub_agents: []
    };
  }
  
  return {
    job_config: jobConfig,
    agent_config: agentConfig,
    template_config: templateConfig
  };
};

const extractAllInputFiles = (agents: AgentType[]): any[] => {
  const allFiles: any[] = [];
  
  const extractFromAgent = (agent: AgentType) => {
    if (agent.class === 'Agent') {
      const agentTyped = agent as Agent;
      if (agentTyped.input_files) {
        // Convert our InputFile format to the expected API format
        const apiFiles = agentTyped.input_files.map(file => {
          // Use the original filename without timestamp prefix
          const uploadDirPattern = /\/uploaded_files\/\d+_/;
          const cleanPath = file.input_path.replace(uploadDirPattern, '/uploaded_files/');
          
          return {
            input_path: cleanPath,
            input_type: file.input_type,
            target_agent: file.target_agent
          };
        });
        allFiles.push(...apiFiles);
      }
    } else {
      // Container agents
      const containerAgent = agent as any;
      if (containerAgent.sub_agents) {
        containerAgent.sub_agents.forEach(extractFromAgent);
      }
    }
  };

  agents.forEach(extractFromAgent);
  return allFiles;
};

const cleanAgentForExport = async (agent: AgentType, useInternalModels = false): Promise<any> => {
  const cleaned: any = {
    name: agent.name,
    class: agent.class,
    module: agent.module,
    description: agent.description
  };

  if (agent.class === 'Agent') {
    const agentTyped = agent as Agent;
    const modelPrefix = useInternalModels ? 'internal' : 'openai';
    cleaned.model = `${modelPrefix}/${agentTyped.model}`;
    cleaned.instruction = agentTyped.instruction;
    cleaned.output_key = agentTyped.output_key || agentTyped.name;
    
    if (agentTyped.tools && agentTyped.tools.length > 0) {
      // Load tool information from database to get full tool details
      try {
        const toolsInfo = await loadToolsInfo();
        const toolsMap = new Map(toolsInfo.map(t => [t.function_name, t]));
        
        cleaned.tools = agentTyped.tools.map(toolName => {
          const toolInfo = toolsMap.get(toolName);
          if (toolInfo) {
            return {
              class: toolInfo.class,
              module: toolInfo.module,
              function_name: toolInfo.function_name,
              function_module: toolInfo.function_module
            };
          } else {
            // Fallback if tool not found in database
            return {
              class: 'FunctionTool',
              module: 'google.adk.tools',
              function_name: toolName,
              function_module: `tools.gadk.${toolName.replace('_tool', '')}`
            };
          }
        });
      } catch (error) {
        console.error('Error loading tool info for export:', error);
        // Fallback to simple tool format
        cleaned.tools = agentTyped.tools.map(toolName => ({
          class: 'FunctionTool',
          module: 'google.adk.tools',
          function_name: toolName,
          function_module: `tools.gadk.${toolName.replace('_tool', '')}`
        }));
      }
    } else {
      cleaned.tools = [];
    }
  } else {
    // Container agents
    const containerAgent = agent as any;
    
    if (agent.class === 'LoopAgent') {
      cleaned.max_iterations = containerAgent.max_iterations;
    }
    
    if (containerAgent.sub_agents) {
      cleaned.sub_agents = await Promise.all(
        containerAgent.sub_agents.map((subAgent: AgentType) => cleanAgentForExport(subAgent, useInternalModels))
      );
    }
  }

  return cleaned;
};

// Load full tool information from database
export const loadToolsInfo = async (): Promise<ToolInfo[]> => {
  try {
    const response = await fetch('http://localhost:3001/api/tools');
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to load tools from database:', error);
    return [];
  }
};

export const loadAvailableTools = async (): Promise<string[]> => {
  try {
    const tools = await loadToolsInfo();
    return tools.map(tool => tool.function_name);
  } catch (error) {
    console.error('Failed to load tools from database:', error);
    // Fallback to hardcoded tools if API fails
    return [
      'get_current_time_tool',
      'get_temperature_tool', 
      'google_search_tool',
      'get_earnings_report_tool',
      'get_company_news_tool'
    ];
  }
};