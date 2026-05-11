import time
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

try:
    from tft_screen import setup_tft, canvas
    from PIL import ImageFont
except ImportError as e:
    print(f"Error: Missing dependencies. {e}")
    print("Ensure luma.lcd and luma.core are installed.")
    sys.exit(1)

def test_screen():
    print("Starting TFT Test...")
    device = setup_tft()
    
    if device is None:
        print("CRITICAL: Device initialization failed. Check wiring and SPI settings.")
        return

    print(f"Device found: {device.width}x{device.height}")
    
    # Define some colors and font
    font = ImageFont.load_default()
    
    with canvas(device) as draw:
        # 1. Fill background
        draw.rectangle(device.bounding_box, fill="black")
        
        # 2. Draw border
        draw.rectangle((0, 0, device.width-1, device.height-1), outline="white")
        
        # 3. Draw some test shapes
        draw.rectangle((20, 20, 100, 100), fill="red", outline="white")
        draw.ellipse((120, 20, 200, 100), fill="blue", outline="white")
        draw.polygon([(220, 100), (260, 20), (300, 100)], fill="green", outline="white")
        
        # 4. Draw text
        draw.text((20, 120), "TFT INITIALIZED", fill="yellow", font=font)
        draw.text((20, 150), f"Res: {device.width}x{device.height}", fill="cyan", font=font)
        draw.text((20, 180), "Pins: DC=22, RST=27, CS=8", fill="magenta", font=font)

    print("Test pattern displayed successfully.")
    print("If you don't see anything, check if SPI is enabled in raspi-config.")
    time.sleep(2)

if __name__ == "__main__":
    try:
        test_screen()
    except KeyboardInterrupt:
        print("\nTest stopped by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
