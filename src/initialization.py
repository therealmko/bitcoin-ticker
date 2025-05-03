import uasyncio as asyncio
import os
import ujson as json
import gc
import uerrno
# Use the project's request library
try:
    import urllib_urequest as urequests
except ImportError:
    import urequests # Fallback if the aliased version isn't found

from screen_manager import ScreenManager
from config import ConfigManager # Assuming config might be needed later

class Initializer:
    """
    Handles one-time initialization tasks after Wi-Fi connection.
    - Ensures applets.json exists.
    - Fetches and stores Bitcoin ATH data if not present.
    """
    ATH_API_URL = "https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false"
    APPLET_CONFIG_FILE = "applets.json"
    ATH_DATA_FILE = "bitcoin_ath.json"
    ATH_DUMP_FILE = "ath_dump.tmp" # Temporary file for raw API data

    def __init__(self, screen_manager: ScreenManager, config_manager: ConfigManager):
        self.screen_manager = screen_manager
        self.config_manager = config_manager # Keep for potential future use

    async def _show_initializing_screen(self, message="Initializing"):
        """Displays an initializing message on the screen."""
        self.screen_manager.clear()
        dots = ""
        for _ in range(3): # Simple animation loop
            self.screen_manager.draw_centered_text(f"{message}{dots}", scale=2)
            self.screen_manager.update()
            await asyncio.sleep_ms(300)
            dots += "."
            if len(dots) > 3:
                dots = ""
            self.screen_manager.clear() # Clear previous text for animation

        # Final message before proceeding
        self.screen_manager.draw_centered_text(f"{message}...", scale=2)
        self.screen_manager.update()
        await asyncio.sleep_ms(100) # Brief pause on final message

    def _file_exists(self, filename):
        """Check if a file exists."""
        try:
            os.stat(filename)
            return True
        except OSError as e:
            if e.args[0] == uerrno.ENOENT:
                return False
            else:
                print(f"[Initializer] Error checking file {filename}: {e}")
                return False # Treat other errors as non-existent for safety

    def _ensure_applets_json(self):
        """Creates a default applets.json if it doesn't exist."""
        if not self._file_exists(self.APPLET_CONFIG_FILE):
            print(f"[Initializer] {self.APPLET_CONFIG_FILE} not found. Creating default.")
            default_data = [{"name": "bitcoin_applet", "enabled": True}]
            try:
                with open(self.APPLET_CONFIG_FILE, "w") as f:
                    json.dump(default_data, f)
                print(f"[Initializer] Default {self.APPLET_CONFIG_FILE} created.")
            except Exception as e:
                print(f"[Initializer] ERROR: Failed to create default {self.APPLET_CONFIG_FILE}: {e}")
        else:
            print(f"[Initializer] {self.APPLET_CONFIG_FILE} found.")

    async def _fetch_and_process_ath(self):
        """Fetches ATH data, saves relevant parts to bitcoin_ath.json."""
        if self._file_exists(self.ATH_DATA_FILE):
            print(f"[Initializer] {self.ATH_DATA_FILE} found. Skipping ATH fetch.")
            return

        print(f"[Initializer] {self.ATH_DATA_FILE} not found. Fetching ATH data...")
        await self._show_initializing_screen("Fetching ATH")

        response = None
        try:
            # WARNING: This reads the entire response into memory.
            # If this causes MemoryError, a streaming approach is needed.
            print(f"[Initializer] Requesting data from {self.ATH_API_URL}")
            response_stream = urequests.urlopen(self.ATH_API_URL)
            gc.collect()

            # --- Assume success if urlopen doesn't raise exception ---
            # The stream directly contains the body for HTTPS in this environment
            body_stream = response_stream
            print("[Initializer] HTTPS request successful, proceeding to read body.")

            # --- Save Response Body ---
            print("[Initializer] Saving ATH response body to temporary file...")
            try:
                with open(self.ATH_DUMP_FILE, "wb") as f:
                    chunk_size = 512
                    while True:
                        chunk = body_stream.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        gc.collect() # Aggressive GC during write
                print(f"[Initializer] Saved response body to {self.ATH_DUMP_FILE}")
            except Exception as write_e:
                 print(f"[Initializer] Error writing response body: {write_e}")
                 await self._show_initializing_screen(f"ATH Write Err")
                 await asyncio.sleep(2)
                 # Still try to close stream and cleanup in finally
            finally:
                 if response_stream: # Close the original stream/socket object
                     response_stream.close()
                 response_stream = None # Ensure it's cleared
                 body_stream = None # Clear reference
                 gc.collect()

            # --- Memory-Efficient Parsing Attempt ---
            print(f"[Initializer] Parsing {self.ATH_DUMP_FILE} for ATH data...")
            await self._show_initializing_screen("Processing ATH")
            ath_usd = None
            ath_date_usd = None
            buffer = ""
            in_market_data = False
            brace_level = 0

            try:
                with open(self.ATH_DUMP_FILE, "r") as f:
                    while True:
                        chunk = f.read(256) # Read small chunks
                        if not chunk:
                            break

                        if not in_market_data:
                            # Search for the start of the market_data object
                            key_index = chunk.find('"market_data":{')
                            if key_index != -1:
                                in_market_data = True
                                buffer = chunk[key_index + len('"market_data":'):] # Start buffer after the key
                                brace_level = 1 # We start inside the first {
                                print("[Initializer] Found start of market_data")
                        else:
                            buffer += chunk

                        # Process buffer only if we are inside market_data
                        if in_market_data:
                            # Simple brace counting (might be fragile with nested strings containing braces)
                            for char in chunk: # Process the newly added chunk
                                if char == '{':
                                    brace_level += 1
                                elif char == '}':
                                    brace_level -= 1

                            # Check if we found the end of the market_data object
                            if brace_level == 0:
                                print("[Initializer] Found end of market_data object.")
                                # Attempt to parse just the market_data buffer
                                try:
                                    # The buffer should now contain the complete market_data object string
                                    market_data_json = buffer
                                    # print(f"[Initializer] DEBUG: Final buffer content (first 500): '{market_data_json[:500]}'") # Optional: Keep for further debugging if needed
                                    market_data = json.loads(market_data_json)
                                    ath_data = market_data.get("ath", {})
                                    ath_usd = ath_data.get("usd")
                                    ath_date_data = market_data.get("ath_date", {})
                                    ath_date_usd = ath_date_data.get("usd")
                                    print(f"[Initializer] Extracted ATH USD: {ath_usd}, Date: {ath_date_usd}")
                                    break # Exit file reading loop
                                except ValueError as json_e:
                                    print(f"[Initializer] JSON parsing error for market_data buffer: {json_e}")
                                    # print(f"Failed buffer content: {market_data_json}") # Debug: print failed buffer
                                    # Could not parse, maybe brace counting failed? Stop processing.
                                    break
                                except Exception as parse_e:
                                     print(f"[Initializer] Unexpected error parsing market_data buffer: {parse_e}")
                                     break
                        gc.collect() # GC frequently during parsing

            except Exception as read_e:
                print(f"[Initializer] Error reading/processing {self.ATH_DUMP_FILE}: {read_e}")

            # --- Save extracted data ---
            if ath_usd is not None and ath_date_usd is not None:
                ath_output = {
                    "ath_usd": ath_usd,
                    "ath_date_usd": ath_date_usd
                }
                try:
                    with open(self.ATH_DATA_FILE, "w") as f:
                        json.dump(ath_output, f)
                    print(f"[Initializer] Successfully saved ATH data to {self.ATH_DATA_FILE}")
                except Exception as e:
                    print(f"[Initializer] ERROR: Failed to write {self.ATH_DATA_FILE}: {e}")
            else:
                print(f"[Initializer] Failed to extract ATH data from {self.ATH_DUMP_FILE}.")
                await self._show_initializing_screen("ATH Parse Fail")
                await asyncio.sleep(2)

        # Removed specific urequests.HTTPError catch, rely on status code check and generic Exception
        except MemoryError:
            print("[Initializer] MemoryError during ATH fetch/process. Pico may not have enough RAM.")
            await self._show_initializing_screen("ATH Mem Error")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"[Initializer] Unexpected error during ATH fetch: {e}")
            await self._show_initializing_screen("ATH Error")
            await asyncio.sleep(2)
        finally:
            # Clean up temporary file regardless of success
            if self._file_exists(self.ATH_DUMP_FILE):
                try:
                    os.remove(self.ATH_DUMP_FILE)
                    print(f"[Initializer] Removed temporary file {self.ATH_DUMP_FILE}")
                except Exception as e:
                    print(f"[Initializer] Error removing temporary file {self.ATH_DUMP_FILE}: {e}")
            # Ensure response_stream is closed if it wasn't already in the try block
            if response_stream:
                try:
                    response_stream.close()
                except Exception as close_e:
                    print(f"[Initializer] Error closing response stream in finally: {close_e}")
            gc.collect()


    async def run_initialization(self):
        """Runs all initialization steps."""
        print("[Initializer] Starting initialization process...")
        await self._show_initializing_screen("Initializing")

        # 1. Ensure applets.json exists
        self._ensure_applets_json()
        gc.collect()
        await asyncio.sleep_ms(100) # Small delay

        # 2. Fetch and process ATH data if needed
        await self._fetch_and_process_ath()
        gc.collect()
        await asyncio.sleep_ms(100) # Small delay

        print("[Initializer] Initialization complete.")
        await self._show_initializing_screen("Initialization Done")
        await asyncio.sleep_ms(500) # Show "Done" briefly
        self.screen_manager.clear()
        self.screen_manager.update()
