# AutoForms Deployment Guide - Railway

## 🚀 Quick Deploy to Railway

### Prerequisites
1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Push your code to GitHub
3. **MongoDB Atlas**: Set up a MongoDB database (recommended for production)
4. **OpenAI API Key**: Get your API key from [OpenAI](https://platform.openai.com)

### 📝 Step-by-Step Deployment

#### 1. Prepare Your Environment Variables

Set up the following environment variables in Railway dashboard:

```bash
# OpenAI Configuration
OPENAI_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Database Configuration (MongoDB Atlas recommended)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/autoforms?retryWrites=true&w=majority
DATABASE_NAME=autoforms

# JWT Security (CRITICAL: Use a strong, unique secret)
JWT_SECRET=your_very_secure_jwt_secret_key_here_minimum_32_characters_long

# Email Configuration (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_specific_password
EMAIL_FROM=your_email@gmail.com

# Application Configuration
BASE_URL=https://your-app-name.railway.app
ADMIN_EMAILS=admin@yourdomain.com,another-admin@yourdomain.com

# Railway Environment
ENVIRONMENT=production
PORT=8000
```

#### 2. Deploy to Railway

1. **Connect Repository**:
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Connect your GitHub repository

2. **Configure Environment**:
   - In your Railway project dashboard
   - Go to "Variables" tab
   - Add all environment variables from above

3. **Deploy**:
   - Railway will automatically detect the configuration
   - The app will build and deploy automatically
   - Your app will be available at: `https://your-app-name.railway.app`

#### 3. Database Setup (MongoDB Atlas)

1. **Create MongoDB Atlas Account**:
   - Go to [mongodb.com/cloud/atlas](https://mongodb.com/cloud/atlas)
   - Create a free cluster

2. **Get Connection String**:
   - In Atlas dashboard, click "Connect"
   - Choose "Connect your application"
   - Copy the connection string
   - Replace `<username>` and `<password>` with your credentials

3. **Configure Database**:
   - Set `MONGODB_URI` to your Atlas connection string
   - Set `DATABASE_NAME` to `autoforms`

#### 4. Email Configuration

1. **Gmail Setup** (recommended):
   - Enable 2-factor authentication
   - Generate an app-specific password
   - Use the app password in `SMTP_PASSWORD`

2. **Other SMTP Providers**:
   - Update `SMTP_HOST` and `SMTP_PORT` accordingly
   - Use appropriate credentials

#### 5. Security Configuration

1. **JWT Secret**:
   - Generate a strong random string (32+ characters)
   - Use a tool like: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

2. **Admin Emails**:
   - Set `ADMIN_EMAILS` to comma-separated list of admin emails
   - These users will have admin privileges

### 🔧 Configuration Files

The project includes these deployment files:

- `railway.json` - Railway configuration
- `nixpacks.toml` - Build configuration
- `Procfile` - Process configuration
- `start.sh` - Startup script
- `requirements.txt` - Python dependencies

### 🌐 Custom Domain (Optional)

1. In Railway dashboard, go to "Settings"
2. Click "Domains"
3. Add your custom domain
4. Update `BASE_URL` environment variable

### 🔍 Monitoring & Logs

- View logs in Railway dashboard under "Deployments"
- Monitor performance and errors
- Set up alerts for critical issues

### 🛠️ Troubleshooting

#### Common Issues:

1. **Database Connection**:
   - Verify MongoDB URI format
   - Check database credentials
   - Ensure IP whitelist includes Railway IPs

2. **OpenAI API**:
   - Verify API key is valid
   - Check API quota and usage
   - Ensure model name is correct

3. **Email Issues**:
   - Check SMTP credentials
   - Verify app-specific password for Gmail
   - Test email configuration

#### Debug Commands:

```bash
# Check environment variables
echo $MONGODB_URI
echo $OPENAI_KEY

# Test database connection
python -c "import pymongo; print(pymongo.version)"

# Check OpenAI connection
python -c "import openai; print(openai.version.VERSION)"
```

### 🚀 Post-Deployment

1. **Test the Application**:
   - Visit your deployed URL
   - Test form generation
   - Verify email functionality
   - Check admin panel access

2. **Monitor Performance**:
   - Watch Railway metrics
   - Monitor database performance
   - Check OpenAI API usage

3. **Backup Strategy**:
   - Set up MongoDB Atlas backups
   - Export environment variables
   - Document deployment process

### 📞 Support

If you encounter issues:
1. Check Railway logs for errors
2. Verify all environment variables are set
3. Test database and API connections
4. Review the troubleshooting section

### 🔐 Security Best Practices

1. **Never commit secrets** to version control
2. **Use strong JWT secrets** (32+ characters)
3. **Rotate API keys** regularly
4. **Enable MongoDB authentication**
5. **Use HTTPS** for all communications
6. **Monitor for suspicious activity**

---

## 📋 Deployment Checklist

- [ ] Railway account created
- [ ] GitHub repository connected
- [ ] MongoDB Atlas database set up
- [ ] OpenAI API key obtained
- [ ] All environment variables configured
- [ ] Application deployed successfully
- [ ] Database connection tested
- [ ] Email functionality verified
- [ ] Admin access confirmed
- [ ] Custom domain configured (optional)
- [ ] Monitoring set up
- [ ] Security measures implemented

Your AutoForms application should now be live and accessible! 🎉