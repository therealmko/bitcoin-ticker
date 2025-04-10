import gc
import os
from system_applets import base_applet
import uasyncio as asyncio
import json

from system_applets.splash_applet import SplashApplet
from system_applets.error_applet import ErrorApplet
from applets import (
    bitcoin_applet,
    bitcoin_eur_applet,
    block_height_applet,
    fee_applet,
    moscow_time_applet,
    halving_countdown_applet
)


class AppletManager:
    """
    Manages the lifecycle of different applets, including their initialization,
    updates, drawing on screen, and error handling.
    """

    def __init__(self, screen_manager, data_manager, wifi_manager) -> None:
        """
        Initialize the AppletManager with managers for screen, data, and Wi-Fi.

        :param screen_manager: Manages the physical or virtual display.
        :param data_manager:   Manages data fetching and distribution.
        :param wifi_manager:   Manages Wi-Fi connectivity (e.g., credentials, connection status).
        """
        self.screen_manager = screen_manager
        self.data_manager = data_manager
        self.wifi_manager = wifi_manager

        self.current_applet = None
        self.current_index = 0
        self.running = True

        self.next_applet_data = None

        self._register_applets()

    def _register_applets(self) -> None:
        """
        Instantiate and store the available applets.
        """

        self.all_applets = {
            "bitcoin_applet": bitcoin_applet.bitcoin_applet,
            "bitcoin_eur_applet": bitcoin_eur_applet.bitcoin_eur_applet,
            "block_height_applet": block_height_applet.mempool_applet,
            "fee_applet": fee_applet.fee_applet,
            "moscow_time_applet": moscow_time_applet.moscow_time_applet,
            "halving_countdown_applet": halving_countdown_applet.halving_countdown_applet,
        }

        self.applets = self.load_applets()

    def update_applets(self, applets, filename="applets.json"):
        """
        Save the applets to a file.
        """
        with open(filename, "w") as f:
            data = []
            for applet in applets:
                # Add the valid applet to the data list
                data.append({
                    "name": applet["name"],
                    "enabled": applet["enabled"]
                })
            # Save the valid data to the file
            json.dump(data, f)

    def get_applets_list(self):
        """
        Return a list of applets with their names and enabled status.
        """
        applets = []
        for applet in self.applets:
            applets.append({
                "name": applet.__class__.__name__,
                "enabled": True
            })
        for applet_name in self.all_applets.keys():
            if applet_name not in [applet["name"] for applet in applets]:
                applets.append({
                    "name": applet_name,
                    "enabled": False
                })
        return applets

    def load_applets(self, filename="applets.json"):
        """
        Load or create a simple list of applets with 'name' and 'enabled' keys,
        then instantiate them. Missing default applets from self.all_applets
        are added automatically.
        """
        try:
            with open(filename, "r") as f:
                data = json.load(f)  # Expecting a list of { "name": str, "enabled": bool }
                print(f"[AppletManager] Loaded applets from {filename}")
        except OSError:
            print(f"[AppletManager] Failed to load applets from {filename}. Starting with defaults.")
            data = []
            for applet_name in self.all_applets.keys():
                data.append({"name": applet_name, "enabled": True})
            self.update_applets(data)
        except (ValueError):
            print(f"[AppletManager] Failed to load applets from {filename}. Starting with defaults.")
            data = []
            for applet_name in self.all_applets.keys():
                data.append({"name": applet_name, "enabled": True})
            self.update_applets(data)

        # Init enabled applets
        applets = []
        for applet in data:
            if not applet.get('enabled', False):
                continue
            applet_name = applet.get('name')
            if not applet_name:
                print(f"[AppletManager] Invalid applet entry: {applet}")
                continue
            applet_class = self.all_applets.get(applet_name)
            if not applet_class:
                print(f"[AppletManager] Applet not found: {applet_name}")
                continue
            applets.append(applet_class(self.screen_manager, self.data_manager))
        return applets



    def _get_applet_class(self, name):
        """
        Map applet names to their respective classes.
        This allows applets to be instantiated dynamically based on their name.
        """
        return self.all_applets.get(name)


    async def start_applets(self) -> None:
        """
        Entry point to start the applets in a continuous loop.
        This method is typically called once after system initialization.
        """
        enabled_applets = self.applets

        if not enabled_applets:
            print("[AppletManager] No applets registered. Displaying error.")
            await self._display_error("No applets registered or enabled.")
            return

        asyncio.create_task(self.data_manager.run())

        while self.running:
            current_applet = enabled_applets[self.current_index]
            await self._run_applet(current_applet)
            # Advance to the next applet
            self.current_index = (self.current_index + 1) % len(enabled_applets)

    async def _run_applet(self, applet, is_system_applet: bool = False) -> None:
        """
        Core method to run a single applet in a loop until it requests an advance or an error occurs.

        :param applet:           The applet to run.
        :param is_system_applet: If True, the applet is a system applet like Splash or Error.
        """
        gc.collect()
        print(f"[AppletManager] Starting applet: {applet.__class__.__name__}")

        if self.current_applet:
            self.current_applet.stop()

        self.screen_manager.clear()
        self.current_applet = applet
        self.current_applet.start()

        self.running = True
        try:
            while self.running:
                should_advance = await self.current_applet.update()
                await self.current_applet.draw()
                self.screen_manager.update()

                if should_advance and not is_system_applet:
                    await self._advance_to_next_applet()
                    break

                await asyncio.sleep(10)

        except Exception as e:
            await self._handle_exception(e)

        finally:
            gc.collect()

    async def run_applet_once(self, applet) -> None:
        """
        Run a single applet once 
        """
        gc.collect()
        print(f"[AppletManager] Starting applet: {applet.__class__.__name__}")
        if self.current_applet:
            self.current_applet.stop()
        try:
            self.screen_manager.clear()
            self.current_applet = applet
            self.current_applet.start()
            await self.current_applet.draw()
            self.screen_manager.update()
        except Exception as e:
            await self._handle_exception(e)
        finally:
            gc.collect()

    async def _advance_to_next_applet(self) -> None:
        """
        Advances to the next applet in the sequence, wrapping around if needed.
        """
        if not self.applets:
            print("[AppletManager] No applets to advance to.")
            return

        self.current_index = (self.current_index + 1) % len(self.applets)

        # Pass any preloaded data to the next applet
        next_applet = self.applets[self.current_index]
        if self.next_applet_data:
            next_applet.set_preloaded_data(self.next_applet_data)
            self.next_applet_data = None

        print(f"[AppletManager] Advancing to applet: {next_applet.__class__.__name__}")

    async def _display_error(self, message: str) -> None:
        """
        Display an error applet with the provided message.

        :param message: The error message to display.
        """
        error_applet = ErrorApplet(self.screen_manager, message)
        await self._run_applet(error_applet, is_system_applet=True)

    async def _handle_exception(self, exception: Exception) -> None:
        """
        Handle exceptions by displaying an error applet, stopping the current loop,
        and preventing further updates to the crashed applet.

        :param exception: The caught exception.
        """
        print(f"[AppletManager] Exception occurred: {exception}")
        if self.current_applet:
            self.current_applet.stop()

        error_message = str(exception)
        error_applet = ErrorApplet(self.screen_manager, error_message)

        # Switch to error applet
        await self._run_applet(error_applet, is_system_applet=True)

        # Stop the main loop to avoid repeated crashes
        self.running = False
