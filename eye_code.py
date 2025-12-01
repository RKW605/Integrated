import cv2
import subprocess
import numpy as np
import shutil
import mediapipe as mp

# --- CONFIGURATION ---
WIDTH = 640
HEIGHT = 480
# FIX LAG: Lowered FPS to 16 to match MediaPipe speed on Pi 4
FPS = 16 

# --- CAMERA SETUP ---
cmd_executable = "rpicam-vid" if shutil.which("rpicam-vid") else "libcamera-vid"
command = [
    cmd_executable, "--inline", "--nopreview",
    "--width", str(WIDTH), "--height", str(HEIGHT),
    "--framerate", str(FPS), "--timeout", "0",
    "--codec", "yuv420", "-o", "-"
]

print(f"Starting Fullscreen Tracker with {cmd_executable}...")
process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**8)
frame_size = int(WIDTH * HEIGHT * 1.5)

# --- MEDIAPIPE SETUP ---
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,  # Enables Iris Tracking
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Iris Indices
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

# --- WINDOW SETUP (FULLSCREEN) ---
window_name = "Eye Tracker"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
# This command forces the window to go Full Screen
cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

try:
    while True:
        # 1. Read Frame
        raw_bytes = process.stdout.read(frame_size)
        if len(raw_bytes) != frame_size:
            print("Frame dropped")
            break

        yuv = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((int(HEIGHT * 1.5), WIDTH))
        frame = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)
        
        # 2. Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 3. Process AI
        results = face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            mesh_points = np.array([
                np.multiply([p.x, p.y], [WIDTH, HEIGHT]).astype(int) 
                for p in results.multi_face_landmarks[0].landmark
            ])

            # Draw Left Iris
            (l_cx, l_cy), l_radius = cv2.minEnclosingCircle(mesh_points[LEFT_IRIS])
            center_left = (int(l_cx), int(l_cy))
            cv2.circle(frame, center_left, 2, (0, 255, 0), -1)
            cv2.circle(frame, center_left, int(l_radius), (0, 255, 0), 1)

            # Draw Right Iris
            (r_cx, r_cy), r_radius = cv2.minEnclosingCircle(mesh_points[RIGHT_IRIS])
            center_right = (int(r_cx), int(r_cy))
            cv2.circle(frame, center_right, 2, (0, 255, 0), -1)
            cv2.circle(frame, center_right, int(r_radius), (0, 255, 0), 1)

            # Display Coordinates
            cv2.putText(frame, f"L: {center_left}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, f"R: {center_right}", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # 4. Show Fullscreen
        cv2.imshow(window_name, frame)
        
        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    pass
finally:
    process.terminate()
    cv2.destroyAllWindows()
