import board
import busio
import neopixel_spi
import time

def turn_on():
    print("Attempting to light up LEDs on SPI1 (GPIO 20 / Pin 38)...")
    try:
        # Initialize SPI1
        spi = busio.SPI(board.SCK_1, board.MOSI_1)
        
        # Initialize 20 pixels (Base + Lid)
        # auto_write=True means they light up immediately
        pixels = neopixel_spi.NeoPixel_SPI(spi, 20, brightness=0.5, auto_write=True)
        
        # Fill with bright white
        pixels.fill((255, 255, 255))
        
        print("✅ SUCCESS: LEDs should be Solid White now.")
        print("Keep this script running to keep them on. Press Ctrl+C to exit.")
        
        while True:
            time.sleep(1)
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("Make sure you are running with 'sudo' and 'dtoverlay=spi1-1cs' is in config.txt")

if __name__ == "__main__":
    turn_on()
