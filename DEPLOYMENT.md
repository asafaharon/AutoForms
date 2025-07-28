# 🚀 AutoForms Deployment Guide

Complete deployment guide for AutoForms across different cloud platforms.

## 📋 Pre-Deployment Checklist

### ✅ 1. Validate Project Readiness
```bash
# Run the deployment validation script
python validate_deployment.py
```

Ensure all checks pass:
- ✅ File Structure
- ✅ Configuration  
- ✅ Security Features
- ✅ Production Features
- ✅ Deployment Configs

### ✅ 2. Environment Configuration
```bash
# Copy the environment template
cp .env.example .env

# Edit with your production values
nano .env
```

**Critical Environment Variables:**
```env
APP_ENV=production
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/autoforms
OPENAI_KEY=sk-your-real-openai-key
JWT_SECRET=your-super-secure-jwt-secret-32-chars-minimum
ALLOWED_ORIGINS=https://your-domain.com
```

### ✅ 3. Database Setup
- Create MongoDB Atlas cluster or configure local MongoDB
- Update `MONGODB_URI` with connection string
- Ensure network access is configured for your deployment platform

### ✅ 4. External Services
- **OpenAI API**: Valid API key with sufficient credits
- **Email Service** (optional): SMTP configuration for password resets
- **Redis** (optional): For caching and performance

---

## ☁️ Cloud Platform Deployment

## 1. Render.com (Recommended)

### Quick Deploy
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com)

### Manual Setup

