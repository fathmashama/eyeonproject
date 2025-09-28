import os
import face_recognition
import pickle
import cv2

dataset_path = "dataset"
encoding_file_path = "FaceDataSheet/encodings.pkl"

print("🔁 Starting face encoding...")

known_encodings = []
known_names = []

# Traverse all folders (each folder is a person)
for person_name in os.listdir(dataset_path):
    person_folder = os.path.join(dataset_path, person_name)
    
    if not os.path.isdir(person_folder):
        continue

    print(f"📁 Encoding images for: {person_name}")
    
    for image_name in os.listdir(person_folder):
        image_path = os.path.join(person_folder, image_name)

        image = cv2.imread(image_path)
        if image is None:
            print(f"⚠️ Could not read {image_path}, skipping.")
            continue

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        boxes = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, boxes)

        if len(encodings) == 0:
            print(f"❌ No face found in {image_path}, skipping.")
            continue

        for encoding in encodings:
            known_encodings.append(encoding)
            known_names.append(person_name)
            print(f"✅ Face encoded from {image_name}")

# Save to pkl
data = {
    "encodings": known_encodings,
    "names": known_names
}

with open(encoding_file_path, "wb") as f:
    pickle.dump(data, f)

print("✅ Encoding complete!")
print(f"🧠 Total encodings: {len(known_encodings)} | Unique people: {len(set(known_names))}")
print(f"💾 Saved to: {encoding_file_path}")