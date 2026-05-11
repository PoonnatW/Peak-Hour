import board
import busio
import neopixel_spi

def turn_off():
    print("Turning off all LEDs on SPI1...")
    try:
        # Initialize SPI1
        spi = busio.SPI(board.SCK_1, board.MOSI_1)
        
        # Initialize 20 pixels
        pixels = neopixel_spi.NeoPixel_SPI(spi, 20, auto_write=True)
        
        # Set all to black (off)
        pixels.fill((0, 0, 0))
        
        print("✅ LEDs are now OFF.")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    turn_off()
