# src/games/stress_click_game.py
import tkinter as tk
from tkinter import ttk
import random
import time
import threading
import math

class StressClickGame:
    """Stress Click game implementation"""
    
    def __init__(self, parent_frame, game_event_callback):
        self.parent_frame = parent_frame
        self.game_event_callback = game_event_callback
        
        # Game state
        self.running = False
        self.score = 0
        self.hits = 0
        self.misses = 0
        self.level = 1
        self.targets = []
        self.game_start_time = None
        
        # Game settings
        self.game_duration = 30  # seconds
        self.target_lifetime = 2.0  # seconds
        self.spawn_interval = 1.0  # seconds between spawns
        self.min_target_size = 30
        self.max_target_size = 80
        
        # Level progression thresholds
        self.level_thresholds = [0, 10, 25, 45, 70]
        
        # UI elements
        self.game_canvas = None
        self.info_frame = None
        self.score_label = None
        self.level_label = None
        self.time_label = None
        self.accuracy_label = None
        
        # Timers
        self.spawn_timer = None
        self.game_timer = None
        self.update_timer = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the game UI"""
        # Clear parent frame
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        
        # Info panel
        self.info_frame = ttk.Frame(self.parent_frame)
        self.info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Score display
        self.score_label = ttk.Label(self.info_frame, text="Score: 0", font=("Arial", 12, "bold"))
        self.score_label.pack(side=tk.LEFT, padx=5)
        
        self.level_label = ttk.Label(self.info_frame, text="Level: 1", font=("Arial", 12))
        self.level_label.pack(side=tk.LEFT, padx=5)
        
        self.time_label = ttk.Label(self.info_frame, text="Time: 30", font=("Arial", 12))
        self.time_label.pack(side=tk.LEFT, padx=5)
        
        self.accuracy_label = ttk.Label(self.info_frame, text="Accuracy: 0%", font=("Arial", 12))
        self.accuracy_label.pack(side=tk.RIGHT, padx=5)
        
        # Game canvas
        self.game_canvas = tk.Canvas(
            self.parent_frame, 
            bg='lightgray', 
            width=600, 
            height=400,
            cursor='crosshair'
        )
        self.game_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Bind canvas events
        self.game_canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Start instruction
        self.show_start_message()
    
    def show_start_message(self):
        """Show start message"""
        self.game_canvas.create_text(
            300, 200,
            text="Stress Click Game\n\nClick the colored targets as they appear!\nTargets get smaller and faster as you progress.\n\nGame will start automatically...",
            font=("Arial", 16),
            fill="darkblue",
            justify=tk.CENTER,
            tags="start_message"
        )
    
    def start(self):
        """Start the game"""
        self.running = True
        self.score = 0
        self.hits = 0
        self.misses = 0
        self.level = 1
        self.targets = []
        self.game_start_time = time.time()
        
        # Clear start message
        self.game_canvas.delete("start_message")
        
        # Emit game start event
        self.game_event_callback('game_start', {
            'game': 'stress_click',
            'duration': self.game_duration
        })
        
        # Start game timers
        self.schedule_target_spawn()
        self.start_game_timer()
        self.start_update_loop()
        
        print("Stress Click game started")
    
    def stop(self):
        """Stop the game"""
        self.running = False
        
        # Cancel timers
        if self.spawn_timer:
            self.parent_frame.after_cancel(self.spawn_timer)
        if self.game_timer:
            self.parent_frame.after_cancel(self.game_timer)
        if self.update_timer:
            self.parent_frame.after_cancel(self.update_timer)
        
        # Clear canvas
        self.game_canvas.delete("all")
        
        # Show final score
        accuracy = (self.hits / max(1, self.hits + self.misses)) * 100
        self.game_canvas.create_text(
            300, 200,
            text=f"Game Over!\n\nFinal Score: {self.score}\nAccuracy: {accuracy:.1f}%\nLevel Reached: {self.level}",
            font=("Arial", 18, "bold"),
            fill="darkgreen",
            justify=tk.CENTER
        )
        
        # Emit game end event
        self.game_event_callback('game_end', {
            'final_score': self.score,
            'accuracy': accuracy,
            'level': self.level,
            'hits': self.hits,
            'misses': self.misses
        })
        
        print(f"Stress Click game ended - Score: {self.score}, Accuracy: {accuracy:.1f}%")
    
    def schedule_target_spawn(self):
        """Schedule the next target spawn"""
        if not self.running:
            return
        
        # Spawn target
        self.spawn_target()
        
        # Calculate next spawn time based on level
        base_interval = max(0.3, self.spawn_interval - (self.level - 1) * 0.1)
        spawn_time = int(base_interval * 1000)
        
        self.spawn_timer = self.parent_frame.after(spawn_time, self.schedule_target_spawn)
    
    def spawn_target(self):
        """Spawn a new target"""
        if not self.running:
            return
        
        canvas_width = self.game_canvas.winfo_width()
        canvas_height = self.game_canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return  # Canvas not ready
        
        # Target properties based on level
        size = max(self.min_target_size, self.max_target_size - (self.level - 1) * 8)
        lifetime = max(0.8, self.target_lifetime - (self.level - 1) * 0.1)
        
        # Random position (ensure target fits within canvas)
        x = random.randint(size, canvas_width - size)
        y = random.randint(size, canvas_height - size)
        
        # Random color (gets more intense with level)
        colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple', 'pink']
        color = random.choice(colors)
        
        # Create target
        target_id = self.game_canvas.create_oval(
            x - size//2, y - size//2,
            x + size//2, y + size//2,
            fill=color,
            outline='white',
            width=2,
            tags="target"
        )
        
        # Store target info
        target_info = {
            'id': target_id,
            'x': x,
            'y': y,
            'size': size,
            'color': color,
            'spawn_time': time.time(),
            'lifetime': lifetime
        }
        self.targets.append(target_info)
        
        # Schedule target removal
        removal_time = int(lifetime * 1000)
        self.parent_frame.after(removal_time, lambda: self.remove_target(target_id))
        
        # Add pulsing animation
        self.animate_target(target_id, size)
        
        # Emit target spawn event
        self.game_event_callback('target_spawn', {
            'target_id': target_id,
            'position': (x, y),
            'size': size,
            'level': self.level
        })
    
    def animate_target(self, target_id, base_size):
        """Add pulsing animation to target"""
        def pulse(scale=1.0, growing=True):
            try:
                # Calculate new size
                if growing:
                    scale += 0.1
                    if scale >= 1.3:
                        growing = False
                else:
                    scale -= 0.1
                    if scale <= 0.8:
                        growing = True
                
                # Get current target position
                coords = self.game_canvas.coords(target_id)
                if coords:
                    cx = (coords[0] + coords[2]) / 2
                    cy = (coords[1] + coords[3]) / 2
                    new_size = base_size * scale
                    
                    # Update target
                    self.game_canvas.coords(
                        target_id,
                        cx - new_size//2, cy - new_size//2,
                        cx + new_size//2, cy + new_size//2
                    )
                    
                    # Schedule next pulse
                    self.parent_frame.after(100, lambda: pulse(scale, growing))
                    
            except tk.TclError:
                # Target was removed
                pass
        
        pulse()
    
    def remove_target(self, target_id):
        """Remove a target (miss)"""
        try:
            # Remove from canvas
            self.game_canvas.delete(target_id)
            
            # Remove from targets list
            self.targets = [t for t in self.targets if t['id'] != target_id]
            
            # Count as miss
            self.misses += 1
            self.update_display()
            
            # Emit miss event
            self.game_event_callback('target_miss', {
                'target_id': target_id,
                'score': self.score
            })
            
        except tk.TclError:
            pass  # Target already removed
    
    def on_canvas_click(self, event):
        """Handle canvas click"""
        if not self.running:
            return
        
        # Find clicked target
        clicked_item = self.game_canvas.find_closest(event.x, event.y)[0]
        
        # Check if it's a target
        target_hit = None
        for target in self.targets[:]:  # Copy list since we might modify it
            if target['id'] == clicked_item:
                target_hit = target
                break
        
        if target_hit:
            # Calculate reaction time
            reaction_time = time.time() - target_hit['spawn_time']
            
            # Calculate points based on speed and level
            base_points = self.level * 2
            time_bonus = max(0, int((2.0 - reaction_time) * 5))
            points = base_points + time_bonus
            
            self.score += points
            self.hits += 1
            
            # Remove target
            self.game_canvas.delete(target_hit['id'])
            self.targets.remove(target_hit)
            
            # Check for level up
            old_level = self.level
            new_level = self.calculate_level()
            if new_level > old_level:
                self.level = new_level
                self.game_event_callback('difficulty_change', {
                    'from': old_level,
                    'to': new_level,
                    'score': self.score
                })
            
            # Update display
            self.update_display()
            
            # Visual feedback
            self.show_hit_feedback(event.x, event.y, points)
            
            # Emit hit event
            self.game_event_callback('target_hit', {
                'target_id': target_hit['id'],
                'reaction_time': reaction_time,
                'points': points,
                'score': self.score,
                'level': self.level
            })
        else:
            # Miss - clicked empty area
            self.misses += 1
            self.update_display()
            
            # Visual feedback for miss
            self.show_miss_feedback(event.x, event.y)
    
    def show_hit_feedback(self, x, y, points):
        """Show visual feedback for successful hit"""
        feedback_id = self.game_canvas.create_text(
            x, y,
            text=f"+{points}",
            font=("Arial", 14, "bold"),
            fill="green"
        )
        
        # Animate feedback
        def animate_feedback(step=0):
            if step < 10:
                self.game_canvas.move(feedback_id, 0, -3)
                alpha = 1.0 - (step / 10.0)
                # Note: Tkinter doesn't support alpha, so we'll just move it
                self.parent_frame.after(50, lambda: animate_feedback(step + 1))
            else:
                try:
                    self.game_canvas.delete(feedback_id)
                except tk.TclError:
                    pass
        
        animate_feedback()
    
    def show_miss_feedback(self, x, y):
        """Show visual feedback for miss"""
        feedback_id = self.game_canvas.create_text(
            x, y,
            text="Miss!",
            font=("Arial", 12),
            fill="red"
        )
        
        # Remove after delay
        self.parent_frame.after(500, lambda: self.game_canvas.delete(feedback_id))
    
    def calculate_level(self):
        """Calculate current level based on score"""
        for i in range(len(self.level_thresholds) - 1, -1, -1):
            if self.score >= self.level_thresholds[i]:
                return min(i + 1, len(self.level_thresholds))
        return 1
    
    def start_game_timer(self):
        """Start the main game timer"""
        def countdown():
            if not self.running:
                return
            
            elapsed = time.time() - self.game_start_time
            remaining = max(0, self.game_duration - elapsed)
            
            if remaining <= 0:
                self.stop()
                return
            
            self.game_timer = self.parent_frame.after(1000, countdown)
        
        countdown()
    
    def start_update_loop(self):
        """Start the display update loop"""
        def update():
            if not self.running:
                return
            
            self.update_display()
            self.update_timer = self.parent_frame.after(100, update)
        
        update()
    
    def update_display(self):
        """Update the game display"""
        elapsed = time.time() - self.game_start_time if self.game_start_time else 0
        remaining = max(0, self.game_duration - elapsed)
        
        accuracy = (self.hits / max(1, self.hits + self.misses)) * 100
        
        self.score_label.config(text=f"Score: {self.score}")
        self.level_label.config(text=f"Level: {self.level}")
        self.time_label.config(text=f"Time: {int(remaining)}")
        self.accuracy_label.config(text=f"Accuracy: {accuracy:.1f}%")
        
        # Emit score update
        self.game_event_callback('score_update', {
            'score': self.score,
            'level': self.level,
            'time_remaining': remaining,
            'accuracy': accuracy
        })