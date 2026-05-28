"""
Face Encoding Utility
Encodes faces from images in known_faces/ directory and saves to encodings.pickle
"""

import face_recognition
import pickle
from pathlib import Path
import os

BASE_DIR = Path(__file__).parent
KNOWN_FACES_DIR = BASE_DIR / 'known_faces'
ENCODINGS_PATH = BASE_DIR / 'encodings.pickle'

def encode_faces():
    """Encode all faces from known_faces directory"""
    known_encodings = []
    known_names = []
    
    if not KNOWN_FACES_DIR.exists():
        print(f"Error: {KNOWN_FACES_DIR} directory not found!")
        print(f"Creating {KNOWN_FACES_DIR} directory...")
        KNOWN_FACES_DIR.mkdir()
        print("Please add face images to this directory and run again.")
        return
    
    # Get all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    image_files = []
    for ext in image_extensions:
        image_files.extend(KNOWN_FACES_DIR.glob(f'*{ext}'))
        image_files.extend(KNOWN_FACES_DIR.glob(f'*{ext.upper()}'))
    
    if len(image_files) == 0:
        print(f"No images found in {KNOWN_FACES_DIR}")
        print("Supported formats: .jpg, .jpeg, .png, .bmp")
        return
    
    print(f"Found {len(image_files)} image(s). Processing...")
    
    for image_path in image_files:
        print(f"Processing: {image_path.name}")
        
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Find face locations
            face_locations = face_recognition.face_locations(image)
            
            if len(face_locations) == 0:
                print(f"  ⚠ No face found in {image_path.name}")
                continue
            
            if len(face_locations) > 1:
                print(f"  ⚠ Multiple faces found in {image_path.name}, using first one")
            
            # Encode face
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if len(face_encodings) > 0:
                # Extract name from filename (without extension)
                name = image_path.stem
                known_encodings.append(face_encodings[0])
                known_names.append(name)
                print(f"  ✅ Encoded: {name}")
            else:
                print(f"  ⚠ Could not encode face in {image_path.name}")
                
        except Exception as e:
            print(f"  ❌ Error processing {image_path.name}: {e}")
    
    # Save encodings
    if len(known_encodings) > 0:
        data = {
            'encodings': known_encodings,
            'names': known_names
        }
        
        with open(ENCODINGS_PATH, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"\n✅ Successfully encoded {len(known_encodings)} face(s)")
        print(f"Encodings saved to: {ENCODINGS_PATH}")
        print("\nEncoded names:")
        for name in known_names:
            print(f"  - {name}")
    else:
        print("\n❌ No faces were encoded. Please check your images.")

if __name__ == '__main__':
    print("=" * 50)
    print("SentinelVision Face Encoding Utility")
    print("=" * 50)
    print()
    encode_faces()
    print()
    print("=" * 50)

