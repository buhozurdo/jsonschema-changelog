# Contributing to jsonschema-changelog

Thank you for your interest in contributing to jsonschema-changelog! This document provides guidelines and instructions for contributing.

## 🤝 Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and constructive in all interactions.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Git
- pip

### Development Setup

1. **Fork and clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/jsonschema-changelog.git
cd jsonschema-changelog
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install development dependencies**

```bash
pip install -e ".[dev]"
```

4. **Run tests to verify setup**

```bash
pytest
```

## 📝 Code Style

### Python Style Guide

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://github.com/psf/black) for formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use type hints for all public functions
- Write docstrings for all public classes and functions

### Pre-commit Hooks

We recommend using pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

### Manual Formatting

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Check types
mypy src/

# Lint
ruff src/ tests/
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/jsonschema_changelog --cov-report=html

# Run specific test file
pytest tests/test_diff.py

# Run specific test
pytest tests/test_diff.py::TestSchemaDiff::test_property_added
```

### Test Requirements

- **Coverage**: Maintain >80% code coverage
- **All tests must pass** before submitting a PR
- Add tests for new features and bug fixes
- Include edge cases (empty schemas, nested structures, etc.)

### Writing Tests

```python
import pytest
from jsonschema_changelog import SchemaDiff

class TestNewFeature:
    """Tests for the new feature."""

    def test_basic_functionality(self):
        """Test the basic use case."""
        # Arrange
        old_schema = {...}
        new_schema = {...}
        
        # Act
        differ = SchemaDiff()
        result = differ.compare(old_schema, new_schema)
        
        # Assert
        assert result.has_changes
        assert len(result.changes) == 1

    def test_edge_case_empty_schema(self):
        """Test with empty schemas."""
        differ = SchemaDiff()
        result = differ.compare({}, {})
        assert not result.has_changes
```

## 📦 Pull Request Process

### Before Submitting

1. **Create a feature branch**

```bash
git checkout -b feature/my-awesome-feature
```

2. **Make your changes**
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation if needed

3. **Run quality checks**

```bash
black src/ tests/
isort src/ tests/
mypy src/
pytest
```

4. **Commit with conventional commits**

```bash
git commit -m "feat(diff): add support for allOf schemas"
```

### Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Scopes:**
- `diff`: Schema diff module
- `classifier`: Change classifier
- `changelog`: Changelog generator
- `compatibility`: Compatibility validator
- `migration`: Migration strategies
- `cli`: Command-line interface
- `formatters`: Output formatters

**Examples:**
```
feat(diff): add detection for oneOf schema changes
fix(classifier): correct severity for enum removal
docs: update API reference examples
test(migration): add edge case for nested objects
```

### Pull Request Guidelines

1. **Title**: Use conventional commit format
2. **Description**: Explain what and why, not how
3. **Link issues**: Reference related issues
4. **Screenshots**: Include for UI changes
5. **Breaking changes**: Clearly document in PR description

### PR Template

```markdown
## Description
Brief description of the changes.

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
```

## 📢 Reporting Issues

### Bug Reports

Include:
- Python version
- Package version
- Minimal reproducible example
- Expected vs actual behavior
- Error messages/tracebacks

### Feature Requests

Include:
- Use case description
- Expected behavior
- Any alternatives considered

## 🌟 Recognition

Contributors will be recognized in:
- GitHub contributors list
- CHANGELOG.md for significant contributions
- README.md acknowledgments section (for major contributors)

## ❓ Questions?

- **GitHub Issues**: For bugs and features
- **Discussions**: For questions and ideas
- **Email**: dev@buhozurdo.com

---

Thank you for contributing to the Búho Zurdo ecosystem! 🦉
