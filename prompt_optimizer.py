#!/usr/bin/env python3
"""
Advanced Prompt Optimization System for Video Generation
Enhances prompts using cinematography best practices and AI understanding
"""

from typing import Dict, List, Optional
import re

class PromptOptimizer:
    """Optimizes prompts for maximum video generation quality"""
    
    def __init__(self):
        self.cinematography_terms = {
            'camera_movements': [
                'dolly in', 'dolly out', 'truck left', 'truck right',
                'crane up', 'crane down', 'pan left', 'pan right',
                'tilt up', 'tilt down', 'rack focus', 'pull focus',
                'handheld', 'steadicam', 'orbit', 'aerial'
            ],
            'shot_types': [
                'extreme close-up (ECU)', 'close-up (CU)', 'medium close-up (MCU)',
                'medium shot (MS)', 'medium wide shot (MWS)', 'wide shot (WS)',
                'extreme wide shot (EWS)', 'establishing shot', 'over-the-shoulder (OTS)',
                'point-of-view (POV)', 'dutch angle', 'bird\'s eye view', 'worm\'s eye view'
            ],
            'lighting_setups': [
                'three-point lighting', 'Rembrandt lighting', 'split lighting',
                'butterfly lighting', 'rim lighting', 'silhouette', 'golden hour',
                'blue hour', 'high key', 'low key', 'chiaroscuro', 'motivated lighting'
            ],
            'lens_types': [
                '14mm ultra-wide', '24mm wide-angle', '35mm standard wide',
                '50mm normal', '85mm portrait', '135mm telephoto', '200mm telephoto',
                'macro lens', 'tilt-shift', 'anamorphic 2.39:1'
            ]
        }
        
        self.style_enhancers = {
            'cinematic': [
                'cinematic color grading', 'film grain', 'letterbox aspect ratio',
                '24fps motion blur', 'shallow depth of field', 'bokeh', 
                'color theory', 'complementary colors', 'film emulation'
            ],
            'realistic': [
                'photorealistic', 'ray-traced lighting', 'subsurface scattering',
                'accurate physics', 'natural skin tones', 'realistic materials',
                'volumetric fog', 'atmospheric perspective', '8K detail'
            ],
            'dramatic': [
                'dramatic lighting', 'strong shadows', 'high contrast',
                'moody atmosphere', 'selective focus', 'lens flares',
                'dynamic composition', 'rule of thirds', 'leading lines'
            ]
        }
        
        self.temporal_markers = {
            'intro': ['0-2 seconds', 'opening frame', 'first moment'],
            'development': ['2-4 seconds', '4-6 seconds', 'mid-sequence'],
            'climax': ['6-7 seconds', 'peak moment', 'key action'],
            'outro': ['7-8 seconds', 'final frame', 'closing shot']
        }
    
    def optimize_prompt(self, base_prompt: str, style: str = 'cinematic') -> str:
        """Optimize a prompt with cinematography best practices"""
        
        # Extract key subjects and actions
        subjects = self._extract_subjects(base_prompt)
        actions = self._extract_actions(base_prompt)
        
        # Build enhanced prompt
        enhanced_prompt = self._build_cinematic_prompt(
            base_prompt, subjects, actions, style
        )
        
        return enhanced_prompt
    
    def _extract_subjects(self, prompt: str) -> List[str]:
        """Extract main subjects from prompt"""
        # Simple extraction - could be enhanced with NLP
        subjects = []
        
        # Common subject patterns
        person_patterns = r'\b(person|man|woman|child|character|people)\b'
        object_patterns = r'\b(car|building|tree|object|device|machine)\b'
        
        if re.search(person_patterns, prompt, re.I):
            subjects.append('person')
        if re.search(object_patterns, prompt, re.I):
            subjects.append('object')
            
        return subjects
    
    def _extract_actions(self, prompt: str) -> List[str]:
        """Extract main actions from prompt"""
        # Action verbs
        action_patterns = r'\b(walk|run|jump|move|turn|look|speak|create|build|transform)\b'
        matches = re.findall(action_patterns, prompt, re.I)
        return matches
    
    def _build_cinematic_prompt(
        self, 
        base_prompt: str, 
        subjects: List[str], 
        actions: List[str],
        style: str
    ) -> str:
        """Build a cinematically enhanced prompt"""
        
        # Start with the base
        enhanced = f"{base_prompt}\n\nCINEMATIC DETAILS:\n"
        
        # Add camera work
        enhanced += f"Camera: {self._select_camera_setup(subjects, actions)}\n"
        
        # Add lighting
        enhanced += f"Lighting: {self._select_lighting(style)}\n"
        
        # Add temporal breakdown
        enhanced += f"Timing: {self._create_temporal_breakdown(actions)}\n"
        
        # Add style keywords
        style_keywords = self.style_enhancers.get(style, self.style_enhancers['cinematic'])
        enhanced += f"Style: {', '.join(style_keywords[:5])}\n"
        
        # Add technical specs
        enhanced += "Technical: 8K resolution, 24fps, motion blur, perfect physics\n"
        
        return enhanced
    
    def _select_camera_setup(self, subjects: List[str], actions: List[str]) -> str:
        """Select appropriate camera setup based on content"""
        
        # Dynamic shots for action
        if any(action in ['run', 'jump', 'move'] for action in actions):
            return "Steadicam following action, 35mm lens, medium shot transitioning to wide"
        
        # Intimate shots for people
        elif 'person' in subjects:
            return "Slow dolly in, 85mm portrait lens, shallow DOF with bokeh"
        
        # Wide establishing for scenes
        else:
            return "Crane establishing shot, 24mm wide-angle, deep focus"
    
    def _select_lighting(self, style: str) -> str:
        """Select lighting setup based on style"""
        
        lighting_presets = {
            'cinematic': "Golden hour with rim lighting, motivated practicals, atmospheric haze",
            'realistic': "Natural daylight, soft shadows, bounce fill, accurate color temperature",
            'dramatic': "Low-key lighting, strong key light from 45°, minimal fill, deep shadows",
            'vibrant': "High-key lighting, colorful practicals, neon accents, saturated colors",
            'moody': "Blue hour atmosphere, silhouettes, fog machine, selective illumination"
        }
        
        return lighting_presets.get(style, lighting_presets['cinematic'])
    
    def _create_temporal_breakdown(self, actions: List[str]) -> str:
        """Create detailed temporal breakdown"""
        
        if len(actions) >= 3:
            return (
                f"0-2s: Establish scene with slow {self.cinematography_terms['camera_movements'][0]}, "
                f"2-5s: Main action '{actions[0]}' with dynamic framing, "
                f"5-7s: Climax moment with {self.cinematography_terms['shot_types'][1]}, "
                f"7-8s: Resolution with pull focus to background"
            )
        else:
            return (
                "0-2s: Atmospheric establishing shot, "
                "2-6s: Main subject focus with subtle camera movement, "
                "6-8s: Elegant closing frame with rack focus"
            )
    
    def generate_style_prompt(self, topic: str, style: str = 'cinematic') -> Dict:
        """Generate a complete style-optimized prompt structure"""
        
        return {
            'base_prompt': topic,
            'camera_work': self._select_camera_setup(['general'], ['general']),
            'lighting': self._select_lighting(style),
            'style_keywords': self.style_enhancers.get(style, [])[:8],
            'technical_specs': {
                'resolution': '8K',
                'fps': '24fps with motion blur',
                'aspect_ratio': '2.39:1 anamorphic' if style == 'cinematic' else '16:9',
                'color_space': 'Rec.709 with film emulation LUT',
                'depth': 'Shallow DOF with circular bokeh'
            },
            'audio_cues': self._generate_audio_suggestions(topic, style)
        }
    
    def _generate_audio_suggestions(self, topic: str, style: str) -> List[str]:
        """Generate audio suggestions based on content and style"""
        
        audio_presets = {
            'cinematic': ['orchestral score', 'ambient soundscape', 'subtle foley', 'room tone'],
            'realistic': ['natural ambience', 'realistic foley', 'diegetic sound only'],
            'dramatic': ['tense strings', 'impact sounds', 'silence for emphasis', 'reverb'],
            'upbeat': ['energetic music', 'rhythmic cuts', 'positive tones', 'crisp sound'],
            'tech': ['electronic music', 'UI sounds', 'futuristic ambience', 'digital effects']
        }
        
        # Detect tech topics
        if any(word in topic.lower() for word in ['ai', 'code', 'tech', 'digital', 'computer']):
            return audio_presets['tech']
        
        return audio_presets.get(style, audio_presets['cinematic'])