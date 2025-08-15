#!/usr/bin/env node

/**
 * Simple database server for Web UI configurations
 * 
 * This script provides a REST API for managing workflow configurations
 * Usage: node database-server.js [port]
 */

const http = require('http');
const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

const PORT = process.argv[2] || 3001;

// Dynamically determine the database path
function getDatabasePath() {
  const cwd = process.cwd();
  
  // If running from the web directory
  if (cwd.endsWith('/web')) {
    return path.join(cwd, 'configurations.db');
  }
  
  // If running from the project root (agentic_exps)
  if (cwd.endsWith('/agentic_exps')) {
    return path.join(cwd, 'web', 'configurations.db');
  }
  
  // Look for web directory
  const webPath = path.join(cwd, 'web', 'configurations.db');
  if (fs.existsSync(path.join(cwd, 'web'))) {
    return webPath;
  }
  
  // Fallback: create in current directory
  return path.join(cwd, 'configurations.db');
}

const DB_PATH = getDatabasePath();
const db = new Database(DB_PATH);

// Initialize database
db.exec(`
  CREATE TABLE IF NOT EXISTS configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    author TEXT NOT NULL,
    creation_date TEXT NOT NULL,
    last_modified TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    configuration_data TEXT NOT NULL,
    system_prompt TEXT NOT NULL
  )
`);

// Create tools table
db.exec(`
  CREATE TABLE IF NOT EXISTS tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    function_name TEXT NOT NULL UNIQUE,
    class TEXT NOT NULL,
    module TEXT NOT NULL,
    function_module TEXT NOT NULL,
    category TEXT,
    description TEXT,
    signature TEXT,
    registry_module TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )
`);

console.log(`📁 Database initialized at: ${DB_PATH}`);

// Load tools from registry on startup - always refresh with latest registry data
function loadToolsFromRegistry() {
  const { spawn } = require('child_process');
  const path = require('path');
  
  console.log('🔧 Re-running registry and updating tools database with latest data...');
  
  const python = spawn('python3', ['extract-tools.py'], {
    cwd: path.dirname(DB_PATH),
    stdio: ['pipe', 'pipe', 'pipe']
  });
  
  let output = '';
  let errorOutput = '';
  
  python.stdout.on('data', (data) => {
    output += data.toString();
  });
  
  python.stderr.on('data', (data) => {
    errorOutput += data.toString();
  });
  
  python.on('close', (code) => {
    if (code === 0) {
      try {
        const result = JSON.parse(output);
        if (result.status === 'success' && result.tools) {
          // ALWAYS clear existing tools and insert fresh ones from registry
          console.log('🗑️  Clearing existing tools from database...');
          db.exec('DELETE FROM tools');
          
          const insertStmt = db.prepare(`
            INSERT INTO tools 
            (function_name, class, module, function_module, category, description, signature, registry_module)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
          `);
          
          const insertMany = db.transaction((tools) => {
            for (const tool of tools) {
              insertStmt.run(
                tool.function_name,
                tool.class,
                tool.module,
                tool.function_module,
                tool.category || 'general',
                tool.description || '',
                tool.signature || '',
                tool.registry_module || ''
              );
            }
          });
          
          insertMany(result.tools);
          console.log(`✅ Successfully refreshed database with ${result.tools.length} tools from registry`);
          
          // List loaded tools with their categories
          const toolsByCategory = {};
          result.tools.forEach(tool => {
            const category = tool.category || 'general';
            if (!toolsByCategory[category]) {
              toolsByCategory[category] = [];
            }
            toolsByCategory[category].push(tool.function_name);
          });
          
          Object.entries(toolsByCategory).forEach(([category, tools]) => {
            console.log(`   📁 ${category}: ${tools.join(', ')}`);
          });
          
          console.log('🔄 Tools database is now synchronized with the latest registry');
        } else {
          console.error('❌ Failed to load tools from registry:', result.error || 'Unknown error');
          console.error('🔧 Please check the tool registry at tools/gadk/');
        }
      } catch (parseError) {
        console.error('❌ Failed to parse tool registry output:', parseError.message);
        console.error('Raw output:', output);
      }
    } else {
      console.error('❌ Tool extraction failed with exit code:', code);
      console.error('Error output:', errorOutput);
      console.error('🔧 Please check that Python environment and tools/gadk/ are accessible');
    }
  });
  
  python.on('error', (error) => {
    console.error('❌ Failed to spawn Python process:', error.message);
    console.error('🔧 Please ensure Python3 is installed and accessible');
  });
}

