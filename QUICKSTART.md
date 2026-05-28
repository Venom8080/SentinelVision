# Quick Start Guide - SentinelVision Defense System

## 🚀 Fast Setup (5 Minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Upload Arduino Firmware
1. Open `arduino_firmware.ino` in Arduino IDE
2. Select: **Tools → Board → Arduino Uno** (or your board)
3. Select: **Tools → Port → COM3** (or your COM port)
4. Click **Upload** button

### Step 3: Connect Hardware
```
Arduino Pin 9  → Pan Servo Signal (Orange/Yellow wire)
Arduino Pin 10 → Tilt Servo Signal (Orange/Yellow wire)
Arduino Pin 11 → Laser Module Signal
Arduino 5V     → Servo Power (Red wire) + Laser VCC
Arduino GND    → Servo GND (Brown/Black) + Laser GND
```

**⚠️ Important**: Use external 5V power supply for servos if they draw too much current!

### Step 4: Add Authorized Faces
1. Put face images in `known_faces/` folder
2. Run encoding:
```bash
python encode_faces.py
```

### Step 5: Run the System
```bash
python sentinelvision.py
```

## ✅ Testing Checklist

- [ ] Camera opens and shows video feed
- [ ] Arduino connects (check status in UI)
- [ ] Authorized face shows "Welcome, [Name]"
- [ ] Unauthorized face triggers laser and tracking
- [ ] Servos move when unauthorized face moves
- [ ] Laser turns on/off correctly

## 🔧 Common Issues

**Camera not working?**
- Try changing `CAM_INDEX = 0` to `1` or `2` in `sentinelvision.py`

**Arduino not connecting?**
- Check USB cable
- Click "Scan for Arduino" button
- Verify COM port in Device Manager

**Face not recognized?**
- Add more images of the person
- Use clear, front-facing photos
- Re-run `encode_faces.py`

**Servos not moving?**
- Check wiring
- Test with Arduino Serial Monitor
- Verify power supply (may need external 5V)

## 📞 Commands Reference

| Python → Arduino | What It Does |
|------------------|--------------|
| `AUTH Arjun` | Authorized face detected |
| `UNAUTH 90 45` | Track face at pan=90°, tilt=45° |
| `LASER_ON` | Turn laser on |
| `LASER_OFF` | Turn laser off |

## 🎯 Expected Behavior

**Authorized Person:**
- ✅ Green message: "Welcome, [Name]"
- ✅ Laser OFF
- ✅ Servos stay centered

**Unauthorized Person:**
- ⚠️ Red warning: "Please Step Back / Go Away"
- 🔴 Laser ON and tracking
- 🎯 Servos follow face movement

