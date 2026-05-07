# Pinout Reference

All GPIO numbers use the board's native numbering (BCM for Pi, GPIO number for ESP32).
RC522 RFID readers operate at 3.3V. All boards share a common ground.

---

## ESP32 #1 — RFID + Encoder + LED + Bell

Connected to Pi as `/dev/ttyUSB0` (verify with startup handshake — see `serial.md`).

### SPI Bus (shared across all 7 RC522 readers)

| GPIO | Function |
|---|---|
| 23 | MOSI |
| 19 | MISO |
| 18 | SCK |
| 25 | RST — shared across all readers |

### RC522 Chip Select Lines

**Time multiplexing required** — only one CS pin may be pulled low at a time.

| GPIO | Reader ID | Station | Message type sent |
|---|---|---|---|
| 5 | 0 | Recipe card reader | `RCPE` only |
| 4 | 1 | Vegetable washer | `RFID` (paired with `SPIN` from AS5600) |
| 16 | 2 | Plate | `RFID` |
| 17 | 3 | Plate | `RFID` |
| 13 | 4 | Plate | `RFID` |
| 12 | 5 | Plate | `RFID` |
| 26 | 9 | Frying Pan 1 | `RFID` and `TOSS` |

> ⚠ GPIO 16 and 17 are PSRAM-mapped on some ESP32 modules — verify your board variant before soldering.

### AS5600 Magnetic Encoder (I2C — fixed address 0x36)

| GPIO | Function | Notes |
|---|---|---|
| 21 | SDA | I2C data |
| 22 | SCL | I2C clock |
| 32 | DIR | Direction pin — tie to GND if rotation direction doesn't matter |

Spin detection: >360° of rotation within a 2-second window. ESP32 handles detection; Pi counts spins per ingredient.

### Bell Button

Use `INPUT_PULLUP` mode. Button connects pin to GND when pressed. Debouncing handled in firmware (50ms window recommended).

| GPIO | Bell ID | Function |
|---|---|---|
| 14 | 0 | Submit order — sends `BELL:0:PRESSED` |

### LED Output

| GPIO | LED ID | Station |
|---|---|---|
| 33 | 0 | Vegetable washer |

### Power

| Pin | Connection |
|---|---|
| 3V3 | VCC for all RC522 readers and AS5600 |
| GND | Common ground |

---

## ESP32 #2 — RFID + Buttons + Analog + LEDs

Connected to Pi as `/dev/ttyUSB1` (verify with startup handshake — see `serial.md`).

### SPI Bus (shared across all 6 RC522 readers)

| GPIO | Function |
|---|---|
| 23 | MOSI |
| 19 | MISO |
| 18 | SCK |
| 25 | RST — shared across all readers |

### RC522 Chip Select Lines

**Time multiplexing required** — only one CS pin may be pulled low at a time.

| GPIO | Reader ID | Station | Message type sent |
|---|---|---|---|
| 5 | 6 | Plate | `RFID` |
| 4 | 7 | Plate | `RFID` |
| 16 | 8 | Plate | `RFID` |
| 13 | 10 | Frying Pan 2 | `RFID` and `TOSS` |
| 12 | 11 | Deep Fryer 1 | `RFID` |
| 14 | 12 | Deep Fryer 2 | `RFID` |

> ⚠ GPIO 16 is PSRAM-mapped on some ESP32 modules — verify your board variant. GPIO 17 is now free on ESP2.

### Button Inputs (deep fryer)

Use `INPUT_PULLUP` mode. Buttons connect pin to GND when pressed. Debouncing handled in firmware (50ms window recommended).

| GPIO | Button ID | Station |
|---|---|---|
| 21 | 0 | Deep Fryer 1 |
| 22 | 1 | Deep Fryer 2 |

> GPIO 21 and 22 are normally I2C pins on ESP32, but ESP2 has no I2C peripherals so they're free to use for general digital input.

### Analog Input (deferred)

| GPIO | Sensor ID | Station | Notes |
|---|---|---|---|
| 34 | 0 | Ice cream station | Input-only ADC pin. Voltage range, sensor type, and game integration TBD. |

### LED Outputs

| GPIO | LED ID | Station |
|---|---|---|
| 33 | 1 | Frying Pan 1 |
| 32 | 2 | Frying Pan 2 |
| 27 | 3 | Deep Fryer 1 |
| 26 | 4 | Deep Fryer 2 |

### Power

| Pin | Connection |
|---|---|
| 3V3 | VCC for all RC522 readers |
| GND | Common ground |

---

## Raspberry Pi — Game Logic

GPIO uses BCM numbering. ESP32 connections are via USB, not GPIO pins.

### I2C — TFT Screen

| GPIO | Physical Pin | Function |
|---|---|---|
| 2 | Pin 3 | SDA |
| 3 | Pin 5 | SCL |

> Confirm I2C address of your TFT module before writing display code.

### GPIO

| GPIO | Physical Pin | Function | Direction |
|---|---|---|---|
| 17 | Pin 11 | USB speaker trigger | Output |
| 22 | Pin 15 | Reset button | Input (pull-up) |

> The bell button has been moved off the Pi onto ESP1 (see ESP32 #1 above). Pi GPIO 27 is now free.

### USB Serial

| Port | Connected to | Notes |
|---|---|---|
| `/dev/ttyUSB0` | ESP32 #1 | Not guaranteed — use startup handshake to confirm |
| `/dev/ttyUSB1` | ESP32 #2 | Not guaranteed — use startup handshake to confirm |

### Power

| Pin | Function |
|---|---|
| Pin 1 (3V3) | 3.3V out if needed for peripherals |
| Pin 9 (GND) | Common ground |
