# Google Sheets Setup Guide

## Quick Start - Use Our Template

### Step 1: Copy the Template
**[→ Click Here to Copy Template ←](https://docs.google.com/spreadsheets/d/1hADNv4Pd_Ikr2SUy8eg_GpcX1cMi_YjIdpAJzLIpeGQ/copy)**

This will:
- Create your own copy automatically
- Set up both tabs (Topics & Published) 
- Have all the correct columns ready

### Step 2: Find Your Spreadsheet ID

Look at your browser's address bar:

```
https://docs.google.com/spreadsheets/d/1ABC123YourIDHere456XYZ/edit#gid=0
                                       ^^^^^^^^^^^^^^^^^^^^^^^^
                                       This is your Sheet ID
```

**Example:**
- Full URL: `https://docs.google.com/spreadsheets/d/1hADNv4Pd_Ikr2SUy8eg_GpcX1cMi_YjIdpAJzLIpeGQ/edit`
- Sheet ID: `1hADNv4Pd_Ikr2SUy8eg_GpcX1cMi_YjIdpAJzLIpeGQ`

### Step 3: Share with Service Account (Important!)

1. Click the **Share** button (top right)
2. Add this email: `admin-507@video-465521.iam.gserviceaccount.com`
3. Set permission to **Editor**
4. Click **Send**

### Step 4: Add to App

1. Open the Driftly AI Video Studio app
2. Click **Setup** button
3. Paste your Sheet ID
4. Save!

## What Each Tab Does

### Topics Tab
- **ID**: Unique number (001, 002, etc.)
- **Status**: Empty, Processing, or Published
- **Topic**: Your video ideas

Example:
| ID  | Status    | Topic                                    |
|-----|-----------|------------------------------------------|
| 001 | Published | How AI is changing coding               |
| 002 |           | 5 Python tricks you need to know        |
| 003 |           | Build a website in 60 seconds           |

### Published Tab
Automatically filled when videos are created:
- Tracks all your published videos
- Stores YouTube URLs
- Records publish dates
- Can track view counts

## Troubleshooting

**"Permission denied" error?**
- Make sure you shared the sheet with the service account email
- Check that permission is set to "Editor" not "Viewer"

**Can't find Sheet ID?**
- It's the long string between `/d/` and `/edit` in the URL
- Usually about 44 characters long
- Only letters, numbers, underscores, and hyphens

**Sheet not updating?**
- Verify the Sheet ID is correct in setup
- Check internet connection
- Try refreshing the Google Sheet

## Pro Tips

1. **Pre-fill topics** - Add 10-20 topic ideas at once
2. **Use formulas** - Add a formula to auto-number IDs
3. **Track performance** - Add columns for likes, comments, etc.
4. **Batch processing** - The app processes topics in order

## Why Use Google Sheets?

- **Queue Management**: Add topics anytime, process later
- **History Tracking**: See all your created videos
- **Team Collaboration**: Others can add topic ideas
- **Performance Analytics**: Track which topics do best
- **Backup**: Never lose your video history

---

Still confused? The app works fine without Google Sheets - it's totally optional!