export interface SavedConfiguration {
  id?: number;
  name: string;
  description?: string | null;
  author: string;
  creation_date: string;
  last_modified: string;
  version: number;
  configuration_data: string; // JSON string of the full configuration
  system_prompt: string;
}

export interface DatabaseConfig {
  dbPath: string;
}

export interface ExecutionConfig {
  apiEndpoint: string;
  timeout?: number;
}