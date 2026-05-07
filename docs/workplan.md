# Project Workplan — Peak Hour

Two ESP32s handle all physical I/O and send processed events over serial. The Raspberry Pi owns all game logic, state, audio, and display.

---

## Architecture Overview

```
[Physical Hardware]
      |
[ESP32 #1]        [ESP32 #2]
  RC522 x7          RC522 x6
  AS5600            Buttons x2 (deep fryer)
  LED x1            Analog x1
  Bell button x1    LEDs x4
      |                  |
   USB serial        USB serial
      |                  |
        [Raspberry Pi]
   Game logic, state, TFT screen, USB speaker, reset button
```

See `docs/serial.md` for the full message protocol.
See `docs/pinout.md` for GPIO assignments.
See `docs/may7_update.md` for the latest hardware/spec change log.

---

## Reader ID Map

| Reader ID | Function | Board |
|---|---|---|
| 0 | Recipe card reader | ESP1 |
| 1 | Vegetable washer | ESP1 |
| 2–5 | Serving plate | ESP1 |
| 9 | Frying pan 1 | ESP1 |
| 6–8 | Serving plate | ESP2 |
| 10 | Frying pan 2 | ESP2 |
| 11–12 | Deep fryer | ESP2 |

Total: 7 plate readers, 2 frying pan stations, 2 deep fryer stations, 1 vegetable washer, 1 recipe card reader.

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
Receives `SPIN:0:DETECTED` from ESP32 #1. If a game piece is at the washer (Reader 1), increments its spin counter. When the required spin count is reached, sends `LED:0:ON` to ESP32 #1.

**Frying pan (toss counting)**
Receives `TOSS:[Reader_ID]:DETECTED` from either ESP32 #1 (Reader 9, Frying Pan 1) or ESP32 #2 (Reader 10, Frying Pan 2). Each ESP handles its own toss timing logic — the Pi simply increments the toss counter for the ingredient at that station. When the required toss count is reached, sends `LED:[1 or 2]:ON` to ESP32 #2.

Toss detection logic on the ESP32: if the same Tag UID is detected on a frying pan reader after ≥0.5s and <5s since its last detection, it counts as a toss. Detections under 0.5s are ignored. Detections after ≥5s are treated as a fresh placement.

**Deep fryer (button press counting)**
Receives `BTN:[0 or 1]:PRESSED` from ESP32 #2. If a game piece is at the matching deep fryer station (Reader 11 or 12), increments its press counter. When the required press count is reached, sends `LED:[3 or 4]:ON` to ESP32 #2.

**Ice cream station (deferred)**
Receives `ANLG:0:[value]` from ESP32 #2. Implementation is currently deferred — code should accept and store these messages, but no recipe currently consumes them.

**Recipe cards**
Receives `RCPE:0:[Tag_UID]` from ESP32 #1. Looks up the UID in `recipes.csv` to get the dish name and required ingredients. Sets the active recipe for the round and triggers the screen flow.

**Bell**
Receives `BELL:0:PRESSED` from ESP32 #1 (the bell button is wired to ESP1). When received:
1. Triggers screen "Checking…" state.
2. Checks all plate RFID readers (IDs 2–8) for the required cooked ingredients.
3. Checks ice cream completion (when implemented).
4. If correct → ✅, win sound, end game.
5. If wrong → ❌, error sound, continue play.

**Reset button**
Physical button input on the Pi (GPIO 22). Clears all cooking doneness, resets all counters, turns off all LEDs (sends `LED:[ID]:OFF` for all IDs). Returns the screen to idle.

### Data Files

| File | Contents |
|---|---|
| `game_pieces.csv` | RFID Tag UID → game piece name (e.g. `A1B2C3D4, Tomato`) |
| `recipes.csv` | Recipe card UID → dish name + required ingredient list |
| `config.py` | Reader ID → station type dict, cooking thresholds per ingredient, timing constants |

---

## Game Pieces

### Raw Ingredients (×30 total)

| Category | Ingredient | Count | Station | Threshold |
|---|---|---|---|---|
| 🥩 Pan | Salmon | 4 | Frying Pan | 4 flips |
| 🥩 Pan | Beef Steak | 5 | Frying Pan | 6 flips |
| 🥩 Pan | Chicken | 4 | Frying Pan | 8 flips |
| 🍟 Fryer | French Fries | 4 | Deep Fryer | 16 presses |
| 🍟 Fryer | Onion Rings | 4 | Deep Fryer | 8 presses |
| 🥦 Wash | Tomato | 3 | Vegetable Washer | 3 spins |
| 🥦 Wash | Mushroom | 3 | Vegetable Washer | 6 spins |
| 🥦 Wash | Broccoli | 3 | Vegetable Washer | 9 spins |

### Ice Cream (×16 total — deferred)

4× each of: Strawberry, Vanilla, Chocolate, Mint Chocolate Chip.
No cooking logic. Stub out as empty data in `game_pieces.csv` until ice cream stacking is confirmed.

### Recipe Cards (×14)

Specific recipe contents pending from partners. Each card maps to a dish that requires some subset of the raw ingredients above. The screen displays only the ingredient list — cooking method per ingredient lives in the printed instruction sheet.

---

## TFT Screen Flow

The screen walks through this sequence on each round:

| # | State | Trigger | Visual |
|---|---|---|---|
| 0 | Idle | — | Waiting for recipe card |
| 1 | Recipe scanned | `RCPE` received | Transition to ingredient showcase |
| 2 | Ingredient showcase (5 s) | After (1) | White background, ingredient GIFs (assets TBD) + count |
| 3 | Pre-game countdown | After (2) | "3" → "2" → "1" |
| 4 | Game start | After (3) | "Game Start!" splash |
| 5 | Game timer (8 min) | After (4) | Timer countdown; background gradually shifts redder as time runs down |
| 6 | Last 10 s | When timer ≤ 10 s | Full fire effect under the timer |
| 7 | Bell check | `BELL` received from ESP1 | Brief "Checking…" progress bar, then ✅ or ❌ |

