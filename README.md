# SentinelVision Software Security System

Run the software-only CCTV dashboard:

```bash
python sentinelvision.py
```

Current software features:

- Live CCTV/webcam monitoring with face recognition
- Green welcome UI for authorized people with name
- Red warning UI for unauthorized people.
- Add authorized faces from the app with basic details
- Authorized captures saved in `captures/authorized/`
- Unauthorized captures saved in `captures/unauthorized/`
- Unauthorized person photo is sent automatically to admin email when SMTP is configured.
- Backend alert settings are saved in `alert_config.json`

Admin recipient is fixed to `example@gmail.com`; admin phone is stored as
`****661***`. Fill sender SMTP details in `alert_config.json` or via environment
variables. The UI does not show a separate alert settings tab.

---
security system that uses real-time face detection and recognition to identify authorized and unauthorized persons. The system tracks unauthorized faces using servo motors and aims a laser pointer at them.

## 🎯 Main Features

- **Real-time Face Detection**: Uses laptop webcam for live video feed
- **Face Recognition**: Identifies authorized persons from a database
- **Authorized Face Response**: Shows welcome message with person's name
  - Displays warning message on UI

## 📦 Software Requirements

- Python 3.8 or higher
- Arduino IDE (for uploading firmware)
- Required Python libraries (see `requirements.txt`)

## 🚀 Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```


### 4. Add Authorized Faces

1. Place images of authorized persons in the `known_faces/` directory
   - Supported formats: `.jpg`, `.jpeg`, `.png`, `.bmp`
   - Use clear, front-facing photos for best results
   - Name files with the person's name (e.g., `Arjun.jpg`, `John.jpg`)

2. Run the face encoding script to generate encodings:

```bash
python encode_faces.py
```

This will create `encodings.pickle` file with face encodings for all authorized persons.

## 🖥 Usage

### Running the Application

```bash
python sentinelvision.py
```

### System Flow

1. **Webcam Capture**: System captures real-time video from webcam
2. **Face Detection**: Detects faces in the video frame
3. **Face Recognition**: Compares detected faces with authorized database
4. **Decision Making**:
   - **Authorized**: Shows welcome message, turns off laser
   - **Unauthorized**: Tracks face with servos, aims laser, shows warning

### UI Features

- **Live Camera Preview**: Shows real-time video feed with face detection boxes
- **Status Display**: Shows current system status (Authorized/Unauthorized/Waiting)
- **System Log**: Displays all system events and messages

### Arduino Commands

The Python application sends these commands to Arduino:

| Command | Description |
|---------|-------------|
| `AUTH <name>` | Authorized face detected, turn off laser |
| `UNAUTH <pan> <tilt>` | Unauthorized face, move servos to specified angles |

```

## 🧪 Testing Scenarios

| Test Case | Expected Behavior |
|-----------|-------------------|
| Authorized known face | UI shows name, no laser, no tracking |
| New/unknown person | Laser aims at face, tracking active, UI warning |
| Person moves left/right | Pan-Tilt servos follow the movement |
| No person in frame | Laser OFF, UI shows "Waiting for face..." |

## 📌 Project Summary

**SentinelVision Defense System** is an security project where a laptop webcam performs real-time face detection. For authorized faces, the UI displays a welcome message. For unauthorized faces, the system tracks the face using servo motors and aims a laser pointer at it, while displaying a warning message on the UI.

## 🔧 Troubleshooting

### Camera Not Working
- Check if webcam is accessible by other applications
- Try changing `CAM_INDEX` in `sentinelvision.py` (0, 1, 2, etc.)

### Face Recognition Not Working
- Ensure `encodings.pickle` file exists
- Add more images of authorized persons to improve accuracy
- Check image quality in `known_faces/` directory

## 📝 Notes

- The system processes every 3rd frame for better performance
- Face recognition tolerance is set to 0.6 (adjustable in code)
- Servo movement is smoothed to prevent jitter
- Laser automatically turns off when no face is detected for 2 seconds

## 👨‍💻 Development

### File Structure


SentinelVision/
├── sentinelvision.py          # Main application
├── SENTINELVISION_helpers.py       # Helper functions (SerialController, etc.)
├── requirements.txt          # Python dependencies
├── encodings.pickle         # Face encodings database
└── README.md                # This file
```

## 👨‍💻 Author

**Jitesh Dewangan**  
Cybersecurity Enthusiast | MCA Student  
---

## ⚠ Disclaimer

This project is developed for educational and authorized security testing purposes only. Unauthorized scanning or testing of systems without permission is strictly prohibited. 

**All rights reserved. This project is proprietary and cannot be used or modified without explicit permission.**


