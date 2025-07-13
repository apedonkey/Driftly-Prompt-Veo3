#!/usr/bin/env python3
"""
AI Video Automation Workflow
Generates 2-3 videos daily using Grok API and Google Veo 3
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import requests
from secure_logger import setup_secure_logger
logger = setup_secure_logger()
from dotenv import load_dotenv
import fal_client
import subprocess
import tempfile
from prompt_optimizer import PromptOptimizer

# Load environment variables
load_dotenv()

# Configure logging
logger.add("logs/video_automation_{time}.log", rotation="1 day", retention="7 days")

class VideoAutomation:
    def _analyze_images_with_grok2(self, image_paths: List[str]) -> str:
        """Analyze images using Grok 2 Vision model"""
        logger.info("Analyzing images with Grok 2 Vision")
        
        headers = {
            'Authorization': f'Bearer {self.grok_api_key}',
            'Content-Type': 'application/json'
        }
        
        # Prepare images for Grok 2 Vision
        image_content = []
        import base64
        from PIL import Image
        import io
        
        for i, img_path in enumerate(image_paths):
            try:
                with Image.open(img_path) as img:
                    logger.info(f"Processing image for Grok 2: {img.size}, format: {img.format}")
                    
                    if img.mode not in ('RGB', 'L'):
                        img = img.convert('RGB')
                    
                    # Resize if needed
                    max_size = 2048
                    if max(img.size) > max_size:
                        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    
                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG', quality=85, optimize=True)
                    buffer.seek(0)
                    
                    image_data = base64.b64encode(buffer.read()).decode('utf-8')
                    
                    image_content.append({
                        'type': 'image_url',
                        'image_url': {
                            'url': f"data:image/jpeg;base64,{image_data}"
                        }
                    })
                logger.info(f"Successfully prepared image {i+1} for Grok 2")
            except Exception as e:
                logger.error(f"Failed to prepare image for Grok 2: {e}")
        
        if not image_content:
            return ""
        
        # Create prompt for image analysis
        analysis_prompt = """Analyze these reference images and describe:
1. Main subjects, characters, or objects visible
2. Visual style, colors, and composition
3. Lighting and atmosphere
4. Any text, UI elements, or specific details
5. How these visual elements could be incorporated into a video

