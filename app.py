#!/usr/bin/env python3
"""
Video Automation Web UI
User-friendly interface for AI video generation
"""

from flask import Flask, render_template, request, jsonify, send_file, session, redirect
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import json
from datetime import datetime, timedelta
import threading
from video_automation import VideoAutomation
from loguru import logger
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import requests
import secrets
from auth import setup_auth_routes, login_required, USE_AUTH

load_dotenv()

# No need for credential setup - users provide their own via UI

# Import configuration
from config import get_config

app = Flask(__name__)
# Load configuration based on environment
app.config.from_object(get_config())

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Store job status
job_status = {}

# Track server start time
app.start_time = datetime.now().isoformat()

# Setup authentication routes
setup_auth_routes(app)

def run_video_generation(job_id, topic, api_keys_from_session, image_paths=None, duration=8):
    """Run video generation in background thread"""
    try:
        job_status[job_id] = {
            'status': 'processing',
            'progress': 'Initializing...',
            'video_url': None,
            'error': None
        }
        
        # Create automation instance with custom API keys, skip external setup
        automation = VideoAutomation(skip_external_setup=True)
        # Ensure API key has proper prefix
        grok_key = api_keys_from_session['grokApiKey']
        if not grok_key.startswith('xai-'):
            grok_key = f"xai-{grok_key}"
        automation.grok_api_key = grok_key
        os.environ['FAL_KEY'] = api_keys_from_session['falApiKey']
        
        # Handle YouTube credentials if provided
        if api_keys_from_session.get('useYoutube') and api_keys_from_session.get('youtubeClientSecrets'):
            try:
                # Save YouTube credentials temporarily
                os.makedirs('config', exist_ok=True)
                with open('config/youtube_client_secrets.json', 'w') as f:
                    f.write(api_keys_from_session['youtubeClientSecrets'])
                # Re-setup YouTube with new credentials
                automation.setup_youtube()
            except Exception as e:
                logger.error(f"Failed to setup YouTube: {str(e)}")
                automation.youtube = None
        
        # Calculate number of segments needed
        num_segments = duration // 8
        
        # Override to use provided topic instead of Google Sheets
        if num_segments == 1:
            # Single segment - use original method  
            job_status[job_id]['progress'] = 'Generating script with Grok...'
            # Note: The original run_video_generation doesn't have style parameter
            # We should get it from the automation instance or use default
            script_data = automation.generate_script(topic, style='cinematic', image_paths=image_paths)
            
            job_status[job_id]['progress'] = 'Creating video with Veo 3...'
            video_path = automation.generate_video(script_data, image_paths)
        else:
            # Multiple segments
            job_status[job_id]['progress'] = f'Generating script for {num_segments} segments with Grok...'
            script_data = automation.generate_multi_segment_script(topic, num_segments, style='cinematic', image_paths=image_paths)
            
            job_status[job_id]['progress'] = f'Creating {num_segments} video segments with Veo 3...'
            video_path = automation.generate_multi_segment_video(script_data, image_paths, job_status[job_id])
        
        if api_keys.get('useYoutube') and automation.youtube:
            job_status[job_id]['progress'] = 'Uploading to YouTube...'
            video_url = automation.upload_to_youtube(video_path, script_data)
        else:
            job_status[job_id]['progress'] = 'Saving video locally...'
            video_url = None
        
        job_status[job_id] = {
            'status': 'completed',
            'progress': 'Video created successfully!',
            'video_url': video_url,
            'video_title': script_data['title'],
            'video_path': video_path,
            'error': None
        }
        
        # Save to recent videos in memory
        if not hasattr(app, 'recent_videos'):
            app.recent_videos = []
        app.recent_videos.insert(0, {
            'title': script_data['title'],
            'topic': topic,
            'video_url': video_url,
            'created_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in job {job_id}: {str(e)}")
        job_status[job_id] = {
            'status': 'error',
            'progress': 'Failed to create video',
            'video_url': None,
            'error': str(e)
        }

@app.before_request
def force_https():
    """Force HTTPS in production"""
    if os.environ.get('FLASK_ENV') == 'production':
        if request.headers.get('X-Forwarded-Proto', 'http') != 'https':
            return redirect(request.url.replace('http://', 'https://'), code=301)

@app.after_request
def set_security_headers(response):
    """Set security headers on all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response

@app.route('/')
def index():
    """Main page"""
    # Simple visitor counter
    visit_count = session.get('visit_counted', False)
    if not visit_count:
        session['visit_counted'] = True
        # Increment counter (stored in app context for simplicity)
        if not hasattr(app, 'visitor_count'):
            app.visitor_count = 0
        app.visitor_count += 1
    
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint for Railway"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/csrf-token')
def get_csrf_token():
    """Get CSRF token for API requests"""
    token = generate_csrf()
    return jsonify({'csrf_token': token})

@app.route('/api/session/keys', methods=['POST'])
def store_api_keys():
    """Store API keys in server-side session"""
    data = request.json
    
    # Store API keys in session (encrypted server-side)
    session['api_keys'] = {
        'grokApiKey': data.get('grokApiKey', ''),
        'falApiKey': data.get('falApiKey', ''),
        'useYoutube': data.get('useYoutube', False),
        'youtubeClientSecrets': data.get('youtubeClientSecrets', '')
    }
    session.permanent = True
    
    return jsonify({'success': True, 'message': 'API keys stored securely'})

@app.route('/api/session/keys', methods=['GET'])
def get_api_keys_status():
    """Check if API keys are stored in session"""
    api_keys = session.get('api_keys', {})
    
    return jsonify({
        'success': True,
        'hasKeys': {
            'grok': bool(api_keys.get('grokApiKey')),
            'fal': bool(api_keys.get('falApiKey')),
            'youtube': bool(api_keys.get('youtubeClientSecrets'))
        }
    })

@app.route('/api/session/clear', methods=['POST'])
def clear_session():
    """Clear session data"""
    session.clear()
    return jsonify({'success': True, 'message': 'Session cleared'})

@app.route('/api/topics', methods=['GET'])
def get_topics():
    """Get topics from Google Sheets"""
    try:
        automation = VideoAutomation(skip_external_setup=False)  # Keep Sheets setup for this endpoint
        all_records = automation.topics_sheet.get_all_records()
        topics = [
            {
                'id': record.get('ID'),
                'topic': record.get('Topic'),
                'status': record.get('Status', 'Pending')
            }
            for record in all_records if record.get('Topic')
        ]
        return jsonify({'success': True, 'topics': topics})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/generate-script', methods=['POST'])
def generate_script():
    """Generate script only (for preview)"""
    # Handle both JSON and form data
    if request.content_type and 'multipart/form-data' in request.content_type:
        topic = request.form.get('topic')
        duration = int(request.form.get('duration', 8))
        video_style = request.form.get('videoStyle', 'cinematic')
        grok_api_key = request.form.get('grokApiKey')
        
        # Handle image uploads for Grok analysis
        image_paths = []
        if 'images' in request.files:
            images = request.files.getlist('images')
            os.makedirs('temp_images', exist_ok=True)
            
            for i, image in enumerate(images):
                if image and image.filename:
                    # Security: Validate file type
                    if not allowed_file(image.filename):
                        return jsonify({'success': False, 'error': f'Invalid file type: {image.filename}. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'})
                    
                    filename = secure_filename(image.filename)
                    image_path = os.path.join('temp_images', f"grok_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}_{filename}")
                    image.save(image_path)
                    image_paths.append(image_path)
    else:
        # JSON data (backward compatibility)
        data = request.json
        topic = data.get('topic')
        duration = data.get('duration', 8)
        video_style = data.get('videoStyle', 'cinematic')
        grok_api_key = data.get('grokApiKey')
        image_paths = []
    
    if not topic or not grok_api_key:
        return jsonify({'success': False, 'error': 'Topic and API key required'})
    
    try:
        # Create temporary automation instance, skip external setup
        automation = VideoAutomation(skip_external_setup=True)
        # Ensure API key has proper prefix
        if not grok_api_key.startswith('xai-'):
            grok_api_key = f"xai-{grok_api_key}"
        automation.grok_api_key = grok_api_key
        
        # Generate script based on duration and style, with image analysis
        num_segments = duration // 8
        if num_segments == 1:
            script_data = automation.generate_script(topic, style=video_style, image_paths=image_paths)
        else:
            script_data = automation.generate_multi_segment_script(topic, num_segments, style=video_style, image_paths=image_paths)
        
        # Apply style-specific optimization only for missing fields
        if hasattr(automation, 'prompt_optimizer') and 'visual_prompts' in script_data:
            # Only update style_keywords if not already present
            if 'style_keywords' not in script_data:
                style_data = automation.prompt_optimizer.generate_style_prompt(
                    script_data.get('visual_prompts', topic),
                    style=video_style
                )
                script_data['style_keywords'] = style_data['style_keywords']
        
        # Log what we're returning for debugging
        logger.info(f"Returning script_data keys: {list(script_data.keys())}")
        logger.info(f"visual_prompts exists: {'visual_prompts' in script_data}")
        logger.info(f"final_veo3_prompt exists: {'final_veo3_prompt' in script_data}")
        logger.info(f"camera_work exists: {'camera_work' in script_data}")
        logger.info(f"camera_work value: {script_data.get('camera_work', 'NOT FOUND')}")
        logger.info(f"lighting exists: {'lighting' in script_data}")
        logger.info(f"lighting value: {script_data.get('lighting', 'NOT FOUND')}")
        if 'visual_prompts' in script_data and isinstance(script_data['visual_prompts'], str):
            logger.info(f"visual_prompts preview: {script_data['visual_prompts'][:100]}...")
        
        return jsonify({'success': True, 'script_data': script_data})
        
    except Exception as e:
        logger.error(f"Error generating script: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/generate-video', methods=['POST'])
def generate_video_from_script():
    """Generate video from pre-generated script"""
    # Handle form data
    topic = request.form.get('topic')
    script_data = json.loads(request.form.get('scriptData'))
    api_keys = {
        'grokApiKey': request.form.get('grokApiKey'),
        'falApiKey': request.form.get('falApiKey'),
        'useYoutube': request.form.get('useYoutube') == 'true',
        'youtubeClientSecrets': request.form.get('youtubeClientSecrets')
    }
    duration = int(request.form.get('duration', 8))
    
    # Handle multiple image uploads
    image_paths = []
    if 'images' in request.files:
        images = request.files.getlist('images')
        os.makedirs('temp_images', exist_ok=True)
        
        for i, image in enumerate(images):
            if image and image.filename:
                # Security: Validate file type
                if not allowed_file(image.filename):
                    return jsonify({'success': False, 'error': f'Invalid file type: {image.filename}. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'})
                
                filename = secure_filename(image.filename)
                image_path = os.path.join('temp_images', f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}_{filename}")
                image.save(image_path)
                image_paths.append(image_path)
    
    if not api_keys['grokApiKey'] or not api_keys['falApiKey']:
        return jsonify({'success': False, 'error': 'API keys are required'})
    
    # Create job ID
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Start background thread with script data
    thread = threading.Thread(
        target=run_video_generation_with_script, 
        args=(job_id, topic, api_keys, script_data, image_paths, duration)
    )
    thread.start()
    
    return jsonify({'success': True, 'job_id': job_id})

def run_video_generation_with_script(job_id, topic, api_keys, script_data, image_paths=None, duration=8):
    """Run video generation with pre-generated script"""
    try:
        job_status[job_id] = {
            'status': 'processing',
            'progress': 'Initializing...',
            'video_url': None,
            'error': None
        }
        
        # Create automation instance with custom API keys, skip external setup
        automation = VideoAutomation(skip_external_setup=True)
        # Ensure API key has proper prefix
        grok_key = api_keys['grokApiKey']
        if not grok_key.startswith('xai-'):
            grok_key = f"xai-{grok_key}"
        automation.grok_api_key = grok_key
        os.environ['FAL_KEY'] = api_keys['falApiKey']
        
        # Handle YouTube credentials if provided
        if api_keys.get('useYoutube') and api_keys.get('youtubeClientSecrets'):
            try:
                os.makedirs('config', exist_ok=True)
                with open('config/youtube_client_secrets.json', 'w') as f:
                    f.write(api_keys['youtubeClientSecrets'])
                automation.setup_youtube()
            except Exception as e:
                logger.error(f"Failed to setup YouTube: {str(e)}")
                automation.youtube = None
        
        # Generate video with provided script
        num_segments = duration // 8
        if num_segments == 1:
            job_status[job_id]['progress'] = 'Creating video with Veo 3...'
            video_path = automation.generate_video(script_data, image_paths)
        else:
            job_status[job_id]['progress'] = f'Creating {num_segments} video segments with Veo 3...'
            video_path = automation.generate_multi_segment_video(script_data, image_paths, job_status[job_id])
        
        if api_keys.get('useYoutube') and automation.youtube:
            job_status[job_id]['progress'] = 'Uploading to YouTube...'
            video_url = automation.upload_to_youtube(video_path, script_data)
        else:
            job_status[job_id]['progress'] = 'Saving video locally...'
            video_url = None
        
        job_status[job_id] = {
            'status': 'completed',
            'progress': 'Video created successfully!',
            'video_url': video_url,
            'video_title': script_data['title'],
            'video_path': video_path,
            'error': None
        }
        
        # Save to recent videos
        if not hasattr(app, 'recent_videos'):
            app.recent_videos = []
        app.recent_videos.insert(0, {
            'title': script_data['title'],
            'topic': topic,
            'video_url': video_url,
            'created_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in job {job_id}: {str(e)}")
        job_status[job_id] = {
            'status': 'error',
            'progress': 'Failed to create video',
            'video_url': None,
            'error': str(e)
        }

@app.route('/api/generate', methods=['POST'])
@limiter.limit("5 per minute")
@login_required if USE_AUTH else lambda f: f
def generate_video():
    """Start video generation"""
    # Get API keys from session
    api_keys = session.get('api_keys', {})
    if not api_keys.get('grokApiKey') or not api_keys.get('falApiKey'):
        return jsonify({'success': False, 'error': 'API keys not configured. Please complete setup first.'})
    
    # Handle both JSON and form data
    if request.content_type and 'multipart/form-data' in request.content_type:
        # Form data with potential file upload
        topic = request.form.get('topic')
        
        # Handle image upload
        image_path = None
        if 'image' in request.files:
            image = request.files['image']
            if image and image.filename:
                # Save uploaded image
                os.makedirs('temp_images', exist_ok=True)
                filename = secure_filename(image.filename)
                image_path = os.path.join('temp_images', f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}")
                image.save(image_path)
        
        # Get duration
        duration = int(request.form.get('duration', 8))
    else:
        # JSON data (backward compatibility)
        data = request.json
        topic = data.get('topic')
        image_path = None
        duration = data.get('duration', 8)
    
    if not topic:
        return jsonify({'success': False, 'error': 'Topic is required'})
    
    # Create job ID
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Start background thread
    # Convert single image_path to list format expected by run_video_generation
    image_paths = [image_path] if image_path else None
    thread = threading.Thread(target=run_video_generation, args=(job_id, topic, api_keys, image_paths, duration))
    thread.start()
    
    return jsonify({'success': True, 'job_id': job_id})

@app.route('/api/status/<job_id>')
def get_status(job_id):
    """Get job status"""
    if job_id not in job_status:
        return jsonify({'success': False, 'error': 'Job not found'})
    
    return jsonify({'success': True, 'job': job_status[job_id]})

@app.route('/api/recent-videos')
def get_recent_videos():
    """Get recently created videos"""
    try:
        # Return videos from memory (doesn't require Google Sheets)
        videos = getattr(app, 'recent_videos', [])
        return jsonify({'success': True, 'videos': videos[:10]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/add-topic', methods=['POST'])
def add_topic():
    """Add topic to Google Sheets"""
    data = request.json
    topic = data.get('topic')
    
    if not topic:
        return jsonify({'success': False, 'error': 'Topic is required'})
    
    try:
        automation = VideoAutomation(skip_external_setup=False)  # Keep Sheets setup for adding topics
        # Find next ID
        records = automation.topics_sheet.get_all_records()
        next_id = f"{len(records) + 1:03d}"
        
        # Add new row
        automation.topics_sheet.append_row([next_id, '', topic])
        
        return jsonify({'success': True, 'message': 'Topic added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/test-script', methods=['GET'])
def test_script():
    """Test endpoint to verify script generation"""
    try:
        # Return a test script data
        test_data = {
            'title': 'Test Video Title',
            'visual_prompts': 'This is a test visual prompt that should appear in the textarea. It includes detailed scene descriptions.',
            'final_veo3_prompt': 'This is the final optimized prompt for Veo 3 with style keywords.',
            'camera_work': 'Dolly in shot with 85mm lens',
            'lighting': 'Golden hour lighting',
            'style_keywords': ['cinematic', '8K', 'photorealistic']
        }
        return jsonify({'success': True, 'script_data': test_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/random-idea', methods=['POST'])
def get_random_idea():
    """Get a random video idea from Grok"""
    data = request.json
    grok_api_key = data.get('grokApiKey')
    
    if not grok_api_key:
        return jsonify({'success': False, 'error': 'API key required'})
    
    try:
        headers = {
            'Authorization': f'Bearer {grok_api_key}',
            'Content-Type': 'application/json'
        }
        
        import random
        
        # Add randomness to the prompt
        categories = [
            "science and nature", "technology and future", "history and culture", 
            "everyday life mysteries", "space and astronomy", "ocean and marine life",
            "human body and health", "art and creativity", "food and cooking science",
            "weather and climate", "animals and wildlife", "transportation and travel",
            "sports and physics", "music and sound", "architecture and engineering"
        ]
        
        styles = [
            "mind-blowing", "surprising", "fascinating", "unexpected", "amazing",
            "little-known", "incredible", "mesmerizing", "astonishing", "remarkable"
        ]
        
        random_category = random.choice(categories)
        random_style = random.choice(styles)
        random_number = random.randint(1, 1000)
        
        prompt = f"""Generate a {random_style} video topic idea about {random_category}. 
        Make it different from typical ideas.
        The idea should be:
        - Interesting and educational
        - Suitable for a short video (8-32 seconds)
        - Specific enough to visualize
        - Appealing to a general audience
        
        Random seed: {random_number}
        
        Return ONLY the topic idea itself, no explanation or additional text.
        Be creative and unique! Don't use quotes."""
        
        data = {
            'model': 'grok-3',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 1.0,  # Maximum temperature for creativity
            'max_tokens': 100,
            'top_p': 0.95
        }
        
        response = requests.post(
            'https://api.x.ai/v1/chat/completions',
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            logger.error(f"Grok API error: {response.status_code} - {response.text}")
            return jsonify({'success': False, 'error': 'Failed to generate idea'})
        
        idea = response.json()['choices'][0]['message']['content'].strip()
        
        # Remove any surrounding quotes
        if idea.startswith('"') and idea.endswith('"'):
            idea = idea[1:-1]
        elif idea.startswith("'") and idea.endswith("'"):
            idea = idea[1:-1]
        
        return jsonify({'success': True, 'idea': idea})
        
    except Exception as e:
        logger.error(f"Error getting random idea: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/admin/visitors')
def admin_visitors():
    """Simple visitor count endpoint"""
    return jsonify({
        'unique_visitors': getattr(app, 'visitor_count', 0),
        'server_start': getattr(app, 'start_time', 'Unknown')
    })

@app.route('/api/stats')
def get_stats():
    """Get video statistics"""
    try:
        videos = getattr(app, 'recent_videos', [])
        today_count = 0
        today = datetime.now().date()
        
        for video in videos:
            video_date = datetime.fromisoformat(video['created_at']).date()
            if video_date == today:
                today_count += 1
        
        return jsonify({
            'success': True,
            'total': len(videos),
            'today': today_count,
            'views': 0,  # Would need YouTube API to get real views
            'visitors': getattr(app, 'visitor_count', 0)  # Total unique visitors
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/schedule-video', methods=['POST'])
def schedule_video():
    """Schedule a video for future creation"""
    data = request.json
    
    topic = data.get('topic')
    scheduled_time = data.get('scheduledTime')
    duration = data.get('duration', 8)
    style = data.get('style', 'cinematic')
    script_data = data.get('scriptData', {})
    
    if not topic or not scheduled_time:
        return jsonify({'success': False, 'error': 'Topic and scheduled time are required'})
    
    try:
        automation = VideoAutomation(skip_external_setup=False)  # Keep Sheets setup for scheduling
        
        # Check if we have a "Scheduled" worksheet, if not create it
        try:
            scheduled_sheet = automation.spreadsheet.worksheet('Scheduled')
        except:
            # Create the Scheduled worksheet with extra column for script data
            scheduled_sheet = automation.spreadsheet.add_worksheet(title='Scheduled', rows=100, cols=10)
            # Add headers
            headers = ['ID', 'Topic', 'Scheduled Time', 'Duration', 'Style', 'Status', 'Created At', 'Video ID', 'Script Data']
            scheduled_sheet.append_row(headers)
        
        # Generate unique ID
        existing_records = scheduled_sheet.get_all_records()
        next_id = f"SCH{len(existing_records) + 1:04d}"
        
        # Add scheduled video with script data
        scheduled_sheet.append_row([
            next_id,
            topic,
            scheduled_time,
            duration,
            style,
            'Pending',
            datetime.now().isoformat(),
            '',  # Video ID will be filled when created
            json.dumps(script_data) if script_data else ''  # Store script data as JSON
        ])
        
        return jsonify({'success': True, 'id': next_id})
    except Exception as e:
        logger.error(f"Error scheduling video: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/scheduled-videos')
def get_scheduled_videos():
    """Get all scheduled videos"""
    try:
        automation = VideoAutomation(skip_external_setup=False)  # Keep Sheets setup for getting scheduled videos
        
        try:
            scheduled_sheet = automation.spreadsheet.worksheet('Scheduled')
            records = scheduled_sheet.get_all_records()
            
            # Format records for frontend
            videos = []
            for record in records:
                if record.get('Topic'):  # Skip empty rows
                    videos.append({
                        'id': record.get('ID'),
                        'topic': record.get('Topic'),
                        'scheduledTime': record.get('Scheduled Time'),
                        'duration': record.get('Duration', 8),
                        'style': record.get('Style', 'cinematic'),
                        'status': record.get('Status', 'Pending'),
                        'videoId': record.get('Video ID', '')
                    })
            
            # Sort by scheduled time
            videos.sort(key=lambda x: x['scheduledTime'])
            
            return jsonify({'success': True, 'videos': videos})
        except:
            # No scheduled sheet yet
            return jsonify({'success': True, 'videos': []})
            
    except Exception as e:
        logger.error(f"Error getting scheduled videos: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/cancel-scheduled/<video_id>', methods=['DELETE'])
def cancel_scheduled_video(video_id):
    """Cancel a scheduled video"""
    try:
        automation = VideoAutomation(skip_external_setup=False)  # Keep Sheets setup for canceling scheduled videos
        scheduled_sheet = automation.spreadsheet.worksheet('Scheduled')
        
        # Find the row with this ID
        all_values = scheduled_sheet.get_all_values()
        for idx, row in enumerate(all_values[1:], start=2):  # Skip header
            if row[0] == video_id:
                # Update status to Cancelled
                scheduled_sheet.update_cell(idx, 6, 'Cancelled')
                return jsonify({'success': True})
        
        return jsonify({'success': False, 'error': 'Video not found'})
    except Exception as e:
        logger.error(f"Error cancelling video: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/clear-cancelled-videos', methods=['DELETE'])
def clear_cancelled_videos():
    """Remove all cancelled videos from the schedule"""
    try:
        automation = VideoAutomation(skip_external_setup=False)  # Keep Sheets setup for clearing cancelled videos
        scheduled_sheet = automation.spreadsheet.worksheet('Scheduled')
        
        # Get all values
        all_values = scheduled_sheet.get_all_values()
        headers = all_values[0]
        
        # Filter out cancelled videos
        filtered_rows = [headers]  # Keep headers
        cleared_count = 0
        
        for row in all_values[1:]:  # Skip header
            if row[5] != 'Cancelled':  # Status column is index 5
                filtered_rows.append(row)
            else:
                cleared_count += 1
        
        # Clear the sheet and rewrite without cancelled videos
        scheduled_sheet.clear()
        if filtered_rows:
            scheduled_sheet.update(filtered_rows)
        
        return jsonify({'success': True, 'cleared': cleared_count})
    except Exception as e:
        logger.error(f"Error clearing cancelled videos: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Use debug mode only in development
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    # Railway provides PORT as environment variable
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)