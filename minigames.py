import pygame
import requests
import random
import html
import time

# --- Constants ---
BASE_WIDTH, BASE_HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 120, 255)
GRAY = (220, 220, 220)
DARK_GRAY = (100, 100, 100)

TRIVIA_API = "https://opentdb.com/api.php"

# --- Utility ---
def fetch_trivia(subject, difficulty="medium", qtype="multiple"):
    """Fetch a single trivia question from Open Trivia DB."""
    category_map = {
        "math": 19,         # Mathematics
        "science": 17,      # Science & Nature
        "history": 23,      # History
        "geography": 22,    # Geography
        "english": 10,      # Books (closest to English/literature)
        "computers": 18,    # Computers
        "sports": 21,       # Sports
        "music": 12,        # Music
        "film": 11,         # Film
        "art": 25,          # Art
        "politics": 24,     # Politics
    }
    cat = category_map.get(subject, 9)  # 9 = General Knowledge
    params = {
        "amount": 1,
        "category": cat,
        "difficulty": difficulty,
        "type": qtype
    }
    try:
        resp = requests.get(TRIVIA_API, params=params, timeout=3)
        data = resp.json()
        if data["response_code"] == 0:
            q = data["results"][0]
            question = html.unescape(q["question"])
            correct = html.unescape(q["correct_answer"])
            incorrect = [html.unescape(ans) for ans in q["incorrect_answers"]]
            all_answers = incorrect + [correct]
            random.shuffle(all_answers)
            return {
                "question": question,
                "answers": all_answers,
                "correct": correct,
                "type": q["type"]
            }
    except Exception as e:
        print("Trivia fetch failed:", e)
    return None

# --- Minigame Base ---
class MiniGameBase:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.result = None  # None = running, True = win, False = lose

    def run(self, time_limit=6):
        """Run the minigame for up to time_limit seconds."""
        clock = pygame.time.Clock()
        start = time.time()
        while self.result is None and (time.time() - start) < time_limit:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                self.handle_event(event)
            self.draw(time_limit - (time.time() - start))
            pygame.display.flip()
            clock.tick(60)
        if self.result is None:
            self.result = False  # Time out = lose
        return self.result

    def handle_event(self, event):
        pass

    def draw(self, time_left):
        pass

