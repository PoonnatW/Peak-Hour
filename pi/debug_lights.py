import board
import busio
import neopixel_spi
import time

def test_bus(name, spi, num_pixels=20):
    print(f"--- Testing {name} ---")
    try:
        pixels = neopixel_spi.NeoPixel_SPI(spi, num_pixels, brightness=0.5, auto_write=True)
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)]
        for color in colors:
            print(f"  Setting to {color}...")
            pixels.fill(color)
            time.sleep(1)
        pixels.fill((0, 0, 0))
        print(f"✅ {name} test sequence finished.")
        return True
    except Exception as e:
        print(f"❌ {name} failed: {e}")
        return False

def main():
    print("PEAK HOUR | NEOPIXEL CHAIN DEBUGGER")
    print("Checking which SPI bus works for your chain...")
    
    # Test SPI 1 (Pin 38 - MOSI, Pin 40 - SCLK)
    try:
        print("\nChecking SPI 1 (GPIO 20 / Pin 38)...")
        spi1 = busio.SPI(board.D21, board.D20)
        test_bus("SPI 1", spi1)
    except Exception as e:
        print(f"SPI 1 Initialization failed: {e}")

    # Test SPI 0 (Pin 19 - MOSI, Pin 23 - SCLK)
    try:
        print("\nChecking SPI 0 (GPIO 10 / Pin 19)...")
        spi0 = busio.SPI(board.D11, board.D10)
        test_bus("SPI 0", spi0)
    except Exception as e:
        print(f"SPI 0 Initialization failed: {e}")

    # Test SPI 5 (Pin 8 - MOSI, Pin 7 - SCLK)
    try:
        print("\nChecking SPI 5 (GPIO 14 / Pin 8)...")
        spi5 = busio.SPI(board.D15, board.D14)
        test_bus("SPI 5", spi5)
    except Exception as e:
        print(f"SPI 5 Initialization failed: {e}")

    print("\nDebug complete. If no lights flashed, check your wiring or SPI overlays.")

if __name__ == "__main__":
    main()
