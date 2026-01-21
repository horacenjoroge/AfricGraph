# Contributing to AfricGraph

Thank you for your interest in contributing to AfricGraph! This guide will help you get started.

## Getting Started

1. **Fork the Repository**
   - Fork the repository on GitHub
   - Clone your fork locally

2. **Set Up Development Environment**
   - Follow the [Developer Guide](./developer-guide.md)
   - Ensure all tests pass

3. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Code Style

- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Follow ESLint rules, use strict mode
- **Commits**: Use conventional commit messages

### Testing

- Write tests for new features
- Ensure all tests pass
- Maintain 85%+ code coverage
- Run tests before committing

### Documentation

- Update relevant documentation
- Add docstrings to new functions
- Update API documentation if needed

## Pull Request Process

### Before Submitting

1. **Ensure Tests Pass**
   ```bash
   pytest
   ```

2. **Check Code Coverage**
   ```bash
   pytest --cov=src --cov-report=html
   ```

3. **Update Documentation**
   - Update relevant docs
   - Add examples if needed

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin feature/your-feature-name
   ```

### Pull Request Checklist

- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Code coverage maintained (85%+)
- [ ] Documentation updated
- [ ] Code follows style guide
- [ ] No linter errors
- [ ] Commit messages follow conventions

### Review Process

1. Submit pull request
2. Automated tests run
3. Code review by maintainers
4. Address feedback
5. Merge after approval

## Commit Message Convention

Use conventional commits:

```
feat: add new feature
fix: fix bug
docs: update documentation
test: add tests
refactor: code refactoring
perf: performance improvement
chore: maintenance tasks
```

Examples:
- `feat(risk): add new risk factor analyzer`
- `fix(api): fix business search pagination`
- `docs: update API reference`

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Follow project guidelines
- Help others learn

## Questions?

- Open an issue for questions
- Check existing documentation
- Ask in discussions

Thank you for contributing!
