from system_applets.base_applet import BaseApplet
from data_manager import DataManager
from micropython import const
import gc

class block_height_applet(BaseApplet):
    TTL = const(120)

    def __init__(self, screen_manager, data_manager: DataManager):
        super().__init__('block_height_applet', screen_manager)
        self.data_manager = data_manager
        self.api_url = "https://mempool.space/api/v1/blocks/tip/height"
        self.current_data = None # Renamed from cached_data for clarity
        # self.drawn flag removed
        self.register()

    def start(self):
        # Reset data when applet starts to ensure fresh fetch
        self.current_data = None
        super().start()

    def stop(self):
        # No need to clear data here, start() handles it.
        super().stop()
        # self.drawn flag removed

    def register(self):
        self.data_manager.register_endpoint(self.api_url, self.TTL)

    async def update(self):
        # Fetch the latest data from cache on each update cycle
        self.current_data = self.data_manager.get_cached_data(self.api_url)
        gc.collect()
        # No need to call super().update() as it does nothing by default

    async def draw(self):
        # Removed self.drawn check - draw every time update() is called by manager
        self.screen_manager.clear()
        self.screen_manager.draw_header("Bitcoin Block Height")

        # Use the data fetched in update()
        if self.current_data is None:
            # Optionally display a loading or error message
            self.screen_manager.draw_centered_text("Loading...")
            # No footer yet if no data
        else:
            self.screen_manager.draw_footer(self.current_data.get('timestamp', None))
            height = self.current_data.get('data')
            if height is not None:
                try:
                    # Format with commas
                    self.screen_manager.draw_centered_text(f"{int(height):,}")
                except (ValueError, TypeError):
                    self.screen_manager.draw_centered_text("Error") # Handle potential conversion errors
            else:
                self.screen_manager.draw_centered_text("N/A") # Handle missing height data

        # screen_manager.update() is called by AppletManager after draw()
        # self.drawn = True removed

        gc.collect()
