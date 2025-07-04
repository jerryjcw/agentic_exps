# Agentic Experiments

A comprehensive agent-based AI framework using Google ADK (Agent Development Kit) with LiteLLM for multi-provider LLM support. This project implements flexible, configurable agents that can be orchestrated in various patterns (sequential, parallel, loop) for complex AI workflows.

## 🚀 Features

- **Multi-provider LLM support** via LiteLLM (OpenAI, Anthropic, Google, etc.)
- **Hierarchical agent orchestration** (sequential, parallel, loop patterns)
- **Configuration-driven workflows** with YAML/JSON
- **Real-time execution tracking** with detailed logging
- **Tool ecosystem** for web search, weather, time, and debugging
- **Template-based query generation** with Jinja2
- **Comprehensive testing suite** for reliability

## 📋 Project Structure

```
agentic_exps/
├── basics/                    # Core agent implementations
│   ├── flexible_agents.py     # Configuration-driven agent framework
│   ├── sequential_agents.py   # Weather information pipeline
│   └── agent.py              # Basic agent with tool integration
├── config/                    # Configuration files
│   ├── agent/                 # Agent configurations (YAML/JSON)
│   ├── job/                   # Job execution parameters
│   └── template/              # Jinja2 templates
├── data_model/                # Pydantic validation models
├── agent_io/                  # Agent instantiation logic
├── tools/                     # Reusable tools (search, weather, time)
├── utils/                     # Agent analysis and execution tracking
├── wrapper/                   # LangChain and OpenAI LiteLLM integration
└── tests/                     # Comprehensive test suite
```

## 🛠️ Prerequisites

### Dependencies
```bash
pip install -r requirements.txt
```

### Required API Keys
Create a `.env` file with:
```bash
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_google_key_here  # For search tools
```

## 🎯 Core Agent Programs

### 1. Flexible Agents (`flexible_agents.py`)
**Purpose**: Configuration-driven agent framework for code analysis workflows

**Features**:
- YAML/JSON configuration loading
- Jinja2 template synthesis for dynamic queries
- Multi-stage code improvement pipeline
- Execution tracking and reporting
- Configurable output formats (text/JSON)

**Usage**:
```bash
# Basic code analysis workflow
python basics/flexible_agents.py --job_name simple_code_improvement

# Custom job configuration
python basics/flexible_agents.py --job_name custom_workflow
```

### 2. Sequential Agents (`sequential_agents.py`)
**Purpose**: Weather information pipeline using sequential agent orchestration

**Features**:
- 3-stage pipeline: Geographic search → Weather data → Time information
- Tool integration (Google search, weather API, time zones)
- Interactive and batch processing modes
- Error handling and fallback mechanisms

**Usage**:
```bash
# Interactive weather pipeline
python basics/sequential_agents.py --interactive

# Specific location query
python basics/sequential_agents.py --location "Tokyo, Japan"

# Demo mode with example locations
python basics/sequential_agents.py
```

### 3. Basic Agent (`agent.py`)
**Purpose**: Simple agent with configurable LLM backend and tool integration

**Features**:
- Multiple model backends (OpenAI, via LiteLLM)
- LangChain wrapper support
- Built-in tools (time, weather, search)
- Interactive mode

**Usage**:
```bash
# Simple agent with tools
python basics/agent.py --interactive --with-tools

# Different model backends
python basics/agent.py --model gpt-3.5-turbo --use-langchain

# Custom configuration
python basics/agent.py --model gpt-4 --name MyAgent --interactive
```

## 🧪 Testing

### Test Structure
- **Unit Tests**: Individual component validation
- **Integration Tests**: End-to-end workflow validation
- **Configuration Tests**: YAML/JSON validation and agent instantiation

### Running Tests
```bash
# Run all tests
python -m unittest discover tests/

# Specific test categories
python -m unittest tests.test_data_models
python -m unittest tests.test_integration
python -m unittest tests.test_agent_utils
```

### Test Coverage
- Agent configuration validation
- Model wrapper functionality
- Tool integration
- Execution tracking
- Error handling and edge cases

## 🔧 Configuration System

### Agent Configurations
Define agent hierarchies in `config/agent/yaml_examples/`:
```yaml
name: "SimpleCodeImprovementWorkflow"
class: "SequentialAgent"
module: "google.adk.agents"
description: "A simplified code improvement workflow"

sub_agents:
  - name: "CodeAnalysisAgent"
    class: "Agent"
    module: "google.adk.agents"
    model: "openai/gpt-4o"
    instruction: "Analyze code structure and architecture..."
    output_key: "code_analysis"
```

### Job Configurations
Control execution parameters in `config/job/yaml_examples/`:
```yaml
job_name: "Simple Code Improvement"
agent_config:
  config_path: "config/agent/yaml_examples/simple_code_improvement.yaml"
input_config:
  input_file_path: "agent_io/agent_io.py"
  language: "Python"
```

## 🛡️ Architecture

### Core Components
- **Data Models**: Pydantic validation for agent configurations
- **Agent I/O**: Agent instantiation from configurations  
- **Tools**: Reusable tools for search, weather, time, and debugging
- **Utilities**: Agent analysis, execution tracking, and reporting
- **Wrappers**: LangChain and OpenAI LiteLLM integration

### Agent Orchestration Patterns
1. **Sequential**: Step-by-step execution (A → B → C)
2. **Parallel**: Concurrent execution (A, B, C simultaneously)
3. **Loop**: Iterative execution with max iterations
4. **Hybrid**: Combinations of the above patterns

## 📊 Execution Tracking

The framework provides comprehensive execution tracking:
- Real-time agent status monitoring
- Event generation and logging
- Performance metrics
- Error handling and recovery
- Detailed execution reports

## 🔍 Example Workflows

### Code Analysis Workflow
1. **CodeAnalysisAgent**: Analyzes code structure and architecture
2. **IssueIdentificationParallel**: 
   - SecurityAnalyzer: Identifies security vulnerabilities
   - QualityAnalyzer: Identifies code quality issues
3. **RecommendationSynthesizer**: Creates prioritized improvement recommendations

### Weather Information Pipeline
1. **GeographicSearchAgent**: Finds nearest capital city
2. **WeatherInformationAgent**: Gets current weather data
3. **TimeInformationAgent**: Adds current time information

## 📈 Advanced Features

### Template-Based Query Generation
Use Jinja2 templates for dynamic query generation:
```python
template_vars = {
    'language': 'Python',
    'file_name': 'example.py',
    'code_content': code_content,
    'analysis_focus': ['security', 'performance']
}
```

### Multi-Provider LLM Support
Easily switch between different LLM providers:
```python
# OpenAI GPT-4
model = LiteLlm(model='openai/gpt-4o')

# Anthropic Claude
model = LiteLlm(model='anthropic/claude-3-sonnet-20240229')

# Local models
model = LiteLlm(model='ollama/llama2')
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋 Support

For questions or issues:
1. Check the test files for usage examples
2. Review configuration examples in `config/`
3. Open an issue for bugs or feature requests

---

**Note**: This project demonstrates advanced agent orchestration patterns suitable for complex, multi-step AI workflows with robust configuration management and execution tracking.
