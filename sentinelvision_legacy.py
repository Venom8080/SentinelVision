import cv2
import face_recognition
import os
import tkinter as tk
from PIL import Image, ImageTk
from datetime import datetime

# Directories
KNOWN_FACES_DIR = "known_faces"
INTRUDERS_DIR = "intruders"
LOG_FILE = "log.txt"

os.makedirs(INTRUDERS_DIR, exist_ok=True)

# Load known faces (jpg, jpeg, png)
known_encodings = []
known_names = []

for file in os.listdir(KNOWN_FACES_DIR):
    if file.lower().endswith((".jpg", ".jpeg", ".png")):
        path = os.path.join(KNOWN_FACES_DIR, file)
        img = face_recognition.load_image_file(path)
        enc = face_recognition.face_encodings(img)
        if enc:
            known_encodings.append(enc[0])
            # Name from filename (e.g. Raj1.jpeg -> Raj1)
            known_names.append(os.path.splitext(file)[0])

# Cooldown so popup doesn't show every frame
last_welcome_time = 0
last_unknown_time = 0
COOLDOWN_SEC = 3

def show_welcome_ui(name):
    """Green theme - Authorized person welcome."""
    win = tk.Toplevel()
    win.title("Authorized")
    win.geometry("420x220")
    win.configure(bg="#0d5c2e")
    win.resizable(False, False)

    tk.Label(win, text="Authorized Person", font=("Segoe UI", 18, "bold"),
             fg="white", bg="#0d5c2e").pack(pady=(24, 8))
    tk.Label(win, text=f"Welcome, {name}!", font=("Segoe UI", 16),
             fg="#a8e6a1", bg="#0d5c2e").pack(pady=4)
    tk.Label(win, text="Access Granted", font=("Segoe UI", 12),
             fg="#c8f0c0", bg="#0d5c2e").pack(pady=(0, 20))
    tk.Button(win, text="OK", font=("Segoe UI", 12), bg="#1a7d3e", fg="white",
              activebackground="#2e9d5a", relief="flat", padx=24, pady=6,
              command=win.destroy).pack(pady=8)
    win.after(4000, win.destroy)

def show_unauthorized_ui():
    """Red theme - Unauthorized person."""
    win = tk.Toplevel()
    win.title("Unauthorized")
    win.geometry("420x220")
    win.configure(bg="#8b1a1a")
    win.resizable(False, False)

    tk.Label(win, text="Unauthorized Person", font=("Segoe UI", 18, "bold"),
             fg="white", bg="#8b1a1a").pack(pady=(24, 8))
    tk.Label(win, text="Unauthorized person detected.", font=("Segoe UI", 14),
             fg="#ffb3b3", bg="#8b1a1a").pack(pady=4)
    tk.Label(win, text="Access Denied", font=("Segoe UI", 12),
             fg="#ffcccc", bg="#8b1a1a").pack(pady=(0, 20))
    tk.Button(win, text="OK", font=("Segoe UI", 12), bg="#a52a2a", fg="white",
              activebackground="#c44", relief="flat", padx=24, pady=6,
              command=win.destroy).pack(pady=8)
    win.after(4000, win.destroy)

# Main window - only camera feed, no start/stop buttons
root = tk.Tk()
root.title("SentinelVision - Camera")
root.geometry("900x600")
root.configure(bg="#1a1a1a")

video_label = tk.Label(root, bg="#1a1a1a")
video_label.pack(fill="both", expand=True)

cap = None
running = False

def start_camera():
    global cap, running
    cap = cv2.VideoCapture(0)
    running = True
    update_frame()

def stop_camera():
    global running
    running = False
    if cap:
        cap.release()
    root.quit()

root.protocol("WM_DELETE_WINDOW", stop_camera)

def update_frame():
    global last_welcome_time, last_unknown_time
    if not running:
        return

    ret, frame = cap.read()
    if not ret:
        root.after(10, update_frame)
        return

    # Fix inverted/mirror: flip horizontally so face looks correct
    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb)
    encodings = face_recognition.face_encodings(rgb, locations)

    now_sec = datetime.now().timestamp()
    welcome_shown = False
    unknown_shown = False

    for (top, right, bottom, left), enc in zip(locations, encodings):
        matches = face_recognition.compare_faces(known_encodings, enc)
        name = "Unknown"

        if True in matches:
            name = known_names[matches.index(True)]
            color = (0, 255, 0)
            if not welcome_shown and now_sec - last_welcome_time >= COOLDOWN_SEC:
                last_welcome_time = now_sec
                welcome_shown = True
                welcome_name = name
                root.after(0, lambda n=name: show_welcome_ui(n))
        else:
            color = (0, 0, 255)
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            cv2.imwrite(os.path.join(INTRUDERS_DIR, f"intruder_{ts}.jpg"), frame)
            with open(LOG_FILE, "a") as f:
                f.write(f"{ts} - Unknown detected\n")
            if not unknown_shown and now_sec - last_unknown_time >= COOLDOWN_SEC:
                last_unknown_time = now_sec
                unknown_shown = True
                root.after(0, show_unauthorized_ui)

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    imgtk = ImageTk.PhotoImage(image=img)
    video_label.imgtk = imgtk
    video_label.config(image=imgtk)

    root.after(10, update_frame)

# Start camera directly when app opens
root.after(100, start_camera)
root.mainloop()
