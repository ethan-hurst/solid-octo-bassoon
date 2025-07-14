# Sports Betting Edge Finder

An advanced sports betting application that analyzes news, fan sentiment, and multiple data points to identify value bets with mathematical edges.

## 🎯 Features

### Core Functionality
- **Real-time Odds Aggregation**: Fetches live odds from multiple bookmakers via The Odds API
- **ML-Powered Predictions**: XGBoost and ensemble models for accurate probability estimation
- **Value Bet Detection**: Kelly Criterion-based bet sizing with confidence scoring
- **Arbitrage Detection**: Identifies risk-free betting opportunities across bookmakers
- **Real-time Alerts**: WebSocket-based notifications for value bets and arbitrage

### Advanced Analytics
- **Portfolio Kelly Optimization**: Manages correlated bets for optimal bankroll allocation
- **Historical Analysis**: Tracks odds movements and betting patterns
- **Performance Metrics**: ROI tracking and model validation
- **Risk Management**: Exposure limits and bet sizing controls

### Infrastructure
- **FastAPI Backend**: High-performance async API with automatic documentation
- **Real-time WebSockets**: Live updates and notifications
- **Celery Background Tasks**: Automated odds fetching and analysis
- **Redis Caching**: Fast data access and pub/sub messaging
- **PostgreSQL + TimescaleDB**: Optimized for time-series betting data

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL with TimescaleDB extension
- Redis
- Docker (optional)

### Installation

1. **Clone and setup environment**:
```bash
git clone <repository-url>
cd sports-betting-edge-finder
python -m venv venv_linux
source venv_linux/bin/activate  # On Windows: venv_linux\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Environment setup**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Database setup**:
```bash
# Start PostgreSQL and Redis (or use Docker)
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head
```

5. **Get The Odds API key**:
   - Sign up at [The Odds API](https://the-odds-api.com/)
   - Add your API key to `.env`

### Running the Application

**Development mode**:
```bash
# Start the API server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker (in another terminal)
celery -A src.celery_app worker --loglevel=info

# Start Celery beat scheduler (in another terminal)
celery -A src.celery_app beat --loglevel=info
```

**Docker mode**:
```bash
docker-compose up
```

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/sports_betting
REDIS_URL=redis://localhost:6379

# The Odds API
ODDS_API_KEY=your_api_key_here
ODDS_API_BASE_URL=https://api.the-odds-api.com/v4

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Betting Parameters
MIN_EDGE_THRESHOLD=0.05
MAX_KELLY_FRACTION=0.25
MAX_BANKROLL_PERCENTAGE=0.10
```

## 📊 API Usage

### Authentication
```bash
# Register
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "user", "password": "password"}'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user&password=password"
```

### Getting Odds
```bash
# Current odds for NFL
curl "http://localhost:8000/api/v1/odds/current/NFL"

# Historical odds for a game
curl "http://localhost:8000/api/v1/odds/history/game_id_123"
```

### Value Betting
```bash
# Find value bets (requires authentication)
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/analysis/value-bets?sport=NFL&min_edge=0.05"

# Calculate bet size
curl -X POST "http://localhost:8000/api/v1/analysis/bet-size" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"value_bet": {...}, "bankroll": 10000}'
```

### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/user_id');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received alert:', data);
};

// Subscribe to NFL alerts
ws.send(JSON.stringify({
    action: 'subscribe',
    channels: ['sport:NFL', 'user:your_user_id']
}));
```

## 🧠 Machine Learning Models

### Training Models
```bash
# Train models for all sports
python scripts/train_models.py

# Train specific sport
python scripts/train_models.py --sport NFL

