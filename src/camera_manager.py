# src/camera_manager.py
import cv2
import threading
import time
from typing import Optional
import numpy as np

class CameraManager:
    """Manages camera capture and frame processing"""
    
    def __init__(self):
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.capture_thread = None
        
    def start(self, camera_index: int = 0) -> bool:
        """Start camera capture"""
        try:
            self.cap = cv2.VideoCapture(camera_index)
            if not self.cap.isOpened():
                return False
                
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.is_running = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            print(f"Camera started on index {camera_index}")
            return True
            
        except Exception as e:
            print(f"Failed to start camera: {e}")
            return False
    
    def stop(self):
        """Stop camera capture"""
        self.is_running = False
        
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2.0)
            
        if self.cap:
            self.cap.release()
            self.cap = None
            
        print("Camera stopped")
    
    def _capture_loop(self):
        """Main capture loop running in separate thread"""
        while self.is_running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                with self.frame_lock:
                    self.current_frame = frame.copy()
            else:
                time.sleep(0.01)  # Brief pause if frame read fails
                
    def get_frame(self) -> Optional[np.ndarray]:
        """Get the latest frame"""
        with self.frame_lock:
            return self.current_frame.copy() if self.current_frame is not None else None
    
    def is_active(self) -> bool:
        """Check if camera is active"""
        return self.is_running and self.cap is not None and self.cap.isOpened()
    
    def get_camera_info(self) -> dict:
        """Get camera information"""
        if not self.cap:
            return {}
            
        return {
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': int(self.cap.get(cv2.CAP_PROP_FPS)),
            'fourcc': int(self.cap.get(cv2.CAP_PROP_FOURCC))
        }