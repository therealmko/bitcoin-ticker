import json
import os

class ConfigManager:
    """
    Manages configuration settings for the Bitcoin Ticker application.
    Currently supports applet duration configuration.
    """
    
    def __init__(self):
        self.config = {}
        self.filename = "config.json"
        self.defaults = {
            "applet_duration": 10  # Default duration in seconds
        }
        self.load_config()
    
    def load_config(self):
        """Load configuration from file or create with defaults if it doesn't exist"""
        try:
            with open(self.filename, "r") as f:
                self.config = json.load(f)
                print(f"[ConfigManager] Loaded configuration from {self.filename}")
        except (OSError, ValueError):
            print(f"[ConfigManager] Failed to load configuration. Using defaults.")
            self.config = self.defaults.copy()
            self.save_config()
    
    def save_config(self):
        """Save current configuration to file"""
        with open(self.filename, "w") as f:
            json.dump(self.config, f)
            print(f"[ConfigManager] Saved configuration to {self.filename}")
    
    def get_applet_duration(self):
        """Get the current applet duration in seconds"""
        return self.config.get("applet_duration", self.defaults["applet_duration"])
    
    def set_applet_duration(self, duration):
        """
        Set and validate the applet duration
        
        :param duration: Duration in seconds (will be clamped between 3-60 seconds)
        :return: The actual duration that was set after validation
        """
        try:
            # Convert to integer and clamp between 3-60 seconds
            duration = int(duration)
            duration = max(3, min(60, duration))
            
            self.config["applet_duration"] = duration
            self.save_config()
            return duration
        except (ValueError, TypeError):
            # If conversion fails, return the current value
            return self.get_applet_duration()
