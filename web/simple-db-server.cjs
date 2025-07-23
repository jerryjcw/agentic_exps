#!/usr/bin/env node

const http = require('http');
const Database = require('better-sqlite3');
const path = require('path');

const PORT = 3001;
const DB_PATH = path.join(process.cwd(), 'configurations.db');

console.log('Initializing database at:', DB_PATH);

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

console.log('Database initialized successfully');

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Content-Type': 'application/json'
};

function sendJSON(res, data, statusCode = 200) {
  res.writeHead(statusCode, corsHeaders);
  res.end(JSON.stringify(data));
}

function sendError(res, message, statusCode = 400) {
  sendJSON(res, { error: message }, statusCode);
}

const server = http.createServer(async (req, res) => {
  const { method, url } = req;
  
  console.log(`${method} ${url}`);
  
  // Handle CORS preflight
  if (method === 'OPTIONS') {
    res.writeHead(200, corsHeaders);
    res.end();
    return;
  }

  try {
    if (url === '/api/configurations' && method === 'GET') {
      // Get all configurations
      const stmt = db.prepare('SELECT * FROM configurations ORDER BY last_modified DESC');
      const configurations = stmt.all();
      sendJSON(res, configurations);
      
    } else if (url.startsWith('/api/configurations/') && method === 'GET') {
      // Get configuration by ID
      const id = parseInt(url.split('/')[3]);
      const stmt = db.prepare('SELECT * FROM configurations WHERE id = ?');
      const config = stmt.get(id);
      
      if (!config) {
        sendError(res, 'Configuration not found', 404);
        return;
      }
      
      sendJSON(res, config);
      
    } else if (url === '/api/configurations' && method === 'POST') {
      // Create/update configuration
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', () => {
        try {
          const data = JSON.parse(body);
          const { name, description, author, configuration_data, system_prompt } = data;

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
          console.error('POST error:', err);
          sendError(res, err.message, 500);
        }
      });
      
    } else if (url.startsWith('/api/configurations/') && method === 'DELETE') {
      // Delete configuration
      const id = parseInt(url.split('/')[3]);
      const stmt = db.prepare('DELETE FROM configurations WHERE id = ?');
      const result = stmt.run(id);
      
      if (result.changes === 0) {
        sendError(res, 'Configuration not found', 404);
        return;
      }
      
      sendJSON(res, { success: true });
      
    } else {
      sendError(res, 'Route not found', 404);
    }
  } catch (err) {
    console.error('Server error:', err);
    sendError(res, 'Internal server error', 500);
  }
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`🚀 Database server running at http://127.0.0.1:${PORT}`);
});

process.on('SIGINT', () => {
  console.log('\\nShutting down database server...');
  db.close();
  process.exit(0);
});