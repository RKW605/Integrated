# hindi_keyboard.py
import os
import pygame
import pygame.freetype
from core_ui import draw_grid, draw_textbox, create_window, init_pygame_and_get_screen_size, BLACK, WHITE, PURPLE, GREEN, TEXT_COLOR
from speech_engine import speak_text

# Init freetype
pygame.init()
pygame.freetype.init()

# Load Hindi freetype font
FONT_PATH_HINDI = os.path.join("assets", "fonts", "hindi.ttf")  # Add this font to your project
hindi_font = pygame.freetype.Font(FONT_PATH_HINDI, 40)

# The six positions (order used for spreads)
POSITIONS = [(0, 0), (0, 1), (0, 2), (2, 0), (2, 1), (2, 2)]

# ----------------- Main layout (single-string per cell, like English) -----------------
MAIN_BUTTONS_HINDI = {
    (0, 0): "क    ख    ग\n\nघ    च    छ",
    (0, 1): "ज    झ    ट\n\nठ    ड    ढ",
    (0, 2): "ण    त    थ\n\nद    ध    न",
    (2, 0): "प    फ   ब\n\nभ   म   य",
    (2, 1): "र    ल   व\n\nश   ष   स",
    # sixth cell: replaced 'સ્વર' with '<--' and 'Nums' with '|__|' (space)
    (2, 2): "ह    ज़    <--\n\n|__|    PDM    Others"
}

OTHERS_BUTTONS_HINDI = {
    (0, 0): "About us",
    (0, 1): "स्वर",
    (0, 2): "Nums",
    (2, 0): "HA",
    (2, 1): "Clear",
    (2, 2): "LANGUAGE"
}

LANGUAGE_SELECTION_LAYOUT_HINDI = {
    (0, 0): "ENGLISH",  # top-left
    (0, 1): "ENGLISH",  # top-middle
    (0, 2): "ENGLISH",  # top-right
    (2, 0): "GUJARATI",    # bottom-left
    (2, 1): "GUJARATI",    # bottom-middle
    (2, 2): "GUJARATI"     # bottom-right
}

SWAR_BUTTONS_HINDI = {
    (0, 0): "अ आ इ\n\nई उ ऊ",
    (0, 1): "ऋ ॠ ए\n\nऐ ओ औ",
    (0, 2): "अं अः क्ष\n\nक्षा क्षि क्षी",
    (2, 0): "क्षु क्षू क्षो\n\nक्षौ क्षं क्षः",
    (2, 1): "र्क्ष आं इं\n\nईं उं ऊं",
    (2, 2): "एं ऐं ओं\n\nऔं ____ ____"
}

NUMS_BUTTONS_HINDI = {
    (0, 0): "1    2    3\n\n4    5    6",
    (0, 1): "7    8    9\n\n0    @    #",
    (0, 2): ",    .    !\n\n?    %    $",
    (2, 0): "Rupees    +    -\n\n*    /    ^",
    (2, 1): "'    \"    `\n\n~    |    \\",
    (2, 2): "____ ____ ____\n\n____ ____ ____"
}

# ----------------- Maatra groups template (for Hindi) -----------------
MAATRA_GROUPS_TEMPLATE_HINDI = {
    (0, 0): "{a} {a}् {a}ा\n\n{a}ि {a}ी {a}े",
    (0, 1): "{a}ै {a}ु {a}ू\n\n{a}ो {a}ौ {a}ं",
    (0, 2): "{a}ः {a}्र {a}्रा\n\n{a}्रि {a}्री {a}ृ",
    (2, 0): "{a}्रू {a}्रे {a}्रै\n\n{a}्रो {a}्रौ {a}्रं",
    (2, 1): "{a}्रः र्{a} ज्ञ\n\nज्ञा ज्ञि ज्ञी",
    (2, 2): "ज्ञु ज्ञू ज्ञे\n\nज्ञै ज्ञो ज्ञौ"
}


# ----------------- Hindi PDM Categories -----------------
PDM_CATEGORIES_HINDI = {
    (0, 0): "मूलभूत आवश्यकताएँ\nऔर अनुरोध",
    (0, 1): "व्यक्तिगत स्थिति",
    (0, 2): "दैनिक गतिविधियाँ",
    (2, 0): "भावनात्मक\nअभिव्यक्तियाँ",
    (2, 1): "आपातकाल संदेश",
    (2, 2): "अन्य वाक्य"
}

