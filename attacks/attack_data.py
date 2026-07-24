# Attack definitions are stored in data so behavior can be tuned without
# changing engine code. Each attack defines its timing, damage, knockback,
# and hitbox geometry.
DEFAULT_ATTACKS = {
    "jab": {
        "name": "Jab",
        "damage": 8,
        "startup": 3,
        "duration": 10,
        "knockback": 6,
        # Hitbox is offset from the player body: x is horizontal offset, y is vertical.
        "hitbox": {"width": 40, "height": 30, "offset_x": 45, "offset_y": 10},
    },
    "uppercut": {
        "name": "Uppercut",
        "damage": 16,
        "startup": 8,
        "duration": 14,
        "knockback": 12,
        "vertical_launch": True,
        "cooldown": 45,
        "hitbox": {"width": 30, "height": 60, "offset_x": 25, "offset_y": -25},
    },
}
