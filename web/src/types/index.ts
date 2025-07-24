export interface InputFile {
  input_path: string;
  input_type: string;
  target_agent: string[];
  file_content?: string;
  original_name?: string;
  file_size?: number;
  is_binary?: boolean;
}

export interface ToolInfo {
  id: number;
  function_name: string;
  class: string;
  module: string;
  function_module: string;
  category?: string;
  description?: string;
  signature?: string;
  registry_module?: string;
  created_at: string;
  updated_at: string;
}

export interface Agent {
  id: string;
  name: string;
  class: 'Agent';
  module: string;
  model: 'gpt-4o' | 'gpt-4.1';
  instruction: string;
  description: string;
  output_key?: string;
  input_files?: InputFile[];
  tools?: string[];
}

export interface SequentialAgent {
  id: string;
  name: string;
  class: 'SequentialAgent';
  module: string;
  description: string;
  sub_agents: (Agent | SequentialAgent | LoopAgent | ParallelAgent)[];
}

export interface LoopAgent {
  id: string;
  name: string;
  class: 'LoopAgent';
  module: string;
  description: string;
  max_iterations: number;
  sub_agents: (Agent | SequentialAgent | LoopAgent | ParallelAgent)[];
}

export interface ParallelAgent {
  id: string;
  name: string;
  class: 'ParallelAgent';
  module: string;
  description: string;
  sub_agents: (Agent | SequentialAgent | LoopAgent | ParallelAgent)[];
}

export type AgentType = Agent | SequentialAgent | LoopAgent | ParallelAgent;

export interface WorkflowConfig {
  systemPrompt: string;
  agents: AgentType[];
  useInternalModels?: boolean;
}

export interface JobConfig {
  job_name: string;
  job_description: string;
  job_type: string;
  runner_config: {
    app_name: string;
    session_config: {
      user_id: string;
      session_id: string;
    };
  };
  input_config: {
    input_files: InputFile[];
    preview_length: number;
  };
  output_config: {
    output_directory: string;
    output_format: string[];
    file_naming: string;
    timestamp_format: string;
    include_metadata: boolean;
  };
  execution_config: {
    track_execution_steps: boolean;
    display_progress: boolean;
    log_level: string;
    error_handling: string;
    timeout_seconds: number;
  };
  report_config: {
    include_final_responses: boolean;
    include_code_preview: boolean;
    include_execution_summary: boolean;
    display_results_summary: boolean;
  };
}

export interface TemplateConfig {
  template_name: string;
  template_description: string;
  template_version: string;
  template_engine: string;
  template_content: string;
  template_variables: Record<string, any>;
}

export interface WorkflowRequest {
  job_config: JobConfig;
  agent_config: AgentType;
  template_config: TemplateConfig;
}

export type NavigationView = 'create' | 'save' | 'list' | 'execute';

export interface AppState {
  currentView: NavigationView;
  currentConfig: WorkflowConfig;
  selectedConfigId?: number;
}