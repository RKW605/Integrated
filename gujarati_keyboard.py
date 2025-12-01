# gujarati_keyboard.py
import os
import pygame
import pygame.freetype
from core_ui import draw_grid, draw_textbox, create_window, init_pygame_and_get_screen_size, BLACK, WHITE, PURPLE, GREEN, TEXT_COLOR
from speech_engine import speak_text

# Init freetype
pygame.init()
pygame.freetype.init()

# Load Gujarati freetype font
FONT_PATH_GUJARATI = os.path.join("assets", "fonts", "gujarati.ttf")
gujarati_font = pygame.freetype.Font(FONT_PATH_GUJARATI, 40)

# The six positions (order used for spreads)
POSITIONS = [(0, 0), (0, 1), (0, 2), (2, 0), (2, 1), (2, 2)]

# ----------------- Main layout (single-string per cell, like English) -----------------
MAIN_BUTTONS_GUJARATI = {
    (0, 0): "ક    ખ    ગ\n\nઘ    ચ    છ",
    (0, 1): "જ    ઝ    ટ\n\nઠ    ડ    ધ",
    (0, 2): "ણ    ત    થ\n\nદ    ધ    ન",
    (2, 0): "પ    ફ    બ\n\nભ    મ    ય",
    (2, 1): "ર    લ    વ\n\nશ    ષ    સ",
    # sixth cell: replaced 'સ્વર' with '<--' and 'Nums' with '|__|' (space)
    (2, 2): "હ    ળ    <--\n\n|__|    PDM    Others"
}

OTHERS_BUTTONS_GUJARATI = {
    (0, 0): "About us",
    (0, 1): "સ્વર",
    (0, 2): "Nums",
    (2, 0): "HA",
    (2, 1): "Clear",
    (2, 2): "LANGUAGE"
}

LANGUAGE_SELECTION_LAYOUT_GUJARATI = {
    (0, 0): "ENGLISH",  # top-left
    (0, 1): "ENGLISH",  # top-middle
    (0, 2): "ENGLISH",  # top-right
    (2, 0): "HINDI",    # bottom-left
    (2, 1): "HINDI",    # bottom-middle
    (2, 2): "HINDI"     # bottom-right
}

SWAR_BUTTONS_GUJARATI = {
    (0, 0): "અ આ ઇ\n\nઈ ઉ ઊ",
    (0, 1): "ઋ ૠ એ\n\nઐ ઓ ઔ",
    (0, 2): "અં અઃ ક્ષ\n\nક્ષા ક્ષિ ક્ષી",
    (2, 0): "ક્ષુ ક્ષૂ ક્ષે\n\nક્ષૈ ક્ષો ક્ષૌ",
    (2, 1): "ર્ક્ષ આં ઇં\n\nઈં ઉં ઊં",
    (2, 2): "એં  ઐં ઓં\n\nઔં ____ ____"
}

NUMS_BUTTONS_GUJARATI = {
    (0, 0): "1    2    3\n\n4    5    6",
    (0, 1): "7    8    9\n\n0    @    #",
    (0, 2): ",    .    !\n\n?    %    $",
    (2, 0): "Rupees    +    -\n\n*    /    ^",
    (2, 1): "'    \"    `\n\n~    |    \\",
    (2, 2): "____ ____ ____ ____ ____ ____"
}

# ----------------- Maatra groups template (will be formatted per alphabet) -----------------
# Templates use {a} as placeholder for the chosen base consonant.
MAATRA_GROUPS_TEMPLATE = {
    (0, 0): "{a} {a}્ {a}ા\n\nિ{a} {a}ી {a}ે",
    (0, 1): "{a}ૈ {a}ુ {a}ૂ\n\n{a}ો {a}ૌ {a}ં",
    (0, 2): "{a}ઃ {a}્ર {a}્રા\n\nિ{a}્ર {a}્રી {a}ૃ",
    (2, 0): "{a}્રૂ {a}્રે {a}્રૈ\n\n{a}્રો {a}્રૌ {a}્રં",
    (2, 1): "{a}્રઃ ર્{a} જ્ઞ\n\nજ્ઞા િજ્ઞ જ્ઞી",
    (2, 2): "જ્ઞુ જ્ઞૂ  જ્ઞે\n\nજ્ઞૈ જ્ઞો જ્ઞૌ"
}

# ----------------- Gujarati PDM (categories + messages) -----------------
PDM_CATEGORIES_GUJARATI = {
    (0, 0): "મૂળભૂત જરૂરિયાતો\nઅને વિનંતીઓ",
    (0, 1): "વ્યક્તિગત સ્થિતિ",
    (0, 2): "દૈનિક પ્રવૃત્તિઓ",
    (2, 0): "ભાવનાત્મક\nઅભિવ્યક્તિઓ",
    (2, 1): "આપત્તિ સંદેશ",
    (2, 2): "અન્ય વાક્યો"
}

