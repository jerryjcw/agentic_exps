# Agent Workflow Studio

A comprehensive web interface for creating, managing, and executing agent workflow configurations with visual workflow building, file management, and real-time execution monitoring.

## 🚀 Quick Start

### Prerequisites
- Node.js (v16 or higher)
- npm (comes with Node.js)

### Installation

1. **Navigate to the web directory**:
   ```bash
   cd web
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

### Running the Application

**⚠️ IMPORTANT**: You need to run **TWO servers** simultaneously for the application to work properly.

#### Method 1: Start Both Servers Manually

**Terminal 1 - Database Server (Port 3001)**:
```bash
cd web
node database-server.cjs
```

**Terminal 2 - Frontend Server (Port 5173)**:
```bash
cd web
npm run dev
```

#### Method 2: Start Both Servers with One Command

```bash
cd web
npm run start:full
```

This runs both servers concurrently in a single terminal.

### Accessing the Application

- **Frontend UI**: [http://localhost:5173](http://localhost:5173)
- **Database API**: [http://localhost:3001](http://localhost:3001)

### Verification

✅ **Success indicators**:
- Frontend loads at localhost:5173
- "Load Configuration" tab shows saved configurations (may be empty initially)
- No console errors in browser developer tools

❌ **If something's wrong**:
- Check both terminals for error messages
- Verify both ports (3001, 5173) are free
- See [Troubleshooting](#troubleshooting) section below

## 🔄 Restart Instructions

### Complete Restart
```bash
# Stop all processes (Ctrl+C in terminals)
# Then restart both servers:
cd web
npm run start:full
```

### Restart Individual Servers

**Database Server Only**:
```bash
# Stop with Ctrl+C, then:
cd web
node database-server.cjs
```

**Frontend Server Only**:
```bash
# Stop with Ctrl+C, then:
cd web
npm run dev
```

### Force Restart (if ports are stuck)
```bash
# Kill processes on the ports
lsof -ti:3001 | xargs kill -9  # Database server
lsof -ti:5173 | xargs kill -9  # Frontend server

# Then restart
cd web
npm run start:full
```

## ✨ Features

### 1. Create Configuration
- **Internal Models Switch**: Toggle between OpenAI (`openai/gpt-4o`) and Internal (`internal/gpt-4o`) model endpoints
- Visual nested list interface for building agent workflows
- Support for SequentialAgent, LoopAgent, ParallelAgent, and base Agent types
- File upload functionality with automatic path management
- Real-time JSON configuration conversion
- System prompt configuration
- Auto-resizing input fields based on content length

### 2. Save Configuration
- SQLite database storage for configurations
- Metadata tracking (author, creation date, version, etc.)
- Configuration name uniqueness validation
- Automatic versioning for updates

### 3. Load Configuration
- Browse all saved configurations with searchable metadata
- Modal overlay for configuration preview and details
- Load configurations back into the editor for modification
- Delete unwanted configurations with confirmation
- Scrollable content with custom scrollbars

### 4. Execute Configuration
- Configurable REST API endpoint (default: `http://localhost:8000/workflow/run`)
- **Enhanced Result Display**: Beautiful, human-readable JSON formatting
- Copy and download execution results
- Real-time execution status and error handling
- Configuration summary before execution

## 📋 Available Scripts

```bash
# Install dependencies
npm install

# Start both servers (recommended)
npm run start:full

# Start development server (frontend only)
npm run dev

# Start database server only (run in separate terminal) 
node database-server.cjs

# Alternative database server commands
npm run db:start        # Port 3001
npm run db:start:3001    # Port 3001

# Build for production
npm run build

# Preview production build
npm run preview

# Run linting
npm run lint
```

## 🏗️ Architecture

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: Node.js with SQLite database
- **File Storage**: Local filesystem with base64 encoding for content
- **API**: RESTful endpoints for configuration and file management
- **Styling**: Custom scrollbars, responsive design, smooth animations

## 📁 File Structure

```
web/
├── src/
│   ├── components/          # React components
│   │   ├── ConfigBuilder.tsx    # Main configuration builder with Internal Models switch
│   │   ├── AgentForm.tsx        # Individual agent forms with auto-resize inputs
│   │   ├── LoadConfiguration.tsx # Configuration loading with modal overlay
│   │   ├── ExecuteConfiguration.tsx # Enhanced execution with beautiful result display
│   │   └── ...
│   ├── utils/              # Utility functions
│   │   ├── configConverter.ts   # Convert UI data to API format (supports internal models)
│   │   ├── fileHandler.ts       # File upload and processing
│   │   ├── database.ts          # Database API functions
│   │   └── ...
│   ├── types/              # TypeScript type definitions
│   └── index.css           # Custom styles including scrollbars
├── database-server.cjs     # SQLite database server
├── configurations.db       # SQLite database file (created automatically)
├── uploaded_files/         # File storage directory (created automatically)
└── package.json           # Dependencies and scripts
```

## 📖 Usage Guide

### Navigation
The UI provides 4 main tabs accessible through the top navigation:
- **Create Configuration**: Build and edit workflows
- **Save Configuration**: Save workflows to database
- **Load Configuration**: Browse and load saved workflows
- **Execute Configuration**: Run workflows via API

### Creating Workflows

