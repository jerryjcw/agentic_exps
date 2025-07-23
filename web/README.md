# Agent Workflow Runner Web UI

A comprehensive web interface for creating, managing, and executing agent workflow configurations.

## Quick Start

### 1. Install Dependencies
```bash
cd web
npm install
```

### 2. Start the Servers

You need to run **TWO servers** for the application to work properly:

#### Database Server (Port 3001)
```bash
# Start the database server in one terminal
node database-server.cjs
```

#### Frontend Development Server (Port 5173)
```bash
# Start the React dev server in another terminal
npm run dev
```

### 3. Access the Application
- Frontend UI: `http://localhost:5173`
- Database API: `http://localhost:3001`

**Important**: Both servers must be running for the "Load Configuration" tab to work properly. If configurations don't show up, verify the database server is running on port 3001.

## Features

### 1. Create Configuration
- Visual nested list interface for building agent workflows
- Support for SequentialAgent, LoopAgent, ParallelAgent, and base Agent types
- File upload functionality with absolute path management
- Real-time JSON configuration conversion
- System prompt configuration

### 2. Save Configuration
- SQLite database storage for configurations
- Metadata tracking (author, creation date, version, etc.)
- Configuration name uniqueness validation
- Automatic versioning for updates

### 3. Load Configuration
- Browse all saved configurations with metadata
- Preview configuration details and JSON structure
- Load configurations back into the editor for modification
- Delete unwanted configurations

### 4. Execute Configuration
- Configurable REST API endpoint for workflow execution
- Real-time execution status and results
- Error handling and display
- Configuration summary before execution

## Available Scripts

```bash
# Install dependencies
npm install

# Start development server (frontend only)
npm run dev

# Start database server (run in separate terminal) 
node database-server.cjs

# Build for production
npm run build

# Preview production build
npm run preview

# Run type checking
npm run typecheck

# Run linting
npm run lint
```

## Architecture

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: Node.js with SQLite database
- **File Storage**: Local filesystem with base64 encoding for content
- **API**: RESTful endpoints for configuration and file management

## File Structure

```
web/
├── src/
│   ├── components/          # React components
│   │   ├── ConfigBuilder.tsx    # Main configuration builder
│   │   ├── AgentForm.tsx        # Individual agent forms
│   │   ├── LoadConfiguration.tsx # Configuration loading interface
│   │   └── ...
│   ├── utils/              # Utility functions
│   │   ├── configConverter.ts   # Convert UI data to API format
│   │   ├── fileHandler.ts       # File upload and processing
│   │   ├── database.ts          # Database API functions
│   │   └── ...
│   └── types/              # TypeScript type definitions
├── database-server.cjs     # SQLite database server
├── configurations.db       # SQLite database file (created automatically)
└── uploaded_files/         # File storage directory (created automatically)
```

## Usage Guide

### Navigation
The UI provides 4 main functions accessible through the top navigation:
- **Create Configuration**: Build and edit workflows
- **Save Configuration**: Save workflows to database
- **Load Configuration**: Browse and load saved workflows
- **Execute Configuration**: Run workflows via API

### Creating Workflows
1. **Set System Prompt**: Enter the orchestration prompt
2. **Add Root Agents**: Only SequentialAgent, LoopAgent, ParallelAgent allowed at root
3. **Configure Agents**: Set names, models, instructions, descriptions
4. **Add Files**: Upload input files with absolute path tracking
5. **Select Tools**: Choose from available tools (earnings, deckbuilder)

### Agent Properties
- **Name**: Unique identifier for the agent
- **Model**: AI model to use (gpt-4o, gpt-4.1)
- **Instruction**: Prompt/task for the agent
- **Description**: Brief description of the agent's purpose
- **Output Key**: Key for storing agent results (defaults to agent name)
- **Input Files**: Files to be processed by the agent
- **Tools**: Available tools (earnings, deckbuilder)

### File Management
- **Upload & Read Files**: Select files through browser file picker
- **File Processing**: Automatic content reading and base64 encoding
- **File Types**: Supports both text and binary files (.pdf, .doc, .txt, etc.)
- **Storage**: Files are stored with absolute paths for API compatibility

### Example Workflow Structure
```
Sequential Agent: "Code Analysis Workflow"
├── Agent: "Code Parser" 
├── Parallel Agent: "Analysis Tasks"
│   ├── Agent: "Security Analyzer"
│   └── Agent: "Performance Analyzer"
└── Agent: "Report Generator"
```

## API Integration

The UI generates JSON configurations compatible with the backend workflow runner:

```json
{
  "template_config": {
    "template_content": "System prompt here..."
  },
  "job_config": {
    "agents": [...],
    "input_files": [...]
  }
}
```

## Database Schema

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

## API Endpoints

The database server provides these endpoints:

- `GET /api/configurations` - List all configurations
- `GET /api/configurations/:id` - Get configuration by ID
- `POST /api/configurations` - Create/update configuration
- `DELETE /api/configurations/:id` - Delete configuration
- `POST /api/files/save` - Save uploaded file to disk

## Troubleshooting

### Common Issues

1. **"Load Configuration" tab shows nothing**:
   - ✅ **Solution**: Start the database server: `node database-server.cjs`
   - The frontend needs the API server running on port 3001

2. **Files not uploading**:
   - Check that the database server is running
   - Verify the `/uploaded_files` directory exists (created automatically)

3. **Port conflicts**:
   - Database server uses port 3001
   - Frontend dev server uses port 5173
   - Kill existing processes: `lsof -ti:3001 | xargs kill -9`

4. **Database connection errors**:
   - Check SQLite database file permissions
   - Database file is created automatically in the web directory

### Development Tips

- Use browser developer tools to inspect network requests
- Check console for error messages
- Verify both servers are running before testing
- Test with different file types and sizes

## Production Deployment

For production deployment:

1. Build the frontend:
   ```bash
   npm run build
   ```

2. Configure environment variables for production API endpoints
3. Set up proper file storage and database persistence
4. Implement authentication and authorization
5. Add input validation and sanitization
6. Use a process manager like PM2 for the database server