import time
from gpiozero import OutputDevice

def test_pins():
    print("Scanning Pi 5 for unlocked GPIO pins...")
    
    # Standard GPIO pins on the Pi header
    test_pins = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
    
    free_pins = []
    locked_pins = []
    
    for pin in test_pins:
        try:
            device = OutputDevice(pin)
            device.close()
            free_pins.append(pin)
        except Exception as e:
            locked_pins.append((pin, str(e)))
            
    print("\n--- RESULTS ---")
    print(f"✅ FREE PINS: {free_pins}")
    print("\n❌ LOCKED PINS:")
    for pin, error in locked_pins:
        print(f"  GPIO {pin}: {error}")

if __name__ == "__main__":
    test_pins()
