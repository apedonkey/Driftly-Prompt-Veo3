#!/usr/bin/env python3
"""
Video Scheduler - Processes scheduled videos from Google Sheets
Run this script via cron to automatically create videos at scheduled times
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict
from loguru import logger
from dotenv import load_dotenv
from video_automation import VideoAutomation
import json

# Load environment variables
load_dotenv()

# Configure logging
logger.add("logs/scheduler_{time}.log", rotation="1 week", retention="4 weeks")

class VideoScheduler:
    def __init__(self):
        self.automation = VideoAutomation()
        
    def get_due_videos(self) -> List[Dict]:
        """Get videos that are due to be created"""
        try:
            scheduled_sheet = self.automation.spreadsheet.worksheet('Scheduled')
            all_records = scheduled_sheet.get_all_records()
            
            due_videos = []
            current_time = datetime.now()
            
            for idx, record in enumerate(all_records, start=2):  # Start at 2 to account for header
                if record.get('Status') == 'Pending' and record.get('Topic'):
                    scheduled_time = datetime.fromisoformat(record.get('Scheduled Time'))
                    
                    # Check if video is due (scheduled time has passed)
                    if scheduled_time <= current_time:
                        video_data = {
                            'row': idx,
                            'id': record.get('ID'),
                            'topic': record.get('Topic'),
                            'duration': int(record.get('Duration', 8)),
                            'style': record.get('Style', 'cinematic'),
                            'scheduled_time': scheduled_time
                        }
                        
                        # Check if we have pre-generated script data
                        script_data_json = record.get('Script Data', '')
                        if script_data_json:
                            try:
                                video_data['script_data'] = json.loads(script_data_json)
                            except:
                                pass
                        
                        due_videos.append(video_data)
            
            return due_videos
        except Exception as e:
            logger.error(f"Error getting due videos: {str(e)}")
            return []
    
    def process_scheduled_video(self, video_data: Dict):
        """Process a single scheduled video"""
        logger.info(f"Processing scheduled video: {video_data['id']} - {video_data['topic']}")
        
        try:
            # Update status to Processing
            scheduled_sheet = self.automation.spreadsheet.worksheet('Scheduled')
            scheduled_sheet.update_cell(video_data['row'], 6, 'Processing')
            
            # Determine number of segments
            num_segments = video_data['duration'] // 8
            
            # Check if we have pre-generated script data
            if 'script_data' in video_data and video_data['script_data']:
                logger.info("Using pre-generated script data")
                script_data = video_data['script_data']
            else:
                # Generate script if not pre-generated
                logger.info("Generating script data")
                if num_segments == 1:
                    script_data = self.automation.generate_script(
                        video_data['topic'], 
                        style=video_data['style']
                    )
                else:
                    script_data = self.automation.generate_multi_segment_script(
                        video_data['topic'], 
                        num_segments, 
                        style=video_data['style']
                    )
            
            # Generate video
            if num_segments == 1:
                video_path = self.automation.generate_video(script_data)
            else:
                # Create a mock job status for multi-segment
                job_status = {'progress': ''}
                video_path = self.automation.generate_multi_segment_video(
                    script_data, 
                    None,  # No image paths for scheduled videos yet
                    job_status
                )
            
            # Upload to YouTube if configured
            if self.automation.youtube:
                video_url = self.automation.upload_to_youtube(video_path, script_data)
            else:
                video_url = f"local://{video_path}"
            
            # Update scheduled sheet with success
            scheduled_sheet.update_cell(video_data['row'], 6, 'Completed')
            scheduled_sheet.update_cell(video_data['row'], 8, video_url)
            
            # Also add to Published sheet
            self.automation.videos_sheet.append_row([
                video_data['id'],
                video_data['topic'],
                script_data['title'],
                video_url,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                0  # Initial view count
            ])
            
            logger.success(f"Successfully created scheduled video: {video_data['id']}")
            
        except Exception as e:
            logger.error(f"Error processing scheduled video {video_data['id']}: {str(e)}")
            # Update status to Error
            try:
                scheduled_sheet = self.automation.spreadsheet.worksheet('Scheduled')
                scheduled_sheet.update_cell(video_data['row'], 6, 'Error')
            except:
                pass
    
    def run(self):
        """Main scheduler run method"""
        logger.info("Starting video scheduler run")
        
        # Get all due videos
        due_videos = self.get_due_videos()
        
        if not due_videos:
            logger.info("No videos due for processing")
            return
        
        logger.info(f"Found {len(due_videos)} videos due for processing")
        
        # Process each due video
        for video in due_videos:
            self.process_scheduled_video(video)
            
        logger.info("Scheduler run completed")

def main():
    """Run the scheduler"""
    scheduler = VideoScheduler()
    scheduler.run()

if __name__ == "__main__":
    main()