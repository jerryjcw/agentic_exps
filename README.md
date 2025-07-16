# Agentic Experiments

A comprehensive framework for building and experimenting with intelligent agents using Google ADK (Agent Development Kit), featuring flexible multi-file processing capabilities and multiple LLM integrations.

## 🏗️ Project Structure

```
agentic_exps/
├── api/                        # FastAPI server components
│   ├── main.py                 # FastAPI server
│   ├── models.py               # Pydantic request/response models
│   ├── example_client.py       # Example API client
│   └── run_example.py          # Complete example runner
├── core/                       # Core framework components
│   ├── flexible_agents.py      # Main flexible agent framework
│   ├── agent.py                # Agent utilities
│   ├── sequential_agents.py    # Sequential processing agents
│   └── ...
├── config/                     # Configuration files
│   ├── agent/                  # Agent configurations (JSON/YAML)
│   ├── job/                    # Job configurations
│   └── template/               # Jinja2 templates
├── tests/                      # Comprehensive test suite
├── wrapper/                    # LLM wrapper implementations
├── tools/                      # Agent tools and utilities
├── agent_io/                   # Agent I/O operations
├── data_model/                 # Data models and validation
└── utils/                      # Utility functions
```

## 🚀 Key Features

### Flexible Agent Framework
- **Multi-file Processing**: Process multiple input files with individual type specifications
- **Template-driven Queries**: Jinja2 template synthesis for dynamic content generation
- **Configurable Workflows**: YAML/JSON configuration for agent behavior
- **Execution Tracking**: Comprehensive step-by-step execution monitoring
- **Multiple Output Formats**: Text and JSON output with detailed metadata

### API Server
- **FastAPI Server**: RESTful API for running flexible agent workflows
- **Real-time Execution**: Run workflows via HTTP POST requests
- **Complete Results**: Returns full execution results, output files, and metadata
- **Interactive Documentation**: Built-in Swagger UI and OpenAPI spec
- **Health Monitoring**: Health check endpoints for service monitoring

### LLM Integrations
- **Google ADK Integration**: Native Google Agent Development Kit support
- **LangChain Wrapper**: Full LangChain ecosystem compatibility
- **OpenAI Integration**: Direct OpenAI API integration
- **Multi-model Support**: Switch between different LLM providers

### Agent Capabilities
- **Sequential Agents**: Step-by-step processing workflows
- **Parallel Agents**: Concurrent execution for performance
- **Loop Agents**: Iterative processing with conditions
- **Tool Integration**: Weather, financial data, and custom tools
- **Memory Management**: Conversation history and context preservation

## 🛠️ Quick Start

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd agentic_exps
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API keys**:
   Create a `.env` file in the project root:
   ```bash
   OPENAI_API_KEY=your_openai_key_here
   GOOGLE_API_KEY=your_google_key_here
   ```

### Basic Usage

1. **Run a flexible agent workflow (CLI)**:
   ```bash
   python core/flexible_agents.py --job_name simple_code_improvement
   ```

2. **Run the API server**:
   ```bash
   cd api
   python main.py
   ```
   The server will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`

3. **Run tests**:
   ```bash
   python -m unittest discover tests
   ```

## 📋 Configuration

### Job Configuration

Configure your agent workflows using YAML files in `config/job/yaml_examples/`:

```yaml
job_name: "MyAgentWorkflow"
job_description: "Process multiple files with custom analysis"

input_config:
  input_files:
    - input_path: "file1.py"
      input_type: "python"
    - input_path: "file2.md"
      input_type: "markdown"

analysis_config:
  template_config_path: "config/template/my_template.yaml"

output_config:
  output_directory: "output"
  file_naming: "agent_execution_{input_filename}_{timestamp}"
```

### Agent Configuration

Define agent behavior in `config/agent/yaml_examples/`:

```yaml
name: "MyAgent"
type: "LlmAgent"
model: "gpt-4o"
instructions: "Analyze the provided content and generate insights"
tools:
  - "weather_tool"
  - "current_time_tool"
