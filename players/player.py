
import pygame
import pymunk
import math
from settings import MAX_SHIELD_HP, PLAYER_WIDTH, PLAYER_HEIGHT

CHAR_GROUP = 1
PLATFORM_CATEGORY = 0b01
PLAYER_CATEGORY = 0b10
ragdoll_filter = pymunk.ShapeFilter(
    group=CHAR_GROUP,
    categories=PLAYER_CATEGORY,
    mask=PLATFORM_CATEGORY,
)


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
        self.kb_x = 0.0
        self.kb_y = 0.0

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
        self.shield_hp = float(MAX_SHIELD_HP)
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

        # Animation / sprite state
        self.sprite_frames = []
        self.sprite_index = 0.0
        self.sprite_anim_speed = 0.15

        self.torso_width = 20
        self.torso_height = 65
        self.head_radius = 16
        self.limb_default_angles = {}

        # Ragdoll limb body/joint state.
        self.head_body = None
        self.head_shape = None
        self.limb_bodies = {}
        self.limb_shapes = {}
        self.limb_motors = {}
        self.limb_attach = {}
        self.limb_lengths = {}
        self.limb_target_angles = {}

    def update_limb_sim(self, move_input=0.0):
        if getattr(self, 'body', None) is None:
            return

        vx = self.body.velocity.x
        vy = self.body.velocity.y
        phase = self.walk_timer * 3.0
        swing = math.sin(phase)
        if abs(vx) > 0.5:
            self.walk_timer += 0.08

        if getattr(self, 'limb_motors', None):
            for name, spring in self.limb_motors.items():
                if spring is not None:
                    if 'leg' in name:
                        if move_input != 0.0:
                            spring.rest_angle = self.facing * (0.15 + 0.05 * abs(move_input)) * (1.0 if 'left' in name else -1.0)
                        else:
                            spring.rest_angle = 0.0
                    elif 'arm' in name:
                        spring.rest_angle = self.facing * 0.12 * (1.0 if 'left' in name else -1.0)

    def reset_position(self, x, y):
        # Reset the player's physical state for respawn and positioning.
        self.x = float(x)
        self.y = float(y)
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        if getattr(self, 'body', None):
            self.body.position = (self.x + self.rect.width / 2, self.y + self.rect.height / 2)
            self.body.velocity = (0.0, 0.0)
            self.body.angle = 0.0
            self.body.angular_velocity = 0.0
            for name, limb_body in self.limb_bodies.items():
                attach = self.limb_attach[name]
                pivot_pos = self.body.position + attach
                angle = self.limb_default_angles.get(name, math.pi / 2)
                direction = pymunk.Vec2d(math.cos(angle), math.sin(angle))
                limb_body.position = pivot_pos + direction * (self.limb_lengths[name] / 2)
                limb_body.angle = angle
                limb_body.velocity = (0.0, 0.0)
                limb_body.angular_velocity = 0.0
                motor = self.limb_motors.get(name)
                if motor:
                    motor.rate = 0.0
            if getattr(self, 'head_body', None):
                head_attachment_offset = pymunk.Vec2d(0, -self.torso_height / 2 - self.head_radius)
                self.head_body.position = self.body.position + head_attachment_offset
                self.head_body.angle = 0.0
                self.head_body.velocity = (0.0, 0.0)
                self.head_body.angular_velocity = 0.0
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
        self.kb_x = 0.0
        self.kb_y = 0.0
        self.shield_hp = float(MAX_SHIELD_HP)
        self.shield_stun = 0

        for name, spring in self.limb_motors.items():
            if spring is not None:
                spring.rest_angle = 0.0

    def create_body(self, space, mass=1.0):
        if self.body is not None or self.shape is not None:
            return

        torso_mass = 4.0
        torso_width = self.torso_width
        torso_height = self.torso_height
        moment = pymunk.moment_for_box(torso_mass, (torso_width, torso_height))
        body = pymunk.Body(torso_mass, moment)
        body.position = (self.x + PLAYER_WIDTH / 2, self.y + PLAYER_HEIGHT / 2)
        body.angular_damping = 0.8
        shape = pymunk.Poly.create_box(body, (torso_width, torso_height))
        shape.friction = 0.6
        shape.elasticity = 0.0
        shape.filter = ragdoll_filter
        space.add(body, shape)
        self.body = body
        self.shape = shape

        head_mass = 1.2
        head_radius = self.head_radius
        head_moment = pymunk.moment_for_circle(head_mass, 0, head_radius)
        head_body = pymunk.Body(head_mass, head_moment)
        head_body.position = (body.position.x, body.position.y - 50)
        head_body.angular_damping = 0.8
        head_shape = pymunk.Circle(head_body, head_radius)
        head_shape.friction = 0.6
        head_shape.filter = ragdoll_filter
        space.add(head_body, head_shape)
        self.head_body = head_body
        self.head_shape = head_shape

        space.add(pymunk.PivotJoint(body, head_body, (0, -32), (0, 16)))

        def add_capsule_part(mass, size, start_pos, name):
            w, h = size
            moment = pymunk.moment_for_box(mass, (w, h))
            limb_body = pymunk.Body(mass, moment)
            limb_body.position = start_pos
            limb_shape = pymunk.Poly.create_box(limb_body, (w, h))
            limb_shape.friction = 0.6
            limb_shape.filter = ragdoll_filter
            space.add(limb_body, limb_shape)
            self.limb_bodies[name] = limb_body
            self.limb_shapes[name] = limb_shape
            self.limb_attach[name] = pymunk.Vec2d(0, 0)
            self.limb_lengths[name] = float(h)
            self.limb_default_angles[name] = 0.0
            self.limb_target_angles[name] = 0.0
            return limb_body

        l_thigh_body = add_capsule_part(1.2, (12, 40), (body.position.x - 10, body.position.y + 45), 'left_leg')
        r_thigh_body = add_capsule_part(1.2, (12, 40), (body.position.x + 10, body.position.y + 45), 'right_leg')
        l_calf_body = add_capsule_part(1.0, (10, 40), (body.position.x - 10, body.position.y + 85), 'left_calf')
        r_calf_body = add_capsule_part(1.0, (10, 40), (body.position.x + 10, body.position.y + 85), 'right_calf')
        l_bicep_body = add_capsule_part(1.0, (10, 35), (body.position.x - 18, body.position.y - 10), 'left_arm')
        r_bicep_body = add_capsule_part(1.0, (10, 35), (body.position.x + 18, body.position.y - 10), 'right_arm')
        l_forearm_body = add_capsule_part(0.8, (8, 35), (body.position.x - 18, body.position.y + 25), 'left_forearm')
        r_forearm_body = add_capsule_part(0.8, (8, 35), (body.position.x + 18, body.position.y + 25), 'right_forearm')

        space.add(pymunk.PivotJoint(body, l_thigh_body, (-8, 32), (0, -20)))
        space.add(pymunk.PivotJoint(body, r_thigh_body, (8, 32), (0, -20)))
        space.add(pymunk.PivotJoint(l_thigh_body, l_calf_body, (0, 20), (0, -20)))
        space.add(pymunk.PivotJoint(r_thigh_body, r_calf_body, (0, 20), (0, -20)))
        space.add(pymunk.PivotJoint(body, l_bicep_body, (-12, -20), (0, -17)))
        space.add(pymunk.PivotJoint(body, r_bicep_body, (12, -20), (0, -17)))
        space.add(pymunk.PivotJoint(l_bicep_body, l_forearm_body, (0, 17), (0, -17)))
        space.add(pymunk.PivotJoint(r_bicep_body, r_forearm_body, (0, 17), (0, -17)))

        def add_muscle(body_a, body_b, stiffness=5000, damping=450):
            spring = pymunk.DampedRotarySpring(body_a, body_b, rest_angle=0.0, stiffness=stiffness, damping=damping)
            space.add(spring)
            return spring

        self.limb_motors['head'] = add_muscle(body, head_body, 12000, 800)
        self.limb_motors['left_leg'] = add_muscle(body, l_thigh_body, 6000, 500)
        self.limb_motors['right_leg'] = add_muscle(body, r_thigh_body, 6000, 500)
        self.limb_motors['left_calf'] = add_muscle(l_thigh_body, l_calf_body, 4000, 350)
        self.limb_motors['right_calf'] = add_muscle(r_thigh_body, r_calf_body, 4000, 350)
        self.limb_motors['left_arm'] = add_muscle(body, l_bicep_body, 3000, 250)
        self.limb_motors['right_arm'] = add_muscle(body, r_bicep_body, 3000, 250)
        self.limb_motors['left_forearm'] = add_muscle(l_bicep_body, l_forearm_body, 2000, 200)
        self.limb_motors['right_forearm'] = add_muscle(r_bicep_body, r_forearm_body, 2000, 200)

        self.body = body
        self.shape = shape

    def sync_rect_to_body(self):
        if getattr(self, 'body', None):
            self.x, self.y = self.body.position
            self.rect.x = int(self.x - self.rect.width / 2)
            self.rect.y = int(self.y - self.rect.height / 2)

    def set_vertical_velocity(self, vy):
        if getattr(self, 'body', None):
            self.body.velocity = (self.body.velocity.x, vy)

    def set_horizontal_velocity(self, vx):
        if getattr(self, 'body', None):
            self.body.velocity = (vx, self.body.velocity.y)

    def apply_knockback(self, vx, vy):
        if getattr(self, 'body', None):
            self.body.velocity = (vx, vy)
        self.kb_x = float(vx)
        self.kb_y = float(vy)

    def is_airborne(self):
        if getattr(self, 'body', None):
            return abs(self.body.velocity.y) > 0.1
        return False
