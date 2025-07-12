# 🎬 Driftly YouTube - AI Video Automation Studio

Create stunning AI-generated videos with just a text prompt! Automate your YouTube content creation with cutting-edge AI technology.

![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.8+-green?style=for-the-badge)
![Grok](https://img.shields.io/badge/Grok-3-purple?style=for-the-badge)
![Veo](https://img.shields.io/badge/Google%20Veo-3-orange?style=for-the-badge)

## ✨ Features

- 🤖 **AI Script Generation** - Powered by Grok 3 from X.AI
- 🎥 **Video Creation** - Using Google's Veo 3 (state-of-the-art video AI)
- 📺 **YouTube Integration** - Automatic uploads to your channel
- 🎨 **Beautiful UI** - Dark theme with glassmorphism effects
- 📊 **Google Sheets** - Track topics and video history
- 🔒 **Secure** - Bring your own API keys - stored only in your browser session
- ⚡ **Fast** - Generate videos in ~60 seconds

## 🖼️ Screenshots

<details>
<summary>Click to see the interface</summary>

### Main Interface
The beautiful dark-themed UI with glassmorphism effects

### Setup Wizard
Easy first-time setup with clear instructions

### Video Generation
Real-time progress tracking

</details>

## 🎯 Perfect For

- 📱 YouTube Shorts creators
- 🎓 Educational content
- 💻 Tech tutorials
- 🚀 Product demos
- 📈 Social media marketing
- 🎨 Creative experiments

## 🔒 Security Notice

**IMPORTANT**: This project requires API keys to function. Please follow these security best practices:
- **Never commit API keys** to version control
- Store keys in `.env` file (see `.env.example` for template)
- Keep `.env` in `.gitignore` (already configured)
- Rotate keys regularly
- Use environment variables in production

## 🚀 Quick Start

### 1. Get Your API Keys (5 minutes)

You'll need two API keys:

#### Grok API Key:
1. Go to [console.x.ai](https://console.x.ai)
2. Sign up or log in with X/Twitter account
3. Click "API Keys" in the dashboard
4. Click "Create API Key"
5. Copy your key (starts with `xai-`)

#### FAL API Key:
1. Go to [fal.ai/dashboard](https://fal.ai/dashboard)
2. Sign up for free account
3. Click "API Keys" in the sidebar
4. Click "Create new key"
5. Copy the entire key (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:xxxx...`)

### 2. Run the App

#### Option A: If you have Python installed
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

#### Option B: Use the provided executable (Windows)
Just double-click `AI_Video_Studio.exe` (coming soon)

### 3. Open Your Browser

Go to: http://localhost:5000

### 4. First Time Setup

The app will guide you through:
1. Enter your API keys (saved locally, never shared)
2. Optional: Add Google Sheets ID for topic management
3. Optional: Enable YouTube uploads

### 5. Create Your First Video!

1. Type a topic or use a template
2. Click "Generate Video"
3. Wait ~1 minute
4. Watch your AI-generated video!

## 💡 Video Ideas That Work Well

- **Tech Tips**: "Python one-liner that will blow your mind"
- **Explanations**: "How recursion works in 8 seconds"
- **Comparisons**: "React vs Vue in one sentence"
- **Demos**: "Build a website with one command"
- **Facts**: "The craziest bug in computer history"

## 💰 Costs

- **Each 8-second video**: ~$6.10 total
  - Grok 3 API: ~$0.10 per script
  - Google Veo 3 (via FAL): ~$0.75/second = $6 per video
  - YouTube upload: Free
- **FAL Credits**: New accounts may get free credits to try
- **Model Used**: `fal-ai/veo3/fast` - Google's latest video AI

## 🛠️ Advanced Setup

### Google Sheets Integration (Optional)

**Easiest Method - Use Template:**
1. [Click here to copy the template](https://docs.google.com/spreadsheets/d/1hADNv4Pd_Ikr2SUy8eg_GpcX1cMi_YjIdpAJzLIpeGQ/copy)
2. Google will create your own copy
3. Get your Sheet ID from the URL:
   - Your URL: `https://docs.google.com/spreadsheets/d/YOUR_ID_HERE/edit`
   - Copy the ID part
4. Paste in the app setup

**Manual Method:**
1. Go to [sheets.new](https://sheets.new)
2. Create two tabs:
   - **Topics** tab: Add headers in row 1: `ID | Status | Topic`
   - **Published** tab: Add headers in row 1: `ID | Topic | Title | Video URL | Published Date | Views`
3. Share with: `admin-507@video-465521.iam.gserviceaccount.com` (Editor access)
4. Copy Sheet ID from URL
5. Add to setup

**What it does:** Tracks your video topics and history automatically

### YouTube Auto-Upload (Optional)

**Quick Version:**
1. The app will guide you through everything - just check "Enable YouTube uploads" in setup
2. Follow the step-by-step instructions shown
3. Paste your credentials when prompted

**Detailed Steps:**
1. Make sure you have a YouTube channel
2. Go to [Google Cloud Console](https://console.cloud.google.com)
3. Create new project → Enable YouTube Data API v3
4. Create OAuth 2.0 credentials (Desktop app type)
5. Download the JSON file
6. Open it, copy everything, paste in the app
7. First video will ask you to log in to YouTube (one time only)

### Running on Schedule

To generate videos automatically:
```bash
python scheduler.py
```

## 🔧 Troubleshooting

**"API Key Invalid"**
- Make sure you copied the entire key
- Check if your FAL account has credits

**"Video Generation Failed"**
- Try a simpler prompt
- Check your internet connection
- Verify API keys are correct

**Videos Not Uploading to YouTube**
- YouTube upload is optional
- Videos are saved locally in `output/` folder
- Check YouTube API quota (limited per day)

## 🤝 Need Help?

- Check the Help button in the app
- Videos are saved in: `output/`
- Logs are in: `logs/`
- Contact Chris for support

## 🎯 Tips for Great Videos

1. **Be Specific**: "How to center a div in CSS" > "CSS tips"
2. **Add Visual Words**: "with animations", "visual example", "step by step"
3. **Keep It Simple**: 8 seconds = one main point
4. **Use Templates**: Start with templates, then customize

## 🔒 Privacy

- API keys are stored locally on your computer
- Never shared or uploaded anywhere
- Videos can be kept private (local only)

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [X.AI](https://x.ai) for Grok API
- [FAL](https://fal.ai) for Google Veo 3 access
- [Google](https://deepmind.google/technologies/veo/) for Veo 3 technology

## ⚠️ Disclaimer

This tool uses AI to generate content. Please review all generated videos before publishing. You are responsible for the content you create and publish.

---

<p align="center">
  Built with ❤️ by <a href="https://github.com/apedonkey">apedonkey</a>
  <br>
  Powered by Grok AI & Google Veo 3
  <br><br>
  <a href="https://github.com/apedonkey/Driftly-Youtube">
    <img src="https://img.shields.io/github/stars/apedonkey/Driftly-Youtube?style=social" alt="GitHub stars">
  </a>
</p>