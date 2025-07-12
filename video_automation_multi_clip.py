#!/usr/bin/env python3
"""
Multi-clip Video Automation for YouTube Shorts
Generates multiple 8-second clips and stitches them together
"""

import os
import json
import time
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import requests
from loguru import logger
from dotenv import load_dotenv
import fal_client

# Load environment variables
load_dotenv()

# Configure logging
logger.add("logs/video_automation_{time}.log", rotation="1 day", retention="7 days")

class MultiClipVideoAutomation:
    def __init__(self):
        self.setup_google_sheets()
        self.setup_youtube()
        self.grok_api_key = os.getenv('GROK_API_KEY')
        self.grok_api_url = os.getenv('GROK_API_URL')
        
    def setup_google_sheets(self):
        """Initialize Google Sheets connection"""
        creds = Credentials.from_service_account_file(
            os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH'),
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.gc = gspread.authorize(creds)
        self.spreadsheet = self.gc.open_by_key(os.getenv('SPREADSHEET_ID'))
        self.topics_sheet = self.spreadsheet.worksheet('Topics')
        self.videos_sheet = self.spreadsheet.worksheet('Published')
        
    def setup_youtube(self):
        """Initialize YouTube API connection"""
        SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        creds = None
        
        token_path = os.getenv('YOUTUBE_CREDENTIALS_PATH')
        if os.path.exists(token_path):
            with open(token_path, 'r') as token:
                creds_data = json.load(token)
                from google.oauth2.credentials import Credentials as OAuthCredentials
                creds = OAuthCredentials.from_authorized_user_info(creds_data, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    os.getenv('YOUTUBE_CLIENT_SECRETS_PATH'), SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.youtube = build('youtube', 'v3', credentials=creds)
        
    def get_next_topic(self) -> Optional[Dict]:
        """Get next unprocessed topic from Google Sheets"""
        all_records = self.topics_sheet.get_all_records()
        for idx, record in enumerate(all_records, start=2):
            if record.get('Status') != 'Published':
                return {'row': idx, 'topic': record.get('Topic'), 'id': record.get('ID')}
        return None
        
    def generate_multi_scene_script(self, topic: str) -> Dict:
        """Generate script with multiple 8-second scenes for a 30-second video"""
        logger.info(f"Generating multi-scene script for topic: {topic}")
        
        headers = {
            'Authorization': f'Bearer {self.grok_api_key}',
            'Content-Type': 'application/json'
        }
        
        prompt = f"""Create a compelling 30-second YouTube Shorts script about: {topic}
        
        Format the response as JSON with:
        - title: Catchy title (include relevant emoji, max 100 chars)
        - description: YouTube Shorts description with #Shorts #YouTubeShorts and other relevant hashtags
        - scenes: Array of exactly 4 scenes, each 7-8 seconds when narrated:
            - scene_number: 1-4
            - narration: What to say in this scene (7-8 seconds)
            - visual_prompt: Detailed visual description for this scene
        - hook: Opening hook text (first 3 seconds must grab attention)
        
        Make sure each scene flows naturally into the next, creating a cohesive 30-second story.
        """
        
        data = {
            'model': 'grok-3',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.7
        }
        
        response = requests.post(self.grok_api_url, headers=headers, json=data)
        response.raise_for_status()
        
        content = response.json()['choices'][0]['message']['content']
        return json.loads(content)
        
    def generate_video_clip(self, scene_data: Dict, scene_number: int) -> str:
        """Generate a single 8-second video clip"""
        logger.info(f"Generating video clip {scene_number}")
        
        def on_queue_update(update):
            if isinstance(update, fal_client.InProgress):
                for log in update.logs:
                    logger.info(f"Veo3 Progress (Scene {scene_number}): {log['message']}")
        
        # Add scene context to prompt
        prompt = f"Scene {scene_number} of 4, vertical 9:16 format: {scene_data['visual_prompt']}"
        
        result = fal_client.subscribe(
            "fal-ai/veo3/fast",
            arguments={
                "prompt": prompt,
                "aspect_ratio": "9:16",
                "duration": "8s"
            },
            with_logs=True,
            on_queue_update=on_queue_update
        )
        
        # Download video clip
        video_url = result.get('video', {}).get('url') or result.get('url') or result.get('video_url')
        clip_path = f"output/clip_{scene_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        response = requests.get(video_url)
        with open(clip_path, 'wb') as f:
            f.write(response.content)
            
        logger.info(f"Clip {scene_number} saved to: {clip_path}")
        return clip_path
        
    def stitch_videos(self, clip_paths: List[str], script_data: Dict) -> str:
        """Stitch multiple clips together using ffmpeg"""
        logger.info("Stitching video clips together")
        
        # Create concat file
        concat_file = "output/concat_list.txt"
        with open(concat_file, 'w') as f:
            for clip in clip_paths:
                f.write(f"file '{os.path.abspath(clip)}'\n")
        
        # Output path
        output_path = f"output/final_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        # FFmpeg command to concatenate videos
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            output_path
        ]
        
        subprocess.run(cmd, check=True)
        
        # Clean up temp files
        os.remove(concat_file)
        for clip in clip_paths:
            os.remove(clip)
            
        logger.info(f"Final video saved to: {output_path}")
        return output_path
        
    def upload_to_youtube(self, video_path: str, script_data: Dict) -> str:
        """Upload video to YouTube"""
        logger.info("Uploading to YouTube")
        
        title = script_data['title']
        if '#Shorts' not in title and len(title) < 90:
            title = f"{title} #Shorts"
            
        body = {
            'snippet': {
                'title': title[:100],
                'description': script_data['description'],
                'categoryId': '22',
                'tags': ['Shorts', 'YouTubeShorts', 'AI generated', 'viral', 'trending']
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }
        
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        
        request = self.youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )
        
        response = request.execute()
        video_id = response['id']
        video_url = f"https://youtube.com/watch?v={video_id}"
        
        logger.info(f"Video uploaded: {video_url}")
        return video_url
        
    def update_sheets(self, topic_data: Dict, video_url: str, script_data: Dict):
        """Update Google Sheets with published video info"""
        self.topics_sheet.update_cell(topic_data['row'], 2, 'Published')
        
        self.videos_sheet.append_row([
            topic_data['id'],
            topic_data['topic'],
            script_data['title'],
            video_url,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            0
        ])
        
    def process_video(self):
        """Main workflow: Topic → Multi-Scene Script → Multiple Clips → Stitch → Upload"""
        try:
            # Get next topic
            topic_data = self.get_next_topic()
            if not topic_data:
                logger.info("No pending topics found")
                return
                
            logger.info(f"Processing topic: {topic_data['topic']}")
            
            # Update status to Processing
            self.topics_sheet.update_cell(topic_data['row'], 2, 'Processing')
            
            # Generate multi-scene script
            script_data = self.generate_multi_scene_script(topic_data['topic'])
            
            # Generate video clips for each scene
            clip_paths = []
            for scene in script_data['scenes']:
                clip_path = self.generate_video_clip(scene, scene['scene_number'])
                clip_paths.append(clip_path)
                time.sleep(2)  # Brief pause between API calls
            
            # Stitch clips together
            final_video_path = self.stitch_videos(clip_paths, script_data)
            
            # Upload to YouTube
            video_url = self.upload_to_youtube(final_video_path, script_data)
            
            # Update sheets
            self.update_sheets(topic_data, video_url, script_data)
            
            logger.success(f"30-second video published successfully: {video_url}")
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            if 'topic_data' in locals():
                self.topics_sheet.update_cell(topic_data['row'], 2, 'Error')
            raise

def main():
    """Run multi-clip video automation"""
    automation = MultiClipVideoAutomation()
    automation.process_video()

if __name__ == "__main__":
    main()