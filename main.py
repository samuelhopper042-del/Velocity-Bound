# ============================================================
# Velocity Bound
#
# Main Game File (refactored)
#
# This file wires together small modules:
# - players/player.py
# - stages/stage.py
# - systems/physics.py
# - systems/combat.py
# - ui/hud.py
# - attacks/
# - data/
#
# The main loop remains here for clarity.
# ============================================================

import asyncio
import pygame
import pymunk
from settings import *

from players.player import Player
from stages.stage import create_stage
from systems import combat
from ui import hud
from attacks import DEFAULT_ATTACKS
from data import GAME_CONFIG


def key_constant(key_name):
    """Convert a config key name into a pygame key constant."""
    if not key_name:
        return None
    normalized = key_name.strip().lower().replace(" ", "_")
    return getattr(pygame, f"K_{normalized}", None)


async def main():
    pygame.init()

    # Create the display surface, window title, and font for HUD text.
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    ui_font = pygame.font.SysFont("Arial", 28)
    clock = pygame.time.Clock()

    # We use asyncio.sleep(0) at the end of each loop to yield control and
    # keep the event loop responsive.

    stage_rect, left_ledge, right_ledge = create_stage()

    # Build the physics world using pymunk. We use a step of `1` per frame so
    # the physics units remain compatible with the existing per-frame movement
    # values already encoded in the game.
    space = pymunk.Space()
    space.gravity = (0, GRAVITY)

    ground_shape = pymunk.Segment(
        space.static_body,
        (stage_rect.left, stage_rect.top),
        (stage_rect.right, stage_rect.top),
        0,
    )
    ground_shape.friction = 1.0
    ground_shape.elasticity = 0.0
    ground_shape.filter = pymunk.ShapeFilter(categories=0b01)
    space.add(ground_shape)

    p1 = Player(
        GAME_CONFIG["players"]["p1"]["start_x"],
        GAME_CONFIG["players"]["p1"]["start_y"],
        tuple(GAME_CONFIG["players"]["p1"]["color"]),
    )
    p2 = Player(
        GAME_CONFIG["players"]["p2"]["start_x"],
        GAME_CONFIG["players"]["p2"]["start_y"],
        tuple(GAME_CONFIG["players"]["p2"]["color"]),
    )

    def create_player_body(player):
        player.create_body(space)

    create_player_body(p1)
    create_player_body(p2)

    # Remove the temporary no-rotation debug override: setting body.moment to inf
    # inside a ragdoll with joints and motors can produce invalid physics state.
    # The game should use normal physics simulation for stable player movement.

    # Attach shared attack data to both players.
    p1.attack_set = DEFAULT_ATTACKS
    p2.attack_set = DEFAULT_ATTACKS
    p1.current_attack = None
    p2.current_attack = None

    # Keep the integer collision rect in sync with the physics body position.
    def sync_player_rect(player):
        if getattr(player, 'body', None):
            player.x, player.y = player.body.position
            player.rect.x = int(player.x - player.rect.width / 2)
            player.rect.y = int(player.y - player.rect.height / 2)

    sync_player_rect(p1)
    sync_player_rect(p2)

    STATE_IDLE = 0
    STATE_RUNNING = 1
    STATE_JUMPING = 2
    STATE_ATTACKING = 3
    STATE_SHIELDING = 4
    STATE_HITSTUN = 5
    STATE_HANGING = 6

    p1_state = STATE_IDLE
    p2_state = STATE_IDLE

    p1_controls = GAME_CONFIG["controls"]["p1"]
    p2_controls = GAME_CONFIG["controls"]["p2"]

    p1_left_key = key_constant(p1_controls["left"])
    p1_right_key = key_constant(p1_controls["right"])
    p1_jump_key = key_constant(p1_controls["jump"])
    p1_shield_key = key_constant(p1_controls["shield"])
    p1_attack_jab_key = key_constant(p1_controls["attack_jab"])
    p1_attack_uppercut_key = key_constant(p1_controls["attack_uppercut"])

    p2_left_key = key_constant(p2_controls["left"])
    p2_right_key = key_constant(p2_controls["right"])
    p2_jump_key = key_constant(p2_controls["jump"])
    p2_shield_key = key_constant(p2_controls["shield"])
    p2_attack_jab_key = key_constant(p2_controls["attack_jab"])
    p2_attack_uppercut_key = key_constant(p2_controls["attack_uppercut"])

    game_active = True
    winner_text = ""

    # Main loop
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # User closed the window: stop the game cleanly.
                pygame.quit()
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Reset match state and respawn both players.
                    p1.stocks = 3
                    p2.stocks = 3
                    p1.damage = 0
                    p2.damage = 0
                    p1.reset_position(350, 250)
                    p2.reset_position(880, 250)
                    p1.attack_frames = 0
                    p2.attack_frames = 0
                    p1.has_hit = False
                    p2.has_hit = False
                    p1.is_hanging = False
                    p2.is_hanging = False
                    p1.shield_hp = MAX_SHIELD_HP
                    p2.shield_hp = MAX_SHIELD_HP
                    p1.shield_stun = 0
                    p2.shield_stun = 0
                    p1.hitstun = 0
                    p2.hitstun = 0
                    p1.invincible_frames = 0
                    p2.invincible_frames = 0
                    game_active = True
                    winner_text = ""

                if game_active:
                    # Only allow player actions if the match is active.
                    # This prevents input after the game has ended.

                    # Player 1: ledge climb / drop or normal jump
                    if p1.is_hanging:
                        # While hanging: tap jump to jump away from the ledge,
                        # press drop to fall. Climb behavior is not bound to tap.
                        if event.key == pygame.K_s:  # drop from ledge
                            p1.is_hanging = False
                            p1.ledge_cooldown = 30
                            p1.set_vertical_velocity(4.0)
                        elif event.key == pygame.K_w:  # tap jump -> jump out of hang
                            # Jump out of the ledge: give upward and outward impulse
                            p1.is_hanging = False
                            p1.ledge_cooldown = 30
                            p1.set_vertical_velocity(-JUMP_POWER)
                            if getattr(p1, 'hang_side', None) == 'left':
                                p1.kb_x = -HANG_JUMP_HORIZONTAL
                                p1.facing = -1
                            else:
                                p1.kb_x = HANG_JUMP_HORIZONTAL
                                p1.facing = 1
                            # consume a jump so double-jump logic remains consistent
                            p1.jumps_left = max(0, p1.jumps_left - 1)
                    else:
                        # Normal jump when not hanging.
                        # If the player is currently in the spin animation from an uppercut,
                        # pressing jump cancels the spin and allows a normal jump.
                        if event.key == p1_jump_key:
                            if getattr(p1, 'is_spinning', False) and p1.jumps_left > 0:
                                p1.is_spinning = False
                                p1.spin_frames = 0
                                p1.spin_angle = 0.0
                                p1.slam_ready = False
                                p1.set_vertical_velocity(-JUMP_POWER)
                                p1.jumps_left -= 1
                            elif getattr(p1, 'prone', False):
                                # Hop up from stomach to land on feet
                                p1.prone = False
                                p1.set_vertical_velocity(-JUMP_POWER * 0.7)
                                p1.jumps_left = max(0, p1.jumps_left - 1)
                            elif p1.jumps_left > 0:
                                p1.set_vertical_velocity(-JUMP_POWER)
                                p1.jumps_left -= 1

                    # Player 2: ledge climb / drop or normal jump (mirrored keys)
                    if p2.is_hanging:
                        if event.key == p2_shield_key:  # drop from ledge
                            p2.is_hanging = False
                            p2.ledge_cooldown = 30
                            p2.set_vertical_velocity(4.0)
                        elif event.key == p2_jump_key:  # tap jump -> jump out
                            p2.is_hanging = False
                            p2.ledge_cooldown = 30
                            p2.set_vertical_velocity(-JUMP_POWER)
                            if getattr(p2, 'hang_side', None) == 'left':
                                p2.kb_x = -HANG_JUMP_HORIZONTAL
                                p2.facing = -1
                            else:
                                p2.kb_x = HANG_JUMP_HORIZONTAL
                                p2.facing = 1
                            p2.jumps_left = max(0, p2.jumps_left - 1)
                    else:
                        if event.key == p2_jump_key:
                            if getattr(p2, 'is_spinning', False) and p2.jumps_left > 0:
                                p2.is_spinning = False
                                p2.spin_frames = 0
                                p2.spin_angle = 0.0
                                p2.slam_ready = False
                                p2.set_vertical_velocity(-JUMP_POWER)
                                p2.jumps_left -= 1
                            elif getattr(p2, 'prone', False):
                                p2.prone = False
                                p2.set_vertical_velocity(-JUMP_POWER * 0.7)
                                p2.jumps_left = max(0, p2.jumps_left - 1)
                            elif p2.jumps_left > 0:
                                p2.set_vertical_velocity(-JUMP_POWER)
                                p2.jumps_left -= 1

                    # Attacks
                    if event.key == p1_attack_jab_key and p1.attack_frames == 0 and p1.attack_cooldown == 0 and not p1.is_hanging:
                        p1.current_attack = p1.attack_set["jab"]
                        p1.attack_frames = p1.current_attack["duration"]
                        p1.has_hit = False
                    if event.key == p1_attack_uppercut_key and p1.attack_frames == 0 and p1.attack_cooldown == 0 and not p1.is_hanging:
                        p1.current_attack = p1.attack_set["uppercut"]
                        p1.attack_frames = p1.current_attack["duration"]
                        p1.has_hit = False
                        p1.attack_cooldown = p1.current_attack.get("cooldown", 0)

                    if event.key == p2_attack_jab_key and p2.attack_frames == 0 and p2.attack_cooldown == 0 and not p2.is_hanging:
                        p2.current_attack = p2.attack_set["jab"]
                        p2.attack_frames = p2.current_attack["duration"]
                        p2.has_hit = False
                    if event.key == p2_attack_uppercut_key and p2.attack_frames == 0 and p2.attack_cooldown == 0 and not p2.is_hanging:
                        p2.current_attack = p2.attack_set["uppercut"]
                        p2.attack_frames = p2.current_attack["duration"]
                        p2.has_hit = False
                        p2.attack_cooldown = p2.current_attack.get("cooldown", 0)

        # Game logic
        # `get_pressed()` returns the current keyboard state for held keys.
        keys = pygame.key.get_pressed()

        def is_airborne(player):
            if getattr(player, 'body', None):
                return abs(player.body.velocity.y) > 0.1
            return False

        # Update simple action states for UI and decision-making.
        # The order is important: hanging and hitstun override movement.
        p1_state = STATE_HANGING if p1.is_hanging else (
            STATE_HITSTUN if p1.hitstun > 0 else (
            STATE_SHIELDING if p1.is_shielding else (
            STATE_ATTACKING if p1.attack_frames > 0 else (
            STATE_JUMPING if is_airborne(p1) else (
            STATE_RUNNING if (keys[pygame.K_a] or keys[pygame.K_d]) else STATE_IDLE)))))

        p2_state = STATE_HANGING if p2.is_hanging else (
            STATE_HITSTUN if p2.hitstun > 0 else (
            STATE_SHIELDING if p2.is_shielding else (
            STATE_ATTACKING if p2.attack_frames > 0 else (
            STATE_JUMPING if is_airborne(p2) else (
            STATE_RUNNING if (keys[pygame.K_j] or keys[pygame.K_l]) else STATE_IDLE)))))

        if game_active:
            # Timers
            # These counters decrement each frame to implement delays, invulnerability,
            # and ledge re-grab prevention.
            if p1.invincible_frames > 0:
                p1.invincible_frames -= 1
            if p2.invincible_frames > 0:
                p2.invincible_frames -= 1
            if p1.ledge_cooldown > 0:
                p1.ledge_cooldown -= 1
            if p2.ledge_cooldown > 0:
                p2.ledge_cooldown -= 1
            if p1.attack_cooldown > 0:
                p1.attack_cooldown -= 1
            if p2.attack_cooldown > 0:
                p2.attack_cooldown -= 1
            # Spin frame countdown and visual rotation update
            if p1.spin_frames > 0:
                p1.spin_frames -= 1
                p1.spin_angle = (p1.spin_angle + 4.0) % 360.0
                if p1.spin_frames == 0:
                    p1.is_spinning = False
                    p1.spin_angle = 0.0
            if p2.spin_frames > 0:
                p2.spin_frames -= 1
                p2.spin_angle = (p2.spin_angle + 4.0) % 360.0
                if p2.spin_frames == 0:
                    p2.is_spinning = False
                    p2.spin_angle = 0.0

            # Update slam particles for both players
            for p in (p1, p2):
                new_particles = []
                for part in getattr(p, 'slam_particles', []):
                    part['x'] += part['vx']
                    part['y'] += part['vy']
                    part['vy'] += GRAVITY * 0.4
                    part['life'] -= 1
                    if part['life'] > 0:
                        new_particles.append(part)
                p.slam_particles = new_particles

                if p.sprite_frames:
                    p.sprite_index = (p.sprite_index + p.sprite_anim_speed) % len(p.sprite_frames)

            # DI (Directional Influence)
            # Allows players to influence knockback direction while in hitstun.
            combat.apply_DI(p1, keys, pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s)
            combat.apply_DI(p2, keys, pygame.K_j, pygame.K_l, pygame.K_i, pygame.K_k)

            # Shielding and movement processing handles input and block state.
            combat.shield_and_movement(p1, keys, pygame.K_a, pygame.K_d, pygame.K_s)
            combat.shield_and_movement(p2, keys, pygame.K_j, pygame.K_l, pygame.K_k)

            # Walk timer updates for stick figure animation.
            for p, left_key, right_key in ((p1, pygame.K_a, pygame.K_d), (p2, pygame.K_j, pygame.K_l)):
                if getattr(p, 'body', None):
                    if abs(p.body.velocity.x) > 0.5 and p.hitstun == 0 and not p.is_shielding and not p.is_hanging:
                        p.walk_timer += 0.16
                    else:
                        p.walk_timer *= 0.88
                    move_input = 0.0
                    if keys[left_key]:
                        move_input = -1.0
                    elif keys[right_key]:
                        move_input = 1.0
                    p.update_limb_sim(move_input)

            # When using pymunk, player position is driven by the physics body.
            # The character rectangle and game state are synchronized after the
            # physics step below.

            # Update attacks and resolve any collisions with opponents.
            p1_hitbox, p2_hitbox, p1_attack_ref, p2_attack_ref = combat.tick_attacks(p1, p2)
            combat.handle_hits(p1, p2, p1_hitbox, p2_hitbox, p1_attack_ref, p2_attack_ref)

            # Clear finished attacks after hit resolution so attack metadata
            # remains available during handle_hits. Reset `has_hit` for the
            # next attack cycle when the attack fully finishes.
            if getattr(p1, 'attack_frames', 0) <= 0:
                p1.current_attack = None
                p1.has_hit = False
            if getattr(p2, 'attack_frames', 0) <= 0:
                p2.current_attack = None
                p2.has_hit = False

            # Step the physics simulation. We use a time step of 1 to keep
            # the pymunk simulation in the same per-frame unit system as the
            # rest of the game.
            space.step(1)

            # Update player rectangles from the physics bodies.
            sync_player_rect(p1)
            sync_player_rect(p2)

            def update_grounded(player):
                if getattr(player, 'shape', None) and getattr(player, 'body', None):
                    on_ground = (
                        player.rect.bottom >= stage_rect.top
                        and player.rect.bottom <= stage_rect.top + 8
                        and stage_rect.left <= player.rect.centerx <= stage_rect.right
                        and player.body.velocity.y >= 0
                    )
                    if on_ground:
                        player.jumps_left = 2
                        if player.slam_ready:
                            player.slam_ready = False
                            player.is_spinning = False
                            player.spin_frames = 0
                            player.spin_angle = 0.0
                            player.prone = True
                            player.body.velocity = (player.body.velocity.x, float(player.slam_strength * 0.5))
                            player.slam_strength = 0.0
                    return on_ground
                return False

            update_grounded(p1)
            update_grounded(p2)

            # Blast zones
            # If a player leaves the visible play area, they are knocked out and respawn.
            DEAD_ZONE_LEFT, DEAD_ZONE_RIGHT = -100, SCREEN_WIDTH + 100
            DEAD_ZONE_BOTTOM, DEAD_ZONE_TOP = SCREEN_HEIGHT + 100, -100

            def respawn(player, x, y):
                player.stocks -= 1
                player.damage = 0
                player.reset_position(x, y)
                player.kb_x = 0.0
                player.kb_y = 0.0
                if getattr(player, 'body', None):
                    player.body.velocity = (0.0, 0.0)
                player.is_hanging = False
                player.invincible_frames = 90
                player.attack_cooldown = 0
                player.is_spinning = False
                player.spin_frames = 0
                player.slam_ready = False
                player.slam_strength = 0.0

            if p1.rect.x < DEAD_ZONE_LEFT or p1.rect.x > DEAD_ZONE_RIGHT or p1.rect.y > DEAD_ZONE_BOTTOM or (p1.rect.y < DEAD_ZONE_TOP and p1.hitstun > 0):
                respawn(p1, 440, 150)

            if p2.rect.x < DEAD_ZONE_LEFT or p2.rect.x > DEAD_ZONE_RIGHT or p2.rect.y > DEAD_ZONE_BOTTOM or (p2.rect.y < DEAD_ZONE_TOP and p2.hitstun > 0):
                respawn(p2, 790, 150)

            if p1.stocks <= 0 or p2.stocks <= 0:
                game_active = False
                if p1.stocks <= 0 and p2.stocks <= 0:
                    winner_text = "Double KO!"
                elif p1.stocks <= 0:
                    winner_text = "Player 2 Wins!"
                else:
                    winner_text = "Player 1 Wins!"
        else:
            p1_hitbox = None
            p2_hitbox = None

        # Draw
        hud.draw(screen, ui_font, p1, p2, p1_hitbox, p2_hitbox, stage_rect, game_active, winner_text)

        clock.tick(FPS)
        await asyncio.sleep(0)


asyncio.run(main())
