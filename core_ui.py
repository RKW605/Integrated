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
    # Determine the pixel positions of the lines
    x1 = w // 3
    x2 = (2 * w) // 3
    y1 = h // 3
    y2 = (2 * h) // 3
    
    thickness = 3
    
    # Draw vertical lines
    pygame.draw.line(screen, WHITE, (x1, 0), (x1, h), thickness)
    pygame.draw.line(screen, WHITE, (x2, 0), (x2, h), thickness)
    
    # Draw horizontal lines
    pygame.draw.line(screen, WHITE, (0, y1), (w, y1), thickness)
    pygame.draw.line(screen, WHITE, (0, y2), (w, y2), thickness)

# ----------------- Text Drawing -----------------
def render_text(surface, text, font, pos, color, use_freetype=False):
    if use_freetype:
        font.render_to(surface, pos, text, color)
    else:
        surf = font.render(text, True, color)
        surface.blit(surf, pos)

# ----------------- Buttons -----------------
def draw_buttons(screen, w, h, texts, custom_font=None, use_freetype=False):
    rects = {}
    
    # Loop through the 3x3 grid
    for r in range(3):
        for c in range(3):
            # 1. Skip the Textbox area (Row 1, Cols 0 and 1)
            #    We only want to draw buttons in the other spots.
            if r == 1 and c < 2:
                continue
            
            # 2. Calculate coordinates EXACTLY (Pixel Perfect)
            #    We calculate the start and end of the cell to determine width/height.
            #    This handles cases where screen width isn't perfectly divisible by 3.
            x_start = (c * w) // 3
            y_start = (r * h) // 3
            x_end = ((c + 1) * w) // 3
            y_end = ((r + 1) * h) // 3
            
            width = x_end - x_start
            height = y_end - y_start
            
            rect = pygame.Rect(x_start, y_start, width, height)
            rects[(r, c)] = rect

            # 3. Determine Color and Label
            if r == 1 and c == 2:  # Speak button (Row 1, Col 2)
                color = GREEN
                label = "Speak"
                font = custom_font if custom_font else pygame.font.Font(None, 50)
            else:
                color = PURPLE
                label = texts.get((r, c), "")
                font = custom_font if custom_font else pygame.font.Font(None, 40)

            # 4. Draw Rect (Full Size, No Margins)
            pygame.draw.rect(screen, color, rect)

            # 5. Center Text
            if label:
                lines = label.split("\n")
                if use_freetype:
                    line_height = font.get_sized_height()
                else:
                    line_height = font.get_linesize()
                
                total_h = len(lines) * line_height
                y_text_start = rect.centery - total_h // 2
                
                for i, line in enumerate(lines):
                    if use_freetype:
                        text_w, text_h = font.get_rect(line).size
                        pos = (rect.centerx - text_w // 2, y_text_start + i * text_h)
                        font.render_to(screen, pos, line, TEXT_COLOR)
                    else:
                        surf = font.render(line, True, TEXT_COLOR)
                        rrect = surf.get_rect(center=(rect.centerx, y_text_start + i * line_height + line_height // 2))
                        screen.blit(surf, rrect)
    return rects

# ----------------- Textbox -----------------
def draw_textbox(screen, w, h, text, custom_font=None, use_freetype=False):
    # Textbox occupies Row 1, Columns 0 and 1.
    
    # Calculate x, y, w, h exactly based on grid logic
    x_start = 0
    y_start = h // 3
    x_end = (2 * w) // 3  # Ends after 2nd column
    y_end = (2 * h) // 3  # Ends after 2nd row (start of 3rd)
    
    width = x_end - x_start
    height = y_end - y_start
    
    rect = pygame.Rect(x_start, y_start, width, height)
    
    pygame.draw.rect(screen, WHITE, rect)

    font = custom_font if custom_font else pygame.font.Font(None, 48)
    padding = 20
    
    lines = text.split("\n")
    cur_y = rect.y + padding
    for line in lines:
        if use_freetype:
            font.render_to(screen, (rect.x + padding, cur_y), line, TXT_COLOR_BLACK)
            cur_y += font.height
        else:
            surf = font.render(line, True, TXT_COLOR_BLACK)
            screen.blit(surf, (rect.x + padding, cur_y))
            cur_y += surf.get_height()

    return rect
