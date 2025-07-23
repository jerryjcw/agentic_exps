// Test configuration parsing without TypeScript restrictions
const testConfigData = `{"job_config":{"job_name":"TestWorkflow","job_description":"Test workflow","job_type":"test","runner_config":{"app_name":"TestWorkflow","session_config":{"user_id":"test_user","session_id":"test_session"}},"input_config":{"input_files":[{"input_path":"/test/file.py","input_type":"python","target_agent":["TestAgent"]}],"preview_length":500},"output_config":{"output_directory":"output","output_format":["txt","json"],"file_naming":"test_{timestamp}","timestamp_format":"%Y%m%d_%H%M%S","include_metadata":true},"execution_config":{"track_execution_steps":true,"display_progress":true,"log_level":"INFO","error_handling":"continue_on_agent_failure","timeout_seconds":300},"report_config":{"include_final_responses":true,"include_code_preview":true,"include_execution_summary":true,"display_results_summary":true}},"agent_config":{"name":"MainWorkflow","class":"SequentialAgent","module":"google.adk.agents","description":"Main workflow container","sub_agents":[{"name":"TestSequential","class":"SequentialAgent","module":"google.adk.agents","description":"Sequential test agent","sub_agents":[{"name":"TestAgent","class":"Agent","module":"google.adk.agents","model":"openai/gpt-4o","instruction":"Test instruction for the agent","description":"Test agent description","output_key":"test_output"},{"name":"TestParallel","class":"ParallelAgent","module":"google.adk.agents","description":"Parallel test section","sub_agents":[{"name":"Agent1","class":"Agent","module":"google.adk.agents","model":"openai/gpt-4o","instruction":"First parallel agent","description":"First agent","output_key":"output1"},{"name":"Agent2","class":"Agent","module":"google.adk.agents","model":"openai/gpt-4o","instruction":"Second parallel agent","description":"Second agent","output_key":"output2"}]}]}]},"template_config":{"template_name":"Test Template","template_description":"Test template","template_version":"1.0","template_engine":"jinja2","template_content":"Test system prompt for workflow orchestration","template_variables":{"language":{"description":"Programming language","type":"string","default":"Python"}}}}`;

// Simulate the parsing logic
const parseWorkflowRequest = (jsonData) => {
  // Extract input files from job_config
  const inputFiles = jsonData.job_config?.input_config?.input_files || [];
  
  // The main agent config contains the root agents as sub_agents
  // If it's a wrapper agent (MainWorkflow), extract its sub_agents
  let rootAgents;
  
  if (jsonData.agent_config.name === 'MainWorkflow' && jsonData.agent_config.sub_agents) {
    // Extract sub_agents as root agents
    rootAgents = jsonData.agent_config.sub_agents.map((agent) => 
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

const parseAgentConfig = (agentData, allInputFiles = []) => {
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
        .map(file => ({
          input_path: file.input_path,
          input_type: file.input_type,
          target_agent: file.target_agent,
          file_content: '', // Content not stored in the JSON format
          original_name: file.input_path.split('/').pop() || file.input_path
        }));

      return {
        ...baseAgent,
        class: 'Agent',
        model: (agentData.model?.includes('gpt-4.1') ? 'gpt-4.1' : 'gpt-4o'),
        instruction: agentData.instruction || '',
        output_key: agentData.output_key || agentData.name,
        input_files: agentInputFiles,
        tools: agentData.tools || []
      };

    case 'SequentialAgent':
      return {
        ...baseAgent,
        class: 'SequentialAgent',
        sub_agents: (agentData.sub_agents || []).map((agent) => parseAgentConfig(agent, allInputFiles))
      };

    case 'LoopAgent':
      return {
        ...baseAgent,
        class: 'LoopAgent',
        max_iterations: agentData.max_iterations || 1,
        sub_agents: (agentData.sub_agents || []).map((agent) => parseAgentConfig(agent, allInputFiles))
      };

    case 'ParallelAgent':
      return {
        ...baseAgent,
        class: 'ParallelAgent',
        sub_agents: (agentData.sub_agents || []).map((agent) => parseAgentConfig(agent, allInputFiles))
      };

    default:
      throw new Error(`Unknown agent class: ${agentData.class}`);
  }
};

const parseConfigurationData = (configData) => {
  try {
    const jsonData = JSON.parse(configData);
    return parseWorkflowRequest(jsonData);
  } catch (error) {
    throw new Error(`Failed to parse configuration data: ${error.message}`);
  }
};

// Test the parsing
try {
  console.log('=== Testing Configuration Parsing ===');
  const workflowConfig = parseConfigurationData(testConfigData);
  
  console.log('\n=== Parsed Workflow Config ===');
  console.log('System Prompt:', workflowConfig.systemPrompt);
  console.log('Number of root agents:', workflowConfig.agents.length);
  
  const printAgent = (agent, indent = '') => {
    console.log(`${indent}${agent.name} (${agent.class})`);
    if (agent.class === 'Agent') {
      console.log(`${indent}  - Model: ${agent.model}`);
      console.log(`${indent}  - Instruction: ${agent.instruction}`);
      console.log(`${indent}  - Output Key: ${agent.output_key}`);
      console.log(`${indent}  - Input Files: ${agent.input_files.length}`);
      if (agent.input_files.length > 0) {
        agent.input_files.forEach(file => {
          console.log(`${indent}    * ${file.input_path} (${file.input_type})`);
        });
      }
    } else if (agent.sub_agents) {
      console.log(`${indent}  - Sub-agents: ${agent.sub_agents.length}`);
      agent.sub_agents.forEach(subAgent => {
        printAgent(subAgent, indent + '    ');
      });
    }
  };
  
  workflowConfig.agents.forEach((agent, i) => {
    console.log(`\nRoot Agent ${i + 1}:`);
    printAgent(agent);
  });
  
  console.log('\n✅ Configuration parsing successful!');
  
} catch (error) {
  console.error('❌ Configuration parsing failed:', error.message);
}