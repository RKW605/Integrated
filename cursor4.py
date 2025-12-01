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
WINDOW_NAME = "3x3 Grid Eye Tracker"

# --- USER CALIBRATED SENSITIVITY ---
ROI_X_OFFSET = 10  
ROI_Y_OFFSET = 5

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

# Landmarks
RIGHT_IRIS_CENTER = 473
LEFT_EYE_LIDS = [159, 145]
RIGHT_EYE_LIDS = [386, 374]

# Colors
SKY_BLUE = (235, 206, 135)
CALIBRATION_COLOR = (255, 0, 0)
ROI_COLOR = (0, 255, 255) # Yellow
CLICK_MSG_COLOR = (0, 0, 255)
GRID_COLOR = (255, 255, 255)
HIGHLIGHT_COLOR = (0, 0, 255) # Reddish highlight

# State
calibrated = False
xs, ys = 0.0, 0.0
click_cooldown = 0
show_click_msg = 0

cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
#cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

print("Look at Blue Dot & Press SPACE to see the Highlighted Grid.")

try:
    while True:
        frame = camera.read()
        if frame is None: break

        small_frame = cv2.resize(frame, (640, 360))
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_small)
        
        key = cv2.waitKey(1) & 0xFF
        
        # Sensitivity Controls
        if key == ord('='): 
            ROI_X_OFFSET += 1
            ROI_Y_OFFSET += 0.5
        elif key == ord('-'):
            ROI_X_OFFSET -= 1
            ROI_Y_OFFSET -= 0.5
        ROI_X_OFFSET = max(1, ROI_X_OFFSET)
        ROI_Y_OFFSET = max(1, ROI_Y_OFFSET)

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            def get_point(idx):
                return (landmarks[idx].x * WIDTH, landmarks[idx].y * HEIGHT)

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
                center_x, center_y = WIDTH // 2, HEIGHT // 2
                cv2.circle(frame, (center_x, center_y), 15, CALIBRATION_COLOR, -1)
                cv2.circle(frame, (int(xi), int(yi)), 4, (0, 255, 0), -1) 
                
                if key == ord(' '):
                    xs = xi
                    ys = yi
                    calibrated = True
            
            # --- ABSOLUTE MAPPING ---
            else:
                # 1. Move Cursor First
                r1x = xs - ROI_X_OFFSET
                r2x = xs + ROI_X_OFFSET
                r1y = ys - ROI_Y_OFFSET
                r2y = ys + ROI_Y_OFFSET

                denom_x = (r2x - r1x)
                denom_y = (r2y - r1y)
                if denom_x == 0: denom_x = 0.001
                if denom_y == 0: denom_y = 0.001

                target_cursor_x = SCREEN_W - ((r2x - xi) * (SCREEN_W / denom_x))
                target_cursor_y = SCREEN_H - ((r2y - yi) * (SCREEN_H / denom_y))

                final_x = max(0, min(target_cursor_x, SCREEN_W))
                final_y = max(0, min(target_cursor_y, SCREEN_H))

                real_x, real_y = pyautogui.position()
                diff_x = int(final_x - real_x)
                diff_y = int(final_y - real_y)

                if diff_x != 0 or diff_y != 0:
                    device.emit(uinput.REL_X, diff_x)
                    device.emit(uinput.REL_Y, diff_y)

                # 2. HIGHLIGHT ACTIVE CELL
                # Create a transparent overlay
                overlay = frame.copy()
                
                # Determine which cell the cursor is in (0, 1, or 2)
                col_idx = int(final_x / (SCREEN_W / 3))
                row_idx = int(final_y / (SCREEN_H / 3))
                
                # Clamp index to 0-2 (handle edge case where cursor is at max screen pixel)
                col_idx = min(2, max(0, col_idx))
                row_idx = min(2, max(0, row_idx))

                # Calculate coordinates on Camera Frame
                cam_cell_w = WIDTH // 3
                cam_cell_h = HEIGHT // 3
                
                x1 = col_idx * cam_cell_w
                y1 = row_idx * cam_cell_h
                x2 = x1 + cam_cell_w
                y2 = y1 + cam_cell_h

                # Draw filled Red Rectangle on overlay
                cv2.rectangle(overlay, (x1, y1), (x2, y2), HIGHLIGHT_COLOR, -1)

                # Blend overlay with original frame (0.3 = 30% opacity)
                cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

                # 3. DRAW GRID LINES ON TOP
                col_1, col_2 = WIDTH // 3, (WIDTH // 3) * 2
                row_1, row_2 = HEIGHT // 3, (HEIGHT // 3) * 2
                cv2.line(frame, (col_1, 0), (col_1, HEIGHT), GRID_COLOR, 2)
                cv2.line(frame, (col_2, 0), (col_2, HEIGHT), GRID_COLOR, 2)
                cv2.line(frame, (0, row_1), (WIDTH, row_1), GRID_COLOR, 2)
                cv2.line(frame, (0, row_2), (WIDTH, row_2), GRID_COLOR, 2)

                # Draw ROI Box & Cursor Circle
                cv2.rectangle(frame, (int(r1x), int(r1y)), (int(r2x), int(r2y)), ROI_COLOR, 1)
                cv2.circle(frame, (int(xi), int(yi)), 2, (0, 255, 0), -1) 
                
                cam_cursor_x = int((final_x / SCREEN_W) * WIDTH)
                cam_cursor_y = int((final_y / SCREEN_H) * HEIGHT)
                cv2.circle(frame, (cam_cursor_x, cam_cursor_y), 20, SKY_BLUE, 3)
                
                text_info = f"Box: {ROI_X_OFFSET:.1f}x{ROI_Y_OFFSET:.1f}"
                cv2.putText(frame, text_info, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, ROI_COLOR, 2)

            if show_click_msg > 0:
                cv2.putText(frame, "CLICK!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2.0, CLICK_MSG_COLOR, 5)
                show_click_msg -= 1

# --- END OF LOOP DISPLAY (MINI-VIEW MODE) ---
        # 1. Resize to a small "Corner" view (e.g., 320x180)
        # We use the aspect ratio of the camera
        mini_w, mini_h = 320, 180
        display_frame = cv2.resize(frame, (mini_w, mini_h))
        
        # 2. Show the window
        cv2.imshow(WINDOW_NAME, display_frame)
        
        # 3. Move window to Top-Right Corner (so it doesn't block the keyboard)
        # (Screen Width - Window Width, 0)
        cv2.moveWindow(WINDOW_NAME, SCREEN_W - mini_w, 0)
        
        if key == ord('q'): break

except KeyboardInterrupt:
    pass
finally:
    camera.stop()
    cv2.destroyAllWindows()
