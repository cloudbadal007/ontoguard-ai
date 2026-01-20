# Contributing to OntoGuard

Thank you for your interest in contributing to OntoGuard! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list to see if the bug has already been reported. When creating a bug report, include:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs actual behavior
- Your environment (OS, Python version, OntoGuard version)
- A minimal code example that reproduces the issue

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) when creating a new issue.

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- A clear, descriptive title
- A detailed description of the proposed enhancement
- Use cases and examples
- Any alternatives you've considered

Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md) when creating a new issue.

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest tests/`)
6. Update documentation if needed
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- (Optional) A virtual environment tool (venv, conda, etc.)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/cloudbadal007/ontoguard-ai.git
   cd ontoguard-ai
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install the package in development mode**
   ```bash
   pip install -e .
   ```

4. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

5. **Run tests to verify setup**
   ```bash
   pytest tests/ -v
   ```

## Code Style

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length**: 100 characters (configured in `pyproject.toml`)
- **Type hints**: Required for all function parameters and return values
- **Docstrings**: Use Google-style docstrings

### Formatting

We use `black` for code formatting and `ruff` for linting:

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Auto-fix linting issues
ruff check --fix src/ tests/
```

### Type Checking

We use `mypy` for type checking:

```bash
mypy src/
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/ontoguard --cov-report=html

# Run specific test file
pytest tests/test_validator.py

# Run specific test
pytest tests/test_validator.py::TestValidation::test_validate_allowed_action
```

### Writing Tests

- Write tests for all new functionality
- Follow the existing test patterns
- Use descriptive test names
- Aim for >80% code coverage
- Use fixtures for common setup

### Test Structure

```python
def test_feature_name():
    """Test description."""
    # Arrange
    validator = OntologyValidator("ontology.owl")
    
    # Act
    result = validator.validate(...)
    
    # Assert
    assert result.allowed is True
```

## Documentation

### Docstrings

All public functions, classes, and methods should have docstrings:

```python
def validate_action(
    action: str,
    entity: str,
    entity_id: str,
    context: Dict[str, Any]
) -> ValidationResult:
    """
    Validates if an action is allowed according to the ontology.
    
    Args:
        action: The action to validate
        entity: The entity type
        entity_id: Unique identifier for the entity
        context: Additional context (role, amounts, etc.)
    
    Returns:
        ValidationResult with allowed status and reason
    
    Raises:
        RuntimeError: If ontology is not loaded
    """
    ...
```

### README Updates

If you add new features, update the README.md to document them.

## Commit Messages

Follow these guidelines for commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters
- Reference issues and pull requests after the first line

Examples:
```
Add support for temporal constraints in validation

- Add time-based rule checking
- Update validator to handle timestamp context
- Add tests for temporal constraints

Fixes #123
```

## Pull Request Process

1. **Update CHANGELOG.md** with your changes
2. **Update documentation** if you've changed APIs
3. **Ensure all tests pass** and coverage is maintained
4. **Request review** from maintainers
5. **Address review feedback** promptly

### PR Checklist

- [ ] Code follows the style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No merge conflicts
- [ ] PR description is clear and complete

## Project Structure

```
OntoGuard/
├── src/
│   └── ontoguard/          # Main package
│       ├── __init__.py
│       ├── validator.py    # Core validation logic
│       ├── cli.py          # Command-line interface
│       └── mcp_server.py   # MCP server
├── tests/                   # Test suite
├── examples/                # Example code and ontologies
├── docs/                    # Documentation
├── .github/                 # GitHub templates and workflows
└── pyproject.toml          # Project configuration
```

## Getting Help

- **Documentation**: Check the README.md and examples/
- **Issues**: Search existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md (if we create one)
- Release notes
- Project documentation

Thank you for contributing to OntoGuard! 🎉
