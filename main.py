import pygame
from english_keyboard import main as english_main
from gujarati_keyboard import main as gujarati_main
from hindi_keyboard import main as hindi_main

current_keyboard = "GUJARATI"  # default

while True:
    if current_keyboard == "ENGLISH":
        result = english_main()
    elif current_keyboard == "GUJARATI":
        result = gujarati_main()
    elif current_keyboard == "HINDI":
        result = hindi_main()

    # Clear old events and wait a bit
    # wait until mouse is fully released
    while any(pygame.mouse.get_pressed()):
        pygame.event.pump()

    if result == "SWITCH_ENGLISH":
        current_keyboard = "ENGLISH"
    elif result == "SWITCH_GUJARATI":
        current_keyboard = "GUJARATI"
    elif result == "SWITCH_HINDI":
        current_keyboard = "HINDI"
    else:
        break

