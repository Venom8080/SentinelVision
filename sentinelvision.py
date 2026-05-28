"""
SentinelVision Software Security System

Pure software CCTV-style face recognition app:
- Authorized faces show a green welcome panel with name.
- Unknown faces show a red warning panel and are captured automatically.
- Authorized and unauthorized detections are saved in separate folders.
- New authorized faces can be registered from the live camera.
- Unauthorized captures can be emailed to the admin.
"""

import csv
import json
import os
import queue
import re
import smtplib
import ssl
import threading
import time
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from tkinter import messagebox, ttk
import tkinter as tk

import cv2
import numpy as np
from PIL import Image, ImageTk

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None


BASE_DIR = Path(__file__).parent
KNOWN_FACES_DIR = BASE_DIR / "known_faces"
AUTHORIZED_CAPTURE_DIR = BASE_DIR / "captures" / "authorized"
UNAUTHORIZED_CAPTURE_DIR = BASE_DIR / "captures" / "unauthorized"
EVENT_LOG_PATH = BASE_DIR / "security_events.csv"
PEOPLE_DB_PATH = BASE_DIR / "authorized_people.json"
ALERT_CONFIG_PATH = BASE_DIR / "alert_config.json"
ADMIN_EMAIL = "antivenom8080@gmail.com"
ADMIN_PHONE = "6266661940"

CAM_INDEX = 0
FRAME_WIDTH = 960
FRAME_HEIGHT = 540
FRAME_FLIP_CODE = 1
PROCESS_EVERY_N = 3
FACE_SIZE = (160, 160)
RECOGNITION_THRESHOLD = 75
AUTHORIZED_SAVE_COOLDOWN = 20
UNAUTHORIZED_ALERT_COOLDOWN = 30


def ensure_dirs():
    for path in [KNOWN_FACES_DIR, AUTHORIZED_CAPTURE_DIR, UNAUTHORIZED_CAPTURE_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def clean_filename(value):
    value = value.strip() or "person"
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    return value.strip("_") or "person"


def timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


class EmailAlertService:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self):
        data = {}
        if self.config_path.exists():
            try:
                data = json.loads(self.config_path.read_text(encoding="utf-8"))
            except Exception:
                data = {}

        return {
            "enabled": str(os.getenv("SENTINELVISION_ALERT_ENABLED", data.get("enabled", False))).lower()
            in {"1", "true", "yes", "on"},
            "smtp_server": os.getenv("SENTINELVISION_SMTP_SERVER", data.get("smtp_server", "")),
            "smtp_port": int(os.getenv("SENTINELVISION_SMTP_PORT", data.get("smtp_port", 587) or 587)),
            "smtp_user": os.getenv("SENTINELVISION_SMTP_USER", data.get("smtp_user", "")),
            "smtp_password": os.getenv("SENTINELVISION_SMTP_PASSWORD", data.get("smtp_password", "")),
            "sender_email": os.getenv("SENTINELVISION_SENDER_EMAIL", data.get("sender_email", "")),
            "admin_email": os.getenv("SENTINELVISION_ADMIN_EMAIL", data.get("admin_email", ADMIN_EMAIL)),
            "admin_phone": os.getenv("SENTINELVISION_ADMIN_PHONE", data.get("admin_phone", ADMIN_PHONE)),
        }

    def save_config(self, values):
        self.config.update(values)
        safe_config = dict(self.config)
        self.config_path.write_text(json.dumps(safe_config, indent=2), encoding="utf-8")

    def is_ready(self):
        c = self.config
        return all([c["enabled"], c["smtp_server"], c["smtp_user"], c["smtp_password"], c["admin_email"]])

    def send_intruder_alert(self, image_path):
        if not self.is_ready():
            return False, "Email alert not configured"

        c = self.config
        sender = c["sender_email"] or c["smtp_user"]
        msg = EmailMessage()
        msg["Subject"] = "SentinelVision Alert: Unauthorized person detected"
        msg["From"] = sender
        msg["To"] = c["admin_email"]
        msg.set_content(
            "SentinelVision detected an unauthorized person.\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Image: {image_path.name}\n"
            f"Admin phone: {c['admin_phone']}\n"
        )

        with image_path.open("rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="image",
                subtype=image_path.suffix.lower().replace(".", "") or "jpeg",
                filename=image_path.name,
            )

        context = ssl.create_default_context()
        with smtplib.SMTP(c["smtp_server"], c["smtp_port"], timeout=20) as server:
            server.starttls(context=context)
            server.login(c["smtp_user"], c["smtp_password"])
            server.send_message(msg)
        return True, "Alert email sent"


