import type { WorkflowConfig, AgentType, Agent, WorkflowRequest, JobConfig, TemplateConfig } from '../types';

export const convertToJSON = (config: WorkflowConfig): WorkflowRequest => {
  return convertToWorkflowRequest(config);
};

export const convertToWorkflowRequest = (config: WorkflowConfig): WorkflowRequest => {
  // Create the main agent config (wrapper for root agents)
  const mainAgentConfig: AgentType = {
    id: 'main',
    name: 'MainWorkflow',
    class: 'SequentialAgent',
    module: 'google.adk.agents',
    description: 'Main workflow containing all agents',
    sub_agents: config.agents
  };

  // Create job config with defaults
  const jobConfig: JobConfig = {
    job_name: 'WebUIWorkflow',
    job_description: 'Workflow created from Web UI',
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

  return {
    job_config: jobConfig,
    agent_config: cleanAgentForExport(mainAgentConfig),
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
        const apiFiles = agentTyped.input_files.map(file => ({
          input_path: file.input_path,
          input_type: file.input_type,
          target_agent: file.target_agent
        }));
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

const cleanAgentForExport = (agent: AgentType): any => {
  const cleaned: any = {
    name: agent.name,
    class: agent.class,
    module: agent.module,
    description: agent.description
  };

  if (agent.class === 'Agent') {
    const agentTyped = agent as Agent;
    cleaned.model = `openai/${agentTyped.model}`;
    cleaned.instruction = agentTyped.instruction;
    cleaned.output_key = agentTyped.output_key || agentTyped.name;
    
    if (agentTyped.tools && agentTyped.tools.length > 0) {
      cleaned.tools = agentTyped.tools;
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
      cleaned.sub_agents = containerAgent.sub_agents.map(cleanAgentForExport);
    }
  }

  return cleaned;
};

export const loadAvailableTools = async (): Promise<string[]> => {
  // This would normally fetch from the Python registry
  // For now, return the tools we know exist based on the registry file
  return [
    'get_current_time_tool',
    'get_temperature_tool', 
    'google_search_tool',
    'get_earnings_report_tool',
    'get_company_news_tool'
  ];
};