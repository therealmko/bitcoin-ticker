from applet_manager import AppletManager
import applet_manager
import uasyncio as asyncio
import json
import wifi_manager  # Your custom WiFiManager module
from config import ConfigManager  # Added import for ConfigManager

def safe_convert_to_int(value, default=0) -> int:
    """
    Safely convert a value to int, returning `default` on error.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


class AsyncWebServer:
    """
    A fully asynchronous web server for configuring Wi-Fi networks,
    selecting applets, and optionally rebooting the device.
    Uses uasyncio.start_server for non-blocking I/O.

    :param wifi_manager: An instance responsible for loading,
                         saving, and manipulating Wi-Fi credentials.
    """

    def __init__(self, wifi_manager: wifi_manager.WiFiManager, applet_manager: applet_manager.AppletManager) -> None:
        self.wifi_manager = wifi_manager
        self.applet_manager = applet_manager
        self.ip_address = self.wifi_manager.ip
        
        # Initialize config manager
        self.config_manager = ConfigManager()

        # Example: define your known applets
        self.applets = self.applet_manager.get_applets_list()
        self.routes = {
            "GET /": self.handle_root,  # Serve the main HTML page
            "GET /networks": self.handle_get_networks,
            "GET /applets": self.handle_get_applets,
            "GET /config": self.handle_get_config,  # New route to fetch config
            "POST /submit": self.handle_submit_network,
            "POST /move_up": self.handle_move_up,
            "POST /move_down": self.handle_move_down,
            "POST /remove": self.handle_remove_network,
            "POST /select_applets": self.handle_select_applets,
            "POST /update_config": self.handle_update_config,  # New route to update config
            "POST /reboot": self.handle_reboot,
        }
        
    async def handle_root(self, request_lines, writer):
        html = self.web_page()
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html\r\n"
            "Connection: close\r\n\r\n" + html
        )
        writer.write(response.encode('utf-8'))
        await writer.drain()

    async def handle_get_networks(self, request_lines, writer):
        ssids = [{"ssid": network["ssid"]} for network in self.wifi_manager.networks]
        response_body = json.dumps(ssids)
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            "Connection: close\r\n\r\n" + response_body
        )
        writer.write(response.encode('utf-8'))
        await writer.drain()
        
    async def handle_get_applets(self, request_lines, writer):
        response_body = json.dumps(self.applets)
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            "Connection: close\r\n\r\n" + response_body
        )
        writer.write(response.encode('utf-8'))
        await writer.drain()
    
    async def handle_get_config(self, request_lines, writer):
        """Handle GET request for configuration settings"""
        config = {
            "applet_duration": self.config_manager.get_applet_duration(),
            "timezone_offset": self.config_manager.get_timezone_offset()
        }
        response_body = json.dumps(config)
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            "Connection: close\r\n\r\n" + response_body
        )
        writer.write(response.encode('utf-8'))
        await writer.drain()

    async def handle_submit_network(self, request_lines, writer):
        _, body = self.parse_request_body(request_lines)
        try:
            params = json.loads(body)
            ssid = params.get("ssid", "")
            password = params.get("password", "")
            self.wifi_manager.save_network(ssid, password)
            print(f"[AsyncWebServer] Added Wi-Fi network: {ssid}")
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                "Connection: close\r\n\r\n"
                "Wi-Fi network added successfully!"
            )
        except Exception:
            response = (
                "HTTP/1.1 400 Bad Request\r\n"
                "Content-Type: text/plain\r\n"
                "Connection: close\r\n\r\n"
                "Could not add Wi-Fi network"
            )
        writer.write(response.encode('utf-8'))
        await writer.drain()

    async def handle_select_applets(self, request_lines, writer):
        print("Select Applets")
        _, body = self.parse_request_body(request_lines)
        try:
            request= json.loads(body)
            self.applet_manager.update_applets(request)
            print("[AsyncWebServer] Updated applet selection:", request)
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                "Connection: close\r\n\r\n"
                "Applet selection updated successfully!"
            )
            writer.write(response.encode('utf-8'))
            await writer.drain()
        except  Exception as e :
            print(e)
            error_message = str(e)  # Convert exception to string
            response = (
                "HTTP/1.1 400 Bad Request\r\n"
                "Content-Type: text/plain\r\n"
                "Connection: close\r\n\r\n"
                f"Could not update applet selection. Error: {error_message}"
            )
            writer.write(response.encode('utf-8'))
            await writer.drain()
    
    async def handle_update_config(self, request_lines, writer):
        """Handle POST request to update configuration settings"""
        _, body = self.parse_request_body(request_lines)
        try:
            params = json.loads(body)
            applet_duration = params.get("applet_duration", 10)
            timezone_offset = params.get("timezone_offset", 0)
            
            # Update the configs with settings
            actual_duration = self.config_manager.set_applet_duration(applet_duration)
            actual_offset = self.config_manager.set_timezone_offset(timezone_offset)
            
            print(f"[AsyncWebServer] Updated config: duration={actual_duration}, tz={actual_offset}")

            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                "Connection: close\r\n\r\n" +
                json.dumps({
                    "applet_duration": actual_duration,
                    "timezone_offset": actual_offset
                })
            )
        except Exception as e:
            print(f"[AsyncWebServer] Error updating config: {e}")
            response = (
                "HTTP/1.1 400 Bad Request\r\n"
                "Content-Type: text/plain\r\n"
                "Connection: close\r\n\r\n"
                "Could not update configuration"
            )
        writer.write(response.encode('utf-8'))
        await writer.drain()

    async def handle_move_up(self, request_lines, writer):
        await self.handle_move("up", request_lines, writer)

    async def handle_move_down(self, request_lines, writer):
        await self.handle_move("down", request_lines, writer)

    async def handle_move(self, direction, request_lines, writer):
        _, body = self.parse_request_body(request_lines)
        params = json.loads(body)
        index = params.get("index", -1)
        if index >= 0:
            self.wifi_manager.move_network(index, direction)
            print(f"[AsyncWebServer] Moved network at index {index} {direction}")
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                "Connection: close\r\n\r\n"
                "Network moved successfully"
            )
        else:
            response = (
                "HTTP/1.1 400 Bad Request\r\n"
                "Content-Type: text/plain\r\n"
                "Connection: close\r\n\r\n"
                "Invalid index"
            )
        writer.write(response.encode('utf-8'))
        await writer.drain()

    async def handle_remove_network(self, request_lines, writer):
        _, body = self.parse_request_body(request_lines)
        params = json.loads(body)
        index = params.get("index", -1)
        if index >= 0:
            self.wifi_manager.remove_network(index)
            print(f"[AsyncWebServer] Removed network at index {index}")
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                "Connection: close\r\n\r\n"
                "Network removed successfully"
            )
        else:
            response = (
                "HTTP/1.1 400 Bad Request\r\n"
                "Content-Type: text/plain\r\n"
                "Connection: close\r\n\r\n"
                "Invalid index"
            )
        writer.write(response.encode('utf-8'))
        await writer.drain()



    async def handle_reboot(self, request_lines, writer):
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n"
            "Connection: close\r\n\r\n"
            "Rebooting device..."
        )
        writer.write(response.encode('utf-8'))
        await writer.drain()
        await writer.wait_closed()
        import machine
        machine.reset()

    def parse_request_body(self, request_lines):
        if isinstance(request_lines, list):
            request_lines = "\n".join(request_lines)  # Ensure it's a single string
        if "\r\n\r\n" in request_lines:
            headers, body = request_lines.split("\r\n\r\n", 1)
        elif "\n\n" in request_lines:
            headers, body = request_lines.split("\n\n", 1)
        else:
            headers, body = (request_lines, "")
        return headers, body.strip()  # Strip extra whitespace
    #
    # -------------------- HTML Generation --------------------
    #
    def web_page(self) -> str:
        print(f"[AsyncWebServer] IP address: {self.ip_address}")
        
        # Get current applet duration
        applet_duration = self.config_manager.get_applet_duration()
        timezone_offset = self.config_manager.get_timezone_offset()
        
        html = f"""
    <!DOCTYPE html>
    <html lang="en">

    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Satoshi Radio Ticker</title>
    <link rel="icon" type="image/png" href="https://pool.satoshiradio.nl/favicon-32x32.png">
    <style>
        /* General styles */
        body {{
        background-color: #000;
        color: #fff;
        font-family: sans-serif;
        text-align: center;
        text-transform: uppercase;
        margin: 0;
        padding: 20px;
        }}

        h1,
        h2 {{
        color: rgb(252, 98, 43);
        }}

        ul {{
        list-style: none;
        padding: 0;
        margin: 0;
        }}

        li {{
        margin: 10px 0;
        padding: 10px;
        background-color: #333;
        border-radius: 5px;
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
        }}

        /* Button styles */
        button {{
        background-color: rgb(252, 98, 43);
        border: none;
        color: white;
        padding: 8px 12px;
        border-radius: 3px;
        cursor: pointer;
        font-size: 14px;
        }}

        button:hover {{
        background-color: #e95b33;
        }}

        /* Input fields */
        input[type="text"],
        input[type="password"],
        input[type="number"],
        button {{
        width: 100%;
        padding: 10px;
        margin: 5px 0;
        border: none;
        border-radius: 5px;
        box-sizing: border-box;
        text-transform: none;
        }}

        /* Container adjustments for mobile */
        #networks-container {{
        margin: 0 auto;
        max-width: 400px;
        }}

        @media (max-width: 600px) {{
        body {{
            padding: 10px;
        }}

        li {{
            flex-direction: column;
            align-items: stretch;
            text-align: left;
        }}

        button {{
            width: 100%;
        }}

        input[type="text"],
        input[type="password"],
        input[type="number"] {{
            width: 100%;
        }}
        }}

        #applet-container {{
        display: flex;
        flex-direction: column;
        gap: 10px;
        }}

        #applet-container label {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        padding: 10px;
        background-color: #333;
        border-radius: 5px;
        font-size: 14px;
        cursor: pointer;
        }}

        #applet-container input[type="checkbox"] {{
        width: 20px;
        height: 20px;
        cursor: pointer;
        }}

        @media (max-width: 600px) {{
        #applet-container label {{
            flex-direction: column;
            align-items: flex-start;
        }}
        }}
    </style>
    </head>

    <body>
    <h1>Satoshi Radio Ticker</h1>
    <h2>Saved Wi-Fi Networks</h2>
    <div id="networks-container">
        <ul id="networks-list">
        <!-- Networks will be dynamically rendered here -->
        </ul>
    </div>

    <h2>Add New Wi-Fi Network</h2>
    <form id="wifi-form" style="max-width: 400px; margin: 0 auto; text-align: left;">
        <label for="ssid" style="display: block; margin-bottom: 5px;">SSID:</label>
        <input type="text" id="ssid" name="ssid" placeholder="Enter Wi-Fi SSID" required>

        <label for="password" style="display: block; margin-top: 10px; margin-bottom: 5px;">Password:</label>
        <input type="password" id="password" name="password" placeholder="Enter Wi-Fi Password" required>

        <button type="submit" style="margin-top: 15px; width: 100%;">Add Network</button>
    </form>

    <h2>Applet Selection</h2>
    <form id="applet-form" style="max-width: 400px; margin: 0 auto; text-align: left;">
        <div id="applet-container">
        <!-- Applets will be dynamically rendered here -->
        </div>
    </form>
    
    <h2>Configuration</h2>
    <form id="config-form" style="max-width: 400px; margin: 0 auto; text-align: left;">
        <label for="applet-duration" style="display: block; margin-bottom: 5px;">Applet Duration (seconds):</label>
        <input type="number" id="applet-duration" name="applet_duration" min="3" max="60" step="1" value="{applet_duration}" required>
        <p style="font-size: 12px; color: #ccc;">Duration must be between 3 and 60 seconds</p>
    
        <label for="timezone-offset" style="display: block; margin-top: 15px; margin-bottom: 5px;">Timezone Offset (hours from UTC):</label>
        <input type="number" id="timezone-offset" name="timezone_offset" min="-12" max="14" step="1" value="{timezone_offset}" required>
        <p style="font-size: 12px; color: #ccc;">Valid values between -12 and +14</p>
    
        <button type="submit" style="margin-top: 15px; width: 100%;">Save Configuration</button>
    </form>

    <button onclick="rebootDevice()" style="max-width: 400px; margin: 20px auto;">Reboot Device</button>

    <script>
