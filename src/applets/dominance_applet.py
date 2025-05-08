from screen_manager import ScreenManager
from system_applets.base_applet import BaseApplet
from data_manager import DataManager
from micropython import const
import gc

class dominance_applet(BaseApplet):
    """
    Displays the Bitcoin Dominance percentage (BTC.D).
    Data from: https://api.coingecko.com/api/v3/global
    """
    TTL = const(600)  # 10 minutes
    API_URL = "https://api.coingecko.com/api/v3/global"

    def __init__(self, screen_manager: ScreenManager, data_manager: DataManager):
        super().__init__('dominance_applet', screen_manager)
        self.data_manager = data_manager
        self.current_data = None
        self.register()

    def register(self):
        self.data_manager.register_endpoint(self.API_URL, self.TTL)

    def start(self):
        self.current_data = None
        super().start()

    def stop(self):
        super().stop()

    async def update(self):
        self.current_data = self.data_manager.get_cached_data(self.API_URL)
        gc.collect()

    async def draw(self):
        self.screen_manager.clear()
        self.screen_manager.draw_header("Bitcoin Dominance")

        timestamp = None
        if isinstance(self.current_data, dict):
            # CoinGecko's global data has 'updated_at' at the top level of the 'data' object
            api_response_data = self.current_data.get('data', {})
            if isinstance(api_response_data, dict):
                timestamp = api_response_data.get("updated_at")
        self.screen_manager.draw_footer(timestamp)

        if self.current_data is None:
            self.screen_manager.draw_centered_text("Loading...")
            gc.collect()
            return

        api_response_data = self.current_data.get('data', {})
        if not isinstance(api_response_data, dict):
            print(f"[dominance_applet] API Error or unexpected data format: {api_response_data}")
            self.screen_manager.draw_centered_text("API Error")
            gc.collect()
            return

        # Extract dominance data
        # Path: data -> market_cap_percentage -> btc
        market_cap_percentage_data = api_response_data.get('market_cap_percentage', {})
        if not isinstance(market_cap_percentage_data, dict):
            self.screen_manager.draw_centered_text("Data Error")
            print(f"[dominance_applet] market_cap_percentage not found or not a dict.")
            gc.collect()
            return
            
        btc_dominance = market_cap_percentage_data.get('btc')

        if btc_dominance is None:
            self.screen_manager.draw_centered_text("No Data")
            print(f"[dominance_applet] btc_dominance value not found.")
            gc.collect()
            return

        try:
            dominance_value = float(btc_dominance)
            
            # Display Title "BTC.D"
            self.screen_manager.draw_centered_text("BTC.D", scale=3, y_offset=-60)
            
            # Display Dominance Percentage
            # Using y_offset=-10 to match ATH applet's main value position
            self.screen_manager.draw_centered_text(f"{dominance_value:.2f}%", y_offset=-10)

        except (ValueError, TypeError) as e:
            print(f"[dominance_applet] Error converting dominance value: {e}")
            self.screen_manager.draw_centered_text("Data Error")

        gc.collect()
