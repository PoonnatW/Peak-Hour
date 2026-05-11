STATIONS = {
    0: "Recipe Card",
    1: "Vegetable Washer",
    2: "Plate", 3: "Plate", 4: "Plate", 5: "Plate",
    6: "Plate", 7: "Plate", 8: "Plate",
    9: "Frying Pan 1", 10: "Frying Pan 2",
    11: "Deep Fryer 1", 12: "Deep Fryer 2",
}

LEDS = {
    "Vegetable Washer": 0,
    "Frying Pan 1": 1,
    "Frying Pan 2": 2,
    "Deep Fryer 1": 3,
    "Deep Fryer 2": 4
}

# Values for ice cream station analog matching
ICE_CREAM_MIN = 1000
ICE_CREAM_MAX = 3000

# Required counts per ingredient for generic operations
THRESHOLDS = {
    # Frying pan (tosses)
    "Salmon":       {"spins": 0, "tosses": 4, "presses": 0},
    "Beef Steak":   {"spins": 0, "tosses": 6, "presses": 0},
    "Chicken":      {"spins": 0, "tosses": 8, "presses": 0},
    # Deep fryer (presses)
    "French Fries": {"spins": 0, "tosses": 0, "presses": 16},
    "Onion Rings":  {"spins": 0, "tosses": 0, "presses": 8},
    # Vegetable washer (spins)
    "Tomato":       {"spins": 3, "tosses": 0, "presses": 0},
    "Mushroom":     {"spins": 6, "tosses": 0, "presses": 0},
    "Broccoli":     {"spins": 9, "tosses": 0, "presses": 0},
}