const serverIP = "{self.ip_address}";

// Fetch and render saved Wi-Fi networks
async function fetchNetworks() {{
  try {{
    const response = await fetch(`http://${{serverIP}}/networks`);
    if (response.ok) {{
      const networks = await response.json();
      const networksList = document.getElementById('networks-list');
      networksList.innerHTML = ''; // Clear existing list

      networks.forEach((network, i) => {{
        const li = document.createElement('li');

        // Create a container for text and actions
        const textContainer = document.createElement('div');
        textContainer.textContent = network.ssid;
        textContainer.style.flex = '1';

        // Add buttons for actions
        const upButton = document.createElement('button');
        upButton.textContent = '↑';
        upButton.onclick = () => moveNetwork('up', i);

        const downButton = document.createElement('button');
        downButton.textContent = '↓';
        downButton.onclick = () => moveNetwork('down', i);

        const removeButton = document.createElement('button');
        removeButton.textContent = '✖';
        removeButton.onclick = () => removeNetwork(i);

        // Append text and buttons to the list item
        li.appendChild(textContainer);

        const buttonContainer = document.createElement('div');
        buttonContainer.style.display = 'flex';
        buttonContainer.style.gap = '10px';
        buttonContainer.appendChild(upButton);
        buttonContainer.appendChild(downButton);
        buttonContainer.appendChild(removeButton);

        li.appendChild(buttonContainer);
        networksList.appendChild(li);
      }});
    }} else {{
      alert('Failed to fetch networks');
    }}
  }} catch (error) {{
    console.error('Error fetching networks:', error);
  }}
}}

