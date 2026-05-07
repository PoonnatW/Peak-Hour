import serial
import time
from PIL import ImageFont

# --- Luma Imports ---
from luma.core.interface.serial import spi
from luma.lcd.device import ili9488
from luma.core.render import canvas

# --- CONFIGURATION ---
SERIAL_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 115200
TIMEOUT_SECONDS = 0.5 

# 1. Setup Luma SPI interface 
# port=0, device=0 automatically binds CS to GPIO 8 (Physical Pin 24)
serial_iface = spi(port=0, device=0, gpio_DC=24, gpio_RST=25, bus_speed_hz=24000000)

# 2. Setup the ILI9488 device
# rotate=1 automatically rotates the screen 90 degrees to Landscape!
device = ili9488(serial_iface)

font = ImageFont.load_default()

# Dictionary to track the current state of the game board
board_state = {
    0: {"uid": None, "last_seen": 0},
    1: {"uid": None, "last_seen": 0}
}

def update_screen():
    # 1. --- TERMINAL OUTPUT ---
    print("\033[H\033[J", end="") 
    print("=== COOKING GAME STATE ===")
    for station, data in board_state.items():
        ingredient = data['uid'] if data['uid'] else "[ Empty ]"
        print(f"Station {station + 1}: {ingredient}")
    print("==========================")

    # 2. --- TFT SCREEN OUTPUT ---
    # Luma automatically pushes to the screen when you exit the "with" block
    with canvas(device) as draw:
        # Draw header banner
        draw.rectangle((0, 0, device.width, 20), fill="red")
        draw.text((10, 2), "--- KITCHEN STATUS ---", font=font, fill="white")
        
        st1_text = board_state[0]['uid'] if board_state[0]['uid'] else "[ Empty ]"
        st2_text = board_state[1]['uid'] if board_state[1]['uid'] else "[ Empty ]"
        
        draw.text((10, 40), f"Frying Pan: {st1_text}", font=font, fill="green")
        draw.text((10, 70), f"Deep Fryer: {st2_text}", font=font, fill="yellow")

def main():
    update_screen()
    
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        
        while True:
            current_time = time.time()
            state_changed = False
            
            # Drain the entire buffer instantly
            while ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if "," in line:
                    parts = line.split(",")
                    try:
                        station_id = int(parts[0])
                        uid = parts[1]
                        
                        if uid == "" or uid.lower() == "none":
                            uid = None
                            
                        if board_state[station_id]["uid"] != uid:
                            board_state[station_id]["uid"] = uid
                            state_changed = True
                            
                        board_state[station_id]["last_seen"] = current_time
                    except ValueError:
                        pass 

            # Check for timeouts
            for station, data in board_state.items():
                if data["uid"] is not None:
                    if (current_time - data["last_seen"]) > TIMEOUT_SECONDS:
                        board_state[station]["uid"] = None
                        state_changed = True

            # Draw if changed
            if state_changed:
                update_screen()

    except KeyboardInterrupt:
        print("\nGame Over.")
        # Clear the TFT screen on exit to black
        with canvas(device) as draw:
            draw.rectangle((0, 0, device.width, device.height), fill="black")
        ser.close()

if __name__ == '__main__':
    main()