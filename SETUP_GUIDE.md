# Video Automation Setup Guide

## Prerequisites
- Python 3.8+
- Google Cloud account
- X.AI account (for Grok API)
- FAL account
- YouTube channel

## Setup Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Google Sheets Setup
1. Create a new Google Sheet with 2 tabs:
   - **Topics**: Columns: ID, Topic, Status
   - **Published**: Columns: ID, Topic, Title, Video URL, Published Date, Views

2. Get Google Sheets credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select existing
   - Enable Google Sheets API
   - Create Service Account credentials
   - Download JSON key file to `config/google_credentials.json`
   - Share your Google Sheet with the service account email

### 3. Grok API Setup
1. Get API key from [X.AI](https://x.ai)
2. Add to `.env` file

### 4. FAL API Setup
1. Sign up at [fal.ai](https://fal.ai)
2. Get API key from dashboard
3. Add to `.env` file

### 5. YouTube API Setup
1. Enable YouTube Data API v3 in Google Cloud Console
2. Create OAuth 2.0 credentials (Desktop application)
3. Download client secrets to `config/youtube_client_secrets.json`
4. Run the script once to authenticate:
   ```bash
   python video_automation.py
   ```

### 6. Configure Environment
Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

### 7. Add Topics to Google Sheet
Add your video topics to the Topics sheet:
- ID: Unique identifier (e.g., 001, 002)
- Topic: The subject for the video
- Status: Leave empty (will be updated automatically)

## Running the Automation

### Manual Run (Single Video)
```bash
python video_automation.py
```

### Scheduled Run (2-3 videos daily)
```bash
python scheduler.py
```

### Run as Service (Linux)
Create systemd service at `/etc/systemd/system/video-automation.service`:
```ini
[Unit]
Description=Video Automation Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/video-automation
ExecStart=/usr/bin/python3 /path/to/video-automation/scheduler.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable video-automation
sudo systemctl start video-automation
```

### Run on Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to "Daily"
4. Set action to start `python.exe` with argument `scheduler.py`
5. Set working directory to project folder

## Monitoring
- Check `logs/` folder for detailed logs
- Monitor Google Sheets for status updates
- YouTube Studio for video performance

## Troubleshooting
- **Authentication errors**: Re-run authentication flow
- **API limits**: Check rate limits for each service
- **Video generation fails**: Check FAL API status and credits
- **Upload fails**: Verify YouTube API quotas