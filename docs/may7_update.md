# Update — May 7

This file tracks changes from the previous workplan iteration. **Both devs should read Part 1**; the **Pi dev should treat Part 2 as their working backlog** for this iteration.

The full updated spec lives in `workplan.md`, `serial.md`, and `pinout.md`. This file is a delta — it does not duplicate the full spec, just the changes and the remaining work.

---

## Part 1 — Hardware Realization

### Reader ID renumbering

Reader IDs have been reordered to put special-purpose readers first:

| New ID | Old ID | Function | Board (was) | Board (now) |
|---|---|---|---|---|
| 0 | 8 | Recipe card | ESP1 | ESP1 |
| 1 | 7 | Vegetable washer | ESP1 | ESP1 |
| 2 | 0 | Plate | ESP1 | ESP1 |
| 3 | 1 | Plate | ESP1 | ESP1 |
| 4 | 2 | Plate | ESP1 | ESP1 |
| 5 | 3 | Plate | ESP1 | ESP1 |
| 6 | 4 | Plate | ESP1 | **ESP2** (moved) |
| 7 | 5 | Plate | ESP1 | **ESP2** (moved) |
| 8 | 6 | Plate | ESP1 | **ESP2** (moved) |
| 9 | 9 | Frying Pan 1 | ESP2 | **ESP1** (moved) |
| 10 | 10 | Frying Pan 2 | ESP2 | ESP2 |
| 11 | 11 | Deep Fryer 1 | ESP2 | ESP2 |
| 12 | 12 | Deep Fryer 2 | ESP2 | ESP2 |

### Bell button moved to ESP1

Previously wired to Pi GPIO 27, the bell now lives on ESP32 #1 (GPIO 14). When pressed, ESP1 sends `BELL:0:PRESSED` to the Pi. The Pi GPIO 27 pin is now free.

This is a small but important protocol change: `BELL` was previously a Pi → ESP broadcast (which had no clear purpose). It is now an ESP → Pi event only.

### Deep fryer buttons stay on ESP2

The 2 deep fryer buttons remain on ESP32 #2, alongside the deep fryer RFID readers. They use GPIO 21 and 22 (which were previously the I2C pins from earlier drafts — ESP2 has no I2C peripherals so these pins are free for digital input).

### AS5600 encoder on ESP1 (unchanged)

The rotational encoder for the vegetable washer continues to live on ESP32 #1 (I2C on GPIO 21/22, DIR on GPIO 32). Calling this out explicitly since it was raised in the latest spec confirmation.

### Board responsibility split

**ESP32 #1** (was 9 RFIDs): 7 RFIDs (recipe + veg washer + 4 plates + **frying pan 1**) + AS5600 + veg washer LED + bell button.

**ESP32 #2** (was 4 RFIDs): 6 RFIDs (3 plates + **frying pan 2** + 2 deep fryers) + 4 LEDs + 2 deep fryer buttons + analog (ice cream).

### Ice cream deferred

The team is unsure whether ice cream stacking will ship. The analog input on ESP2 (GPIO 34) is still wired and the protocol still accepts `ANLG` messages, but no current recipe consumes them. Add 16 ice cream entries as empty stubs in `game_pieces.csv`. No cooking logic needed.

### Reference docs

- Updated GPIO assignments → `pinout.md`
- Updated message reference → `serial.md`
- Updated full spec → `workplan.md`

---

## Part 2 — Pi Dev TODO

Tasks grouped by area. Format is markdown checkboxes — tick them in PRs as you go, or move them into GitHub issues, whatever you prefer. Top-level items are deliverables; sub-items are acceptance criteria.

### Data files

- [ ] Build `pi/game_pieces.csv` — 30 raw ingredients + 16 ice cream stubs
  - 30 raw entries with their UID and name
  - 16 ice cream entries with empty / placeholder cooking data
- [ ] Build `pi/recipes.csv` — 14 recipe cards
  - Recipe contents pending from partners — leave as 14 stub rows for now, fill as info arrives
  - Format: `RecipeUID, DishName, Ingredient1|Ingredient2|...`
- [ ] Encode cooking thresholds in `pi/config.py`:
  ```python
  COOKING_THRESHOLDS = {
      # Frying pan (toss count)
      "Salmon":       4,
      "Beef Steak":   6,
      "Chicken":      8,
      # Deep fryer (press count)
      "French Fries": 16,
      "Onion Rings":  8,
      # Vegetable washer (spin count)
      "Tomato":       3,
      "Mushroom":     6,
      "Broccoli":     9,
  }
  ```
- [ ] Update `STATIONS` map in `config.py` to match the new reader IDs:
  ```python
  STATIONS = {
      0: "Recipe Card",
      1: "Vegetable Washer",
      2: "Plate", 3: "Plate", 4: "Plate", 5: "Plate",
      6: "Plate", 7: "Plate", 8: "Plate",
      9: "Frying Pan", 10: "Frying Pan",
      11: "Deep Fryer", 12: "Deep Fryer",
  }
  ```

### Bell handler refactor

The bell is no longer a Pi GPIO input — it now arrives as a serial message.

- [ ] Remove the GPIO 27 bell button code path on the Pi
- [ ] Add `BELL:[ID]:PRESSED` handling to the serial parser
- [ ] Wire it into the same check-plate logic that the GPIO version triggered
- [ ] Pi GPIO 27 is now free — leave unconfigured

### TFT screen flow

Full spec in `workplan.md` § *TFT Screen Flow*. Implement the state machine that drives this.

- [ ] **Idle state** — waiting for `RCPE`
- [ ] **Ingredient showcase** (5 s) — white background, ingredient GIFs + counts
  - Coordinate asset filenames with art team (`pi/assets/<ingredient>.gif`)
- [ ] **Pre-game countdown** (3 → 2 → 1)
- [ ] **"Game Start!"** splash
- [ ] **Game timer** (8 min) — background gradient shifts redder over time
- [ ] **Last 10 s effect** — fire under the timer
- [ ] **Bell check overlay** — "Checking…" progress bar → ✅ or ❌

### Sound effects

Full spec in `workplan.md` § *USB Speaker — Sound Effects*. Source from the YouTube refs as clean WAV/MP3 files.

- [ ] Pre-game countdown
- [ ] Last-minute alarm (loops while timer ≤ 60 s)
- [ ] Bell ding (on bell press)
- [ ] Menu correct (✅)
- [ ] Menu wrong (❌)
- [ ] Pan fry SFX (loops while frying pan station active)
- [ ] Deep fryer SFX (loops while deep fryer station active)

### Game state machine

- [ ] Implement: `idle → recipe_scanned → showcase → countdown → playing → checking → win|lose → idle`
- [ ] 8-minute timer starts on "Game Start!" — if it hits 0 before a successful bell check, transition to `lose`
- [ ] Reset button always returns to `idle` and clears all counters/LEDs

### Bell handler logic

- [ ] On `BELL:0:PRESSED` from ESP1, check all plate readers (IDs 2–8) for required cooked ingredients
- [ ] Match against active recipe's ingredient list
- [ ] Trigger ✅ or ❌ flow accordingly
