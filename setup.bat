@echo off
echo Setting up Video Automation Environment...
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Setup complete! 
echo.
echo Next steps:
echo 1. Copy .env.example to .env and fill in your API keys
echo 2. Set up Google Sheets and YouTube credentials as per SETUP_GUIDE.md
echo 3. Run: python video_automation.py (for single video)
echo 4. Run: python scheduler.py (for automated scheduling)
echo.
pause