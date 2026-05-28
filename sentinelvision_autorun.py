
import os
import time
import threading
import queue
import pickle
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import cv2
import face_recognition
import numpy as np
import serial
import serial.tools.list_ports
from playsound import playsound
from SENTINELVISION_helpers import SerialController, load_encodings

# Text-to-speech for welcome messages
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("Warning: pyttsx3 not available. Install with: pip install pyttsx3")

# Paths
BASE_DIR = Path(__file__).parent
ENCODINGS_PATH = BASE_DIR / 'encodings.pickle'
WELCOME_SOUND = BASE_DIR / 'welcome.mp3'
UNAUTH_SOUND = BASE_DIR / 'unauth.mp3'

# Globals
CAM_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FACE_TOLERANCE = 0.5
PROCESS_EVERY_N = 3  # Process every Nth frame for performance

class SentinelVisionApp:
    def __init__(self, root):
        self.root = root
        self.root.title('SentinelVision Defense — Final')
        self.root.geometry('900x600')
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

        # Serial controller (to Arduino)
        self.serial = SerialController(baudrate=115200)

        # Face encodings
        self.known_encodings, self.known_names = load_encodings(ENCODINGS_PATH)
        if len(self.known_encodings) == 0:
            self.log_msg("WARNING: No face encodings loaded! Run build_encodings.py first.")
        
        # Tracking state
        self.last_face_time = 0
        self.current_status = "Waiting for face…"
        self.current_name = None
        self.laser_active = False
        self.last_match_name = None
        self.last_face_locations = []
        self.access_ui_active = False  # Flag to prevent multiple access UIs
        self.last_welcomed_name = None  # Track last welcomed name to avoid repeating

        # Camera thread
        self.cap = None
        self.video_thread = None
        self.stop_event = threading.Event()
        self.frame_queue = queue.Queue(maxsize=2)
        self.camera_running = False

        # UI
        self._setup_ui()

        # Start camera
        self.start_camera()

    def _setup_ui(self):
        # Left: video panel with face detection overlay
        self.video_panel = tk.Label(self.root, bg='black', text='Initializing camera...')
        self.video_panel.place(x=10, y=10, width=640, height=480)

        # Right: status panel
        right_frame = tk.Frame(self.root, bg='#f0f0f0')
        right_frame.place(x=660, y=10, width=230, height=480)

        # Status message (large, color-coded)
        status_frame = tk.Frame(right_frame, bg='#f0f0f0')
        status_frame.pack(pady=10, padx=10, fill='x')
        
        self.status_label = tk.Label(
            status_frame, 
            text='Waiting for face…', 
            font=('Helvetica', 14, 'bold'),
            bg='#f0f0f0',
            fg='black',
            wraplength=210,
            justify='center'
        )
        self.status_label.pack(pady=5)

        # Name display
        name_frame = tk.Frame(right_frame, bg='#f0f0f0')
        name_frame.pack(pady=5, padx=10, fill='x')
        ttk.Label(name_frame, text='Name:', font=('Helvetica', 10)).pack(anchor='w')
        self.name_var = tk.StringVar(value='-')
        self.name_label = tk.Label(
            name_frame, 
            textvariable=self.name_var, 
            font=('Helvetica', 12, 'bold'),
            bg='#f0f0f0',
            fg='blue'
        )
        self.name_label.pack(anchor='w', pady=2)

        # Laser status
        laser_frame = tk.Frame(right_frame, bg='#f0f0f0')
        laser_frame.pack(pady=5, padx=10, fill='x')
        ttk.Label(laser_frame, text='Laser:', font=('Helvetica', 10)).pack(anchor='w')
        self.laser_var = tk.StringVar(value='OFF')
        self.laser_label = tk.Label(
            laser_frame, 
            textvariable=self.laser_var, 
            font=('Helvetica', 12, 'bold'),
            bg='#f0f0f0',
            fg='red'
        )
        self.laser_label.pack(anchor='w', pady=2)

        # Separator
        ttk.Separator(right_frame, orient='horizontal').pack(fill='x', pady=10, padx=10)

        # Serial connection
        self.serial_label = tk.StringVar(value='Serial: Not connected')
        ttk.Label(right_frame, textvariable=self.serial_label, font=('Helvetica', 9)).pack(pady=5)
        
        self.btn_scan = ttk.Button(right_frame, text='🔌 Scan Serial Port', command=self.scan_serial)
        self.btn_scan.pack(fill='x', padx=10, pady=4)

        # Log area
        self.log = tk.Text(self.root, height=6, font=('Consolas', 9))
        self.log.place(x=10, y=500, width=880, height=90)

    def log_msg(self, text):
        ts = time.strftime('%Y-%m-%d %H:%M:%S')
        self.log.insert(tk.END, f'[{ts}] {text}\n')
        self.log.see(tk.END)

    def scan_serial(self):
        """Auto-detect and connect to Arduino"""
        port = self.serial.auto_connect()
        if port:
            self.serial_label.set(f'Serial: {port} ✅')
            self.log_msg(f'✅ Connected to Arduino on {port}')
        else:
            self.serial_label.set('Serial: Not connected ❌')
            self.log_msg('⚠️ Arduino not found. Check USB connection.')

    def start_camera(self):
        """Start webcam capture and face detection loop"""
        if self.camera_running:
            return  # Already running
        
        self.cap = cv2.VideoCapture(CAM_INDEX)
        if not self.cap.isOpened():
            self.log_msg('ERROR: Could not open camera')
            return
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.stop_event.clear()
        self.camera_running = True
        self.video_thread = threading.Thread(target=self._camera_loop, daemon=True)
        self.video_thread.start()
        self.root.after(30, self._update_frame)
        self.log_msg('Camera started')
        self.root.after(0, lambda: self._update_status_ui("Waiting for face…", "-", False, 'black'))

    def stop_camera(self):
        """Stop webcam capture and close OpenCV windows"""
        if not self.camera_running:
            return  # Already stopped
        
        self.log_msg('Stopping camera...')
        self.stop_event.set()
        self.camera_running = False
        
        # Wait for thread to finish (with timeout)
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join(timeout=2.0)
        
        # Release camera
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Close all OpenCV windows
        cv2.destroyAllWindows()
        
        self.log_msg('Camera stopped')

    def _map_to_servo_angle(self, coord, coord_max, invert=False):
        """Map frame coordinate to servo angle (0-180)"""
        if invert:
            # For tilt: top of frame (0) = 180°, bottom (height) = 0°
            return int(np.interp(coord, [0, coord_max], [180, 0]))
        else:
            # For pan: left (0) = 0°, right (width) = 180°
            return int(np.interp(coord, [0, coord_max], [0, 180]))

    def _camera_loop(self):
        frame_count = 0
        while not self.stop_event.is_set():
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            
            # Flip frame horizontally to fix mirror effect (ulta video)
            frame = cv2.flip(frame, 1)
            
            frame_count += 1
            
            # Resize for faster processing (0.25x = 4x smaller)
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # Process every Nth frame for performance
            if frame_count % PROCESS_EVERY_N == 0:
                # Skip processing if access UI is active
                if self.access_ui_active:
                    time.sleep(0.1)
                    continue
                
                # Detect faces
                face_locations = face_recognition.face_locations(rgb_small, model='hog')
                face_encodings = face_recognition.face_encodings(rgb_small, face_locations)
                
                # Store for drawing outside this block
                self.last_face_locations = face_locations

                detected_face = False
                authorized_faces = []
                unauthorized_faces = []
                
                if len(face_encodings) > 0:
                    detected_face = True
                    self.last_face_time = time.time()
                    
                    # Check all faces for authorization
                    for i, enc in enumerate(face_encodings):
                        match_name = None
                        if len(self.known_encodings) > 0:
                            matches = face_recognition.compare_faces(
                                self.known_encodings, enc, tolerance=FACE_TOLERANCE
                            )
                            face_distances = face_recognition.face_distance(self.known_encodings, enc)
                            best_idx = np.argmin(face_distances) if len(face_distances) > 0 else None
                            
                            if best_idx is not None and matches[best_idx]:
                                match_name = self.known_names[best_idx]
                                authorized_faces.append((match_name, i))
                            else:
                                unauthorized_faces.append(i)
                        else:
                            unauthorized_faces.append(i)
                
                # Store match name for drawing (first authorized face if any)
                self.last_match_name = authorized_faces[0][0] if authorized_faces else None

                # Draw bounding boxes for ALL detected faces immediately
                if len(face_locations) > 0:
                    for i, loc in enumerate(face_locations):
                        top, right, bottom, left = loc
                        # Convert to original frame scale (multiply by 4)
                        top_full = top * 4
                        right_full = right * 4
                        bottom_full = bottom * 4
                        left_full = left * 4
                        
                        # Check if this face is authorized
                        is_authorized = i in [idx for _, idx in authorized_faces]
                        
                        if is_authorized:
                            # Authorized face - green box
                            auth_name = next((name for name, idx in authorized_faces if idx == i), "Authorized")
                            cv2.rectangle(frame, (int(left_full), int(top_full)), 
                                        (int(right_full), int(bottom_full)), (0, 255, 0), 2)
                            cv2.putText(frame, auth_name, (int(left_full), int(top_full) - 10),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        else:
                            # Unauthorized face - red box
                            cv2.rectangle(frame, (int(left_full), int(top_full)), 
                                        (int(right_full), int(bottom_full)), (0, 0, 255), 2)
                            cv2.putText(frame, "UNAUTHORIZED", (int(left_full), int(top_full) - 10),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                # Multiple faces logic:
                # - If all faces are authorized, show access UI
                # - If at least one unauthorized, continue tracking
                if len(authorized_faces) > 0 and len(unauthorized_faces) == 0:
                    # All faces are authorized - show access UI
                    first_authorized_name = authorized_faces[0][0]
                    self.current_status = f"🟢 Access Granted: Welcome {first_authorized_name}"
                    self.current_name = first_authorized_name
                    self.laser_active = False
                    
                    # Speak welcome message with name (only once per person)
                    if first_authorized_name != self.last_welcomed_name:
                        self.log_msg(f'🎤 Calling TTS for: {first_authorized_name}')
                        self._speak_welcome(first_authorized_name)
                        self.last_welcomed_name = first_authorized_name
                    
                    # Send AUTH command to Arduino (laser off, stop tracking)
                    if self.serial.is_open():
                        self.serial.send_auth_command(first_authorized_name)
                        self.serial.send_cmd('LASER_OFF')
                    
                    # Show access UI (stops camera, shows fullscreen, waits for SPACE)
                    self.root.after(0, lambda n=first_authorized_name: self.show_access_ui(n))
                    
                # Handle unauthorized face (at least one unauthorized present)
                elif detected_face:
                    # Track first unauthorized face (or first face if mixed)
                    track_idx = unauthorized_faces[0] if unauthorized_faces else 0
                    
                    if len(face_locations) > track_idx:
                        loc = face_locations[track_idx]  # top, right, bottom, left in small frame
                        top, right, bottom, left = loc
                        
                        # Convert to original frame scale (multiply by 4)
                        top_full = top * 4
                        right_full = right * 4
                        bottom_full = bottom * 4
                        left_full = left * 4
                        
                        # Calculate center coordinates
                        cx = (left_full + right_full) / 2
                        cy = (top_full + bottom_full) / 2
                        
                        # Map to servo angles
                        pan_angle = self._map_to_servo_angle(cx, FRAME_WIDTH, invert=False)
                        tilt_angle = self._map_to_servo_angle(cy, FRAME_HEIGHT, invert=True)
                        
                        # Send tracking command to Arduino
                        if self.serial.is_open():
                            self.serial.send_track_command(pan_angle, tilt_angle)
                            self.serial.send_cmd('LASER_ON')
                    
                    # Update status
                    self.current_status = "🔴 Warning: Please Step Back / Go Away"
                    self.current_name = "Unknown"
                    self.laser_active = True
                    
                    # Update UI
                    self.root.after(0, lambda s=self.current_status, n=self.current_name, 
                                  l=self.laser_active: self._update_status_ui(s, n, l, 'red'))
                    
                    self.log_msg('⚠️ Unauthorized face detected - Tracking active')
                    threading.Thread(target=self._play_unauth, daemon=True).start()
                    
                # No face detected
                else:
                    # Turn off laser if no face for a while
                    if self.laser_active and (time.time() - self.last_face_time) > 2.0:
                        self.laser_active = False
                        if self.serial.is_open():
                            self.serial.send_cmd('LASER_OFF')
                    
                    self.current_status = "Waiting for face…"
                    self.current_name = None
                    self.last_match_name = None
                    self.last_face_locations = []
                    self.last_welcomed_name = None  # Reset welcomed name when no face
                    
                    # Update UI
                    self.root.after(0, lambda s=self.current_status: 
                                  self._update_status_ui(s, "-", False, 'black'))

            # Put frame in queue for UI display (non-blocking)
            try:
                if self.frame_queue.full():
                    _ = self.frame_queue.get_nowait()
                self.frame_queue.put_nowait(frame)
            except:
                pass

            time.sleep(0.01)  # Small delay to prevent CPU overload

        # Cleanup
        if self.cap:
            self.cap.release()

    def _update_status_ui(self, status, name, laser_on, color):
        """Update status UI elements (called from main thread)"""
        self.status_label.config(text=status, fg=color)
        self.name_var.set(name)
        self.laser_var.set('ON' if laser_on else 'OFF')
        self.laser_label.config(fg='red' if laser_on else 'gray')

    def _update_frame(self):
        """Update video frame in UI"""
        try:
            frame = self.frame_queue.get_nowait()
            # Convert BGR to RGB for display
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil = Image.fromarray(rgb_frame)
            pil = pil.resize((640, 480), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=pil)
            self.video_panel.imgtk = imgtk
            self.video_panel.config(image=imgtk, text='')
        except queue.Empty:
            pass
        self.root.after(30, self._update_frame)

    def show_access_ui(self, name):
        """Show fullscreen green access granted UI and wait for SPACE key"""
        if self.access_ui_active:
            return  # Already showing
        
        self.access_ui_active = True
        
        # Stop camera first
        self.stop_camera()
        
        # Create fullscreen window
        access_window = tk.Toplevel(self.root)
        access_window.attributes('-fullscreen', True)
        access_window.attributes('-topmost', True)
        access_window.configure(bg='#00ff00')
        access_window.overrideredirect(True)
        
        # Bind SPACE key to close window and restart camera
        def on_space_key(event):
            if event.keysym == 'space':
                access_window.destroy()
                self.access_ui_active = False
                # Restart camera
                self.root.after(100, self.start_camera)
                self.log_msg(f'Access UI closed - Camera restarted')
        
        access_window.bind('<KeyPress>', on_space_key)
        access_window.focus_set()
        
        # Create message label
        welcome_text = f'●{name} Verified — Defense System Stand Down'
        lbl = tk.Label(
            access_window,
            text=welcome_text,
            font=('Helvetica', 48, 'bold'),
            bg='#00ff00',
            fg='black',
            wraplength=1200
        )
        lbl.pack(expand=True)
        
        # Instruction label
        instruction_text = 'Press SPACE to continue'
        instruction_lbl = tk.Label(
            access_window,
            text=instruction_text,
            font=('Helvetica', 24),
            bg='#00ff00',
            fg='#004400'
        )
        instruction_lbl.pack(pady=50)
        
        # Play sound
        if WELCOME_SOUND.exists():
            try:
                playsound(str(WELCOME_SOUND), block=False)
            except:
                pass
        
        # Update status in main UI
        self.root.after(0, lambda: self._update_status_ui(
            f"🟢 Access Granted: Welcome {name}", name, False, 'green'
        ))
        
        self.log_msg(f'✅ Access granted for {name} - Waiting for SPACE key')
        
        # Handle window close
        def on_close():
            self.access_ui_active = False
            access_window.destroy()
            self.root.after(100, self.start_camera)
        
        access_window.protocol('WM_DELETE_WINDOW', on_close)

    def _speak_welcome(self, name):
        """Speak welcome message with person's name using text-to-speech"""
        def speak():
            try:
                self.log_msg(f'🔊 TTS_AVAILABLE: {TTS_AVAILABLE}')
                if TTS_AVAILABLE:
                    try:
                        engine = pyttsx3.init()
                        # Set properties for better voice
                        engine.setProperty('rate', 150)  # Speed of speech
                        engine.setProperty('volume', 0.9)  # Volume level
                        
                        # Try to set a better voice (if available)
                        try:
                            voices = engine.getProperty('voices')
                            if len(voices) > 0:
                                # Prefer female voice if available, otherwise use first available
                                for voice in voices:
                                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                                        engine.setProperty('voice', voice.id)
                                        break
                                else:
                                    engine.setProperty('voice', voices[0].id)
                        except:
                            pass  # Use default voice if selection fails
                        
                        # Speak welcome message
                        welcome_text = f"Welcome {name}"
                        self.log_msg(f'🔊 Speaking: {welcome_text}')
                        engine.say(welcome_text)
                        engine.runAndWait()
                        self.log_msg(f'✅ TTS completed: {welcome_text}')
                    except Exception as e:
                        self.log_msg(f'❌ TTS engine error: {e}')
                        # Fallback: use Windows SAPI directly
                        try:
                            import win32com.client
                            speaker = win32com.client.Dispatch("SAPI.SpVoice")
                            speaker.Speak(f"Welcome {name}")
                            self.log_msg(f'🔊 Spoke via SAPI: Welcome {name}')
                        except:
                            # Final fallback: use PowerShell TTS
                            try:
                                import subprocess
                                text = f"Welcome {name}"
                                ps_command = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak("{text}")'
                                subprocess.run(['powershell', '-Command', ps_command], 
                                             shell=True, capture_output=True, timeout=5)
                                self.log_msg(f'🔊 Spoke via PowerShell: Welcome {name}')
                            except Exception as e2:
                                self.log_msg(f'⚠️ All TTS methods failed: {e2}')
                else:
                    # Fallback: use Windows built-in TTS
                    try:
                        import win32com.client
                        speaker = win32com.client.Dispatch("SAPI.SpVoice")
                        speaker.Speak(f"Welcome {name}")
                        self.log_msg(f'🔊 Spoke via SAPI (fallback): Welcome {name}')
                    except:
                        # Final fallback: use PowerShell TTS
                        try:
                            import subprocess
                            text = f"Welcome {name}"
                            ps_command = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak("{text}")'
                            subprocess.run(['powershell', '-Command', ps_command], 
                                         shell=True, capture_output=True, timeout=5)
                            self.log_msg(f'🔊 Spoke via PowerShell (fallback): Welcome {name}')
                        except Exception as e:
                            self.log_msg(f'⚠️ TTS not available. Error: {e}')
            except Exception as e:
                self.log_msg(f'❌ TTS error: {e}')
        
        # Run in separate thread to avoid blocking
        threading.Thread(target=speak, daemon=True).start()

    def _play_unauth(self):
        try:
            if UNAUTH_SOUND.exists():
                playsound(str(UNAUTH_SOUND))
        except Exception as e:
            self.log_msg(f'Unauth sound error: {e}')

    def on_close(self):
        """Handle application close"""
        self.log_msg('Shutting down...')
        self.stop_camera()  # Use stop_camera function
        if self.serial.is_open():
            self.serial.send_cmd('LASER_OFF')
            self.serial.close()
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    app = SentinelVisionApp(root)
    root.mainloop()