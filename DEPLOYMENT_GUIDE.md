# 🚀 Deployment Guide - Video Automation App

## Pre-Deployment Checklist

### 1. **Security Configuration**
```bash
# Set these in your .env file
USE_AUTH=true
FLASK_SECRET_KEY=<generate-strong-random-key>
ADMIN_PASSWORD_HASH=<will-be-generated-on-first-login>
```

### 2. **Remove Development Settings**
- Change `app.run(debug=True)` to `app.run(debug=False)` in app.py
- Set `SESSION_COOKIE_SECURE=True` only if using HTTPS

## Deployment Options

### Option 1: **Heroku** (Easiest for beginners)

1. **Install Heroku CLI**
   ```bash
   # Visit https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Create Procfile**
   ```bash
   echo "web: gunicorn app:app" > Procfile
   ```

3. **Add gunicorn to requirements.txt**
   ```bash
   echo "gunicorn" >> requirements.txt
   ```

4. **Deploy**
   ```bash
   heroku create your-app-name
   heroku config:set USE_AUTH=true
   heroku config:set FLASK_SECRET_KEY=your-secret-key
   git push heroku main
   ```

**Pros**: Free tier available, easy SSL, automatic scaling
**Cons**: Limited free hours, cold starts

### Option 2: **Railway** (Modern & Simple)

1. **Connect GitHub**
   - Visit [railway.app](https://railway.app)
   - Connect your GitHub repo
   - Railway auto-detects Flask

2. **Set Environment Variables**
   - Add all your .env variables in Railway dashboard
   - Railway provides SSL automatically

**Pros**: Generous free tier, fast deploys, great UI
**Cons**: Requires GitHub integration

### Option 3: **DigitalOcean App Platform**

1. **Create app.yaml**
   ```yaml
   name: video-automation
   services:
   - name: web
     environment_slug: python
     github:
       branch: main
       deploy_on_push: true
       repo: your-username/your-repo
     run_command: gunicorn app:app
     http_port: 8080
   ```

2. **Deploy via DO dashboard**

**Pros**: $5/month, reliable, good performance
**Cons**: Not free

### Option 4: **VPS (Full Control)**

For Ubuntu/Debian VPS:

1. **Install dependencies**
   ```bash
   sudo apt update
   sudo apt install python3-pip nginx supervisor
   pip3 install -r requirements.txt
   pip3 install gunicorn
   ```

2. **Create systemd service**
   ```bash
   sudo nano /etc/systemd/system/videoapp.service
   ```

   ```ini
   [Unit]
   Description=Video Automation App
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/var/www/video-automation
   Environment="PATH=/var/www/video-automation/venv/bin"
   ExecStart=/var/www/video-automation/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app

   [Install]
   WantedBy=multi-user.target
   ```

3. **Configure Nginx**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       client_max_body_size 20M;  # For file uploads
   }
   ```

4. **Enable HTTPS with Let's Encrypt**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

**Pros**: Full control, best performance, one-time cost
**Cons**: Requires Linux knowledge, manual updates

### Option 5: **Google Cloud Run** (Serverless)

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD exec gunicorn --bind :$PORT app:app
   ```

2. **Deploy**
   ```bash
   gcloud run deploy video-app --source .
   ```

**Pros**: Scales to zero, pay per use, Google infrastructure
**Cons**: Cold starts, complexity

## Important Considerations

### 1. **API Keys Security**
- Never commit .env file
- Use platform's environment variables
- Consider using a secrets manager

### 2. **File Storage**
- Videos in `output/` won't persist on serverless platforms
- Consider using cloud storage (S3, Google Cloud Storage)
- Update code to upload videos to cloud storage

### 3. **Session Storage**
- Default Flask sessions won't work across multiple instances
- Use Redis for session storage:
  ```python
  # Add to requirements.txt: redis, flask-session
  from flask_session import Session
  import redis
  
  app.config['SESSION_TYPE'] = 'redis'
  app.config['SESSION_REDIS'] = redis.from_url(os.environ.get('REDIS_URL'))
  Session(app)
  ```

### 4. **Database (Optional)**
- For user management, consider PostgreSQL
- Most platforms offer managed databases

### 5. **Monitoring**
- Add error tracking (Sentry)
- Use platform's logging features
- Monitor API usage and costs

## Quick Start Recommendations

**For beginners**: Start with Railway or Heroku
**For production**: Use DigitalOcean App Platform or VPS
**For scale**: Use Google Cloud Run or AWS

## Environment Variables Template

```env
# Production settings
FLASK_ENV=production
USE_AUTH=true
FLASK_SECRET_KEY=generate-very-long-random-string

# API Keys (from your .env)
GROK_API_KEY=xai-your-key
FAL_KEY=your-fal-key
SPREADSHEET_ID=your-sheet-id

# Optional
REDIS_URL=redis://your-redis-url
SENTRY_DSN=your-sentry-dsn
```

## Post-Deployment

1. **Test everything**
   - Authentication works
   - File uploads work
   - Video generation works
   - API rate limits work

2. **Monitor costs**
   - Set up billing alerts
   - Monitor API usage
   - Check storage usage

3. **Backup**
   - Regular database backups
   - Keep local copies of important videos

Ready to deploy? Choose your platform and follow the steps above! 🚀