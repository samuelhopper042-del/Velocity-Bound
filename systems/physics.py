from settings import *
import random


def apply_gravity(player, keys, fastfall_key, _unused=None):
    """Apply gravity to a player, respecting fast-fall and hang state.

    Gravity updates the player's vertical velocity and position each frame.
    Players do not fall while hanging on a ledge.
    """
    if not player.is_hanging:
        player.y_velocity += GRAVITY
        current_cap = FAST_FALL_SPEED if (keys[fastfall_key] and player.y_velocity > 0) else MAX_FALL_SPEED
        if player.y_velocity > current_cap:
            player.y_velocity = current_cap
        player.y += player.y_velocity
        player.rect.y = int(player.y)


def try_ledge_grab(player, stage_rect, left_ledge, right_ledge):
    """Attempt to transition the player into a ledge-hang state.

    This is a simple ledge grab mechanic: the player must overlap a small edge
    region and be moving downward. If successful, the player is moved to a fixed
    hanging position and can later jump away or drop.
    """
    MIN_FALL_VEL = 1.0
    if player.hitstun == 0 and player.ledge_cooldown == 0 and not player.is_hanging and player.y_velocity > MIN_FALL_VEL:
        hang_y = float(stage_rect.top)
        if player.rect.colliderect(left_ledge) and player.rect.bottom > left_ledge.y - 1:
            player.is_hanging = True
            player.hang_side = 'left'
            player.x = float(stage_rect.left - player.rect.width)
            player.y = hang_y
            player.y_velocity = 0.0
            player.kb_x = 0.0
            player.kb_y = 0.0
            player.jumps_left = 2
        elif player.rect.colliderect(right_ledge) and player.rect.bottom > right_ledge.y - 1:
            player.is_hanging = True
            player.hang_side = 'right'
            player.x = float(stage_rect.right)
            player.y = hang_y
            player.y_velocity = 0.0
            player.kb_x = 0.0
            player.kb_y = 0.0
            player.jumps_left = 2


def ground_collision(player, stage_rect):
    # Only land on the platform when the player is falling onto it from above.
    if player.rect.colliderect(stage_rect) and player.y_velocity >= 0:
        previous_bottom = player.y - player.y_velocity + player.rect.height
        if previous_bottom <= stage_rect.top + 5:
            player.rect.bottom = stage_rect.top
            player.y = float(player.rect.y)
            player.y_velocity = 0.0
            player.jumps_left = 2
            if getattr(player, 'slam_ready', False):
                # Trigger slam landing effects: particles + small downward impulse
                player.slam_ready = False
                player.is_spinning = False
                player.spin_frames = 0
                player.kb_y = float(player.slam_strength * 0.5)
                # spawn a few dust particles at the feet
                particles = []
                for i in range(8):
                    vx = (i - 4) * 0.6 + (random.random() - 0.5) * 1.2
                    vy = - (1.0 + random.random() * 2.0)
                    particles.append({
                        "x": float(player.rect.centerx + (i - 4) * 4),
                        "y": float(player.rect.bottom),
                        "vx": vx,
                        "vy": vy,
                        "life": 18 + random.randint(0, 8),
                    })
                player.slam_particles = particles
                player.slam_strength = 0.0
                # Put the player into a prone (stomach) state on slam landing.
                player.prone = True
        else:
            # If the player is intersecting the stage from the side or below,
            # keep the current vertical motion and avoid snapping to the top.
            player.y = float(player.rect.y)


def interpolate_knockback(p1, p2, stage_rect):
    # Break knockback movement into smaller steps so players do not pass
    # through the stage or through each other during a single fast frame.
    max_step = max(1, int(max(abs(p1.kb_x), abs(p1.kb_y), abs(p2.kb_x), abs(p2.kb_y))))
    if max_step > 20:
        max_step = 20
    for _ in range(max_step):
        p1.x += p1.kb_x / max_step
        p1.y += p1.kb_y / max_step
        p2.x += p2.kb_x / max_step
        p2.y += p2.kb_y / max_step
        p1.rect.x, p1.rect.y = int(p1.x), int(p1.y)
        p2.rect.x, p2.rect.y = int(p2.x), int(p2.y)

        # If a player hits the stage from above, stop their vertical knockback.
        if p1.rect.colliderect(stage_rect) and p1.kb_y >= 0:
            if p1.rect.bottom - (p1.kb_y / max_step) <= stage_rect.top + 10:
                p1.rect.bottom = stage_rect.top
                p1.y = float(p1.rect.y)
                p1.kb_y = 0.0

        if p2.rect.colliderect(stage_rect) and p2.kb_y >= 0:
            if p2.rect.bottom - (p2.kb_y / max_step) <= stage_rect.top + 10:
                p2.rect.bottom = stage_rect.top
                p2.y = float(p2.rect.y)
                p2.kb_y = 0.0


def apply_knockback_decay(player):
    player.kb_x *= KNOCKBACK_DECAY
    player.kb_y *= KNOCKBACK_DECAY
    if abs(player.kb_x) < 0.1:
        player.kb_x = 0.0
    if abs(player.kb_y) < 0.1:
        player.kb_y = 0.0


def resolve_solid_collision(p1, p2):
    # Basic player collision resolution pushes players apart when they overlap.
    # This only runs when neither player is hanging on a ledge.
    if p1.rect.colliderect(p2.rect) and not p1.is_hanging and not p2.is_hanging:
        overlap_left = p1.rect.right - p2.rect.left
        overlap_right = p2.rect.right - p1.rect.left
        if overlap_left < overlap_right:
            push = overlap_left // 2
            p1.x -= push
            p2.x += push
            if p1.kb_x > 0:
                p1.kb_x = 0.0
            if p2.kb_x < 0:
                p2.kb_x = 0.0
        else:
            push = overlap_right // 2
            p1.x += push
            p2.x -= push
            if p1.kb_x < 0:
                p1.kb_x = 0.0
            if p2.kb_x > 0:
                p2.kb_x = 0.0
