import pygame
import sys

# --- Initialization ---
pygame.init()

# --- Constants ---
BASE_WIDTH, BASE_HEIGHT = 800, 600
FPS = 60
BUTTON_SIZE = 100
BUTTON_MARGIN = 30

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 120, 255)
GRAY = (220, 220, 220)
DARK_GRAY = (100, 100, 100)
TITLE_OUTLINE = (1, 9, 69, 255)  # #010945ff

# --- Display Setup ---
screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("GonkWare")
clock = pygame.time.Clock()

# --- Utility Functions ---
def get_scale():
    win_w, win_h = screen.get_size()
    return win_w / BASE_WIDTH, win_h / BASE_HEIGHT

def scale_rect(rect, scale_x, scale_y):
    return pygame.Rect(
        int(rect.x * scale_x),
        int(rect.y * scale_y),
        int(rect.width * scale_x),
        int(rect.height * scale_y)
    )

def scale_pos(pos, scale_x, scale_y):
    return int(pos[0] * scale_x), int(pos[1] * scale_y)

def render_outlined_text(font, message, fgcolor, outlinecolor, outline_width):
    base = font.render(message, True, fgcolor)
    outline = pygame.Surface(
        (base.get_width() + 2 * outline_width, base.get_height() + 2 * outline_width),
        pygame.SRCALPHA
    )
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx or dy:
                pos = (outline_width + dx, outline_width + dy)
                outline.blit(font.render(message, True, outlinecolor), pos)
    outline.blit(base, (outline_width, outline_width))
    return outline

