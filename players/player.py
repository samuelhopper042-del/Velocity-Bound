
import pygame
from settings import PLAYER_WIDTH, PLAYER_HEIGHT


class Player:
    def __init__(self, x, y, color, character_name=None):
        # Rect and visual
        self.rect = pygame.Rect(int(x), int(y), PLAYER_WIDTH, PLAYER_HEIGHT)
        self.color = color
        self.character_name = character_name
        self.is_grounded = False
        self.walk_timer = 0.0
        self.vx = 0.0

        # Precise float positions (rect uses ints for drawing/collision)
        self.x = float(x)
        self.y = float(y)

        # Movement
        # Number of mid-air jumps remaining
        self.jumps_left = 2
        # Facing direction: 1 == right, -1 == left
        self.facing = 1

        # Combat / stats
        self.damage = 0
        self.stocks = 3

        # Action state (frame counters and flags)
        # `attack_frames` counts remaining frames for an active attack
        self.attack_frames = 0
        # `attack_cooldown` prevents rapid repeat use of strong moves
        self.attack_cooldown = 0
        # `has_hit` ensures single-hit-per-attack behavior
        self.has_hit = False
        # `hitstun` frames during which player cannot act
        self.hitstun = 0
        # `invincible_frames` frames of post-respawn invulnerability
        self.invincible_frames = 0

        # Spin / slam effects from vertical launch attacks
        # `is_spinning` + `spin_frames` control a visual spin animation
        self.is_spinning = False
        self.spin_frames = 0
        # `spin_angle` stores the current rendered rotation for the player
        self.spin_angle = 0.0
        # Slam state: when True, a ground collision will trigger particles / impact
        self.slam_ready = False
        self.slam_strength = 0.0
        # Particle list for ground-slam dust effects (list of dicts)
        self.slam_particles = []
        # Prone state: when True the player is lying on their stomach
        # Pressing the jump key will make them hop upright.
        self.prone = False

        # Shield
        self.is_shielding = False
        self.shield_hp = 100.0
        self.shield_stun = 0

        # Ledge / recovery
        # `is_hanging` indicates a ledge-grab state
        self.is_hanging = False
        # `ledge_cooldown` prevents immediate re-grab after release
        self.ledge_cooldown = 0
        # Which side the player is hanging on ('left'|'right'|None)
        self.hang_side = None
        # pymunk physics body and shape for movement/collision
        self.body = None
        self.shape = None

    def reset_position(self, x, y):
        # Reset the player's physical state for respawn and positioning.
        self.x = float(x)
        self.y = float(y)
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        self.attack_cooldown = 0
        self.is_spinning = False
        self.spin_frames = 0
        self.spin_angle = 0.0
        self.slam_ready = False
        self.slam_strength = 0.0
        self.slam_particles = []
        self.walk_timer = 0.0
        self.vx = 0.0
        self.is_grounded = False
        self.is_hanging = False
        self.hang_side = None
        self.jumps_left = 2
        self.prone = False
        self.sprite_index = 0.0
        self.sprite_anim_speed = 0.15

    def set_vertical_velocity(self, vy):
        if getattr(self, 'body', None):
            self.body.velocity = (self.body.velocity.x, vy)

    def set_horizontal_velocity(self, vx):
        if getattr(self, 'body', None):
            self.body.velocity = (vx, self.body.velocity.y)
