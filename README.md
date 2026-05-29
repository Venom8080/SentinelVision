# 🛡️ SentinelVision Software Security System

## 🚀 Real-Time Face Recognition Security Monitoring System

SentinelVision is a Computer Vision-based security monitoring system developed using Python, OpenCV, and Tkinter. It performs real-time face detection and face recognition through a webcam to identify authorized and unauthorized individuals.

The system automatically stores evidence images, maintains security logs, manages authorized users, and can send email alerts when unknown individuals are detected.

---

## ✨ Features

### 🔍 Real-Time Face Detection

* Live webcam monitoring
* Fast face detection using OpenCV
* Real-time processing and tracking

### 👤 Face Recognition

* Recognizes registered users
* Displays person name upon successful recognition
* Green ACCESS GRANTED notification

### 🚨 Unauthorized Detection

* Detects unknown individuals
* Displays warning alerts
* Stores evidence images automatically
* Generates security logs

### 📧 Email Alerts

* Sends unauthorized person's image to administrator
* SMTP-based notification system
* Configurable email settings

### 📁 Evidence Management

* Authorized captures stored separately
* Unauthorized captures stored separately
* Automatic timestamp generation

### 📊 Security Logging

* CSV-based event logging
* Detection history tracking
* Security audit records

### 🎙 Voice Greeting

* Optional voice welcome message for authorized users

---

## 🏗️ System Workflow

```text
Webcam
   │
   ▼
Face Detection
   │
   ▼
Face Recognition
   │
 ┌─┴─────────────┐
 │               │
 ▼               ▼
Authorized    Unauthorized
 │               │
 ▼               ▼
Green UI      Red Alert
 │               │
 ▼               ▼
Capture Save  Capture Save
 │               │
 ▼               ▼
Event Log     Email Alert
```

---

## 🛠️ Technology Stack

| Technology | Purpose                      |
| ---------- | ---------------------------- |
| Python     | Core Development             |
| OpenCV     | Face Detection & Recognition |
| Tkinter    | Desktop GUI                  |
| NumPy      | Numerical Processing         |
| Pillow     | Image Processing             |
| pyttsx3    | Voice Greeting               |
| SMTP       | Email Notifications          |

---

# 📋 Requirements

* Python 3.8 or Higher
* Webcam
* Windows / Linux / macOS
* Internet Connection (for Email Alerts)

---

# 📥 Installation Guide

## 1. Clone Repository

```bash
git clone https://github.com/Venom8080/SentinelVision.git
```

## 2. Open Project Directory

```bash
cd SentinelVision
```

## 3. Create Virtual Environment (Recommended)

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ▶️ Run The Project

```bash
python sentinelvision.py
```

Alternative Entry Point:

```bash
python sentinelvision_main.py
```

---

# 👥 Register Authorized Users

## Method 1 (Recommended)

1. Launch SentinelVision
2. Open Add Face section
3. Enter user details
4. Capture face image
5. Save

The system automatically:

* Stores face image
* Updates authorized database
* Retrains recognizer
* Logs registration event

---

## Method 2 (Manual)

Place images inside:

```text
known_faces/
```

Example:

```text
known_faces/
├── Jitesh/
│   ├── image1.jpg
│   └── image2.jpg
```

Use clear front-facing images for better recognition accuracy.

---

# 📧 Email Alert Configuration

Create:

```text
alert_config.json
```

Example:

```json
{
  "enabled": true,
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_user": "your_email@gmail.com",
  "smtp_password": "your_app_password",
  "sender_email": "your_email@gmail.com",
  "admin_email": "your_admin_email@gmail.com"
}
```

### Gmail Users

Use a Gmail App Password instead of your normal Gmail password.

---

# 📂 Project Structure

```text
SentinelVision/
│
├── sentinelvision.py
├── sentinelvision_main.py
├── requirements.txt
├── README.md
│
├── known_faces/
│
├── captures/
│   ├── authorized/
│   └── unauthorized/
│
├── screenshots/
│
├── authorized_people.json
├── security_events.csv
├── alert_config.example.json
└── alert_config.json
```

---

# 🧪 Testing Scenarios

| Test Case          | Expected Result      |
| ------------------ | -------------------- |
| Authorized User    | Access Granted       |
| Unauthorized User  | Warning Alert        |
| No Face Detected   | Waiting State        |
| Multiple Faces     | Detect All Faces     |
| Email Notification | Admin Receives Alert |

---

# 🔧 Troubleshooting

## Camera Not Working

* Check webcam permissions
* Close other camera applications
* Change camera index

```python
CAM_INDEX = 1
```

---

## Face Recognition Not Working

* Install opencv-contrib-python
* Add multiple face samples
* Improve lighting conditions
* Use clear front-facing images

---

## Email Alert Not Working

* Verify SMTP credentials
* Check internet connection
* Use Gmail App Password
* Ensure alert system is enabled

---

# 🎯 Skills Demonstrated

* Python Programming
* OpenCV
* Computer Vision
* Face Recognition
* Security Monitoring
* Event Logging
* Email Automation
* Tkinter GUI Development
* Image Processing

---

# 🔮 Future Improvements

* Multi-Camera Monitoring
* Database Integration
* Mobile Notifications
* Cloud Storage
* User Authentication Dashboard
* Web-Based Monitoring Panel

---

# 👨‍💻 Author

## Jitesh Dewangan

Cybersecurity Enthusiast | MCA Student | CyberSecurity

### Connect With Me

🔗 LinkedIn
https://www.linkedin.com/in/jitesh-dewangan-17617424b/

🔗 GitHub
https://github.com/Venom8080

---

# ⚠️ Disclaimer

This project is developed for educational and research purposes only. Users are responsible for complying with local laws and regulations regarding surveillance, monitoring, and data collection.

---

# ⭐ Support

If you find this project useful:
⭐ Star the Repository
🍴 Fork the Repository
🤝 Contribute Improvements
📢 Share with Others

---

### Made with ❤️ by Jitesh Dewangan
