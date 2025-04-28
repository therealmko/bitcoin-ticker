import json
import os

class ConfigManager:
    """
    Manages configuration settings for the Bitcoin Ticker application.
    Currently supports applet duration and timezone offset configuration.
    """
    
    def __init__(self):
        self.config = {}
        self.filename = "config.json"
        self.defaults = {
            "applet_duration": 10,      # Default duration in seconds
            "timezone_offset": 0,       # Default timezone offset (UTC)
            "transition_effect": "None" # Default transition effect
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
    
    def get_timezone_offset(self):
        """Get the current timezone offset from UTC in hours"""
        return self.config.get("timezone_offset", self.defaults["timezone_offset"])
    
    def set_timezone_offset(self, offset):
        """
        Set and validate the timezone offset
        
        :param offset: Offset in hours from UTC (clamped between -12 and +14)
        :return: The actual offset that was set after validation
        """
        try:
            # Convert to integer and clamp between -12 and +14 hours
            # (Valid timezone ranges from UTC-12 to UTC+14)
            offset = int(offset)
            offset = max(-12, min(14, offset))
            
            self.config["timezone_offset"] = offset
            self.save_config()
            return offset
        except (ValueError, TypeError):
            # If conversion fails, return the current value
            return self.get_timezone_offset()

    def get_transition_effect(self):
        """Get the current transition effect name"""
        # Import locally to avoid circular dependency if transitions need config
        from transitions import AVAILABLE_TRANSITIONS
        effect = self.config.get("transition_effect", self.defaults["transition_effect"])
        # Ensure the stored effect is still valid
        if effect not in AVAILABLE_TRANSITIONS:
            print(f"[ConfigManager] Invalid transition '{effect}' found. Reverting to default.")
            return self.defaults["transition_effect"]
        return effect

    def set_transition_effect(self, effect_name):
        """
        Set and validate the transition effect.

        :param effect_name: The name of the transition effect (e.g., "None", "Fade")
        :return: The actual effect name that was set after validation
        """
        # Import locally to avoid circular dependency
        from transitions import AVAILABLE_TRANSITIONS
        if effect_name in AVAILABLE_TRANSITIONS:
            self.config["transition_effect"] = effect_name
            self.save_config()
            return effect_name
        else:
            print(f"[ConfigManager] Invalid transition effect '{effect_name}'. Not saving.")
            # Return the current valid value instead of saving an invalid one
            return self.get_transition_effect()
