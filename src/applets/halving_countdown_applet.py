from system_applets.base_applet import BaseApplet
from data_manager import DataManager
from micropython import const
import gc

class halving_countdown_applet(BaseApplet):
    TTL = const(120)
    BLOCKS_PER_HALVING = const(210_000)

    def __init__(self, screen_manager, data_manager: DataManager):
        super().__init__('halving_countdown_applet', screen_manager)
        self.data_manager = data_manager
        self.api_url = "https://mempool.space/api/blocks/tip/height"
        self.current_data = None
        # self.drawn flag removed
        self.register()

    def start(self):
        # Reset data when applet starts
        self.current_data = None
        super().start()

    def stop(self):
        super().stop()
        # self.drawn flag removed

    def register(self):
        self.data_manager.register_endpoint(self.api_url, self.TTL)

    def calculate_next_halving(self, current_height):
        # Calculate how many halvings have occurred
        halvings_occurred = current_height // self.BLOCKS_PER_HALVING
        # Calculate next halving block height
        next_halving_height = (halvings_occurred + 1) * self.BLOCKS_PER_HALVING
        # Calculate blocks remaining
        blocks_remaining = next_halving_height - current_height
        return blocks_remaining

    async def update(self):
        # Fetch the latest data from cache on each update cycle
        self.current_data = self.data_manager.get_cached_data(self.api_url)
        gc.collect()
        # No need to call super().update()

    async def draw(self):
        # Removed self.drawn check
        self.screen_manager.clear()
        self.screen_manager.draw_header("Bitcoin Halving Countdown")

        # Use the data fetched in update()
        if self.current_data is None:
            self.screen_manager.draw_centered_text("Loading...")
            # No footer yet
        else:
            self.screen_manager.draw_footer(self.current_data.get('timestamp', None))
            try:
                current_height = int(self.current_data.get('data', 0))
                if current_height > 0:
                    blocks_remaining = self.calculate_next_halving(current_height)
                    self.screen_manager.draw_centered_text(f"{blocks_remaining:,}")
                else:
                    self.screen_manager.draw_centered_text("N/A") # Handle case where height is 0 or missing
            except (ValueError, TypeError) as e:
                print("Error processing block height:", e)
                self.screen_manager.draw_centered_text("Error") # Display error on screen

        # screen_manager.update() is called by AppletManager
        # self.drawn = True removed
        gc.collect()
