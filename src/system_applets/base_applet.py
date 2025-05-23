from screen_manager import ScreenManager


class BaseApplet:
    def __init__(self, applet_name, screen_manager, config_manager=None, ticks_on_screen=5):
        self.screen_manager: ScreenManager = screen_manager
        self.config_manager = config_manager
        self.data_manager = None
        self.ticks_on_screen = ticks_on_screen
        self.ticks = 0
        self.data = None
        self.should_advance = False
        self.applet_name = applet_name
        self.needs_redraw = True # Add needs_redraw flag

    def getName(self)->str:
        return self.applet_name

    def register(self):
        """Registers the applet with the applet manager."""
        print(f"Registering applet {self.applet_name}")
        pass

    def start(self):
        """Called when the applet is started."""
        self.ticks = 0
        print(f"Starting applet {self.applet_name}")
        pass

    def stop(self):
        """Called when the applet is stopped."""
        self.screen_manager.clear()
        print(f"Stopping applet {self.applet_name}")
        pass

    async def update(self):
        """Called every frame to update the applet's state."""
        print(f"Ticks: {self.ticks}")
        self.ticks += 1
        return self.should_advance or self.ticks >= self.ticks_on_screen

    async def draw(self):
        """Called every frame to draw the applet's output."""
        if self.needs_redraw: # Check needs_redraw flag
            print(f"Drawing applet {self.applet_name}")
            # ... (drawing logic would go here)
            self.needs_redraw = False # Reset the flag