Asset GIFs for each ingredient will come from the art team — coordinate file naming with the Pi dev so they slot into `pi/assets/` cleanly.

---

## USB Speaker — Sound Effects

The Pi triggers each of these via the USB speaker. Reference clips provided as YouTube links — Pi dev should source clean WAV/MP3 files.

| SFX | Trigger | Reference |
|---|---|---|
| Pre-game countdown | Screen state 3 | https://youtu.be/KOoCEIwswYg |
| Last-minute alarm | Game timer ≤ 60 s (loop) | https://youtu.be/ebvtJCu33vM |
| Bell ding | On bell press | https://youtu.be/t7bxsTm4IyM |
| Menu correct (✅) | Bell check passes | https://youtu.be/qZC5gtOw3DU |
| Menu wrong (❌) | Bell check fails | https://youtu.be/2naim9F4010 |
| Pan fry SFX | Frying pan in active use (loop) | https://youtu.be/GMNFph2tn2c |
| Deep fryer SFX | Deep fryer in active use (loop) | https://youtu.be/LJwWSwZgVY0 |

---

## Hardware Outputs

**TFT screen (I2C):** Displays the screen flow above.
**USB speaker:** Plays SFX above.

---

## ESP32 #1

**Language:** Arduino C
**Hardware:** 7× RC522 RFID readers, 1× AS5600 magnetic encoder, 1× LED, 1× bell button

### RFID Readers (RC522, SPI)

All 7 readers share MOSI, MISO, SCK, and RST. Each has its own CS line.
**Time multiplexing required** — only one CS pin may be pulled low at a time. Poll readers sequentially in the main loop.

- Reader ID 0: recipe card reader → sends `RCPE` only.
- Reader ID 1: vegetable washer → sends `RFID`.
- Reader IDs 2–5: plate readers → send `RFID`.
- Reader ID 9: frying pan 1 → see toss logic below.

**Frying pan toss detection** — for Reader ID 9:
- Track last Tag UID and last detection timestamp.
- On each new detection of the same UID:
  - < 0.5s since last detection → ignore
  - ≥ 0.5s and < 5s → send `TOSS:9:DETECTED`
  - ≥ 5s → treat as fresh placement, reset state, send `RFID:9:[Tag_UID]`
- Detection of a *different* UID always resets state and sends `RFID` as normal.

### AS5600 Magnetic Encoder (I2C — fixed address 0x36)

Reads raw angle data continuously. Detects a spin when total angle change exceeds 360° within a 2-second window. Sends `SPIN:0:DETECTED`. The Pi handles all spin counting.

DIR pin (GPIO 32): tie to GND if rotation direction is irrelevant.

### Bell Button

The "submit order" button. Physically sits at the player's serving area, near the recipe card reader.

- Use `INPUT_PULLUP` mode. Button connects pin to GND when pressed.
- **Debounce in firmware** — 50ms window recommended.
- On press, send `BELL:0:PRESSED` to the Pi.

### LED

GPIO 33 — vegetable washer (LED ID 0). Activates on `LED:0:ON` from Pi.

### Command Filtering

Silently ignores any Pi command whose LED ID is not `0`.

---

## ESP32 #2

**Language:** Arduino C
**Hardware:** 6× RC522 RFID readers, 2× buttons, 1× analog input, 4× LEDs

### RFID Readers (RC522, SPI)

Same SPI sharing rules as ESP32 #1. **Time multiplexing required.**

- Reader IDs 6–8: plate readers → send `RFID`.
- Reader ID 10: frying pan 2 → see toss logic below.
- Reader IDs 11–12: deep fryer → send `RFID`.

**Frying pan toss detection** — for Reader ID 10:
- Track last Tag UID and last detection timestamp per reader.
- On each new detection of the same UID:
  - < 0.5s since last detection → ignore
  - ≥ 0.5s and < 5s → send `TOSS:10:DETECTED`
  - ≥ 5s → treat as fresh placement, reset state, send `RFID:10:[Tag_UID]`
- Detection of a *different* UID always resets state and sends `RFID` as normal.

### Buttons (deep fryer)

2 buttons, one per deep fryer station.

- Use `INPUT_PULLUP` mode. Button connects pin to GND when pressed.
- **Debounce in firmware** — 50ms window recommended.
- Sends `BTN:[ID]:PRESSED`. Pi handles all press counting and thresholds.

| Button ID | Station |
|---|---|
| 0 | Deep Fryer 1 |
| 1 | Deep Fryer 2 |

### Ice Cream Station (Analog, deferred)

GPIO 34 reads a direct voltage from the ice cream station. Sends `ANLG:0:[0-4095]`. Sensor type and voltage range TBD.

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

1. A recipe card is scanned → Pi loads required ingredients, runs screen flow.
2. Each ingredient must be placed at its correct cooking station and cooked to completion (LED on = done):
   - Vegetable washer → enough spins counted
   - Frying pan → enough valid tosses counted
   - Deep fryer → enough button presses counted
3. Cooked ingredients must be placed on plate readers (IDs 2–8).
4. Bell pressed (on ESP1) → Pi receives `BELL:0:PRESSED`, checks plate contents → if all required ingredients present and cooked, game ends with win.
5. If 8-minute timer expires before bell success, game ends with loss.

All cooking doneness resets on the reset button (on the Pi).
