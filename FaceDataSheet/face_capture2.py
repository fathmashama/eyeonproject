import cv2
import os

# === SETTINGS ===
TOTAL_IMAGES = 40
BEEP_ENABLED = True
BEEP_FREQ = 1000  # Hz
BEEP_DURATION = 150  # ms

# === STEP 1: Get user's name and setup ===
person_name = input("Enter person's name: ").strip()
save_path = os.path.join("dataset", person_name)
os.makedirs(save_path, exist_ok=True)

# === STEP 2: Load face detectors ===
frontal_face = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
profile_face = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')

# === STEP 3: Start camera ===
cam = cv2.VideoCapture(0)
count = 0

print("\n📢 Instructions:")
print("➡️  Face the camera, change angle, expression, blink, close eyes, etc.")
print("➡️  Press SPACE to capture image. Press 'q' to quit early.\n")

while True:
    ret, frame = cam.read()
    if not ret:
        print("❌ Could not read from webcam.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect both frontal and side faces
    faces = frontal_face.detectMultiScale(gray, 1.3, 5)
    if len(faces) == 0:
        faces = profile_face.detectMultiScale(gray, 1.3, 5)

    # Draw rectangle around detected faces
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (100, 255, 100), 2)

    # Show counter and instructions
    cv2.putText(frame, f"Captured: {count}/{TOTAL_IMAGES}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    cv2.putText(frame, "Press SPACE to capture. 'q' to quit.",
                (10, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 255), 1)

    cv2.imshow("📷 Capture Face Dataset", frame)
    key = cv2.waitKey(1)

    # Quit
    if key == ord('q'):
        print("⏹️ Stopped manually.")
        break

    # Capture on SPACE bar
    if key == 32:  # SPACE
        if len(faces) == 0:
            print("⚠️ No face detected. Try again.")
            continue

        # Save only the first detected face
        (x, y, w, h) = faces[0]
        face_img = frame[y:y+h, x:x+w]
        cv2.imwrite(os.path.join(save_path, f"{count + 1}.jpg"), face_img)
        print(f"✅ Captured image {count + 1}")

        if BEEP_ENABLED:
            import winsound
            winsound.Beep(BEEP_FREQ, BEEP_DURATION)

        count += 1

        # Show the captured image briefly
        cv2.imshow("Last Captured", face_img)
        cv2.waitKey(500)

        if count >= TOTAL_IMAGES:
            print("🎉 Dataset complete!")
            break

cam.release()
cv2.destroyAllWindows()
print(f"\n✅ All {count} images saved to: {save_path}")