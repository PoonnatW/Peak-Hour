from luma.core.interface.serial import spi
from luma.lcd.device import ili9488
from luma.core.render import canvas
from PIL import ImageFont
import config

# --- REAL PINOUT ---
# TFT RESET: GPIO 27
# TFT DC/RS: GPIO 22
# TFT MOSI:  GPIO 10 (Hardware SPI0)
def setup_tft():
    """
    Initializes and returns the ILI9488 TFT device using the native GPIO backend.
    """
    print("[TFT] Initializing ILI9488 on SPI0...")
    try:
        # port=0, device=0 uses hardware SPI (kernel handles SCLK, MOSI, and CS)
        serial_iface = spi(
            port=0, 
            device=0, 
            gpio_DC=22, 
            gpio_RST=27, 
            gpio_CS=26,
            bus_speed_hz=2000000
        )
        
        # Setup the ILI9488 device, use a known FREE pin (GPIO 16) for backlight to avoid GPIO 18 conflicts
        device = ili9488(
            serial_iface, 
            rotate=2, 
            gpio_LIGHT=16
        )
        print("[TFT] Display initialized successfully.")
        return device
    except Exception as e:
        print(f"[TFT] ERROR: Could not initialize display: {e}")
        return None

def get_default_font():
    """Returns the default PIL font."""
    return ImageFont.load_default()

def draw_game_state(device, logic):
    """Draws a highly graphical game state to the TFT screen using Pillow."""
    if not device: return
    
    from PIL import Image, ImageDraw, ImageFont
    import os
    import time
    
    # Create base image
    img = Image.new("RGB", (device.width, device.height), "white")
    draw = ImageDraw.Draw(img)
    
    # Try to load a nice font
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        font_large = ImageFont.truetype(font_path, 40)
        font_med = ImageFont.truetype(font_path, 24)
    except:
        font_large = get_default_font()
        font_med = get_default_font()

    # 1. Background / Recipe Card
    recipe = logic.active_recipe
    recipe_id = None
    if recipe:
        recipe_id = next((k for k, v in logic.recipes_db.items() if v == recipe), "None")
        
    asset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    card_path = os.path.join(asset_dir, f"Recipe_Card_{recipe_id}.png")
    
    if os.path.exists(card_path):
        try:
            # Paste the beautiful recipe card directly to the screen!
            card = Image.open(card_path).convert("RGBA")
            # The ILI9488 is 480x320. Resize the card to fit exactly!
            card = card.resize((device.width, device.height), Image.Resampling.LANCZOS)
            # Create a white background and composite
            bg = Image.new("RGBA", (device.width, device.height), "white")
            bg.paste(card, (0, 0), card)
            img = bg.convert("RGB")
            draw = ImageDraw.Draw(img)
        except Exception as e:
            print(f"[TFT] Error loading image: {e}")
    else:
        # Fallback dark background
        draw.rectangle((0, 0, device.width, device.height), fill=(20, 20, 30))
        draw.text((20, 20), f"ORDER: {recipe['name'] if recipe else 'NONE'}", fill="white", font=font_large)

    # 2. Overlays based on State
    if logic.state == "idle":
        draw.rectangle((0, device.height//2 - 40, device.width, device.height//2 + 40), fill=(0, 0, 0))
        draw.text((device.width//2 - 160, device.height//2 - 15), "WAITING FOR KEYCARD...", fill="yellow", font=font_med)
        
    elif logic.state == "showcase" or logic.state == "recipe_scanned":
        draw.rectangle((0, device.height - 60, device.width, device.height), fill=(0, 100, 200))
        draw.text((20, device.height - 45), "PRESS LID BUTTON TO START!", fill="white", font=font_med)
        
    elif logic.state == "countdown":
        elapsed = time.time() - logic.state_time
        count = max(1, 3 - int(elapsed))
        
        # Giant red countdown
        try: font_giant = ImageFont.truetype(font_path, 150)
        except: font_giant = font_large
        
        draw.rectangle((device.width//2 - 100, device.height//2 - 100, device.width//2 + 100, device.height//2 + 100), fill="white", outline="red", width=5)
        draw.text((device.width//2 - 45, device.height//2 - 80), str(count), fill="red", font=font_giant)
        
    elif logic.state == "playing":
        # Draw Timer Box Top Right
        time_limit = int(recipe.get("time_limit", 180)) if recipe else 180
        elapsed = time.time() - logic.state_time
        time_left = max(0, time_limit - elapsed)
        mins, secs = int(time_left // 60), int(time_left % 60)
        
        draw.rectangle((device.width - 120, 10, device.width - 10, 50), fill=(0, 0, 0), outline=(0, 255, 255), width=2)
        draw.text((device.width - 110, 15), f"{mins:02d}:{secs:02d}", fill="cyan", font=font_med)
        
        # --- Ingredient Status List ---
        # Draw a translucent panel at the bottom for ingredients
        panel_h = 80
        draw.rectangle((0, device.height - panel_h, device.width, device.height), fill=(0, 0, 0, 180))
        
        required = [ing for ing in recipe["ingredients"] if ing.strip()] if recipe else []
        
        # Get all pieces to find matches
        all_pieces = list(logic.plate_contents.values())
        for content in logic.station_contents.values():
            if isinstance(content, list): all_pieces.extend(content)
            else: all_pieces.append(content)
        
        available_pieces = all_pieces[:]
        plated_uids = [p.uid for p in logic.plate_contents.values()]
        
        for i, ing_name in enumerate(required):
            x = 10 + i * (device.width // len(required)) if len(required) > 0 else 10
            y = device.height - panel_h + 5
            
            match = None
            for p in available_pieces:
                if p.name == ing_name:
                    match = p
                    available_pieces.remove(p)
                    break
            
            is_plated = match and match.uid in plated_uids
            color = (0, 255, 0) if is_plated else "white"
            
            # Draw name
            short_name = ing_name[:8] # Truncate for TFT
            draw.text((x, y), short_name, fill=color, font=font_med)
            
            # Draw progress
            if is_plated:
                draw.text((x, y + 25), "PLATED", fill=(0, 255, 0), font=font_med)
            elif match:
                reqs = config.THRESHOLDS.get(ing_name, {})
                status = ""
                if reqs.get("spins", 0) > 0: status += f"S:{match.operations['spins']}/{reqs['spins']} "
                if reqs.get("tosses", 0) > 0: status += f"T:{match.operations['tosses']}/{reqs['tosses']} "
                if reqs.get("presses", 0) > 0: status += f"F:{match.operations['presses']}/{reqs['presses']} "
                draw.text((x, y + 25), status.strip(), fill="yellow", font=font_med)
            else:
                draw.text((x, y + 25), "MISSING", fill="red", font=font_med)

    elif logic.state == "win":
        draw.rectangle((0, device.height//2 - 50, device.width, device.height//2 + 50), fill=(0, 200, 0))
        draw.text((device.width//2 - 80, device.height//2 - 20), "YOU WIN!", fill="white", font=font_large)
        
    elif logic.state == "lose":
        draw.rectangle((0, device.height//2 - 50, device.width, device.height//2 + 50), fill=(200, 0, 0))
        draw.text((device.width//2 - 100, device.height//2 - 20), "GAME OVER", fill="white", font=font_large)

    # Render image to screen!
    device.display(img)