```

## 🔧 Core Components

### Flexible Agents (`core/flexible_agents.py`)
The main framework for creating and running flexible agents with:
- Multi-file input processing
- Template-based query generation
- Configurable execution workflows
- Comprehensive result tracking

### LLM Wrappers (`wrapper/`)
- **LangChain Wrapper**: Integration with LangChain ecosystem
- **OpenAI Wrapper**: Direct OpenAI API integration
- Message format conversion between different LLM providers

### Tools (`tools/gadk/`)
Built-in tools for agent capabilities:
- **Weather Tools**: Real-time weather information
- **Financial Tools**: Market data and company information
- **Debug Tools**: Development and testing utilities

## 🧪 Testing

The project includes a comprehensive test suite covering:

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Wrapper Tests**: LLM wrapper functionality
- **Tool Tests**: Agent tool capabilities

Run specific test categories:
```bash
# Run all tests
python -m unittest discover tests

# Run specific test modules
python -m unittest tests.test_langchain_wrapper
python -m unittest tests.test_integration
```

## 📚 Templates

Create dynamic queries using Jinja2 templates in `config/template/`:

```yaml
template_content: |
  Analyze the following files:
  
  {% for i in range(file_name|length) %}
  ## File {{ loop.index }}: {{ file_name[i] }}
  Type: {{ file_type[i] }}
  
  Content:
  ```{{ file_type[i] }}
  {{ file_content[i] }}
  ```
  {% endfor %}
```

## 🔍 Examples

### Process Multiple Files (CLI)
```python
from core.flexible_agents import main_async

# Configure input files in job config
input_files = [
    {"input_path": "src/main.py", "input_type": "python"},
    {"input_path": "docs/README.md", "input_type": "markdown"}
]

# Run agent workflow
await main_async("my_workflow")
```

### API Usage Example
```python
import requests

# Example configuration contents
job_config = """
job_name: "SimpleCodeImprovementAnalysis"
input_config:
  input_files:
    - input_path: "core/gpt_caller.py"
      input_type: "text"
# ... rest of job config
"""

agent_config = """
name: "SimpleCodeImprovementWorkflow"
class: "SequentialAgent"
sub_agents:
  - name: "CodeAnalysisAgent"
    model: "openai/gpt-4o"
# ... rest of agent config
"""

template_config = """
template_content: |
  Please analyze the following code for improvements:
  # ... rest of template config
"""

# Call the API
response = requests.post(
    "http://localhost:8000/workflow/run",
    json={
        "job_config": job_config,
        "agent_config": agent_config,
        "template_config": template_config
    }
)

result = response.json()
print(f"Status: {result['status']}")
print(f"Output file: {result['output_file']}")
print(f"Events generated: {result['events_generated']}")
```

### Custom Agent with Tools
```yaml
name: "WeatherAnalyst"
type: "LlmAgent"
model: "gpt-4o"
instructions: "Provide weather analysis and recommendations"
tools:
  - name: "weather_tool"
    description: "Get current weather for any location"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run the test suite: `python -m unittest discover tests`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🚀 Recent Updates

- **FastAPI Server**: Added REST API server for running workflows via HTTP
- **Enhanced Results**: Improved return values with complete execution results
- **API Documentation**: Integrated API documentation with examples
- **v2.0**: Renamed `basics/` to `core/` for better organization
- **Multi-file Support**: Added support for processing multiple input files
- **Template Engine**: Enhanced Jinja2 template system for dynamic queries
- **Improved Testing**: Comprehensive test suite with 70+ tests
- **Better Documentation**: Updated documentation and examples
- **Optimized Logging**: Reduced verbose logging for better performance

## 🔧 Development

### Project Philosophy
This project focuses on:
- **Flexibility**: Adaptable to different use cases and requirements
- **Modularity**: Clean separation of concerns and reusable components
- **Reliability**: Comprehensive testing and error handling
- **Performance**: Optimized execution and resource usage
- **Usability**: Clear documentation and intuitive APIs

### Architecture
The framework follows a modular architecture with:
- **Core Framework**: Central agent execution engine
- **Configuration Layer**: YAML/JSON-based configuration system
- **Integration Layer**: Multiple LLM provider support
- **Tool Ecosystem**: Extensible tool system
- **Testing Framework**: Comprehensive test coverage