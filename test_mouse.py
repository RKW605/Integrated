import cv2
import subprocess
import numpy as np
import shutil
import mediapipe as mp
import uinput
import os

# --- CONFIGURATION ---
# We now use HD resolution so it doesn't look "enlarged" or pixelated
WIDTH = 1280
HEIGHT = 720
FPS = 20  # 20 FPS is smooth for HD on Pi 4
SENSITIVITY_X = 20.0 
SENSITIVITY_Y = 20.0
DEADZONE = 1.0 # Increased slightly for HD resolution
WINDOW_NAME = "HD Eye Tracker"

# --- DETECT SCREEN SIZE ---
try:
    output = subprocess.check_output("xrandr | grep '*' | awk '{print $1}'", shell=True).decode()
    SCREEN_W, SCREEN_H = map(int, output.strip().split('x'))
except:
    SCREEN_W, SCREEN_H = 1920, 1080

# --- TRACKER STATE ---
global_xc = SCREEN_W / 2.0
global_yc = SCREEN_H / 2.0

# --- VIRTUAL MOUSE ---
device = uinput.Device([
    uinput.BTN_LEFT, uinput.BTN_RIGHT, uinput.REL_X, uinput.REL_Y
])
acc_x = 0.0
acc_y = 0.0

# --- CAMERA (HD MODE) ---
cmd_executable = "rpicam-vid" if shutil.which("rpicam-vid") else "libcamera-vid"
command = [
    cmd_executable, "--inline", "--nopreview",
    "--width", str(WIDTH), "--height", str(HEIGHT),
    "--framerate", str(FPS), "--timeout", "0",
    "--codec", "yuv420", "-o", "-"
]
process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**8)
frame_size = int(WIDTH * HEIGHT * 1.5)

# --- AI ---
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
RIGHT_IRIS_CENTER = 473
RIGHT_EYE_CORNERS = [263, 362]
SKY_BLUE = (235, 206, 135)

# --- WINDOW SETUP ---
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

print(f"Starting HD Tracker ({WIDTH}x{HEIGHT}). Press Q to Quit.")

try:
    while True:
        raw_bytes = process.stdout.read(frame_size)
        if len(raw_bytes) != frame_size: break

        # 1. Process HD Image
        yuv = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((int(HEIGHT * 1.5), WIDTH))
        frame = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)
        frame = cv2.flip(frame, 1)
        
        # 2. OPTIMIZATION: Shrink image for AI (Speed)
        # We send a tiny 640px version to the AI so it stays fast
        small_frame = cv2.resize(frame, (640, 360))
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        results = face_mesh.process(rgb_small)

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            
            # Helper to map AI points back to the HD Frame
            def get_point(idx):
                # Note: We multiply by HD WIDTH/HEIGHT
                return (landmarks[idx].x * WIDTH, landmarks[idx].y * HEIGHT)

            # Calculate Points (using HD coordinates)
            p1 = get_point(RIGHT_EYE_CORNERS[0])
            p2 = get_point(RIGHT_EYE_CORNERS[1])
            xr, yr = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
            xi, yi = get_point(RIGHT_IRIS_CENTER)

            # Draw Dots (On the big HD frame)
            cv2.circle(frame, (int(xr), int(yr)), 4, (0, 0, 255), -1)
            cv2.circle(frame, (int(xi), int(yi)), 4, (0, 255, 0), -1)

            # Movement Logic
            raw_dx = xr - xi
            raw_dy = yr - yi
            if abs(raw_dx) < DEADZONE: raw_dx = 0
            if abs(raw_dy) < DEADZONE: raw_dy = 0

            acc_x += raw_dx * SENSITIVITY_X
            acc_y += raw_dy * SENSITIVITY_Y
            move_x = int(acc_x)
            move_y = int(acc_y)

            if move_x != 0 or move_y != 0:
                device.emit(uinput.REL_X, move_x)
                device.emit(uinput.REL_Y, move_y)
                
                global_xc += move_x
                global_yc += move_y
                global_xc = max(0, min(global_xc, SCREEN_W))
                global_yc = max(0, min(global_yc, SCREEN_H))
                acc_x -= move_x
                acc_y -= move_y

            # Draw Blue Circle
            cam_cursor_x = int((global_xc / SCREEN_W) * WIDTH)
            cam_cursor_y = int((global_yc / SCREEN_H) * HEIGHT)
            cv2.circle(frame, (cam_cursor_x, cam_cursor_y), 20, SKY_BLUE, 3)
            cv2.line(frame, (cam_cursor_x-8, cam_cursor_y), (cam_cursor_x+8, cam_cursor_y), SKY_BLUE, 1)
            cv2.line(frame, (cam_cursor_x, cam_cursor_y-8), (cam_cursor_x, cam_cursor_y+8), SKY_BLUE, 1)

            # Debug Text
            cv2.putText(frame, f"Raw: {raw_dx:.2f}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

        # 3. Final Display Stretch
        # Resize HD frame to Monitor Size (Clean scaling)
        display_frame = cv2.resize(frame, (SCREEN_W, SCREEN_H))

        cv2.imshow(WINDOW_NAME, display_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

except KeyboardInterrupt:
    pass
finally:
    process.terminate()
    cv2.destroyAllWindows()
