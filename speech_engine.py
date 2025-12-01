from gtts import gTTS
import pygame
import os
import time
import subprocess
import tempfile
from ctypes import *
from contextlib import contextmanager

# ---------------- 1. ALSA Error Suppression (The Visual Fix) ----------------
# This block hides the C-level ALSA warnings from the terminal
ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

def py_error_handler(filename, line, function, err, fmt):
    pass

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

try:
    asound = cdll.LoadLibrary('libasound.so')
    asound.snd_lib_error_set_handler(c_error_handler)
except OSError:
    pass # ALSA not available or different OS, ignore

# ---------------- 2. Pygame Init with Larger Buffer (The Real Fix) ----------------
try:
    # buffer=4096 increases latency slightly but prevents 'underrun' errors 
    # when the CPU is busy with CV/AI tasks.
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
except Exception as e:
    print(f"⚠️ pygame.mixer init failed: {e}")

# ---------------- Logic ----------------

# Map our languages to gTTS codes and TLD for Indian accents
LANG_CODE_TLD = {
    'ENGLISH': ('en', 'com'),   # default English
    'HINDI': ('hi', 'co.in'),   # Indian Hindi accent
    'GUJARATI': ('gu', 'co.in') # Indian Gujarati accent
}

def speak_sentence(text, language='ENGLISH', temp_file=None):
    """
    Speak full sentences using gTTS (online) for natural voice.
    Falls back to mpg123 if pygame.mixer fails.
    """
    if not text.strip():
        return

    lang, tld = LANG_CODE_TLD.get(language.upper(), ('en', 'com'))

    # Use a temporary file if not provided
    if temp_file is None:
        temp_file = os.path.join(tempfile.gettempdir(), "temp_speech.mp3")

    try:
        # Generate speech
        tts = gTTS(text=text, lang=lang, tld=tld)
        tts.save(temp_file)
        
        # 0.1s sleep helps ensure file handle is released before read
        time.sleep(0.1) 

        # Try playing via pygame.mixer
        try:
            # Check if mixer is initialized before loading
            if pygame.mixer.get_init():
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                
                # Unload to release the file lock
                pygame.mixer.music.unload()
            else:
                raise Exception("Mixer not initialized")
                
        except Exception:
            # Fallback: use mpg123 via subprocess
            # -q suppresses mpg123's own terminal output
            subprocess.run(['mpg123', '-q', temp_file], check=True)

    except Exception as e:
        print(f"❌ gTTS failed: {e}")

# ---------------- Unified function ----------------
def speak_text(text, language='ENGLISH', mode='auto'):
    """
    Speak text with gTTS first. Mode 'auto' ignores letters vs sentences.
    """
    if not text.strip():
        return

    speak_sentence(text, language)
