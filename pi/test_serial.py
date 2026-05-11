import serial
import time
import os

def test_ports():
    # Common Raspberry Pi USB serial ports
    ports = ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/ttyACM1"]
    active_serials = []

    print("--- PEAK HOUR SERIAL MONITOR ---")
    print("Searching for ESP32 devices...")
    
    for p in ports:
        if os.path.exists(p):
            try:
                ser = serial.Serial(p, 115200, timeout=1)
                active_serials.append((p, ser))
                print(f"✅ Found and connected to {p}")
            except Exception as e:
                print(f"❌ Failed to connect to {p}: {e}")
    
    if not active_serials:
        print("\n🚨 No ESP32 devices detected!")
        print("1. Check if the USB cable is plugged in.")
        print("2. Run 'ls /dev/tty*' to see available ports.")
        return

    print("\nREADY: Listening for data...")
    print("Action: Scan an RFID tag, press the Bell, or trigger a Toss/Spin.")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            for p, ser in active_serials:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        print(f"[{p}] 📥 {line}")
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nStopping monitor.")
        for p, ser in active_serials:
            ser.close()

if __name__ == "__main__":
    test_ports()