// ALWAYS load fresh tools from registry on every database startup
// This ensures the database is synchronized with the latest tool registry changes
loadToolsFromRegistry();

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Content-Type': 'application/json'
};

// Helper function to send JSON response
function sendJSON(res, data, statusCode = 200) {
  res.writeHead(statusCode, corsHeaders);
  res.end(JSON.stringify(data));
}

// Helper function to send error response
function sendError(res, message, statusCode = 400) {
  sendJSON(res, { error: message }, statusCode);
}

// Helper function to parse request body
function parseBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch (err) {
        reject(new Error('Invalid JSON'));
      }
    });
  });
}

// File saving helper functions (inline to avoid ES module issues)
const UPLOAD_DIR = path.join(process.cwd(), 'uploaded_files');

// Ensure upload directory exists
if (!fs.existsSync(UPLOAD_DIR)) {
  fs.mkdirSync(UPLOAD_DIR, { recursive: true });
  console.log(`📁 Created directory: ${UPLOAD_DIR}`);
}

function saveFile(fileData) {
  try {
    const rawFileName = fileData.originalName || `file_${fileData.timestamp}`;
    // Sanitize filename to match frontend behavior - replace spaces and special chars with underscores
    const sanitizedName = rawFileName.replace(/[^a-zA-Z0-9.-]/g, '_');
    // Add timestamp prefix to match frontend path generation
    const timestamp = fileData.timestamp || Date.now();
    const fileName = `${timestamp}_${sanitizedName}`;
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
        
        // Convert bytes back to UTF-8 string
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

function isBase64Encoded(str) {
  try {
    return Buffer.from(str, 'base64').toString('base64') === str;
  } catch (error) {
    return false;
  }
}

// Route handlers
const routes = {
  // GET /api/system/info - Get system information including project paths
  'GET /api/system/info': (req, res) => {
    try {
      const cwd = process.cwd();
      let projectRoot = cwd;
      
      // Auto-detect project root based on current working directory
      if (cwd.endsWith('/web')) {
        projectRoot = cwd.replace('/web', '');
      } else if (cwd.includes('/agentic_exps')) {
        projectRoot = cwd.substring(0, cwd.indexOf('/agentic_exps') + '/agentic_exps'.length);
      }
      
      const systemInfo = {
        projectRoot: projectRoot,
        uploadDir: path.join(projectRoot, 'web', 'uploaded_files'),
        currentWorkingDir: cwd,
        homeDir: require('os').homedir()
      };
      
      sendJSON(res, systemInfo);
    } catch (err) {
      sendError(res, err.message, 500);
    }
  },
  // POST /api/files/save - Save uploaded file to disk
  'POST /api/files/save': async (req, res) => {
    try {
      const fileData = await parseBody(req);
      
      if (!fileData.originalName || !fileData.content) {
        sendError(res, 'Missing required fields: originalName and content', 400);
        return;
      }
      
      const savedPath = saveFile(fileData);
      
      if (savedPath) {
        sendJSON(res, { 
          success: true, 
          path: savedPath,
          message: `File saved successfully: ${fileData.originalName}` 
        });
      } else {
        sendError(res, 'Failed to save file', 500);
      }
    } catch (err) {
      sendError(res, err.message, 500);
    }
  },
  // GET /api/tools - Get all available tools
  'GET /api/tools': (req, res) => {
    try {
      const stmt = db.prepare('SELECT * FROM tools ORDER BY category, function_name');
      const tools = stmt.all();
      sendJSON(res, tools);
    } catch (err) {
      sendError(res, err.message, 500);
    }
  },

  // GET /api/configurations - Get all configurations
  'GET /api/configurations': (req, res) => {
    try {
      const stmt = db.prepare('SELECT * FROM configurations ORDER BY last_modified DESC');
      const configurations = stmt.all();
      sendJSON(res, configurations);
    } catch (err) {
      sendError(res, err.message, 500);
    }
  },

  // GET /api/configurations/:id - Get configuration by ID
  'GET /api/configurations/': (req, res, id) => {
    try {
      const stmt = db.prepare('SELECT * FROM configurations WHERE id = ?');
      const config = stmt.get(parseInt(id));
      
      if (!config) {
        sendError(res, 'Configuration not found', 404);
        return;
      }
      
      sendJSON(res, config);
    } catch (err) {
      sendError(res, err.message, 500);
    }
  },

  // POST /api/configurations - Create/update configuration
  'POST /api/configurations': async (req, res) => {
    try {
      const body = await parseBody(req);
      const { name, description, author, configuration_data, system_prompt } = body;

      if (!name || !author || !configuration_data || !system_prompt) {
        sendError(res, 'Missing required fields: name, author, configuration_data, system_prompt');
        return;
      }

      const now = new Date().toISOString();
      
      // Check if configuration exists
      const existingStmt = db.prepare('SELECT * FROM configurations WHERE name = ?');
      const existing = existingStmt.get(name);
      
      if (existing) {
        // Update existing
        const updateStmt = db.prepare(`
          UPDATE configurations 
          SET description = ?, author = ?, last_modified = ?, 
              version = version + 1, configuration_data = ?, system_prompt = ?
          WHERE name = ?
        `);
        
        updateStmt.run(description, author, now, configuration_data, system_prompt, name);
        const updated = existingStmt.get(name);
        sendJSON(res, updated);
      } else {
        // Create new
        const insertStmt = db.prepare(`
          INSERT INTO configurations 
          (name, description, author, creation_date, last_modified, version, configuration_data, system_prompt)
          VALUES (?, ?, ?, ?, ?, 1, ?, ?)
        `);
        
        const result = insertStmt.run(name, description, author, now, now, configuration_data, system_prompt);
        const created = db.prepare('SELECT * FROM configurations WHERE id = ?').get(result.lastInsertRowid);
        sendJSON(res, created, 201);
      }
    } catch (err) {
      sendError(res, err.message, 500);
    }
  },

  // DELETE /api/configurations/:id - Delete configuration
  'DELETE /api/configurations/': (req, res, id) => {
    try {
      const stmt = db.prepare('DELETE FROM configurations WHERE id = ?');
      const result = stmt.run(parseInt(id));
      
      if (result.changes === 0) {
        sendError(res, 'Configuration not found', 404);
        return;
      }
      
      sendJSON(res, { success: true });
    } catch (err) {
      sendError(res, err.message, 500);
    }
  }
};

// Request handler
const server = http.createServer(async (req, res) => {
  const { method, url } = req;
  
  // Handle CORS preflight
  if (method === 'OPTIONS') {
    res.writeHead(200, corsHeaders);
    res.end();
    return;
  }

  console.log(`${method} ${url}`);

  // Parse URL
  const urlParts = url.split('/');
  const routeKey = `${method} ${url}`;
  const configRouteKey = `${method} /api/configurations`;
  const configRouteKeyWithId = `${method} /api/configurations/`;

  try {
    // Check for exact route match (including file save endpoint)
    if (routes[routeKey]) {
      routes[routeKey](req, res);
    } else if (routes[configRouteKey] && url === '/api/configurations') {
      // Configuration routes - exact match
      routes[configRouteKey](req, res);
    } else if (routes[configRouteKeyWithId] && url.startsWith('/api/configurations/')) {
      // Configuration routes with ID parameter
      const id = urlParts[3];
      if (id) {
        routes[configRouteKeyWithId](req, res, id);
      } else {
        sendError(res, 'ID parameter required', 400);
      }
    } else {
      sendError(res, 'Route not found', 404);
    }
  } catch (err) {
    console.error('Server error:', err);
    sendError(res, 'Internal server error', 500);
  }
});

server.listen(PORT, () => {
  console.log(`🚀 Database server running at http://localhost:${PORT}`);
  console.log(`📊 Available endpoints:`);
  console.log(`   GET    /api/system/info          - Get system information and paths`);
  console.log(`   POST   /api/files/save           - Save uploaded file to disk`);
  console.log(`   GET    /api/tools                - Get all available tools`);
  console.log(`   GET    /api/configurations        - List all configurations`);
  console.log(`   GET    /api/configurations/:id    - Get configuration by ID`);
  console.log(`   POST   /api/configurations        - Create/update configuration`);
  console.log(`   DELETE /api/configurations/:id    - Delete configuration`);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\\n🔄 Shutting down database server...');
  db.close();
  process.exit(0);
});