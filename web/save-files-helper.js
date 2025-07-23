#!/usr/bin/env node

/**
 * File Save Helper for Web UI
 * 
 * This script reads files from localStorage and saves them to the web/uploaded_files directory.
 * Usage: node save-files-helper.js
 */

const fs = require('fs');
const path = require('path');

// Dynamically determine the upload directory based on current working directory
function getUploadDir() {
  const cwd = process.cwd();
  
  // If running from the web directory
  if (cwd.endsWith('/web')) {
    return path.join(cwd, 'uploaded_files');
  }
  
  // If running from the project root (agentic_exps)
  if (cwd.endsWith('/agentic_exps')) {
    return path.join(cwd, 'web', 'uploaded_files');
  }
  
  // If running from anywhere else, try to find the project
  const webPath = path.join(cwd, 'web', 'uploaded_files');
  if (fs.existsSync(path.join(cwd, 'web'))) {
    return webPath;
  }
  
  // Fallback: create in current directory
  return path.join(cwd, 'uploaded_files');
}

const UPLOAD_DIR = getUploadDir();

// Ensure upload directory exists
if (!fs.existsSync(UPLOAD_DIR)) {
  fs.mkdirSync(UPLOAD_DIR, { recursive: true });
  console.log(`📁 Created directory: ${UPLOAD_DIR}`);
}

/**
 * Save a file to the upload directory
 */
function saveFile(fileData) {
  try {
    const fileName = fileData.originalName || `file_${fileData.timestamp}`;
    const filePath = path.join(UPLOAD_DIR, fileName);
    
    // Handle binary files (base64 encoded) vs text files
    if (fileData.is_binary && fileData.content) {
      // Decode base64 content and write as binary
      const binaryContent = Buffer.from(fileData.content, 'base64');
      fs.writeFileSync(filePath, binaryContent);
      console.log(`✅ Saved binary file: ${fileName} -> ${filePath} (${binaryContent.length} bytes)`);
    } else if (fileData.content) {
      // For text files, decode base64 and handle UTF-8 properly
      let textContent = fileData.content;
      
      if (isBase64Encoded(fileData.content)) {
        // Decode base64 to get the UTF-8 bytes that were encoded on the frontend
        const base64Decoded = Buffer.from(fileData.content, 'base64');
        
        // Convert bytes back to UTF-8 string using TextDecoder approach
        try {
          textContent = base64Decoded.toString('utf8');
        } catch (error) {
          // Fallback to direct base64 decode if UTF-8 decoding fails
          textContent = base64Decoded.toString();
        }
      }
      
      fs.writeFileSync(filePath, textContent, 'utf8');
      console.log(`✅ Saved text file: ${fileName} -> ${filePath} (${textContent.length} chars)`);
    } else {
      console.log(`⚠️ No content to save for: ${fileName}`);
    }
    
    return filePath;
  } catch (error) {
    console.error(`❌ Failed to save ${fileData.originalName}:`, error.message);
    return null;
  }
}

/**
 * Check if a string is base64 encoded
 */
function isBase64Encoded(str) {
  try {
    return Buffer.from(str, 'base64').toString('base64') === str;
  } catch (error) {
    return false;
  }
}

/**
 * Mock function to simulate getting files from browser localStorage
 * In a real implementation, this would come from a server API endpoint
 */
function getMockUploadedFiles() {
  // This would normally come from the browser via an API call
  // For demonstration, return empty array
  return [];
}

/**
 * Main function
 */
function main() {
  console.log('📂 File Save Helper for Web UI');
  console.log('==============================');
  console.log(`🔍 Current working directory: ${process.cwd()}`);
  console.log(`📁 Detected upload directory: ${UPLOAD_DIR}`);
  
  const files = getMockUploadedFiles();
  
  if (files.length === 0) {
    console.log('📭 No files to save.');
    console.log('');
    console.log('💡 How to use:');
    console.log('1. Upload files through the web UI');
    console.log('2. Files are stored in browser localStorage');
    console.log('3. Use this script to save them to disk');
    console.log('4. Or implement a proper server API endpoint');
    return;
  }
  
  let savedCount = 0;
  files.forEach(file => {
    if (saveFile(file)) {
      savedCount++;
    }
  });
  
  console.log(`\n📊 Summary: ${savedCount}/${files.length} files saved successfully`);
}

// Export for potential use as module
module.exports = { saveFile, UPLOAD_DIR };

// Run if called directly
if (require.main === module) {
  main();
}