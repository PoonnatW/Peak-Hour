from luma.core.interface.serial import spi
from luma.lcd.device import ili9488
from luma.core.render import canvas
from PIL import ImageFont

# --- REAL PINOUT ---
# TFT RESET: GPIO 27
# TFT DC/RS: GPIO 22
# TFT MOSI:  GPIO 10 (Hardware SPI0)
# TFT SCLK:  GPIO 11 (Hardware SPI0)
# TFT CS:    GPIO 08 (Hardware SPI0 CE0)

from gpiozero import OutputDevice

class GpiozeroLumaWrapper:
    """A tiny wrapper to make gpiozero look like RPi.GPIO for luma.core"""
    def __init__(self):
        self.OUT = 1
        self.IN = 0
        self.HIGH = 1
        self.LOW = 0
        self.BCM = 11  # Dummy value for luma's setmode call
        self.pins = {}

    def setmode(self, mode):
        # Ignore setmode as gpiozero natively uses BCM
        pass

    def setup(self, pin, mode):
        if mode == self.OUT and pin not in self.pins:
            self.pins[pin] = OutputDevice(pin)

    def output(self, pin, value):
        if pin in self.pins:
            if value == self.HIGH:
                self.pins[pin].on()
            else:
                self.pins[pin].off()

    def cleanup(self):
        for pin, device in self.pins.items():
            device.close()
        self.pins.clear()

def setup_tft():
    """
    Initializes and returns the ILI9488 TFT device using gpiozero backend.
    """
    print("[TFT] Initializing ILI9488 on SPI0 with Custom gpiozero Backend...")
    try:
        gpio_backend = GpiozeroLumaWrapper()
        
        # port=0, device=0 uses hardware SPI (kernel handles SCLK, MOSI, and CS)
        serial_iface = spi(
            port=0, 
            device=0, 
            gpio_DC=22, 
            gpio_RST=27, 
            bus_speed_hz=8000000,
            gpio=gpio_backend
        )
        
        # Setup the ILI9488 device
        # rotate=1 automatically rotates the screen 90 degrees to Landscape
        device = ili9488(serial_iface, rotate=1)
        print("[TFT] Display initialized successfully.")
        return device
    except Exception as e:
        print(f"[TFT] ERROR: Could not initialize display: {e}")
        return None

def get_default_font():
    """Returns the default PIL font."""
    return ImageFont.load_default()

def draw_game_state(device, logic):
    """Draws the current game state to the TFT screen."""
    if not device: return
    
    with canvas(device) as draw:
        font = get_default_font()
        
        # Background
        draw.rectangle(device.bounding_box, outline="white", fill="black")
        
        # State
        state_text = f"STATE: {logic.state.upper()}"
        draw.text((10, 10), state_text, fill="yellow", font=font)
        
        if logic.state == "playing":
            # Timer
            time_left = max(0, logic.time_left)
            mins = int(time_left // 60)
            secs = int(time_left % 60)
            time_text = f"TIME: {mins:02d}:{secs:02d}"
            draw.text((10, 40), time_text, fill="cyan", font=font)
            
            # Recipe
            recipe = logic.current_recipe
            if recipe:
                draw.text((10, 70), f"ORDER: {recipe['name']}", fill="white", font=font)
                
            # Completed ingredients
            ready_count = sum(1 for i in logic.ingredients if i.get("state") == "plated")
            total_count = len(logic.ingredients)
            draw.text((10, 100), f"PLATED: {ready_count}/{total_count}", fill="green", font=font)
            
        elif logic.state == "win":
            draw.text((10, 40), "YOU WIN!", fill="green", font=font)
        elif logic.state == "lose":
            draw.text((10, 40), "GAME OVER", fill="red", font=font)