# Evaluate model performance
python scripts/evaluate_models.py
```

### Model Architecture
- **XGBoost**: Primary model for win probability prediction
- **Random Forest**: Secondary model for ensemble
- **Logistic Regression**: Baseline model
- **Ensemble**: Weighted combination of all models

### Features
- Team statistics (offensive/defensive rankings)
- Recent performance metrics
- Head-to-head history
- Injury reports
- Weather conditions
- Market sentiment indicators

## 🧪 Testing

### Run Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/test_value_calculator.py

# With coverage
pytest --cov=src tests/

# Integration tests only
pytest tests/test_integration.py -v
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **API Tests**: Endpoint functionality testing
- **WebSocket Tests**: Real-time communication testing

## 📈 Monitoring and Analytics

### Health Checks
```bash
curl http://localhost:8000/health
```

### Metrics Endpoints
- `/metrics` - Prometheus metrics
- `/api/v1/analytics/performance` - Model performance
- `/api/v1/analytics/roi` - Return on investment tracking

### Logging
Structured logging with correlation IDs:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Value bet found", extra={
    "game_id": "123",
    "edge": 0.08,
    "confidence": 0.85
})
```

## 🔄 Data Pipeline

### Automated Tasks
- **Odds Fetching**: Every 5 minutes
- **Value Bet Analysis**: Every 10 minutes  
- **Model Updates**: Daily at 3 AM UTC
- **Data Cleanup**: Weekly on Sundays

### Data Flow
1. **Collection**: Odds fetched from The Odds API
2. **Storage**: Cached in Redis, persisted in PostgreSQL
3. **Analysis**: ML models generate probability predictions
4. **Detection**: Value bets identified using Kelly Criterion
5. **Notification**: Real-time alerts sent to subscribed users

## 🚀 Deployment

### Production Deployment
```bash
# Build Docker images
docker-compose build

# Deploy with production settings
docker-compose -f docker-compose.prod.yml up -d

# Database migrations
docker-compose exec api alembic upgrade head
```

### Scaling Considerations
- **Horizontal Scaling**: Multiple API instances behind load balancer
- **Database**: Read replicas for analytics queries
- **Cache**: Redis Cluster for high availability
- **Background Tasks**: Multiple Celery workers

## 🔐 Security

### Best Practices Implemented
- JWT token authentication with expiration
- Password hashing with bcrypt
- SQL injection prevention via SQLAlchemy
- Rate limiting on API endpoints
- Input validation with Pydantic
- CORS configuration for web clients

### Recommended Production Settings
- Use HTTPS in production
- Set strong SECRET_KEY
- Configure rate limiting
- Enable database SSL
- Use environment variable secrets

## 📝 API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Key Endpoints
- `GET /api/v1/odds/current/{sport}` - Current odds
- `GET /api/v1/analysis/value-bets` - Value betting opportunities
- `GET /api/v1/analysis/arbitrage` - Arbitrage opportunities
- `WebSocket /api/v1/ws/{user_id}` - Real-time alerts

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Install development dependencies: `pip install -r requirements-dev.txt`
4. Make changes and add tests
5. Run tests: `pytest`
6. Submit pull request

### Code Standards
- Follow PEP 8 style guidelines
- Use type hints
- Write docstrings for all functions
- Add tests for new features
- Keep functions under 50 lines

## 📋 Roadmap

### Short Term
- [ ] Add more sports (NCAAF, NCAAB, Soccer leagues)
- [ ] Implement prop bet analysis
- [ ] Add live betting support
- [ ] Mobile app development

### Medium Term
- [ ] Advanced ML features (player props, live betting)
- [ ] Social features (leaderboards, bet sharing)
- [ ] Integration with more data sources
- [ ] Advanced risk management tools

### Long Term
- [ ] Multi-language support
- [ ] Cryptocurrency betting integration
- [ ] AI-powered betting strategies
- [ ] Professional trader tools

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes only. Sports betting involves financial risk. Always bet responsibly and within your means. The developers are not responsible for any financial losses incurred through the use of this software.

## 📞 Support

- **Documentation**: [Link to docs]
- **Issues**: [GitHub Issues]
- **Discord**: [Community Discord]
- **Email**: support@sportsbetting-edge.com

---

**Made with ❤️ for the sports betting community**