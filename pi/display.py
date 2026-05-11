import pygame
import os
import time
import math

class DisplayService:
    def __init__(self, width=800, height=480):
        # Initialize Pygame and Mixer
        pygame.init()
        try:
            pygame.mixer.init()
        except:
            print("[AUDIO] Warning: Could not initialize mixer.")
            
        self.width = width
        self.height = height
        
        # UI Selection: Modern Pi (DRM/KMS) or Desktop (X11/Wayland)
        drivers = ['x11', 'wayland', 'kmsdrm', 'fbcon']
        success = False
        
        for driver in drivers:
            try:
                if not os.environ.get('DISPLAY') and driver in ['x11', 'wayland']:
                    continue
                os.environ['SDL_VIDEODRIVER'] = driver
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF | pygame.HWSURFACE)
                print(f"[DISPLAY] Successfully initialized using {driver} driver.")
                success = True
                break
            except Exception as e:
                print(f"[DISPLAY] {driver} driver failed: {e}")
        
        if not success:
            print("[DISPLAY] All drivers failed. Attempting final emergency fallback...")
            if 'SDL_VIDEODRIVER' in os.environ: del os.environ['SDL_VIDEODRIVER']
            # Try a smaller resolution for fallback
            self.width, self.height = 640, 480
            self.screen = pygame.display.set_mode((self.width, self.height))
            
        pygame.display.set_caption("PEAK HOUR | EXECUTIVE CHEF")
        
        # --- CLASSIC LIGHT DESIGN TOKENS ---
        self.CLR_BG = (255, 255, 255)          # Pure White
        self.CLR_PANEL = (225, 225, 230)       # Light Gray
        self.CLR_ACCENT = (0, 102, 204)        # Professional Blue
        self.CLR_SUCCESS = (0, 150, 0)         # Forest Green
        self.CLR_DANGER = (200, 0, 0)          # Solid Red
        self.CLR_TEXT = (20, 20, 20)           # Deep Black
        self.CLR_TEXT_DIM = (80, 80, 80)       # Dim Gray
        
        # Debug Button Rects (Repositioned for 800x480)
        btn_y = self.height - 70
        btn_w, btn_h = 160, 45
        self.debug_btn_rect = pygame.Rect(self.width // 2 - 80, self.height - 130, 160, 40)
        self.btn_spin = pygame.Rect(30, btn_y, btn_w, btn_h)
        self.btn_toss = pygame.Rect(220, btn_y, btn_w, btn_h)
        self.btn_press = pygame.Rect(410, btn_y, btn_w, btn_h)
        self.btn_bell = pygame.Rect(600, btn_y, btn_w + 10, btn_h)
        
        # Fonts
        try:
            self.font_title = pygame.font.SysFont("Arial", 72, bold=True)
            self.font_main = pygame.font.SysFont("Arial", 36, bold=True)
            self.font_sub = pygame.font.SysFont("Arial", 22)
            self.font_timer = pygame.font.SysFont("monospace", 90, bold=True)
        except:
            self.font_title = pygame.font.Font(None, 80)
            self.font_main = pygame.font.Font(None, 40)
            self.font_sub = pygame.font.Font(None, 24)
            self.font_timer = pygame.font.Font(None, 100)
            
        self.assets = {}
        self.load_assets()
        
        self.current_recipe = "None"
        self.ingredients = []
        self.start_time = time.time()
        
    def load_assets(self):
        asset_dir = os.path.join(os.path.dirname(__file__), "assets")
        if os.path.exists(asset_dir):
            for file in os.listdir(asset_dir):
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    name = os.path.splitext(file)[0]
                    try:
                        img = pygame.image.load(os.path.join(asset_dir, file)).convert_alpha()
                        img = pygame.transform.smoothscale(img, (140, 140))
                        self.assets[name] = img
                    except Exception as e:
                        print(f"[DISPLAY] Failed to load {file}: {e}")

    def draw_glass_panel(self, rect, color, border_color=None, alpha=180):
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, alpha), (0, 0, rect.width, rect.height), border_radius=15)
        if border_color:
            pygame.draw.rect(s, border_color, (0, 0, rect.width, rect.height), width=2, border_radius=15)
        self.screen.blit(s, (rect.x, rect.y))

    def update(self, state, elapsed, piece_data=None):
        pygame.event.pump()
        self.piece_data = piece_data or [] # Store progress data
        
        # Animated Background
        # Fill background
        self.screen.fill(self.CLR_BG)
        # Grid removed for "All White" look
        
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
            self.draw_result("SHIFT COMPLETE", self.CLR_SUCCESS)
        elif state == "lose":
            self.draw_result("RESTAURANT CLOSED", self.CLR_DANGER)
            
        pygame.display.flip()

    def draw_idle(self):
        self.render_text("PEAK HOUR", self.height // 2 - 40, size="title", color=self.CLR_ACCENT)
        # Pulsing subtitle
        alpha = int(155 + 100 * math.sin(time.time() * 4))
        self.render_text("SCAN RECIPE CARD TO START", self.height // 2 + 50, size="main", color=(alpha, alpha, alpha))
        
        # Debug Start
        self.draw_glass_panel(self.debug_btn_rect, self.CLR_PANEL, self.CLR_ACCENT)
        self.render_text("DEBUG START", self.debug_btn_rect.centery, x=self.debug_btn_rect.centerx, size="sub", color=self.CLR_ACCENT)

    def draw_showcase(self):
        # Header Panel
        header_rect = pygame.Rect(50, 30, self.width - 100, 100)
        self.draw_glass_panel(header_rect, self.CLR_PANEL, self.CLR_ACCENT)
        self.render_text("NEW ORDER RECEIVED", 60, size="sub", color=self.CLR_TEXT_DIM)
        self.render_text(self.current_recipe.upper(), 100, size="main", color=self.CLR_TEXT)
        
        # Ingredient Cards
        for i, ing in enumerate(self.ingredients):
            x = 100 + (i % 4) * 180
            y = 160 + (i // 4) * 180
            card_rect = pygame.Rect(x - 70, y - 10, 140, 140)
            self.draw_glass_panel(card_rect, self.CLR_PANEL)
            
            if ing in self.assets:
                self.screen.blit(self.assets[ing], (x - 70, y - 20))
            self.render_text(ing, y + 140, x, size="sub", color=self.CLR_ACCENT)

    def draw_countdown(self, elapsed):
        count = 3 - int(elapsed)
        if count > 0:
            scale = 1.0 + (elapsed % 1.0)
            self.render_text(str(count), self.height // 2, size="title", color=self.CLR_DANGER)
        else:
            self.render_text("COOK!", self.height // 2, size="title", color=self.CLR_SUCCESS)

    def draw_game(self, elapsed):
        remaining = max(0, 480 - elapsed)
        minutes, seconds = int(remaining // 60), int(remaining % 60)
        
        # Large Timer Center
        time_str = f"{minutes:02d}:{seconds:02d}"
        t_color = self.CLR_DANGER if remaining < 60 else self.CLR_TEXT
        self.render_text(time_str, self.height // 2, size="timer", color=t_color)
        
        # Mini Inventory (Top)
        inv_rect = pygame.Rect(20, 20, self.width - 40, 100)
        self.draw_glass_panel(inv_rect, self.CLR_PANEL, alpha=100)
        
        for i, piece in enumerate(self.piece_data):
            ing = piece['name']
            x_pos = 60 + i * 110
            if ing in self.assets:
                small = pygame.transform.smoothscale(self.assets[ing], (50, 50))
                self.screen.blit(small, (x_pos - 25, 30))
            
            # Show counts
            ops = []
            if piece['spins'] > 0: ops.append(f"S:{piece['spins']}")
            if piece['tosses'] > 0: ops.append(f"T:{piece['tosses']}")
            if piece['presses'] > 0: ops.append(f"P:{piece['presses']}")
            
            status_str = " ".join(ops) if ops else "WAITING"
            self.render_text(status_str, 90, x=x_pos, size="sub", color=self.CLR_TEXT)

        # Bottom Bar
        bar_rect = pygame.Rect(0, self.height - 100, self.width, 100)
        self.draw_glass_panel(bar_rect, self.CLR_BG, alpha=200)
        self.render_text(f"CURRENT TASK: {self.current_recipe}", self.height - 115, size="sub", color=self.CLR_ACCENT)

        # Action Labels (Debug)
        self.draw_action(self.btn_spin, "SPIN [S]", self.CLR_ACCENT)
        self.draw_action(self.btn_toss, "TOSS [T]", (255, 165, 0))
        self.draw_action(self.btn_press, "PRESS [P]", self.CLR_DANGER)
        self.draw_action(self.btn_bell, "SERVICE! [B]", self.CLR_SUCCESS)

    def draw_action(self, rect, text, color):
        self.draw_glass_panel(rect, self.CLR_PANEL, color, alpha=255)
        self.render_text(text, rect.centery, x=rect.centerx, size="sub", color=self.CLR_TEXT)

    def draw_checking(self):
        self.screen.fill(self.CLR_PANEL)
        self.render_text("VERIFYING INGREDIENTS...", self.height // 2, size="main", color=self.CLR_ACCENT)

    def draw_result(self, text, color):
        self.screen.fill(self.CLR_BG)
        # Shadow effect
        self.render_text(text, self.height // 2 + 4, size="title", color=(20, 20, 20))
        self.render_text(text, self.height // 2, size="title", color=color)

    def render_text(self, text, y, x=None, size="main", color=(255, 255, 255)):
        if x is None: x = self.width // 2
        font = self.font_title if size == "title" else self.font_timer if size == "timer" else self.font_sub if size == "sub" else self.font_main
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(x, y))
        self.screen.blit(surf, rect)

    def show_recipe(self, recipe_name, required_ingredients):
        self.current_recipe = recipe_name
        self.ingredients = required_ingredients

    def show_error(self, message):
        print(f"[DISPLAY] ERROR: {message}")

    def play_sound(self, sound_type):
        sound_files = {"countdown": "countdown.wav", "alarm": "alarm.wav", "bell": "bell.ding.wav", "win": "correct.wav", "error": "wrong.wav"}
        if sound_type in sound_files:
            path = os.path.join(os.path.dirname(__file__), "assets", sound_files[sound_type])
            if os.path.exists(path):
                try: pygame.mixer.Sound(path).play()
                except: pass