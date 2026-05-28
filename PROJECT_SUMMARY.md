# SentinelVision Defense System - Project Summary

## 📋 Project Overview

**SentinelVision Defense System** is an AI-based security project that uses real-time face detection and recognition to identify authorized and unauthorized persons. The system responds differently based on face recognition results:

- **Authorized Face**: Shows welcome message with person's name
- **Unauthorized Face**: Tracks face using servo motors and aims laser pointer at it

## 📁 Project Structure

```
SentinelVision/
├── sentinelvision.py          # Main application (Python)
├── SENTINELVISION_helpers.py       # Helper functions (SerialController, load_encodings)
├── encode_faces.py           # Utility to encode faces from images
├── arduino_firmware.ino      # Arduino code for servo and laser control
├── requirements.txt          # Python dependencies
├── README.md                 # Complete documentation
├── QUICKSTART.md             # Quick setup guide
├── encodings.pickle          # Face encodings database (generated)
└── known_faces/              # Directory for authorized face images
    ├── Jitesh1.jpg
    └── Jitesh2.jpg
```

## 🎯 Key Features Implemented

### ✅ Face Detection & Recognition
- Real-time video capture from webcam
- Face detection using `face_recognition` library
- Face matching against authorized database
- Visual feedback with bounding boxes

### ✅ Authorized Face Response
- UI displays: "🟢 Access Granted: Welcome [Name]"
- Laser automatically turns OFF
- Servos remain in center position
- Green status indicator

### ✅ Unauthorized Face Response
- UI displays: "🔴 Warning: Please Step Back / Go Away"
- Face position calculated in frame
- Pan-Tilt servos track face movement
- Laser pointer aims at face
- Red warning status indicator

### ✅ Arduino Communication
- Serial communication at 115200 baud
- Auto-detection of Arduino COM port
- Commands: `AUTH`, `UNAUTH`, `LASER_ON`, `LASER_OFF`
- Smooth servo movement to prevent jitter

### ✅ User Interface
- Live camera preview with face detection boxes
- Real-time status display
- Arduino connection indicator
- Laser status indicator
- System log for debugging
- Modern dark theme UI

## 🔌 Hardware Connections

| Component | Arduino Pin |
|-----------|-------------|
| Pan Servo | Pin 9 |
| Tilt Servo | Pin 10 |
| Laser Module | Pin 11 |
| Power | 5V, GND |

## 📡 Communication Protocol

### Python → Arduino Commands

| Command | Format | Description |
|---------|--------|-------------|
| `AUTH` | `AUTH <name>` | Authorized face detected |
| `UNAUTH` | `UNAUTH <pan> <tilt>` | Track unauthorized face |
| `LASER_ON` | `LASER_ON` | Turn laser on |
| `LASER_OFF` | `LASER_OFF` | Turn laser off |

### Example Commands
```
AUTH Arjun
UNAUTH 90 45
LASER_ON
LASER_OFF
```

## 🧮 Servo Tracking Algorithm

1. Face center calculated: `(face_center_x, face_center_y)`
2. Map to servo angles:
   - `pan_angle = map(face_center_x, 0 → 640, 0 → 180)`
   - `tilt_angle = map(face_center_y, 0 → 480, 0 → 180)`
3. Send to Arduino: `UNAUTH <pan_angle> <tilt_angle>`
4. Arduino moves servos smoothly to target position

## 🚀 How to Run

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Upload Arduino firmware:**
   - Open `arduino_firmware.ino` in Arduino IDE
   - Select board and COM port
   - Upload

3. **Encode authorized faces:**
   ```bash
   python encode_faces.py
   ```

4. **Run the system:**
   ```bash
   python sentinelvision.py
   ```

## 🧪 Testing Scenarios

| Scenario | Expected Behavior |
|----------|-------------------|
| Authorized person appears | Green welcome message, laser OFF |
| Unauthorized person appears | Red warning, laser ON, servos track |
| Person moves left/right | Pan servo follows movement |
| Person moves up/down | Tilt servo follows movement |
| No face in frame | "Waiting for face...", laser OFF |
| Multiple faces | Processes first detected face |

## 📊 System Flow

```
Webcam → Face Detection → Face Recognition
                              ↓
                    ┌─────────┴─────────┐
                    ↓                   ↓
            Authorized?            Unauthorized?
                    ↓                   ↓
         Show Welcome Message    Calculate Face Position
         Laser OFF                      ↓
         Servos Center          Send UNAUTH to Arduino
                                        ↓
                                 Servos Track Face
                                 Laser ON
                                 Show Warning
```

## 🔧 Configuration Options

In `sentinelvision.py`:
- `CAM_INDEX = 0` - Camera device index
- `FRAME_WIDTH = 640` - Video frame width
- `FRAME_HEIGHT = 480` - Video frame height
- `PROCESS_EVERY_N = 3` - Process every Nth frame (performance)

In `arduino_firmware.ino`:
- `PAN_SERVO_PIN = 9` - Pan servo pin
- `TILT_SERVO_PIN = 10` - Tilt servo pin
- `LASER_PIN = 11` - Laser control pin

## 📝 Notes

- System processes every 3rd frame for better performance
- Face recognition tolerance: 0.6 (adjustable)
- Servo movement is smoothed to prevent jitter
- Laser automatically turns off when no face detected for 2 seconds
- System auto-connects to Arduino on startup

## 🎓 For Viva/Presentation

**One-Sentence Summary:**
"SentinelVision Defense System ek AI-based security project hai jisme laptop webcam realtime face detect karta hai, authorized face par UI par welcome message show hota hai aur unauthorized face par system servo motors ke through face ko track karke laser pointer face par aim karta hai, saath hi UI par warning display hoti hai."

**Key Points to Highlight:**
1. Real-time face detection and recognition
2. Different responses for authorized vs unauthorized
3. Servo motor tracking system
4. Laser pointer warning mechanism
5. User-friendly UI with status indicators
6. Arduino integration for hardware control

## 🔐 Safety Notes

⚠️ **Important Safety Warnings:**
- Laser pointer should be Class 1 or Class 2 (eye-safe)
- Never point laser directly at eyes
- Use appropriate power supply for servos
- Ensure proper grounding for all components
- This is a demonstration project - not for actual security use

## 📚 Technologies Used

- **Python 3.8+**: Main programming language
- **OpenCV**: Video processing and image handling
- **face_recognition**: Face detection and recognition
- **Tkinter**: GUI framework
- **PySerial**: Arduino communication
- **Arduino C++**: Hardware control firmware
- **NumPy**: Numerical computations
- **Pillow**: Image processing

---

**Project Status**: ✅ Complete and Ready for Use

