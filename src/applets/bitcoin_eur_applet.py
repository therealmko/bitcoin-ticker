from screen_manager import ScreenManager
from system_applets.base_applet import BaseApplet
from data_manager import DataManager
from micropython import const
import gc

class bitcoin_eur_applet(BaseApplet):
    TTL = const(120)

    def __init__(self, screen_manager: ScreenManager, data_manager: DataManager):
        super().__init__('bitcoin_eur_applet', screen_manager)
        self.data_manager = data_manager
        self.api_url = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCEUR"
        self.drawn = False
        #self.register()

    def start(self):
        super().start()
        self.register()

    def stop(self):
        super().stop()
        self.drawn = False

    def register(self):
        self.data_manager.register_endpoint(self.api_url)

    async def update(self):
        gc.collect()
        return await super().update()

    async def draw(self):
        if self.drawn:
            return

        self.screen_manager.clear()
        self.screen_manager.draw_header("Bitcoin Euro Price")
        self.data = self.data_manager.get_cached_data(self.api_url)

        print("Initial cached data:", self.data)

        if self.data is None:
            gc.collect()
            await self.data_manager._update_cache(self.api_url)
            self.data = self.data_manager.get_cached_data(self.api_url)
            if self.data is None:
                return

        if isinstance(self.data, dict):
            # Access the nested 'data' dictionary first
            bitcoin_data = self.data.get('data', {})

            # Now get the price from the nested data
            price = bitcoin_data.get('lastPrice')
            change_percent = bitcoin_data.get('priceChangePercent')

            if price:
                try:
                    eur_price = float(price)
                    change = float(change_percent)

                    # Draw the label, price and change
                    self.screen_manager.draw_centered_text("BTC/EUR", scale=3, y_offset=-60)  # Label above price
                    self.screen_manager.draw_centered_text(f"E{int(eur_price):,}")  # Price with default scale=8 and thousand separator
                    # Draw the change percentage
                    change_text = f"24h change: {change:+.2f}%"
                    text_width = self.screen_manager.display.measure_text(change_text, scale=2)
                    x = (self.screen_manager.width - text_width) // 2
                    y = (self.screen_manager.height - 16) // 2 + 60  # 16 is text height at scale 2

                    # Draw triangle before the text
                    triangle_size = 10
                    triangle_x = x - triangle_size - 5  # 5 pixels gap
                    triangle_y = y + 8  # Center vertically with text

                    # Set color based on change direction
                    triangle_color = self.screen_manager.theme["POSITIVE_COLOR"] if change >= 0 else self.screen_manager.theme["NEGATIVE_COLOR"]
                    self.screen_manager.display.set_pen(self.screen_manager.get_pen(triangle_color))

                    if change >= 0:
                        # Upward triangle
                        self.screen_manager.display.triangle(
                            triangle_x, triangle_y,
                            triangle_x + triangle_size, triangle_y,
                            triangle_x + (triangle_size // 2), triangle_y - triangle_size
                        )
                    else:
                        # Downward triangle
                        self.screen_manager.display.triangle(
                            triangle_x, triangle_y - triangle_size,
                            triangle_x + triangle_size, triangle_y - triangle_size,
                            triangle_x + (triangle_size // 2), triangle_y
                        )

                    # Draw the text
                    self.screen_manager.draw_text(change_text, x, y, scale=2)
                except ValueError as e:
                    print("Error converting values:", e)

        # Draw the timestamp from the outer dictionary
        self.screen_manager.draw_footer(self.data.get('timestamp', None))

        self.data = None
        self.screen_manager.update()
        self.drawn = True
        gc.collect()
