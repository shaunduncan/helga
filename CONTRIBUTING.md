# Contributing to Helga

Thank you for your interest in contributing to Helga! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Release Process](#release-process)

## Code of Conduct

Be respectful, inclusive, and professional. We're all here to make Helga better.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Docker and Docker Compose (for local testing)
- MongoDB (or use Docker)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork:

   ```bash
   git clone https://github.com/YOUR_USERNAME/helga.git
   cd helga
   ```

3. Add upstream remote:

   ```bash
   git remote add upstream https://github.com/shaunduncan/helga.git
   ```

## Development Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Development Dependencies

```bash
# Install package in editable mode with dev dependencies
pip install -e .[dev]

# Or install from requirements files
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Install Pre-commit Hooks

```bash
pre-commit install
```

This will automatically run code quality checks before each commit.

### 4. Verify Setup

```bash
# Run tests
pytest

# Check code quality
ruff check helga
black --check helga
mypy helga
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

- Write code following our [Code Standards](#code-standards)
- Add tests for new features
- Update documentation as needed
- Keep commits focused and atomic

### 3. Run Quality Checks

```bash
# Format code
black helga
ruff check --fix helga

# Run all pre-commit hooks
pre-commit run --all-files

# Run tests
pytest

# Check type hints
mypy helga
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
```

**Commit Message Format:**

```
<type>: <description>

[optional body]

[optional footer]
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Standards

### Python Style

We use modern Python tooling for consistent code quality:

#### Black (Code Formatting)

- Line length: 100 characters
- Automatic formatting on commit (via pre-commit)

```bash
black helga
```

#### Ruff (Linting)

- Replaces flake8, isort, pyupgrade, and more
- Fast and comprehensive

```bash
ruff check helga
ruff check --fix helga  # Auto-fix issues
```

#### Mypy (Type Checking)

- Add type hints to new code
- Check with mypy

```bash
mypy helga
```

### Code Guidelines

1. **Follow PEP 8** (enforced by Black and Ruff)
2. **Add type hints** to function signatures
3. **Write docstrings** for public APIs
4. **Keep functions focused** - one responsibility per function
5. **Use meaningful names** - clear and descriptive
6. **Avoid magic numbers** - use named constants
7. **Handle errors gracefully** - don't silently fail

### Example

```python
from typing import Optional, List

def process_message(
    message: str,
    channel: str,
    nick: Optional[str] = None
) -> List[str]:
    """
    Process an IRC message and return responses.

    Args:
        message: The message text to process
        channel: The channel where the message was sent
        nick: Optional nickname of the sender

    Returns:
        List of response messages to send

    Raises:
        ValueError: If message is empty
    """
    if not message:
        raise ValueError("Message cannot be empty")

    # Process message...
    responses = []
    return responses
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=helga --cov-report=html

# Run specific test file
pytest helga/tests/test_settings.py

# Run specific test
pytest helga/tests/test_settings.py::TestSettings::test_configure
```

### Writing Tests

1. **Use pytest** - modern testing framework
2. **Test file naming** - `test_*.py`
3. **Test function naming** - `test_*`
4. **Use fixtures** - for setup/teardown
5. **Mock external dependencies** - use `mock` or `pretend`
6. **Aim for high coverage** - but focus on meaningful tests

### Example Test

```python
import pytest
from helga.plugins import help

def test_help_command():
    """Test that help command returns plugin list."""
    result = help.help(None, "#test", "helga", "help", "", [])
    assert isinstance(result, str)
    assert "Available commands" in result

@pytest.fixture
def mock_client():
    """Fixture providing a mock IRC client."""
    from mock import Mock
    client = Mock()
    client.nickname = "helga"
    return client

def test_with_fixture(mock_client):
    """Test using a fixture."""
    assert mock_client.nickname == "helga"
```

### Test Coverage

- Aim for >80% coverage
- Focus on critical paths
- Don't test external libraries
- Test edge cases and error conditions

## Documentation

### Docstrings

Use Google-style docstrings:

```python
def function(arg1: str, arg2: int) -> bool:
    """
    Short description.

    Longer description if needed.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Raises:
        ValueError: When something is wrong
    """
    pass
```

### Documentation Files

- Update `README.rst` for user-facing changes
- Update `docs/source/*.rst` for detailed documentation
- Add examples for new features
- Update `CHANGELOG.rst` for notable changes

### Building Documentation

```bash
cd docs
make html
# Open docs/build/html/index.html
```

## Submitting Changes

### Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines (Black, Ruff)
- [ ] All tests pass (`pytest`)
- [ ] Type checking passes (`mypy`)
- [ ] New code has tests
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] PR description explains changes
- [ ] No merge conflicts with main branch

### Pull Request Process

1. **Create PR** with clear title and description
2. **Link related issues** using "Fixes #123"
3. **Wait for CI** - all checks must pass
4. **Address review feedback** - make requested changes
5. **Squash commits** if requested
6. **Merge** - maintainer will merge when approved

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

## Release Process

For maintainers:

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Creating a Release

1. **Update version** in `helga/__init__.py` and `pyproject.toml`
2. **Update CHANGELOG.rst** with release notes
3. **Commit changes**:

   ```bash
   git commit -m "chore: bump version to X.Y.Z"
   ```

4. **Create tag**:

   ```bash
   git tag -a vX.Y.Z -m "Release X.Y.Z"
   git push origin vX.Y.Z
   ```

5. **Create GitHub Release** - CI will automatically:
   - Build packages
   - Publish to PyPI
   - Build Docker images
   - Generate release notes

## Getting Help

- **Questions?** Open a discussion on GitHub
- **Bug reports?** Open an issue with details
- **IRC:** Join #helgabot on Freenode
- **Documentation:** <https://helga.readthedocs.org>

## Recognition

Contributors are recognized in:

- GitHub contributors page
- Release notes
- Project documentation

Thank you for contributing to Helga! 🎉
