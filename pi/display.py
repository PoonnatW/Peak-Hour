class DisplayService:
    def __init__(self):
        print("[DISPLAY] Initializing TFT screen and USB speaker...")

    def show_recipe(self, recipe_name, required_ingredients):
        print(f"\n[DISPLAY] === NEW RECIPE: {recipe_name} ===")
        print(f"[DISPLAY] Requirements: {', '.join(required_ingredients)}")
        print("[DISPLAY] ================================\n")

    def show_win(self):
        print("\n[DISPLAY] ********************************")
        print("[DISPLAY] ***      ORDER COMPLETE!     ***")
        print("[DISPLAY] ********************************\n")

    def show_error(self, message):
        print(f"\n[DISPLAY] ERROR: {message}\n")

    def play_sound(self, sound_type):
        if sound_type == "win":
            print("[AUDIO] Playing win jingle!")
        elif sound_type == "error":
            print("[AUDIO] Playing error buzz!")
        else:
            print(f"[AUDIO] Playing unknown sound: {sound_type}")