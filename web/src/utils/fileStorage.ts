import type { InputFile } from '../types';

// Note: In production, would use actual server endpoint like '/api/files/upload'

export interface StoredFile {
  originalName: string;
  storedPath: string;
  content: string;
  type: string;
  size: number;
  uploadedAt: string;
}

export const uploadFilesToServer = async (files: InputFile[]): Promise<StoredFile[]> => {
  // In a real implementation, this would upload files to a server
  // For now, we'll simulate the server response
  
  const storedFiles: StoredFile[] = [];
  
  for (const file of files) {
    if (file.file_content) {
      const storedFile: StoredFile = {
        originalName: file.original_name || 'unknown',
        storedPath: file.input_path,
        content: file.file_content,
        type: file.input_type,
        size: file.file_content.length,
        uploadedAt: new Date().toISOString()
      };
      
      // Simulate saving to server
      try {
        // In real implementation, would be:
        // const response = await fetch(FILE_UPLOAD_ENDPOINT, {
        //   method: 'POST',
        //   headers: { 'Content-Type': 'application/json' },
        //   body: JSON.stringify(storedFile)
        // });
        
        // For now, just log and store locally
        console.log(`📁 File uploaded: ${storedFile.originalName} -> ${storedFile.storedPath}`);
        
        // Store metadata only in localStorage (without file content to avoid quota limits)
        const existingFiles = JSON.parse(localStorage.getItem('serverFiles') || '[]');
        const fileMetadata = {
          originalName: storedFile.originalName,
          storedPath: storedFile.storedPath,
          type: storedFile.type,
          size: storedFile.size,
          uploadedAt: storedFile.uploadedAt
          // content excluded to avoid localStorage quota limits
        };
        existingFiles.push(fileMetadata);
        localStorage.setItem('serverFiles', JSON.stringify(existingFiles));
        
        storedFiles.push(storedFile);
        
      } catch (error) {
        console.error(`Failed to upload ${file.original_name}:`, error);
        throw new Error(`Failed to upload ${file.original_name}: ${error}`);
      }
    }
  }
  
  return storedFiles;
};

export const getStoredFiles = (): StoredFile[] => {
  try {
    return JSON.parse(localStorage.getItem('serverFiles') || '[]');
  } catch {
    return [];
  }
};

export const deleteStoredFile = (storedPath: string): boolean => {
  try {
    const existingFiles = getStoredFiles();
    const updatedFiles = existingFiles.filter(file => file.storedPath !== storedPath);
    localStorage.setItem('serverFiles', JSON.stringify(updatedFiles));
    return true;
  } catch {
    return false;
  }
};

export const createFileManifest = (files: InputFile[]): string => {
  // Create a manifest showing all uploaded files and their absolute paths
  const manifest = {
    uploadedAt: new Date().toISOString(),
    totalFiles: files.length,
    files: files.map(file => ({
      originalName: file.original_name,
      storedPath: file.input_path,
      type: file.input_type,
      size: file.file_content?.length || 0,
      targetAgents: file.target_agent
    }))
  };
  
  return JSON.stringify(manifest, null, 2);
};