# --- Multiple Choice Minigame ---
class TriviaMiniGame(MiniGameBase):
    def __init__(self, screen, font, subject):
        super().__init__(screen, font)
        self.trivia = fetch_trivia(subject)
        self.selected = 0

    def handle_event(self, event):
        if not self.trivia:
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.trivia["answers"])
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.trivia["answers"])
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.trivia["answers"][self.selected] == self.trivia["correct"]:
                    self.result = True
                else:
                    self.result = False

    def draw(self, time_left):
        self.screen.fill(DARK_GRAY)
        if not self.trivia:
            txt = self.font.render("Failed to load question!", True, WHITE)
            self.screen.blit(txt, (BASE_WIDTH//2 - txt.get_width()//2, BASE_HEIGHT//2 - txt.get_height()//2))
            return
        qtxt = self.font.render(self.trivia["question"], True, WHITE)
        self.screen.blit(qtxt, (BASE_WIDTH//2 - qtxt.get_width()//2, 60))
        for i, ans in enumerate(self.trivia["answers"]):
            color = BLUE if i == self.selected else WHITE
            atxt = self.font.render(ans, True, color)
            self.screen.blit(atxt, (BASE_WIDTH//2 - atxt.get_width()//2, 150 + i*60))
        timer = self.font.render(f"Time: {int(time_left)}", True, WHITE)
        self.screen.blit(timer, (BASE_WIDTH - 140, 20))

# --- Math Minigame (Short Answer) ---
class MathMiniGame(MiniGameBase):
    def __init__(self, screen, font):
        super().__init__(screen, font)
        # Generate a random math question (year 10 level)
        ops = [('+', lambda a, b: a + b), ('-', lambda a, b: a - b), ('*', lambda a, b: a * b), ('/', lambda a, b: a // b if b != 0 else 0)]
        op, fn = random.choice(ops)
        a = random.randint(10, 99)
        b = random.randint(2, 20) if op == '/' else random.randint(10, 99)
        self.question = f"{a} {op} {b} = ?"
        self.answer = str(fn(a, b))
        self.user_input = ""

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.user_input = self.user_input[:-1]
            elif event.key == pygame.K_RETURN:
                self.result = (self.user_input.strip() == self.answer)
            elif event.unicode.isdigit() or (event.unicode == '-' and len(self.user_input) == 0):
                self.user_input += event.unicode

    def draw(self, time_left):
        self.screen.fill(DARK_GRAY)
        qtxt = self.font.render(self.question, True, WHITE)
        self.screen.blit(qtxt, (BASE_WIDTH//2 - qtxt.get_width()//2, 120))
        atxt = self.font.render(self.user_input, True, BLUE)
        self.screen.blit(atxt, (BASE_WIDTH//2 - atxt.get_width()//2, 200))
        timer = self.font.render(f"Time: {int(time_left)}", True, WHITE)
        self.screen.blit(timer, (BASE_WIDTH - 140, 20))

# --- Fast Typing (English/Spelling) ---
class TypingMiniGame(MiniGameBase):
    WORDS = [
        "accommodate", "rhythm", "conscience", "pronunciation", "embarrass", "occurrence", "supersede", "threshold",
        "miscellaneous", "conscientious", "recommendation", "bureaucracy", "entrepreneur", "exaggerate", "maintenance"
    ]
    def __init__(self, screen, font):
        super().__init__(screen, font)
        self.word = random.choice(self.WORDS)
        self.user_input = ""

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.user_input = self.user_input[:-1]
            elif event.key == pygame.K_RETURN:
                self.result = (self.user_input.strip().lower() == self.word.lower())
            elif len(event.unicode) == 1 and event.unicode.isalpha():
                self.user_input += event.unicode

    def draw(self, time_left):
        self.screen.fill(DARK_GRAY)
        prompt = self.font.render("Type the word:", True, WHITE)
        self.screen.blit(prompt, (BASE_WIDTH//2 - prompt.get_width()//2, 100))
        wtxt = self.font.render(self.word, True, BLUE)
        self.screen.blit(wtxt, (BASE_WIDTH//2 - wtxt.get_width()//2, 160))
        itxt = self.font.render(self.user_input, True, WHITE)
        self.screen.blit(itxt, (BASE_WIDTH//2 - itxt.get_width()//2, 240))
        timer = self.font.render(f"Time: {int(time_left)}", True, WHITE)
        self.screen.blit(timer, (BASE_WIDTH - 140, 20))

# --- Science True/False ---
class ScienceTFMiniGame(MiniGameBase):
    def __init__(self, screen, font):
        super().__init__(screen, font)
        self.trivia = fetch_trivia("science", qtype="boolean")
        self.selected = 0  # 0 = True, 1 = False

    def handle_event(self, event):
        if not self.trivia:
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.selected = 1 - self.selected
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                chosen = "True" if self.selected == 0 else "False"
                self.result = (chosen == self.trivia["correct"])

    def draw(self, time_left):
        self.screen.fill(DARK_GRAY)
        if not self.trivia:
            txt = self.font.render("Failed to load question!", True, WHITE)
            self.screen.blit(txt, (BASE_WIDTH//2 - txt.get_width()//2, BASE_HEIGHT//2 - txt.get_height()//2))
            return
        qtxt = self.font.render(self.trivia["question"], True, WHITE)
        self.screen.blit(qtxt, (BASE_WIDTH//2 - qtxt.get_width()//2, 100))
        for i, ans in enumerate(["True", "False"]):
            color = BLUE if i == self.selected else WHITE
            atxt = self.font.render(ans, True, color)
            self.screen.blit(atxt, (BASE_WIDTH//2 - atxt.get_width()//2 + (i-0.5)*200, 200))
        timer = self.font.render(f"Time: {int(time_left)}", True, WHITE)
        self.screen.blit(timer, (BASE_WIDTH - 140, 20))

# --- Geography Flag Guess (requires local flag images) ---
class GeographyFlagMiniGame(MiniGameBase):
    FLAGS = [
        ("France", "assets/flags/france.png"),
        ("Japan", "assets/flags/japan.png"),
        ("Brazil", "assets/flags/brazil.png"),
        ("Australia", "assets/flags/australia.png"),
        ("Canada", "assets/flags/canada.png"),
        ("Germany", "assets/flags/germany.png"),
        ("South Korea", "assets/flags/south_korea.png"),
    ]
    def __init__(self, screen, font):
        super().__init__(screen, font)
        self.country, self.flag_path = random.choice(self.FLAGS)
        self.flag_img = None
        try:
            self.flag_img = pygame.image.load(self.flag_path).convert_alpha()
        except Exception:
            self.flag_img = pygame.Surface((120, 80))
            self.flag_img.fill(GRAY)
        self.choices = random.sample([c for c, _ in self.FLAGS if c != self.country], 3) + [self.country]
        random.shuffle(self.choices)
        self.selected = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % 4
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % 4
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.choices[self.selected] == self.country:
                    self.result = True
                else:
                    self.result = False

    def draw(self, time_left):
        self.screen.fill(DARK_GRAY)
        prompt = self.font.render("Which country does this flag belong to?", True, WHITE)
        self.screen.blit(prompt, (BASE_WIDTH//2 - prompt.get_width()//2, 60))
        flag_img = pygame.transform.smoothscale(self.flag_img, (180, 120))
        self.screen.blit(flag_img, (BASE_WIDTH//2 - 90, 120))
        for i, choice in enumerate(self.choices):
            color = BLUE if i == self.selected else WHITE
            ctxt = self.font.render(choice, True, color)
            self.screen.blit(ctxt, (BASE_WIDTH//2 - ctxt.get_width()//2, 270 + i*50))
        timer = self.font.render(f"Time: {int(time_left)}", True, WHITE)
        self.screen.blit(timer, (BASE_WIDTH - 140, 20))

# --- Example: How to use in your main game loop ---
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT))
    font = pygame.font.SysFont("arial", 32)

    # Pick a random minigame type for demo
    minigames = [
        lambda: TriviaMiniGame(screen, font, random.choice(["history", "computers", "music", "film", "art", "politics"])),
        lambda: MathMiniGame(screen, font),
        lambda: TypingMiniGame(screen, font),
        lambda: ScienceTFMiniGame(screen, font),
        lambda: GeographyFlagMiniGame(screen, font),
    ]
    mg = random.choice(minigames)()
    result = mg.run()
    screen.fill((0, 180, 0) if result else (180, 0, 0))
    msg = font.render("Success!" if result else "Failed!", True, WHITE)
    screen.blit(msg, (BASE_WIDTH//2 - msg.get_width()//2, BASE_HEIGHT//2 - msg.get_height()//2))
    pygame.display.flip()
    pygame.time.wait(2000)
    pygame.quit()