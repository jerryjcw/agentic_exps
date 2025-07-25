import type { InputFile } from '../types';
import { generateFilePath } from './pathUtils';


export const handleFileUpload = async (file: File, agentName: string): Promise<InputFile> => {
  return new Promise(async (resolve, reject) => {
    const fullPath = await generateFilePath(file.name);
    const fileIsText = isTextFile(file.name);
    
    if (fileIsText) {
      // Handle text files with proper encoding
      const textReader = new FileReader();
      
      textReader.onload = (event) => {
        const textContent = event.target?.result as string;
        
        // For text files, store as base64 with proper UTF-8 encoding
        const encoder = new TextEncoder();
        const utf8Bytes = encoder.encode(textContent);
        const base64Content = btoa(String.fromCharCode(...utf8Bytes));
        
        const inputFile: InputFile = {
          input_path: fullPath,
          input_type: getFileType(file.name),
          target_agent: [agentName],
          file_content: base64Content,
          original_name: file.name,
          file_size: file.size,
          is_binary: false
        };
        
        resolve(inputFile);
      };
      
      textReader.onerror = () => {
        reject(new Error(`Failed to read text file: ${file.name}`));
      };
      
      // Read as text with UTF-8 encoding
      textReader.readAsText(file, 'UTF-8');
      
    } else {
      // Handle binary files
      const binaryReader = new FileReader();
      
      binaryReader.onload = (event) => {
        const arrayBuffer = event.target?.result as ArrayBuffer;
        
        // Convert ArrayBuffer to base64 for binary files
        const uint8Array = new Uint8Array(arrayBuffer);
        
        // Handle large files by processing in chunks to avoid call stack overflow
        let binaryString = '';
        const chunkSize = 8192; // Process 8KB at a time
        
        for (let i = 0; i < uint8Array.length; i += chunkSize) {
          const chunk = uint8Array.slice(i, i + chunkSize);
          binaryString += String.fromCharCode.apply(null, Array.from(chunk));
        }
        
        const base64Content = btoa(binaryString);
        
        const inputFile: InputFile = {
          input_path: fullPath,
          input_type: getFileType(file.name),
          target_agent: [agentName],
          file_content: base64Content,
          original_name: file.name,
          file_size: file.size,
          is_binary: true
        };
        
        resolve(inputFile);
      };
      
      binaryReader.onerror = () => {
        reject(new Error(`Failed to read binary file: ${file.name}`));
      };
      
      // Read as ArrayBuffer for binary files
      binaryReader.readAsArrayBuffer(file);
    }
  });
};

/**
 * Determine if a file is likely to be a text file based on its extension
 */
const isTextFile = (fileName: string): boolean => {
  const extension = fileName.split('.').pop()?.toLowerCase();
  
  const textExtensions = new Set([
    // Programming languages
    'py', 'js', 'jsx', 'ts', 'tsx', 'java', 'cpp', 'cc', 'cxx', 'c', 'h', 'hpp',
    'go', 'rs', 'php', 'rb', 'swift', 'kt', 'scala', 'r', 'pl', 'sh', 'bat',
    // Web technologies
    'html', 'htm', 'css', 'scss', 'sass', 'less', 'vue', 'svelte',
    // Data formats
    'json', 'xml', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'conf',
    // Documentation
    'md', 'rst', 'txt', 'rtf', 'tex',
    // Configuration
    'gitignore', 'gitattributes', 'dockerignore', 'editorconfig',
    // Other text formats
    'csv', 'tsv', 'log', 'sql', 'graphql', 'gql'
  ]);
  
  return textExtensions.has(extension || '');
};

