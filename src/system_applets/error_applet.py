from system_applets.base_applet import BaseApplet

class ErrorApplet(BaseApplet):
    def __init__(self, screen_manager, error_message="An error occurred"):
        self.screen_manager = screen_manager
        self.error_message = error_message

    def start(self):
        print("Error Applet: Starting")

    def stop(self):
        print("Error Applet: Stopping")

    async def update(self):
        print("Error Applet: Updating")
        return False

    async def draw(self):
        print("Error Applet: Drawing")
        self.screen_manager.clear()
        self.screen_manager.draw_text("Error!", 0, 0)
        self.screen_manager.draw_text(self.error_message, 0, 20)
        self.screen_manager.update()
