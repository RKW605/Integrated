import pygame
from core_ui import *
from speech_engine import speak_text

# ----------------- Layout Data -----------------
alpha_buttons = {
    (0, 0): "A    B    C\n\nD    E    F",
    (0, 1): "G    H    I\n\nJ    K    L",
    (0, 2): "M    N    O\n\nP    Q    R",
    (2, 0): "S    T    U\n\nV    W    X",
    (2, 1): "Y    Z    |__|\n\n<--    Clear    Nums",
    (2, 2): "PDM   CL    HA\n\nAboutUs    LANGUAGE    WCC",
}

LANGUAGE_SELECTION_LAYOUT_ENGLISH = {
    (0, 0): "GUJARATI",
    (0, 1): "GUJARATI",
    (0, 2): "GUJARATI",
    (2, 0): "HINDI",
    (2, 1): "HINDI",
    (2, 2): "HINDI"
}


nums_buttons = {
    (0, 0): "1    2    3\n\n4    5    6",
    (0, 1): "7    8    9\n\n0    @    #",
    (0, 2): ",    .    !\n\n?    %    $",
    (2, 0): "Rupees    +    -\n\n*    /    ^",
    (2, 1): "'    \"    `\n\n~    |    \\",
    (2, 2): "Back"
}

pdm_categories = {
    (0, 0): "Basic Needs & Requests",
    (0, 1): "Personal Status",
    (0, 2): "Daily Activities",
    (2, 0): "Emotional Expressions",
    (2, 1): "Emergency Message",
    (2, 2): "Other Sentences",
}

pdm_messages = {
    "Basic Needs & Requests": [
        "I need water", "I need food", "Please bring a blanket",
        "May I have a chair?", "I need medicine", "I need help"
    ],
    "Personal Status": [
        "I am okay", "I am sick", "I am tired",
        "I am resting", "I am confused", "I am alert"
    ],
    "Daily Activities": [
        "I am eating now", "I am going out", "I am studying",
        "I am cleaning", "I am walking", "I am reading"
    ],
    "Emotional Expressions": [
        "I feel happy", "I feel sad", "I feel angry",
        "I feel calm", "I feel anxious", "I feel grateful"
    ],
    "Emergency Message": [
        "Call ambulance", "Call police", "I am lost",
        "I need urgent help", "Fire here", "Evacuate now"
    ],
    "Other Sentences": [
        "Good morning", "Good night", "Thank you",
        "You're welcome", "Excuse me", "See you soon"
    ],
}

placeholders = {"CL", "HA", "AboutUs", "WCC"}
POSITIONS = [(0, 0), (0, 1), (0, 2), (2, 0), (2, 1), (2, 2)]

# ----------------- Helpers -----------------
def make_spread_from_items(items):
    spread = {}
    for i, pos in enumerate(POSITIONS):
        spread[pos] = items[i] if i < len(items) else ""
    return spread

def open_spread_from_alpha_cell(r, c):
    items = alpha_buttons[(r, c)].replace("\n\n", " ").split()
    return make_spread_from_items(items)

def open_spread_from_nums_cell(r, c):
    items = nums_buttons[(r, c)].replace("\n\n", " ").split()
    return make_spread_from_items(items)

def open_spread_from_pdm_category(category_name):
    items = pdm_messages.get(category_name, [])
    return make_spread_from_items(items)

def handle_click_label(label, text):
    if not label: return text
    if label in placeholders: return text
    if label == "|__|": return text + " "
    if label == "<--": return text[:-1]
    if label == "Clear": return ""
    return text + label

def handle_language_select_click(pos, btn_rects, layout):
    for (r, c), rect in btn_rects.items():
        if rect.collidepoint(pos):
            choice = layout.get((r, c), "")
            if choice == "ENGLISH":
                return "SWITCH_ENGLISH"
            elif choice == "GUJARATI":
                return "SWITCH_GUJARATI"
            elif choice == "HINDI":
                return "SWITCH_HINDI"
    return None

