import board
import busio
import neopixel_spi
import time

def run_test():
    print("--- AUTOMATIC COLOR CYCLE TEST ---")
    try:
        # Initialize SPI1 for GPIO 20 (Pin 38)
        spi = busio.SPI(board.SCK_1, board.MOSI_1)
        pixels = neopixel_spi.NeoPixel_SPI(spi, 20, brightness=0.5, auto_write=True)

        # (R, G, B) colors
        sequence = [
            ((255, 0, 0), "🔴 RED (Raw/Cooking)"),
            ((255, 100, 0), "🟠 ORANGE (Medium)"),
            ((255, 200, 0), "🟡 YELLOW (Almost Done)"),
            ((0, 255, 0), "🟢 GREEN (Ready!)"),
            ((0, 0, 255), "🔵 BLUE (Processing/Spinning)"),
            ((0, 0, 0), "⚫ OFF")
        ]

        for color, name in sequence:
            print(f"Setting LEDs to: {name}")
            pixels.fill(color)
            time.sleep(2) # Change every 2 seconds

        print("\n✅ Automatic test complete!")

    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    run_test()