# ----------------- Hindi PDM Messages -----------------
PDM_MESSAGES_HINDI = {
    "मूलभूत आवश्यकताएँ\nऔर अनुरोध": [
        "मुझे पानी दो", "मुझे खाना चाहिए", "कृपया बिस्तर लाओ",
        "मेरे कपड़े बदलो", "मुझे दवा चाहिए", "मुझे मदद चाहिए"
    ],
    "व्यक्तिगत स्थिति": [
        "मैं ठीक हूँ", "मैं बीमार हूँ", "मैं थका हुआ हूँ",
        "मैं आराम कर रहा हूँ", "मैं घबराया हुआ हूँ", "मैं सतर्क हूँ"
    ],
    "दैनिक गतिविधियाँ": [
        "मैं आ रहा हूँ", "मैं बाहर जा रहा हूँ", "मैं पढ़ाई कर रहा हूँ",
        "मैं सफाई कर रहा हूँ", "मैं चल रहा हूँ", "मैं पढ़ रहा हूँ"
    ],
    "भावनात्मक\nअभिव्यक्तियाँ": [
        "मुझे खुशी है", "मुझे दुख है", "मुझे गुस्सा आ रहा है",
        "मैं शांत हूँ", "मुझे चिंता है", "मुझे दया आ रही है"
    ],
    "आपातकाल संदेश": [
        "मदद करो", "आपातकाल! तुरंत सहायता भेजो", "मैं खो गया हूँ",
        "मुझे तुरंत मदद चाहिए", "आग लग गई है", "स्थान खाली करो"
    ],
    "अन्य वाक्य": [
        "सुप्रभात", "शुभ रात्रि", "धन्यवाद",
        "आपका स्वागत है", "माफ कीजिए", "फिर मिलेंगे"
    ]
}


# ----------------- Helpers -----------------
def make_spread_from_string(s: str):
    """
    Convert a main-string or multi-line group string to an ordered spread dict:
    POSITIONS -> token (string)
    """
    tokens = s.replace("\n\n", " ").split()
    spread = {}
    for i, pos in enumerate(POSITIONS):
        spread[pos] = tokens[i] if i < len(tokens) else ""
    return spread

def make_spread_from_list(items):
    """Takes a list of strings (even with spaces) -> maps each to one cell"""
    spread = {}
    for i, pos in enumerate(POSITIONS):
        spread[pos] = items[i] if i < len(items) else ""
    return spread

def generate_maatra_groups(alpha: str):
    """Return dict pos -> multi-line group-string for given alphabet alpha."""
    groups = {}
    for pos, template in MAATRA_GROUPS_TEMPLATE_HINDI.items():
        groups[pos] = template.format(a=alpha)
    return groups

# In draw_buttons_hindi: keep speak button green always
def draw_buttons_hindi(screen, w, h, layout):
    cell_w, cell_h = w // 3, h // 3
    xm, ym = cell_w // 12, cell_h // 12
    btn_rects = {}

    for r in range(3):
        for c in range(3):
            if (r, c) in [(1, 0), (1, 1)]:
                continue

            rect = pygame.Rect(c * cell_w + xm, r * cell_h + ym, cell_w - 2 * xm, cell_h - 2 * ym)
            btn_rects[(r, c)] = rect

            # Speak button stays green always
            if (r, c) == (1, 2):
                color = GREEN
                pygame.draw.rect(screen, color, rect, border_radius=6)
                sys_font = pygame.font.SysFont(None, 42, bold=True)
                surf = sys_font.render("Speak", True, WHITE)
                screen.blit(surf, surf.get_rect(center=rect.center))
                continue

            # Purple for all other cells
            pygame.draw.rect(screen, PURPLE, rect, border_radius=6)
            label = layout.get((r, c), "")
            if not label:
                continue

            # Multiline text center
            lines = label.split("\n")
            line_rects = [hindi_font.get_rect(line) for line in lines]
            total_h = sum(rh.height for rh in line_rects)
            y = rect.y + (rect.height - total_h) // 2

            for i, line in enumerate(lines):
                rct = line_rects[i]
                x = rect.x + (rect.width - rct.width) // 2
                hindi_font.render_to(screen, (x, y), line, WHITE)
                y += rct.height

    return btn_rects


