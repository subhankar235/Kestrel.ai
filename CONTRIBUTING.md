# Contributing to Kestrel.ai

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a new branch for your feature/fix
4. Make your changes
5. Submit a pull request

## Development Setup

### Prerequisites

- Node.js 22+ (see `.nvmrc`)
- Python 3.12+ (see `.python-version`)
- Bun package manager
- PostgreSQL

### Installation

```bash
# Install dependencies
bun install

# Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Copy environment files
cp .env.example .env
# Edit .env with your configuration
```

### Running the Project

```bash
# Start all services
make dev

# Or run individually
make dev-frontend
make dev-backend
```

## Code Style

### TypeScript/JavaScript

- Use Prettier for formatting (config in `.prettierrc`)
- ESLint for linting (config in `frontend/eslint.config.mjs`)
- Follow existing patterns in the codebase

### Python

- Use Ruff for linting and formatting
- Follow PEP 8 style guidelines
- Type hints are required for all functions

## Commit Messages

- Use clear, descriptive commit messages
- Start with a verb in imperative mood (e.g., "Add feature", "Fix bug")
- Keep the subject line under 72 characters
- Reference issue numbers when applicable

## Pull Request Process

1. Update documentation if needed
2. Add tests for new features
3. Ensure all tests pass
4. Request a review from maintainers

## Reporting Issues

- Use the GitHub issue tracker
- Include steps to reproduce
- Include expected vs actual behavior
- Include environment details

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
