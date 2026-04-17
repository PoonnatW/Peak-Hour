STATIONS = {
    0: "Plate 1",
    1: "Plate 2",
    2: "Plate 3",
    3: "Plate 4",
    4: "Plate 5",
    5: "Plate 6",
    6: "Plate 7",
    7: "Vegetable Washer",
    9: "Frying Pan 1",
    10: "Frying Pan 2",
    11: "Deep Fryer 1",
    12: "Deep Fryer 2"
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
    "Potato": {"spins": 5, "tosses": 0, "presses": 3},
    "Tomato": {"spins": 3, "tosses": 0, "presses": 0},
    "Lettuce": {"spins": 2, "tosses": 0, "presses": 0},
    "Carrot": {"spins": 4, "tosses": 0, "presses": 0},
    "Beef Patty": {"spins": 0, "tosses": 5, "presses": 0},
    "Bun": {"spins": 0, "tosses": 2, "presses": 0}
}