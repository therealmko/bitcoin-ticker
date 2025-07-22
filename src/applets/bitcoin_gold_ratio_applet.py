from screen_manager import ScreenManager
from system_applets.base_applet import BaseApplet
from data_manager import DataManager
from micropython import const
import gc
import ujson as json
import os
import uerrno

class bitcoin_gold_ratio_applet(BaseApplet):
    """
    Displays Bitcoin to Gold price ratio:
    - Current BTC price in USD
    - Current Gold price per oz in USD
    - The ratio between them (BTC/Gold)
    """
    TTL = const(300)  # 5 minutes, gold price updates less frequently

    def __init__(self, screen_manager: ScreenManager, data_manager: DataManager):
        super().__init__('bitcoin_gold_ratio_applet', screen_manager)
        self.data_manager = data_manager
        self.btc_api_url = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
        self.gold_api_url = "https://api.gold-api.com/price/XAU"
        self.current_price_data = None
        self.gold_price_data = None
        self.register()

    def start(self):
        self.current_price_data = None
        self.gold_price_data = None
        self._load_gold_data()
        super().start()

    def _load_gold_data(self):
        """Load gold price data from the JSON file."""
        try:
            with open("gold.json", "r") as f:
                self.gold_price_data = json.load(f)
        except OSError as e:
            if e.args[0] == uerrno.ENOENT:
                print("[bitcoin_gold_ratio_applet] gold.json not found.")
            else:
                print(f"[bitcoin_gold_ratio_applet] Error loading gold.json: {e}")
            self.gold_price_data = None
        except Exception as e:
            print(f"[bitcoin_gold_ratio_applet] Error reading gold data: {e}")
            self.gold_price_data = None

    def register(self):
        self.data_manager.register_endpoint(self.btc_api_url, self.TTL)
        self.data_manager.register_endpoint(self.gold_api_url, self.TTL)

    async def update(self):
        self.current_price_data = self.data_manager.get_cached_data(self.btc_api_url)
        new_gold_data = self.data_manager.get_cached_data(self.gold_api_url)
        if new_gold_data:
            self.gold_price_data = new_gold_data
        gc.collect()

    async def draw(self):
        self.screen_manager.clear()
        self.screen_manager.draw_header("Bitcoin/Gold Ratio")

        if self.current_price_data is None:
            self.screen_manager.draw_centered_text("Loading BTC Price...")
            return

        if self.gold_price_data is None:
            self.screen_manager.draw_centered_text("Loading Gold Price...")
            return

        try:
            # Get BTC price directly from Binance response (no nested 'data' field)
            btc_price = float(self.current_price_data.get('lastPrice', 0))

            # Get Gold price from our cached data
            gold_price = float(self.gold_price_data.get('price', 0))

            if btc_price > 0 and gold_price > 0:
                ratio = btc_price / gold_price
                
                # Display BTC/Gold ratio
                self.screen_manager.draw_centered_text("BTC/GOLD", scale=3, y_offset=-60)
                self.screen_manager.draw_centered_text(f"{ratio:.2f}x", y_offset=-10)
                
                # Display individual prices
                btc_text = f"BTC: ${int(btc_price):,}"
                gold_text = f"Gold: ${int(gold_price):,}/oz"
                
                self.screen_manager.draw_centered_text(btc_text, scale=2, y_offset=30)
                self.screen_manager.draw_centered_text(gold_text, scale=2, y_offset=60)

            else:
                self.screen_manager.draw_centered_text("Invalid Price Data")

        except (ValueError, TypeError, KeyError) as e:
            print(f"[bitcoin_gold_ratio_applet] Error: {e}")
            self.screen_manager.draw_centered_text("Data Error")

        # Use timestamp from BTC price data for footer
        self.screen_manager.draw_footer(self.current_price_data.get('timestamp', None))
        gc.collect()
