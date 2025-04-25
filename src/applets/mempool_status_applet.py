from system_applets.base_applet import BaseApplet
from data_manager import DataManager
from micropython import const
import gc

class mempool_status_applet(BaseApplet):
    TTL = const(60)

    def __init__(self, screen_manager, data_manager: DataManager):
        super().__init__('mempool_status_applet', screen_manager)
        self.data_manager = data_manager
        self.api_url = "https://mempool.space/api/mempool"
        self.current_data = None # Store data fetched in update()
        self.previous_vsize = None # Store vsize from the previous update
        self.register()

    def start(self):
        # Reset data when applet starts
        self.current_data = None
        super().start()

    def stop(self):
        # No need for drawn flag handling
        super().stop()

    def register(self):
        self.data_manager.register_endpoint(self.api_url, self.TTL)

    async def update(self):
        # Store previous vsize if current_data exists
        if self.current_data and isinstance(self.current_data.get('data'), dict):
            try:
                self.previous_vsize = int(self.current_data['data'].get("vsize", 0))
            except (ValueError, TypeError):
                self.previous_vsize = None # Reset if previous data was bad

        # Fetch new data
        self.current_data = self.data_manager.get_cached_data(self.api_url)
        gc.collect()
        # No need to call super().update()

    async def draw(self):
        # Draw uses data fetched by update()
        self.screen_manager.clear()
        self.screen_manager.draw_header("Bitcoin Mempool Size")

        if self.current_data is None:
            self.screen_manager.draw_centered_text("Loading...")
            # No footer if no data
            gc.collect()
            return

        # Draw timestamp from the outer cache dictionary
        self.screen_manager.draw_footer(self.current_data.get('timestamp', None))

        # Access the nested 'data' dictionary which holds the actual API response
        mempool_data = self.current_data.get('data', {})
        if not isinstance(mempool_data, dict):
            print(f"[mempool_status_applet] Unexpected data format: {mempool_data}")
            self.screen_manager.draw_centered_text("Data Error")
            gc.collect()
            return

        try:
            count = int(mempool_data.get("count", 0))
            vsize = int(mempool_data.get("vsize", 0))  # in vbytes

            size_mb = vsize / 1_000_000.0 # Calculate MB
            size_str = f"{size_mb:.2f} MB"
            tx_count_str = f"{count:,} TXs"

            # --- Removed Traffic Light ---
            # if size_mb < 2.0:
            #     congestion_level = "low"
            # elif size_mb < 10.0:
            #     congestion_level = "medium"
            # else:
            #     congestion_level = "high"
            # self.screen_manager.draw_traffic_light(congestion_level)

            # --- Draw Main Size ---
            # Removed small header text
            # self.screen_manager.draw_horizontal_centered_text("Mempool Size (MB)", y=60, scale=2)
            self.screen_manager.draw_centered_text(size_str, scale=6, y_offset=-10) # Shifted up slightly

            # --- Draw Change Indicator ---
            change_text = "Change: N/A"
            change_percent = 0.0
            valid_change = False
            if self.previous_vsize is not None and self.previous_vsize > 0:
                try:
                    change_percent = ((vsize - self.previous_vsize) / self.previous_vsize) * 100.0
                    change_text = f"Change: {change_percent:+.1f}%"
                    valid_change = True
                except Exception as e_calc:
                    print(f"[mempool_status_applet] Error calculating change: {e_calc}")
                    change_text = "Change: Error"

            # Calculate position for change text (below main size)
            text_width = self.screen_manager.display.measure_text(change_text, scale=2)
            x = (self.screen_manager.width - text_width) // 2
            y = (self.screen_manager.height // 2) + 20 # Position below center

            if valid_change:
                # Draw triangle indicator if change is valid
                triangle_size = 10
                triangle_x = x - triangle_size - 5
                triangle_y = y + 8 # Approx vertical center

                # Increase is "bad" (red up arrow), Decrease is "good" (green down arrow)
                triangle_color_name = "NEGATIVE_COLOR" if change_percent >= 0 else "POSITIVE_COLOR"
                triangle_color = self.screen_manager.theme[triangle_color_name]
                self.screen_manager.display.set_pen(self.screen_manager.get_pen(triangle_color))

                if change_percent >= 0: # Upward triangle (Red)
                    self.screen_manager.display.triangle(
                        triangle_x, triangle_y,
                        triangle_x + triangle_size, triangle_y,
                        triangle_x + (triangle_size // 2), triangle_y - triangle_size
                    )
                else: # Downward triangle (Green)
                    self.screen_manager.display.triangle(
                        triangle_x, triangle_y - triangle_size,
                        triangle_x + triangle_size, triangle_y - triangle_size,
                        triangle_x + (triangle_size // 2), triangle_y
                    )

            # Draw the change text
            self.screen_manager.draw_text(change_text, x, y, scale=2)

            # --- Draw Transaction Count ---
            # Positioned further down
            self.screen_manager.draw_horizontal_centered_text(tx_count_str, y=self.screen_manager.height - 40, scale=2)

        except (ValueError, TypeError, KeyError) as e:
            print(f"[mempool_status_applet] Error parsing data: {e}")
            self.screen_manager.draw_centered_text("Data Error")

        # screen_manager.update() is called by AppletManager or transition
        # self.drawn flag removed
        gc.collect()
