import os
import sys
import time
from PIL import Image
from tft_screen import setup_tft

def show_tomato():
    print("Initializing TFT to show Tomato...")
    device = setup_tft()
    
    if device is None:
        print("CRITICAL: Device initialization failed.")
        return

    # Path to assets
    asset_dir = os.path.join(os.path.dirname(__file__), "assets")
    tomato_path = os.path.join(asset_dir, "Tomato.png")
    
    if not os.path.exists(tomato_path):
        print(f"ERROR: Tomato image not found at {tomato_path}")
        return

    print(f"Loading {tomato_path}...")
    try:
        # Open the image
        img = Image.open(tomato_path).convert("RGBA")
        
        # Resize it to be nice and large on the screen
        # ILI9488 is 480x320 in landscape (rotate=1)
        # Let's resize tomato to 240x240
        img = img.resize((240, 240), Image.Resampling.LANCZOS)
        
        # Create a black background the size of the screen
        canvas = Image.new("RGB", device.size, "BLACK")
        
        # Center the tomato
        x = (device.width - img.width) // 2
        y = (device.height - img.height) // 2
        
        # Paste tomato onto background (using alpha channel for transparency)
        canvas.paste(img, (x, y), img)
        
        # Push to display
        print(f"Displaying on {device.width}x{device.height} screen at position ({x}, {y})...")
        device.display(canvas)
        print("Success! You should see a large tomato on the screen.")
        
        # Keep it visible
        time.sleep(5)
        
    except Exception as e:
        print(f"An error occurred while displaying the image: {e}")

if __name__ == "__main__":
    show_tomato()
