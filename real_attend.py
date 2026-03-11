import cv2
import face_recognition
import pandas as pd
import os
import pickle
from datetime import datetime
from ultralytics import YOLO

# ========== PATHS ==========
ENCODING_FILE = "FaceDataSheet/encodings.pkl"
EMPLOYEE_INFO_CSV = "employee_info.csv"
ATTENDANCE_FOLDER = "AttendanceRecords"

# ========== LOAD KNOWN FACES ==========
with open(ENCODING_FILE, "rb") as f:
    data = pickle.load(f)
known_encodings = data["encodings"]
known_names = data["names"]

# ========== LOAD EMPLOYEE INFO ==========
employee_info = pd.read_csv(EMPLOYEE_INFO_CSV)
name_to_info = employee_info.set_index("Name")[["EmployeeID", "Email"]].to_dict("index")

# ========== ATTENDANCE LOGIC ==========
if not os.path.exists(ATTENDANCE_FOLDER):
    os.makedirs(ATTENDANCE_FOLDER)

if not os.path.exists("attendance.csv"):
    with open("attendance.csv", "w") as f:
        f.write("EmployeeID,Name,Email,DateTime\n")

today_date = datetime.now().strftime("%Y-%m-%d")
attendance_file = os.path.join(ATTENDANCE_FOLDER, f"{today_date}.xlsx")

attendance_df = pd.DataFrame(columns=["EmployeeID", "Name", "Email", "Time"])
marked_names = set()

# ========== LOAD YOLOv8 FACE MODEL ==========
model = YOLO("yolov8n-face.pt")  # You must have this model file in your project folder

# ========== START CCTV/WEBCAM ==========
camera_url = ""
  # Change this to your CCTV RTSP/HTTP URl
cap = cv2.VideoCapture(camera_url) # Replace 0 with your CCTV stream URL if needed
cv2.namedWindow("Face Attendance", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("Face Attendance", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

print("🎥 Starting camera...")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to grab frame")
        break

    results = model(frame, verbose=False)[0]

    for det in results.boxes:
        x1, y1, x2, y2 = map(int, det.xyxy[0])

        face_img = frame[y1:y2, x1:x2]
        rgb_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb_face)

        if encodings:
            match = face_recognition.compare_faces(known_encodings, encodings[0], tolerance=0.5)
            face_distances = face_recognition.face_distance(known_encodings, encodings[0])

            if True in match:
                best_match_index = face_distances.argmin()
                name = known_names[best_match_index]

                if name not in marked_names:
                    info = name_to_info.get(name, {"EmployeeID": "Unknown", "Email": "Unknown"})
                    now = datetime.now().strftime("%H:%M:%S")
                    now_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    attendance_df.loc[len(attendance_df)] = [info["EmployeeID"], name, info["Email"], now]
                    marked_names.add(name)
                    
                    # Append to attendance.csv
                    with open("attendance.csv", "a") as f:
                        f.write(f"{info['EmployeeID']},{name},{info['Email']},{now_datetime}\n")

                    print(f"✅ {name} marked present at {now}")

                label = name
            else:
                label = "Unknown"
        else:
            label = "No Face"

        # Draw Bounding Box & Label
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.rectangle(frame, (x1, y2 + 5), (x2, y2 + 35), (0, 255, 0), cv2.FILLED)
        cv2.putText(frame, label, (x1 + 6, y2 + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

    cv2.imshow("Face Attendance", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # Press Esc to quit
        break

# ========== SAVE ATTENDANCE ==========
attendance_df.to_excel(attendance_file, index=False)
print(f"📁 Attendance saved to {attendance_file}")

cap.release()
cv2.destroyAllWindows()