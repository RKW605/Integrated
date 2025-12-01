#!/bin/bash

echo "--- STARTING ALS SYSTEM ---"

# 1. Load the Mouse Driver (Just in case)
echo "Loading Kernel Driver..."
sudo modprobe uinput

# 2. Start Eye Tracker in Background (&)
# We use 'nohup' so it keeps running even if terminal closes
echo "Starting Eye Tracker..."
sudo QT_QPA_PLATFORM=xcb /home/het/Downloads/gemini/myenv/bin/python3 cursor4.py &

# Save the Process ID (PID) so we can kill it later
TRACKER_PID=$!

# Wait a few seconds for the camera to warm up
sleep 5

# 3. Start the Virtual Keyboard
# (Replace 'keyboard.py' with your ACTUAL keyboard filename)
echo "Starting Virtual Keyboard..."
sudo /home/het/Downloads/gemini/myenv/bin/python3 main.py

# 4. Cleanup: When keyboard closes, kill the eye tracker
echo "Keyboard closed. Stopping Eye Tracker..."
sudo kill $TRACKER_PID
