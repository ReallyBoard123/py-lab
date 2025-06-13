# src/emotion_analyzer.py
import numpy as np
import cv2
import time
from typing import Optional, Dict
import pandas as pd

try:
    from feat import Detector
    FEAT_AVAILABLE = True
except ImportError:
    FEAT_AVAILABLE = False
    print("py-feat not available. Install with: pip install py-feat")

class EmotionAnalyzer:
    """Facial emotion analysis using py-feat"""
    
    def __init__(self):
        self.detector = None
        self.running = False
        self.emotion_history = []
        self.au_history = []
        self.current_emotions = None
        self.current_aus = None
        self.frame_skip = 30  # Process every 30th frame for performance
        self.frame_count = 0
        
        # Emotion labels
        self.emotion_labels = [
            'anger', 'disgust', 'fear', 'happiness', 
            'sadness', 'surprise', 'neutral'
        ]
        
    def is_available(self) -> bool:
        """Check if py-feat is available"""
        return FEAT_AVAILABLE
    
    def initialize(self) -> bool:
        """Initialize the detector"""
        if not FEAT_AVAILABLE:
            print("py-feat not available")
            return False
        
        try:
            print("Initializing emotion detector...")
            # Initialize detector with optimized settings for real-time use
            self.detector = Detector(
                face_model="retinaface",  # Fast face detection
                landmark_model="mobilefacenet",  # Lightweight landmarks
                au_model="xgb",  # Fast AU detection
                emotion_model="resmasknet",  # Good emotion detection
                facepose_model="img2pose",  # Head pose estimation
                device="cpu"  # Use CPU for compatibility
            )
            print("✓ Emotion detector initialized")
            return True
            
        except Exception as e:
            print(f"✗ Failed to initialize emotion detector: {e}")
            return False
    
    def start(self) -> bool:
        """Start emotion analysis"""
        if not self.detector:
            if not self.initialize():
                return False
        
        self.running = True
        self.emotion_history = []
        self.au_history = []
        self.frame_count = 0
        print("Emotion analysis started")
        return True
    
    def stop(self):
        """Stop emotion analysis"""
        self.running = False
        print("Emotion analysis stopped")
    
    def process_frame(self, frame: np.ndarray) -> Optional[Dict]:
        """Process frame and return emotion data"""
        if not self.running or not self.detector:
            return None
        
        self.frame_count += 1
        
        # Skip frames for performance
        if self.frame_count % self.frame_skip != 0:
            return self.current_emotions
        
        try:
            # Convert BGR to RGB for py-feat
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect emotions and AUs
            result = self.detector.detect_image(frame_rgb)
            
            if result is not None and len(result) > 0:
                # Extract emotion data
                emotions = {}
                aus = {}
                
                # Get the first (main) face
                face_data = result.iloc[0]
                
                # Extract emotions
                for emotion in self.emotion_labels:
                    if emotion in face_data:
                        emotions[emotion] = float(face_data[emotion])
                
                # Extract Action Units (AUs)
                au_columns = [col for col in face_data.index if col.startswith('AU')]
                for au_col in au_columns:
                    aus[au_col] = float(face_data[au_col])
                
                # Store current results
                self.current_emotions = emotions
                self.current_aus = aus
                
                # Add to history with timestamp
                timestamp = time.time()
                self.emotion_history.append({
                    'timestamp': timestamp,
                    **emotions
                })
                
                self.au_history.append({
                    'timestamp': timestamp,
                    **aus
                })
                
                # Limit history size
                if len(self.emotion_history) > 500:
                    self.emotion_history = self.emotion_history[-500:]
                if len(self.au_history) > 500:
                    self.au_history = self.au_history[-500:]
                
                return {
                    'emotions': emotions,
                    'action_units': aus,
                    'timestamp': timestamp
                }
        
        except Exception as e:
            print(f"Emotion analysis error: {e}")
        
        return None
    
    def get_current_emotions(self) -> Optional[Dict]:
        """Get current emotion state"""
        return self.current_emotions
    
    def get_current_aus(self) -> Optional[Dict]:
        """Get current Action Units"""
        return self.current_aus
    
    def get_emotion_history(self) -> list:
        """Get emotion history"""
        return self.emotion_history.copy()
    
    def get_au_history(self) -> list:
        """Get Action Unit history"""
        return self.au_history.copy()
    
    def get_dominant_emotion(self) -> Optional[str]:
        """Get the currently dominant emotion"""
        if not self.current_emotions:
            return None
        
        # Find emotion with highest value (excluding neutral)
        emotions_no_neutral = {k: v for k, v in self.current_emotions.items() if k != 'neutral'}
        if not emotions_no_neutral:
            return 'neutral'
        
        return max(emotions_no_neutral, key=emotions_no_neutral.get)
    
    def get_emotion_statistics(self) -> Dict:
        """Calculate emotion statistics from history"""
        if not self.emotion_history:
            return {}
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(self.emotion_history)
        
        statistics = {}
        for emotion in self.emotion_labels:
            if emotion in df.columns:
                emotion_data = df[emotion]
                statistics[emotion] = {
                    'mean': float(emotion_data.mean()),
                    'std': float(emotion_data.std()),
                    'min': float(emotion_data.min()),
                    'max': float(emotion_data.max()),
                    'peaks': self._find_peaks(emotion_data.values),
                    'duration_above_threshold': self._calculate_duration_above_threshold(
                        emotion_data.values, threshold=0.5
                    )
                }
        
        return statistics
    
    def get_au_statistics(self) -> Dict:
        """Calculate Action Unit statistics from history"""
        if not self.au_history:
            return {}
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(self.au_history)
        
        statistics = {}
        au_columns = [col for col in df.columns if col.startswith('AU')]
        
        for au in au_columns:
            if au in df.columns:
                au_data = df[au]
                statistics[au] = {
                    'mean': float(au_data.mean()),
                    'std': float(au_data.std()),
                    'min': float(au_data.min()),
                    'max': float(au_data.max()),
                    'activation_rate': float((au_data > 0.5).mean()),
                    'max_intensity': float(au_data.max())
                }
        
        return statistics
    
    def _find_peaks(self, data: np.ndarray, min_height: float = 0.5) -> list:
        """Find peaks in emotion data"""
        peaks = []
        if len(data) < 3:
            return peaks
        
        for i in range(1, len(data) - 1):
            if (data[i] > data[i-1] and data[i] > data[i+1] and data[i] > min_height):
                peaks.append({
                    'index': i,
                    'value': data[i],
                    'timestamp': self.emotion_history[i]['timestamp'] if i < len(self.emotion_history) else None
                })
        
        return peaks
    
    def _calculate_duration_above_threshold(self, data: np.ndarray, threshold: float = 0.5) -> float:
        """Calculate total duration above threshold"""
        if len(data) == 0:
            return 0.0
        
        above_threshold = data > threshold
        total_frames = np.sum(above_threshold)
        
        # Approximate duration based on frame skip
        duration_seconds = (total_frames * self.frame_skip) / 30.0  # Assuming 30 FPS
        return duration_seconds
    
    def identify_key_moments(self, emotion_threshold: float = 0.7) -> list:
        """Identify key emotional moments"""
        key_moments = []
        
        if not self.emotion_history:
            return key_moments
        
        for i, emotion_data in enumerate(self.emotion_history):
            # Check for high emotion values
            for emotion, value in emotion_data.items():
                if emotion != 'timestamp' and value > emotion_threshold:
                    key_moments.append({
                        'timestamp': emotion_data['timestamp'],
                        'type': 'emotion_spike',
                        'emotion': emotion,
                        'value': value,
                        'reason': f"High {emotion} detected ({value:.2f})",
                        'frame_index': i
                    })
        
        return key_moments