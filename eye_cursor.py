import cv2
import subprocess
import numpy as np
import shutil
import mediapipe as mp

# --- CONFIGURATION ---
WIDTH = 640
HEIGHT = 480
FPS = 16  # Keep low to prevent lag/tearing on Pi 4

# --- CAMERA SETUP ---
cmd_executable = "rpicam-vid" if shutil.which("rpicam-vid") else "libcamera-vid"
command = [
    cmd_executable, "--inline", "--nopreview",
    "--width", str(WIDTH), "--height", str(HEIGHT),
    "--framerate", str(FPS), "--timeout", "0",
    "--codec", "yuv420", "-o", "-"
]

print(f"Starting Eye Center Tracker with {cmd_executable}...")
process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**8)
frame_size = int(WIDTH * HEIGHT * 1.5)

# --- MEDIAPIPE SETUP ---
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# --- LANDMARK INDICES ---
# 1. Iris (The Moving Part)
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

# 2. Eye Corners (The Fixed Part) to calculate "Eye Center"
# Left Eye: 33 (Outer), 133 (Inner)
LEFT_EYE_CORNERS = [33, 133]
# Right Eye: 263 (Outer), 362 (Inner)
RIGHT_EYE_CORNERS = [263, 362]

# --- WINDOW SETUP ---
window_name = "Geometric Eye Tracker"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

try:
    while True:
        # Read Frame
        raw_bytes = process.stdout.read(frame_size)
        if len(raw_bytes) != frame_size:
            print("Frame dropped")
            break

        yuv = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((int(HEIGHT * 1.5), WIDTH))
        frame = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        results = face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            # Convert normalized landmarks to pixel coordinates
            mesh_points = np.array([
                np.multiply([p.x, p.y], [WIDTH, HEIGHT]).astype(int) 
                for p in results.multi_face_landmarks[0].landmark
            ])

            # ---------------------------------------------------------
            # LEFT EYE PROCESSING
            # ---------------------------------------------------------
            
            # A. Calculate Fixed Eye Center (Red Dot)
            # Center = (Corner1 + Corner2) / 2
            l_corner1 = mesh_points[LEFT_EYE_CORNERS[0]]
            l_corner2 = mesh_points[LEFT_EYE_CORNERS[1]]
            l_eye_center = np.mean([l_corner1, l_corner2], axis=0).astype(int)
            
            # Draw Red Dot for Eye Center
            cv2.circle(frame, tuple(l_eye_center), 3, (0, 0, 255), -1)

            # B. Calculate Iris Center (Green Dot)
            (l_iris_x, l_iris_y), l_radius = cv2.minEnclosingCircle(mesh_points[LEFT_IRIS])
            l_iris_center = (int(l_iris_x), int(l_iris_y))
            
            # Draw Green Dot for Iris
            cv2.circle(frame, l_iris_center, 2, (0, 255, 0), -1)
            cv2.circle(frame, l_iris_center, int(l_radius), (0, 255, 0), 1)

            # ---------------------------------------------------------
            # RIGHT EYE PROCESSING
            # ---------------------------------------------------------
            
            # A. Calculate Fixed Eye Center (Red Dot)
            r_corner1 = mesh_points[RIGHT_EYE_CORNERS[0]]
            r_corner2 = mesh_points[RIGHT_EYE_CORNERS[1]]
            r_eye_center = np.mean([r_corner1, r_corner2], axis=0).astype(int)
            
            # Draw Red Dot for Eye Center
            cv2.circle(frame, tuple(r_eye_center), 3, (0, 0, 255), -1)

            # B. Calculate Iris Center (Green Dot)
            (r_iris_x, r_iris_y), r_radius = cv2.minEnclosingCircle(mesh_points[RIGHT_IRIS])
            r_iris_center = (int(r_iris_x), int(r_iris_y))
            
            # Draw Green Dot for Iris
            cv2.circle(frame, r_iris_center, 2, (0, 255, 0), -1)
            cv2.circle(frame, r_iris_center, int(r_radius), (0, 255, 0), 1)

            # ---------------------------------------------------------
            # DISPLAY TEXT
            # ---------------------------------------------------------
            # Calculate distance vector (Iris - Center)
            # This tells you where they are looking relative to the center
            l_dx = l_iris_center[0] - l_eye_center[0]
            l_dy = l_iris_center[1] - l_eye_center[1]

            cv2.putText(frame, f"L Center(Red): {l_eye_center}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.putText(frame, f"L Iris(Grn): {l_iris_center}", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"L Vector: ({l_dx}, {l_dy})", (30, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.imshow(window_name, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    pass
finally:
    process.terminate()
    cv2.destroyAllWindows()
