import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
BUTTON_SIZE = 100
BUTTON_MARGIN = 30

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 120, 255)
GRAY = (220, 220, 220)
DARK_GRAY = (100, 100, 100)
TITLE_OUTLINE = (1, 9, 69, 255)  # #010945ff

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("GonkWare")
clock = pygame.time.Clock()

# Load icons (replace with your own icon paths or use pygame.draw for simple shapes)
def load_icon(name, size):
    try:
        icon = pygame.image.load(f"assets/icons/{name}.png").convert_alpha()
        icon = pygame.transform.smoothscale(icon, (size, size))
        return icon
    except Exception:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        if name == "play":
            pygame.draw.polygon(surf, DARK_GRAY, [(size//4, size//4), (size//4, size*3//4), (size*3//4, size//2)])
        elif name == "quit":
            pygame.draw.line(surf, DARK_GRAY, (size//4, size//4), (size*3//4, size*3//4), 8)
            pygame.draw.line(surf, DARK_GRAY, (size*3//4, size//4), (size//4, size*3//4), 8)
        elif name == "settings":
            pygame.draw.circle(surf, DARK_GRAY, (size//2, size//2), size//3, 8)
            pygame.draw.circle(surf, DARK_GRAY, (size//2, size//2), size//8)
        return surf

ICON_NAMES = ["play", "settings", "quit"]
ICONS = [load_icon(name, BUTTON_SIZE//2) for name in ICON_NAMES]

# Helper to render outlined text
def render_outlined_text(font, message, fgcolor, outlinecolor, outline_width):
    base = font.render(message, True, fgcolor)
    outline = pygame.Surface((base.get_width() + 2*outline_width, base.get_height() + 2*outline_width), pygame.SRCALPHA)
    # Draw outline by blitting text shifted in 8 directions
    for dx in range(-outline_width, outline_width+1):
        for dy in range(-outline_width, outline_width+1):
            if dx != 0 or dy != 0:
                pos = (outline_width + dx, outline_width + dy)
                outline.blit(font.render(message, True, outlinecolor), pos)
    outline.blit(base, (outline_width, outline_width))
    return outline

class SettingsMenu:
    def __init__(self):
        self.options = ["Back"]
        self.selected = 0

    def draw(self):
        screen.fill(WHITE)
        font = pygame.font.Font("assets/font/PhillySans.ttf", 64)
        title_surface = render_outlined_text(font, "Settings", WHITE, TITLE_OUTLINE, 4)
        screen.blit(title_surface, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 100))

        option_font = pygame.font.Font("assets/font/PhillySans.ttf", 36)
        for i, option in enumerate(self.options):
            color = BLUE if i == self.selected else BLACK
            text = option_font.render(option, True, color)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 300 + i * 80))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_DOWN):
                self.selected = 0  # Only one option
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                if self.selected == 0:
                    return "back"
        return None

# Menu state
class Menu:
    def __init__(self):
        self.options = ["Start Game", "Settings", "Quit"]
        self.selected = 0

    def draw(self):
        screen.fill(WHITE)
        # Title on the left, vertically centered, with outline
        font = pygame.font.Font("assets/font/PhillySans.ttf", 74)
        title_surface = render_outlined_text(font, "GonkWare", WHITE, TITLE_OUTLINE, 4)
        title_x = 60
        title_y = SCREEN_HEIGHT // 2 - title_surface.get_height() // 2
        screen.blit(title_surface, (title_x, title_y))

        # Buttons vertically aligned on the right
        total_height = len(self.options) * BUTTON_SIZE + (len(self.options) - 1) * BUTTON_MARGIN
        start_y = SCREEN_HEIGHT // 2 - total_height // 2
        button_x = SCREEN_WIDTH - BUTTON_SIZE - 60

        option_font = pygame.font.Font("assets/font/PhillySans.ttf", 36)
        for i, option in enumerate(self.options):
            button_y = start_y + i * (BUTTON_SIZE + BUTTON_MARGIN)
            rect = pygame.Rect(button_x, button_y, BUTTON_SIZE, BUTTON_SIZE)
            color = BLUE if i == self.selected else GRAY
            pygame.draw.rect(screen, color, rect, border_radius=18)
            pygame.draw.rect(screen, DARK_GRAY, rect, 4, border_radius=18)

            # Draw icon centered in button
            icon = ICONS[i]
            icon_rect = icon.get_rect(center=rect.center)
            screen.blit(icon, icon_rect)

            # Draw label to the left of the button, vertically centered
            text = option_font.render(option, True, BLACK)
            text_rect = text.get_rect()
            text_rect.centery = rect.centery
            text_rect.right = rect.left - 20
            screen.blit(text, text_rect)

        # Footer
        footer_font = pygame.font.Font("assets/font/PhillySans.ttf", 28)
        footer_text = footer_font.render("UP/DOWN to navigate, ENTER to select", True, BLACK)
        screen.blit(footer_text, (SCREEN_WIDTH // 2 - footer_text.get_width() // 2, SCREEN_HEIGHT - 40))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return self.selected
        return None

# Main loop
def main():
    menu = Menu()
    settings_menu = SettingsMenu()
    state = "main"
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

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
            menu.draw()
        elif state == "settings":
            settings_menu.draw()

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()