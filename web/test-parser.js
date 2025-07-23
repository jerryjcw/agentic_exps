// Simple test for the configuration parser
const testConfigData = `{"job_config":{"job_name":"TestWorkflow","job_description":"Test workflow","job_type":"test","runner_config":{"app_name":"TestWorkflow","session_config":{"user_id":"test_user","session_id":"test_session"}},"input_config":{"input_files":[{"input_path":"/test/file.py","input_type":"python","target_agent":["TestAgent"]}],"preview_length":500},"output_config":{"output_directory":"output","output_format":["txt","json"],"file_naming":"test_{timestamp}","timestamp_format":"%Y%m%d_%H%M%S","include_metadata":true},"execution_config":{"track_execution_steps":true,"display_progress":true,"log_level":"INFO","error_handling":"continue_on_agent_failure","timeout_seconds":300},"report_config":{"include_final_responses":true,"include_code_preview":true,"include_execution_summary":true,"display_results_summary":true}},"agent_config":{"name":"MainWorkflow","class":"SequentialAgent","module":"google.adk.agents","description":"Main workflow container","sub_agents":[{"name":"TestSequential","class":"SequentialAgent","module":"google.adk.agents","description":"Sequential test agent","sub_agents":[{"name":"TestAgent","class":"Agent","module":"google.adk.agents","model":"openai/gpt-4o","instruction":"Test instruction for the agent","description":"Test agent description","output_key":"test_output"},{"name":"TestParallel","class":"ParallelAgent","module":"google.adk.agents","description":"Parallel test section","sub_agents":[{"name":"Agent1","class":"Agent","module":"google.adk.agents","model":"openai/gpt-4o","instruction":"First parallel agent","description":"First agent","output_key":"output1"},{"name":"Agent2","class":"Agent","module":"google.adk.agents","model":"openai/gpt-4o","instruction":"Second parallel agent","description":"Second agent","output_key":"output2"}]}]}]},"template_config":{"template_name":"Test Template","template_description":"Test template","template_version":"1.0","template_engine":"jinja2","template_content":"Test system prompt for workflow orchestration","template_variables":{"language":{"description":"Programming language","type":"string","default":"Python"}}}}`;

try {
  const jsonData = JSON.parse(testConfigData);
  console.log('=== Parsed JSON Structure ===');
  console.log('Agent config name:', jsonData.agent_config.name);
  console.log('Agent config class:', jsonData.agent_config.class);
  console.log('Has sub_agents:', !!jsonData.agent_config.sub_agents);
  console.log('Number of sub_agents:', jsonData.agent_config.sub_agents?.length || 0);
  
  if (jsonData.agent_config.sub_agents) {
    console.log('\n=== Root Agents ===');
    jsonData.agent_config.sub_agents.forEach((agent, i) => {
      console.log(`${i + 1}. ${agent.name} (${agent.class})`);
      if (agent.sub_agents) {
        console.log(`   - Has ${agent.sub_agents.length} sub-agents`);
        agent.sub_agents.forEach((subAgent, j) => {
          console.log(`     ${j + 1}. ${subAgent.name} (${subAgent.class})`);
          if (subAgent.sub_agents) {
            subAgent.sub_agents.forEach((subSubAgent, k) => {
              console.log(`        ${k + 1}. ${subSubAgent.name} (${subSubAgent.class})`);
            });
          }
        });
      }
    });
  }
  
  console.log('\n=== Input Files ===');
  console.log('Input files:', JSON.stringify(jsonData.job_config.input_config.input_files, null, 2));
  
  console.log('\n=== Template Config ===');
  console.log('System prompt:', jsonData.template_config.template_content);
  
} catch (error) {
  console.error('Error parsing JSON:', error);
}