// Fetch and render applets
async function fetchApplets() {{
  try {{
    const response = await fetch(`http://${{serverIP}}/applets`);
    if (response.ok) {{
      const applets = await response.json();
      const form = document.getElementById('applet-container');
      form.innerHTML = '';
      applets.forEach(applet => {{
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.name = 'applets';
        checkbox.value = applet.name;
        checkbox.checked = applet.enabled;

        const label = document.createElement('label');
        label.textContent = applet.name;
        label.appendChild(checkbox);

        form.appendChild(label);
        form.appendChild(document.createElement('br'));
      }});
      const submitButton = document.createElement('button');
      submitButton.textContent = 'Save Applets';
      submitButton.type = 'submit';
      submitButton.style.marginTop = '10px';
      form.appendChild(submitButton);

    }} else {{
      alert('Failed to fetch applets');
    }}
  }} catch (error) {{
    console.error('Error fetching applets:', error);
  }}
}}

// Fetch configuration
async function fetchConfig() {{
  try {{
    const response = await fetch(`http://${{serverIP}}/config`);
    if (response.ok) {{
      const config = await response.json();
      document.getElementById('applet-duration').value = config.applet_duration;
      document.getElementById('timezone-offset').value = config.timezone_offset;
    }} else {{
      alert('Failed to fetch configuration');
    }}
  }} catch (error) {{
    console.error('Error fetching configuration:', error);
  }}
}}

