import csv
import os
import time
import config

class GamePiece:
    def __init__(self, uid, name):
        self.uid = uid
        self.name = name
        self.reset_doneness()
        
    def reset_doneness(self):
        self.operations = {"spins": 0, "tosses": 0, "presses": 0}
        
    def add_operation(self, op_type, amount=1):
        if op_type in self.operations:
            self.operations[op_type] += amount

    def is_cooked(self):
        if self.name not in config.THRESHOLDS:
            return False
            
        reqs = config.THRESHOLDS[self.name]
        return (
            self.operations["spins"] >= reqs.get("spins", 0) and
            self.operations["tosses"] >= reqs.get("tosses", 0) and
            self.operations["presses"] >= reqs.get("presses", 0)
        )

class GameLogic:
    def __init__(self, serial_handler, display, hardware=None):
        self.serial = serial_handler
        self.display = display
        self.hardware = hardware
        if self.hardware:
            self.hardware.set_button_callbacks(
                base_cb=self.hardware_button_pressed,
                lid_cb=self.lid_button_pressed
            )
        self.consumed_spins = 0
        self.last_angle = None
        self.pieces_db = {}
        self.recipes_db = {}
        self.load_data()
        
        self.active_recipe = None
        self.station_contents = {} # station_name -> GamePiece
        self.plate_contents = {}   # plate reader id -> GamePiece
        self.ice_cream_val = 0
        
        self.state = "idle"
        self.state_time = time.time()
        
    def load_data(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        pieces_path = os.path.join(base_dir, "game_pieces.csv")
        if os.path.exists(pieces_path):
            with open(pieces_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.pieces_db[row['UID']] = row['Ingredient']
                    
        recipes_path = os.path.join(base_dir, "recipes.csv")
        if os.path.exists(recipes_path):
            with open(recipes_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    reqs = row['Ingredients'].split('|')
                    self.recipes_db[row['UID']] = {
                        "name": row['DishName'],
                        "ingredients": reqs
                    }

    def process_message(self, msg_type, msg_id, value):
        # msg_id might be string, try handle as int if possible
        try:
            reader_id = int(msg_id)
        except ValueError:
            reader_id = msg_id

        if msg_type == "RCPE":
            self.set_recipe(value)
            
        elif msg_type == "RFID":
            # Tag arrived at a station or plate
            if value in self.pieces_db:
                piece_name = self.pieces_db[value]
                # We reuse GamePiece instances if they exist, or create new
                piece = self._get_or_create_piece(value, piece_name)
                
                # If reader is 2-8 it's a plate
                if isinstance(reader_id, int) and 2 <= reader_id <= 8:
                    self.plate_contents[reader_id] = piece
                    piece.location = f"Plate {reader_id}"
                # If reader is in stations
                elif reader_id in config.STATIONS:
                    station_name = config.STATIONS[reader_id]
                    self.station_contents[station_name] = piece
                    piece.location = station_name
                    
        elif msg_type == "SPIN":
            # SPINS happen at Vegetable Washer
            self._handle_operation("Vegetable Washer", "spins")
            
        elif msg_type == "TOSS":
            if reader_id in config.STATIONS:
                station_name = config.STATIONS[reader_id]
                self._handle_operation(station_name, "tosses")
                
        elif msg_type == "BTN":
            # buttons are 0 or 1 mapping to Deep Fryer 1 or 2
            # ID mapping based on workplan docs:
            # BTN 0 -> Deep Fryer 1 (Station ID 11)
            # BTN 1 -> Deep Fryer 2 (Station ID 12)
            station_map = {0: "Deep Fryer 1", 1: "Deep Fryer 2"}
            if reader_id in station_map:
                self._handle_operation(station_map[reader_id], "presses")
                
        elif msg_type == "ANLG":
            # Analog value for ice cream
            try:
                self.ice_cream_val = int(value)
            except:
                pass
                
        elif msg_type == "BELL":
            if self.state == "playing":
                self.bell_pressed()
                
    def _get_or_create_piece(self, uid, name):
        # Look for existing piece to maintain doneness state
        for piece in self.station_contents.values():
            if piece.uid == uid:
                return piece
        for piece in self.plate_contents.values():
            if piece.uid == uid:
                return piece
        return GamePiece(uid, name)

    def _handle_operation(self, station_name, op_type):
        # Get all pieces at this station (handling multiple pieces if needed)
        pieces_to_cook = []
        if station_name in self.station_contents:
            # We check if it's a list or a single piece
            content = self.station_contents[station_name]
            if isinstance(content, list):
                pieces_to_cook = content
            else:
                pieces_to_cook = [content]
                
        for piece in pieces_to_cook:
            piece.add_operation(op_type)
            print(f"[LOGIC] {piece.name} at {station_name}: {op_type}={piece.operations[op_type]}")
            
            # Update Neopixels for food doneness
            req = config.THRESHOLDS.get(piece.name, {}).get(op_type, 0)
            if self.hardware and req > 0:
                progress = piece.operations[op_type] / req
                color = (255, 0, 0) # Red (0-49%)
                if progress >= 1.0: 
                    color = (0, 255, 0) # Green (100%)
                elif progress >= 0.5: 
                    color = (255, 80, 0) # Orange (50-99%)
                
                # Assign to correct strip
                if station_name == "Vegetable Washer":
                    self.hardware.set_led_color(0, color, target="lid")
                elif station_name in config.LEDS:
                    led_idx = config.LEDS[station_name]
                    self.hardware.set_led_color(led_idx, color, target="base")

            # Check if threshold met
            if req > 0 and piece.operations[op_type] == req:
                # Play audio cue for Vegetable Washer when exactly done
                if station_name == "Vegetable Washer":
                    self.display.play_sound("bell") # Use the bell sound for washer

            if req > 0 and piece.operations[op_type] >= req:
                # Turn on LED for this station
                if station_name in config.LEDS:
                    led_id = config.LEDS[station_name]
                    self.serial.send_command("LED", led_id, "ON")

    def set_recipe(self, uid):
        if self.state != "idle":
            return
        if uid in self.recipes_db:
            recipe = self.recipes_db[uid]
            self.active_recipe = recipe
            self.change_state("recipe_scanned")
            self.display.show_recipe(recipe["name"], recipe["ingredients"])
            
            # Clear all current doneness for a fresh start 
            self._reset_all_doneness()
            
            # --- AUTO-POPULATE STATIONS FOR HARDWARE TESTING ---
            # This allows you to test sensors without scanning ingredient tags
            print(f"[DEBUG] Auto-populating stations for {recipe['name']}...")
            for ing_name in recipe["ingredients"]:
                if not ing_name.strip(): continue
                
                # Create a temporary piece for this ingredient
                piece = GamePiece(f"TMP_{ing_name}", ing_name)
                
                # Find the right station for it based on thresholds
                station_name = None
                if ing_name in config.THRESHOLDS:
                    reqs = config.THRESHOLDS[ing_name]
                    if reqs.get("spins", 0) > 0:
                        station_name = "Vegetable Washer"
                    elif reqs.get("tosses", 0) > 0:
                        station_name = "Frying Pan 1"
                    elif reqs.get("presses", 0) > 0:
                        station_name = "Deep Fryer 1"
                
                if station_name:
                    if station_name not in self.station_contents:
                        self.station_contents[station_name] = []
                    self.station_contents[station_name].append(piece)
            # ---------------------------------------------------

    def _reset_all_doneness(self):
        self.station_contents = {}
        self.plate_contents = {}
        # Turn off all LEDs
        for led_id in config.LEDS.values():
            self.serial.send_command("LED", led_id, "OFF")
        if self.hardware:
            self.hardware.clear_leds()

    def reset_pressed(self):
        self._reset_all_doneness()
        self.active_recipe = None
        self.display.show_recipe("None", [])
        self.change_state("idle")

    def change_state(self, new_state):
        self.state = new_state
        self.state_time = time.time()
        print(f"[LOGIC] State changed to: {new_state}")

    def hardware_button_pressed(self):
        # Base Button (GPIO 6) -> Progress all food in deep fryers
        for station in ["Deep Fryer 1", "Deep Fryer 2"]:
            if station in self.station_contents:
                self._handle_operation(station, "presses")

    def lid_button_pressed(self):
        # Lid Button (GPIO 5) -> Confirm Order / Start Countdown
        if self.state == "showcase":
            print("[LOGIC] Order Confirmed! Starting countdown...")
            self.change_state("countdown")
            self.display.play_sound("countdown")
        else:
            print("[LOGIC] Lid Button Pressed (GPIO 5)")

    def update(self):
        # Update AS5600 for Vegetable Washer via hardware controller
        if self.hardware:
            self.hardware.update()
            while self.hardware.spins > self.consumed_spins:
                print(f"[LOGIC] Consuming spin {self.consumed_spins + 1} from hardware")
                self._handle_operation("Vegetable Washer", "spins")
                self.consumed_spins += 1

        now = time.time()
        elapsed = now - self.state_time
        
        if self.state == "recipe_scanned":
            if elapsed > 1:
                self.change_state("showcase")
                # display showcase implementation is pending art team
        elif self.state == "showcase":
            # Now waits for manual Lid Button press to proceed to countdown
            pass
        elif self.state == "countdown":
            if elapsed > 3:
                self.change_state("playing")
                # display game start splash is pending
        elif self.state == "playing":
            remaining = 480 - elapsed
            if remaining <= 0:
                self.display.show_error("Time's up!")
                self.display.play_sound("error")
                self.change_state("lose")
            elif remaining <= 60 and remaining + 1 > 60:
                self.display.play_sound("alarm")
        elif self.state in ["win", "lose"]:
            if elapsed > 5:
                self.reset_pressed()
                
        # Collect status for display
        piece_data = []
        if self.active_recipe:
            # We look for all pieces that match our recipe requirements
            required = self.active_recipe["ingredients"]
            all_pieces = list(self.plate_contents.values())
            for content in self.station_contents.values():
                if isinstance(content, list): all_pieces.extend(content)
                else: all_pieces.append(content)
            
            # Map them for display
            for ing_name in required:
                if not ing_name.strip(): continue
                # Find the piece for this ingredient
                match = next((p for p in all_pieces if p.name == ing_name), None)
                reqs = config.THRESHOLDS.get(ing_name, {})
                
                if match:
                    piece_data.append({
                        "name": match.name,
                        "spins": match.operations["spins"],
                        "spins_req": reqs.get("spins", 0),
                        "tosses": match.operations["tosses"],
                        "tosses_req": reqs.get("tosses", 0),
                        "presses": match.operations["presses"],
                        "presses_req": reqs.get("presses", 0)
                    })
                else:
                    piece_data.append({
                        "name": ing_name, 
                        "spins": 0, "spins_req": reqs.get("spins", 0),
                        "tosses": 0, "tosses_req": reqs.get("tosses", 0),
                        "presses": 0, "presses_req": reqs.get("presses", 0)
                    })

        # Update the graphical display
        self.display.update(self.state, elapsed, piece_data=piece_data)

    def bell_pressed(self):
        self.change_state("checking")
        self.display.play_sound("bell")
        
        if not self.active_recipe:
            self.display.show_error("No active recipe!")
            self.display.play_sound("error")
            self.change_state("lose")
            return
            
        # Ignore empty ingredient requirement if recipe is just a stub
        required = [ing for ing in self.active_recipe["ingredients"] if ing.strip()]
        
        # Check plate contents AND station contents (for manual testing)
        all_available_pieces = list(self.plate_contents.values())
        for content in self.station_contents.values():
            if isinstance(content, list):
                all_available_pieces.extend(content)
            else:
                all_available_pieces.append(content)
        
        for piece in all_available_pieces:
            if piece.name in required:
                if piece.is_cooked():
                    required.remove(piece.name)
                else:
                    self.display.show_error(f"{piece.name} is not fully cooked!")
                    self.display.play_sound("error")
                    self.change_state("lose")
                    return
                    
        if len(required) > 0:
            self.display.show_error(f"Missing ingredients on plates: {', '.join(required)}")
            self.display.play_sound("error")
            self.change_state("lose")
            return
            
        # Ice cream check (deferred for now, but keeping error block as stub)
        if self.ice_cream_val > 0 and (self.ice_cream_val < config.ICE_CREAM_MIN or self.ice_cream_val > config.ICE_CREAM_MAX):
             self.display.show_error("Ice cream station not complete/in range!")
             self.display.play_sound("error")
             self.change_state("lose")
             return
             
        # All good!
        self.display.play_sound("win")
        self.change_state("win")