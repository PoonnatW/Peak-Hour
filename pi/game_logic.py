import csv
import os
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
    def __init__(self, serial_handler, display):
        self.serial = serial_handler
        self.display = display
        
        self.pieces_db = {}
        self.recipes_db = {}
        self.load_data()
        
        self.active_recipe = None
        self.station_contents = {} # station_name -> GamePiece
        self.plate_contents = {}   # plate reader id -> GamePiece
        self.ice_cream_val = 0
        
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
                
                # If reader is 0-6 it's a plate
                if isinstance(reader_id, int) and 0 <= reader_id <= 6:
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
        if station_name in self.station_contents:
            piece = self.station_contents[station_name]
            piece.add_operation(op_type)
            # Check if threshold met
            req = config.THRESHOLDS.get(piece.name, {}).get(op_type, 0)
            if req > 0 and piece.operations[op_type] >= req:
                # Turn on LED for this station
                if station_name in config.LEDS:
                    led_id = config.LEDS[station_name]
                    self.serial.send_command("LED", led_id, "ON")

    def set_recipe(self, uid):
        if uid in self.recipes_db:
            recipe = self.recipes_db[uid]
            self.active_recipe = recipe
            self.display.show_recipe(recipe["name"], recipe["ingredients"])
            # Clear all current doneness for a fresh start 
            self._reset_all_doneness()

    def _reset_all_doneness(self):
        for piece in self.station_contents.values():
            piece.reset_doneness()
        for piece in self.plate_contents.values():
            piece.reset_doneness()
        # Turn off all LEDs
        for led_id in config.LEDS.values():
            self.serial.send_command("LED", led_id, "OFF")

    def reset_pressed(self):
        self._reset_all_doneness()
        self.active_recipe = None
        self.display.show_recipe("None", [])

    def bell_pressed(self):
        self.serial.send_command("BELL", 0, "PRESSED")
        
        if not self.active_recipe:
            self.display.show_error("No active recipe!")
            self.display.play_sound("error")
            return
            
        required = self.active_recipe["ingredients"].copy()
        
        # Check plate contents
        for piece in self.plate_contents.values():
            if piece.name in required:
                if piece.is_cooked():
                    required.remove(piece.name)
                else:
                    self.display.show_error(f"{piece.name} is not fully cooked!")
                    self.display.play_sound("error")
                    return
                    
        if len(required) > 0:
            self.display.show_error(f"Missing ingredients on plates: {', '.join(required)}")
            self.display.play_sound("error")
            return
            
        # Check ice cream
        if self.ice_cream_val < config.ICE_CREAM_MIN or self.ice_cream_val > config.ICE_CREAM_MAX:
             self.display.show_error("Ice cream station not complete/in range!")
             self.display.play_sound("error")
             return
             
        # All good!
        self.display.show_win()
        self.display.play_sound("win")