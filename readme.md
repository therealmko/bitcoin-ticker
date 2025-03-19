![Satoshi Radio Ticker](https://i.postimg.cc/DzDmwdKK/ticker-landscape.webp "Satoshi Radio Ticker")
# 📻 Satoshi Radio Ticker

Welcome to the Satoshi Radio Ticker project! This compact, desk-friendly device keeps you updated on Bitcoin's price and blockchain status at a glance. Built with affordable, accessible components, it's perfect for crypto enthusiasts who want real-time information without constantly checking their phones.

A Bitcoin price and blockchain information display built with Raspberry Pi Pico W and Pimoroni Display Pack 2.8.

![Satoshi Radio Ticker](https://via.placeholder.com/400x300 "Satoshi Radio Ticker")

## ✨ Features

- 💰 Real-time Bitcoin price display (BTC/USD)
- ⛓️ Current blockchain height display
- 📶 WiFi connectivity for live data updates
- 🔄 Automatic applet cycling
- 🚦 RGB LED status indicator
- ⚡ Low power consumption

## 🔧 Hardware Requirements

To build your own Satoshi Radio Ticker, you'll need:

- Raspberry Pi Pico W
- Pimoroni Display Pack 2.8
- 3D printed case (files provided in this repo)
- 4x M2 x 5mm bolts
- Laser cut acrylic (3mm thick, transparent black)
- Vinyl sticker for the frame
- Double-sided tape for assembly

## 💻 Software Setup

### Option 1: Quick Setup with UF2 File

1. Download the latest `satoshi_radio_ticker.uf2` file from the releases section.
2. Connect your Raspberry Pi Pico W to your computer while holding the BOOTSEL button.
3. The Pico will appear as a USB drive.
4. Copy the `satoshi_radio_ticker.uf2` file to the Pico drive.
5. The Pico will automatically reboot and run the ticker software.

### Option 2: Manual Setup

1. Install [MicroPython](https://micropython.org/download/RPI_PICO_W/) on your Pico W if not already installed.
2. Clone this repository:
   ```
   git clone https://github.com/yourusername/satoshi_radio_ticker.git
   ```
3. Create a `.env` file in the `src` directory with your WiFi credentials:
   ```
   SSID_1=your_wifi_name
   PASSWORD_1=your_wifi_password
   # Add additional networks if needed
   SSID_2=backup_wifi_name
   PASSWORD_2=backup_wifi_password
   ```
4. Install the required tools:
   ```
   pip install -r src/requirements.txt
   ```
5. Upload the code using the makefile:
   ```
   make upload
   ```

## 📡 WiFi Configuration

The ticker needs internet access to fetch Bitcoin data. Create a `.env` file with your network credentials:

```
SSID_1=your_wifi_name
PASSWORD_1=your_wifi_password
# You can add multiple network configurations
SSID_2=second_network_name
PASSWORD_2=second_network_password
```

## 🔨 Physical Assembly

1. 3D print the case (004_CASE_TICKER_PICO_2.8).
2. Mount the Raspberry Pi Pico W in the case using the four M2 x 5mm bolts.
3. Attach the Pimoroni Display Pack to the Pico.
4. Apply the double-sided tape (005_TAPE_TICKER_PICO_2.8) to secure the display.
5. Place the vinyl sticker (003_VINYL_TICKER_PICO_2.8) over the front frame.
6. Add the acrylic cover (002_ACRYL_TICKER_PICO_2.8) to complete the assembly.

Refer to the exploded view diagram in the repository for detailed assembly guidance.

## 🔍 Troubleshooting

### Resetting the Pico

If you need to reset your Pico W:
1. Disconnect power from the device
2. Reconnect while holding the BOOTSEL button
3. Release the button after 2 seconds

### LED Status Indicators

- Yellow: Fetching data from the internet
- Red: Error occurred
- Green: Successfully retrieved data
- Off: Idle state

### Common Issues

- **No WiFi Connection**: Check your network credentials in the `.env` file
- **Screen Doesn't Update**: Try resetting the device
- **Display Shows Error Message**: Check the error text and verify internet connectivity

## 🆘 Support

If you have questions or need help, please open an issue on the GitHub repository.

## 📜 License

This project is released under the Open Source Non-Commercial License. See the LICENSE file for details.
