# Complete Python FaceIt Analysis System
# main.py - Entry point for the integrated system

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import cv2
import numpy as np
from datetime import datetime
import os
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd

# Import our modules
from src.camera_manager import CameraManager
from src.eye_tracker import EyeTracker
from src.emotion_analyzer import EmotionAnalyzer
from src.games.stress_click_game import StressClickGame
from src.games.flappy_bird_game import FlappyBirdGame
from src.data_recorder import DataRecorder
from src.visualizer import RealTimeVisualizer, ResultsVisualizer

class FaceItAnalysisSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FaceIt Analysis System - Python Edition")
        self.root.geometry("1400x900")
        
        # Initialize components
        self.camera_manager = CameraManager()
        self.eye_tracker = EyeTracker()
        self.emotion_analyzer = EmotionAnalyzer()
        self.data_recorder = DataRecorder()
        self.visualizer = RealTimeVisualizer()
        
        # Session state
        self.is_recording = False
        self.current_game = None
        self.session_data = {
            'emotions': [],
            'gaze_points': [],
            'game_events': [],
            'video_frames': [],
            'timestamps': []
        }
        
        # Settings
        self.settings = {
            'enable_eye_tracking': tk.BooleanVar(value=True),
            'enable_emotion_analysis': tk.BooleanVar(value=True),
            'camera_index': tk.IntVar(value=0),
            'game_duration': tk.IntVar(value=30),
            'selected_game': tk.StringVar(value='stress_click')
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the main UI"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Session tab
        self.session_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.session_frame, text="Session")
        self.setup_session_tab()
        
        # Results tab
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="Results")
        self.setup_results_tab()
        
        # Settings tab
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Settings")
        self.setup_settings_tab()
        
    def setup_session_tab(self):
        """Setup the main session interface"""
        # Left panel - Camera and controls
        left_panel = ttk.Frame(self.session_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
        
        # Camera preview
        camera_label = ttk.Label(left_panel, text="Camera Preview", font=("Arial", 12, "bold"))
        camera_label.pack(pady=(0, 10))
        
        self.camera_canvas = tk.Canvas(left_panel, width=640, height=480, bg='black')
        self.camera_canvas.pack(pady=(0, 10))
        
        # Status display
        self.status_label = ttk.Label(left_panel, text="Status: Ready", font=("Arial", 10))
        self.status_label.pack(pady=(0, 10))
        
        # Controls
        controls_frame = ttk.LabelFrame(left_panel, text="Session Controls", padding=10)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Game selection
        ttk.Label(controls_frame, text="Game:").grid(row=0, column=0, sticky=tk.W, pady=2)
        game_combo = ttk.Combobox(controls_frame, textvariable=self.settings['selected_game'],
                                 values=['stress_click', 'flappy_bird'], state='readonly')
        game_combo.grid(row=0, column=1, sticky=tk.EW, pady=2, padx=(10, 0))
        
        # Duration
        ttk.Label(controls_frame, text="Duration (seconds):").grid(row=1, column=0, sticky=tk.W, pady=2)
        duration_spin = ttk.Spinbox(controls_frame, from_=10, to=300, textvariable=self.settings['game_duration'])
        duration_spin.grid(row=1, column=1, sticky=tk.EW, pady=2, padx=(10, 0))
        
        controls_frame.columnconfigure(1, weight=1)
        
        # Action buttons
        button_frame = ttk.Frame(left_panel)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.calibrate_btn = ttk.Button(button_frame, text="Calibrate Eye Tracking", 
                                       command=self.calibrate_eye_tracking)
        self.calibrate_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.start_btn = ttk.Button(button_frame, text="Start Session", 
                                   command=self.start_session, style="Accent.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="Stop Session", 
                                  command=self.stop_session, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Right panel - Game and visualizations
        right_panel = ttk.Frame(self.session_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Game area
        self.game_frame = ttk.LabelFrame(right_panel, text="Game Area", padding=10)
        self.game_frame.pack(fill=tk.BOTH, expand=True)
        
        # Real-time data display
        data_frame = ttk.LabelFrame(right_panel, text="Live Data", padding=10)
        data_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.emotion_label = ttk.Label(data_frame, text="Emotions: --")
        self.emotion_label.pack(anchor=tk.W)
        
        self.gaze_label = ttk.Label(data_frame, text="Gaze: --")
        self.gaze_label.pack(anchor=tk.W)
        
        self.game_score_label = ttk.Label(data_frame, text="Game Score: --")
        self.game_score_label.pack(anchor=tk.W)
        
    def setup_results_tab(self):
        """Setup the results visualization tab"""
        # Create matplotlib figure for results
        self.results_fig, ((self.emotion_ax, self.gaze_ax), 
                          (self.timeline_ax, self.heatmap_ax)) = plt.subplots(2, 2, figsize=(12, 8))
        
        self.results_canvas = FigureCanvasTkAgg(self.results_fig, self.results_frame)
        self.results_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Results controls
        results_controls = ttk.Frame(self.results_frame)
        results_controls.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)
        
        ttk.Button(results_controls, text="Export Data", 
                  command=self.export_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(results_controls, text="Generate Report", 
                  command=self.generate_report).pack(side=tk.LEFT, padx=5)
        
    def setup_settings_tab(self):
        """Setup the settings tab"""
        settings_notebook = ttk.Notebook(self.settings_frame)
        settings_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # General settings
        general_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(general_frame, text="General")
        
        # Camera settings
        camera_frame = ttk.LabelFrame(general_frame, text="Camera", padding=10)
        camera_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(camera_frame, text="Camera Index:").grid(row=0, column=0, sticky=tk.W)
        ttk.Spinbox(camera_frame, from_=0, to=10, textvariable=self.settings['camera_index']).grid(row=0, column=1)
        
        # Analysis settings
        analysis_frame = ttk.LabelFrame(general_frame, text="Analysis", padding=10)
        analysis_frame.pack(fill=tk.X, pady=10)
        
        ttk.Checkbutton(analysis_frame, text="Enable Eye Tracking", 
                       variable=self.settings['enable_eye_tracking']).pack(anchor=tk.W)
        ttk.Checkbutton(analysis_frame, text="Enable Emotion Analysis", 
                       variable=self.settings['enable_emotion_analysis']).pack(anchor=tk.W)
        
    def calibrate_eye_tracking(self):
        """Calibrate the eye tracking system"""
        if not self.settings['enable_eye_tracking'].get():
            messagebox.showwarning("Warning", "Eye tracking is disabled in settings")
            return
            
        self.status_label.config(text="Status: Calibrating eye tracking...")
        self.calibrate_btn.config(state=tk.DISABLED)
        
        def calibrate():
            try:
                success = self.eye_tracker.calibrate(self.settings['camera_index'].get())
                if success:
                    self.status_label.config(text="Status: Eye tracking calibrated ✓")
                    messagebox.showinfo("Success", "Eye tracking calibration completed!")
                else:
                    self.status_label.config(text="Status: Calibration failed ✗")
                    messagebox.showerror("Error", "Eye tracking calibration failed")
            except Exception as e:
                self.status_label.config(text="Status: Calibration error ✗")
                messagebox.showerror("Error", f"Calibration error: {str(e)}")
            finally:
                self.calibrate_btn.config(state=tk.NORMAL)
        
        threading.Thread(target=calibrate, daemon=True).start()
        
    def start_session(self):
        """Start a new analysis session"""
        try:
            # Initialize camera
            if not self.camera_manager.start(self.settings['camera_index'].get()):
                messagebox.showerror("Error", "Failed to start camera")
                return
            
            # Initialize analyzers
            if self.settings['enable_emotion_analysis'].get():
                self.emotion_analyzer.start()
            
            if self.settings['enable_eye_tracking'].get():
                if not self.eye_tracker.is_calibrated():
                    messagebox.showwarning("Warning", "Eye tracking not calibrated")
                else:
                    self.eye_tracker.start()
            
            # Initialize game
            game_name = self.settings['selected_game'].get()
            if game_name == 'stress_click':
                self.current_game = StressClickGame(self.game_frame, self.on_game_event)
            elif game_name == 'flappy_bird':
                self.current_game = FlappyBirdGame(self.game_frame, self.on_game_event)
            
            self.current_game.start()
            
            # Start data recording
            self.data_recorder.start_session()
            
            # Update UI
            self.is_recording = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_label.config(text="Status: Recording session...")
            
            # Start the main processing loop
            self.process_frame()
            
            # Auto-stop after duration
            duration = self.settings['game_duration'].get() * 1000  # Convert to ms
            self.root.after(duration, self.stop_session)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start session: {str(e)}")
            
    def stop_session(self):
        """Stop the current session"""
        self.is_recording = False
        
        # Stop components
        self.camera_manager.stop()
        if self.current_game:
            self.current_game.stop()
        self.emotion_analyzer.stop()
        self.eye_tracker.stop()
        
        # Stop recording and get data
        session_data = self.data_recorder.stop_session()
        self.session_data = session_data
        
        # Update UI
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Session completed")
        
        # Switch to results tab and show analysis
        self.notebook.select(self.results_frame)
        self.show_results()
        
    def process_frame(self):
        """Main processing loop for each frame"""
        if not self.is_recording:
            return
            
        # Get frame from camera
        frame = self.camera_manager.get_frame()
        if frame is None:
            self.root.after(33, self.process_frame)  # ~30 FPS
            return
        
        timestamp = time.time()
        
        # Process with emotion analyzer
        emotions = None
        if self.settings['enable_emotion_analysis'].get():
            emotions = self.emotion_analyzer.process_frame(frame)
            if emotions:
                self.update_emotion_display(emotions)
        
        # Process with eye tracker
        gaze_point = None
        if self.settings['enable_eye_tracking'].get() and self.eye_tracker.is_calibrated():
            gaze_point = self.eye_tracker.process_frame(frame)
            if gaze_point:
                self.update_gaze_display(gaze_point)
        
        # Record data
        self.data_recorder.add_frame_data(timestamp, frame, emotions, gaze_point)
        
        # Update camera display
        self.update_camera_display(frame, gaze_point)
        
        # Schedule next frame
        self.root.after(33, self.process_frame)  # ~30 FPS
        
    def update_camera_display(self, frame, gaze_point=None):
        """Update the camera preview display"""
        # Resize frame for display
        display_frame = cv2.resize(frame, (640, 480))
        
        # Draw gaze point if available
        if gaze_point:
            cv2.circle(display_frame, (int(gaze_point[0]), int(gaze_point[1])), 
                      10, (0, 255, 0), 2)
        
        # Convert to PhotoImage and display
        frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        photo = tk.PhotoImage(data=cv2.imencode('.ppm', frame_rgb)[1].tobytes())
        self.camera_canvas.create_image(320, 240, image=photo)
        self.camera_canvas.image = photo  # Keep a reference
        
    def update_emotion_display(self, emotions):
        """Update the emotion display"""
        if emotions:
            emotion_text = ", ".join([f"{k}: {v:.2f}" for k, v in emotions.items() if v > 0.1])
            self.emotion_label.config(text=f"Emotions: {emotion_text}")
        
    def update_gaze_display(self, gaze_point):
        """Update the gaze display"""
        if gaze_point:
            self.gaze_label.config(text=f"Gaze: ({gaze_point[0]:.0f}, {gaze_point[1]:.0f})")
            
    def on_game_event(self, event_type, event_data):
        """Handle game events"""
        timestamp = time.time()
        self.data_recorder.add_game_event(timestamp, event_type, event_data)
        
        # Update game score display
        if event_type == 'score_update':
            self.game_score_label.config(text=f"Game Score: {event_data.get('score', 0)}")
            
    def show_results(self):
        """Display analysis results"""
        if not self.session_data:
            return
            
        # Create results visualizer
        results_viz = ResultsVisualizer(self.session_data)
        
        # Clear previous plots
        for ax in [self.emotion_ax, self.gaze_ax, self.timeline_ax, self.heatmap_ax]:
            ax.clear()
        
        # Generate visualizations
        results_viz.plot_emotions_timeline(self.emotion_ax)
        results_viz.plot_gaze_heatmap(self.gaze_ax)
        results_viz.plot_combined_timeline(self.timeline_ax)
        results_viz.plot_attention_heatmap(self.heatmap_ax)
        
        # Update canvas
        self.results_canvas.draw()
        
    def export_data(self):
        """Export session data"""
        if not self.session_data:
            messagebox.showwarning("Warning", "No data to export")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"faceit_session_{timestamp}.json"
        
        try:
            # Convert numpy arrays to lists for JSON serialization
            export_data = self.data_recorder.prepare_for_export(self.session_data)
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            messagebox.showinfo("Success", f"Data exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")
            
    def generate_report(self):
        """Generate a comprehensive report"""
        if not self.session_data:
            messagebox.showwarning("Warning", "No data to generate report")
            return
            
        # TODO: Implement report generation
        messagebox.showinfo("Info", "Report generation feature coming soon!")
        
    def run(self):
        """Start the application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            # Cleanup
            self.camera_manager.stop()
            if self.current_game:
                self.current_game.stop()


def main():
    """Main entry point"""
    print("Starting FaceIt Analysis System...")
    
    # Check dependencies
    try:
        import cv2
        import feat
        import eyetrax
        print("✓ All dependencies available")
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please install required packages:")
        print("pip install opencv-python py-feat eyetrax matplotlib pandas")
        return
    
    # Create and run application
    app = FaceItAnalysisSystem()
    app.run()


if __name__ == "__main__":
    main()