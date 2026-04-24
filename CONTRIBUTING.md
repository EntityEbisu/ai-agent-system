# Contributing to Agentic Conversational AI System

Thank you for your interest in contributing to this project! This guide will help you get started.

## 🚀 Getting Started

### Prerequisites
- Python 3.13+
- Git
- Docker (for containerized development)

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-agent-system.git
cd ai-agent-system

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env  # Create from template
# Edit .env with your API keys
```

## 🧪 Testing

### Running Tests

```bash
# Run validation tests
python tests/validate_project.py

# Run comprehensive test suite
python tests/test_core.py

# Run frontend integration tests
python tests/test_integration.py

# Run all tests
python tests/run_all_tests.py
```

### Test Structure
- `scripts/validate_project.py` - Core functionality validation
- `scripts/comprehensive_test.py` - Full system testing
- `scripts/test_frontend_integration.py` - Frontend-backend integration

## 🔧 Development Workflow

### Feature Development
1. Create a new branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Add tests for your changes
4. Update documentation
5. Run tests: `python tests/run_all_tests.py`
6. Commit your changes: `git commit -m "Add your feature"`
7. Push to branch: `git push origin feature/your-feature-name`
8. Create a Pull Request

### Bug Fixes
1. Create a bugfix branch: `git checkout -b bugfix/issue-description`
2. Reproduce the issue
3. Implement the fix
4. Add regression tests
5. Update documentation if needed
6. Run tests to verify fix
7. Commit and push
8. Create a Pull Request

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Write comprehensive docstrings
- Keep functions focused and small
- Add comments for complex logic

## 📝 Documentation

### Updating Documentation
- Keep README.md up to date
- Update relevant documentation files
- Add examples and usage patterns
- Include screenshots if UI changes

### Documentation Files
- `README.md` - Main project overview
- `QUICK_START.md` - Quick reference guide
- `ASSIGNMENT_ALIGNMENT.md` - Requirement coverage
- `IaC_DOCUMENTATION.md` - Deployment guide
- `DATA_LIFECYCLE.md` - Data versioning guide

## 🎯 Pull Request Process

1. Ensure your code follows project standards
2. Update documentation
3. Add/update tests
4. Verify all tests pass
5. Update CHANGELOG.md
6. Create descriptive PR title
7. Include detailed description of changes
8. Reference related issues
9. Request review from maintainers

## 📚 Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/) code of conduct. Be respectful and inclusive in all interactions.

## 🤝 Community

- Report bugs by opening GitHub Issues
- Suggest features through GitHub Issues
- Join discussions and help others

## 📋 Maintainers

- Nguyễn Trọng Minh

Thank you for contributing! Your help makes this project better for everyone.
