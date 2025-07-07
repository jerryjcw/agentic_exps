# Test Suite for Agentic Experiments

This directory contains comprehensive tests for the agentic experiments project, organized using the unittest framework with automatic test discovery.

## Test Organization

### Current Test Modules

1. **`test_agent_utils.py`** - Agent utility functions testing
   - `collect_agent_execution_steps()` functionality
   - `display_execution_steps_summary()` testing
   - ExecutionStep creation and management
   - Complex agent hierarchy handling
   - Edge case testing and integration

2. **`test_code_improvement_execution.py`** - Code improvement workflow testing
   - Agent properties validation
   - Agent structure validation
   - Configuration to execution pipeline
   - Workflow instantiation
   - Mock execution context preparation

3. **`test_comprehensive_parameters.py`** - Agent parameter testing
   - Agents with all supported parameters
   - Financial tools integration
   - Loop agents with max_iterations
   - Nested agents with comprehensive parameters
   - Parallel agents with descriptions
   - Sequential agents with output_key

4. **`test_data_models.py`** - Data model validation testing
   - Configuration file validation (8 configs tested)
   - Agent hierarchy validation
   - Tool configuration validation
   - Invalid configuration rejection
   - Code improvement workflow validation
   - Financial analysis workflow validation

5. **`test_integration.py`** - Google ADK integration testing
   - Simple agent functionality
   - Mathematical query processing
   - Conversation memory testing
   - Tool integration (current_time_tool, temperature_tool)
   - Name memory persistence

6. **`test_langchain_wrapper.py`** - LangChain wrapper unit tests
   - Wrapper creation and configuration
   - Message conversion between Google ADK and LangChain formats
   - `_maybe_append_user_content` functionality
   - Basic integration with LangChain models
   - Custom parameter handling

7. **`test_maybe_append_user_content.py`** - Dedicated `_maybe_append_user_content` testing
   - Comprehensive scenario testing for both LangChain and OpenAI wrappers
   - Empty contents list handling
   - Assistant vs user message handling
   - Cross-wrapper functionality validation

8. **`test_model_comparison.py`** - LiteLLM vs LangChain wrapper comparison
   - Response consistency between implementations
   - Creative vs factual response handling
   - Conversation memory consistency
   - Response length consistency validation

9. **`test_openai_wrapper.py`** - OpenAI wrapper testing
   - Wrapper creation and configuration
   - Message conversion and handling
   - API integration when available

## Running Tests

### Primary Method - Unittest Auto Discovery

```bash
# Run all tests (recommended)
python -m unittest discover tests

# Run all tests with verbose output
python -m unittest discover tests -v

# Run specific test module
python -m unittest tests.test_langchain_wrapper

# Run specific test class
python -m unittest tests.test_agent_utils.TestCollectAgentExecutionSteps

# Run specific test method
python -m unittest tests.test_langchain_wrapper.TestLangChainWrapperCreation.test_wrapper_creation_without_api_key
```

### Alternative Methods

```bash
# Run from project root
cd /path/to/agentic_exps
python -m unittest discover tests

# Run with pattern matching
python -m unittest discover tests -p "test_*.py"

# Run with start directory
python -m unittest discover -s tests -p "test_*.py"
```

## Test Environment Requirements

### Required Dependencies

- **Google ADK** - Core framework for agents
- **LangChain** - For LangChain wrapper functionality  
- **LiteLLM** - For model comparison tests
- **Jinja2** - For template processing tests
- **PyYAML** - For configuration file testing

### Optional Dependencies

- **OpenAI API Key** - For integration tests with real models
- **Tools** - For tool integration tests (weather, financial data)
- **Network Access** - For API-based integration tests

### Environment Setup

1. **API Key Setup** (for integration tests):
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
   OR place it in `config/apikey` file

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Test Categories

### Unit Tests (Fast, Isolated)
- **Agent Utils**: Testing utility functions
- **Data Models**: Configuration validation
- **Wrapper Creation**: LLM wrapper instantiation
- **Message Conversion**: Format conversion testing

### Integration Tests (Require External APIs)
- **Google ADK Integration**: End-to-end agent workflows
- **LLM Model Integration**: Real API calls to language models
- **Tool Integration**: Weather, time, and other external tools

### Validation Tests (Configuration & Structure)
- **Configuration Validation**: YAML/JSON config file testing
- **Agent Structure**: Hierarchy and parameter validation
- **Workflow Testing**: Complete pipeline validation

### Comparison Tests (Cross-Implementation)
- **Model Behavior**: LiteLLM vs LangChain consistency
- **Response Quality**: Consistency metrics across implementations
- **Memory Handling**: Conversation state management

## Test Statistics

