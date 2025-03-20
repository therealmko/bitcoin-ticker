import screen_manager
from system_applets.base_applet import BaseApplet
from wifi_manager import WiFiManager
import wifi_manager

class ApApplet(BaseApplet):
    def __init__(self, screen_manager: screen_manager.ScreenManager,wifi_manager: WiFiManager):
        super().__init__("ApApplet", screen_manager)
        self.screen_manager = screen_manager
        self.wifi_manager = wifi_manager


    def start(self):
        print("AP Applet: Starting")

    def stop(self):
        print("AP Applet: Stopping")

    async def update(self):
        print("AP Applet: Updating")
        if self.wifi_manager and self.wifi_manager.is_connected():
            return True
        return False

    async def draw(self):
        print("AP Applet: drawing")
        self.screen_manager.clear()
        self.screen_manager.draw_header('SETUP')
        self.screen_manager.draw_text(f"SSID: {self.wifi_manager.get_ap_ssid()}\nPassword: havefunstayingpoor\n\nAfter connecting to the AP,\nscan the QR code to access \nthe web interface.\n192.168.4.1", 10, 40, scale=2)

        # self.screen_manager.draw_text("After connecting to the AP,\nscan the QR code to access \nthe web interface\n 192.168.4.1", 10, 80, scale=2)
        self.screen_manager.draw_image("data:image/jpeg;base64,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", 10, self.screen_manager.height-84-10 )
