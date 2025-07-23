import type { SavedConfiguration } from '../types/database';

const API_BASE_URL = 'http://127.0.0.1:3001/api';

// Helper function for making API requests
async function apiRequest(endpoint: string, options: RequestInit = {}): Promise<any> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(error.error || `HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

export const saveConfiguration = async (config: Omit<SavedConfiguration, 'id'>): Promise<number> => {
  const result = await apiRequest('/configurations', {
    method: 'POST',
    body: JSON.stringify(config),
  });
  
  return result.id;
};

export const getAllConfigurations = async (): Promise<SavedConfiguration[]> => {
  return apiRequest('/configurations');
};

export const getConfigurationById = async (id: number): Promise<SavedConfiguration | null> => {
  try {
    return await apiRequest(`/configurations/${id}`);
  } catch (error) {
    if (error instanceof Error && error.message.includes('404')) {
      return null;
    }
    throw error;
  }
};

export const getConfigurationByName = async (name: string): Promise<SavedConfiguration | null> => {
  const configurations = await getAllConfigurations();
  return configurations.find(config => config.name === name) || null;
};

export const deleteConfiguration = async (id: number): Promise<boolean> => {
  try {
    await apiRequest(`/configurations/${id}`, {
      method: 'DELETE',
    });
    return true;
  } catch (error) {
    if (error instanceof Error && error.message.includes('404')) {
      return false;
    }
    throw error;
  }
};

export const updateConfiguration = async (id: number, config: Partial<SavedConfiguration>): Promise<boolean> => {
  try {
    // For updates, we need to get the existing config first, then POST with updated data
    const existing = await getConfigurationById(id);
    if (!existing) return false;

    const updatedConfig = {
      ...existing,
      ...config,
      last_modified: new Date().toISOString(),
    };

    await apiRequest('/configurations', {
      method: 'POST',
      body: JSON.stringify(updatedConfig),
    });
    
    return true;
  } catch (error) {
    return false;
  }
};