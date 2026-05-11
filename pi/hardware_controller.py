import time
try:
    import board
    import neopixel
except ImportError:
    print("Adafruit Blinka and Neopixel libraries not found.")
    board = None
    neopixel = None

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
    A controller for interacting with Neopixel LEDs, a button, and an AS5600 sensor via I2C on Raspberry Pi.
    """
    def __init__(self, led_pin=None, num_pixels=10, button_pin=23, i2c_bus=1):
        # Initialize Neopixel
        self.num_pixels = num_pixels
        self.pixels = None
        if neopixel and board:
            led_pin = led_pin or board.D18
            try:
                self.pixels = neopixel.NeoPixel(led_pin, self.num_pixels, auto_write=False)
                print(f"Neopixel initialized on pin {led_pin} with {num_pixels} pixels.")
            except Exception as e:
                print(f"Error initializing Neopixel: {e}")

        # Initialize Button
        self.button = None
        self.btn_callback = None
        if Button:
            try:
                self.button = Button(button_pin, pull_up=True, bounce_time=0.1)
                self.button.when_pressed = self._button_handler
                print(f"Button initialized on GPIO {button_pin}.")
            except Exception as e:
                print(f"Error initializing Button on GPIO {button_pin}: {e}")

        # Initialize AS5600 via I2C
        self.i2c_bus_num = i2c_bus
        self.as5600_addr = 0x36
        self.bus = None
        if smbus2:
            try:
                self.bus = smbus2.SMBus(self.i2c_bus_num)
                # Quick test to see if device is present
                self.bus.read_byte(self.as5600_addr)
                print(f"AS5600 initialized on I2C bus {self.i2c_bus_num} at address {hex(self.as5600_addr)}.")
            except Exception as e:
                print(f"Error initializing I2C for AS5600 (check wiring and if I2C is enabled): {e}")
                self.bus = None

        # Tracking state
        self.spins = 0
        self.last_angle = None

    def _button_handler(self):
        print("[HARDWARE] Physical Button (GPIO 23) Pressed!")
        if self.btn_callback:
            self.btn_callback()

    def set_button_callback(self, callback):
        """Set a callback function for when the button is pressed."""
        self.btn_callback = callback

    def update(self):
        """Poll sensors. Called by the main loop."""
        # Check AS5600 for spins
        angle = self.read_as5600_angle()
        if angle is not None:
            if self.last_angle is not None:
                diff = abs(angle - self.last_angle)
                if diff > 500: # Threshold for a spin
                    print(f"[HARDWARE] AS5600 Spin Detected: {angle}")
                    self.spins += 1
            self.last_angle = angle

    # --- Neopixel Methods ---
    def set_led_color(self, index, color):
        if self.pixels and 0 <= index < self.num_pixels:
            self.pixels[index] = color
            self.pixels.show()
            
    def fill_leds(self, color):
        if self.pixels:
            self.pixels.fill(color)
            self.pixels.show()
            
    def clear_leds(self):
        self.fill_leds((0, 0, 0))

    # --- Button Methods ---
    def get_button_state(self):
        if self.button:
            return self.button.is_active
        return False

    # --- AS5600 Methods ---
    def read_as5600_angle(self):
        if self.bus is None:
            return None
        try:
            data = self.bus.read_i2c_block_data(self.as5600_addr, 0x0E, 2)
            angle = (data[0] << 8) | data[1]
            return angle
        except Exception as e:
            return None

if __name__ == "__main__":
    # Simple test script
    print("Testing Hardware Controller...")
    hw = HardwareController()
    hw.set_button_callback(lambda: print("Callback Triggered!"))

    try:
        while True:
            hw.update()
            angle = hw.read_as5600_angle()
            if angle is not None:
                print(f"AS5600 Angle: {angle} | Spins: {hw.spins}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        hw.clear_leds()