Be specific and detailed in your description."""
        
        message_content = [
            {'type': 'text', 'text': analysis_prompt}
        ] + image_content
        
        data = {
            'model': 'grok-2-vision-1212',  # Using Grok 2 Vision model
            'messages': [{'role': 'user', 'content': message_content}],
            'temperature': 0.7
        }
        
        try:
            response = requests.post(self.grok_api_url, headers=headers, json=data)
            
            if response.status_code != 200:
                logger.error(f"Grok 2 Vision API failed - Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return ""
            
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            logger.info("Image analysis successful")
            return content
            
        except Exception as e:
            logger.error(f"Failed to analyze images with Grok 2: {e}")
            return ""
    
    def __init__(self, skip_external_setup=False):
        # Allow skipping external service setup for web UI usage
        if not skip_external_setup:
            try:
                self.setup_google_sheets()
            except Exception as e:
                logger.warning(f"Google Sheets setup failed: {e}")
                self.gc = None
                self.spreadsheet = None
                self.topics_sheet = None
                self.videos_sheet = None
            
            try:
                self.setup_youtube()
            except Exception as e:
                logger.warning(f"YouTube setup failed: {e}")
                self.youtube = None
        else:
            # Initialize as None when skipping setup
            self.gc = None
            self.spreadsheet = None
            self.topics_sheet = None
            self.videos_sheet = None
            self.youtube = None
            
        self.grok_api_key = os.getenv('GROK_API_KEY')
        self.grok_api_url = os.getenv('GROK_API_URL', 'https://api.x.ai/v1/chat/completions')
        self.fal_api_key = os.getenv('FAL_API_KEY')
        self.prompt_optimizer = PromptOptimizer()
        
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
                # Create credentials from saved token
                from google.oauth2.credentials import Credentials as OAuthCredentials
                creds = OAuthCredentials.from_authorized_user_info(creds_data, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    os.getenv('YOUTUBE_CLIENT_SECRETS_PATH'), SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.youtube = build('youtube', 'v3', credentials=creds)
        
    def get_next_topic(self) -> Optional[Dict]:
        """Get next unprocessed topic from Google Sheets"""
        all_records = self.topics_sheet.get_all_records()
        for idx, record in enumerate(all_records, start=2):  # Start at 2 (header is row 1)
            if record.get('Status') != 'Published':
                return {'row': idx, 'topic': record.get('Topic'), 'id': record.get('ID')}
        return None
        
    def generate_script(self, topic: str, style: str = 'cinematic', image_paths: Optional[List[str]] = None) -> Dict:
        """Generate video script using Grok API with advanced cinematography prompting and image analysis"""
        logger.info(f"Generating script for topic: {topic} in {style} style")
        if image_paths:
            logger.info(f"Analyzing {len(image_paths)} reference images")
        
        headers = {
            'Authorization': f'Bearer {self.grok_api_key}',
            'Content-Type': 'application/json'
        }
        
        # Style-specific instructions
        style_instructions = {
            'cinematic': "Use dramatic camera movements, film-like color grading, shallow depth of field, and professional cinematography techniques.",
            'realistic': "Focus on natural lighting, realistic physics, authentic movements, and documentary-style camera work.",
            'dramatic': "Emphasize high contrast lighting, moody atmosphere, dynamic camera angles, and emotional intensity.",
            'vibrant': "Use bright colors, energetic camera movements, high-key lighting, and upbeat pacing.",
            'tech': "Apply futuristic aesthetics, digital effects, clean compositions, and modern visual language."
        }
        
        # Analyze images with Grok 2 Vision if provided
        image_description = ""
        if image_paths:
            image_description = self._analyze_images_with_grok2(image_paths)
            if image_description:
                logger.info(f"Image analysis complete: {image_description[:200]}...")
            else:
                logger.warning("Image analysis failed, continuing without image context")
        
        prompt = f"""You are an expert cinematographer and AI video prompt engineer. Create a compelling 8-second video script about: {topic}

        STYLE DIRECTIVE: {style.upper()} - {style_instructions.get(style, style_instructions['cinematic'])}

        {f"REFERENCE IMAGE ANALYSIS: {image_description}" if image_description else ""}

        CRITICAL: Generate prompts that maximize Veo 3's capabilities. Use these advanced techniques:

        1. CINEMATIC LANGUAGE: Use specific film terminology (dolly, crane shot, rack focus, etc.)
        2. DETAILED SCENE COMPOSITION: Specify foreground, midground, background elements
        3. LIGHTING SETUP: Describe key light, fill light, rim light, practical lights
        4. CAMERA MOVEMENT: Specify exact movements with timing (e.g., "slow dolly in from 0-3s")
        5. COLOR GRADING: Mention specific color palettes, contrast levels, mood
        6. PHYSICS & REALISM: Emphasize realistic physics, natural movements, proper weight
        7. TEMPORAL PRECISION: Break down actions by exact seconds (0-2s, 2-4s, etc.)

        Format as JSON with:
        - title: Compelling title (max 100 chars)
        - description: YouTube description with keywords and hashtags
        - script: Narration for 8 seconds
        - visual_prompts: ULTRA-DETAILED scene description including:
          * Opening shot (0-2s): What happens, who/what is visible
          * Main action (2-6s): Subject behavior, interactions, key moments
          * Closing shot (6-8s): Final frame, transition ready
          * Environment: Setting, textures, materials, atmosphere
          * Characters/subjects: Appearance, emotions, movements
          * Audio cues: Ambient sounds, foley, music genre
        - camera_work: Specific camera setup (e.g., "Slow dolly in, 85mm portrait lens, shallow DOF, eye-level, smooth steadicam movement from wide to medium close-up")
        - lighting: Detailed lighting setup (e.g., "Golden hour with rim lighting, motivated practicals, atmospheric haze, warm key light from window")
        - style_keywords: Array of 8-10 style descriptors for Veo 3 (e.g., "photorealistic", "cinematic", "8K", "shallow DOF", "film grain", "anamorphic")
        - hook: Attention-grabbing opening (first 2 seconds)

        IMPORTANT: Write prompts as if directing a real film crew. Be specific about EVERYTHING - camera angles, lighting setups, actor movements, timing, emotions, and environmental details. The more specific, the better Veo 3 performs."""
        
        # For Grok 3, we only send text (no images)
        data = {
            'model': 'grok-3',  # Using Grok 3 for script generation
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.7
        }
        
        response = requests.post(self.grok_api_url, headers=headers, json=data)
        
        # Log request details for debugging
        if response.status_code != 200:
            logger.error(f"API Request failed - Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            logger.error(f"Request URL: {self.grok_api_url}")
            logger.error(f"Request Headers: {headers}")
            # Log request data
            logger.error(f"Request Data: {json.dumps(data, indent=2)}")
            
            # Check for specific error messages
            try:
                error_data = response.json()
                if 'error' in error_data:
                    logger.error(f"API Error Message: {error_data['error']}")
            except:
                pass
        
        response.raise_for_status()
        
        content = response.json()['choices'][0]['message']['content']
        logger.info(f"Raw Grok response: {content[:500]}...")  # Log first 500 chars
        
        try:
            script_data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Grok: {e}")
            logger.error(f"Content: {content}")
            # Try to extract JSON from content if it's wrapped in markdown
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                script_data = json.loads(json_match.group(1))
            else:
                raise
        
        logger.info(f"Parsed script data keys: {list(script_data.keys())}")
        visual_prompts = script_data.get('visual_prompts', 'NOT FOUND')
        if visual_prompts != 'NOT FOUND' and isinstance(visual_prompts, str):
            logger.info(f"visual_prompts content: {visual_prompts[:200]}...")
        else:
            logger.info(f"visual_prompts content: {visual_prompts}")
        
        # Store original camera_work and lighting if they exist
        original_camera_work = script_data.get('camera_work')
        original_lighting = script_data.get('lighting')
        
        # Apply prompt optimization only if fields are missing
        if 'visual_prompts' in script_data:
            # Convert dict visual prompts to string if needed
            visual_prompts_text = script_data['visual_prompts']
            if isinstance(visual_prompts_text, dict):
                # Store original for reference
                script_data['_original_visual_prompts'] = visual_prompts_text.copy()
                
                # Convert structured dict to narrative string
                prompt_parts = []
                for key, value in visual_prompts_text.items():
                    if isinstance(value, dict):
                        # Handle nested dicts
                        for sub_key, sub_value in value.items():
                            prompt_parts.append(f"{sub_value}")
                    else:
                        prompt_parts.append(f"{value}")
                visual_prompts_text = " ".join(prompt_parts)
                script_data['visual_prompts'] = visual_prompts_text
            
            # Get optimized style data
            style_data = self.prompt_optimizer.generate_style_prompt(
                visual_prompts_text,
                style=style
            )
            
            # Enhance the visual prompts with optimization
            enhanced_prompt = self.prompt_optimizer.optimize_prompt(
                visual_prompts_text,
                style=style
            )
            
            script_data['visual_prompts'] = enhanced_prompt
            
            # Restore original camera_work and lighting if they existed
            if original_camera_work:
                script_data['camera_work'] = original_camera_work
            elif 'camera_work' not in script_data:
                script_data['camera_work'] = style_data['camera_work']
            
            if original_lighting:
                script_data['lighting'] = original_lighting
            elif 'lighting' not in script_data:
                script_data['lighting'] = style_data['lighting']
            
            if 'technical_specs' not in script_data:
                script_data['technical_specs'] = style_data['technical_specs']
            
            # Ensure we have style keywords
            if 'style_keywords' not in script_data:
                script_data['style_keywords'] = style_data['style_keywords']
        
        # Build the final prompt that will be sent to Veo 3
        final_prompt = script_data.get('visual_prompts', '')
        if 'style_keywords' in script_data and isinstance(script_data['style_keywords'], list):
            final_prompt = f"{final_prompt}. Style: {', '.join(script_data['style_keywords'])}"
        
        # Store the final prompt for preview
        script_data['final_veo3_prompt'] = final_prompt
        
        logger.info(f"Generated script data keys: {list(script_data.keys())}")
        vp_preview = script_data.get('visual_prompts', '')
        if vp_preview and isinstance(vp_preview, str):
            logger.info(f"Visual prompts preview: {vp_preview[:200]}...")
        else:
            logger.info(f"Visual prompts preview: {vp_preview}")
            
        fvp_preview = script_data.get('final_veo3_prompt', '')
        if fvp_preview and isinstance(fvp_preview, str):
            logger.info(f"Final veo3 prompt preview: {fvp_preview[:200]}...")
        else:
            logger.info(f"Final veo3 prompt preview: {fvp_preview}")
        
        # Ensure we always have at least one prompt field
        if not script_data.get('visual_prompts') and not script_data.get('final_veo3_prompt'):
            logger.warning("No visual prompts found in script data!")
            script_data['visual_prompts'] = f"Create a video about {topic}"
            script_data['final_veo3_prompt'] = script_data['visual_prompts']
        
        return script_data
    
    def generate_multi_segment_script(self, topic: str, num_segments: int, style: str = 'cinematic', image_paths: Optional[List[str]] = None) -> Dict:
        """Generate script for multiple connected video segments with image analysis"""
        logger.info(f"Generating {num_segments}-segment script for topic: {topic} in {style} style")
        if image_paths:
            logger.info(f"Analyzing {len(image_paths)} reference images")
        
        headers = {
            'Authorization': f'Bearer {self.grok_api_key}',
            'Content-Type': 'application/json'
        }
        
        # Style-specific instructions (same as single segment)
        style_instructions = {
            'cinematic': "Use dramatic camera movements, film-like color grading, shallow depth of field, and professional cinematography techniques.",
            'realistic': "Focus on natural lighting, realistic physics, authentic movements, and documentary-style camera work.",
            'dramatic': "Emphasize high contrast lighting, moody atmosphere, dynamic camera angles, and emotional intensity.",
            'vibrant': "Use bright colors, energetic camera movements, high-key lighting, and upbeat pacing.",
            'tech': "Apply futuristic aesthetics, digital effects, clean compositions, and modern visual language."
        }
        
        # Analyze images with Grok 2 Vision if provided
        image_description = ""
        if image_paths:
            image_description = self._analyze_images_with_grok2(image_paths)
            if image_description:
                logger.info(f"Image analysis complete: {image_description[:200]}...")
            else:
                logger.warning("Image analysis failed, continuing without image context")
        
        prompt = f"""Create a compelling {num_segments * 8}-second video script about: {topic}
        
        STYLE DIRECTIVE: {style.upper()} - {style_instructions.get(style, style_instructions['cinematic'])}
        
        {f"REFERENCE IMAGES PROVIDED: {image_description}" if image_description else ""}
        
        The video will be split into {num_segments} segments of 8 seconds each.
        Create a cohesive narrative that flows smoothly across all segments.
        
        Format the response as JSON with:
        - title: Clear, descriptive title (max 100 chars)
        - description: YouTube video description with relevant keywords and hashtags
        - camera_work: Overall camera style for the entire video
        - lighting: Overall lighting approach for consistency
        - style_keywords: Array of 8-10 style descriptors for Veo 3
        - segments: Array of {num_segments} segments, each containing:
          - segment_number: 1 to {num_segments}
          - script: Narration for this 8-second segment
          - visual_prompts: Detailed visual scene description
          - continuity_note: Brief note on how this connects to the next segment (except last)
        
        Important: 
        - Maintain visual and narrative continuity between segments
        - Each segment should be able to stand alone but flow naturally into the next
        - Include specific visual elements that carry through segments (characters, objects, settings)
        - End each segment with a natural transition point
        - Keep camera_work and lighting consistent across all segments
        """
        
        # For Grok 3, we only send text (no images)
        data = {
            'model': 'grok-3',  # Using Grok 3 for script generation
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.7
        }
        
        response = requests.post(self.grok_api_url, headers=headers, json=data)
        
        # Log request details for debugging
        if response.status_code != 200:
            logger.error(f"API Request failed - Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
        
        response.raise_for_status()
        
        content = response.json()['choices'][0]['message']['content']
        logger.info(f"Raw Grok multi-segment response: {content[:500]}...")  # Log first 500 chars
        
        try:
            script_data = json.loads(content)
            logger.info(f"Multi-segment parsed keys: {list(script_data.keys())}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Grok: {e}")
            logger.error(f"Content: {content}")
            # Try to extract JSON from content if it's wrapped in markdown
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                script_data = json.loads(json_match.group(1))
            else:
                raise
        
        # For multi-segment, we need to combine all visual prompts
        if 'segments' in script_data:
            all_prompts = []
            for segment in script_data['segments']:
                if 'visual_prompts' in segment:
                    all_prompts.append(segment['visual_prompts'])
            
            # Combine into a single visual prompt for the preview
            script_data['visual_prompts'] = ' '.join(all_prompts)
            
            # Apply style-specific optimization
            style_data = self.prompt_optimizer.generate_style_prompt(
                script_data.get('visual_prompts', topic),
                style=style
            )
            
            # Build final prompt
            final_prompt = script_data.get('visual_prompts', '')
            if 'style_keywords' in script_data and isinstance(script_data['style_keywords'], list):
                final_prompt = f"{final_prompt}. Style: {', '.join(script_data['style_keywords'])}"
            
            script_data['final_veo3_prompt'] = final_prompt
        
        logger.info(f"Multi-segment script data keys: {list(script_data.keys())}")
        
        # For multi-segment, create a combined visual_prompts for preview
        if 'segments' in script_data and script_data['segments']:
            combined_prompts = []
            for i, segment in enumerate(script_data['segments']):
                if 'visual_prompts' in segment:
                    combined_prompts.append(f"SEGMENT {i+1} (8 seconds):\n{segment['visual_prompts']}")
            
            # Store combined prompts for preview
            script_data['visual_prompts'] = "\n\n".join(combined_prompts) if combined_prompts else f"Create a {num_segments * 8}-second video about {topic}"
            
            # Build final prompt with style keywords
            final_prompt = script_data['visual_prompts']
            if 'style_keywords' in script_data and isinstance(script_data['style_keywords'], list):
                final_prompt = f"{final_prompt}\n\nStyle: {', '.join(script_data['style_keywords'])}"
            script_data['final_veo3_prompt'] = final_prompt
            
            logger.info(f"Combined {len(combined_prompts)} segment prompts for preview")
        
        return script_data
        
    def generate_video(self, script_data: Dict, image_paths: Optional[List[str]] = None) -> str:
        """Generate video using Google Veo 3 via FAL API with support for multiple reference images"""
        logger.info("Generating video with Veo 3")
        
        # FAL client will use FAL_KEY from environment
        
        # Combine visual prompts into video generation prompt
        if isinstance(script_data.get('visual_prompts'), list):
            video_prompt = f"{script_data['title']}. " + " ".join(script_data['visual_prompts'])
        else:
            # New detailed format
            video_prompt = script_data.get('visual_prompts', '')
        
        # Add style keywords if available
        if 'style_keywords' in script_data:
            video_prompt = f"{video_prompt}. Style: {', '.join(script_data['style_keywords'])}"
        
        # Generate video using Google Veo 3
        def on_queue_update(update):
            if isinstance(update, fal_client.InProgress):
                for log in update.logs:
                    logger.info(f"Veo3 Progress: {log['message']}")
        
        # Build arguments
        arguments = {
            "prompt": video_prompt,
            "aspect_ratio": "16:9",  # Horizontal standard YouTube
            "duration": "8s"  # Veo 3 currently only supports 8 seconds
        }
        
        # Handle multiple reference images
        if image_paths:
            import base64
            
            if isinstance(image_paths, str):
                # Single image path (backward compatibility)
                image_paths = [image_paths]
            
            if len(image_paths) == 1:
                # Single image - use as before
                with open(image_paths[0], 'rb') as img_file:
                    image_data = base64.b64encode(img_file.read()).decode('utf-8')
                    arguments["image_url"] = f"data:image/jpeg;base64,{image_data}"
                    logger.info(f"Using single image guidance from: {image_paths[0]}")
            else:
                # Multiple images - create array of image URLs
                image_urls = []
                for i, img_path in enumerate(image_paths):
                    with open(img_path, 'rb') as img_file:
                        image_data = base64.b64encode(img_file.read()).decode('utf-8')
                        image_urls.append(f"data:image/jpeg;base64,{image_data}")
                    logger.info(f"Added reference image {i+1}: {img_path}")
                
                # Try sending as array (Veo 3 might support this)
                arguments["image_urls"] = image_urls
                
                # Also add specific frame references if we have 2 images
                if len(image_paths) == 2:
                    arguments["first_frame_image"] = image_urls[0]
                    arguments["last_frame_image"] = image_urls[1]
                    logger.info("Using first and last frame specification")
        
        # Standard horizontal video format
        
        result = fal_client.subscribe(
            "fal-ai/veo3",
            arguments=arguments,
            with_logs=True,
            on_queue_update=on_queue_update
        )
        
        # Log the result to see structure
        logger.info(f"Veo3 result: {result}")
        
        # Download video - check for different possible keys
        video_url = result.get('video', {}).get('url') or result.get('url') or result.get('video_url')
        
        if not video_url:
            logger.error(f"No video URL found in Veo3 result. Result structure: {result}")
            raise ValueError("Failed to generate video: No video URL returned from Veo3 API")
        
        video_path = f"output/video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        response = requests.get(video_url)
        with open(video_path, 'wb') as f:
            f.write(response.content)
            
        logger.info(f"Video saved to: {video_path}")
        return video_path
    
    def generate_multi_segment_video(self, script_data: Dict, image_paths: Optional[List[str]], job_status: Dict) -> str:
        """Generate multiple video segments and concatenate them"""
        segments = script_data.get('segments', [script_data])  # Fallback for single segment
        segment_paths = []
        
        os.makedirs('temp_segments', exist_ok=True)
        
        for i, segment in enumerate(segments):
            segment_num = i + 1
            job_status['progress'] = f'Creating segment {segment_num}/{len(segments)}...'
            logger.info(f"Generating segment {segment_num}/{len(segments)}")
            
            # Prepare segment data in the format expected by generate_video
            segment_data = {
                'title': f"{script_data['title']} - Part {segment_num}",
                'visual_prompts': [segment['visual_prompts']]
            }
            
            # Add continuity instructions to maintain consistency
            if i > 0 and 'continuity_note' in segments[i-1]:
                segment_data['visual_prompts'][0] = f"Continuing from previous scene: {segments[i-1]['continuity_note']}. {segment_data['visual_prompts'][0]}"
            
            # Generate this segment (use same images for all segments to maintain style)
            segment_path = self.generate_video(segment_data, image_paths)
            
            # Move to temp directory with proper naming
            temp_segment_path = f"temp_segments/segment_{segment_num:03d}.mp4"
            os.rename(segment_path, temp_segment_path)
            segment_paths.append(temp_segment_path)
        
        # If only one segment, just return it
        if len(segment_paths) == 1:
            final_path = f"output/video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            os.rename(segment_paths[0], final_path)
            return final_path
        
        # Concatenate segments using ffmpeg
        job_status['progress'] = 'Combining segments into final video...'
        return self.concatenate_videos(segment_paths)
    
    def concatenate_videos(self, video_paths: List[str]) -> str:
        """Concatenate multiple video files using ffmpeg"""
        logger.info(f"Concatenating {len(video_paths)} video segments")
        
        # Create a temporary file listing all videos
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for path in video_paths:
                f.write(f"file '{os.path.abspath(path)}'\n")
            concat_file = f.name
        
        # Output path
        output_path = f"output/video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        # FFmpeg command to concatenate
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            '-y',  # Overwrite output
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Videos concatenated successfully: {output_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            raise Exception(f"Failed to concatenate videos: {e.stderr}")
        finally:
            # Cleanup
            os.unlink(concat_file)
            for path in video_paths:
                if os.path.exists(path):
                    os.unlink(path)
        
        return output_path
        
    def upload_to_youtube(self, video_path: str, script_data: Dict) -> str:
        """Upload video to YouTube"""
        logger.info("Uploading to YouTube")
        
        body = {
            'snippet': {
                'title': script_data['title'][:100],  # YouTube title limit
                'description': script_data['description'],
                'categoryId': '28',  # Science & Technology
                'tags': ['AI', 'Claude Code', 'programming', 'coding', 'tutorial', 'tech']
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
        # Update topic status
        self.topics_sheet.update_cell(topic_data['row'], 2, 'Published')  # Assuming Status is column B
        
        # Add to published videos
        self.videos_sheet.append_row([
            topic_data['id'],
            topic_data['topic'],
            script_data['title'],
            video_url,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            0  # Initial view count
        ])
        
    def process_video(self):
        """Main workflow: Topic → Script → Video → Upload"""
        try:
            # Get next topic
            topic_data = self.get_next_topic()
            if not topic_data:
                logger.info("No pending topics found")
                return
                
            logger.info(f"Processing topic: {topic_data['topic']}")
            
            # Update status to Processing
            self.topics_sheet.update_cell(topic_data['row'], 2, 'Processing')
            
            # Generate script
            script_data = self.generate_script(topic_data['topic'])
            
            # Generate video
            video_path = self.generate_video(script_data)
            
            # Upload to YouTube
            video_url = self.upload_to_youtube(video_path, script_data)
            
            # Update sheets
            self.update_sheets(topic_data, video_url, script_data)
            
            logger.success(f"Video published successfully: {video_url}")
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            # Update status back to Pending on error
            if 'topic_data' in locals():
                self.topics_sheet.update_cell(topic_data['row'], 2, 'Error')
            raise

def main():
    """Run video automation"""
    automation = VideoAutomation()
    automation.process_video()

if __name__ == "__main__":
    main()