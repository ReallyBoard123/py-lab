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
        
    def start(self, camera_index: int = None) -> bool:
        """Start camera capture, auto-detecting if index not specified"""
        if camera_index is not None:
            return self._start_camera(camera_index)
        
        # Auto-detect working camera
        return self._auto_detect_camera()
    
    def _start_camera(self, camera_index: int) -> bool:
        """Start camera with specific index"""
        try:
            self.cap = cv2.VideoCapture(camera_index)
            if not self.cap.isOpened():
                return False
            
            # Test if we can actually read a frame
            ret, frame = self.cap.read()
            if not ret or frame is None:
                self.cap.release()
                return False
                
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.is_running = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            print(f"✓ Camera started on index {camera_index}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to start camera {camera_index}: {e}")
            return False
    
    def _auto_detect_camera(self) -> bool:
        """Auto-detect working camera by trying multiple indices"""
        print("Auto-detecting camera...")
        
        # Try common camera indices
        for index in range(10):
            print(f"  Trying camera index {index}...")
            if self._start_camera(index):
                return True
            time.sleep(0.1)  # Brief pause between attempts
        
        print("✗ No working camera found")
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
    
    @staticmethod
    def list_available_cameras() -> list:
        """List all available camera indices"""
        available_cameras = []
        
        for index in range(10):
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                # Test if we can read a frame
                ret, frame = cap.read()
                if ret and frame is not None:
                    available_cameras.append({
                        'index': index,
                        'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                        'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                        'fps': int(cap.get(cv2.CAP_PROP_FPS))
                    })
                cap.release()
            
        return available_cameras