import pygame
from settings import *


# Combat system: handles attack lifecycles, hit detection, DI, and basic shield/movement rules.


def tick_attacks(p1, p2):
    """Advance attack frame counters and produce hitbox rects for active attacks.

    This function consumes a frame from each active attack, builds the
    corresponding hitbox rectangle, and returns metadata for hit resolution.
    """
    p1_hitbox = None
    if p1.attack_frames > 0 and p1.current_attack:
        # consume a frame of the active attack
        p1.attack_frames -= 1
        p1_center_y = p1.rect.y + (p1.rect.height // 2)
        width = p1.current_attack["hitbox"]["width"]
        height = p1.current_attack["hitbox"]["height"]
        offset_x = p1.current_attack["hitbox"]["offset_x"]
        offset_y = p1.current_attack["hitbox"]["offset_y"]
        # small overlap so the attack hitbox touches the attacker's body
        overlap = 4
        if p1.facing == 1:
            x = p1.rect.right + offset_x - overlap
            # Ensure the hitbox at least touches the attacker's body
            if x > p1.rect.right - 1:
                x = p1.rect.right - 1
        else:
            x = p1.rect.left - offset_x - width + overlap
            # Ensure the hitbox at least touches the attacker's body
            if x + width < p1.rect.left + 1:
                x = p1.rect.left - width + 1
        p1_hitbox = pygame.Rect(x, p1_center_y + offset_y - (height // 2), width, height)

    p2_hitbox = None
    if p2.attack_frames > 0 and p2.current_attack:
        p2.attack_frames -= 1
        p2_center_y = p2.rect.y + (p2.rect.height // 2)
        width = p2.current_attack["hitbox"]["width"]
        height = p2.current_attack["hitbox"]["height"]
        offset_x = p2.current_attack["hitbox"]["offset_x"]
        offset_y = p2.current_attack["hitbox"]["offset_y"]
        overlap = 4
        if p2.facing == 1:
            x = p2.rect.right + offset_x - overlap
            if x > p2.rect.right - 1:
                x = p2.rect.right - 1
        else:
            x = p2.rect.left - offset_x - width + overlap
            if x + width < p2.rect.left + 1:
                x = p2.rect.left - width + 1
        p2_hitbox = pygame.Rect(x, p2_center_y + offset_y - (height // 2), width, height)

    # Return hitboxes plus immutable references to the attack data for
    # this frame. Clearing of `current_attack` is handled by the caller
    # after hit-resolution so the attack metadata is available here.
    p1_attack_ref = p1.current_attack if getattr(p1, 'attack_frames', 0) > 0 else None
    p2_attack_ref = p2.current_attack if getattr(p2, 'attack_frames', 0) > 0 else None

    return p1_hitbox, p2_hitbox, p1_attack_ref, p2_attack_ref


def handle_hits(p1, p2, p1_hitbox, p2_hitbox, p1_attack=None, p2_attack=None):
    # When an active hitbox overlaps the opponent's body, apply damage and knockback.
    if p1_hitbox and p1_attack and p1_hitbox.colliderect(p2.rect) and not p1.has_hit and p2.invincible_frames == 0:
        # If defender was prone, getting hit should immediately bring them upright.
        if getattr(p2, 'prone', False):
            p2.prone = False
        if p2.is_shielding and p2.shield_hp > 0:
            # Shielded hit: no damage, reduced knockback, and shield HP loss.
            p2.shield_hp -= p1_attack["damage"] * 0.5
            if p2.shield_hp < 0:
                p2.shield_hp = 0
            p2.kb_x = float((p1_attack["knockback"] * 0.25) * p1.facing)
            p2.kb_y = -3.0
            p2.shield_stun = int(abs(p2.kb_x) * 1.5) + 5
        else:
            p2.damage += p1_attack["damage"]
            if p1_attack.get("vertical_launch"):
                p2.attack_cooldown = p1_attack.get("cooldown", 0)
                p2.kb_x = float((p1_attack["knockback"] * 0.2) * p1.facing)
                p2.kb_y = float(-(p1_attack["knockback"] + (p2.damage // 3)))
                p2.hitstun = int(max(abs(p2.kb_x), abs(p2.kb_y)) * 0.6)
                p2.is_spinning = True
                # Use a large spin frame count so the visual spin persists
                # until the slam landing clears it in physics.ground_collision.
                p2.spin_frames = 99999
                p2.slam_ready = True
                p2.slam_strength = max(8.0, abs(p2.kb_y) * 0.75)
            else:
                p2.kb_x = float((p1_attack["knockback"] + (p2.damage // 2)) * p1.facing)
                p2.kb_y = -8.5
                p2.hitstun = int(abs(p2.kb_x) * 0.75)
        p1.has_hit = True
        p2.is_hanging = False

    if p2_hitbox and p2_attack and p2_hitbox.colliderect(p1.rect) and not p2.has_hit and p1.invincible_frames == 0:
        # If defender was prone, getting hit should immediately bring them upright.
        if getattr(p1, 'prone', False):
            p1.prone = False
        # If the defender is shielding, reduce damage and apply shield impact.
        if p1.is_shielding and p1.shield_hp > 0:
            p1.shield_hp -= p2_attack["damage"] * 0.5
            if p1.shield_hp < 0:
                p1.shield_hp = 0
            p1.kb_x = float((p2_attack["knockback"] * 0.25) * p2.facing)
            p1.kb_y = -3.0
            p1.shield_stun = int(abs(p1.kb_x) * 1.5) + 5
        else:
            # Normal hit: add damage percentage and apply knockback.
            p1.damage += p2_attack["damage"]
            if p2_attack.get("vertical_launch"):
                p1.attack_cooldown = p2_attack.get("cooldown", 0)
                p1.kb_x = float((p2_attack["knockback"] * 0.2) * p2.facing)
                p1.kb_y = float(-(p2_attack["knockback"] + (p1.damage // 3)))
                p1.hitstun = int(max(abs(p1.kb_x), abs(p1.kb_y)) * 0.6)
                p1.is_spinning = True
                p1.spin_frames = 99999
                p1.slam_ready = True
                p1.slam_strength = max(8.0, abs(p1.kb_y) * 0.75)
            else:
                p1.kb_x = float((p2_attack["knockback"] + (p1.damage // 2)) * p2.facing)
                p1.kb_y = -8.5
                p1.hitstun = int(abs(p1.kb_x) * 0.75)
        p2.has_hit = True
        # Exit ledge hang if the player was hit while hanging.
        p1.is_hanging = False


def apply_DI(p, keys, left, right, up, down):
    # Apply directional influence while the player is in hitstun.
    # This lets the defender adjust their knockback trajectory slightly.
    if p.hitstun > 0:
        if keys[left]:
            p.kb_x -= DI_STRENGTH
        if keys[right]:
            p.kb_x += DI_STRENGTH
        if keys[up]:
            p.kb_y -= DI_STRENGTH
        if keys[down]:
            p.kb_y += DI_STRENGTH


def shield_and_movement(p, keys, left_key, right_key, shield_key):
    # This function processes shield input, hitstun, and player movement.
    # It prevents movement while shielding or stunned.
    if p.shield_stun > 0:
        # Shield stun after a broken shield; player cannot act.
        p.shield_stun -= 1
        p.is_shielding = False
    elif p.hitstun > 0:
        p.hitstun -= 1
        p.is_shielding = False
    elif keys[shield_key] and p.shield_hp > 0 and not p.is_hanging:
        # Hold shield: drain HP and potentially cause shield stun
        p.is_shielding = True
        p.shield_hp -= SHIELD_DRAIN_SPEED
        if p.shield_hp <= 0:
            p.shield_hp = 0
            p.shield_stun = 120
            p.is_shielding = False
    else:
        p.is_shielding = False

    # Passive shield regen when not shielding
    if p.shield_hp < MAX_SHIELD_HP and not p.is_shielding:
        p.shield_hp += SHIELD_REGEN_SPEED

    # Movement input allowed when not stunned/shielding/hanging/prone
    if not p.is_shielding and p.shield_stun == 0 and p.hitstun == 0 and not p.is_hanging and not getattr(p, 'prone', False):
        if keys[left_key]:
            p.x -= PLAYER_SPEED
            p.facing = -1
        if keys[right_key]:
            p.x += PLAYER_SPEED
            p.facing = 1
