import pygame
import time
import sys
from display import DisplayService

def preview():
    print("Starting UI Preview...")
    # Initialize display with windowed mode for Mac
    display = DisplayService()
    
    # Mock some data
    recipe_name = "Mega Burger"
    ingredients = ["Beef Steak", "Tomato", "Mushroom", "Broccoli"]
    display.show_recipe(recipe_name, ingredients)
    
    states = [
        ("idle", 0),
        ("recipe_scanned", 1),
        ("showcase", 5),
        ("countdown", 3),
        ("playing", 10), # Will show 10 seconds of timer
        ("checking", 2),
        ("win", 3),
        ("lose", 3)
    ]
    
    try:
        for state, duration in states:
            print(f"Previewing state: {state}")
            start_time = time.time()
            while time.time() - start_time < duration:
                elapsed = time.time() - start_time
                
                # Special handling for 'playing' to show timer counting
                if state == "playing":
                    # Simulate some elapsed time into an 8-minute game
                    display.update(state, 400 + elapsed) # Near the end for red background
                else:
                    display.update(state, elapsed)
                    
                time.sleep(0.05)
                
                # Check for window close
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                        
        print("Preview finished.")
        pygame.quit()
        
    except KeyboardInterrupt:
        pygame.quit()

if __name__ == "__main__":
    preview()
