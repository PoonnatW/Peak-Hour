import board
import busio
import neopixel_spi
import time

def run_test():
    print("--- DUAL STRIP COLOR TEST (Pin 38 & Pin 8) ---")
    try:
        # Initialize Base (SPI1 on Pin 38 / GPIO 20)
        print("Initializing Base Strip on Pin 38...")
        spi1 = busio.SPI(board.SCK_1, board.MOSI_1)
        base = neopixel_spi.NeoPixel_SPI(spi1, 10, brightness=0.5, auto_write=True)

        # Initialize Lid (SPI2 on Pin 28 / GPIO 1)
        print("Initializing Lid Strip on Pin 28...")
        # SCLK=D0 (Pin 27), MOSI=D1 (Pin 28)
        spi2 = busio.SPI(board.D0, board.D1)
        lid = neopixel_spi.NeoPixel_SPI(spi2, 10, brightness=0.5, auto_write=True)

        sequence = [
            ((255, 0, 0), "🔴 RED"),
            ((255, 100, 0), "🟠 ORANGE"),
            ((255, 200, 0), "🟡 YELLOW"),
            ((0, 255, 0), "🟢 GREEN"),
            ((0, 0, 255), "🔵 BLUE"),
            ((0, 0, 0), "⚫ OFF")
        ]

        for color, name in sequence:
            print(f"Switching both strips to: {name}")
            base.fill(color)
            lid.fill(color)
            time.sleep(2)

        print("\n✅ Dual Strip test complete!")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("Make sure you added 'dtoverlay=spi1-1cs' and 'dtoverlay=spi3-1cs' to config.txt")

if __name__ == "__main__":
    run_test()