class SentinelVisionApp:
    def __init__(self, root):
        ensure_dirs()
        self.root = root
        self.root.title("SentinelVision Software Security")
        self.root.geometry("1180x760")
        self.root.minsize(1050, 680)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.alerts = EmailAlertService(ALERT_CONFIG_PATH)
        self.people = self.load_people()
        self.face_detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.recognizer = self.create_recognizer()
        self.label_to_name = {}
        self.face_model_ready = False
        self.train_face_database()

        self.cap = None
        self.video_thread = None
        self.stop_event = threading.Event()
        self.frame_queue = queue.Queue(maxsize=2)
        self.latest_frame = None
        self.latest_frame_lock = threading.Lock()

        self.last_authorized_save = {}
        self.last_unauthorized_alert = 0
        self.last_spoken_name = None
        self.last_status = "idle"
        self.current_mode = "monitor"

        self.status_var = tk.StringVar(value="Monitoring")
        self.name_var = tk.StringVar(value="-")
        self.count_auth_var = tk.StringVar(value="0")
        self.count_unauth_var = tk.StringVar(value="0")
        self.register_status_var = tk.StringVar(value="Camera ready for enrollment")

        self.setup_ui()
        self.refresh_counts()
        self.load_recent_events()
        self.start_camera()

    def setup_ui(self):
        self.root.configure(bg="#101418")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#101418", borderwidth=0, tabmargins=(0, 4, 0, 0))
        style.configure("TNotebook.Tab", padding=(22, 11), font=("Segoe UI", 10, "bold"),
                        background="#1b242c", foreground="#b8c4cf", borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", "#25313b")], foreground=[("selected", "#f5f7fa")])
        style.configure("TButton", padding=(12, 8), font=("Segoe UI", 10, "bold"),
                        background="#2f6f9f", foreground="#ffffff", borderwidth=0)
        style.map("TButton", background=[("active", "#3b82b6"), ("pressed", "#255a80")])
        style.configure("Secondary.TButton", background="#26323d", foreground="#dce6ea")
        style.map("Secondary.TButton", background=[("active", "#33424f"), ("pressed", "#202b34")])
        style.configure("TEntry", padding=(8, 8), fieldbackground="#f8fafc", foreground="#111827")
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 9), background="#111820",
                        fieldbackground="#111820", foreground="#dce6ea", borderwidth=0)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#1d2730",
                        foreground="#f5f7fa", borderwidth=0)

        header = tk.Frame(self.root, bg="#101418")
        header.pack(fill="x", padx=22, pady=(18, 10))
        tk.Label(header, text="SentinelVision Security Dashboard", fg="#f5f7fa", bg="#101418",
                 font=("Segoe UI", 24, "bold")).pack(side="left")
        tk.Label(header, text="Software CCTV monitoring and face access control",
                 fg="#7f8c98", bg="#101418", font=("Segoe UI", 10)).pack(side="left", padx=(16, 0), pady=(10, 0))

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=22, pady=(0, 18))

        self.monitor_tab = tk.Frame(self.tabs, bg="#101418")
        self.register_tab = tk.Frame(self.tabs, bg="#101418")
        self.tabs.add(self.monitor_tab, text="Live Monitor")
        self.tabs.add(self.register_tab, text="Add Face")

        self.setup_monitor_tab()
        self.setup_register_tab()
        self.tabs.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, _event=None):
        selected = self.tabs.select()
        current_tab = self.tabs.tab(selected, "text") if selected else ""
        self.current_mode = "register" if current_tab == "Add Face" else "monitor"
        if self.current_mode == "register":
            self.root.after(0, lambda: self.set_status("Enrollment Mode", "Recognition paused while adding face", "#334155"))
            self.register_status_var.set("Position one clear face in the frame, then capture.")
        else:
            self.register_status_var.set("Camera ready for enrollment")

    def setup_monitor_tab(self):
        left = tk.Frame(self.monitor_tab, bg="#101418")
        left.pack(side="left", fill="both", expand=True, padx=(0, 14), pady=10)

        video_header = tk.Frame(left, bg="#101418")
        video_header.pack(fill="x", pady=(0, 8))
        tk.Label(video_header, text="Live Camera", fg="#f5f7fa", bg="#101418",
                 font=("Segoe UI", 14, "bold")).pack(side="left")
        tk.Label(video_header, text="Recognition active", fg="#2dd4bf", bg="#101418",
                 font=("Segoe UI", 10, "bold")).pack(side="right", pady=(3, 0))

        self.video_panel = tk.Label(left, bg="#050607", text="Starting camera...", fg="#c9d1d9",
                                    font=("Segoe UI", 13), bd=0, highlightthickness=1,
                                    highlightbackground="#26323d")
        self.video_panel.pack(fill="both", expand=True)

        right = tk.Frame(self.monitor_tab, bg="#101418", width=330)
        right.pack(side="right", fill="y", pady=10)
        right.pack_propagate(False)

        self.status_card = tk.Frame(right, bg="#263238", height=155)
        self.status_card.pack(fill="x", pady=(0, 12))
        self.status_card.pack_propagate(False)
        self.status_title = tk.Label(self.status_card, textvariable=self.status_var, fg="white",
                                     bg="#263238", font=("Segoe UI", 18, "bold"), wraplength=290)
        self.status_title.pack(padx=18, pady=(20, 6), anchor="w")
        self.status_subtitle = tk.Label(self.status_card, textvariable=self.name_var, fg="#dce6ea",
                                        bg="#263238", font=("Segoe UI", 13), wraplength=290)
        self.status_subtitle.pack(padx=18, pady=4, anchor="w")

        stats = tk.Frame(right, bg="#101418")
        stats.pack(fill="x", pady=(0, 12))
        self.make_stat(stats, "Authorized captures", self.count_auth_var).pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.make_stat(stats, "Unauthorized captures", self.count_unauth_var).pack(side="left", fill="x", expand=True, padx=(5, 0))

        tk.Label(right, text="Recent Events", fg="#f5f7fa", bg="#101418",
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(6, 7))
        self.event_tree = ttk.Treeview(right, columns=("time", "type", "name"), show="headings", height=14)
        self.event_tree.heading("time", text="Time")
        self.event_tree.heading("type", text="Type")
        self.event_tree.heading("name", text="Name")
        self.event_tree.column("time", width=85)
        self.event_tree.column("type", width=95)
        self.event_tree.column("name", width=120)
        self.event_tree.pack(fill="both", expand=True)

    def make_stat(self, parent, label, variable):
        frame = tk.Frame(parent, bg="#182027", height=82, highlightthickness=1, highlightbackground="#26323d")
        frame.pack_propagate(False)
        tk.Label(frame, text=label, fg="#a8b3bd", bg="#182027", font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(9, 0))
        tk.Label(frame, textvariable=variable, fg="#f5f7fa", bg="#182027", font=("Segoe UI", 19, "bold")).pack(anchor="w", padx=10)
        return frame

    def setup_register_tab(self):
        form = tk.Frame(self.register_tab, bg="#141c23", width=390, highlightthickness=1, highlightbackground="#26323d")
        form.pack(side="left", fill="y", padx=(0, 16), pady=12, ipadx=14, ipady=14)
        form.pack_propagate(False)

        tk.Label(form, text="Enroll Authorized Face", fg="#f5f7fa", bg="#141c23",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(0, 4))
        tk.Label(form, text="Recognition and alerts pause while this tab is open.",
                 fg="#8ea0ad", bg="#141c23", font=("Segoe UI", 10), wraplength=330,
                 justify="left").pack(anchor="w", pady=(0, 14))

        self.name_entry = self.add_field(form, "Full name")
        self.phone_entry = self.add_field(form, "Phone")
        self.email_entry = self.add_field(form, "Email")
        self.relation_entry = self.add_field(form, "Relation / note")

        ttk.Button(form, text="Capture and Add Face", command=self.register_current_face).pack(fill="x", pady=(14, 7))
        ttk.Button(form, text="Reload Face Database", style="Secondary.TButton",
                   command=self.reload_face_database).pack(fill="x")

        tk.Label(form, textvariable=self.register_status_var,
                 fg="#2dd4bf", bg="#141c23", font=("Segoe UI", 10, "bold"), wraplength=330,
                 justify="left").pack(anchor="w", pady=(16, 0))

        preview_wrap = tk.Frame(self.register_tab, bg="#101418")
        preview_wrap.pack(side="left", fill="both", expand=True, pady=12)
        preview_header = tk.Frame(preview_wrap, bg="#101418")
        preview_header.pack(fill="x", pady=(0, 8))
        tk.Label(preview_header, text="Enrollment Camera", fg="#f5f7fa", bg="#101418",
                 font=("Segoe UI", 14, "bold")).pack(side="left")
        tk.Label(preview_header, text="Capture mode", fg="#fbbf24", bg="#101418",
                 font=("Segoe UI", 10, "bold")).pack(side="right", pady=(3, 0))
        self.register_preview = tk.Label(preview_wrap, bg="#050607", fg="#c9d1d9",
                                         text="Live preview", font=("Segoe UI", 13), bd=0,
                                         highlightthickness=1, highlightbackground="#26323d")
        self.register_preview.pack(fill="both", expand=True)

    def add_field(self, parent, label):
        tk.Label(parent, text=label, fg="#dce6ea", bg="#141c23", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(8, 3))
        entry = ttk.Entry(parent, font=("Segoe UI", 10))
        entry.pack(fill="x")
        return entry

    def load_people(self):
        if PEOPLE_DB_PATH.exists():
            try:
                return json.loads(PEOPLE_DB_PATH.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def save_people(self):
        PEOPLE_DB_PATH.write_text(json.dumps(self.people, indent=2), encoding="utf-8")

    def create_recognizer(self):
        if not hasattr(cv2, "face"):
            return None
        return cv2.face.LBPHFaceRecognizer_create()

    def detect_faces(self, gray, min_size=(60, 60)):
        faces = self.face_detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=min_size,
        )
        return [(int(y), int(x + w), int(y + h), int(x)) for x, y, w, h in faces]

    def face_crop(self, gray, loc):
        top, right, bottom, left = loc
        top = max(0, top)
        left = max(0, left)
        bottom = min(gray.shape[0], bottom)
        right = min(gray.shape[1], right)
        if bottom <= top or right <= left:
            return None
        crop = gray[top:bottom, left:right]
        crop = cv2.resize(crop, FACE_SIZE)
        return cv2.equalizeHist(crop)

    def train_face_database(self):
        if self.recognizer is None:
            self.face_model_ready = False
            self.log_ui("Install opencv-contrib-python for face recognition support")
            return

        faces = []
        labels = []
        name_to_label = {}
        image_extensions = {".jpg", ".jpeg", ".png", ".bmp"}

        for image_path in KNOWN_FACES_DIR.rglob("*"):
            if image_path.suffix.lower() not in image_extensions:
                continue

            image = cv2.imread(str(image_path))
            if image is None:
                continue
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            locations = self.detect_faces(gray)
            if not locations:
                continue

            relative = image_path.relative_to(KNOWN_FACES_DIR)
            name = relative.parts[0] if len(relative.parts) > 1 else image_path.stem
            if name not in name_to_label:
                name_to_label[name] = len(name_to_label)
            crop = self.face_crop(gray, locations[0])
            if crop is None:
                continue
            faces.append(crop)
            labels.append(name_to_label[name])

        if not faces:
            self.label_to_name = {}
            self.face_model_ready = False
            self.log_ui("No authorized faces trained yet")
            return

        self.recognizer.train(faces, np.array(labels, dtype=np.int32))
        self.label_to_name = {label: name for name, label in name_to_label.items()}
        self.face_model_ready = True
        self.log_ui(f"Loaded {len(faces)} authorized face sample(s)")

    def start_camera(self):
        self.cap = cv2.VideoCapture(CAM_INDEX)
        if not self.cap.isOpened():
            self.set_status("Camera not available", "-", "#5b1f23")
            self.log_ui("Camera not available")
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.stop_event.clear()
        self.video_thread = threading.Thread(target=self.camera_loop, daemon=True)
        self.video_thread.start()
        self.root.after(30, self.update_frame)
        self.log_ui("Camera started")

    def camera_loop(self):
        frame_count = 0
        while not self.stop_event.is_set():
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            if FRAME_FLIP_CODE is not None:
                frame = cv2.flip(frame, FRAME_FLIP_CODE)
            with self.latest_frame_lock:
                self.latest_frame = frame.copy()

            frame_count += 1
            display_frame = frame.copy()

            if frame_count % PROCESS_EVERY_N == 0:
                small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                gray_small = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                face_locations = self.detect_faces(gray_small, min_size=(24, 24))
                if self.current_mode == "register":
                    display_frame = self.draw_enrollment_frame(frame, face_locations)
                else:
                    detections = self.classify_faces(frame, face_locations)
                    display_frame = self.handle_detections(frame, face_locations, detections)

            self.push_frame(display_frame)
            time.sleep(0.01)

        if self.cap:
            self.cap.release()

    def classify_faces(self, frame, face_locations):
        detections = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        for loc in face_locations:
            name = None
            if self.face_model_ready and self.recognizer is not None:
                full_loc = tuple(int(v * 4) for v in loc)
                crop = self.face_crop(gray, full_loc)
                if crop is not None:
                    label, confidence = self.recognizer.predict(crop)
                    if confidence <= RECOGNITION_THRESHOLD:
                        name = self.label_to_name.get(label)
            detections.append(name)
        return detections

    def draw_enrollment_frame(self, frame, face_locations):
        display = frame.copy()
        for loc in face_locations:
            top, right, bottom, left = [int(v * 4) for v in loc]
            cv2.rectangle(display, (left, top), (right, bottom), (0, 190, 255), 2)
            cv2.putText(display, "CAPTURE CANDIDATE", (left, max(25, top - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 190, 255), 2)

        if len(face_locations) == 1:
            message = "One face detected. Ready to capture."
        elif len(face_locations) == 0:
            message = "No face detected. Move closer to the camera."
        else:
            message = "Multiple faces detected. Keep only one face in frame."
        self.root.after(0, lambda m=message: self.register_status_var.set(m))
        return display

    def handle_detections(self, frame, face_locations, detections):
        display = frame.copy()
        has_unauthorized = any(name is None for name in detections)
        authorized_names = [name for name in detections if name]

        for loc, name in zip(face_locations, detections):
            top, right, bottom, left = [int(v * 4) for v in loc]
            color = (0, 0, 255) if name is None else (0, 180, 0)
            label = "UNAUTHORIZED" if name is None else name
            cv2.rectangle(display, (left, top), (right, bottom), color, 2)
            cv2.putText(display, label, (left, max(25, top - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        if has_unauthorized:
            self.root.after(0, lambda: self.set_status("UNAUTHORIZED WARNING", "Please go back. Admin has been notified.", "#7f1d1d"))
            self.capture_unauthorized(frame)
            self.last_spoken_name = None
        elif authorized_names:
            name = authorized_names[0]
            self.root.after(0, lambda n=name: self.set_status("ACCESS GRANTED", f"Welcome, {n}", "#17693a"))
            self.capture_authorized(frame, name)
            if self.last_spoken_name != name:
                self.last_spoken_name = name
                threading.Thread(target=self.speak, args=(f"Welcome {name}",), daemon=True).start()
        else:
            self.root.after(0, lambda: self.set_status("Monitoring", "Waiting for face", "#263238"))
            self.last_spoken_name = None

        return display

    def capture_authorized(self, frame, name):
        now = time.time()
        if now - self.last_authorized_save.get(name, 0) < AUTHORIZED_SAVE_COOLDOWN:
            return
        self.last_authorized_save[name] = now
        person_dir = AUTHORIZED_CAPTURE_DIR / clean_filename(name)
        person_dir.mkdir(parents=True, exist_ok=True)
        path = person_dir / f"{timestamp()}.jpg"
        cv2.imwrite(str(path), frame)
        self.log_event("authorized", name, path)

    def capture_unauthorized(self, frame):
        now = time.time()
        if now - self.last_unauthorized_alert < UNAUTHORIZED_ALERT_COOLDOWN:
            return
        self.last_unauthorized_alert = now
        path = UNAUTHORIZED_CAPTURE_DIR / f"unknown_{timestamp()}.jpg"
        cv2.imwrite(str(path), frame)
        self.log_event("unauthorized", "Unknown", path)
        threading.Thread(target=self.send_alert_for_path, args=(path,), daemon=True).start()

    def log_event(self, event_type, name, image_path):
        new_file = not EVENT_LOG_PATH.exists()
        with EVENT_LOG_PATH.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if new_file:
                writer.writerow(["time", "type", "name", "image_path"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), event_type, name, str(image_path)])
        self.root.after(0, self.load_recent_events)
        self.root.after(0, self.refresh_counts)

    def load_recent_events(self):
        if not hasattr(self, "event_tree"):
            return
        for item in self.event_tree.get_children():
            self.event_tree.delete(item)
        if not EVENT_LOG_PATH.exists():
            return
        with EVENT_LOG_PATH.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))[-25:]
        for row in reversed(rows):
            event_time = row["time"].split(" ")[-1]
            self.event_tree.insert("", "end", values=(event_time, row["type"], row["name"]))

    def refresh_counts(self):
        auth_count = len(list(AUTHORIZED_CAPTURE_DIR.rglob("*.jpg"))) if AUTHORIZED_CAPTURE_DIR.exists() else 0
        unauth_count = len(list(UNAUTHORIZED_CAPTURE_DIR.glob("*.jpg"))) if UNAUTHORIZED_CAPTURE_DIR.exists() else 0
        self.count_auth_var.set(str(auth_count))
        self.count_unauth_var.set(str(unauth_count))

    def push_frame(self, frame):
        try:
            if self.frame_queue.full():
                self.frame_queue.get_nowait()
            self.frame_queue.put_nowait(frame)
        except queue.Empty:
            pass

    def update_frame(self):
        try:
            frame = self.frame_queue.get_nowait()
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            monitor_image = Image.fromarray(rgb)
            monitor_image.thumbnail((780, 560), Image.Resampling.LANCZOS)
            monitor_imgtk = ImageTk.PhotoImage(image=monitor_image)
            self.video_panel.imgtk = monitor_imgtk
            self.video_panel.config(image=monitor_imgtk, text="")

            register_image = Image.fromarray(rgb)
            register_image.thumbnail((720, 560), Image.Resampling.LANCZOS)
            register_imgtk = ImageTk.PhotoImage(image=register_image)
            self.register_preview.imgtk = register_imgtk
            self.register_preview.config(image=register_imgtk, text="")
        except queue.Empty:
            pass
        self.root.after(30, self.update_frame)

    def set_status(self, title, subtitle, color):
        if self.last_status == f"{title}:{subtitle}":
            return
        self.last_status = f"{title}:{subtitle}"
        self.status_var.set(title)
        self.name_var.set(subtitle)
        self.status_card.config(bg=color)
        self.status_title.config(bg=color)
        self.status_subtitle.config(bg=color)

    def register_current_face(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Name required", "Authorized person ka naam enter karein.")
            return

        with self.latest_frame_lock:
            frame = None if self.latest_frame is None else self.latest_frame.copy()
        if frame is None:
            messagebox.showerror("Camera", "Camera frame available nahi hai.")
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        locations = self.detect_faces(gray)
        if len(locations) != 1:
            messagebox.showwarning("Face capture", "Camera me sirf ek clear face rakhein.")
            return

        crop = self.face_crop(gray, locations[0])
        if crop is None:
            messagebox.showerror("Face capture", "Face encode nahi ho paya. Light aur angle check karein.")
            return

        safe_name = clean_filename(name)
        person_dir = KNOWN_FACES_DIR / safe_name
        person_dir.mkdir(parents=True, exist_ok=True)
        image_path = person_dir / f"{safe_name}_{timestamp()}.jpg"
        top, right, bottom, left = locations[0]
        face_margin_x = int((right - left) * 0.35)
        face_margin_y = int((bottom - top) * 0.45)
        crop_top = max(0, top - face_margin_y)
        crop_left = max(0, left - face_margin_x)
        crop_bottom = min(frame.shape[0], bottom + face_margin_y)
        crop_right = min(frame.shape[1], right + face_margin_x)
        enrollment_photo = frame[crop_top:crop_bottom, crop_left:crop_right]
        if enrollment_photo.size == 0:
            enrollment_photo = frame
        cv2.imwrite(str(image_path), enrollment_photo)

        person = {
            "name": name,
            "phone": self.phone_entry.get().strip(),
            "email": self.email_entry.get().strip(),
            "relation": self.relation_entry.get().strip(),
            "image_path": str(image_path),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.people.append(person)
        self.save_people()
        self.train_face_database()
        self.log_event("registered", name, image_path)
        self.clear_registration_form()
        self.register_status_var.set(f"{name} added to authorized database.")
        messagebox.showinfo("Registered", f"{name} authorized database me add ho gaya.")

    def clear_registration_form(self):
        for entry in [self.name_entry, self.phone_entry, self.email_entry, self.relation_entry]:
            entry.delete(0, tk.END)

    def reload_face_database(self):
        self.train_face_database()
        messagebox.showinfo("Reloaded", f"{len(self.label_to_name)} authorized person loaded.")

    def send_alert_for_path(self, path, show_popup=False):
        try:
            ok, message = self.alerts.send_intruder_alert(path)
        except Exception as e:
            ok, message = False, str(e)
        self.root.after(0, lambda: self.log_ui(message))
        if show_popup:
            self.root.after(0, lambda: messagebox.showinfo("Alert test", message if ok else f"Failed: {message}"))

    def speak(self, text):
        if pyttsx3 is None:
            return
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 150)
            engine.say(text)
            engine.runAndWait()
        except Exception:
            pass

    def log_ui(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def on_close(self):
        self.stop_event.set()
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join(timeout=1.5)
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SentinelVisionApp(root)
    root.mainloop()
