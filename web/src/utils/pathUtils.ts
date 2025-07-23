/**
 * Path utilities for dynamic project path resolution
 */

// Cache for system info
let systemInfoCache: { projectRoot: string; uploadDir: string } | null = null;

/**
 * Get system info from server (cached)
 */
const getSystemInfo = async (): Promise<{ projectRoot: string; uploadDir: string }> => {
  if (systemInfoCache) {
    return systemInfoCache;
  }
  
  try {
    const response = await fetch('http://127.0.0.1:3001/api/system/info');
    if (response.ok) {
      const info = await response.json();
      systemInfoCache = {
        projectRoot: info.projectRoot,
        uploadDir: info.uploadDir
      };
      return systemInfoCache;
    }
  } catch (error) {
    console.warn('Failed to fetch system info from server, using fallback paths');
  }
  
  // Fallback if server is not available
  return {
    projectRoot: '/Users/user/projects/agentic_exps',
    uploadDir: '/Users/user/projects/agentic_exps/web/uploaded_files'
  };
};

/**
 * Get the project root path dynamically
 * Fetches from server in browser, uses process.cwd() in Node.js
 */
export const getProjectRoot = async (): Promise<string> => {
  // Check environment variable first
  if (typeof process !== 'undefined' && process.env.PROJECT_ROOT) {
    return process.env.PROJECT_ROOT;
  }
  
  if (typeof window !== 'undefined') {
    // Browser environment - get from server
    const systemInfo = await getSystemInfo();
    return systemInfo.projectRoot;
  }
  
  // Node.js environment - auto-detect based on cwd
  if (typeof process !== 'undefined' && process.cwd) {
    const cwd = process.cwd();
    
    // If we're running from the web directory, go up one level
    if (cwd.endsWith('/web')) {
      return cwd.replace('/web', '');
    }
    
    // If we're running from the project root
    if (cwd.endsWith('/agentic_exps')) {
      return cwd;
    }
    
    // Look for agentic_exps in the path
    if (cwd.includes('/agentic_exps')) {
      return cwd.substring(0, cwd.indexOf('/agentic_exps') + '/agentic_exps'.length);
    }
    
    // Otherwise, assume current directory contains the project
    return cwd;
  }
  
  // Final fallback
  return '/project/agentic_exps';
};

/**
 * Get the web upload directory path
 */
export const getUploadDir = async (): Promise<string> => {
  // Check environment variable first
  if (typeof process !== 'undefined' && process.env.UPLOAD_DIR) {
    return process.env.UPLOAD_DIR;
  }
  
  // Check Vite environment variable for browser
  if (typeof window !== 'undefined' && import.meta.env.VITE_UPLOAD_DIR) {
    return import.meta.env.VITE_UPLOAD_DIR;
  }
  
  if (typeof window !== 'undefined') {
    // Browser environment - get from server
    const systemInfo = await getSystemInfo();
    return systemInfo.uploadDir;
  }
  
  // Default: construct from project root
  const projectRoot = await getProjectRoot();
  return `${projectRoot}/web/uploaded_files`;
};

/**
 * Generate a file path within the upload directory
 */
export const generateFilePath = async (originalName: string): Promise<string> => {
  const timestamp = Date.now();
  const sanitizedName = originalName.replace(/[^a-zA-Z0-9.-]/g, '_');
  const uploadDir = await getUploadDir();
  return `${uploadDir}/${timestamp}_${sanitizedName}`;
};

/**
 * Get relative path from project root
 */
export const getRelativeFromRoot = async (absolutePath: string): Promise<string> => {
  const projectRoot = await getProjectRoot();
  return absolutePath.replace(projectRoot, '');
};

/**
 * Environment-aware path resolution
 */
export const getEnvironmentPath = async (): Promise<string> => {
  // Check if we're in a browser environment
  if (typeof window !== 'undefined') {
    // Browser - use environment variables or fallback
    return (window as any).__PROJECT_ROOT__ || await getProjectRoot();
  }
  
  // Node.js - use process.cwd()
  if (typeof process !== 'undefined') {
    return process.cwd().includes('agentic_exps') 
      ? process.cwd().split('agentic_exps')[0] + 'agentic_exps'
      : process.cwd();
  }
  
  return '/project';
};