1. **Internal Models Switch**: Toggle at the top to use internal vs OpenAI model endpoints
2. **Set System Prompt**: Enter the orchestration prompt (auto-resizing textarea)
3. **Add Root Agents**: Choose from SequentialAgent, LoopAgent, ParallelAgent (horizontal icon guide)
4. **Configure Agents**: Set names, models, instructions, descriptions (auto-resizing inputs)
5. **Add Files**: Upload input files with automatic content processing
6. **Select Tools**: Choose from available tools

### Agent Types & Icons
- **SequentialAgent** (→): Execute agents in sequence
- **LoopAgent** (↻): Repeat execution with max iterations
- **ParallelAgent** (‖): Execute agents concurrently
- **Agent** (•): Base agent for individual tasks

### File Management
- **Upload & Read Files**: Select files through browser file picker
- **File Processing**: Automatic content reading and base64 encoding
- **File Types**: Supports both text and binary files (.pdf, .doc, .txt, .py, .js, etc.)
- **Storage**: Files stored with correct paths for API compatibility

### Example Workflow Structure
```
Sequential Agent: "Code Analysis Workflow"
├── Agent: "Code Parser" 
├── Parallel Agent: "Analysis Tasks"
│   ├── Agent: "Security Analyzer"
│   └── Agent: "Performance Analyzer"
└── Agent: "Report Generator"
```

## 🔧 API Integration

The UI generates JSON configurations compatible with the backend workflow runner:

```json
{
  "job_config": {
    "job_name": "WebUIWorkflow",
    "job_description": "Workflow created from Web UI",
    "input_config": {
      "input_files": [...],
      "preview_length": 500
    },
    "execution_config": {
      "track_execution_steps": true,
      "display_progress": true,
      "log_level": "INFO"
    }
  },
  "agent_config": {
    "name": "MainAgent",
    "class": "SequentialAgent",
    "module": "google.adk.agents",
    "sub_agents": [...]
  },
  "template_config": {
    "template_name": "Web UI Workflow Template",
    "template_content": "System prompt here..."
  }
}
```

### Model Endpoints
- **Internal Models OFF**: `"model": "openai/gpt-4o"`
- **Internal Models ON**: `"model": "internal/gpt-4o"`

## 🗄️ Database Schema

Configurations are stored in SQLite with the following structure:

```sql
CREATE TABLE configurations (
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
```

## 🌐 API Endpoints

The database server provides these endpoints:

- `GET /api/configurations` - List all configurations
- `GET /api/configurations/:id` - Get configuration by ID
- `POST /api/configurations` - Create/update configuration
- `DELETE /api/configurations/:id` - Delete configuration
- `POST /api/files/save` - Save uploaded file to disk
- `GET /api/system/info` - Get system information

## 🔍 Troubleshooting

### Common Issues

1. **"Load Configuration" tab shows nothing**:
   ```bash
   # ✅ Solution: Start the database server
   cd web
   node database-server.cjs
   ```
   - The frontend needs the API server running on port 3001

2. **Internal Models switch not visible**:
   - Refresh the page after starting servers
   - Check browser console for JavaScript errors
   - Switch should appear at the top of Create Configuration tab

3. **Files not uploading**:
   - Ensure database server is running
   - Check that `/uploaded_files` directory exists (created automatically)
   - Verify file permissions

4. **Port conflicts**:
   ```bash
   # Kill existing processes
   lsof -ti:3001 | xargs kill -9  # Database server
   lsof -ti:5173 | xargs kill -9  # Frontend server
   ```

5. **Database connection errors**:
   - Check SQLite database file permissions
   - Database file is created automatically in the web directory
   - Restart database server if needed

6. **Execution results not showing properly**:
   - Verify API endpoint is correct (default: `http://localhost:8000/workflow/run`)
   - Check if backend workflow runner is running
   - Look for CORS issues in browser console

### Development Tips

- **Check both servers are running**: Both terminals should show no errors
- **Use browser developer tools**: Check console for error messages
- **Network tab**: Inspect API requests and responses
- **Test incrementally**: Start with simple configurations
- **File uploads**: Test with different file types and sizes

### Restart Checklist

When restarting the application:

1. ✅ Stop all processes (Ctrl+C in terminals)
2. ✅ Clear any port conflicts if needed
3. ✅ Navigate to web directory: `cd web`
4. ✅ Start both servers: `npm run start:full` or manually
5. ✅ Verify frontend loads at localhost:5173
6. ✅ Test Load Configuration tab to confirm database connectivity
7. ✅ Check browser console for any errors

## 🚀 Production Deployment

For production deployment:

1. **Build the frontend**:
   ```bash
   npm run build
   ```

2. **Configure environment variables** for production API endpoints
3. **Set up proper file storage** and database persistence
4. **Implement authentication** and authorization
5. **Add input validation** and sanitization
6. **Use a process manager** like PM2 for the database server
7. **Configure reverse proxy** (nginx/Apache) for proper routing
8. **Set up HTTPS** for secure communication

## 🆘 Need Help?

If you encounter issues:

1. **Check this README** for troubleshooting steps
2. **Verify installation** steps were followed correctly
3. **Check terminal outputs** for error messages
4. **Test with a fresh installation** in a new directory
5. **Ensure Node.js version** is 16 or higher

---

**Happy workflow building!** 🎉