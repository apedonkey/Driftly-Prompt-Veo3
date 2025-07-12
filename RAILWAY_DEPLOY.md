# 🚂 Railway Deployment Guide - Video Automation App

## Overview
This app lets users input their own API keys through the web UI. No need to configure API keys on the server!

## Quick Deploy Steps

### 1. **Prepare Your Code**

```bash
# Add files to git
git add .
git commit -m "Ready for Railway deployment"

# Push to GitHub
git push origin main
```

### 2. **Deploy on Railway**

1. Go to [railway.app](https://railway.app)
2. Click **"Start a New Project"**
3. Choose **"Deploy from GitHub repo"**
4. Connect your GitHub account and select your repository

### 3. **Set Environment Variables**

In Railway's Variables tab, add only these:

```bash
FLASK_ENV=production
FLASK_SECRET_KEY=your-random-secret-key-here
USE_AUTH=false
```

To generate a secret key:
```python
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. **That's It! 🎉**

Railway will:
- Detect your Python app automatically
- Install dependencies from requirements.txt
- Start your app with gunicorn
- Provide you with a URL like: `your-app.railway.app`

## How Users Will Use Your App

1. **Visit your Railway URL**
2. **Click Setup** and enter their own:
   - Grok API key
   - FAL API key  
   - Google Sheets ID (optional)
   - YouTube credentials (optional)
3. **Start creating videos!**

All API keys are stored in the user's browser session - not on your server.

## Important Notes

### Security
- User API keys are stored in encrypted server-side sessions
- Sessions expire after 2 hours for security
- No API keys are logged or stored permanently

### File Uploads
- Users upload images from their local computer
- Images are temporarily stored during video generation
- All temporary files are cleaned up after use

### Limitations on Railway
- **Free tier**: 512MB RAM, may be slow for video generation
- **Hobby tier** ($5/month): 8GB RAM, much better performance
- Generated videos are temporary (not permanently stored)

### Optional: Password Protection

If you want to restrict access to your app:

1. Set in Railway variables:
   ```bash
   USE_AUTH=true
   ```

2. First visitor sets the admin password
3. All subsequent visitors need the password to access

## Monitoring

- Check logs in Railway dashboard
- Monitor memory usage
- Set up error alerts (optional)

## Custom Domain (Optional)

1. In Railway settings, add your domain
2. Update your DNS records as instructed
3. Railway provides free SSL

## Troubleshooting

**App not starting?**
- Check Railway logs for errors
- Verify FLASK_SECRET_KEY is set

**Out of memory?**
- Upgrade to Hobby plan for more RAM
- Video generation requires ~1-2GB RAM

**Sessions expiring?**
- This is normal after 2 hours
- Users just need to re-enter their API keys

## Cost Estimate

- **Your server costs**: Free tier or $5/month
- **User costs**: They pay for their own API usage
  - Grok API: ~$0.10 per video script
  - FAL/Veo3: ~$6 per 8-second video

## Success! 🎉

Your app provides the platform - users bring their own API keys. This way:
- You don't handle sensitive keys
- Users control their own costs
- No API rate limit issues
- Truly scalable solution