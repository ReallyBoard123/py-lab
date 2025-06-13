# src/eye_tracker.py
import numpy as np
from typing import Optional, Tuple
import cv2
import time

try:
    from eyetrax import GazeEstimator, run_9_point_calibration
    EYETRAX_AVAILABLE = True
except ImportError:
    EYETRAX_AVAILABLE = False
    print("EyeTrax not available. Install with: pip install eyetrax")

class EyeTracker:
    """Eye tracking using EyeTrax"""
    
    def __init__(self):
        self.gaze_estimator = None
        self.calibrated = False
        self.running = False
        self.last_gaze_point = None
        self.gaze_history = []
        self.screen_width = 1920  # Default screen resolution
        self.screen_height = 1080
        
        # Get actual screen resolution
        try:
            import tkinter as tk
            root = tk.Tk()
            self.screen_width = root.winfo_screenwidth()
            self.screen_height = root.winfo_screenheight()
            root.destroy()
        except:
            pass
    
    def is_available(self) -> bool:
        """Check if EyeTrax is available"""
        return EYETRAX_AVAILABLE
    
    def calibrate(self, camera_index: int = None) -> bool:
        """Calibrate the eye tracking system"""
        if not EYETRAX_AVAILABLE:
            print("EyeTrax not available for calibration")
            return False
        
        try:
            print("Starting EyeTrax calibration...")
            
            # Auto-detect camera if not specified
            if camera_index is None:
                from .camera_manager import CameraManager
                available_cameras = CameraManager.list_available_cameras()
                if not available_cameras:
                    print("✗ No cameras detected for calibration")
                    return False
                camera_index = available_cameras[0]['index']
                print(f"Using camera index {camera_index}")
            
            print("Follow the instructions in the calibration window")
            
            # Create gaze estimator
            self.gaze_estimator = GazeEstimator()
            
            # Run calibration
            run_9_point_calibration(self.gaze_estimator, camera_index=camera_index)
            
            self.calibrated = True
            print("✓ Eye tracking calibration completed successfully!")
            return True
            
        except Exception as e:
            print(f"✗ Eye tracking calibration failed: {e}")
            self.calibrated = False
            return False
    
    def is_calibrated(self) -> bool:
        """Check if system is calibrated"""
        return self.calibrated and self.gaze_estimator is not None
    
    def start(self) -> bool:
        """Start eye tracking"""
        if not self.is_calibrated():
            print("Eye tracking not calibrated")
            return False
        
        self.running = True
        self.gaze_history = []
        print("Eye tracking started")
        return True
    
    def stop(self):
        """Stop eye tracking"""
        self.running = False
        print("Eye tracking stopped")
    
    def process_frame(self, frame: np.ndarray) -> Optional[Tuple[float, float]]:
        """Process frame and return gaze point"""
        if not self.running or not self.is_calibrated():
            return None
        
        try:
            # Extract features from frame
            features, blink_detected = self.gaze_estimator.extract_features(frame)
            
            if features is not None and not blink_detected:
                # Predict gaze point
                gaze_point = self.gaze_estimator.predict(np.array([features]))[0]
                
                # Clamp to screen bounds
                x = max(0, min(self.screen_width, gaze_point[0]))
                y = max(0, min(self.screen_height, gaze_point[1]))
                
                self.last_gaze_point = (x, y)
                
                # Add to history with timestamp
                self.gaze_history.append({
                    'x': x,
                    'y': y,
                    'timestamp': time.time(),
                    'confidence': 1.0  # EyeTrax doesn't provide confidence, assume 1.0
                })
                
                # Limit history size
                if len(self.gaze_history) > 1000:
                    self.gaze_history = self.gaze_history[-1000:]
                
                return (x, y)
        
        except Exception as e:
            print(f"Eye tracking error: {e}")
        
        return None
    
    def get_current_gaze(self) -> Optional[Tuple[float, float]]:
        """Get the last known gaze point"""
        return self.last_gaze_point
    
    def get_gaze_history(self) -> list:
        """Get the full gaze history"""
        return self.gaze_history.copy()
    
    def get_heatmap_data(self, grid_size: int = 50) -> list:
        """Generate heatmap data from gaze history"""
        if not self.gaze_history:
            return []
        
        # Create grid-based heatmap
        heatmap_grid = {}
        
        for point in self.gaze_history:
            grid_x = int(point['x'] // grid_size) * grid_size
            grid_y = int(point['y'] // grid_size) * grid_size
            key = f"{grid_x},{grid_y}"
            weight = point.get('confidence', 1.0)
            
            heatmap_grid[key] = heatmap_grid.get(key, 0) + weight
        
        # Convert to list format
        heatmap_data = []
        for key, weight in heatmap_grid.items():
            x_str, y_str = key.split(',')
            heatmap_data.append({
                'x': int(x_str),
                'y': int(y_str),
                'weight': weight
            })
        
        return heatmap_data
    
    def save_model(self, path: str) -> bool:
        """Save the calibrated model"""
        if not self.is_calibrated():
            return False
        
        try:
            self.gaze_estimator.save_model(path)
            print(f"Eye tracking model saved to {path}")
            return True
        except Exception as e:
            print(f"Failed to save model: {e}")
            return False
    
    def load_model(self, path: str) -> bool:
        """Load a pre-calibrated model"""
        if not EYETRAX_AVAILABLE:
            return False
        
        try:
            self.gaze_estimator = GazeEstimator()
            self.gaze_estimator.load_model(path)
            self.calibrated = True
            print(f"Eye tracking model loaded from {path}")
            return True
        except Exception as e:
            print(f"Failed to load model: {e}")
            return False
    
    def get_statistics(self) -> dict:
        """Get eye tracking statistics"""
        if not self.gaze_history:
            return {}
        
        # Calculate basic statistics
        x_coords = [p['x'] for p in self.gaze_history]
        y_coords = [p['y'] for p in self.gaze_history]
        
        return {
            'total_points': len(self.gaze_history),
            'mean_x': np.mean(x_coords),
            'mean_y': np.mean(y_coords),
            'std_x': np.std(x_coords),
            'std_y': np.std(y_coords),
            'min_x': np.min(x_coords),
            'max_x': np.max(x_coords),
            'min_y': np.min(y_coords),
            'max_y': np.max(y_coords),
            'screen_coverage_x': (np.max(x_coords) - np.min(x_coords)) / self.screen_width,
            'screen_coverage_y': (np.max(y_coords) - np.min(y_coords)) / self.screen_height
        }