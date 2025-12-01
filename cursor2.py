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

SENSITIVITY_X = 20.0 
SENSITIVITY_Y = 40.0  
DEADZONE = 1.0 
WINDOW_NAME = "Instant Click Tracker"

# --- CLICK SETTINGS ---
# Vertical distance (pixels). If L-Dist falls below this, it clicks.
BLINK_THRESHOLD = 6.5 

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

SKY_BLUE = (235, 206, 135)
CALIBRATION_COLOR = (255, 0, 0)
CLICK_MSG_COLOR = (0, 0, 255)

acc_x, acc_y = 0.0, 0.0
calibrated = False
xs, ys = 0.0, 0.0

click_cooldown = 0
show_click_msg = 0

cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

print("Look at Blue Dot & Press SPACE to Calibrate.")

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

            p1 = get_point(RIGHT_EYE_CORNERS[0])
            p2 = get_point(RIGHT_EYE_CORNERS[1])
            xr, yr = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
            xi, yi = get_point(RIGHT_IRIS_CENTER)

            # --- INSTANT CLICK LOGIC ---
            l_top = get_point(LEFT_EYE_LIDS[0])
            l_bot = get_point(LEFT_EYE_LIDS[1])
            left_dist = abs(l_top[1] - l_bot[1])

            r_top = get_point(RIGHT_EYE_LIDS[0])
            r_bot = get_point(RIGHT_EYE_LIDS[1])
            right_dist = abs(r_top[1] - r_bot[1])

            # Cooldown logic (decrements every frame)
            if click_cooldown > 0:
                click_cooldown -= 1

            # Condition: Left Closed AND Right Open AND Cooldown Ready
            if left_dist < BLINK_THRESHOLD and right_dist > BLINK_THRESHOLD and click_cooldown == 0:
                # CLICK INSTANTLY
                device.emit(uinput.BTN_LEFT, 1)
                device.emit(uinput.BTN_LEFT, 0)
                
                print("INSTANT CLICK!")
                show_click_msg = 10
                click_cooldown = 10  # Wait ~0.3s before allowing next click (prevents machine gun)

            # Draw Dots
            cv2.circle(frame, (int(xr), int(yr)), 4, (0, 0, 255), -1) 
            cv2.circle(frame, (int(xi), int(yi)), 4, (0, 255, 0), -1) 

            # --- TRACKING ---
            if not calibrated:
                center_x, center_y = WIDTH // 2, HEIGHT // 2
                cv2.circle(frame, (center_x, center_y), 15, CALIBRATION_COLOR, -1)
                cv2.putText(frame, "LOOK HERE & PRESS SPACE", (center_x - 150, center_y - 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, CALIBRATION_COLOR, 2)
                
                if key == ord(' '):
                    xs = xi
                    ys = yi
                    calibrated = True

            else:
                cv2.circle(frame, (int(xs), int(ys)), 6, CALIBRATION_COLOR, -1)
                
                raw_dx = xi - xr
                raw_dy = yi - ys
                if abs(raw_dx) < DEADZONE: raw_dx = 0
                if abs(raw_dy) < DEADZONE: raw_dy = 0

                acc_x += raw_dx * SENSITIVITY_X
                acc_y += raw_dy * SENSITIVITY_Y
                move_x = int(acc_x)
                move_y = int(acc_y)

                if move_x != 0 or move_y != 0:
                    device.emit(uinput.REL_X, move_x)
                    device.emit(uinput.REL_Y, move_y)
                    acc_x -= move_x
                    acc_y -= move_y

                real_x, real_y = pyautogui.position()
                cam_cursor_x = int((real_x / SCREEN_W) * WIDTH)
                cam_cursor_y = int((real_y / SCREEN_H) * HEIGHT)
                cv2.circle(frame, (cam_cursor_x, cam_cursor_y), 20, SKY_BLUE, 3)
                cv2.line(frame, (cam_cursor_x-8, cam_cursor_y), (cam_cursor_x+8, cam_cursor_y), SKY_BLUE, 1)
                cv2.line(frame, (cam_cursor_x, cam_cursor_y-8), (cam_cursor_x, cam_cursor_y+8), SKY_BLUE, 1)

            if show_click_msg > 0:
                cv2.putText(frame, "CLICK!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2.0, CLICK_MSG_COLOR, 5)
                show_click_msg -= 1

            cv2.putText(frame, f"L-Dist: {left_dist:.1f}", (10, HEIGHT - 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        display_frame = cv2.resize(frame, (SCREEN_W, SCREEN_H))
        cv2.imshow(WINDOW_NAME, display_frame)
        
        if key == ord('q'): break

except KeyboardInterrupt:
    pass
finally:
    camera.stop()
    cv2.destroyAllWindows()
