import cv2
import subprocess
import numpy as np
import shutil
import mediapipe as mp
import uinput
import os
import threading
import time
import pyautogui

# --- CONFIGURATION ---
WIDTH = 1280
HEIGHT = 720
FPS = 30
WINDOW_NAME = "Absolute Eye Mapping"

# --- MAPPING SETTINGS ---
# Your formula uses these offsets to define the "Active Box" around the eye.
# If cursor is too fast/jittery, INCREASE these numbers (e.g., 4->10, 2->6)
ROI_X_OFFSET = 4  
ROI_Y_OFFSET = 2

# SMOOTHING FACTOR (0.0 to 1.0)
# 0.1 = Very Smooth (Slow)
# 0.9 = Very Fast (Jittery)
SMOOTHING = 0.2

# CLICK SETTINGS
BLINK_THRESHOLD = 6.5 
CLICK_COOLDOWN_FRAMES = 10

# --- DETECT SCREEN SIZE ---
try:
    output = subprocess.check_output("xrandr | grep '*' | awk '{print $1}'", shell=True).decode()
    SCREEN_W, SCREEN_H = map(int, output.strip().split('x'))
except:
    SCREEN_W, SCREEN_H = 1920, 1080

# --- CLASS: CAMERA WORKER ---
class CameraStream:
    def __init__(self, width, height, fps):
        self.width = width
        self.height = height
        self.frame_size = int(width * height * 1.5)
        self.frame = None
        self.running = False
        
        cmd_executable = "rpicam-vid" if shutil.which("rpicam-vid") else "libcamera-vid"
        command = [
            cmd_executable, "--inline", "--nopreview",
            "--width", str(width), "--height", str(height),
            "--framerate", str(fps), "--timeout", "0",
            "--codec", "yuv420", "-o", "-"
        ]
        
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**8)
        self.running = True
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()
        
        print("Waiting for camera stream...")
        while self.frame is None:
            time.sleep(0.1)

    def update(self):
        while self.running:
            raw_bytes = self.process.stdout.read(self.frame_size)
            if len(raw_bytes) != self.frame_size:
                self.running = False
                break
            yuv = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((int(self.height * 1.5), self.width))
            bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)
            self.frame = cv2.flip(bgr, 1)

    def read(self):
        return self.frame

    def stop(self):
        self.running = False
        self.process.terminate()

# --- MAIN SETUP ---
camera = CameraStream(WIDTH, HEIGHT, FPS)
device = uinput.Device([uinput.BTN_LEFT, uinput.BTN_RIGHT, uinput.REL_X, uinput.REL_Y])

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1, refine_landmarks=True, 
    min_detection_confidence=0.5, min_tracking_confidence=0.5
)

RIGHT_IRIS_CENTER = 473
RIGHT_EYE_CORNERS = [263, 362]
LEFT_EYE_LIDS = [159, 145]
RIGHT_EYE_LIDS = [386, 374]

# Colors
SKY_BLUE = (235, 206, 135)
CALIBRATION_COLOR = (255, 0, 0)
ROI_COLOR = (0, 255, 255) # Yellow Box

# State
calibrated = False
xs, ys = 0.0, 0.0
click_cooldown = 0
show_click_msg = 0

# Variables for Smoothing
cur_screen_x = SCREEN_W / 2
cur_screen_y = SCREEN_H / 2

cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

print("Absolute Mapping Mode. Look at Blue Dot & Press SPACE.")

