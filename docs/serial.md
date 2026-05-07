# Serial Message Protocol

All communication between the Raspberry Pi and each ESP32 uses plain-text messages over USB serial.

## Connection Settings

| Setting | Value |
|---|---|
| Baud rate | `115200` |
| Message terminator | `\n` (newline) |
| Format | `TYPE:ID:VALUE\n` |
| Error handling | Silently discard malformed messages |

---

## ESP32 → Pi (sensor reports)

| Type | Format | Example | Notes |
|---|---|---|---|
| `RFID` | `RFID:[Reader_ID]:[Tag_UID]` | `RFID:3:A1B2C3D4` | Game piece detected on any RFID reader |
| `TOSS` | `TOSS:[Reader_ID]:DETECTED` | `TOSS:9:DETECTED` | Valid frying pan toss — see toss logic below |
| `BTN` | `BTN:[Button_ID]:PRESSED` | `BTN:0:PRESSED` | Debounced deep fryer button press (sent by ESP2) |
| `BELL` | `BELL:[Bell_ID]:PRESSED` | `BELL:0:PRESSED` | Bell button pressed (sent by ESP1) |
| `SPIN` | `SPIN:[Encoder_ID]:DETECTED` | `SPIN:0:DETECTED` | Full rotation on AS5600 (>360° within 2 seconds) |
| `ANLG` | `ANLG:[Sensor_ID]:[0-4095]` | `ANLG:0:2048` | Raw ADC value from ice cream station (deferred) |
| `RCPE` | `RCPE:[Reader_ID]:[Tag_UID]` | `RCPE:0:FF3C12AA` | Recipe card placed on the recipe reader |

> **RCPE note:** The ESP32 sends the raw Tag UID only — it does not know the dish name. The Pi maps the UID to a recipe name using `recipes.csv`.

### Frying pan toss logic (Reader 9 on ESP32 #1, Reader 10 on ESP32 #2)

Each board runs the same toss logic independently for its own frying pan reader. On each new detection of the same tag:

- **< 0.5s** since last detection → ignore (tag hasn't left, continuous read)
- **≥ 0.5s and < 5s** since last detection → valid toss, send `TOSS:[Reader_ID]:DETECTED`
- **≥ 5s** since last detection → treat as fresh placement, reset state, send `RFID:[Reader_ID]:[Tag_UID]` as normal

The Pi receives `TOSS` events and increments the toss counter for the ingredient at that station. No timing logic is needed on the Pi side for the frying pan.

---

## Pi → ESP32 (commands)

| Type | Format | Example | Notes |
|---|---|---|---|
| `LED` | `LED:[LED_ID]:ON` or `LED:[LED_ID]:OFF` | `LED:1:ON` | Turn a station LED on or off |

> **Filtering note:** Each ESP32 silently ignores any command whose ID does not correspond to hardware on that board. No acknowledgement is sent.

---

## ID Reference

| ID Type | Owner | Notes |
|---|---|---|
| Reader ID 0 | ESP32 #1 | Recipe card reader (sends `RCPE` only) |
| Reader ID 1 | ESP32 #1 | Vegetable washer |
| Reader IDs 2–5 | ESP32 #1 | Plate readers |
| Reader ID 9 | ESP32 #1 | Frying Pan 1 (sends `TOSS` for valid tosses) |
| Reader IDs 6–8 | ESP32 #2 | Plate readers |
| Reader ID 10 | ESP32 #2 | Frying Pan 2 (sends `TOSS` for valid tosses) |
| Reader IDs 11–12 | ESP32 #2 | Deep fryer |
| Button IDs 0–1 | ESP32 #2 | Deep Fryer 1 and 2 |
| Bell ID 0 | ESP32 #1 | Bell button (submit order) |
| LED ID 0 | ESP32 #1 | Vegetable washer |
| LED IDs 1–4 | ESP32 #2 | Frying Pan 1, Frying Pan 2, Deep Fryer 1, Deep Fryer 2 |
| Encoder ID 0 | ESP32 #1 | AS5600 on vegetable washer |
| Analog Sensor ID 0 | ESP32 #2 | Ice cream station (deferred) |

Full GPIO assignments in `docs/pinout.md`.
