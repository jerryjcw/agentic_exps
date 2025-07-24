import { useState, useCallback, useEffect } from 'react';
import type { WorkflowConfig, NavigationView } from './types';
import { ConfigBuilder } from './components/ConfigBuilder';
import SaveConfiguration from './components/SaveConfiguration';
import LoadConfiguration from './components/LoadConfiguration';
import ExecuteConfiguration from './components/ExecuteConfiguration';
import { convertToWorkflowRequest } from './utils/configConverter';
import { uploadFilesToServer, createFileManifest } from './utils/fileStorage';
import { Plus, Save, FolderOpen, Play, Code, Copy, Download } from 'lucide-react';

function App() {
  const [currentView, setCurrentView] = useState<NavigationView>('create');
  const [config, setConfig] = useState<WorkflowConfig>({
    systemPrompt: '',
    agents: [],
    useInternalModels: false
  });
  const [jsonConfig, setJsonConfig] = useState<string>('');

  // Clear JSON when configuration changes
  useEffect(() => {
    setJsonConfig('');
  }, [config]);

  const handleSaveSuccess = (id: number, name: string) => {
    console.log(`Configuration "${name}" saved with ID: ${id}`);
    // Optionally switch to another view or show success message
  };

  const handleConfigurationLoad = (loadedConfig: WorkflowConfig) => {
    setConfig(loadedConfig);
    setJsonConfig(''); // Clear JSON when loading new config
    setCurrentView('create'); // Switch to create view to show loaded config
  };

  const handleConvertToJSON = useCallback(async () => {
    try {
      // First, collect all files from all agents
      const allFiles: any[] = [];
      const extractFiles = (agents: any[]) => {
        agents.forEach(agent => {
          if (agent.class === 'Agent' && agent.input_files) {
            allFiles.push(...agent.input_files);
          } else if (agent.class !== 'Agent' && agent.sub_agents) {
            extractFiles(agent.sub_agents);
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
      
      const workflowRequest = await convertToWorkflowRequest(config);
      const formattedJson = JSON.stringify(workflowRequest, null, 2);
      
      console.log('✅ JSON generated successfully - length:', formattedJson.length);
      
      setJsonConfig(formattedJson);
      
      console.log('✅ JSON Config set. First 100 chars:', formattedJson.substring(0, 100));
      
    } catch (error) {
      console.error('Error converting config:', error);
      alert('Error converting configuration. Please check that all required fields are filled.');
    }
  }, [config]);

  const handleCopyToClipboard = useCallback(async () => {
    if (!jsonConfig) {
      await handleConvertToJSON();
      return;
    }

    try {
      await navigator.clipboard.writeText(jsonConfig);
      alert('Configuration copied to clipboard!');
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
      // Fallback for browsers that don't support clipboard API
      const textArea = document.createElement('textarea');
      textArea.value = jsonConfig;
      textArea.style.position = 'fixed';
      textArea.style.opacity = '0';
      document.body.appendChild(textArea);
      textArea.select();
      try {
        document.execCommand('copy');
        alert('Configuration copied to clipboard!');
      } catch (fallbackError) {
        console.error('Fallback copy failed:', fallbackError);
        alert('Failed to copy to clipboard. Please copy manually from the JSON modal.');
      }
      document.body.removeChild(textArea);
    }
  }, [jsonConfig, handleConvertToJSON]);

  const handleDownloadConfig = useCallback(async () => {
    if (!jsonConfig) {
      await handleConvertToJSON();
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
  }, [jsonConfig, handleConvertToJSON]);

  const handleExecuteWorkflow = useCallback(async () => {
    if (!jsonConfig) {
      await handleConvertToJSON();
      if (!jsonConfig) return;
    }

    try {
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
  }, [jsonConfig, handleConvertToJSON]);

  const tabs = [
    { id: 'create' as NavigationView, label: 'Create Configuration', icon: Plus },
    { id: 'save' as NavigationView, label: 'Save Configuration', icon: Save },
    { id: 'list' as NavigationView, label: 'Load Configuration', icon: FolderOpen },
    { id: 'execute' as NavigationView, label: 'Execute Configuration', icon: Play },
  ];

  const renderCurrentView = () => {
    switch (currentView) {
      case 'create':
        return (
          <ConfigBuilder
            config={config}
            onChange={setConfig}
            jsonConfig={jsonConfig}
          />
        );
      case 'save':
        return (
          <SaveConfiguration
            config={config}
            onSaveSuccess={handleSaveSuccess}
          />
        );
      case 'list':
        return (
          <LoadConfiguration
            onConfigurationLoad={handleConfigurationLoad}
          />
        );
      case 'execute':
        return (
          <ExecuteConfiguration
            config={config}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-md shadow-lg border-b border-gray-200/50 sticky top-0 z-40">
        <div className="w-3/5 mx-auto px-6 py-4">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent text-center">
            Agent Workflow Studio
          </h1>
        </div>
      </div>

      {/* Tabs */}
      <div className="py-4">
        <div className="w-3/5 mx-auto px-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-1 flex space-x-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setCurrentView(tab.id)}
                  className={`flex-1 inline-flex items-center justify-center px-3 py-2 text-sm font-medium transition-all duration-200 rounded-md ${
                    currentView === tab.id
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Function Buttons for Create Tab */}
      {currentView === 'create' && (
        <div className="pb-4">
          <div className="w-3/5 mx-auto px-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="flex flex-wrap gap-3">
                <button
                onClick={handleConvertToJSON}
                className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 font-medium shadow-md hover:shadow-lg"
              >
                <Code className="w-4 h-4 mr-2" />
                Convert to JSON
              </button>
              
              <button
                onClick={handleCopyToClipboard}
                disabled={!jsonConfig}
                className={`inline-flex items-center px-4 py-2 rounded-lg transition-all duration-200 font-medium shadow-md hover:shadow-lg ${
                  !jsonConfig 
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                <Copy className="w-4 h-4 mr-2" />
                Copy to Clipboard
              </button>
              
              <button
                onClick={handleDownloadConfig}
                disabled={config.agents.length === 0}
                className={`inline-flex items-center px-4 py-2 rounded-lg transition-all duration-200 font-medium shadow-md hover:shadow-lg ${
                  config.agents.length === 0 
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                    : 'bg-green-600 text-white hover:bg-green-700'
                }`}
              >
                <Download className="w-4 h-4 mr-2" />
                Download Config
              </button>
              
              <button
                onClick={handleExecuteWorkflow}
                disabled={config.agents.length === 0}
                className={`inline-flex items-center px-4 py-2 rounded-lg transition-all duration-200 font-medium shadow-md hover:shadow-lg ${
                  config.agents.length === 0 
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                    : 'bg-orange-600 text-white hover:bg-orange-700'
                }`}
              >
                <Play className="w-4 h-4 mr-2" />
                Execute Workflow
              </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      <main>
        {renderCurrentView()}
      </main>
    </div>
  );
}

export default App;