const getFileType = (fileName: string): string => {
  const extension = fileName.split('.').pop()?.toLowerCase();
  
  // Programming languages
  const languageMap = {
    'py': 'python',
    'js': 'javascript',
    'jsx': 'javascript',
    'ts': 'typescript',
    'tsx': 'typescript',
    'java': 'java',
    'cpp': 'cpp',
    'cc': 'cpp',
    'cxx': 'cpp',
    'c': 'c',
    'h': 'c',
    'hpp': 'cpp',
    'go': 'go',
    'rs': 'rust',
    'php': 'php',
    'rb': 'ruby',
    'swift': 'swift',
    'kt': 'kotlin',
    'scala': 'scala',
    'r': 'r',
    'pl': 'perl',
    'sh': 'shell',
    'bat': 'batch'
  };
  
  // Web technologies
  const webMap = {
    'html': 'html',
    'htm': 'html',
    'css': 'css',
    'scss': 'scss',
    'sass': 'sass',
    'less': 'less',
    'vue': 'vue',
    'svelte': 'svelte'
  };
  
  // Data formats
  const dataMap = {
    'json': 'json',
    'xml': 'xml',
    'yaml': 'yaml',
    'yml': 'yaml',
    'toml': 'toml',
    'ini': 'ini',
    'cfg': 'config',
    'conf': 'config',
    'csv': 'csv',
    'tsv': 'tsv'
  };
  
  // Documentation
  const docMap = {
    'md': 'markdown',
    'rst': 'restructuredtext',
    'txt': 'text',
    'rtf': 'rtf',
    'tex': 'latex'
  };
  
  // Binary/Media files
  const binaryMap = {
    // Images
    'jpg': 'image',
    'jpeg': 'image',
    'png': 'image',
    'gif': 'image',
    'bmp': 'image',
    'svg': 'image',
    'webp': 'image',
    'ico': 'image',
    // Documents
    'pdf': 'pdf',
    'doc': 'document',
    'docx': 'document',
    'xls': 'spreadsheet',
    'xlsx': 'spreadsheet',
    'ppt': 'presentation',
    'pptx': 'presentation',
    // Archives
    'zip': 'archive',
    'tar': 'archive',
    'gz': 'archive',
    'rar': 'archive',
    '7z': 'archive',
    // Executables
    'exe': 'executable',
    'dll': 'library',
    'so': 'library',
    'dylib': 'library',
    // Audio/Video
    'mp3': 'audio',
    'wav': 'audio',
    'mp4': 'video',
    'avi': 'video',
    'mov': 'video'
  };
  
  // Check in order of specificity
  const ext = extension || '';
  if (languageMap[ext as keyof typeof languageMap]) return languageMap[ext as keyof typeof languageMap];
  if (webMap[ext as keyof typeof webMap]) return webMap[ext as keyof typeof webMap];
  if (dataMap[ext as keyof typeof dataMap]) return dataMap[ext as keyof typeof dataMap];
  if (docMap[ext as keyof typeof docMap]) return docMap[ext as keyof typeof docMap];
  if (binaryMap[ext as keyof typeof binaryMap]) return binaryMap[ext as keyof typeof binaryMap];
  
  // Default based on whether it's likely text or binary
  return isTextFile(fileName) ? 'text' : 'binary';
};

export const saveFileToKnownLocation = async (inputFile: InputFile): Promise<boolean> => {
  try {
    // Only process files that actually have content (newly uploaded files)
    if (!inputFile.file_content || inputFile.file_content.length === 0) {
      return true; // Return true since this isn't an error, just a loaded file reference
    }

    // Extract timestamp from the generated path to ensure consistency
    const pathMatch = inputFile.input_path.match(/\/(\d+)_/);
    const timestamp = pathMatch ? parseInt(pathMatch[1]) : Date.now();

    const fileData = {
      path: inputFile.input_path,
      content: inputFile.file_content,
      originalName: inputFile.original_name,
      type: inputFile.input_type,
      file_size: inputFile.file_size,
      is_binary: inputFile.is_binary,
      timestamp: timestamp
    };
    
    // Files are saved to server - no need for localStorage backup to avoid quota issues
    
    console.log(`📁 File ready for storage at: ${inputFile.input_path}`);
    console.log(`📄 Original name: ${inputFile.original_name}`);
    console.log(`📋 File size: ${inputFile.file_size} bytes`);
    console.log(`📝 File type: ${inputFile.input_type} (${inputFile.is_binary ? 'binary' : 'text'})`);
    console.log(`🔗 Content encoded as base64 for storage`);
    
    // Make API call to save the file physically
    try {
      const response = await fetch('http://localhost:3001/api/files/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(fileData)
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log(`✅ File saved to disk: ${result.path}`);
      } else {
        const error = await response.json();
        console.error(`❌ Failed to save file to disk: ${error.error}`);
      }
    } catch (error) {
      console.error(`❌ Network error saving file: ${error}`);
      // Don't fail the upload if file saving fails - file is still in localStorage
    }
    
    return true;
  } catch (error) {
    console.error('Failed to prepare file for storage:', error);
    return false;
  }
};