// Move a network up or down
async function moveNetwork(direction, index) {{
  try {{
    const response = await fetch(`http://${{serverIP}}/move_${{direction}}`, {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{index}}),
    }});
    if (response.ok) {{
      fetchNetworks();
    }} else {{
      alert('Failed to move network');
    }}
  }} catch (error) {{
    console.error(`Error moving network ${{direction}}:`, error);
  }}
}}

async function rebootDevice() {{
    try {{
        const response = await fetch(`http://${{serverIP}}/reboot`, {{
            method: 'POST',
        }});
        if (response.ok) {{
            alert('Rebooting device...');
        }} else {{
            alert('Failed to reboot device');
        }}
    }} catch (error) {{
        console.error('Error rebooting device:', error);
    }}
}}
async function addNetwork(event) {{
  event.preventDefault();
  const form = document.getElementById('wifi-form');
  const data = Object.fromEntries(new FormData(form));

  try {{
    const response = await fetch(`http://${{serverIP}}/submit`, {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify(data),
    }});
    if (response.ok) {{
      alert('Network added successfully!');
      form.reset();
      fetchNetworks();
    }} else {{
      alert('Failed to add network');
    }}
  }} catch (error) {{
    console.error('Error adding network:', error);
  }}
}}

// Remove a network
async function removeNetwork(index) {{
  try {{
    const response = await fetch(`http://${{serverIP}}/remove`, {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{index}}),
    }});
    if (response.ok) {{
      fetchNetworks();
    }} else {{
      alert('Failed to remove network');
    }}
  }} catch (error) {{
    console.error('Error removing network:', error);
  }}
}}

// Save applet selections
async function saveApplets(event) {{
  event.preventDefault();
  const checkboxes = Array.from(document.querySelectorAll('#applet-form input[type="checkbox"]'));
  const applets = checkboxes.map(checkbox => ({{
    name: checkbox.value,
    enabled: checkbox.checked,
  }}));

  try {{
    const response = await fetch(`http://${{serverIP}}/select_applets`, {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify(applets),
    }});
    if (response.ok) {{
      alert('Applet selection saved successfully!');
    }} else {{
      alert('Failed to save applet selection');
    }}
  }} catch (error) {{
    console.error('Error saving applet selection:', error);
  }}
}}

