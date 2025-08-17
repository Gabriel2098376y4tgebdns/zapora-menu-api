# Contributing to Zapora Delivery API

First off, thank you for considering contributing to Zapora! 🎉

This is a **production system** serving real users, so we maintain high standards for code quality, security, and reliability.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Security Considerations](#security-considerations)

## 🤝 Code of Conduct

This project adheres to a professional standard. Please be respectful, constructive, and collaborative.

## 🛠️ How Can I Contribute?

### 🐛 Bug Reports
- Use the issue template
- Include reproduction steps
- Provide environment details
- Check for existing issues first

### 💡 Feature Requests
- Explain the business value
- Provide use cases
- Consider backward compatibility
- Align with project goals

### 📝 Documentation
- API documentation improvements
- Architecture diagrams
- Deployment guides
- Performance optimization tips

### 🔍 Code Reviews
- Security-focused reviews
- Performance improvements
- Code quality enhancements
- Best practices enforcement

## 🚀 Development Setup

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+
- Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/zapora-delivery-api.git
   cd zapora-delivery-api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start dependencies**
   ```bash
   docker-compose up -d postgres redis
   ```

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

7. **Start development server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

8. **Verify setup**
   ```bash
   curl http://localhost:8000/healthz
   ```

### 🧪 Testing Setup

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/security/

# Run performance tests
locust -f tests/performance/locustfile.py
```

### 🔍 Code Quality Tools

```bash
# Linting
flake8 app/
black app/ --check
isort app/ --check-only

# Type checking
mypy app/

# Security scanning
bandit -r app/
safety check
```

## 📏 Coding Standards

### 🐍 Python Style Guide

- **Follow PEP 8** with 88-character line limit
- **Use type hints** for all function signatures
- **Write docstrings** for all public functions/classes
- **Prefer async/await** for I/O operations

### 📁 File Organization

```
app/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration settings
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
├── routers/             # API route handlers
├── services/            # Business logic layer
├── utils/               # Utility functions
└── tests/               # Test suite
    ├── unit/
    ├── integration/
    └── performance/
```

### 🔒 Security Requirements

- **Never commit secrets** or credentials
- **Validate all inputs** using Pydantic schemas
- **Use parameterized queries** (SQLAlchemy handles this)
- **Implement proper error handling** without exposing internals
- **Add audit logging** for sensitive operations

### 📝 Documentation Standards

```python
def create_menu_item(
    db: Session,
    item_data: MenuItemCreate,
    current_user: User
) -> MenuItem:
    """
    Create a new menu item with proper validation and audit logging.
    
    Args:
        db: Database session
        item_data: Validated menu item data
        current_user: Authenticated user making the request
        
    Returns:
        Created menu item with generated ID and timestamps
        
    Raises:
        HTTPException: If validation fails or user lacks permissions
        
    Example:
        >>> item = create_menu_item(db, item_data, user)
        >>> assert item.id is not None
    """
```

### 🧪 Testing Standards

- **90%+ code coverage** required
- **Unit tests** for business logic
- **Integration tests** for API endpoints
- **Security tests** for authentication/authorization
- **Performance tests** for critical paths

```python
def test_create_menu_item_success():
    """Test successful menu item creation with proper permissions."""
    # Arrange
    user = create_test_user(role=UserRole.MANAGER)
    item_data = MenuItemCreate(name="Test Item", price=10.99)
    
    # Act
    result = create_menu_item(db, item_data, user)
    
    # Assert
    assert result.name == "Test Item"
    assert result.created_by == user.id
    assert_audit_log_created("CREATE_MENU_ITEM")
```

## 🔄 Pull Request Process

### 1. **Branch Strategy**
```bash
# Feature branch
git checkout -b feature/add-payment-integration

# Bug fix branch
git checkout -b fix/authentication-timeout

# Security fix branch
git checkout -b security/fix-sql-injection
```

### 2. **Commit Convention**
Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
feat(api): add menu item bulk upload endpoint
fix(auth): resolve JWT token expiration handling
docs(readme): update deployment instructions
test(security): add rate limiting test coverage
security(auth): patch authentication bypass vulnerability
```

### 3. **Pre-commit Checklist**
- [ ] All tests pass (`pytest`)
- [ ] Code coverage above 90% (`pytest --cov`)
- [ ] No linting errors (`flake8`, `black`, `isort`)
- [ ] Type checking passes (`mypy`)
- [ ] Security scan clean (`bandit`)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)

### 4. **Pull Request Template**

When creating a PR, include:

```markdown
## 📝 Description
Brief description of changes and motivation.

## 🔧 Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Security fix

## 🧪 Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed
- [ ] Security testing completed

## 📊 Impact Assessment
- Performance impact: None/Positive/Negative
- Breaking changes: Yes/No
- Database changes: Yes/No
- API changes: Yes/No

## 🔍 Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added for new functionality
- [ ] Security considerations addressed
```

### 5. **Review Process**
- **2 approvals required** for main branch
- **1 approval required** for feature branches
- **Security team review** for security-related changes
- **Automated checks** must pass
- **Manual testing** for critical features

## 🐛 Issue Reporting

### 🔍 Before Creating an Issue
1. Search existing issues
2. Check documentation
3. Verify with latest version
4. Reproduce with minimal example

### 📝 Issue Templates

**Bug Report:**
```markdown
**Bug Description**
Clear description of the bug.

**Reproduction Steps**
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g. iOS]
- Python Version: [e.g. 3.11]
- API Version: [e.g. 1.2.0]
```

**Feature Request:**
```markdown
**Feature Description**
Clear description of the feature.

**Business Justification**
Why is this feature needed?

**Proposed Solution**
How should this be implemented?

**Alternatives Considered**
What other solutions were considered?
```

## 🔒 Security Considerations

### 🚨 Security Issues
- **Never report security issues publicly**
- **Use security@zapora.com** for private disclosure
- **Follow responsible disclosure** practices

### 🛡️ Security Guidelines
- Validate all inputs
- Use prepared statements
- Implement proper authentication
- Add audit logging
- Follow OWASP guidelines

## 🏅 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Annual contributor highlights

## 📞 Getting Help

- **Documentation**: Check `/docs` folder
- **API Docs**: http://localhost:8000/docs
- **Issues**: GitHub Issues for bugs/features
- **Discussions**: GitHub Discussions for questions
- **Email**: dev@zapora.com for complex topics

## 🎯 Project Goals

Keep in mind our project goals:
- **Production reliability** - 99.9% uptime
- **Security first** - Zero security incidents
- **Performance** - <100ms response times
- **Scalability** - Handle 10x traffic growth
- **Maintainability** - Clean, documented code

---

**Thank you for contributing to Zapora! 🚀**

Your contributions help make delivery services better for thousands of users worldwide.
