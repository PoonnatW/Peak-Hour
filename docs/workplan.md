# Project Workplan — Peak Hour

Two ESP32s handle all physical I/O and send processed events over serial. The Raspberry Pi owns all game logic and state.

---

## Architecture Overview

```
[Physical Hardware]
      |
[ESP32 #1]        [ESP32 #2]
  RC522 x9          RC522 x4
  AS5600            Buttons x2
  LED x1            Analog x1
                    LEDs x4
      |                  |
   USB serial        USB serial
      |                  |
        [Raspberry Pi]
   Game logic, state, display
   TFT screen, USB speaker, bell, reset
```

See `docs/pinout.md` for GPIO assignments.

---

## Serial Message Protocol

- Baud rate: `115200`
- Format: `TYPE:ID:VALUE\n`
- See `docs/serial.md` for full message reference.

---

## Raspberry Pi

**Language:** Python
**Serial ports:** `/dev/ttyUSB0` and `/dev/ttyUSB1` — use startup handshake to detect which is which (each ESP32 sends `HELLO:ESP1` or `HELLO:ESP2` on boot).

### Game Logic Responsibilities

**RFID tracking**
Reads `RFID:[ID]:[Tag]` messages and maps them to game pieces using `game_pieces.csv`. Knows which piece is at which station at all times.

**Vegetable washer (spin counting)**
Receives `SPIN:0:DETECTED` from ESP32 #1. If a game piece is at that station, increments its spin counter. When the required spin count is reached, sends `LED:0:ON` to ESP32 #1.

**Frying pan (toss counting)**
Receives `TOSS:[Reader_ID]:DETECTED` from ESP32 #1. ESP32 handles all timing logic — the Pi simply increments the toss counter for the ingredient at that station. When the required toss count (ingredient-specific) is reached, sends `LED:[1 or 2]:ON` to ESP32 #2.

Toss detection logic on the ESP32: if the same Tag UID is detected on a frying pan reader after ≥0.5s and <5s since its last detection, it counts as a toss. Detections under 0.5s are ignored (continuous read). Detections after ≥5s are treated as a fresh placement.

**Deep fryer (button press counting)**
Receives `BTN:[0 or 1]:PRESSED` from ESP32 #2. If a game piece is at that station, increments its press counter. When the required press count (ingredient-specific) is reached, sends `LED:[3 or 4]:ON` to ESP32 #2.

**Ice cream station**
Receives `ANLG:0:[value]` from ESP32 #2. Tracks whether the ice cream task is complete. Checked when the bell is pressed, confirms whether voltage falls within the range demanded by the recipe card.

**Recipe cards**
Receives `RCPE:8:[Tag_UID]` from ESP32 #1. Looks up the UID in `recipes.csv` to get the dish name and required ingredients. Sets the active recipe for the round. Ice cream implementation (e.g. main recipe paired with ice cream or separate) is TBD, for now focus on recipes for main dish cards, ice cream will likely be added as new recipe IDs with different values later on.

**Bell**
Physical button input on the Pi. When pressed:
1. Checks all plate RFID readers for the required cooked ingredients.
2. Checks ice cream completion.
3. If all required items are present and cooked → game ends, plays win sound, shows score.
4. Otherwise → plays error sound.

Broadcasts `BELL:0:PRESSED` to both ESP32s after reading.

**Reset button**
Physical button input on the Pi. Clears all cooking doneness, resets all counters and toss/press counts, turns off all LEDs (sends `LED:[ID]:OFF` for all IDs). Does not restart the program.

### Data Files

| File | Contents |
|---|---|
| `game_pieces.csv` | RFID Tag UID → game piece name (e.g. `A1B2C3D4, Tomato`) |
| `recipes.csv` | Recipe card UID → dish name + required ingredient list (e.g. `FF3C12AA, Salad, Tomato\|Lettuce\|Carrot`) |
| `config.py` | Sensor ID → station type dict (e.g. `{3: "Frying Pan", 4: "Deep Fryer"}`), cooking thresholds, toss/press counts per ingredient |

