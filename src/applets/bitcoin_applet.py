from screen_manager import ScreenManager
from system_applets.base_applet import BaseApplet
from data_manager import DataManager
from micropython import const
import gc

class bitcoin_applet(BaseApplet):
    TTL = const(61)

    def __init__(self, screen_manager: ScreenManager, data_manager: DataManager):
        super().__init__('bitcoin_applet', screen_manager)
        self.data_manager = data_manager
        self.api_url = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
        self.current_data = None # Store data fetched in update()
        self.register()

    def start(self):
        # Reset data when applet starts
        self.current_data = None
        super().start()

    def stop(self):
        # No need for drawn flag handling
        super().stop()

    def register(self):
        # Register with default TTL from BaseApplet if not specified otherwise
        self.data_manager.register_endpoint(self.api_url, self.TTL)

    async def update(self):
        # Fetch data in update
        self.current_data = self.data_manager.get_cached_data(self.api_url)
        # print(f"[bitcoin_applet] Updated data: {self.current_data}") # Optional debug
        # No need to call super().update()

    async def draw(self):
        # Draw uses data fetched by update()
        self.screen_manager.clear()
        self.screen_manager.draw_header("Bitcoin US Dollar Price")

        if self.current_data is None:
            self.screen_manager.draw_centered_text("Loading...")
            # No footer if no data
        elif isinstance(self.current_data, dict):
            # Draw timestamp from the outer cache dictionary
            self.screen_manager.draw_footer(self.current_data.get('timestamp', None))

            # Access the nested 'data' dictionary which holds the actual API response
            bitcoin_data = self.current_data.get('data', {})
            if not isinstance(bitcoin_data, dict):
                 # Handle cases where 'data' might not be a dict (e.g., error response)
                 print(f"[bitcoin_applet] Unexpected data format: {bitcoin_data}")
                 self.screen_manager.draw_centered_text("Data Error")
                 gc.collect()
                 return # Stop drawing if data format is wrong

            price = bitcoin_data.get('lastPrice')
