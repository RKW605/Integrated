# Save this script as 'gaze_detector.py'
import cv2
from picamera2 import Picamera2
from gazetracking import GazeTracking
import numpy as np # Used by Picamera2 and OpenCV

# 1. Initialize Picamera2 and GazeTracking
picam2 = Picamera2()
# Configure for the desired resolution and color format
config = picam2.create_video_configuration(main={"size": (640, 480), "format": 'XRGB8888'})
picam2.configure(config)
picam2.start()

gaze = GazeTracking()

print("Gaze Detection Active. Press 'q' to quit.")
while True:
    # 2. Capture frame as a numpy array from Picamera2
    # The format 'XRGB8888' is needed for efficiency with Picamera2
    frame = picam2.capture_array()

    # Convert the frame to BGR format for OpenCV and GazeTracking
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    # 3. Process the frame
    gaze.refresh(frame)

    # ... (Rest of your processing/display code) ...
    # Add gaze detection text and show the frame
    text = gaze.localized_direction() # Example of getting gaze direction
    
    cv2.putText(frame, text, (90, 60), cv2.FONT_HERSHEY_DUPLEX, 1.6, (147, 58, 31), 2)
    cv2.imshow("Gaze Detector", frame)

    if cv2.waitKey(1) == ord('q'):
        break

cv2.destroyAllWindows()
picam2.stop()
# Deactivate the environment when you are completely finished
# (Done outside the script, in the terminal)
