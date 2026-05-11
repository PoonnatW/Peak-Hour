STATIONS = {
    # Board 1
    0: "Plate 7",
    1: "Plate 6",
    2: "Plate 5",
    3: "Deep Fryer 2",
    4: "Deep Fryer 1",
    5: "Frying Pan 1",
    
    # Board 2
    9: "Frying Pan 2",
    10: "Recipe Card",
    11: "Plate 1",
    12: "Plate 2",
    13: "Plate 3",
    14: "Plate 4",
    15: "Vegetable Washer",
}

LEDS = {
    "Vegetable Washer": 0, # Usually on Lid
    "Frying Pan 1": 0,     # Base Light 1
    "Frying Pan 2": 1,     # Base Light 2
    "Deep Fryer 1": 2,     # Placeholder
    "Deep Fryer 2": 3      # Placeholder
}

# Values for ice cream station analog matching
ICE_CREAM_MIN = 1000
ICE_CREAM_MAX = 3000

# Required counts per ingredient for generic operations
THRESHOLDS = {
    # Frying pan (tosses)
    "Salmon":       {"spins": 0, "tosses": 2, "presses": 0},
    "Beef Steak":   {"spins": 0, "tosses": 2, "presses": 0},
    "Chicken":      {"spins": 0, "tosses": 2, "presses": 0},
    # Deep fryer (presses)
    "French Fries": {"spins": 0, "tosses": 0, "presses": 3},
    "Onion Rings":  {"spins": 0, "tosses": 0, "presses": 3},
    # Vegetable washer (spins)
    "Tomato":       {"spins": 3, "tosses": 0, "presses": 0},
    "Mushroom":     {"spins": 3, "tosses": 0, "presses": 0},
    "Broccoli":     {"spins": 3, "tosses": 0, "presses": 0},
}