### Hardware Outputs

**TFT screen (I2C):** Displays current recipe, cooking status per station, win/loss screen.
**USB speaker:** Plays audio feedback — win jingle, error buzz.

---

## ESP32 #1

**Language:** Arduino C
**Hardware:** 9× RC522 RFID readers, 1× AS5600 magnetic encoder, 1× LED

### RFID Readers (RC522, SPI)

All 9 readers share MOSI, MISO, SCK, and RST. Each has its own CS line.
**Time multiplexing required** — only one CS pin may be pulled low at a time. Poll readers sequentially in the main loop; never activate two simultaneously or they will corrupt each other's SPI output.

Reader IDs 0–6 are plate readers.   Reader ID 7 is the Vegetable Washer. Reader ID 8 is the recipe card reader and sends `RCPE` instead of `RFID`.

### AS5600 Magnetic Encoder (I2C — fixed address 0x36)

Reads raw angle data continuously. Detects a spin when total angle change exceeds 360° within a 2-second window. Sends `SPIN:0:DETECTED`. The Pi handles all spin counting logic.

DIR pin (GPIO 32): tie to GND if rotation direction is irrelevant.

Only one AS5600 can be on the I2C bus at a time without a multiplexer.

### LED

GPIO 33 — vegetable washer (LED ID 0). Activates on `LED:0:ON` from Pi.

### Command Filtering

Silently ignores any Pi command whose LED ID is not `0`.

---

## ESP32 #2

**Language:** Arduino C
**Hardware:** 4× RC522 RFID readers, 2× buttons, 1× analog input, 4× LEDs

### RFID Readers (RC522, SPI)

Same SPI sharing rules as ESP32 #1. **Time multiplexing required.**
Reader IDs 9–12 are station readers. Send `RFID:[ID]:[Tag_UID]` only — no toss logic on these readers.

**Frying pan toss detection** — for reader IDs designated as frying pan stations (defined in firmware, matching `config.py`):
- Track last Tag UID and last detection timestamp per reader.
- On each new detection of the same UID:
  - < 0.5s since last detection → ignore
  - ≥ 0.5s and < 5s → send `TOSS:[Reader_ID]:DETECTED`
  - ≥ 5s → treat as fresh placement, reset state, send `RFID:[Reader_ID]:[Tag_UID]`
- Detection of a *different* UID always resets state and sends `RFID` as normal.

### Buttons (deep fryer only)

2 buttons total, one per deep fryer station.
- Use `INPUT_PULLUP` mode. Button connects pin to GND when pressed.
- **Debounce in firmware** — 50ms window recommended. Do not send multiple `PRESSED` events for a single physical press.
- Sends `BTN:[ID]:PRESSED`. Pi handles all press counting and thresholds.

| Button ID | Station |
|---|---|
| 0 | Deep Fryer 1 |
| 1 | Deep Fryer 2 |

### Ice Cream Station (Analog)

GPIO 34 reads a direct voltage from the ice cream station. Sends `ANLG:0:[0-4095]`.
Sensor type and voltage range TBD — update this section when confirmed.

### LEDs

| LED ID | Station |
|---|---|
| 1 | Frying Pan 1 |
| 2 | Frying Pan 2 |
| 3 | Deep Fryer 1 |
| 4 | Deep Fryer 2 |

### Command Filtering

Silently ignores any Pi command whose LED ID is not 1–4.

---

## Win Condition

1. A recipe card is scanned → Pi loads the required ingredients for that dish.
2. Each ingredient must be placed at its correct station and cooked to completion (LED on = done):
   - Vegetable washer → enough spins counted
   - Frying pan → enough valid tosses counted
   - Deep fryer → enough button presses counted
3. Cooked ingredients must be placed on the plate readers (IDs 0-6).
4. Ice cream task must also be completed.
5. Bell is pressed → Pi checks plate contents + ice cream state → if all requirements met, game ends.

All cooking doneness resets on the reset button. Active recipe resets when a new recipe card is scanned.
