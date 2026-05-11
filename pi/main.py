import time
import signal
import sys

# Initialize TFT Screen FIRST to avoid GPIO allocation conflicts on Pi 5
try:
    from tft_screen import setup_tft, draw_game_state
    tft_device = setup_tft()
except Exception as e:
    print(f"Warning: TFT Setup failed early: {e}")
    tft_device = None

from gpiozero import Button

from serial_handler import SerialHandler
from game_logic import GameLogic
from display import DisplayService
from hardware_controller import HardwareController

def main():
    print("Starting Peak Hour Game Controller...")
    display = DisplayService()
    
    # Init serial handler
    serial_handler = SerialHandler(baudrate=115200)
    
    # Init hardware
    hardware = HardwareController()
    
    # Init game logic (handles hardware button callbacks)
    logic = GameLogic(serial_handler, display, hardware)
    
    # Wire serial callback to logic.process_message
    serial_handler.start_listening(logic.process_message)
    
    # Setup physical buttons based on docs/pinout.md
    # Reset = GPIO 4 (Moved from 22 due to TFT conflict)
    try:
        reset_btn = Button(4, pull_up=True, bounce_time=0.1)
        reset_btn.when_pressed = logic.reset_pressed
        print("Hardware buttons initialized (Reset on GPIO 4).")
    except Exception as e:
        print(f"Warning: Could not initialize GPIO buttons: {e}")
        print("Are you running this on a Raspberry Pi?")
        print("Continuing without physical buttons...")

    # Keep alive loop
    try:
        import pygame
        last_tft_update = time.time()
        while True:
            # Handle Pygame Events (Mouse clicks for debugging)
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    print(f"[DEBUG] Click at {pos}")
                    if logic.state == "idle":
                        if display.debug_btn_rect.collidepoint(pos):
                            import random
                            recipe_ids = list(logic.recipes_db.keys())
                            if recipe_ids:
                                rid = random.choice(recipe_ids)
                                print(f"[DEBUG] Manual Start Clicked - Loading {rid}")
                                logic.process_message("RCPE", "0", rid)
                            else:
                                print("[DEBUG] No recipes found in database!")
                    elif logic.state == "showcase":
                        # Fallback: Click anywhere to confirm if button is broken
                        print("[DEBUG] Manual Confirm Clicked")
                        logic.lid_button_pressed()
                    elif logic.state == "playing":
                        if display.btn_spin.collidepoint(pos):
                            logic.process_message("SPIN", "1", "1") # ID 1 = Vegetable Washer
                        elif display.btn_toss.collidepoint(pos):
                            logic.process_message("TOSS", "9", "1") # ID 9 = Frying Pan
                        elif display.btn_press.collidepoint(pos):
                            logic.process_message("BTN", "0", "1")  # ID 0 = Deep Fryer
                        elif display.btn_bell.collidepoint(pos):
                            logic.process_message("BELL", "0", "1")
                
                # Keyboard shortcuts for quick debugging
                if event.type == pygame.KEYDOWN:
                    if logic.state == "showcase":
                        if event.key == pygame.K_RETURN: logic.lid_button_pressed()
                    elif logic.state == "playing":
                        if event.key == pygame.K_s: logic.process_message("SPIN", "1", "1")
                        elif event.key == pygame.K_t: logic.process_message("TOSS", "9", "1")
                        elif event.key == pygame.K_p: logic.process_message("BTN", "0", "1")
                        elif event.key == pygame.K_b: logic.process_message("BELL", "0", "1")
                
                if event.type == pygame.QUIT:
                    sys.exit()

            logic.update()
            
            # Update TFT Screen periodically (5 FPS to avoid lagging the game loop)
            current_time = time.time()
            if current_time - last_tft_update > 0.2:
                if tft_device:
                    draw_game_state(tft_device, logic)
                last_tft_update = current_time
                
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        serial_handler.stop()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()