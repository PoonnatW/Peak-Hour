import time
try:
    import board
    import neopixel_spi
    import busio
except ImportError as e:
    print(f"❌ LIBRARY ERROR: {e}")
    print("Try: sudo pip3 install adafruit-blinka adafruit-circuitpython-neopixel-spi --break-system-packages")
    board = None
    neopixel_spi = None

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
        # Initialize Neopixels (Chained SPI Mode)
        self.pixels = None
        if neopixel_spi and board:
            try:
                # SPI 1 on Pin 38 / GPIO 20 (MOSI) and Pin 40 / GPIO 21 (SCLK)
                # Explicitly using GPIO pins to avoid Blinka mapping issues on Pi 5
                import board
                spi1 = busio.SPI(board.D21, board.D20) 
                # Chained 20 pixels (10 Base + 10 Lid)
                # Explicitly set bitrate to 6.4MHz for reliable NeoPixel timing
                self.pixels = neopixel_spi.NeoPixel_SPI(spi1, 20, bitrate=6400000, auto_write=True)
                print("✅ NeoPixels initialized (Chained on SPI1/GPIO20)")
            except Exception as e:
                print(f"⚠️ NeoPixel fail: {e}")

        # Initialize Buttons
        self.base_btn = None
        self.lid_btn = None
        self.base_callback = None
        self.lid_callback = None
        if Button:
            try:
                # Increase bounce_time to 0.2s to prevent "ghost" presses
                self.base_btn = Button(6, pull_up=True, bounce_time=0.2)
                self.lid_btn = Button(5, pull_up=True, bounce_time=0.2)
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
        if not self.pixels: return
        
        # Calculate final index based on chain
        # Base = 0-9, Lid = 10-19
        final_idx = index
        if target == "lid":
            final_idx += 10
            
        if 0 <= final_idx < 20:
            self.pixels[final_idx] = color
            self.pixels.show()
            
    def fill_leds(self, color, target="all"):
        if not self.pixels: return
        
        if target == "all":
            self.pixels.fill(color)
        elif target == "base":
            for i in range(0, 10):
                self.pixels[i] = color
        elif target == "lid":
            for i in range(10, 20):
                self.pixels[i] = color
                
        self.pixels.show()
            
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
