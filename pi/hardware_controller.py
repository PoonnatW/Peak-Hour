import time
try:
    from rpi_ws281x import Adafruit_NeoPixel, Color
    ws281x_available = True
except ImportError:
    print("rpi-ws281x library not found. Run: sudo pip3 install rpi-ws281x")
    ws281x_available = False
    Color = None

try:
    from gpiozero import Button
except ImportError:
    print("gpiozero library not found.")
    Button = None

try:
    import smbus2
except ImportError:
    print("smbus2 library not found.")
    smbus2 = None

class HardwareController:
    """
    A controller for interacting with Base/Lid Neopixels, Buttons, and AS5600 sensor.
    Pins: 
    - Base Neopixel: GPIO 13
    - Lid Neopixel: GPIO 18
    - Base Button: GPIO 6
    - Lid Button: GPIO 5
    - AS5600: I2C Bus 4 (SDA 23, SCL 24)
    """
    def __init__(self, i2c_bus=4):
        # Initialize Neopixels (rpi-ws281x)
        self.base_pixels = None
        self.lid_pixels = None
        if ws281x_available:
            try:
                # Base Strip: GPIO 13, Channel 1
                self.base_pixels = Adafruit_NeoPixel(10, 13, 800000, 10, False, 255, 1)
                self.base_pixels.begin()
                # Lid Strip: GPIO 18, Channel 0
                self.lid_pixels = Adafruit_NeoPixel(10, 18, 800000, 10, False, 255, 0)
                self.lid_pixels.begin()
                print("Neopixels initialized via rpi-ws281x: Base (GPIO 13), Lid (GPIO 18)")
            except Exception as e:
                print(f"Error initializing Neopixels: {e}")

        # Initialize Buttons
        self.base_btn = None
        self.lid_btn = None
        self.base_callback = None
        self.lid_callback = None
        if Button:
            try:
                self.base_btn = Button(6, pull_up=True, bounce_time=0.1)
                self.lid_btn = Button(5, pull_up=True, bounce_time=0.1)
                self.base_btn.when_pressed = self._base_handler
                self.lid_btn.when_pressed = self._lid_handler
                print("Buttons initialized: Base (GPIO 6), Lid (GPIO 5)")
            except Exception as e:
                print(f"Error initializing Buttons: {e}")

        # Initialize AS5600 via I2C (Bus 4 for GPIO 23/24)
        self.i2c_bus_num = i2c_bus
        self.as5600_addr = 0x36
        self.bus = None
        if smbus2:
            try:
                self.bus = smbus2.SMBus(self.i2c_bus_num)
                # Quick test
                self.bus.read_byte(self.as5600_addr)
                print(f"AS5600 initialized on I2C bus {self.i2c_bus_num}")
            except Exception as e:
                print(f"Error initializing AS5600 on bus {self.i2c_bus_num}: {e}")
                self.bus = None

        # Tracking state
        self.spins = 0
        self.last_angle = None
        self.cumulative_angle = 0 # Track total movement for full rotations

    def _base_handler(self):
        print("[HARDWARE] Base Button (GPIO 6) Pressed!")
        if self.base_callback: self.base_callback()

    def _lid_handler(self):
        print("[HARDWARE] Lid Button (GPIO 5) Pressed!")
        if self.lid_callback: self.lid_callback()

    def set_button_callbacks(self, base_cb=None, lid_cb=None):
        self.base_callback = base_cb
        self.lid_callback = lid_cb

    def update(self):
        """Poll sensors. Called by the main loop."""
        angle = self.read_as5600_angle()
        if angle is not None:
            if self.last_angle is not None:
                diff = angle - self.last_angle
                if diff > 2048: diff -= 4096
                elif diff < -2048: diff += 4096
                
                self.cumulative_angle += diff
                
                if abs(self.cumulative_angle) >= 4096:
                    print(f"[HARDWARE] Full Spin Detected! (Cumulative: {self.cumulative_angle})")
                    self.spins += 1
                    if self.cumulative_angle > 0: self.cumulative_angle -= 4096
                    else: self.cumulative_angle += 4096
            self.last_angle = angle

    def set_led_color(self, index, color, target="base"):
        """
        Sets a specific pixel to a color.
        color: tuple (r, g, b)
        """
        pixels = self.base_pixels if target == "base" else self.lid_pixels
        if pixels and 0 <= index < 10:
            # rpi-ws281x uses Color(r, g, b)
            c = Color(color[0], color[1], color[2])
            pixels.setPixelColor(index, c)
            pixels.show()

    def fill_leds(self, color, target="all"):
        """
        Fills a strip or all strips with a color.
        """
        c = Color(color[0], color[1], color[2])
        if target in ["base", "all"] and self.base_pixels:
            for i in range(10):
                self.base_pixels.setPixelColor(i, c)
            self.base_pixels.show()
        if target in ["lid", "all"] and self.lid_pixels:
            for i in range(10):
                self.lid_pixels.setPixelColor(i, c)
            self.lid_pixels.show()

    def clear_leds(self):
        self.fill_leds((0, 0, 0), "all")

    def read_as5600_angle(self):
        if self.bus is None: return None
        try:
            data = self.bus.read_i2c_block_data(self.as5600_addr, 0x0E, 2)
            return (data[0] << 8) | data[1]
        except: return None

if __name__ == "__main__":
    # Simple test script
    import time
    print("PEAK HOUR | HARDWARE TEST SUITE")
    print("--------------------------------")
    hw = HardwareController()
    
    # 1. Test Neopixels
    print("Step 1: Testing Neopixel Strips (Base & Lid)...")
    test_colors = [(255, 0, 0), (255, 255, 0), (0, 255, 0)] # Red, Yellow, Green
    for color in test_colors:
        hw.fill_leds(color, "all")
        time.sleep(0.5)
    hw.clear_leds()
    print("LED Test Complete.")

    # 2. Setup Button Callbacks
    hw.set_button_callbacks(
        base_cb=lambda: print("\n[EVENT] Base Button (GPIO 6) Pressed!"),
        lid_cb=lambda: print("\n[EVENT] Lid Button (GPIO 5) Pressed!")
    )

    if hw.bus is None:
        print("WARNING: AS5600 not connected. Check I2C settings and reboot.")

    try:
        print("\nStep 2: Monitoring Sensors & Buttons...")
        print("(Rotate Magnet for Spins | Press Buttons for Events)")
        print("(Press Ctrl+C to exit)")
        while True:
            hw.update()
            angle = hw.read_as5600_angle()
            if angle is not None:
                print(f"Angle: {angle:4d} | Spins: {hw.spins} | Cum: {int(hw.cumulative_angle):5d}", end="\r")
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nTest stopped.")
        hw.clear_leds()