**Current Test Coverage**: 70+ individual tests across 9 modules

### Test Distribution
- **Agent Utils Tests**: 19 tests (collection, display, edge cases)
- **Data Model Tests**: 8 configuration files validated
- **Integration Tests**: 5 end-to-end workflow tests
- **LangChain Wrapper Tests**: 8 comprehensive wrapper tests
- **Model Comparison Tests**: 3 cross-implementation tests
- **OpenAI Wrapper Tests**: 7 wrapper-specific tests
- **Maybe Append Tests**: 7 dedicated function tests
- **Code Improvement Tests**: 6 workflow validation tests
- **Comprehensive Parameter Tests**: 6 parameter validation tests

## Test Patterns

### Automatic Skipping
Tests automatically skip when dependencies are unavailable:
```python
@unittest.skipIf(not has_openai_key(), "OpenAI API key not available")
def test_openai_integration(self):
    # Test code here
```

### Async Test Pattern
For Google ADK integration:
```python
def test_agent_functionality(self):
    async def _test():
        # Async test code here
        result = await agent.run(query)
        self.assertIsNotNone(result)
    
    asyncio.run(_test())
```

### Subtest Pattern for Multiple Scenarios
```python
test_cases = [
    ("scenario1", "expected1"),
    ("scenario2", "expected2")
]
for scenario, expected in test_cases:
    with self.subTest(scenario=scenario):
        result = test_function(scenario)
        self.assertEqual(result, expected)
```

### Configuration Validation Pattern
```python
def test_config_validation(self):
    config_files = glob.glob("config/agent/**/*.yaml", recursive=True)
    for config_file in config_files:
        with self.subTest(config=config_file):
            result, warnings = validate_configuration_file(config_file)
            self.assertTrue(result)
```

## Adding New Tests

### Creating a Test Module

1. **Create Test File**: `test_your_feature.py` in `tests/` directory
2. **Import Framework**:
   ```python
   import unittest
   import asyncio  # If testing async functionality
   ```
3. **Follow Naming Convention**: `test_*.py` for auto-discovery

### Test Class Structure
```python
class TestYourFeature(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures, runs before each test method."""
        pass
    
    def tearDown(self):
        """Clean up after each test method."""
        pass
    
    @unittest.skipIf(condition, "Reason for skipping")
    def test_specific_functionality(self):
        """Test a specific piece of functionality."""
        # Arrange
        setup_data = create_test_data()
        
        # Act
        result = function_under_test(setup_data)
        
        # Assert
        self.assertEqual(result, expected_value)
```

### Best Practices

1. **Descriptive Names**: Use clear, descriptive test method names
2. **Single Purpose**: Each test should verify one specific behavior
3. **Arrange-Act-Assert**: Structure tests with clear phases
4. **Use Subtests**: For testing multiple similar scenarios
5. **Proper Skipping**: Skip tests when dependencies unavailable
6. **Specific Assertions**: Use the most specific assertion method available

## Troubleshooting

### Common Issues

1. **Import Errors**: 
   - Ensure you're running from the project root
   - Check that `__init__.py` files exist in test directories
   - Verify Python path includes project directories

2. **API Rate Limits**: 
   - Some integration tests may hit rate limits
   - Consider adding delays between API calls in tests

3. **Missing Dependencies**:
   - Install all requirements: `pip install -r requirements.txt`
   - Check for optional dependencies needed for specific tests

4. **Configuration Issues**:
   - Ensure configuration files exist and are valid
   - Check that the `core/` directory structure is correct

### Debugging Tips

1. **Run Specific Tests**: Isolate issues by running individual test methods
2. **Use Verbose Mode**: Run with `-v` flag for detailed output
3. **Check Test Output**: Look for specific error messages and stack traces
4. **Verify Environment**: Ensure all paths and dependencies are correct

## Continuous Integration

The test suite is designed to work in CI environments:

- **Graceful Degradation**: Tests skip when dependencies unavailable
- **No External Dependencies**: Core tests work without API keys
- **Fast Execution**: Unit tests run quickly for rapid feedback
- **Comprehensive Coverage**: Integration tests validate full workflows

## Contributing

When contributing new features:

1. **Add Unit Tests**: Test individual components in isolation
2. **Add Integration Tests**: Test feature interactions with the system
3. **Update Documentation**: Update this README for new test patterns
4. **Follow Conventions**: Use existing test patterns and naming conventions
5. **Test Edge Cases**: Include boundary conditions and error scenarios

### Test Checklist

- [ ] Unit tests for new functionality
- [ ] Integration tests for API interactions
- [ ] Edge case and error condition testing
- [ ] Documentation updates
- [ ] Proper test skipping for missing dependencies
- [ ] Clear, descriptive test names and docstrings