import serial
import serial.tools.list_ports
import pickle
import time

class SerialController:
    def __init__(self, baudrate=115200, timeout=1):
        self.ser = None
        self.baudrate = baudrate
        self.timeout = timeout

    def auto_connect(self):
        """Automatically detect Arduino COM port and connect"""
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            if "Arduino" in p.description or "CH340" in p.description or "USB Serial" in p.description:
                try:
                    self.ser = serial.Serial(p.device, self.baudrate, timeout=self.timeout)
                    time.sleep(2)  # allow Arduino reset
                    return p.device
                except Exception as e:
                    print("Serial connect error:", e)
        return None

    def is_open(self):
        return self.ser is not None and self.ser.is_open

    def send_cmd(self, cmd):
        """Send command to Arduino"""
        if self.is_open():
            try:
                self.ser.write((cmd + "\n").encode('utf-8'))
            except Exception as e:
                print("Send error:", e)

    def send_track_command(self, pan_angle, tilt_angle):
        """Send UNAUTH command with pan and tilt angles for servo tracking"""
        if self.is_open():
            try:
                # Constrain angles to 0-180 range
                pan_angle = max(0, min(180, int(pan_angle)))
                tilt_angle = max(0, min(180, int(tilt_angle)))
                cmd = f"UNAUTH {pan_angle} {tilt_angle}"
                self.ser.write((cmd + "\n").encode('utf-8'))
            except Exception as e:
                print("Send track command error:", e)

    def send_auth_command(self, name):
        """Send AUTH command with person's name"""
        if self.is_open():
            try:
                cmd = f"AUTH {name}"
                self.ser.write((cmd + "\n").encode('utf-8'))
            except Exception as e:
                print("Send auth command error:", e)

    def close(self):
        try:
            if self.is_open():
                self.ser.close()
        except Exception:
            pass


def load_encodings(path):
    """Load known face encodings from pickle file"""
    try:
        # Handle both Path objects and strings
        from pathlib import Path
        path_obj = Path(path) if not isinstance(path, Path) else path
        if not path_obj.exists():
            print(f"Encodings file not found: {path_obj}")
            return [], []
        with open(path_obj, 'rb') as f:
            data = pickle.load(f)
            return data.get('encodings', []), data.get('names', [])
    except Exception as e:
        print("Error loading encodings:", e)
        return [], []
