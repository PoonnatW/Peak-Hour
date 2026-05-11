import board
import busio
import neopixel_spi
import time

def run_test():
    print("--- CHAINED STRIP COLOR TEST (SPI1 - 20 Pixels) ---")
    try:
        # Initialize SPI1 for GPIO 20 (Pin 38)
        print("Initializing Chained Strip on Pin 38...")
        spi = busio.SPI(board.SCK_1, board.MOSI_1)
        pixels = neopixel_spi.NeoPixel_SPI(spi, 20, brightness=0.5, auto_write=True)

        sequence = [
            ((255, 0, 0), "🔴 RED"),
            ((255, 100, 0), "🟠 ORANGE"),
            ((255, 200, 0), "🟡 YELLOW"),
            ((0, 255, 0), "🟢 GREEN"),
            ((0, 0, 255), "🔵 BLUE"),
            ((0, 0, 0), "⚫ OFF")
        ]

        for color, name in sequence:
            print(f"Switching all 20 LEDs to: {name}")
            pixels.fill(color)
            time.sleep(2)

        print("\n✅ Chained Strip test complete!")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("Make sure you added 'dtoverlay=spi1-1cs' and 'dtoverlay=spi3-1cs' to config.txt")

if __name__ == "__main__":
    run_test()