try:
    while True:
        frame = camera.read()
        if frame is None: break

        small_frame = cv2.resize(frame, (640, 360))
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_small)
        key = cv2.waitKey(1) & 0xFF

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            def get_point(idx):
                return (landmarks[idx].x * WIDTH, landmarks[idx].y * HEIGHT)

            # Get Raw Coords
            xi, yi = get_point(RIGHT_IRIS_CENTER)

            # --- CLICK LOGIC ---
            l_top = get_point(LEFT_EYE_LIDS[0])
            l_bot = get_point(LEFT_EYE_LIDS[1])
            left_dist = abs(l_top[1] - l_bot[1])

            r_top = get_point(RIGHT_EYE_LIDS[0])
            r_bot = get_point(RIGHT_EYE_LIDS[1])
            right_dist = abs(r_top[1] - r_bot[1])

            if click_cooldown > 0: click_cooldown -= 1
            
            if left_dist < BLINK_THRESHOLD and right_dist > BLINK_THRESHOLD and click_cooldown == 0:
                device.emit(uinput.BTN_LEFT, 1)
                device.emit(uinput.BTN_LEFT, 0)
                show_click_msg = 10
                click_cooldown = 15

            # --- CALIBRATION ---
            if not calibrated:
                # Show instructions
                center_x, center_y = WIDTH // 2, HEIGHT // 2
                cv2.circle(frame, (center_x, center_y), 15, CALIBRATION_COLOR, -1)
                cv2.circle(frame, (int(xi), int(yi)), 4, (0, 255, 0), -1) 
                
                if key == ord(' '):
                    xs = xi
                    ys = yi
                    calibrated = True
                    # Initialize current position to center so it doesn't jump
                    cur_screen_x = SCREEN_W / 2
                    cur_screen_y = SCREEN_H / 2
            
            # --- ABSOLUTE MAPPING LOGIC ---
            else:
                # 1. Define ROI based on Calibration (xs, ys)
                r1x = xs - ROI_X_OFFSET
                r2x = xs + ROI_X_OFFSET
                r1y = ys - ROI_Y_OFFSET
                r2y = ys + ROI_Y_OFFSET

                # Draw the ROI Box (Yellow) so you can see the active area
                cv2.rectangle(frame, (int(r1x), int(r1y)), (int(r2x), int(r2y)), ROI_COLOR, 1)
                cv2.circle(frame, (int(xi), int(yi)), 2, (0, 255, 0), -1) 

                # 2. YOUR EXACT LOGIC IMPLEMENTATION
                # Note: We added guards to prevent Division by Zero just in case
                denom_x = (r2x - r1x)
                denom_y = (r2y - r1y)
                
                if denom_x == 0: denom_x = 1
                if denom_y == 0: denom_y = 1

                # Calculate Target Screen X/Y
                target_cursor_x = SCREEN_W - ((r2x - xi) * (SCREEN_W / denom_x))
                target_cursor_y = SCREEN_H - ((r2y - yi) * (SCREEN_H / denom_y))

                # 3. SMOOTHING (Essential because ROI is small)
                # We blend the New Target with the Old Position
                cur_screen_x = (SMOOTHING * target_cursor_x) + ((1 - SMOOTHING) * cur_screen_x)
                cur_screen_y = (SMOOTHING * target_cursor_y) + ((1 - SMOOTHING) * cur_screen_y)

                # 4. CLAMP TO SCREEN (Prevent going out of bounds)
                final_x = max(0, min(cur_screen_x, SCREEN_W))
                final_y = max(0, min(cur_screen_y, SCREEN_H))

                # 5. MOVE MOUSE (Using Relative Delta to simulate Absolute)
                # We ask the OS "Where are we now?"
                real_x, real_y = pyautogui.position()
                
                # Calculate how much we need to move to get to Final X/Y
                diff_x = int(final_x - real_x)
                diff_y = int(final_y - real_y)

                # Move using uinput
                if diff_x != 0 or diff_y != 0:
                    device.emit(uinput.REL_X, diff_x)
                    device.emit(uinput.REL_Y, diff_y)

                # Draw Blue Cursor Circle
                cam_cursor_x = int((final_x / SCREEN_W) * WIDTH)
                cam_cursor_y = int((final_y / SCREEN_H) * HEIGHT)
                cv2.circle(frame, (cam_cursor_x, cam_cursor_y), 20, SKY_BLUE, 3)

            # Debug Info
            if show_click_msg > 0:
                cv2.putText(frame, "CLICK!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2.0, CLICK_MSG_COLOR, 5)
                show_click_msg -= 1

        display_frame = cv2.resize(frame, (SCREEN_W, SCREEN_H))
        cv2.imshow(WINDOW_NAME, display_frame)
        if key == ord('q'): break

except KeyboardInterrupt:
    pass
finally:
    camera.stop()
    cv2.destroyAllWindows()
