# src/data_recorder.py
import numpy as np
import cv2
import time
import json
from typing import Optional, Dict, List
import os
from datetime import datetime

class DataRecorder:
    """Records and manages session data"""
    
    def __init__(self):
        self.session_active = False
        self.session_start_time = None
        self.session_data = {
            'session_info': {},
            'video_frames': [],
            'emotions': [],
            'gaze_points': [],
            'game_events': [],
            'timestamps': [],
            'frame_count': 0
        }
        
        # Video recording
        self.video_writer = None
        self.video_filename = None
        self.frame_size = (640, 480)
        self.fps = 30
        
        # Data export settings
        self.export_video = True
        self.export_raw_frames = False
        self.max_frames_in_memory = 1000  # Limit memory usage
        
    def start_session(self) -> bool:
        """Start a new recording session"""
        try:
            self.session_active = True
            self.session_start_time = time.time()
            
            # Reset session data
            self.session_data = {
                'session_info': {
                    'start_time': self.session_start_time,
                    'start_datetime': datetime.now().isoformat(),
                    'session_id': f"session_{int(self.session_start_time)}"
                },
                'video_frames': [],
                'emotions': [],
                'gaze_points': [],
                'game_events': [],
                'timestamps': [],
                'frame_count': 0
            }
            
            # Setup video recording
            if self.export_video:
                self.setup_video_recording()
            
            print(f"Data recording session started: {self.session_data['session_info']['session_id']}")
            return True
            
        except Exception as e:
            print(f"Failed to start recording session: {e}")
            return False
    
    def stop_session(self) -> Dict:
        """Stop recording session and return data"""
        self.session_active = False
        
        # Finalize session info
        if self.session_start_time:
            self.session_data['session_info']['end_time'] = time.time()
            self.session_data['session_info']['duration'] = (
                self.session_data['session_info']['end_time'] - self.session_start_time
            )
            self.session_data['session_info']['end_datetime'] = datetime.now().isoformat()
        
        # Finalize video recording
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            if self.video_filename:
                self.session_data['session_info']['video_file'] = self.video_filename
        
        print(f"Data recording session stopped. Recorded {self.session_data['frame_count']} frames")
        return self.session_data.copy()
    
    def setup_video_recording(self):
        """Setup video recording"""
        try:
            # Create output directory
            output_dir = "recordings"
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.video_filename = os.path.join(output_dir, f"session_{timestamp}.mp4")
            
            # Setup video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(
                self.video_filename,
                fourcc,
                self.fps,
                self.frame_size
            )
            
            print(f"Video recording setup: {self.video_filename}")
            
        except Exception as e:
            print(f"Failed to setup video recording: {e}")
            self.video_writer = None
    
    def add_frame_data(self, 
                      timestamp: float, 
                      frame: np.ndarray, 
                      emotions: Optional[Dict] = None, 
                      gaze_point: Optional[tuple] = None):
        """Add frame data to the session"""
        if not self.session_active:
            return
        
        try:
            # Calculate relative timestamp
            relative_timestamp = timestamp - self.session_start_time if self.session_start_time else 0
            
            # Store timestamp
            self.session_data['timestamps'].append(relative_timestamp)
            self.session_data['frame_count'] += 1
            
            # Process video frame
            if frame is not None:
                # Resize frame for consistent output
                frame_resized = cv2.resize(frame, self.frame_size)
                
                # Write to video file
                if self.video_writer:
                    self.video_writer.write(frame_resized)
                
                # Store frame in memory (limit memory usage)
                if (self.export_raw_frames and 
                    len(self.session_data['video_frames']) < self.max_frames_in_memory):
                    self.session_data['video_frames'].append({
                        'timestamp': relative_timestamp,
                        'frame': frame_resized.copy()
                    })
            
            # Store emotion data
            if emotions:
                emotion_entry = {
                    'timestamp': relative_timestamp,
                    'frame_number': self.session_data['frame_count']
                }
                
                # Add emotion data
                if 'emotions' in emotions:
                    emotion_entry.update(emotions['emotions'])
                
                # Add AU data
                if 'action_units' in emotions:
                    emotion_entry.update(emotions['action_units'])
                
                self.session_data['emotions'].append(emotion_entry)
            
            # Store gaze data
            if gaze_point:
                gaze_entry = {
                    'timestamp': relative_timestamp,
                    'frame_number': self.session_data['frame_count'],
                    'x': gaze_point[0],
                    'y': gaze_point[1],
                    'confidence': 1.0  # Default confidence
                }
                self.session_data['gaze_points'].append(gaze_entry)
                
        except Exception as e:
            print(f"Error adding frame data: {e}")
    
    def add_game_event(self, timestamp: float, event_type: str, event_data: Dict):
        """Add game event to the session"""
        if not self.session_active:
            return
        
        try:
            relative_timestamp = timestamp - self.session_start_time if self.session_start_time else 0
            
            game_event = {
                'timestamp': relative_timestamp,
                'type': event_type,
                'data': event_data,
                'frame_number': self.session_data['frame_count']
            }
            
            self.session_data['game_events'].append(game_event)
            
        except Exception as e:
            print(f"Error adding game event: {e}")
    
    def get_summary_statistics(self) -> Dict:
        """Calculate summary statistics for the session"""
        if not self.session_data:
            return {}
        
        summary = {
            'session_info': self.session_data['session_info'].copy(),
            'frame_statistics': {
                'total_frames': self.session_data['frame_count'],
                'fps': self.fps
            },
            'emotion_statistics': {},
            'gaze_statistics': {},
            'game_statistics': {}
        }
        
        # Emotion statistics
        if self.session_data['emotions']:
            emotions_df = self._emotions_to_dataframe()
            if emotions_df is not None:
                summary['emotion_statistics'] = self._calculate_emotion_stats(emotions_df)
        
        # Gaze statistics
        if self.session_data['gaze_points']:
            summary['gaze_statistics'] = self._calculate_gaze_stats()
        
        # Game statistics
        if self.session_data['game_events']:
            summary['game_statistics'] = self._calculate_game_stats()
        
        return summary
    
    def _emotions_to_dataframe(self):
        """Convert emotions data to DataFrame-like structure"""
        try:
            import pandas as pd
            return pd.DataFrame(self.session_data['emotions'])
        except ImportError:
            # Fallback without pandas
            return None
    
    def _calculate_emotion_stats(self, emotions_df) -> Dict:
        """Calculate emotion statistics"""
        if emotions_df is None or emotions_df.empty:
            return {}
        
        emotion_columns = ['anger', 'disgust', 'fear', 'happiness', 'sadness', 'surprise', 'neutral']
        stats = {}
        
        for emotion in emotion_columns:
            if emotion in emotions_df.columns:
                emotion_data = emotions_df[emotion]
                stats[emotion] = {
                    'mean': float(emotion_data.mean()),
                    'std': float(emotion_data.std()),
                    'min': float(emotion_data.min()),
                    'max': float(emotion_data.max()),
                    'peaks': self._find_emotion_peaks(emotion_data.values)
                }
        
        return stats
    
    def _calculate_gaze_stats(self) -> Dict:
        """Calculate gaze statistics"""
        gaze_points = self.session_data['gaze_points']
        if not gaze_points:
            return {}
        
        x_coords = [p['x'] for p in gaze_points]
        y_coords = [p['y'] for p in gaze_points]
        
        return {
            'total_points': len(gaze_points),
            'mean_x': np.mean(x_coords),
            'mean_y': np.mean(y_coords),
            'std_x': np.std(x_coords),
            'std_y': np.std(y_coords),
            'range_x': np.max(x_coords) - np.min(x_coords),
            'range_y': np.max(y_coords) - np.min(y_coords),
            'heatmap_data': self._generate_gaze_heatmap()
        }
    
    def _calculate_game_stats(self) -> Dict:
        """Calculate game statistics"""
        events = self.session_data['game_events']
        if not events:
            return {}
        
        stats = {
            'total_events': len(events),
            'event_types': {},
            'score_progression': [],
            'level_changes': []
        }
        
        # Count event types
        for event in events:
            event_type = event['type']
            stats['event_types'][event_type] = stats['event_types'].get(event_type, 0) + 1
        
        # Extract score progression
        for event in events:
            if event['type'] in ['score_update', 'target_hit', 'flappy_bird_score_update']:
                score = event['data'].get('score', 0)
                stats['score_progression'].append({
                    'timestamp': event['timestamp'],
                    'score': score
                })
        
        # Extract level changes
        for event in events:
            if event['type'] == 'difficulty_change':
                stats['level_changes'].append({
                    'timestamp': event['timestamp'],
                    'from_level': event['data'].get('from', 0),
                    'to_level': event['data'].get('to', 0)
                })
        
        return stats
    
    def _find_emotion_peaks(self, emotion_data: np.ndarray, min_height: float = 0.5) -> List[Dict]:
        """Find peaks in emotion data"""
        peaks = []
        if len(emotion_data) < 3:
            return peaks
        
        for i in range(1, len(emotion_data) - 1):
            if (emotion_data[i] > emotion_data[i-1] and 
                emotion_data[i] > emotion_data[i+1] and 
                emotion_data[i] > min_height):
                
                peaks.append({
                    'index': i,
                    'value': float(emotion_data[i]),
                    'timestamp': self.session_data['timestamps'][i] if i < len(self.session_data['timestamps']) else None
                })
        
        return peaks
    
    def _generate_gaze_heatmap(self, grid_size: int = 50) -> List[Dict]:
        """Generate heatmap data from gaze points"""
        gaze_points = self.session_data['gaze_points']
        if not gaze_points:
            return []
        
        heatmap_grid = {}
        
        for point in gaze_points:
            grid_x = int(point['x'] // grid_size) * grid_size
            grid_y = int(point['y'] // grid_size) * grid_size
            key = f"{grid_x},{grid_y}"
            weight = point.get('confidence', 1.0)
            
            heatmap_grid[key] = heatmap_grid.get(key, 0) + weight
        
        heatmap_data = []
        for key, weight in heatmap_grid.items():
            x_str, y_str = key.split(',')
            heatmap_data.append({
                'x': int(x_str),
                'y': int(y_str),
                'weight': weight
            })
        
        return heatmap_data
    
    def prepare_for_export(self, data: Dict) -> Dict:
        """Prepare data for JSON export"""
        export_data = data.copy()
        
        # Remove video frames from export (too large for JSON)
        if 'video_frames' in export_data:
            export_data['video_frames'] = f"Removed {len(export_data['video_frames'])} frames to reduce file size"
        
        # Convert numpy arrays to lists if any
        def convert_numpy(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(v) for v in obj]
            return obj
        
        return convert_numpy(export_data)
    
    def export_to_json(self, filename: str) -> bool:
        """Export session data to JSON file"""
        try:
            export_data = self.prepare_for_export(self.session_data)
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"Session data exported to {filename}")
            return True
            
        except Exception as e:
            print(f"Failed to export data: {e}")
            return False
    
    def save_summary_report(self, filename: str) -> bool:
        """Save a summary report"""
        try:
            summary = self.get_summary_statistics()
            
            with open(filename, 'w') as f:
                json.dump(summary, f, indent=2)
            
            print(f"Summary report saved to {filename}")
            return True
            
        except Exception as e:
            print(f"Failed to save summary report: {e}")
            return False