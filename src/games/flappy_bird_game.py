# src/games/flappy_bird_game.py
import tkinter as tk
from tkinter import ttk
import random
import time
import math

class FlappyBirdGame:
    """Flappy Bird game implementation"""
    
    def __init__(self, parent_frame, game_event_callback):
        self.parent_frame = parent_frame
        self.game_event_callback = game_event_callback
        
        # Game constants
        self.GAME_WIDTH = 600
        self.GAME_HEIGHT = 400
        self.BIRD_SIZE = 20
        self.BIRD_X = 100
        self.PIPE_WIDTH = 60
        self.PIPE_GAP = 120
        self.GRAVITY = 0.8
        self.JUMP_STRENGTH = -12
        self.PIPE_SPEED = 3
        self.PIPE_SPAWN_DISTANCE = 250
        
        # Game state
        self.running = False
        self.score = 0
        self.bird_y = self.GAME_HEIGHT // 2
        self.bird_velocity = 0
        self.pipes = []
        self.game_start_time = None
        
        # UI elements
        self.game_canvas = None
        self.info_frame = None
        self.score_label = None
        self.instruction_label = None
        
        # Game objects
        self.bird_id = None
        self.next_pipe_x = self.GAME_WIDTH
        
        # Timers
        self.game_loop_timer = None
        
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
        self.score_label = ttk.Label(self.info_frame, text="Score: 0", font=("Arial", 16, "bold"))
        self.score_label.pack(side=tk.LEFT, padx=5)
        
        # Instructions
        self.instruction_label = ttk.Label(
            self.info_frame, 
            text="Press SPACE or Click to Jump!", 
            font=("Arial", 12)
        )
        self.instruction_label.pack(side=tk.RIGHT, padx=5)
        
        # Game canvas
        self.game_canvas = tk.Canvas(
            self.parent_frame,
            bg='lightblue',
            width=self.GAME_WIDTH,
            height=self.GAME_HEIGHT
        )
        self.game_canvas.pack(padx=10, pady=5)
        
        # Bind events
        self.game_canvas.bind("<Button-1>", self.on_click)
        self.game_canvas.focus_set()
        self.game_canvas.bind("<KeyPress-space>", self.on_space)
        
        # Make canvas focusable
        self.game_canvas.config(highlightthickness=1)
        
        self.show_start_message()
    
    def show_start_message(self):
        """Show start message"""
        self.game_canvas.create_text(
            self.GAME_WIDTH // 2, self.GAME_HEIGHT // 2,
            text="Flappy Bird\n\nPress SPACE or Click to jump!\nAvoid the pipes!\n\nGame will start automatically...",
            font=("Arial", 16),
            fill="darkblue",
            justify=tk.CENTER,
            tags="start_message"
        )
    
    def start(self):
        """Start the game"""
        self.running = True
        self.score = 0
        self.bird_y = self.GAME_HEIGHT // 2
        self.bird_velocity = 0
        self.pipes = []
        self.next_pipe_x = self.GAME_WIDTH
        self.game_start_time = time.time()
        
        # Clear start message
        self.game_canvas.delete("start_message")
        
        # Focus canvas for key events
        self.game_canvas.focus_set()
        
        # Create bird
        self.create_bird()
        
        # Emit game start event
        self.game_event_callback('flappy_bird_game_start', {
            'score': self.score
        })
        
        # Start game loop
        self.game_loop()
        
        print("Flappy Bird game started")
    
    def stop(self):
        """Stop the game"""
        self.running = False
        
        # Cancel timer
        if self.game_loop_timer:
            self.parent_frame.after_cancel(self.game_loop_timer)
        
        # Show game over message
        self.game_canvas.create_text(
            self.GAME_WIDTH // 2, self.GAME_HEIGHT // 2,
            text=f"Game Over!\n\nFinal Score: {self.score}\n\nClick to restart",
            font=("Arial", 18, "bold"),
            fill="red",
            justify=tk.CENTER,
            tags="game_over"
        )
        
        # Emit game over event
        self.game_event_callback('flappy_bird_game_over', {
            'finalScore': self.score
        })
        
        print(f"Flappy Bird game ended - Score: {self.score}")
    
    def create_bird(self):
        """Create the bird sprite"""
        self.bird_id = self.game_canvas.create_oval(
            self.BIRD_X - self.BIRD_SIZE // 2,
            self.bird_y - self.BIRD_SIZE // 2,
            self.BIRD_X + self.BIRD_SIZE // 2,
            self.bird_y + self.BIRD_SIZE // 2,
            fill="yellow",
            outline="orange",
            width=2,
            tags="bird"
        )
    
    def jump(self):
        """Make the bird jump"""
        if self.running:
            self.bird_velocity = self.JUMP_STRENGTH
            
            # Emit jump event
            self.game_event_callback('flappy_bird_jump', {
                'bird_y': self.bird_y,
                'velocity': self.bird_velocity
            })
    
    def on_click(self, event):
        """Handle mouse click"""
        if not self.running:
            # Restart game if it's over
            if "game_over" in [tag for item in self.game_canvas.find_all() for tag in self.game_canvas.gettags(item)]:
                self.restart_game()
        else:
            self.jump()
    
    def on_space(self, event):
        """Handle space key press"""
        if self.running:
            self.jump()
    
    def restart_game(self):
        """Restart the game"""
        self.game_canvas.delete("all")
        self.start()
    
    def create_pipe(self, x):
        """Create a pipe at position x"""
        # Random gap position
        gap_top = random.randint(60, self.GAME_HEIGHT - self.PIPE_GAP - 60)
        gap_bottom = gap_top + self.PIPE_GAP
        
        # Top pipe
        top_pipe = self.game_canvas.create_rectangle(
            x, 0,
            x + self.PIPE_WIDTH, gap_top,
            fill="green",
            outline="darkgreen",
            width=2,
            tags="pipe"
        )
        
        # Bottom pipe
        bottom_pipe = self.game_canvas.create_rectangle(
            x, gap_bottom,
            x + self.PIPE_WIDTH, self.GAME_HEIGHT,
            fill="green",
            outline="darkgreen",
            width=2,
            tags="pipe"
        )
        
        pipe_data = {
            'x': x,
            'gap_top': gap_top,
            'gap_bottom': gap_bottom,
            'top_pipe': top_pipe,
            'bottom_pipe': bottom_pipe,
            'scored': False
        }
        
        self.pipes.append(pipe_data)
        return pipe_data
    
    def update_bird(self):
        """Update bird physics"""
        # Apply gravity
        self.bird_velocity += self.GRAVITY
        self.bird_y += self.bird_velocity
        
        # Update bird position on canvas
        if self.bird_id:
            self.game_canvas.coords(
                self.bird_id,
                self.BIRD_X - self.BIRD_SIZE // 2,
                self.bird_y - self.BIRD_SIZE // 2,
                self.BIRD_X + self.BIRD_SIZE // 2,
                self.bird_y + self.BIRD_SIZE // 2
            )
        
        # Check bounds
        if self.bird_y <= 0 or self.bird_y >= self.GAME_HEIGHT:
            self.stop()
            return False
        
        return True
    
    def update_pipes(self):
        """Update pipe positions and check collisions"""
        # Move existing pipes
        for pipe in self.pipes[:]:  # Copy list since we might modify it
            pipe['x'] -= self.PIPE_SPEED
            
            # Update pipe positions on canvas
            self.game_canvas.move(pipe['top_pipe'], -self.PIPE_SPEED, 0)
            self.game_canvas.move(pipe['bottom_pipe'], -self.PIPE_SPEED, 0)
            
            # Check if pipe is off screen
            if pipe['x'] + self.PIPE_WIDTH < 0:
                self.game_canvas.delete(pipe['top_pipe'])
                self.game_canvas.delete(pipe['bottom_pipe'])
                self.pipes.remove(pipe)
                continue
            
            # Check scoring
            if not pipe['scored'] and pipe['x'] + self.PIPE_WIDTH < self.BIRD_X:
                pipe['scored'] = True
                self.score += 1
                self.score_label.config(text=f"Score: {self.score}")
                
                # Emit score update event
                self.game_event_callback('flappy_bird_score_update', {
                    'score': self.score
                })
            
            # Check collision
            if (self.BIRD_X + self.BIRD_SIZE // 2 > pipe['x'] and 
                self.BIRD_X - self.BIRD_SIZE // 2 < pipe['x'] + self.PIPE_WIDTH):
                
                if (self.bird_y - self.BIRD_SIZE // 2 < pipe['gap_top'] or 
                    self.bird_y + self.BIRD_SIZE // 2 > pipe['gap_bottom']):
                    
                    self.stop()
                    return False
        
        # Spawn new pipes
        if self.next_pipe_x <= self.GAME_WIDTH:
            self.create_pipe(self.next_pipe_x)
            self.next_pipe_x += self.PIPE_SPAWN_DISTANCE
        else:
            self.next_pipe_x -= self.PIPE_SPEED
        
        return True
    
    def draw_background(self):
        """Draw background elements"""
        # Draw ground
        self.game_canvas.create_rectangle(
            0, self.GAME_HEIGHT - 20,
            self.GAME_WIDTH, self.GAME_HEIGHT,
            fill="brown",
            outline="",
            tags="background"
        )
        
        # Draw clouds (simple decoration)
        for i in range(3):
            x = (i + 1) * self.GAME_WIDTH // 4
            y = 50 + i * 20
            self.game_canvas.create_oval(
                x - 30, y - 15,
                x + 30, y + 15,
                fill="white",
                outline="lightgray",
                tags="background"
            )
    
    def game_loop(self):
        """Main game loop"""
        if not self.running:
            return
        
        # Clear dynamic elements (keep background)
        self.game_canvas.delete("background")
        
        # Draw background
        self.draw_background()
        
        # Update game state
        if not self.update_bird():
            return
        
        if not self.update_pipes():
            return
        
        # Schedule next frame
        self.game_loop_timer = self.parent_frame.after(16, self.game_loop)  # ~60 FPS