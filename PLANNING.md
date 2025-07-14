# Sports Betting Edge Finder - Project Planning

## 🎯 Project Overview

The Sports Betting Edge Finder is a sophisticated application that analyzes sports betting markets to identify value betting opportunities and arbitrage situations using machine learning and mathematical models.

## 🏗️ Architecture & Design Principles

### Core Architecture
- **FastAPI Backend**: Async REST API with automatic OpenAPI documentation
- **PostgreSQL + TimescaleDB**: Time-series optimized database for betting data
- **Redis**: Caching layer and pub/sub for real-time features
- **Celery**: Distributed task queue for background processing
- **WebSockets**: Real-time alerts and notifications

### Design Patterns
- **Repository Pattern**: Data access abstraction in `src/database/`
- **Service Layer**: Business logic separation in `src/services/`
- **Factory Pattern**: Model creation and configuration
- **Observer Pattern**: Real-time alert system
- **Strategy Pattern**: Multiple ML model implementations

### Code Organization
```
src/
├── api/                    # FastAPI routes and endpoints
├── core/                   # Core utilities, config, logging
├── database/               # SQLAlchemy models and repositories
├── services/               # Business logic and external integrations
├── ml/                     # Machine learning models and training
├── notifications/          # Alert and notification system
└── celery_app.py          # Background task definitions
```

## 📋 Naming Conventions

### Files and Directories
- **Snake_case** for all Python files: `value_calculator.py`
- **Lowercase** for directories: `src/services/odds/`
- **Descriptive names**: `kelly_optimizer.py` not `ko.py`

### Code Conventions
- **Classes**: PascalCase - `ValueBetCalculator`
- **Functions/Variables**: snake_case - `calculate_kelly_size()`
- **Constants**: UPPER_SNAKE_CASE - `MAX_KELLY_FRACTION`
- **Private methods**: Leading underscore - `_validate_input()`

### Database
- **Tables**: snake_case - `betting_odds`, `value_bets`
- **Columns**: snake_case - `game_id`, `created_at`
- **Indexes**: descriptive - `idx_odds_game_bookmaker`

## 🔧 Technology Stack

### Core Dependencies
- **FastAPI**: Web framework with automatic docs
- **SQLAlchemy**: ORM with async support
- **Pydantic**: Data validation and serialization
- **Redis**: Caching and message broker
- **Celery**: Background task processing

### ML/Analytics
- **XGBoost**: Primary ML model for predictions
- **scikit-learn**: Additional ML algorithms and metrics
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computations

### Infrastructure
- **PostgreSQL**: Primary database
- **TimescaleDB**: Time-series data optimization
- **Docker**: Containerization
- **Alembic**: Database migrations

## 🎨 Style Guidelines

### Python Code Style
- **PEP 8** compliance with 88-character line limit
- **Type hints** for all function parameters and returns
- **Docstrings** in Google format for all public functions
- **Black** formatter for consistent styling

### API Design
- **RESTful** endpoints with proper HTTP methods
- **Consistent** response formats using Pydantic models
- **Versioning** with `/api/v1/` prefix
- **Error handling** with standardized error responses

### Database Design
- **Normalized** structure with proper foreign keys
- **Indexes** on frequently queried columns
- **Constraints** for data integrity
- **Time-series** optimization for betting data

## 🧪 Testing Strategy

### Test Structure
```
tests/
├── unit/                  # Unit tests for individual components
├── integration/           # Integration tests for workflows
├── api/                   # API endpoint testing
└── conftest.py           # Shared test fixtures
```

### Testing Requirements
- **Minimum 80%** code coverage for all modules
- **Unit tests** for all business logic functions
- **Integration tests** for API endpoints
- **Mock external services** (The Odds API, databases)

### Test Naming
- `test_[function_name]_[scenario]_[expected_result]()`
- Example: `test_calculate_kelly_size_positive_edge_returns_fraction()`

## 🔄 Development Workflow

### Environment Setup
1. **Virtual Environment**: Use `venv_linux` for all Python operations
2. **Environment Variables**: Load from `.env` using `python-dotenv`
3. **Database**: Local PostgreSQL with TimescaleDB extension
4. **Redis**: Local Redis server for caching and queues

### Code Quality Checks
- **Black** formatting before commits
- **Flake8** linting for code quality
- **mypy** for type checking
- **Pytest** for test execution

### File Size Limits
- **Maximum 500 lines** per Python file
- **Split large files** into logical modules
- **Use helper functions** and classes for organization

## 🔐 Security Considerations

### Authentication
- **JWT tokens** with configurable expiration
- **Password hashing** using bcrypt
- **Rate limiting** on authentication endpoints

### Data Protection
- **Input validation** using Pydantic schemas
- **SQL injection prevention** via SQLAlchemy ORM
- **Environment variables** for sensitive configuration

### API Security
- **CORS** configuration for web clients
- **Request validation** for all endpoints
- **Error handling** without information leakage

## 🚀 Deployment Architecture

### Development
- **Local development** with hot reloading
- **Docker Compose** for service dependencies
- **Environment isolation** with virtual environments

### Production
- **Container orchestration** with Docker
- **Horizontal scaling** for API and worker processes
- **Load balancing** for high availability
- **Database replicas** for read scaling

## 📊 Monitoring & Observability

### Logging
- **Structured logging** with JSON format
- **Correlation IDs** for request tracing
- **Log levels** appropriate for environment
- **Centralized logging** for production

### Metrics
- **Business metrics**: Bet success rates, profit tracking
- **Technical metrics**: Response times, error rates
- **ML metrics**: Model accuracy, prediction confidence

This planning document serves as the foundation for consistent development practices and architectural decisions throughout the project lifecycle.