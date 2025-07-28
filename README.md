# AutoForms - AI-Powered Form Generator

![AutoForms Logo](https://via.placeholder.com/200x80/2563eb/ffffff?text=AutoForms)

AutoForms is a production-ready AI-powered form generation platform that creates beautiful, functional forms using natural language descriptions. Built with FastAPI, MongoDB, and OpenAI's GPT models.

## ✨ Features

### 🎯 Core Features
- **AI Form Generation**: Create forms using natural language prompts
- **Professional Templates**: 6+ pre-built form templates across multiple categories
- **Multi-language Support**: Generate forms in multiple languages
- **Real-time Preview**: Instant form preview and editing
- **PDF Export**: Export forms to PDF format
- **User Management**: Complete authentication and user management system

### 🛡️ Security & Production Ready
- **Security Headers**: Comprehensive security middleware
- **Rate Limiting**: Built-in rate limiting and abuse prevention
- **Error Handling**: Custom error pages and graceful degradation
- **Health Checks**: Production-ready health monitoring endpoints
- **Environment Validation**: Automatic configuration validation

### 🚀 Performance
- **Async Architecture**: Built on FastAPI with async/await support
- **Database Optimization**: MongoDB with optimized indexes
- **Caching**: Redis-based caching system
- **Static File Serving**: Optimized static asset delivery

## 🏗️ Architecture

```
AutoForms/
├── backend/                    # FastAPI application
│   ├── main.py                # Application entry point
│   ├── config.py              # Configuration management
│   ├── models/                # Data models
│   ├── routers/               # API endpoints
│   ├── services/              # Business logic
│   ├── templates/             # HTML templates
│   └── static/                # Static assets
├── tests/                     # Test suite
├── start_production.py        # Production startup script
├── validate_deployment.py     # Deployment validation
└── requirements.txt           # Dependencies
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- MongoDB (local or MongoDB Atlas)
- OpenAI API key
- Redis (optional, for caching)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd AutoForms
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Start Development Server
```bash
python backend/main.py
```

### 5. Access the Application
- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/healthz

## ⚙️ Configuration

### Required Environment Variables

```env
# Application
APP_ENV=development
HOST=127.0.0.1
PORT=8000
DEBUG=true

# Database
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=autoforms

# AI Integration
OPENAI_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-4o-mini

# Security
JWT_SECRET=your-super-secret-jwt-key-min-32-chars

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com

# Caching (Optional)
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true
```

### Optional Configuration

See `.env.example` for complete configuration options including:
- CORS settings
- Rate limiting configuration
- Cache TTL settings
- Logging configuration
- Admin user settings

## 🏭 Production Deployment

### Using the Production Startup Script

```bash
# Validate deployment readiness
python validate_deployment.py

# Start production server
python start_production.py
```

The production script automatically:
- ✅ Validates environment configuration
- ✅ Checks all dependencies
- ✅ Tests database connectivity
- ✅ Sets up production logging
- ✅ Starts optimized server

### Cloud Platform Deployment

#### Render.com
```yaml
# render.yaml included
services:
  - type: web
    name: autoforms
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python start_production.py
```

#### Railway
```bash
railway login
railway init
railway add
railway deploy
```

#### Heroku
```bash
heroku create your-app-name
git push heroku main
```

### Docker Deployment (Optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "start_production.py"]
```

## 🧪 Testing

### Run All Tests
```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=backend --cov-report=html
```

### Run Production Validation
```bash
python validate_deployment.py
```

### Run Specific Test Categories
```bash
# Production readiness tests
python -m pytest tests/test_production_readiness.py -v

# Integration tests
python -m pytest tests/integration/ -v

# Unit tests
python -m pytest tests/unit/ -v
```

## 📚 API Documentation

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Homepage |
| `/test-generator` | GET | Form generator interface |
| `/api/generate/form` | POST | Generate form from prompt |
| `/api/templates/` | GET | List form templates |
| `/api/forms/` | GET | User's saved forms |
| `/healthz` | GET | Basic health check |
| `/health/ready` | GET | Comprehensive readiness check |

### Authentication Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | User registration |
| `/api/auth/login` | POST | User login |
| `/api/auth/logout` | POST | User logout |
| `/api/auth/forgot-password` | POST | Password reset request |

### Form Templates

Built-in templates include:
- 📝 **Contact Forms**: Basic and advanced contact forms
- 📊 **Survey Forms**: Customer feedback and research surveys  
- 📋 **Registration Forms**: Event and service registration
- 💼 **Business Forms**: Quote requests and applications
- 📧 **Newsletter Forms**: Subscription and preferences

## 🔧 Development

### Project Structure

```
backend/
├── main.py                    # FastAPI app and routing
├── config.py                  # Configuration management
├── db.py                      # Database connection
├── deps.py                    # Dependency injection
├── models/                    # Pydantic models
│   ├── user.py
│   └── form_models.py
├── routers/                   # API route handlers
│   ├── auth.py                # Authentication
│   ├── forms.py               # Form management
│   ├── generate.py            # AI form generation
│   ├── templates.py           # Form templates
│   └── admin.py               # Admin interface
├── services/                  # Business logic
│   ├── auth_service.py        # Authentication logic
│   ├── form_generator.py      # AI form generation
│   ├── form_templates.py      # Template management
│   ├── pdf_service.py         # PDF generation
│   ├── email_service.py       # Email functionality
│   ├── security.py            # Security utilities
│   └── error_handler.py       # Error handling
└── templates/                 # Jinja2 HTML templates
    ├── index.html
    ├── test-generator.html
    └── errors/
        ├── 404.html
        └── 500.html
```

### Adding New Features

1. **Create Model** (if needed):
   ```python
   # backend/models/new_model.py
   from dataclasses import dataclass
   
   @dataclass
   class NewModel:
       field: str
   ```

2. **Create Service**:
   ```python
   # backend/services/new_service.py
   class NewService:
       async def process(self):
           pass
   ```

3. **Create Router**:
   ```python
   # backend/routers/new_router.py
   from fastapi import APIRouter
   
   router = APIRouter(prefix="/api/new", tags=["new"])
   
   @router.get("/")
   async def get_items():
       return {"items": []}
   ```

4. **Register Router**:
   ```python
   # backend/main.py
   from backend.routers import new_router
   app.include_router(new_router.router)
   ```

### Database Models

The application uses dataclasses for models instead of Pydantic for simplicity:

```python
@dataclass
class User:
    username: str
    email: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass  
class Form:
    title: str
    html: str
    prompt: str
    user_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
```

## 🔒 Security

### Production Security Checklist

- ✅ **Environment Variables**: All secrets in environment variables
- ✅ **JWT Tokens**: Secure token generation and validation
- ✅ **Password Hashing**: bcrypt with salt rounds
- ✅ **CORS Configuration**: Restricted origins in production
- ✅ **Security Headers**: CSP, HSTS, X-Frame-Options, etc.
- ✅ **Rate Limiting**: Request throttling and abuse prevention
- ✅ **Input Validation**: Comprehensive input sanitization
- ✅ **Error Handling**: No sensitive data in error responses

### Security Headers

The application automatically sets these security headers:

```python
{
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY", 
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}
```

## 📊 Monitoring

### Health Check Endpoints

- **`/healthz`**: Basic health check for load balancers
- **`/health/live`**: Liveness probe for container orchestration
- **`/health/ready`**: Comprehensive readiness check including:
  - Database connectivity
  - External service availability
  - Configuration validation
  - Response time metrics

### Logging

Structured logging with configurable levels:

```python
# Production logging configuration
LOG_LEVEL=INFO
SENTRY_DSN=your-sentry-dsn  # Optional error tracking
```

### Metrics (Optional)

Prometheus metrics available when enabled:
- HTTP request duration
- Database query performance
- Error rates
- Active user sessions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `python -m pytest tests/ -v`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Run in development mode
python backend/main.py

# Run tests
python -m pytest tests/ -v --cov=backend
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Create an issue on GitHub for bugs or feature requests
- **Email**: Contact support@autoforms.com for commercial support

## 🙏 Acknowledgments

- **FastAPI**: Modern, fast web framework for building APIs
- **OpenAI**: Powerful AI models for form generation
- **MongoDB**: Flexible document database
- **Tailwind CSS**: Utility-first CSS framework
- **HTMX**: Modern frontend interactivity

---

**AutoForms** - Making form creation effortless with AI ✨