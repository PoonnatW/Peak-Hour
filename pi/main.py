import time
import signal
import sys
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
    
    # Init game logic
    logic = GameLogic(serial_handler, display, hardware)
    
    # Wire serial callback to logic.process_message
    serial_handler.start_listening(logic.process_message)
    
    # Setup hardware button from controller
    hardware.set_button_callback(logic.hardware_button_pressed)
    
    # Setup physical buttons based on docs/pinout.md
    # Reset = GPIO 22 (Bell moved to ESP1)
    try:
        reset_btn = Button(22, pull_up=True, bounce_time=0.1)
        reset_btn.when_pressed = logic.reset_pressed
        print("Hardware buttons initialized.")
    except Exception as e:
        print(f"Warning: Could not initialize GPIO buttons: {e}")
        print("Are you running this on a Raspberry Pi?")
        print("Continuing without physical buttons...")

    # Keep alive loop
    try:
        import pygame
        while True:
            # Handle Pygame Events (Mouse clicks for debugging)
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    if logic.state == "idle":
                        if display.debug_btn_rect.collidepoint(pos):
                            print("[DEBUG] Manual Start Clicked")
                            logic.process_message("RCPE", "0", "0000")
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
                    if logic.state == "playing":
                        if event.key == pygame.K_s: logic.process_message("SPIN", "1", "1")
                        elif event.key == pygame.K_t: logic.process_message("TOSS", "9", "1")
                        elif event.key == pygame.K_p: logic.process_message("BTN", "0", "1")
                        elif event.key == pygame.K_b: logic.process_message("BELL", "0", "1")
                
                if event.type == pygame.QUIT:
                    sys.exit()

            logic.update()
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        serial_handler.stop()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()