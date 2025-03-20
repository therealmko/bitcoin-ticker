import applet_manager
import uasyncio as asyncio
from pimoroni import RGBLED

from screen_manager import ScreenManager
from data_manager import DataManager
from wifi_manager import WiFiManager
from web_server import AsyncWebServer
from applet_manager import AppletManager
from system_applets import ap_applet

RGBLED(6, 7, 8).set_rgb(0, 0, 0)

async def main() -> None:
    """
    Main entry point for the application.
    Initializes managers (screen, data, Wi-Fi), launches the appropriate applets,
    and starts the web server. It keeps an asynchronous loop alive to service
    other tasks such as applets and data retrieval.
    """
    screen_manager = ScreenManager()
    data_manager = DataManager()
    wifi_manager = WiFiManager()

    applet_manager_instance = AppletManager(screen_manager, data_manager, wifi_manager)
    splash_applet = applet_manager.SplashApplet(screen_manager)
    print("[Main] Starting splash applet.")
    await applet_manager_instance.run_applet_once(splash_applet)

     # Attempt to connect to known Wi-Fi networks
    if wifi_manager.connect_to_saved_networks():
        print("[Main] Connected to a known Wi-Fi network.")
        asyncio.create_task(applet_manager_instance.start_applets())
    else:
        print("[Main] No saved networks found or unable to connect. Setting up AP mode.")
        wifi_manager.setup_ap()
        ap_mode_applet = ap_applet.ApApplet(screen_manager, wifi_manager)
        asyncio.create_task(applet_manager_instance._run_applet(ap_mode_applet, is_system_applet=True))

    web_server = AsyncWebServer(wifi_manager, applet_manager_instance)
    asyncio.create_task(web_server.start_web_server())

    # Keep the main event loop alive
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
