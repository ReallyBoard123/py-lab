# src/visualizer.py
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import seaborn as sns

class RealTimeVisualizer:
    """Real-time visualization for live data"""
    
    def __init__(self):
        self.fig = None
        self.axes = {}
        self.emotion_lines = {}
        self.gaze_scatter = None
        self.max_points = 100  # Limit points for performance
        
    def setup_realtime_plot(self):
        """Setup real-time plotting interface"""
        plt.ion()  # Turn on interactive mode
        self.fig, ((self.emotion_ax, self.gaze_ax), 
                  (self.au_ax, self.game_ax)) = plt.subplots(2, 2, figsize=(12, 8))
        
        self.fig.suptitle("Real-Time FaceIt Analysis", fontsize=16)
        
        # Setup emotion plot
        self.emotion_ax.set_title("Live Emotions")
        self.emotion_ax.set_xlabel("Time (frames)")
        self.emotion_ax.set_ylabel("Intensity")
        self.emotion_ax.set_ylim(0, 1)
        
        # Setup gaze plot
        self.gaze_ax.set_title("Gaze Points")
        self.gaze_ax.set_xlabel("X Position")
        self.gaze_ax.set_ylabel("Y Position")
        
        # Setup AU plot
        self.au_ax.set_title("Action Units")
        self.au_ax.set_xlabel("Time (frames)")
        self.au_ax.set_ylabel("Intensity")
        
        # Setup game events plot
        self.game_ax.set_title("Game Events")
        self.game_ax.set_xlabel("Time (frames)")
        self.game_ax.set_ylabel("Score")
        
        plt.tight_layout()
    
    def update_realtime_data(self, emotion_data=None, gaze_data=None, game_data=None):
        """Update real-time visualizations"""
        if not self.fig:
            return
        
        # Update emotion data
        if emotion_data:
            self.update_emotion_plot(emotion_data)
        
        # Update gaze data
        if gaze_data:
            self.update_gaze_plot(gaze_data)
        
        # Update game data
        if game_data:
            self.update_game_plot(game_data)
        
        # Refresh display
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()


