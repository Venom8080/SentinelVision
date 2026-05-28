"""
Face Encoding Builder for SentinelVision Defense System
Scans known_faces/ directory and generates encodings.pickle file
"""

import os
import pickle
from pathlib import Path
import face_recognition

BASE_DIR = Path(__file__).parent
KNOWN_FACES_DIR = BASE_DIR / 'known_faces'
ENCODINGS_FILE = BASE_DIR / 'encodings.pickle'


def build_encodings(known_dir=KNOWN_FACES_DIR, enc_file=ENCODINGS_FILE):
    """Scan known_faces directory and build encodings"""
    print(f"[INFO] Building face encodings from: {known_dir}")
    
    if not known_dir.exists():
        print(f"[ERROR] Directory not found: {known_dir}")
        return [], []
    
    encodings = []
    names = []
    
    # Scan all files in known_faces directory (including subdirectories)
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    
    for root, dirs, files in os.walk(known_dir):
        for filename in files:
            filepath = Path(root) / filename
            
            # Check if it's an image file
            if filepath.suffix.lower() not in image_extensions:
                continue
            
            try:
                # Load image
                image = face_recognition.load_image_file(str(filepath))
                
                # Find face locations
                face_locations = face_recognition.face_locations(image, model='hog')
                
                if len(face_locations) == 0:
                    print(f"  [WARN] No face found in: {filepath}")
                    continue
                
                # Get face encoding (use first face if multiple)
                face_encodings = face_recognition.face_encodings(image, face_locations)
                
                if len(face_encodings) == 0:
                    print(f"  [WARN] Could not encode face in: {filepath}")
                    continue
                
                # Use folder name or filename (without extension) as person name
                relative_path = filepath.relative_to(known_dir)
                if len(relative_path.parts) > 1:
                    # If in subdirectory, use subdirectory name
                    person_name = relative_path.parts[0]
                else:
                    # Otherwise use filename without extension
                    person_name = filepath.stem
                
                # Add encoding and name
                encodings.append(face_encodings[0])
                names.append(person_name)
                print(f"  [OK] Encoded: {person_name} from {filepath.name}")
                
            except Exception as e:
                print(f"  [ERROR] Processing {filepath}: {e}")
                continue
    
    if len(encodings) == 0:
        print("[ERROR] No face encodings generated. Check your images in known_faces/")
        return [], []
    
    # Save encodings to pickle file
    try:
        with open(enc_file, 'wb') as f:
            pickle.dump({'encodings': encodings, 'names': names}, f)
        print(f"[SUCCESS] Saved {len(encodings)} encodings to {enc_file}")
    except Exception as e:
        print(f"[ERROR] Failed to save encodings: {e}")
        return [], []
    
    return encodings, names


if __name__ == '__main__':
    print("=" * 50)
    print("SentinelVision Defense System - Face Encoding Builder")
    print("=" * 50)
    
    encodings, names = build_encodings()
    
    if encodings:
        print(f"\n[SUMMARY]")
        print(f"  Total encodings: {len(encodings)}")
        print(f"  Unique names: {len(set(names))}")
        print(f"  Names: {', '.join(set(names))}")
        print("\n[INFO] You can now run SENTINELVISION_autorun.py")
    else:
        print("\n[ERROR] Failed to build encodings. Please check your known_faces/ folder.")

