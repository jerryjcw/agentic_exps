# Test Suite for Agentic Experiments

This directory contains comprehensive tests for the agentic experiments project, organized using the unittest framework.

## Test Organization

### Test Modules

1. **`test_langchain_wrapper.py`** - Unit tests for LangChain wrapper
   - Wrapper creation and configuration
   - Message conversion between formats
   - `_maybe_append_user_content` functionality
   - Basic integration with LangChain models

2. **`test_integration.py`** - Integration tests with Google ADK
   - Simple agent functionality
   - Conversation memory
   - Tool integration (when tools are available)

3. **`test_model_comparison.py`** - Comparison tests between LiteLlm and LangChain wrapper
   - Response consistency
   - Conversation memory consistency
   - Tool usage consistency
   - Response quality metrics

## Running Tests

### Quick Start

```bash
# Run all tests
python tests/run_tests.py

# Run specific test suites
python tests/run_tests.py wrapper
python tests/run_tests.py integration
python tests/run_tests.py comparison

# Run multiple specific suites
python tests/run_tests.py wrapper integration

# Check test environment
python tests/run_tests.py --check-env

# Run with different verbosity levels
python tests/run_tests.py --quiet      # Minimal output
python tests/run_tests.py --verbose    # Detailed output
```

### Using unittest directly

```bash
# Run all tests
python -m unittest discover tests

# Run specific test module
python -m unittest tests.test_langchain_wrapper

# Run specific test class
python -m unittest tests.test_langchain_wrapper.TestLangChainWrapperCreation

# Run specific test method
python -m unittest tests.test_langchain_wrapper.TestLangChainWrapperCreation.test_wrapper_creation_without_api_key
```

## Test Environment Requirements

### Required Dependencies

- **Google ADK** - Core framework for agents
- **LangChain** - For LangChain wrapper functionality
- **OpenAI API Key** - For integration tests (set `OPENAI_API_KEY` environment variable or place in `config/apikey` file)

### Optional Dependencies

- **Tools** - For tool integration tests (from `tools.gadk.tools`)
- **DuckDuckGo Search** - For search tool functionality

### Environment Setup

1. **API Key**: Set up your OpenAI API key in one of these ways:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
   OR place it in `config/apikey` file

2. **Dependencies**: Ensure all required packages are installed:
   ```bash
   pip install google-adk langchain langchain-openai
   ```

## Test Categories

### Unit Tests
- Fast, isolated tests
- Mock external dependencies
- Test individual components

### Integration Tests
- Test component interactions
- Require real API connections
- Test end-to-end workflows

### Comparison Tests
- Compare behavior between different implementations
- Ensure consistency between LiteLlm and LangChain wrapper
- Validate feature parity

## Test Patterns

### Skipping Tests
Tests automatically skip when dependencies are unavailable:
- Missing API key → Integration tests skipped
- Missing LangChain → Wrapper tests skipped
- Missing tools → Tool tests skipped

### Async Tests
Many tests use asyncio for Google ADK integration:
```python
def test_something(self):
    async def _test():
        # Your async test code here
        pass
    
    asyncio.run(_test())
```

### Subtest Pattern
For testing multiple scenarios:
```python
test_cases = [("query1", "expected1"), ("query2", "expected2")]
for query, expected in test_cases:
    with self.subTest(query=query):
        result = test_function(query)
        self.assertEqual(result, expected)
```

## Adding New Tests

### Creating a New Test Module

1. Create `test_your_module.py` in the `tests/` directory
2. Import required testing utilities:
   ```python
   import unittest
   import asyncio  # If needed for Google ADK
   ```
3. Add your test module to `TEST_MODULES` in `run_tests.py`

### Test Class Structure
```python
class TestYourFeature(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        pass
    
    def tearDown(self):
        """Clean up after each test method."""
        pass
    
    def test_specific_functionality(self):
        """Test a specific piece of functionality."""
        pass
```

### Best Practices

1. **Descriptive Test Names**: Use clear, descriptive test method names
2. **Single Responsibility**: Each test should test one specific behavior
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Use Subtests**: For testing multiple similar scenarios
5. **Skip Appropriately**: Skip tests when dependencies unavailable
6. **Clean Assertions**: Use specific assertion methods

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure project paths are properly set up
2. **API Rate Limits**: Tests may fail due to API rate limiting
3. **Network Issues**: Integration tests require internet connectivity
4. **Missing Dependencies**: Check that all required packages are installed

### Debugging Tips

1. **Run Single Tests**: Use specific test methods to isolate issues
2. **Increase Verbosity**: Use `--verbose` flag for detailed output
3. **Check Environment**: Use `--check-env` to verify setup
4. **Check Logs**: Look for detailed error messages in test output

## Contributing

When adding new features:

1. Add corresponding unit tests
2. Add integration tests if the feature interacts with external systems
3. Update comparison tests if the feature affects model behavior
4. Update this README if adding new test categories or patterns