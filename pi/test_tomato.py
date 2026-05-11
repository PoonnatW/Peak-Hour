import pygame
import os
import sys
import time

def test_tomato():
    print("Starting Tomato Display Test...")
    
    # pygame initialization
    pygame.init()
    
    # 3.5" TFT resolution is typically 480x320
    size = (480, 320)
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("Tomato Test")
    
    # Fill background with white
    screen.fill((255, 255, 255))
    
    # Try to load the tomato image
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(base_dir, "assets", "Tomato.png")
    
    if os.path.exists(img_path):
        try:
            tomato = pygame.image.load(img_path)
            # Scale to fit nicely
            tomato = pygame.transform.smoothscale(tomato, (200, 200))
            screen.blit(tomato, (size[0]//2 - 100, size[1]//2 - 120))
            print(f"Loaded {img_path} successfully!")
        except Exception as e:
            print(f"Error loading image: {e}")
    else:
        # Draw a red circle if image missing
        pygame.draw.circle(screen, (255, 0, 0), (size[0]//2, size[1]//2 - 20), 80)
        print("Tomato.png not found, drawing a red circle instead.")

    # Add some text
    font = pygame.font.SysFont("Arial", 30, bold=True)
    text = font.render("TFT TEST: TOMATO", True, (0, 0, 0))
    screen.blit(text, (size[0]//2 - text.get_width()//2, size[1] - 80))
    
    pygame.display.flip()
    print("Tomato should be visible on screen now! Waiting 10 seconds...")
    
    time.sleep(10)
    pygame.quit()

if __name__ == "__main__":
    test_tomato()
