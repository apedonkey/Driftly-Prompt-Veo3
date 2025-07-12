# Video Scheduler Setup Guide

The video scheduler allows you to automatically create videos at scheduled times using cron jobs.

## How It Works

1. You schedule videos through the web UI
2. Videos are saved to the "Scheduled" tab in your Google Sheet
3. The scheduler script runs periodically (via cron) and checks for due videos
4. When a video is due, it automatically creates and uploads it
5. The status is updated in the sheet

## Setup Instructions

### 1. Make the scheduler executable
```bash
chmod +x scheduler.py
```

### 2. Test the scheduler manually
```bash
python3 scheduler.py
```

### 3. Set up cron job

Edit your crontab:
```bash
crontab -e
```

Add one of these lines based on how often you want to check:

**Check every 15 minutes:**
```bash
*/15 * * * * cd /path/to/video-automation && /usr/bin/python3 scheduler.py >> logs/cron.log 2>&1
```

**Check every hour:**
```bash
0 * * * * cd /path/to/video-automation && /usr/bin/python3 scheduler.py >> logs/cron.log 2>&1
```

**Check every 30 minutes:**
```bash
*/30 * * * * cd /path/to/video-automation && /usr/bin/python3 scheduler.py >> logs/cron.log 2>&1
```

### 4. Windows Task Scheduler (Alternative)

If you're on Windows, use Task Scheduler instead:

1. Open Task Scheduler
2. Create Basic Task
3. Name: "Video Automation Scheduler"
4. Trigger: Daily, repeat every 15 minutes
5. Action: Start a program
6. Program: `python.exe`
7. Arguments: `C:\path\to\video-automation\scheduler.py`
8. Start in: `C:\path\to\video-automation`

## Google Sheets Structure

The scheduler expects a "Scheduled" worksheet with these columns:
- ID: Unique identifier (e.g., SCH0001)
- Topic: Video topic/description
- Scheduled Time: ISO format datetime (e.g., 2024-01-15T14:30:00)
- Duration: Video duration in seconds (8, 16, 24, or 32)
- Style: Video style (cinematic, realistic, dramatic, vibrant, tech)
- Status: Pending, Processing, Completed, Error, or Cancelled
- Created At: When the schedule was created
- Video ID: URL of the created video (filled after creation)

## Monitoring

- Check `logs/scheduler_*.log` for scheduler activity
- Check the "Scheduled" sheet for video status
- Completed videos also appear in the "Published" sheet

## Troubleshooting

1. **Videos not being created:**
   - Check if the scheduler is running: `ps aux | grep scheduler.py`
   - Check logs: `tail -f logs/scheduler_*.log`
   - Verify cron is working: `grep CRON /var/log/syslog`

2. **Authentication errors:**
   - Ensure all environment variables are set in `.env`
   - Check Google Sheets credentials are valid
   - Verify YouTube credentials if uploading

3. **Time zone issues:**
   - The scheduler uses system time
   - Ensure your server time zone matches your scheduling expectations
   - You can set TZ in cron: `TZ=America/New_York` before the cron command

## Best Practices

1. **Schedule wisely:** Don't schedule too many videos at the same time
2. **Monitor credits:** Keep track of your API credits (Grok and FAL)
3. **Test first:** Always test with a single scheduled video before bulk scheduling
4. **Check regularly:** Monitor the Scheduled sheet for any errors
5. **Backup:** Keep backups of your Google Sheets data

## Cost Considerations

Remember that each scheduled video will consume:
- Grok API credits (~$0.10 per script)
- FAL.ai credits (~$6.00 per 8-second segment)
- YouTube API quota (if uploading)

Plan your schedule according to your budget!