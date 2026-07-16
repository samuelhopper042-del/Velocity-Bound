import pygame
import sys
import asyncio  # FIXED: Added for web browser loading compatibility

async def main():  # FIXED: Wrapped game loop in async environment
    # Initialize basic display
    pygame.init()

    # Setup display window (16:9 widescreen format)
    SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Velocity Bound")

     # UI Font Setup
    ui_font = pygame.font.SysFont("Arial", 28)
    
    # Frame rate controller
    clock = pygame.time.Clock()
    FPS = 60

    # --- GAME OBJECTS & STAGE SETUP ---
    stage_rect = pygame.Rect(240, 500, 800, 50)
    STAGE_COLOR = (70, 70, 80) # Steel gray

    # Ledge Grabbing Rectangles (Left and Right corners of the stage)
    LEDGE_WIDTH, LEDGE_HEIGHT = 15, 15
    left_ledge = pygame.Rect(stage_rect.left - 5, stage_rect.top, LEDGE_WIDTH, LEDGE_HEIGHT)
    right_ledge = pygame.Rect(stage_rect.right - 10, stage_rect.top, LEDGE_WIDTH, LEDGE_HEIGHT)

    # Player 1 Profile (WASD Character)
    p1_rect = pygame.Rect(350, 300, 50, 60)
    p1_COLOR = (0, 100, 255) # Blue
    p1_x = float(p1_rect.x)
    p1_y = float(p1_rect.y)

    # Player 2 Profile (IJKL Character)
    p2_rect = pygame.Rect(880, 300, 50, 60)
    p2_COLOR = (255, 50, 50) # Red
    p2_x = float(p2_rect.x)
    p2_y = float(p2_rect.y)

    # --- PLAYER VELOCITY & TERMINAL CONFIGURATION ---
    p1_y_velocity = 0.0
    p2_y_velocity = 0.0
    GRAVITY = 0.5
    PLAYER_SPEED = 5
    JUMP_POWER = 12
    MAX_FALL_SPEED = 10.0 # System 5: Standard Terminal Velocity Cap
    FAST_FALL_SPEED = 16.0 # System 5: Fast fall terminal speed cap

    # Double Jump Configuration
    p1_jumps_left = 2
    p2_jumps_left = 2

    # Facing Directions (-1 = Left, 1 = Right)
    p1_facing = 1
    p2_facing = -1

    # Attack Timers & Multi-Hit Prevention Flags
    p1_attack_frames = 0
    p2_attack_frames = 0
    ATTACK_DURATION = 15
    p1_has_hit = False
    p2_has_hit = False

    # Hitbox Dimensions
    HITBOX_WIDTH = 45
    HITBOX_HEIGHT = 30
    p1_hitbox = None
    p2_hitbox = None

    # Knockback Physics Forces
    p1_kb_x = 0.0
    p1_kb_y = 0.0 # Upgraded: Now tracking vertical vector for full directional influence
    p2_kb_x = 0.0
    p2_kb_y = 0.0
    KNOCKBACK_DECAY = 0.88
    KNOCKBACK_force = 12

    # System 3 & 4: DI Strength & Ledge State Trackers
    DI_STRENGTH = 0.4
    p1_is_hanging = False
    p1_ledge_cooldown = 0
    p2_is_hanging = False
    p2_ledge_cooldown = 0

    # --- DAMAGE & STOCK TRACKING ---
    p1_stocks = 3
    p2_stocks = 3
    p1_damage = 0
    p2_damage = 0

    # --- STATE MACHINE ARCHITECTURE ---
    STATE_IDLE = 0
    STATE_RUNNING = 1
    STATE_JUMPING = 2
    STATE_ATTACKING = 3
    STATE_SHIELDING = 4
    STATE_HITSTUN = 5
    STATE_HANGING = 6

    p1_state = STATE_IDLE
    p2_state = STATE_IDLE

    # Match state tracker
    game_active = True
    winner_text = ""
    p1_hitstun = 0
    p2_hitstun = 0
    p1_invincible_frames = 0
    p2_invincible_frames = 0

    # SHIELD HEALTH & STUN ENGINE ---
    p1_is_shielding = False
    p2_is_shielding = False
    p1_shield_hp = 100.0
    p2_shield_hp = 100.0
    p1_shield_stun = 0
    p2_shield_stun = 0
    MAX_SHIELD_HP = 100.0
    SHIELD_DRAIN_SPEED = 0.4
    SHIELD_REGEN_SPEED = 0.15

    # Core Game Loop
    while True:
        # 1. Event Handling (Window Controls & Single-Tap Actions)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return  # FIXED: Changed from sys.exit() for web async compatibility

            if event.type == pygame.KEYDOWN:
                # Check for instant round reset button
                if event.key == pygame.K_r:
                    p1_stocks = 3
                    p2_stocks = 3
                    p1_damage = 0
                    p2_damage = 0
                    p1_x, p1_y = 350.0, 300.0
                    p2_x, p2_y = 880.0, 300.0
                    p1_kb_x, p1_kb_y = 0.0, 0.0
                    p2_kb_x, p2_kb_y = 0.0, 0.0
                    p1_y_velocity = 0.0
                    p2_y_velocity = 0.0
                    p1_jumps_left = 2
                    p2_jumps_left = 2
                    p1_attack_frames = 0
                    p2_attack_frames = 0
                    p1_has_hit = False
                    p2_has_hit = False
                    p1_is_hanging = False
                    p2_is_hanging = False
                    game_active = True
                    winner_text = ""
                    p1_shield_hp = 100.0
                    p2_shield_hp = 100.0
                    p1_shield_stun = 0
                    p2_shield_stun = 0
                    p1_hitstun = 0
                    p2_hitstun = 0
                    p1_invincible_frames = 0
                    p2_invincible_frames = 0

                if game_active:
                    # System 4: Ledge Escape mechanic (Pressing down drops down from ledge)
                    if p1_is_hanging and event.key == pygame.K_s:
                        p1_is_hanging = False
                        p1_ledge_cooldown = 30
                    elif not p1_is_hanging and event.key == pygame.K_w and p1_jumps_left > 0:
                        p1_y_velocity = -JUMP_POWER
                        p1_jumps_left -= 1

                    if p2_is_hanging and event.key == pygame.K_k:
                        p2_is_hanging = False
                        p2_ledge_cooldown = 30
                    elif not p2_is_hanging and event.key == pygame.K_i and p2_jumps_left > 0:
                        p2_y_velocity = -JUMP_POWER
                        p2_jumps_left -= 1

                    if event.key == pygame.K_f and p1_attack_frames == 0 and not p1_is_hanging:
                        p1_attack_frames = ATTACK_DURATION
                        p1_has_hit = False

                    if event.key == pygame.K_h and p2_attack_frames == 0 and not p2_is_hanging:
                        p2_attack_frames = ATTACK_DURATION
                        p2_has_hit = False

        # 2. Game Logic Updates
        keys = pygame.key.get_pressed()

        if p1_is_hanging:
            p1_state = STATE_HANGING
        elif p1_hitstun > 0:
            p1_state = STATE_HITSTUN
        elif p1_is_shielding:
            p1_state = STATE_SHIELDING
        elif p1_attack_frames > 0:
            p1_state = STATE_ATTACKING
        elif p1_y_velocity != 0:
            p1_state = STATE_JUMPING
        elif keys[pygame.K_a] or keys[pygame.K_d]:
            p1_state = STATE_RUNNING
        else:
            p1_state = STATE_IDLE

        # === UPDATE PLAYER 2 STATE MACHINE ===
        if p2_is_hanging:
            p2_state = STATE_HANGING
        elif p2_hitstun > 0:
            p2_state = STATE_HITSTUN
        elif p2_is_shielding:
            p2_state = STATE_SHIELDING
        elif p2_attack_frames > 0:
            p2_state = STATE_ATTACKING
        elif p2_y_velocity != 0:
            p2_state = STATE_JUMPING
        elif keys[pygame.K_j] or keys[pygame.K_l]:
            p2_state = STATE_RUNNING
        else:
            p2_state = STATE_IDLE

        if game_active:
            if p1_invincible_frames > 0: p1_invincible_frames -= 1
            if p2_invincible_frames > 0: p2_invincible_frames -= 1
            if p1_ledge_cooldown > 0: p1_ledge_cooldown -= 1
            if p2_ledge_cooldown > 0: p2_ledge_cooldown -= 1

            # === SYSTEM 3: ACTIVE DIRECTIONAL INFLUENCE (DI) ENGINE ===
            if p1_hitstun > 0:
                if keys[pygame.K_a]: p1_kb_x -= DI_STRENGTH
                if keys[pygame.K_d]: p1_kb_x += DI_STRENGTH
                if keys[pygame.K_w]: p1_kb_y -= DI_STRENGTH
                if keys[pygame.K_s]: p1_kb_y += DI_STRENGTH

            if p2_hitstun > 0:
                if keys[pygame.K_j]: p2_kb_x -= DI_STRENGTH
                if keys[pygame.K_l]: p2_kb_x += DI_STRENGTH
                if keys[pygame.K_i]: p2_kb_y -= DI_STRENGTH
                if keys[pygame.K_k]: p2_kb_y += DI_STRENGTH

                    # === PLAYER 1 SHIELD, STUN, & STANDARD MOVEMENT ===
            if p1_shield_stun > 0:
                p1_shield_stun -= 1
                p1_is_shielding = False
            elif p1_hitstun > 0:
                p1_hitstun -= 1
                p1_is_shielding = False
            elif keys[pygame.K_s] and p1_shield_hp > 0 and not p1_is_hanging:
                p1_is_shielding = True
                p1_shield_hp -= SHIELD_DRAIN_SPEED
                if p1_shield_hp <= 0:
                    p1_shield_hp = 0
                    p1_shield_stun = 120
                    p1_is_shielding = False
            else:
                p1_is_shielding = False

            if p1_shield_hp < MAX_SHIELD_HP and not p1_is_shielding:
                p1_shield_hp += SHIELD_REGEN_SPEED

            if not p1_is_shielding and p1_shield_stun == 0 and p1_hitstun == 0 and not p1_is_hanging:
                if keys[pygame.K_a]:
                    p1_x -= PLAYER_SPEED
                    p1_facing = -1
                if keys[pygame.K_d]:
                    p1_x += PLAYER_SPEED
                    p1_facing = 1

            # === PLAYER 2 SHIELD, STUN, & STANDARD MOVEMENT ===
            if p2_shield_stun > 0:
                p2_shield_stun -= 1
                p2_is_shielding = False
            elif p2_hitstun > 0:
                p2_hitstun -= 1
                p2_is_shielding = False
            elif keys[pygame.K_k] and p2_shield_hp > 0 and not p2_is_hanging:
                p2_is_shielding = True
                p2_shield_hp -= SHIELD_DRAIN_SPEED
                if p2_shield_hp <= 0:
                    p2_shield_hp = 0
                    p2_shield_stun = 120
                    p2_is_shielding = False
            else:
                p2_is_shielding = False

            if p2_shield_hp < MAX_SHIELD_HP and not p2_is_shielding:
                p2_shield_hp += SHIELD_REGEN_SPEED

            if not p2_is_shielding and p2_shield_stun == 0 and p2_hitstun == 0 and not p2_is_hanging:
                if keys[pygame.K_j]:
                    p2_x -= PLAYER_SPEED
                    p2_facing = -1
                if keys[pygame.K_l]:
                    p2_x += PLAYER_SPEED
                    p2_facing = 1

            # Sync floats to physics rect boundaries
            p1_rect.x = int(p1_x)
            p2_rect.x = int(p2_x)

            # --- STEP 2: TICK DOWN ATTACK TIMERS & GENERATE HITBOX RECTANGLES ---
            p1_hitbox = None
            if p1_attack_frames > 0:
                p1_attack_frames -= 1
                p1_center_y = p1_rect.y + (p1_rect.height // 2)
                if p1_facing == 1:
                    p1_hitbox = pygame.Rect(p1_rect.right, p1_center_y - (HITBOX_HEIGHT // 2), HITBOX_WIDTH, HITBOX_HEIGHT)
                else:
                    p1_hitbox = pygame.Rect(p1_rect.left - HITBOX_WIDTH, p1_center_y - (HITBOX_HEIGHT // 2), HITBOX_WIDTH, HITBOX_HEIGHT)

            p2_hitbox = None
            if p2_attack_frames > 0:
                p2_attack_frames -= 1
                p2_center_y = p2_rect.y + (p2_rect.height // 2)
                if p2_facing == 1:
                    p2_hitbox = pygame.Rect(p2_rect.right, p2_center_y - (HITBOX_HEIGHT // 2), HITBOX_WIDTH, HITBOX_HEIGHT)
                else:
                    p2_hitbox = pygame.Rect(p2_rect.left - HITBOX_WIDTH, p2_center_y - (HITBOX_HEIGHT // 2), HITBOX_WIDTH, HITBOX_HEIGHT)

            # --- STEP 3: COMBAT HIT DETECTION ---
            if p1_hitbox and p1_hitbox.colliderect(p2_rect) and not p1_has_hit and p2_invincible_frames == 0:
                p2_damage += 12
                p2_kb_x = float((KNOCKBACK_force + (p2_damage // 2)) * p1_facing)
                p2_kb_y = -8.5
                p1_has_hit = True
                p2_is_hanging = False
                p2_hitstun = int(abs(p2_kb_x) * 0.75)

            if p2_hitbox and p2_hitbox.colliderect(p1_rect) and not p2_has_hit and p1_invincible_frames == 0:
                p1_damage += 12
                p1_kb_x = float((KNOCKBACK_force + (p1_damage // 2)) * p2_facing)
                p1_kb_y = -8.5
                p2_has_hit = True
                p1_is_hanging = False
                p1_hitstun = int(abs(p1_kb_x) * 0.75)

            # === SYSTEM 2: HITBOX INTERPOLATION ===
            max_step = max(1, int(max(abs(p1_kb_x), abs(p1_kb_y), abs(p2_kb_x), abs(p2_kb_y))))
            for _ in range(max_step):
                p1_x += p1_kb_x / max_step
                p1_y += p1_kb_y / max_step
                p2_x += p2_kb_x / max_step
                p2_y += p2_kb_y / max_step
                p1_rect.x, p1_rect.y = int(p1_x), int(p1_y)
                p2_rect.x, p2_rect.y = int(p2_x), int(p2_y)

                if p1_rect.colliderect(stage_rect) and p1_kb_y >= 0:
                    if p1_rect.bottom - (p1_kb_y / max_step) <= stage_rect.top + 10:
                        p1_rect.bottom = stage_rect.top
                        p1_y = float(p1_rect.y)
                        p1_kb_y = 0.0

                if p2_rect.colliderect(stage_rect) and p2_kb_y >= 0:
                    if p2_rect.bottom - (p2_kb_y / max_step) <= stage_rect.top + 10:
                        p2_rect.bottom = stage_rect.top
                        p2_y = float(p2_rect.y)
                        p2_kb_y = 0.0

            p1_kb_x *= KNOCKBACK_DECAY
            p1_kb_y *= KNOCKBACK_DECAY
            p2_kb_x *= KNOCKBACK_DECAY
            p2_kb_y *= KNOCKBACK_DECAY
            if abs(p1_kb_x) < 0.1: p1_kb_x = 0.0
            if abs(p1_kb_y) < 0.1: p1_kb_y = 0.0
            if abs(p2_kb_x) < 0.1: p2_kb_x = 0.0
            if abs(p2_kb_y) < 0.1: p2_kb_y = 0.0

            # --- STEP 5: PERMANENT SOLIDITY ENGINE ---
            if p1_rect.colliderect(p2_rect) and not p1_is_hanging and not p2_is_hanging:
                overlap_left = p1_rect.right - p2_rect.left
                overlap_right = p2_rect.right - p1_rect.left
                if overlap_left < overlap_right:
                    push = overlap_left // 2
                    p1_x -= push
                    p2_x += push
                    if p1_kb_x > 0: p1_kb_x = 0.0
                    if p2_kb_x < 0: p2_kb_x = 0.0
                else:
                    push = overlap_right // 2
                    p1_x += push
                    p2_x -= push
                    if p1_kb_x < 0: p1_kb_x = 0.0
                    if p2_kb_x > 0: p2_kb_x = 0.0

            # === SYSTEM 4 & 5: RECOVERY INTERSECT, FAST FALL, & GRAVITY PROCESSING ===
            if not p1_is_hanging:
                p1_y_velocity += GRAVITY
                current_cap = FAST_FALL_SPEED if (keys[pygame.K_s] and p1_y_velocity > 0) else MAX_FALL_SPEED
                if p1_y_velocity > current_cap: p1_y_velocity = current_cap
                p1_y += p1_y_velocity
                p1_rect.y = int(p1_y)

                if p1_y_velocity >= 0 and p1_hitstun == 0 and p1_ledge_cooldown == 0:
                    if p1_rect.colliderect(left_ledge):
                        p1_is_hanging = True
                        p1_x, p1_y = float(left_ledge.x - 15), float(left_ledge.y)
                        p1_y_velocity, p1_kb_x, p1_kb_y = 0.0, 0.0, 0.0
                        p1_jumps_left = 2
                    elif p1_rect.colliderect(right_ledge):
                        p1_is_hanging = True
                        p1_x, p1_y = float(right_ledge.x - 20), float(right_ledge.y)
                        p1_y_velocity, p1_kb_x, p1_kb_y = 0.0, 0.0, 0.0
                        p1_jumps_left = 2

            if not p2_is_hanging:
                p2_y_velocity += GRAVITY
                current_cap = FAST_FALL_SPEED if (keys[pygame.K_k] and p2_y_velocity > 0) else MAX_FALL_SPEED
                if p2_y_velocity > current_cap: p2_y_velocity = current_cap
                p2_y += p2_y_velocity
                p2_rect.y = int(p2_y)

                if p2_y_velocity >= 0 and p2_hitstun == 0 and p2_ledge_cooldown == 0:
                    if p2_rect.colliderect(left_ledge):
                        p2_is_hanging = True
                        p2_x, p2_y = float(left_ledge.x - 15), float(left_ledge.y)
                        p2_y_velocity, p2_kb_x, p2_kb_y = 0.0, 0.0, 0.0
                        p2_jumps_left = 2
                    elif p2_rect.colliderect(right_ledge):
                        p2_is_hanging = True
                        p2_x, p2_y = float(right_ledge.x - 20), float(right_ledge.y)
                        p2_y_velocity, p2_kb_x, p2_kb_y = 0.0, 0.0, 0.0
                        p2_jumps_left = 2

            # Standard Platform Landing Checks
            if p1_rect.colliderect(stage_rect) and p1_y_velocity >= 0:
                p1_rect.bottom = stage_rect.top
                p1_y = float(p1_rect.y)
                p1_y_velocity = 0.0
                p1_jumps_left = 2

            if p2_rect.colliderect(stage_rect) and p2_y_velocity >= 0:
                p2_rect.bottom = stage_rect.top
                p2_y = float(p2_rect.y)
                p2_y_velocity = 0.0
                p2_jumps_left = 2

            # === SYSTEM 1: BLAST ZONE PARAMETERS ===
            DEAD_ZONE_LEFT, DEAD_ZONE_RIGHT = -100, SCREEN_WIDTH + 100
            DEAD_ZONE_BOTTOM, DEAD_ZONE_TOP = SCREEN_HEIGHT + 100, -100

            if p1_rect.x < DEAD_ZONE_LEFT or p1_rect.x > DEAD_ZONE_RIGHT or p1_rect.y > DEAD_ZONE_BOTTOM or (p1_rect.y < DEAD_ZONE_TOP and p1_hitstun > 0):
                p1_stocks -= 1
                p1_damage = 0
                p1_x, p1_y = 440.0, 150.0
                p1_y_velocity, p1_kb_x, p1_kb_y = 0.0, 0.0, 0.0
                p1_is_hanging = False
                p1_invincible_frames = 90

            if p2_rect.x < DEAD_ZONE_LEFT or p2_rect.x > DEAD_ZONE_RIGHT or p2_rect.y > DEAD_ZONE_BOTTOM or (p2_rect.y < DEAD_ZONE_TOP and p2_hitstun > 0):
                p2_stocks -= 1
                p2_damage = 0
                p2_x, p2_y = 790.0, 150.0
                p2_y_velocity, p2_kb_x, p2_kb_y = 0.0, 0.0, 0.0
            # --- COMBAT & ROUND END STATE PROCESSING ---
            if p1_stocks <= 0: 
                game_active = False
                winner_text = "PLAYER 2 WINS!"
            if p2_stocks <= 0: 
                game_active = False
                winner_text = "PLAYER 1 WINS!"

        # 3. Drawing / Rendering
        screen.fill((20, 20, 25))
        pygame.draw.rect(screen, STAGE_COLOR, stage_rect)

        # Draw Player 1 Stun Flashes, Invincibility, or Base Sprite
        if p1_shield_stun > 0 and (p1_shield_stun // 4) % 2 == 0: 
            pygame.draw.rect(screen, (255, 255, 255), p1_rect)
        elif p1_invincible_frames > 0 and (p1_invincible_frames // 4) % 2 == 0: 
            pygame.draw.rect(screen, (255, 215, 0), p1_rect)
        else: 
            pygame.draw.rect(screen, p1_COLOR, p1_rect)

        # Draw Player 2 Stun Flashes, Invincibility, or Base Sprite
        if p2_shield_stun > 0 and (p2_shield_stun // 4) % 2 == 0: 
            pygame.draw.rect(screen, (255, 255, 255), p2_rect)
        elif p2_invincible_frames > 0 and (p2_invincible_frames // 4) % 2 == 0: 
            pygame.draw.rect(screen, (255, 215, 0), p2_rect)
        else: 
            pygame.draw.rect(screen, p2_COLOR, p2_rect)

        # Draw Active Combat Hitboxes
        if p1_hitbox: pygame.draw.rect(screen, (255, 255, 0), p1_hitbox)
        if p2_hitbox: pygame.draw.rect(screen, (255, 255, 0), p2_hitbox)

        # Draw Player 1 Active Shield Ring Matrix
        if p1_is_shielding:
            p1_center = (p1_rect.x + p1_rect.width // 2, p1_rect.y + p1_rect.height // 2)
            pygame.draw.circle(screen, (0, 255, 255), p1_center, int(20 + (25 * (p1_shield_hp / MAX_SHIELD_HP))), 3)

        # Draw Player 2 Active Shield Ring Matrix
        if p2_is_shielding:
            p2_center = (p2_rect.x + p2_rect.width // 2, p2_rect.y + p2_rect.height // 2)
            pygame.draw.circle(screen, (255, 0, 255), p2_center, int(20 + (25 * (p2_shield_hp / MAX_SHIELD_HP))), 3)

        # Render Interface Overlays
        screen.blit(ui_font.render(f"P1 STOCKS: {p1_stocks} | {p1_damage}%", True, (255, 255, 255)), (50, 30))
        screen.blit(ui_font.render(f"{p2_damage}% | P2 STOCKS: {p2_stocks}", True, (255, 255, 255)), (950, 30))

        if not game_active:
            screen.blit(ui_font.render(winner_text, True, (255, 255, 0)), (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50))
            screen.blit(ui_font.render("Press 'R' to Restart Match", True, (150, 150, 150)), (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2))

        pygame.display.flip()
        clock.tick(FPS)
        
        # FIXED: Gives breathing room to the browser window so it never freezes up
        await asyncio.sleep(0) 

# FIXED: Runs the runtime framework logic
asyncio.run(main())

