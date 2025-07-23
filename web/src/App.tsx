import { useState } from 'react';
import type { WorkflowConfig, NavigationView } from './types';
import { ConfigBuilder } from './components/ConfigBuilder';
import Navigation from './components/Navigation';
import SaveConfiguration from './components/SaveConfiguration';
import LoadConfiguration from './components/LoadConfiguration';
import ExecuteConfiguration from './components/ExecuteConfiguration';

function App() {
  const [currentView, setCurrentView] = useState<NavigationView>('create');
  const [config, setConfig] = useState<WorkflowConfig>({
    systemPrompt: '',
    agents: []
  });

  const handleSaveSuccess = (id: number, name: string) => {
    console.log(`Configuration "${name}" saved with ID: ${id}`);
    // Optionally switch to another view or show success message
  };

  const handleConfigurationLoad = (loadedConfig: WorkflowConfig) => {
    setConfig(loadedConfig);
    setCurrentView('create'); // Switch to create view to show loaded config
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'create':
        return (
          <ConfigBuilder
            config={config}
            onChange={setConfig}
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
    <div className="min-h-screen bg-gray-100">
      <Navigation
        currentView={currentView}
        onViewChange={setCurrentView}
      />
      
      <main className="py-6">
        {renderCurrentView()}
      </main>
    </div>
  );
}

export default App;