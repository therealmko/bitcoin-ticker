from system_applets.base_applet import BaseApplet
from data_manager import DataManager
from micropython import const
import gc

class moscow_time_applet(BaseApplet):
    TTL = const(120)

    def __init__(self, screen_manager, data_manager: DataManager):
        super().__init__('moscow_time_applet', screen_manager)
        self.data_manager = data_manager
        self.api_url = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
        self.drawn = False
        self.register()

    def start(self):
        super().start()

    def stop(self):
        super().stop()
        self.drawn = False

    def register(self):
        self.data_manager.register_endpoint(self.api_url, self.TTL)

    async def update(self):
        gc.collect()
        return await super().update()

    async def draw(self):
        if self.drawn:
            return

        self.screen_manager.clear()
        self.screen_manager.draw_header("Moscow Time")
        self.data = self.data_manager.get_cached_data(self.api_url)

        if self.data is None:
            gc.collect()
            await self.data_manager._update_cache(self.api_url)
            self.data = self.data_manager.get_cached_data(self.api_url)
            if self.data is None:
                return

        if isinstance(self.data, dict):
            bitcoin_data = self.data.get('data', {})
            price = bitcoin_data.get('lastPrice')

            if price:
                try:
                    btc_price = float(price)
                    if btc_price != 0:  # Check to prevent divide by zero
                        # Calculate Moscow Time (sats per dollar)
                        moscow_time = int(100_000_000 / btc_price)

                        # Format as clock display
                        if moscow_time < 1000:
                            display_time = f"0{moscow_time//100}:{moscow_time%100:02d}"
                        else:
                            display_time = f"{moscow_time//100}:{moscow_time%100:02d}"

                        self.screen_manager.draw_centered_text(display_time, scale=12)
                    else:
                        print("BTC price is zero, cannot calculate Moscow Time.")
                except ValueError as e:
                    print("Error converting values:", e)

        self.screen_manager.draw_footer(self.data.get('timestamp', None))
        self.data = None
        self.screen_manager.update()
        self.drawn = True
        gc.collect()