# --- Assets ---
def load_icon(name, size):
    try:
        icon = pygame.image.load(f"assets/icons/{name}.png").convert_alpha()
        return pygame.transform.smoothscale(icon, (size, size))
    except Exception:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        if name == "play":
            pygame.draw.polygon(surf, DARK_GRAY, [
                (size // 4, size // 4),
                (size // 4, size * 3 // 4),
                (size * 3 // 4, size // 2)
            ])
        elif name == "quit":
            pygame.draw.line(surf, DARK_GRAY, (size // 4, size // 4), (size * 3 // 4, size * 3 // 4), 8)
            pygame.draw.line(surf, DARK_GRAY, (size * 3 // 4, size // 4), (size // 4, size * 3 // 4), 8)
        elif name == "settings":
            pygame.draw.circle(surf, DARK_GRAY, (size // 2, size // 2), size // 3, 8)
            pygame.draw.circle(surf, DARK_GRAY, (size // 2, size // 2), size // 8)
        return surf

ICON_NAMES = ["play", "settings", "quit"]
ICONS = [load_icon(name, BUTTON_SIZE // 2) for name in ICON_NAMES]

def load_blurred_bg():
    try:
        img = pygame.image.load("assets/img/title.png").convert()
        return img
    except Exception:
        surf = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
        surf.fill(GRAY)
        return surf

BLURRED_BG = load_blurred_bg()
BG_SCROLL_SPEED = 40  # pixels per second

def draw_scrolling_bg(surface, dt, scroll_offset):
    scale_x, scale_y = get_scale()
    win_w, win_h = surface.get_size()
    bg = pygame.transform.smoothscale(BLURRED_BG, (int(win_w * 1.2), int(win_h * 1.2)))
    bg_w, bg_h = bg.get_size()
    x = int(-scroll_offset % (bg_w - win_w))
    surface.blit(bg, (-x, 0))
    if x > 0:
        surface.blit(bg, (bg_w - x, 0))
    return (scroll_offset + BG_SCROLL_SPEED * dt) % (bg_w - win_w)

# --- Audio ---
try:
    pygame.mixer.init()
    pygame.mixer.music.load("assets/audio/title.opus")
    pygame.mixer.music.play(-1)
except Exception as e:
    print("Could not play title music:", e)

# --- Slider Class ---
class Slider:
    def __init__(self, label, min_value, max_value, value, step=1):
        self.label = label
        self.min = min_value
        self.max = max_value
        self.value = value
        self.step = step
        self.dragging = False

    def set_value(self, new_value):
        self.value = max(self.min, min(self.max, new_value))

    def get_percent(self):
        return (self.value - self.min) / (self.max - self.min)

    def handle_mouse(self, mouse_x, slider_x, slider_width):
        percent = (mouse_x - slider_x) / slider_width
        percent = max(0, min(1, percent))
        raw_value = self.min + percent * (self.max - self.min)
        stepped = round(raw_value / self.step) * self.step
        self.set_value(stepped)

# --- Settings Menu ---
class SettingsMenu:
    def __init__(self):
        self.options = [
            ("slider", Slider("Music Volume", 0, 100, 80, 5)),
            ("slider", Slider("SFX Volume", 0, 100, 70, 5)),
            ("slider", Slider("Brightness", 0, 100, 50, 1)),
            ("slider", Slider("Mouse Sensitivity", 1, 10, 5, 1)),
            ("choice", {"label": "Graphics Quality", "choices": ["Low", "Medium", "High", "Ultra"], "selected": 2}),
            ("choice", {"label": "Difficulty", "choices": ["Easy", "Normal", "Hard", "Insane"], "selected": 1}),
            ("choice", {"label": "Language", "choices": ["EN", "FR", "DE", "JP"], "selected": 0}),
            ("choice", {"label": "Subtitles", "choices": ["Off", "On"], "selected": 1}),
            ("back", "Back"),
        ]
        self.selected = 0
        self.slider_rects = []

    def draw(self, dt, scroll_offset):
        scroll_offset = draw_scrolling_bg(screen, dt, scroll_offset)
        scale_x, scale_y = get_scale()
        font = pygame.font.Font("assets/font/PhillySans.ttf", int(64 * scale_y))
        title_surface = render_outlined_text(font, "Settings", WHITE, TITLE_OUTLINE, int(4 * scale_y))
        screen.blit(title_surface, (
            (screen.get_width() // 2) - (title_surface.get_width() // 2),
            int(60 * scale_y)
        ))

        option_font = pygame.font.Font("assets/font/PhillySans.ttf", int(36 * scale_y))
        slider_width = int(350 * scale_x)
        slider_height = int(16 * scale_y)
        self.slider_rects = []
        for i, (opt_type, opt) in enumerate(self.options):
            y = int(180 * scale_y) + i * int(70 * scale_y)
            color = BLUE if i == self.selected else WHITE  # <-- changed BLACK to WHITE

            if opt_type == "slider":
                label = option_font.render(opt.label, True, color)
                label_x = screen.get_width() // 2 - slider_width // 2 - label.get_width() - 30
                screen.blit(label, (label_x, y))
                slider_x = screen.get_width() // 2 - slider_width // 2
                slider_y = y + label.get_height() // 2 - slider_height // 2
                pygame.draw.rect(screen, GRAY, (slider_x, slider_y, slider_width, slider_height), border_radius=6)
                fill_width = int(slider_width * opt.get_percent())
                pygame.draw.rect(screen, BLUE if i == self.selected else DARK_GRAY, (slider_x, slider_y, fill_width, slider_height), border_radius=6)
                handle_x = slider_x + fill_width
                handle_rect = pygame.Rect(handle_x-8, slider_y-6, 16, slider_height+12)
                pygame.draw.rect(screen, DARK_GRAY, handle_rect, border_radius=8)
                self.slider_rects.append((slider_x, slider_y, slider_width, slider_height, i))
                value_text = option_font.render(str(opt.value), True, color)
                screen.blit(value_text, (slider_x + slider_width + 30, y))
            elif opt_type == "choice":
                label = option_font.render(opt["label"], True, color)
                label_x = screen.get_width() // 2 - slider_width // 2 - label.get_width() - 30
                screen.blit(label, (label_x, y))
                choices = opt["choices"]
                selected = opt["selected"]
                for idx, choice in enumerate(choices):
                    ch_color = BLUE if idx == selected and i == self.selected else WHITE  # <-- changed BLACK to WHITE
                    ch_font = pygame.font.Font("assets/font/PhillySans.ttf", int(32 * scale_y))
                    ch_text = ch_font.render(choice, True, ch_color)
                    ch_x = screen.get_width() // 2 - slider_width // 2 + idx * int(120 * scale_x)
                    screen.blit(ch_text, (ch_x, y))
            elif opt_type == "back":
                label = option_font.render(opt, True, color)
                screen.blit(label, (screen.get_width() // 2 - label.get_width() // 2, y))
        return scroll_offset

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key == pygame.K_LEFT:
                opt_type, opt = self.options[self.selected]
                if opt_type == "slider":
                    opt.set_value(opt.value - opt.step)
                elif opt_type == "choice":
                    opt["selected"] = (opt["selected"] - 1) % len(opt["choices"])
            elif event.key == pygame.K_RIGHT:
                opt_type, opt = self.options[self.selected]
                if opt_type == "slider":
                    opt.set_value(opt.value + opt.step)
                elif opt_type == "choice":
                    opt["selected"] = (opt["selected"] + 1) % len(opt["choices"])
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                opt_type, opt = self.options[self.selected]
                if opt_type == "back":
                    return "back"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            for slider_x, slider_y, slider_width, slider_height, idx in self.slider_rects:
                if slider_y <= my <= slider_y + slider_height and slider_x <= mx <= slider_x + slider_width:
                    opt_type, opt = self.options[idx]
                    if opt_type == "slider":
                        opt.dragging = True
                        opt.handle_mouse(mx, slider_x, slider_width)
                        self.selected = idx
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for opt_type, opt in self.options:
                if opt_type == "slider":
                    opt.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            mx, my = pygame.mouse.get_pos()
            for slider_x, slider_y, slider_width, slider_height, idx in self.slider_rects:
                opt_type, opt = self.options[idx]
                if opt_type == "slider" and getattr(opt, "dragging", False):
                    opt.handle_mouse(mx, slider_x, slider_width)
        return None

# --- Main Menu ---
class Menu:
    def __init__(self):
        self.options = ["Start Game", "Settings", "Quit"]
        self.selected = 0

    def draw(self, dt, scroll_offset):
        scroll_offset = draw_scrolling_bg(screen, dt, scroll_offset)
        scale_x, scale_y = get_scale()
        screen_w, screen_h = screen.get_size()
        font = pygame.font.Font("assets/font/PhillySans.ttf", int(74 * scale_y))
        title_surface = render_outlined_text(font, "GonkWare", WHITE, TITLE_OUTLINE, int(4 * scale_y))
        title_x = int(60 * scale_x)
        title_y = screen_h // 2 - title_surface.get_height() // 2
        screen.blit(title_surface, (title_x, title_y))

        btn_size = int(BUTTON_SIZE * min(scale_x, scale_y))
        btn_margin = int(BUTTON_MARGIN * scale_y)
        total_height = len(self.options) * btn_size + (len(self.options) - 1) * btn_margin
        start_y = screen_h // 2 - total_height // 2
        button_x = screen_w - btn_size - int(60 * scale_x)

        option_font = pygame.font.Font("assets/font/PhillySans.ttf", int(36 * scale_y))
        for i, option in enumerate(self.options):
            button_y = start_y + i * (btn_size + btn_margin)
            rect = pygame.Rect(button_x, button_y, btn_size, btn_size)
            color = BLUE if i == self.selected else GRAY
            pygame.draw.rect(screen, color, rect, border_radius=int(18 * min(scale_x, scale_y)))
            pygame.draw.rect(screen, DARK_GRAY, rect, int(4 * min(scale_x, scale_y)), border_radius=int(18 * min(scale_x, scale_y)))

            icon = pygame.transform.smoothscale(ICONS[i], (btn_size // 2, btn_size // 2))
            icon_rect = icon.get_rect(center=rect.center)
            screen.blit(icon, icon_rect)

            text = option_font.render(option, True, WHITE)  # <-- changed BLACK to WHITE
            text_rect = text.get_rect()
            text_rect.centery = rect.centery
            text_rect.right = rect.left - int(20 * scale_x)
            screen.blit(text, text_rect)

        footer_font = pygame.font.Font("assets/font/PhillySans.ttf", int(28 * scale_y))
        footer_text = footer_font.render("UP/DOWN to navigate, ENTER to select", True, WHITE)  # <-- changed BLACK to WHITE
        screen.blit(footer_text, (screen_w // 2 - footer_text.get_width() // 2, screen_h - int(40 * scale_y)))
        return scroll_offset

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.selected
        return None

# --- Main Loop ---
def main():
    menu = Menu()
    settings_menu = SettingsMenu()
    state = "main"
    running = True
    last_time = pygame.time.get_ticks() / 1000.0
    scroll_offset = 0

    while running:
        now = pygame.time.get_ticks() / 1000.0
        dt = now - last_time
        last_time = now

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                w, h = max(400, event.w), max(300, event.h)
                pygame.display.set_mode((w, h), pygame.RESIZABLE)

            if state == "main":
                result = menu.handle_event(event)
                if result == 0:
                    print("Start Game selected (implement game launch here)")
                elif result == 1:
                    state = "settings"
                elif result == 2:
                    pygame.quit()
                    sys.exit()
            elif state == "settings":
                result = settings_menu.handle_event(event)
                if result == "back":
                    state = "main"

        if state == "main":
            scroll_offset = menu.draw(dt, scroll_offset)
        elif state == "settings":
            scroll_offset = settings_menu.draw(dt, scroll_offset)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()