**Step 1: Create Account**
- Sign up at [render.com](https://render.com)
- Connect your GitHub repository

**Step 2: Configure Service**
```yaml
# render.yaml (already included)
services:
  - type: web
    name: autoforms
    env: python
    plan: free  # or starter for production
    buildCommand: pip install -r requirements.txt
    startCommand: python start_production.py
    envVars:
      - key: APP_ENV
        value: production
      - key: MONGODB_URI
        sync: false  # Set in Render dashboard
      - key: OPENAI_KEY
        sync: false  # Set in Render dashboard
      - key: JWT_SECRET
        generateValue: true  # Auto-generate secure secret
```

**Step 3: Environment Variables**
Set in Render Dashboard:
- `MONGODB_URI`: Your MongoDB connection string
- `OPENAI_KEY`: Your OpenAI API key
- `ALLOWED_ORIGINS`: Your Render app URL

**Step 4: Deploy**
- Push to your connected GitHub repository
- Render automatically builds and deploys
- Access your app at `https://your-app-name.onrender.com`

### Render Configuration Benefits
- ✅ Automatic HTTPS
- ✅ Custom domains
- ✅ Automatic scaling
- ✅ Zero-downtime deployments
- ✅ Built-in monitoring

---

## 2. Railway

### Quick Deploy
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway add
railway deploy
```

### Manual Setup

**Step 1: Create Project**
- Visit [railway.app](https://railway.app)
- Create new project from GitHub

**Step 2: Environment Variables**
Set in Railway Dashboard:
```env
APP_ENV=production
MONGODB_URI=mongodb+srv://...
OPENAI_KEY=sk-...
JWT_SECRET=auto-generated-by-railway
PORT=8000
```

**Step 3: Configure Build**
Railway auto-detects Python and uses:
- Build: `pip install -r requirements.txt`
- Start: `python start_production.py`

**Step 4: Custom Domain (Optional)**
- Add custom domain in Railway dashboard
- Configure DNS records

### Railway Benefits
- ✅ Simple pricing model
- ✅ Excellent performance
- ✅ Built-in databases
- ✅ Automatic deployments

---

## 3. Heroku

### Quick Deploy
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

### Manual Setup

**Step 1: Install Heroku CLI**
```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login
```

**Step 2: Create App**
```bash
# Create Heroku app
heroku create your-autoforms-app

# Add buildpack
heroku buildpacks:add heroku/python
```

**Step 3: Configure Environment**
```bash
# Set environment variables
heroku config:set APP_ENV=production
heroku config:set MONGODB_URI="mongodb+srv://..."
heroku config:set OPENAI_KEY="sk-..."
heroku config:set JWT_SECRET="$(openssl rand -base64 32)"
```

**Step 4: Configure Procfile**
```
# Procfile (create if not exists)
web: python start_production.py
```

**Step 5: Deploy**
```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

### Heroku Benefits
- ✅ Mature platform
- ✅ Extensive add-ons
- ✅ Easy scaling
- ✅ Good documentation

---

## 4. Vercel (For Static + Serverless)

**Note**: Vercel is primarily for frontend. For full-stack deployment, use Render or Railway.

### Frontend Only Setup
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy frontend assets
vercel --prod
```

### Configuration
```json
// vercel.json
{
  "builds": [
    {
      "src": "backend/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "backend/main.py"
    }
  ]
}
```

---

## 5. DigitalOcean App Platform

### Setup
**Step 1: Create App**
- Go to DigitalOcean App Platform
- Connect GitHub repository

**Step 2: Configure**
```yaml
# .do/app.yaml
name: autoforms
services:
- name: web
  source_dir: /
  github:
    repo: your-username/autoforms
    branch: main
  run_command: python start_production.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: APP_ENV
    value: production
  - key: MONGODB_URI
    value: ${MONGODB_URI}
  - key: OPENAI_KEY  
    value: ${OPENAI_KEY}
```

---

## 🐳 Docker Deployment

### Dockerfile
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash autoforms
RUN chown -R autoforms:autoforms /app
USER autoforms

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Start application
CMD ["python", "start_production.py"]
```

### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  autoforms:
    build: .
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - MONGODB_URI=mongodb://mongo:27017/autoforms
      - OPENAI_KEY=${OPENAI_KEY}
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - mongo
    restart: unless-stopped

  mongo:
    image: mongo:6
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  mongo_data:
```

### Deploy with Docker
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f autoforms

# Scale service
docker-compose up -d --scale autoforms=3
```

---

## 🏗️ Self-Hosted Deployment

### Ubuntu/Debian Server

**Step 1: System Setup**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv nginx git

# Create application user
sudo useradd --system --create-home autoforms
sudo usermod -aG www-data autoforms
```

**Step 2: Application Setup**
```bash
# Switch to app user
sudo su - autoforms

# Clone repository
git clone https://github.com/your-username/autoforms.git
cd autoforms

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit with your values
```

**Step 3: Systemd Service**
```ini
# /etc/systemd/system/autoforms.service
[Unit]
Description=AutoForms Application
After=network.target

[Service]
Type=simple
User=autoforms
Group=autoforms
WorkingDirectory=/home/autoforms/autoforms
Environment=PATH=/home/autoforms/autoforms/venv/bin
ExecStart=/home/autoforms/autoforms/venv/bin/python start_production.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable autoforms
sudo systemctl start autoforms
sudo systemctl status autoforms
```

**Step 4: Nginx Configuration**
```nginx
# /etc/nginx/sites-available/autoforms
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/autoforms/autoforms/backend/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/autoforms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Step 5: SSL with Let's Encrypt**
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 📊 Monitoring & Maintenance

### Health Monitoring
Set up monitoring for:
- `/healthz` - Basic health check
- `/health/ready` - Comprehensive readiness
- `/health/live` - Liveness probe

### Log Management
```bash
# View application logs
sudo journalctl -u autoforms -f

# Rotate logs
sudo logrotate -f /etc/logrotate.d/autoforms
```

### Backup Strategy
```bash
# Database backup script
#!/bin/bash
mongodump --uri="$MONGODB_URI" --out="/backup/$(date +%Y%m%d)"
```

### Updates
```bash
# Update application
cd /home/autoforms/autoforms
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart autoforms
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check MongoDB URI format
echo $MONGODB_URI

# Test connection
python -c "import pymongo; print(pymongo.MongoClient('$MONGODB_URI').admin.command('ping'))"
```

**2. OpenAI API Errors**
```bash
# Verify API key
curl -H "Authorization: Bearer $OPENAI_KEY" https://api.openai.com/v1/models
```

**3. Port Already in Use**
```bash
# Find process using port
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>
```

**4. Environment Variables Not Loading**
```bash
# Check .env file exists
ls -la .env

# Validate environment
python validate_deployment.py
```

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run with debug
python start_production.py
```

---

## 📈 Performance Optimization

### Production Optimizations
- ✅ Use `uvloop` for better async performance (Linux/Mac)
- ✅ Enable Redis caching
- ✅ Configure CDN for static assets
- ✅ Set up database connection pooling
- ✅ Use Nginx for reverse proxy and static files

### Scaling
```bash
# Horizontal scaling with multiple workers
gunicorn backend.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Database Optimization
```python
# Ensure indexes are created
python -c "
from backend.services.db_indexes import create_indexes
import asyncio
asyncio.run(create_indexes())
"
```

---

**Need Help?** 
- 📧 Contact: support@autoforms.com
- 📖 Documentation: Check README.md
- 🐛 Issues: Create GitHub issue

---

✨ **AutoForms is now ready for production!** ✨