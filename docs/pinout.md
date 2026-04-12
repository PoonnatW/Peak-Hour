# Pinout Reference

All GPIO numbers use the board's native numbering (BCM for Pi, GPIO number for ESP32).
RC522 RFID readers operate at 3.3V. All boards share a common ground.

---

## ESP32 #1 — RFID Readers + AS5600 Encoder

Connected to Pi as `/dev/ttyUSB0` (verify with startup handshake — see `serial.md`).

### SPI Bus (shared across all 9 RC522 readers)

| GPIO | Function |
|---|---|
| 23 | MOSI |
| 19 | MISO |
| 18 | SCK |
| 25 | RST — shared across all readers |

### RC522 Chip Select Lines

**Time multiplexing required** — only one CS pin may be pulled low at a time. Poll readers sequentially; never activate two simultaneously.

| GPIO | Reader ID | Station | Message type sent |
|---|---|---|---|
| 5 | 0 | Plate | `RFID`  |
| 4 | 1 | Plate | `RFID`  |
| 16 | 2 | Plate | `RFID`  |
| 17 | 3 | Plate | `RFID`  |
| 13 | 4 | Plate | `RFID`  |
| 12 | 5 | Plate | `RFID`  |
| 14 | 6 | Plate | `RFID`  |
| 27 | 7 | Vegetable Washer | `RFID` and `SPIN` |
| 26 | 8 | Recipe card reader | `RCPE` only |

> ⚠ GPIO 16 and 17 are PSRAM-mapped on some ESP32 modules — verify your board variant before soldering. Avoid GPIO 2 and 15 for CS lines (boot-mode strapping pins).

### AS5600 Magnetic Encoder (I2C — fixed address 0x36)

| GPIO | Function | Notes |
|---|---|---|
| 21 | SDA | I2C data |
| 22 | SCL | I2C clock |
| 32 | DIR | Direction pin — tie to GND if rotation direction doesn't matter |

Spin detection: >360° of rotation within a 2-second window. ESP32 handles detection; Pi counts spins per ingredient.

### Output

| GPIO | LED ID | Station |
|---|---|---|
| 33 | 0 | Vegetable washer |

### Power

| Pin | Connection |
|---|---|
| 3V3 | VCC for all RC522 readers and AS5600 |
| GND | Common ground |

---

## ESP32 #2 — Buttons + Analog

Connected to Pi as `/dev/ttyUSB1` (verify with startup handshake — see `serial.md`).

### SPI Bus (shared across all 4 RC522 readers)

| GPIO | Function |
|---|---|
| 23 | MOSI |
| 19 | MISO |
| 18 | SCK |
| 25 | RST — shared across all readers |

### RC522 Chip Select Lines

**Time multiplexing required** — only one CS pin may be pulled low at a time.

| GPIO | Reader ID | Station |
|---|---|---|
| 5 | 9 | Frying Pan |
| 4 | 10 | Frying Pan |
| 2 | 11 | Deep Fryer |
| 15 | 12 | Deep Fryer |

> ⚠ GPIO 2 and GPIO 15 are strapping pins — add 10kΩ pull-up resistors to ensure they are high at boot.

### Button Inputs (deep fryer only)

Use `INPUT_PULLUP` mode. Buttons connect the pin to GND when pressed. Debouncing handled in firmware (50ms window recommended).

| GPIO | Button ID | Station |
|---|---|---|
| 26 | 0 | Deep Fryer 1 |
| 27 | 1 | Deep Fryer 2 |

### Analog Input

| GPIO | Sensor ID | Station | Notes |
|---|---|---|---|
| 34 | 0 | Ice cream station | Input-only ADC pin. Voltage range and sensor type TBD. |

### LED Outputs

| GPIO | LED ID | Station |
|---|---|---|
| 33 | 1 | Frying Pan 1 |
| 32 | 2 | Frying Pan 2 |
| 14 | 3 | Deep Fryer 1 |
| 16 | 4 | Deep Fryer 2 |

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

> Confirm I2C address of your TFT module (typically 0x3C or 0x3D) before writing display code.

### GPIO

| GPIO | Physical Pin | Function | Direction |
|---|---|---|---|
| 17 | Pin 11 | USB speaker trigger | Output |
| 27 | Pin 13 | Bell button | Input (pull-up) |
| 22 | Pin 15 | Reset button | Input (pull-up) |

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
