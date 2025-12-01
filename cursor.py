import cv2
import subprocess
import numpy as np
import shutil
import mediapipe as mp
import uinput  # <--- The Magic Kernel Library

# --- CONFIGURATION ---
WIDTH = 640
HEIGHT = 480
FPS = 16
SENSITIVITY = 2.0  # Lower is safer for uinput (start low!)
DEADZONE = 1.0

# --- VIRTUAL DEVICE SETUP ---
# We create a virtual mouse that supports Relative X and Y movement
events = (uinput.REL_X, uinput.REL_Y)
device = uinput.Device(events, name="EyeTrackerMouse")

print("Virtual USB Mouse Created! Control active.")

# --- CAMERA SETUP ---
cmd_executable = "rpicam-vid" if shutil.which("rpicam-vid") else "libcamera-vid"
command = [
    cmd_executable, "--inline", "--nopreview",
    "--width", str(WIDTH), "--height", str(HEIGHT),
    "--framerate", str(FPS), "--timeout", "0",
    "--codec", "yuv420", "-o", "-"
]

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

# Indices
RIGHT_IRIS_CENTER = 473
RIGHT_EYE_CORNERS = [263, 362]

try:
    while True:
        raw_bytes = process.stdout.read(frame_size)
        if len(raw_bytes) != frame_size:
            break

        yuv = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((int(HEIGHT * 1.5), WIDTH))
        frame = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)
        
        # Mirror frame
        frame = cv2.flip(frame, 1)
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            
            def get_point(idx):
                return (int(landmarks[idx].x * WIDTH), int(landmarks[idx].y * HEIGHT))

            # 1. Calc Positions
            p1 = get_point(RIGHT_EYE_CORNERS[0])
            p2 = get_point(RIGHT_EYE_CORNERS[1])
            xr, yr = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
            xi, yi = get_point(RIGHT_IRIS_CENTER)
            
            # Draw (Debug)
            cv2.circle(frame, (int(xr), int(yr)), 3, (0, 0, 255), -1)
            cv2.circle(frame, (int(xi), int(yi)), 3, (0, 255, 0), -1)

            # 2. Calc Delta (How far is iris from center?)
            raw_dx = xr - xi
            raw_dy = yr - yi

            # 3. Apply Deadzone
            if abs(raw_dx) < DEADZONE: raw_dx = 0
            if abs(raw_dy) < DEADZONE: raw_dy = 0

            # 4. KERNEL MOVEMENT
            # uinput expects Integers. 
            # If raw_dx is 5.0 and Sensitivity is 2.0, we move 10 pixels.
            move_x = int(raw_dx * SENSITIVITY)
            move_y = int(raw_dy * SENSITIVITY)

            # Only emit if there is movement
            if move_x != 0 or move_y != 0:
                device.emit(uinput.REL_X, move_x)
                device.emit(uinput.REL_Y, move_y) 
                # Note: Check if Up/Down is reversed. If so, use: device.emit(uinput.REL_Y, -move_y)

            # Debug Text
            color = (0, 255, 0) if (move_x != 0 or move_y != 0) else (0, 0, 255)
            cv2.putText(frame, f"Move: {move_x}, {move_y}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.imshow("Kernel Mouse Control", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    pass
finally:
    process.terminate()
    cv2.destroyAllWindows()
