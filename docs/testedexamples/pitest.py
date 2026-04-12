import serial
import time

# --- CONFIGURATION ---
# Change this to /dev/ttyUSB0 or /dev/ttyACM0 based on Step 3
SERIAL_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 115200

# How long (in seconds) before we assume a tag was removed from the board?
TIMEOUT_SECONDS = 0.5 

# Dictionary to track the current state of the game board
# Format: { Station_ID: {"uid": "TAG_ID", "last_seen": timestamp} }
board_state = {
    0: {"uid": None, "last_seen": 0},
    1: {"uid": None, "last_seen": 0}
}

def print_board():
    """Prints a clean view of the current cooking stations."""
    # Clears the terminal screen (works on Linux/Mac)
    print("\033[H\033[J", end="") 
    print("=== COOKING GAME STATE ===")
    for station, data in board_state.items():
        ingredient = data['uid'] if data['uid'] else "[ Empty ]"
        print(f"Station {station + 1}: {ingredient}")
    print("==========================")

def main():
    try:
        # Open the serial connection
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        print(f"Connected to ESP32 on {SERIAL_PORT}. Waiting for data...")
        
        while True:
            current_time = time.time()
            state_changed = False
            
            # 1. READ INCOMING DATA
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                
                # We expect data like "0,0A1B2C3D"
                if "," in line:
                    parts = line.split(",")
                    try:
                        station_id = int(parts[0])
                        uid = parts[1]
                        
                        # Update the state if it's a new tag or just update the timestamp
                        if board_state[station_id]["uid"] != uid:
                            board_state[station_id]["uid"] = uid
                            state_changed = True
                            
                        board_state[station_id]["last_seen"] = current_time
                        
                    except ValueError:
                        pass # Ignore malformed serial junk

            # 2. CHECK FOR REMOVED TAGS (TIMEOUTS)
            for station, data in board_state.items():
                if data["uid"] is not None:
                    # If the tag hasn't been scanned recently, clear it
                    if (current_time - data["last_seen"]) > TIMEOUT_SECONDS:
                        board_state[station]["uid"] = None
                        state_changed = True

            # 3. UPDATE THE SCREEN ONLY IF SOMETHING MOVED
            if state_changed:
                print_board()

    except KeyboardInterrupt:
        print("\nGame Over. Closing serial port.")
        ser.close()
    except Exception as e:
        print(f"Error: {e}. Is the ESP32 plugged in to {SERIAL_PORT}?")

if __name__ == '__main__':
    main()