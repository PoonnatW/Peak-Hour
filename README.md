# Peak Hour

Raspberry Pi + 2× ESP32 cooking minigame using RFID, physical buttons,
and sensors. 

Pi handles game logic; ESP32s handle I/O.

## Repo structure
docs/       → Serial protocol, pinout reference, this workplan
pi/         → Python game logic (runs on Raspberry Pi)
esp32/      → Arduino sketches for ESP32 #1 and #2

## Hardware setup
See docs/pinout.md for all GPIO/pin assignments, subject to change once hardware.
Both ESP32s connect to the Pi via USB.

## Running the Pi code
# 1. Install dependencies
pip install -r pi/requirements.txt

# 2. Run
python pi/main.py

## Flashing an ESP32
Open esp32/esp32_1/esp32_1.ino (or esp32_2) in Arduino IDE.
Select board: ESP32 Dev Module. Flash normally.

## Serial protocol
See docs/serial.md.
