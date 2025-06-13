# src/config.py - Configuration management for FaceIt Analysis System
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """Configuration manager for the FaceIt Analysis System"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/config.json"
        self.config_data = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        config_file = Path(self.config_path)
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    self.config_data = json.load(f)
                print(f"✅ Configuration loaded from {config_file}")
            except Exception as e:
                print(f"⚠️ Failed to load config from {config_file}: {e}")
                self.config_data = self.get_default_config()
        else:
            print(f"⚠️ Config file not found at {config_file}, using defaults")
            self.config_data = self.get_default_config()
            self.save_config()  # Save default config
    
    def save_config(self):
        """Save configuration to file"""
        config_file = Path(self.config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config_data, f, indent=4)
            print(f"✅ Configuration saved to {config_file}")
        except Exception as e:
            print(f"❌ Failed to save config to {config_file}: {e}")
    
    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            "camera": {
                "default_index": 0,
                "resolution": {
                    "width": 1280,
                    "height": 720
                },
                "fps": 30,
                "buffer_size": 1
            },
            "eye_tracking": {
                "enabled": True,
                "calibration_points": 9,
                "model_save_path": "models/eye_tracking_model.pkl",
                "confidence_threshold": 0.5
            },
            "emotion_analysis": {
                "enabled": True,
                "frame_skip": 30,
                "face_model": "retinaface",
                "landmark_model": "mobilefacenet",
                "au_model": "xgb", 
                "emotion_model": "resmasknet",
                "device": "cpu"
            },
            "games": {
                "stress_click": {
                    "default_duration": 30,
                    "difficulty_levels": 5,
                    "target_lifetime": 2.0,
                    "spawn_interval": 1.0,
                    "min_target_size": 30,
                    "max_target_size": 80
                },
                "flappy_bird": {
                    "gravity": 0.8,
                    "jump_strength": -12,
                    "pipe_speed": 3,
                    "pipe_gap": 120
                }
            },
            "recording": {
                "video_format": "mp4",
                "export_raw_frames": False,
                "max_frames_memory": 1000,
                "output_directory": "recordings",
                "video_codec": "mp4v"
            },
            "visualization": {
                "emotion_colors": {
                    "anger": "#ef4444",
                    "disgust": "#f97316",
                    "fear": "#a855f7", 
                    "happiness": "#22c55e",
                    "sadness": "#3b82f6",
                    "surprise": "#eab308",
                    "neutral": "#6b7280"
                },
                "realtime_update_interval": 100,
                "max_realtime_points": 100
            },
            "ui": {
                "window_size": "1400x900",
                "theme": "default",
                "font_family": "Arial",
                "font_size": 10
            },
            "export": {
                "default_format": "json",
                "include_video": True,
                "compress_data": False,
                "export_directory": "exports"
            }
        }
    
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'camera.fps')"""
        keys = key_path.split('.')
        value = self.config_data
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value):
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self.config_data
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
    
    def get_camera_config(self) -> Dict[str, Any]:
        """Get camera configuration"""
        return self.get('camera', {})
    
    def get_eye_tracking_config(self) -> Dict[str, Any]:
        """Get eye tracking configuration"""
        return self.get('eye_tracking', {})
    
    def get_emotion_config(self) -> Dict[str, Any]:
        """Get emotion analysis configuration"""
        return self.get('emotion_analysis', {})
    
    def get_game_config(self, game_name: str) -> Dict[str, Any]:
        """Get configuration for specific game"""
        return self.get(f'games.{game_name}', {})
    
    def get_recording_config(self) -> Dict[str, Any]:
        """Get recording configuration"""
        return self.get('recording', {})
    
    def get_visualization_config(self) -> Dict[str, Any]:
        """Get visualization configuration"""
        return self.get('visualization', {})
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values"""
        def update_nested_dict(target, source):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    update_nested_dict(target[key], value)
                else:
                    target[key] = value
        
        update_nested_dict(self.config_data, updates)
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config_data = self.get_default_config()
        self.save_config()
    
    def validate_config(self) -> bool:
        """Validate configuration values"""
        errors = []
        
        # Check camera configuration
        camera_index = self.get('camera.default_index', 0)
        if not isinstance(camera_index, int) or camera_index < 0:
            errors.append("Invalid camera index")
        
        # Check resolution
        width = self.get('camera.resolution.width', 1280)
        height = self.get('camera.resolution.height', 720)
        if not (isinstance(width, int) and isinstance(height, int) and width > 0 and height > 0):
            errors.append("Invalid camera resolution")
        
        # Check FPS
        fps = self.get('camera.fps', 30)
        if not isinstance(fps, (int, float)) or fps <= 0:
            errors.append("Invalid camera FPS")
        
        # Check paths exist
        output_dir = self.get('recording.output_directory', 'recordings')
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except:
                errors.append(f"Cannot create output directory: {output_dir}")
        
        if errors:
            print("❌ Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        print("✅ Configuration validation passed")
        return True
    
    def print_config(self):
        """Print current configuration"""
        print("Current Configuration:")
        print("=" * 50)
        print(json.dumps(self.config_data, indent=2))
    
    def export_config(self, filename: str):
        """Export configuration to a file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.config_data, f, indent=4)
            print(f"✅ Configuration exported to {filename}")
        except Exception as e:
            print(f"❌ Failed to export configuration: {e}")


# Global config instance
config = Config()

def get_config() -> Config:
    """Get the global configuration instance"""
    return config

def reload_config():
    """Reload configuration from file"""
    global config
    config.load_config()