PDM_MESSAGES_GUJARATI = {
    "મૂળભૂત જરૂરિયાતો\nઅને વિનંતીઓ": [
        "મને પાણી આપો", "મને ખાવું છે", "કૃપા કરીને બેડ લાવો",
        "મને કપડાં બદલો", "મને દવા જોઈએ", "મને મદદ જોઈએ"
    ],
    "વ્યક્તિગત સ્થિતિ": [
        "હું ઠીક છું", "હું બીમાર છું", "હું થાક્યો છું",
        "હું આરામ કરી રહ્યો છું", "હું ગભરાયો છું", "હું સતર્ક છું"
    ],
    "દૈનિક પ્રવૃત્તિઓ": [
        "હું આવી રહ્યો છું", "હું બહાર જઈ રહ્યો છું", "હું અભ્યાસ કરી રહ્યો છું",
        "હું સફાઇ કરી રહ્યો છું", "હું ચાલું છું", "હું વાંચી રહ્યો છું"
    ],
    "ભાવનાત્મક\nઅભિવ્યક્તિઓ": [
        "મને આનંદ છે", "મને દુઃખ છે", "મને ગુસ્સો આવે છે",
        "હું શાંત છું", "મને ચિંતા છે", "મને કૃપા લાગે છે"
    ],
    "આપત્તિ સંદેશ": [
        "મદદ કરો", "ઈમર્જન્સી! સહાય પણ મોકલો", "હું ભટકી ગયો છું",
        "મારી તાત્કાલીક મદદ કરો", "આગ લાગી છે", "અભ્યાસ સ્થળ છોડો"
    ],
    "અન્ય વાક્યો": [
        "શુભ સવાર", "શુભ રાત્રિ", "આભાર",
        "આપનું સ્વાગત છે", "માફ કરશો", "પાછા મળશું"
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
    for pos, template in MAATRA_GROUPS_TEMPLATE.items():
        groups[pos] = template.format(a=alpha)
    return groups

# In draw_buttons_gujarati: keep speak button green always
def draw_buttons_gujarati(screen, w, h, layout):
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
            line_rects = [gujarati_font.get_rect(line) for line in lines]
            total_h = sum(rh.height for rh in line_rects)
            y = rect.y + (rect.height - total_h) // 2

            for i, line in enumerate(lines):
                rct = line_rects[i]
                x = rect.x + (rect.width - rct.width) // 2
                gujarati_font.render_to(screen, (x, y), line, WHITE)
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
            layout = MAIN_BUTTONS_GUJARATI
        elif state in ("spread_alpha", "maatra_spread"):
            layout = spread
        elif state == "maatra_groups":
            layout = spread
        elif state == "pdm_categories":
            layout = PDM_CATEGORIES_GUJARATI
        elif state == "pdm_messages" and current_pdm_category:
            msgs = PDM_MESSAGES_GUJARATI.get(current_pdm_category, [])
            layout = make_spread_from_list(msgs)
        elif state == "others":
            layout = OTHERS_BUTTONS_GUJARATI
        elif state == "nums":
            layout = spread
        elif state == "swar":
            layout = spread
        elif state == "nums_spread":
            layout = spread
        elif state == "swar_spread":
            layout = spread
        elif state == "language_select":
            layout = LANGUAGE_SELECTION_LAYOUT_GUJARATI

        btn_rects = draw_buttons_gujarati(screen, w, h, layout)
        # draw textbox using freetype font
        textbox_rect = draw_textbox(screen, w, h, text, custom_font=gujarati_font, use_freetype=True)

        pygame.display.update()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                running = False
            if ev.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                # QUICK: if user clicked speak button (only active green in main)
                if (1, 2) in btn_rects and btn_rects[(1, 2)].collidepoint(pos):
                    speak_text(text, language="GUJARATI")
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
                # layout may be PDM_CATEGORIES_GUJARATI (mapping) or spread (dict) or MAIN_BUTTONS_GUJARATI (dict)
                if isinstance(layout, dict):
                    # layout used by draw is dict keyed by positions; but for pdm_messages layout is also a dict (from make_spread_from_string)
                    current_label = layout.get((r, c), "")

                # ----------------- State logic -----------------
                if state == "main":
                    # clicking main cell => produce spread of its 6 items (may include special tokens like <-- or |__| or PDM/CL)
                    main_str = MAIN_BUTTONS_GUJARATI.get((r, c), "")
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
                        spread = NUMS_BUTTONS_GUJARATI
                        state = "nums"
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
                    cat = PDM_CATEGORIES_GUJARATI.get((r, c), "")
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
                    chosen = OTHERS_BUTTONS_GUJARATI.get((r, c), "")
                    if not chosen:
                        continue

                    if chosen == "About us":
                        print("About us clicked")  # placeholder

                    elif chosen == "સ્વર":
                        spread = SWAR_BUTTONS_GUJARATI
                        state = "swar"
                        continue

                    elif chosen == "Nums":
                        spread = NUMS_BUTTONS_GUJARATI
                        state = "nums"
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