# ----------------- Event Handlers -----------------
def handle_main_click(pos, btn_rects, text):
    for (r, c), rect in btn_rects.items():
        if rect.collidepoint(pos):
            if (r, c) == (1, 2):  # Speak button
                speak_text(text, language="ENGLISH")
                return "main", {}
            if (r, c) in alpha_buttons:
                return "spread_alpha", open_spread_from_alpha_cell(r, c)
    return "main", {}

def handle_spread_alpha_click(pos, btn_rects, textbox_rect, spread, text):
    for (r, c), rect in btn_rects.items():
        if rect.collidepoint(pos):
            lbl = spread.get((r, c), "")
            if lbl == "Nums": return "nums", {}, text
            if lbl == "PDM": return "pdm_categories", {}, text
            if lbl == "LANGUAGE": return "language_select", LANGUAGE_SELECTION_LAYOUT_ENGLISH, ""
            if lbl: text = handle_click_label(lbl, text)
            return "main", {}, text
    if textbox_rect.collidepoint(pos): return "main", {}, text
    return "spread_alpha", spread, text

def handle_nums_click(pos, btn_rects):
    for (r, c), rect in btn_rects.items():
        if rect.collidepoint(pos):
            if (r, c) == (2, 2): return "main", {}
            if (r, c) in nums_buttons: return "spread_nums", open_spread_from_nums_cell(r, c)
    return "nums", {}

def handle_spread_nums_click(pos, btn_rects, textbox_rect, spread, text):
    for (r, c), rect in btn_rects.items():
        if rect.collidepoint(pos):
            lbl = spread.get((r, c), "")
            if lbl: text = handle_click_label(lbl, text)
            return "main", {}, text
    if textbox_rect.collidepoint(pos): return "main", {}, text
    return "spread_nums", spread, text

def handle_pdm_categories_click(pos, btn_rects):
    for (r, c), rect in btn_rects.items():
        if rect.collidepoint(pos):
            cat = pdm_categories.get((r, c), "")
            if cat: return "pdm_messages", open_spread_from_pdm_category(cat)
    return "pdm_categories", {}

def handle_pdm_messages_click(pos, btn_rects, textbox_rect, spread, text):
    for (r, c), rect in btn_rects.items():
        if rect.collidepoint(pos):
            lbl = spread.get((r, c), "")
            if lbl: text += lbl + " "
            return "main", {}, text
    if textbox_rect.collidepoint(pos): return "main", {}, text
    return "pdm_messages", spread, text

# ----------------- MAIN LOOP -----------------
def main():
    w, h = init_pygame_and_get_screen_size()
    screen = create_window(w, h)
    text, state, spread = "", "main", {}
    running = True

    while running:
        screen.fill(BLACK)
        draw_grid(screen, w, h)

        # Decide what to draw
        if state == "main": layout = alpha_buttons
        elif state == "nums": layout = nums_buttons
        elif state == "pdm_categories": layout = pdm_categories
        else: layout = spread

        btn_rects = draw_buttons(screen, w, h, layout)
        textbox_rect = draw_textbox(screen, w, h, text)
        pygame.display.update()

        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                running = False
            if e.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if state == "main": state, spread = handle_main_click(pos, btn_rects, text)
                elif state == "spread_alpha": state, spread, text = handle_spread_alpha_click(pos, btn_rects, textbox_rect, spread, text)
                elif state == "nums": state, spread = handle_nums_click(pos, btn_rects)
                elif state == "spread_nums": state, spread, text = handle_spread_nums_click(pos, btn_rects, textbox_rect, spread, text)
                elif state == "pdm_categories": state, spread = handle_pdm_categories_click(pos, btn_rects)
                elif state == "pdm_messages": state, spread, text = handle_pdm_messages_click(pos, btn_rects, textbox_rect, spread, text)
                elif state == "language_select":
                    choice = handle_language_select_click(pos, btn_rects, layout)
                    return choice

    pygame.quit()