# ----------------- Main loop & state machine -----------------
def main():
    w, h = init_pygame_and_get_screen_size()
    screen = create_window(w, h)

    text = ""
    state = "main"  # main, spread_alpha, maatra_groups, maatra_spread, pdm_categories, pdm_messages
    spread = {}
    current_alphabet = ""
    current_pdm_category = None

    running = True
    while running:
        screen.fill(BLACK)
        draw_grid(screen, w, h)

        # choose layout for drawing
        if state == "main":
            layout = MAIN_BUTTONS_HINDI
        elif state in ("spread_alpha", "maatra_spread"):
            layout = spread
        elif state == "maatra_groups":
            layout = spread
        elif state == "pdm_categories":
            layout = PDM_CATEGORIES_HINDI
        elif state == "pdm_messages" and current_pdm_category:
            msgs = PDM_MESSAGES_HINDI.get(current_pdm_category, [])
            layout = make_spread_from_list(msgs)
        elif state == "others":
            layout = OTHERS_BUTTONS_HINDI
        elif state == "nums":
            layout = spread
        elif state == "swar":
            layout = spread
        elif state == "nums_spread":
            layout = spread
        elif state == "swar_spread":
            layout = spread
        elif state == "language_select":
            layout = LANGUAGE_SELECTION_LAYOUT_HINDI

        btn_rects = draw_buttons_hindi(screen, w, h, layout)
        # draw textbox using freetype font
        textbox_rect = draw_textbox(screen, w, h, text, custom_font=hindi_font, use_freetype=True)

        pygame.display.update()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                running = False
            if ev.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                # QUICK: if user clicked speak button (only active green in main)
                if (1, 2) in btn_rects and btn_rects[(1, 2)].collidepoint(pos):
                    speak_text(text, language="HINDI")
                    continue

                # find which button was clicked
                clicked = None
                for key, rect in btn_rects.items():
                    if rect.collidepoint(pos):
                        clicked = key
                        break
                if clicked is None:
                    # clicked outside buttons: if clicked textbox, clear it (old behaviour)
                    if textbox_rect.collidepoint(pos):
                        state = "main"
                        spread = {}
                    continue

                r, c = clicked
                # get the label shown at that moment
                current_label = None
                # layout may be PDM_CATEGORIES_HINDI (mapping) or spread (dict) or MAIN_BUTTONS_HINDI (dict)
                if isinstance(layout, dict):
                    # layout used by draw is dict keyed by positions; but for pdm_messages layout is also a dict (from make_spread_from_string)
                    current_label = layout.get((r, c), "")

                # ----------------- State logic -----------------
                if state == "main":
                    # clicking main cell => produce spread of its 6 items (may include special tokens like <-- or |__| or PDM/CL)
                    main_str = MAIN_BUTTONS_HINDI.get((r, c), "")
                    if not main_str:
                        continue
                    spread = make_spread_from_string(main_str)
                    state = "spread_alpha"
                    continue

                elif state == "spread_alpha":
                    chosen = spread.get((r, c), "")
                    if not chosen:
                        continue
                    # handle special tokens immediately here
                    if chosen == "<--":
                        text = text[:-1]
                        state = "main"
                        spread = {}
                        continue
                    if chosen == "|__|":
                        text += " "
                        state = "main"
                        spread = {}
                        continue
                    if chosen == "PDM":
                        state = "pdm_categories"
                        spread = {}
                        current_pdm_category = None
                        continue
                    if chosen == "Others":
                        state = "others"
                        spread = {}
                        continue
                    if chosen == "Nums":
                        spread = NUMS_BUTTONS_HINDI
                        state = "nums"
                        continue
                    if chosen == "स्वर":
                        spread = SWAR_BUTTONS_HINDI
                        state = "swar"
                        continue
                    if chosen == "Clear":
                        text = ""
                        state = "main"
                        spread = {}
                        continue
                    # otherwise it's a base alphabet -> open its maatra groups
                    current_alphabet = chosen
                    spread = generate_maatra_groups(chosen)
                    state = "maatra_groups"
                    continue

                elif state == "maatra_groups":
                    # clicked a group (multi-line string) -> generate final spread of maatras
                    group_str = spread.get((r, c), "")
                    if not group_str or group_str.strip().startswith("____"):
                        # placeholder -> do nothing and go back to main (or stay)
                        state = "main"
                        spread = {}
                        continue
                    # make final spread from this group string
                    spread = make_spread_from_string(group_str)
                    state = "maatra_spread"
                    continue

                elif state == "maatra_spread":
                    chosen = spread.get((r, c), "")
                    if chosen and not chosen.startswith("____"):
                        # append chosen maatra/cluster to textbox
                        text += chosen
                    # after selecting a maatra, always return to main
                    state = "main"
                    spread = {}
                    current_alphabet = ""
                    continue

                elif state == "pdm_categories":
                    cat = PDM_CATEGORIES_HINDI.get((r, c), "")
                    if cat:
                        current_pdm_category = cat
                        state = "pdm_messages"
                        # layout will be generated above in drawing step
                    continue

                elif state == "pdm_messages":
                    chosen = layout.get((r, c), "")
                    if chosen:
                        # layout here is a dict produced by make_spread_from_string("  ".join(msgs))
                        # but in drawing step we used that dict; chosen is a message token
                        text += (" " + chosen) if text and not text.endswith(" ") else chosen
                    # after selecting PDM message return to main
                    state = "main"
                    spread = {}
                    current_pdm_category = None
                    continue
                elif state == "others":
                    chosen = OTHERS_BUTTONS_HINDI.get((r, c), "")
                    if not chosen:
                        continue

                    if chosen == "About us":
                        print("About us clicked")  # placeholder

                    elif chosen == "સ્વર":
                        print("સ્વર clicked")      # placeholder

                    elif chosen == "Nums":
                        spread = NUMS_BUTTONS_HINDI
                        state = "nums"
                        continue
                    elif chosen == "स्वर":
                        spread = SWAR_BUTTONS_HINDI
                        state = "swar"
                        continue

                    elif chosen == "HA":
                        print("HA clicked")         # placeholder

                    elif chosen == "Clear":
                        text = ""
                        state = "main"
                        spread = {}
                        continue

                    elif chosen == "LANGUAGE":
                        text = ""  # clear textbox
                        state = "language_select"
                        spread = None  # no normal spread
                        continue

                    # After action, return to main unless Nums handled above
                    state = "main"
                    spread = {}
                    continue

                elif state == "nums":
                    chosen = spread.get((r, c), "")
                    if not chosen:
                        continue

                    # Spread the clicked NUMS cell's 6 items
                    spread = make_spread_from_string(chosen)
                    state = "nums_spread"  # new temporary state
                    continue

                elif state == "swar":
                    chosen = spread.get((r, c), "")
                    if not chosen:
                        continue

                    # Spread the clicked स्वर cell's 6 items
                    spread = make_spread_from_string(chosen)
                    state = "swar_spread"  # new temporary state
                    continue

                elif state == "nums_spread":
                    chosen = spread.get((r, c), "")
                    if chosen and not chosen.startswith("____"):
                        text += chosen  # append the number or symbol to textbox
                    # After picking one item, return to main keyboard
                    spread = {}
                    state = "main"
                    continue

                elif state == "swar_spread":
                    chosen = spread.get((r, c), "")
                    if chosen and not chosen.startswith("____"):
                        text += chosen  # append the स्वर
                    # After picking one item, return to main keyboard
                    spread = {}
                    state = "main"
                    continue
                
                if state == "language_select":
                    chosen = layout.get((r, c), "")
                    if chosen == "ENGLISH":
                        return "SWITCH_ENGLISH"
                    elif chosen == "GUJARATI":
                        return "SWITCH_GUJARATI"
                    elif chosen == "HINDI":
                        return "SWITCH_HINDI"
                
                # fallback: if clicked textbox, clear
                if textbox_rect.collidepoint(pos):
                    text = ""

    pygame.quit()

if __name__ == "__main__":
    main()
