# High-level game configuration stored in a data file.
# This can be used for default stage settings, player spawns, and control layout.
GAME_CONFIG = {
    "stage": {
        "width": 800,
        "height": 50,
        "x": 240,
        "y": 500,
        "color": [100, 100, 100],
    },
    "players": {
        "p1": {
            "start_x": 350,
            "start_y": 250,
            "color": [0, 100, 255],
        },
        "p2": {
            "start_x": 880,
            "start_y": 250,
            "color": [255, 50, 50],
        },
    },
    "controls": {
        "p1": {
            "left": "A",
            "right": "D",
            "jump": "W",
            "shield": "S",
            "attack_jab": "F",
            "attack_uppercut": "G",
        },
        
        "p2": {
            "left": "J",
            "right": "L",
            "jump": "I",
            "shield": "K",
            "attack_jab": "H",
            "attack_uppercut": "U",
            
        },
    },
}
