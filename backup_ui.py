import pygame
import pygame.freetype

# ----------------- Colors -----------------
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
PURPLE = (128, 0, 128)
GREEN = (0, 255, 0)
TEXT_COLOR = WHITE
TXT_COLOR_BLACK = (0, 0, 0)

# ----------------- Basic UI -----------------
def init_pygame_and_get_screen_size():
    pygame.init()
    pygame.freetype.init()
    info = pygame.display.Info()
    return info.current_w, info.current_h

def create_window(w, h):
    return pygame.display.set_mode((w, h), pygame.FULLSCREEN)

def draw_grid(screen, w, h):
    thickness = 3
    pygame.draw.line(screen, WHITE, (w // 3, 0), (w // 3, h), thickness)
    pygame.draw.line(screen, WHITE, (2 * w // 3, 0), (2 * w // 3, h), thickness)
    pygame.draw.line(screen, WHITE, (0, h // 3), (w, h // 3), thickness)
    pygame.draw.line(screen, WHITE, (0, 2 * h // 3), (w, 2 * h // 3), thickness)

# ----------------- Text Drawing -----------------
def render_text(surface, text, font, pos, color, use_freetype=False):
    if use_freetype:
        font.render_to(surface, pos, text, color)
    else:
        surf = font.render(text, True, color)
        surface.blit(surf, pos)

# ----------------- Buttons -----------------
def draw_buttons(screen, w, h, texts, custom_font=None, use_freetype=False):
    cell_w, cell_h = w // 3, h // 3
    rects = {}
    for r in range(3):
        for c in range(3):
            if (r, c) in [(1, 0), (1, 1)]:
                continue
            x, y = c * cell_w, r * cell_h
            xm, ym = cell_w // 12, cell_h // 12
            rect = pygame.Rect(x + xm, y + ym, cell_w - 2 * xm, cell_h - 2 * ym)
            rects[(r, c)] = rect

            if (r, c) == (1, 2):
                color = GREEN
                label = "Speak"
                font = custom_font if custom_font else pygame.font.Font(None, 50)
            else:
                color = PURPLE
                label = texts.get((r, c), "")
                font = custom_font if custom_font else pygame.font.Font(None, 40)

            pygame.draw.rect(screen, color, rect)

            if label:
                lines = label.split("\n")
                total_h = len(lines) * (font.get_sized_height() if use_freetype else font.get_linesize())
                y_start = rect.centery - total_h // 2
                for i, line in enumerate(lines):
                    if use_freetype:
                        text_w, text_h = font.get_rect(line).size
                        pos = (rect.centerx - text_w // 2, y_start + i * text_h)
                        font.render_to(screen, pos, line, TEXT_COLOR)
                    else:
                        surf = font.render(line, True, TEXT_COLOR)
                        rrect = surf.get_rect(center=(rect.centerx, y_start + i * font.get_linesize()))
                        screen.blit(surf, rrect)
    return rects

# ----------------- Textbox -----------------
def draw_textbox(screen, w, h, text, custom_font=None, use_freetype=False):
    cell_w, cell_h = w // 3, h // 3
    total_w = 2 * cell_w
    xm = total_w // 24
    ym = cell_h // 12
    rect = pygame.Rect(xm, cell_h + ym, total_w - 2 * xm, cell_h - 2 * ym)
    pygame.draw.rect(screen, WHITE, rect)

    font = custom_font if custom_font else pygame.font.Font(None, 48)
    padding = 10
    max_width = max(1, rect.width - 2 * padding)

    # wrap text into multiple lines (like English keyboard)
    lines = text.split("\n")
    y = rect.y + padding
    for line in lines:
        if use_freetype:
            # compute position
            font.render_to(screen, (rect.x + padding, y), line, TXT_COLOR_BLACK)
            y += font.height
        else:
            surf = font.render(line, True, TXT_COLOR_BLACK)
            screen.blit(surf, (rect.x + padding, y))
            y += surf.get_height()

    return rect
