import time
import signal
import sys
from gpiozero import Button

from serial_handler import SerialHandler
from game_logic import GameLogic
from display import DisplayService

def main():
    print("Starting Peak Hour Game Controller...")
    
    display = DisplayService()
    
    # Init serial handler
    serial_handler = SerialHandler(baudrate=115200)
    
    # Init game logic
    logic = GameLogic(serial_handler, display)
    
    # Wire serial callback to logic.process_message
    serial_handler.start_listening(logic.process_message)
    
    # Setup physical buttons based on docs/pinout.md
    # Bell = GPIO 27, Reset = GPIO 22
    try:
        bell_btn = Button(27, pull_up=True, bounce_time=0.1)
        reset_btn = Button(22, pull_up=True, bounce_time=0.1)
        
        bell_btn.when_pressed = logic.bell_pressed
        reset_btn.when_pressed = logic.reset_pressed
        print("Hardware buttons initialized.")
    except Exception as e:
        print(f"Warning: Could not initialize GPIO buttons: {e}")
        print("Are you running this on a Raspberry Pi?")
        print("Continuing without physical buttons...")

    # Keep alive loop
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        serial_handler.stop()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()