import pygame
import os
import time

class DisplayService:
    def __init__(self, width=480, height=320):
        # Initialize Pygame and Mixer
        pygame.init()
        try:
            pygame.mixer.init()
        except:
            print("[AUDIO] Warning: Could not initialize mixer. Audio will be disabled.")
            
        self.width = width
        self.height = height
        
        # Try to use framebuffer if on Pi, otherwise normal window
        # For 3.5" TFTs, you may need to set: export SDL_FBDEV=/dev/fb1
        try:
            # Check if we are running in a terminal without X11
            if not os.environ.get('DISPLAY'):
                os.environ['SDL_VIDEODRIVER'] = 'fbcon'
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
        except:
            print("[DISPLAY] Falling back to windowed mode.")
            self.screen = pygame.display.set_mode((self.width, self.height))
            
        pygame.display.set_caption("Peak Hour Game")
        
        # UI Colors
        self.COLOR_WHITE = (250, 250, 250)
        self.COLOR_BLACK = (20, 20, 20)
        self.COLOR_ACCENT = (0, 150, 255)
        self.COLOR_RED = (220, 50, 50)
        self.COLOR_GREEN = (50, 200, 100)
        
        # Debug Button Rects
        self.debug_btn_rect = pygame.Rect(self.width // 2 - 80, self.height - 60, 160, 40)
        self.btn_spin = pygame.Rect(10, self.height - 90, 100, 40)
        self.btn_toss = pygame.Rect(120, self.height - 90, 100, 40)
        self.btn_press = pygame.Rect(230, self.height - 90, 100, 40)
        self.btn_bell = pygame.Rect(340, self.height - 90, 130, 40)
        
        # Fonts
        try:
            self.font_title = pygame.font.SysFont("Arial", 42, bold=True)
            self.font_main = pygame.font.SysFont("Arial", 30, bold=True)
            self.font_sub = pygame.font.SysFont("Arial", 20)
        except:
            self.font_title = pygame.font.Font(None, 50)
            self.font_main = pygame.font.Font(None, 36)
            self.font_sub = pygame.font.Font(None, 24)
            
        self.assets = {}
        self.load_assets()
        
        self.current_recipe = "None"
        self.ingredients = []
        
    def load_assets(self):
        asset_dir = os.path.join(os.path.dirname(__file__), "assets")
        if os.path.exists(asset_dir):
            for file in os.listdir(asset_dir):
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    name = os.path.splitext(file)[0]
                    try:
                        img = pygame.image.load(os.path.join(asset_dir, file)).convert_alpha()
                        # Standardize ingredient size
                        img = pygame.transform.smoothscale(img, (100, 100))
                        self.assets[name] = img
                    except Exception as e:
                        print(f"[DISPLAY] Failed to load {file}: {e}")

    def update(self, state, elapsed):
        # Keep window events processing
        pygame.event.pump()
        
        # Background
        self.screen.fill(self.COLOR_WHITE)
        
        if state == "idle":
            self.draw_idle()
        elif state == "recipe_scanned" or state == "showcase":
            self.draw_showcase()
        elif state == "countdown":
            self.draw_countdown(elapsed)
        elif state == "playing":
            self.draw_game(elapsed)
        elif state == "checking":
            self.draw_checking()
        elif state == "win":
            self.draw_result("SUCCESS!", self.COLOR_GREEN)
        elif state == "lose":
            self.draw_result("FAILED", self.COLOR_RED)
            
        pygame.display.flip()

    def draw_idle(self):
        # Draw a subtle pulsing background or logo here
        self.render_text("PEAK HOUR", self.height // 2 - 30, size="title", color=self.COLOR_BLACK)
        self.render_text("Scan Recipe Card to Start", self.height // 2 + 30, size="main", color=self.COLOR_ACCENT)
        
        # Draw Debug Button
        pygame.draw.rect(self.screen, self.COLOR_BLACK, self.debug_btn_rect, border_radius=10)
        self.render_text("DEBUG START", self.debug_btn_rect.centery, x=self.debug_btn_rect.centerx, size="sub", color=self.COLOR_WHITE)

    def draw_showcase(self):
        self.render_text("ORDER UP!", 35, size="title", color=self.COLOR_BLACK)
        self.render_text(self.current_recipe, 75, size="main", color=self.COLOR_ACCENT)
        
        # Display ingredients in a grid
        for i, ing in enumerate(self.ingredients):
            x = 80 + (i % 4) * 110
            y = 120 + (i // 4) * 120
            if ing in self.assets:
                self.screen.blit(self.assets[ing], (x - 50, y - 50))
            self.render_text(ing, y + 60, x, size="sub", color=self.COLOR_BLACK)

    def draw_countdown(self, elapsed):
        count = 3 - int(elapsed)
        if count > 0:
            # Pulsing effect
            pulse = 1.0 + 0.2 * (elapsed % 1.0)
            size = int(100 * pulse)
            font = pygame.font.SysFont("Arial", size, bold=True)
            self.render_text(str(count), self.height // 2, font=font, color=self.COLOR_RED)
        else:
            self.render_text("START!", self.height // 2, size="title", color=self.COLOR_GREEN)

    def draw_game(self, elapsed):
        remaining = 480 - elapsed
        if remaining < 0: remaining = 0
        
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        
        # Background gets redder as time runs out
        danger = 1.0 - (remaining / 480)
        bg_color = (255, 255 - int(100 * danger), 255 - int(100 * danger))
        self.screen.fill(bg_color)
        
        # Timer
        time_str = f"{minutes:02d}:{seconds:02d}"
        color = self.COLOR_RED if remaining < 60 else self.COLOR_BLACK
        self.render_text(time_str, self.height // 2, size="title", color=color)
        
        # Active recipe at bottom
        pygame.draw.rect(self.screen, self.COLOR_BLACK, (0, self.height - 40, self.width, 40))
        self.render_text(f"Recipe: {self.current_recipe}", self.height - 20, color=self.COLOR_WHITE, size="sub")
        
        # Debug Action Buttons
        self.draw_debug_action(self.btn_spin, "SPIN (S)", self.COLOR_ACCENT)
        self.draw_debug_action(self.btn_toss, "TOSS (T)", (255, 165, 0))
        self.draw_debug_action(self.btn_press, "PRESS (P)", self.COLOR_RED)
        self.draw_debug_action(self.btn_bell, "RING BELL (B)", self.COLOR_GREEN)

    def draw_debug_action(self, rect, text, color):
        pygame.draw.rect(self.screen, color, rect, border_radius=5)
        self.render_text(text, rect.centery, x=rect.centerx, size="sub", color=self.COLOR_WHITE)

    def draw_checking(self):
        self.screen.fill(self.COLOR_ACCENT)
        self.render_text("CHECKING...", self.height // 2, size="title", color=self.COLOR_WHITE)

    def draw_result(self, text, color):
        self.screen.fill(color)
        self.render_text(text, self.height // 2, size="title", color=self.COLOR_WHITE)

    def render_text(self, text, y, x=None, size="main", color=(0, 0, 0), font=None):
        if x is None: x = self.width // 2
        if font is None:
            if size == "title": font = self.font_title
            elif size == "sub": font = self.font_sub
            else: font = self.font_main
            
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(x, y))
        self.screen.blit(surf, rect)

    def show_recipe(self, recipe_name, required_ingredients):
        self.current_recipe = recipe_name
        self.ingredients = required_ingredients

    def show_win(self):
        pass

    def show_error(self, message):
        print(f"[DISPLAY] ERROR: {message}")

    def play_sound(self, sound_type):
        # We handle sound types as per workplan
        sound_files = {
            "countdown": "countdown.wav",
            "alarm": "alarm.wav",
            "bell": "bell.ding.wav",
            "win": "correct.wav",
            "error": "wrong.wav"
        }
        
        if sound_type in sound_files:
            path = os.path.join(os.path.dirname(__file__), "assets", sound_files[sound_type])
            if os.path.exists(path):
                try:
                    pygame.mixer.Sound(path).play()
                except:
                    pass
            else:
                print(f"[AUDIO] Sound file not found: {path}")

    def show_win(self):
        pass