class ResultsVisualizer:
    """Generate comprehensive analysis visualizations"""
    
    def __init__(self, session_data: Dict):
        self.session_data = session_data
        self.emotion_colors = {
            'anger': '#ef4444',
            'disgust': '#f97316',
            'fear': '#a855f7',
            'happiness': '#22c55e',
            'sadness': '#3b82f6',
            'surprise': '#eab308',
            'neutral': '#6b7280'
        }
    
    def plot_emotions_timeline(self, ax):
        """Plot emotions over time"""
        emotions_data = self.session_data.get('emotions', [])
        if not emotions_data:
            ax.text(0.5, 0.5, 'No emotion data available', 
                   transform=ax.transAxes, ha='center', va='center')
            return
        
        # Convert to DataFrame for easier plotting
        df = pd.DataFrame(emotions_data)
        
        # Plot each emotion
        emotion_columns = ['anger', 'disgust', 'fear', 'happiness', 'sadness', 'surprise', 'neutral']
        
        for emotion in emotion_columns:
            if emotion in df.columns:
                ax.plot(df['timestamp'], df[emotion], 
                       label=emotion.capitalize(), 
                       color=self.emotion_colors[emotion],
                       linewidth=2, alpha=0.8)
        
        # Add game events as vertical lines
        self.add_game_events_to_plot(ax)
        
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('Emotion Intensity')
        ax.set_title('Emotional Timeline')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1)
    
    def plot_gaze_heatmap(self, ax):
        """Plot gaze heatmap"""
        gaze_data = self.session_data.get('gaze_points', [])
        if not gaze_data:
            ax.text(0.5, 0.5, 'No gaze data available', 
                   transform=ax.transAxes, ha='center', va='center')
            return
        
        # Extract coordinates
        x_coords = [point['x'] for point in gaze_data]
        y_coords = [point['y'] for point in gaze_data]
        
        # Create 2D histogram for heatmap
        hist, xedges, yedges = np.histogram2d(x_coords, y_coords, bins=50)
        
        # Plot heatmap
        im = ax.imshow(hist.T, origin='lower', 
                      extent=[min(x_coords), max(x_coords), min(y_coords), max(y_coords)],
                      cmap='hot', alpha=0.8)
        
        # Add scatter points for individual gaze points
        ax.scatter(x_coords[::10], y_coords[::10], 
                  s=1, c='white', alpha=0.3, label='Gaze Points')
        
        ax.set_xlabel('X Position (pixels)')
        ax.set_ylabel('Y Position (pixels)')
        ax.set_title('Gaze Heatmap')
        
        # Add colorbar
        try:
            plt.colorbar(im, ax=ax, label='Gaze Density')
        except:
            pass  # Skip if colorbar fails
    
    def plot_combined_timeline(self, ax):
        """Plot combined timeline with emotions and game events"""
        # Get data
        emotions_data = self.session_data.get('emotions', [])
        game_events = self.session_data.get('game_events', [])
        
        if not emotions_data and not game_events:
            ax.text(0.5, 0.5, 'No timeline data available', 
                   transform=ax.transAxes, ha='center', va='center')
            return
        
        # Plot dominant emotion over time
        if emotions_data:
            df = pd.DataFrame(emotions_data)
            emotion_columns = ['anger', 'disgust', 'fear', 'happiness', 'sadness', 'surprise']
            
            # Calculate dominant emotion for each timepoint
            dominant_emotions = []
            for _, row in df.iterrows():
                emotion_values = {col: row.get(col, 0) for col in emotion_columns if col in row}
                if emotion_values:
                    dominant = max(emotion_values, key=emotion_values.get)
                    dominant_emotions.append((row['timestamp'], dominant, emotion_values[dominant]))
                else:
                    dominant_emotions.append((row['timestamp'], 'neutral', 0))
            
            if dominant_emotions:
                timestamps, emotions, intensities = zip(*dominant_emotions)
                
                # Create colored timeline
                for i, (t, emotion, intensity) in enumerate(dominant_emotions):
                    color = self.emotion_colors.get(emotion, '#6b7280')
                    ax.scatter(t, 0.5, c=color, s=intensity*100, alpha=0.6)
        
        # Add game events
        event_y_positions = {'score_update': 0.8, 'difficulty_change': 0.9, 
                           'target_hit': 0.7, 'game_start': 1.0, 'game_end': 1.0}
        
        for event in game_events:
            y_pos = event_y_positions.get(event['type'], 0.6)
            ax.scatter(event['timestamp'], y_pos, 
                      marker='|', s=100, c='red', alpha=0.8)
            
            # Add text for important events
            if event['type'] in ['game_start', 'game_end', 'difficulty_change']:
                ax.annotate(event['type'], 
                           (event['timestamp'], y_pos),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=8, alpha=0.7)
        
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('Event Level')
        ax.set_title('Combined Timeline: Emotions & Game Events')
        ax.set_ylim(0, 1.1)
        ax.grid(True, alpha=0.3)
    
    def plot_attention_heatmap(self, ax):
        """Plot attention heatmap with game context"""
        gaze_data = self.session_data.get('gaze_points', [])
        game_events = self.session_data.get('game_events', [])
        
        if not gaze_data:
            ax.text(0.5, 0.5, 'No attention data available', 
                   transform=ax.transAxes, ha='center', va='center')
            return
        
        # Create attention regions based on gaze density
        x_coords = [point['x'] for point in gaze_data]
        y_coords = [point['y'] for point in gaze_data]
        
        # Calculate attention statistics
        attention_stats = {
            'center_x': np.mean(x_coords),
            'center_y': np.mean(y_coords),
            'spread_x': np.std(x_coords),
            'spread_y': np.std(y_coords),
            'total_points': len(gaze_data)
        }
        
        # Create visualization
        ax.scatter(x_coords, y_coords, alpha=0.3, s=10, c='blue')
        
        # Add attention center
        ax.scatter(attention_stats['center_x'], attention_stats['center_y'], 
                  s=200, c='red', marker='x', linewidth=3, label='Attention Center')
        
        # Add spread ellipse
        ellipse = patches.Ellipse(
            (attention_stats['center_x'], attention_stats['center_y']),
            attention_stats['spread_x'] * 2,
            attention_stats['spread_y'] * 2,
            fill=False, edgecolor='red', linewidth=2, alpha=0.5,
            label='Attention Spread'
        )
        ax.add_patch(ellipse)
        
        ax.set_xlabel('X Position')
        ax.set_ylabel('Y Position')
        ax.set_title(f'Attention Analysis ({len(gaze_data)} points)')
        ax.legend()
        
        # Add stats text
        stats_text = f"""Attention Stats:
Center: ({attention_stats['center_x']:.0f}, {attention_stats['center_y']:.0f})
Spread: ({attention_stats['spread_x']:.0f}, {attention_stats['spread_y']:.0f})
Points: {attention_stats['total_points']}"""
        
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
               verticalalignment='top', fontsize=8, 
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    def add_game_events_to_plot(self, ax):
        """Add game events as vertical lines to any plot"""
        game_events = self.session_data.get('game_events', [])
        
        event_colors = {
            'game_start': 'green',
            'game_end': 'red',
            'difficulty_change': 'orange',
            'score_update': 'blue',
            'target_hit': 'purple'
        }
        
        for event in game_events:
            color = event_colors.get(event['type'], 'gray')
            ax.axvline(x=event['timestamp'], color=color, alpha=0.5, linestyle='--')
    
    def create_emotion_distribution_plot(self, ax):
        """Create emotion distribution plot"""
        emotions_data = self.session_data.get('emotions', [])
        if not emotions_data:
            ax.text(0.5, 0.5, 'No emotion data available', 
                   transform=ax.transAxes, ha='center', va='center')
            return
        
        df = pd.DataFrame(emotions_data)
        emotion_columns = ['anger', 'disgust', 'fear', 'happiness', 'sadness', 'surprise', 'neutral']
        
        # Calculate mean values for each emotion
        mean_emotions = {}
        for emotion in emotion_columns:
            if emotion in df.columns:
                mean_emotions[emotion] = df[emotion].mean()
        
        if mean_emotions:
            emotions = list(mean_emotions.keys())
            values = list(mean_emotions.values())
            colors = [self.emotion_colors.get(e, '#6b7280') for e in emotions]
            
            bars = ax.bar(emotions, values, color=colors, alpha=0.8)
            ax.set_xlabel('Emotions')
            ax.set_ylabel('Average Intensity')
            ax.set_title('Emotion Distribution')
            ax.tick_params(axis='x', rotation=45)
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f'{value:.2f}', ha='center', va='bottom', fontsize=8)
    
    def create_comprehensive_report(self, save_path: str = None):
        """Create a comprehensive analysis report"""
        fig = plt.figure(figsize=(16, 12))
        
        # Create subplot layout
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Main timeline (spans top row)
        ax_timeline = fig.add_subplot(gs[0, :])
        self.plot_emotions_timeline(ax_timeline)
        
        # Second row
        ax_gaze = fig.add_subplot(gs[1, 0])
        self.plot_gaze_heatmap(ax_gaze)
        
        ax_distribution = fig.add_subplot(gs[1, 1])
        self.create_emotion_distribution_plot(ax_distribution)
        
        ax_combined = fig.add_subplot(gs[1, 2])
        self.plot_combined_timeline(ax_combined)
        
        # Third row
        ax_attention = fig.add_subplot(gs[2, :2])
        self.plot_attention_heatmap(ax_attention)
        
        # Session summary (text)
        ax_summary = fig.add_subplot(gs[2, 2])
        ax_summary.axis('off')
        
        # Add summary statistics
        summary_text = self.generate_summary_text()
        ax_summary.text(0.1, 0.9, summary_text, transform=ax_summary.transAxes,
                       verticalalignment='top', fontsize=10,
                       bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
        
        plt.suptitle('FaceIt Analysis Report', fontsize=20, fontweight='bold')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Report saved to {save_path}")
        
        return fig
    
    def generate_summary_text(self) -> str:
        """Generate summary text for the report"""
        session_info = self.session_data.get('session_info', {})
        emotions_data = self.session_data.get('emotions', [])
        gaze_data = self.session_data.get('gaze_points', [])
        game_events = self.session_data.get('game_events', [])
        
        # Calculate basic statistics
        duration = session_info.get('duration', 0)
        
        dominant_emotion = 'Unknown'
        if emotions_data:
            df = pd.DataFrame(emotions_data)
            emotion_columns = ['anger', 'disgust', 'fear', 'happiness', 'sadness', 'surprise']
            emotion_means = {col: df[col].mean() for col in emotion_columns if col in df.columns}
            if emotion_means:
                dominant_emotion = max(emotion_means, key=emotion_means.get)
        
        summary = f"""SESSION SUMMARY
        
Duration: {duration:.1f}s
Frames: {len(emotions_data)}
Gaze Points: {len(gaze_data)}
Game Events: {len(game_events)}

Dominant Emotion: {dominant_emotion.capitalize()}

Game Performance:
"""
        
        # Add game-specific stats
        score_events = [e for e in game_events if 'score' in e.get('data', {})]
        if score_events:
            final_score = score_events[-1]['data']['score']
            summary += f"Final Score: {final_score}\n"
        
        level_events = [e for e in game_events if e['type'] == 'difficulty_change']
        if level_events:
            max_level = max(e['data']['to'] for e in level_events)
            summary += f"Max Level: {max_level}\n"
        
        return summary