// Save configuration
async function saveConfig(event) {{
  event.preventDefault();
  const form = document.getElementById('config-form');
  const formData = new FormData(form);
  const data = {{
    applet_duration: parseInt(formData.get('applet_duration'), 10),
    timezone_offset: parseInt(formData.get('timezone_offset'), 10)
  }};
  
  try {{
    const response = await fetch(`http://${{serverIP}}/update_config`, {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify(data),
    }});
    
    if (response.ok) {{
      const result = await response.json();
      // Update the input field with the actual value (in case it was adjusted)
      document.getElementById('applet-duration').value = result.applet_duration;
      alert('Configuration saved successfully!');
    }} else {{
      alert('Failed to save configuration');
    }}
  }} catch (error) {{
    console.error('Error saving configuration:', error);
  }}
}}

// Attach handlers
document.getElementById('wifi-form').addEventListener('submit', addNetwork);
document.getElementById('applet-form').addEventListener('submit', saveApplets);
document.getElementById('config-form').addEventListener('submit', saveConfig);

// Initial fetch
fetchNetworks();
fetchApplets();
fetchConfig();
    </script>
    </body>

    </html>
        """
        return html
    #
    # -------------------- URL/Form Parsing --------------------
    #
    def url_decode(self, s: str) -> str:
        """
        Decode URL-encoded form data, replacing '+' with space
        and '%xx' with the corresponding character.
        """
        result = ''
        i = 0
        while i < len(s):
            c = s[i]
            if c == '+':
                result += ' '
                i += 1
            elif c == '%':
                hex_value = s[i+1:i+3]
                try:
                    result += chr(int(hex_value, 16))
                except ValueError:
                    print(f"[AsyncWebServer] Malformed percent-encoding: %{hex_value}")
                i += 3
            else:
                result += c
                i += 1
        return result

    def parse_form_data(self, form_data: str) -> dict:
        """
        Parse the URL-encoded form data into a dictionary.
        e.g. 'key1=value1&key2=value2' -> {'key1': 'value1', 'key2': 'value2'}.
        """
        params = {}
        for pair in form_data.split('&'):
            if '=' in pair:
                key, value = pair.split('=', 1)
                key = self.url_decode(key)
                value = self.url_decode(value)
                params[key] = value
        return params

    def update_applets(self, selected_applets) -> None:
        """
        Save the user-selected applets to a JSON file.
        """
        self.applet_manager.update_applets(selected_applets)

    #
    # -------------------- Request Handling --------------------
    #
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            # Read up to 4 KB of data from the client
            request_bytes = await reader.read(4096)
            if not request_bytes:
                await writer.aclose()
                return

            request_str = request_bytes.decode('utf-8', 'ignore')
            print('[AsyncWebServer] Received request:\n', request_str)

            # Parse the HTTP request
            request_lines = request_str.split("\r\n")
            request_line = request_lines[0] if request_lines else ""
            method, path, *_ = request_line.split(" ")

            # Match the route
            handler = self.routes.get(f"{method} {path}")
            if handler:
                # Call the handler with the request details
                await handler(request_lines, writer)
            else:
                # Default response for unknown routes
                response = (
                    "HTTP/1.1 404 Not Found\r\n"
                    "Content-Type: text/plain\r\n"
                    "Connection: close\r\n\r\n"
                    "404 Not Found"
                )
                writer.write(response.encode('utf-8'))
                await writer.drain()
        except Exception as e:
            print(f"[AsyncWebServer] Error handling request: {e}")
            try:
                error_resp = "HTTP/1.1 500 Internal Server Error\r\n\r\n"
                writer.write(error_resp.encode('utf-8'))
                await writer.drain()
            except Exception:
                pass
        finally:
            await writer.aclose()

    #
    # -------------------- Starting the Server --------------------
    #
    async def start_web_server(self) -> None:
        """
        Create an asynchronous server listening on port 80.
        Each new client is handled in `handle_client`.
        """
        server = await asyncio.start_server(self.handle_client, '0.0.0.0', 80)
        print('[AsyncWebServer] Listening on 0.0.0.0:80')
        # Serve forever (non-blocking)
        try:
            while True:
                print("[AsyncWebServer] Waiting for incoming connections...")
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            server.close()
            await server.wait_closed()
            print('[AsyncWebServer] Server stopped.')
