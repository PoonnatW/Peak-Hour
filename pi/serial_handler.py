import serial
import serial.tools.list_ports
import threading
import time

class SerialHandler:
    def __init__(self, baudrate=115200):
        self.baudrate = baudrate
        self.ports = []
        self.running = False
        self.callback = None
        
        self._connect_ports()
        
    def _connect_ports(self):
        # Find available USB serial ports (usually /dev/ttyUSB*)
        available_ports = [p.device for p in serial.tools.list_ports.comports() if 'USB' in p.device or 'ACM' in p.device]
        
        for port_name in available_ports:
            try:
                ser = serial.Serial(port_name, self.baudrate, timeout=1)
                self.ports.append(ser)
                print(f"Connected to {port_name}")
            except Exception as e:
                print(f"Failed to connect to {port_name}: {e}")
                
    def start_listening(self, callback):
        self.callback = callback
        self.running = True
        
        for ser in self.ports:
            t = threading.Thread(target=self._listen_thread, args=(ser,), daemon=True)
            t.start()
            
    def _listen_thread(self, ser):
        while self.running:
            try:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    if line:
                        self._parse_and_dispatch(line)
            except OSError as e:
                print(f"Serial disconnected from {ser.name}: {e}")
                self.running = False
            except Exception as e:
                print(f"Error reading from {ser.name}: {e}")
                time.sleep(0.5)
                
    def _parse_and_dispatch(self, line):
        # Format 1: TYPE:ID:VALUE (Preferred)
        parts = line.split(":")
        if len(parts) >= 3:
            msg_type = parts[0]
            msg_id = parts[1]
            value = parts[-1]
            if self.callback:
                self.callback(msg_type, msg_id, value)
            return

        # Format 2: TYPE:VALUE (e.g. BELL:1)
        if len(parts) == 2:
            msg_type = parts[0]
            value = parts[1]
            if self.callback:
                self.callback(msg_type, "0", value)
            return

        # Format 3: Raw RFID (e.g. "3E53E79C fries 3")
        # If it starts with a hex-like string of 8+ chars
        clean_line = line.strip()
        first_word = clean_line.split()[0]
        if len(first_word) >= 8 and all(c in "0123456789ABCDEFabcdef" for c in first_word):
            if self.callback:
                # Dispatch as a generic RFID scan at dummy station 99
                self.callback("RFID", "99", clean_line)
            return

        print(f"[SERIAL] Unrecognized format: {line}")
            
    def send_command(self, msg_type, msg_id, value):
        cmd = f"{msg_type}:{msg_id}:{value}\n".encode('utf-8')
        for ser in self.ports:
            try:
                ser.write(cmd)
            except Exception as e:
                print(f"Error writing to {ser.name}: {e}")
                
    def stop(self):
        self.running = False
        for ser in self.ports:
            try:
                ser.close()
            except:
                pass