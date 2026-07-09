import pygame
import sys

# Initialize basic display
pygame.init()

# Setup display window (16:9 widescreen format)
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Velocity Bound")

# Frame rate controller
clock = pygame.time.Clock()
FPS = 60

# --- GAME OBJECTS ---
stage_rect = pygame.Rect(240, 500, 800, 50)
STAGE_COLOR = (70, 70, 80) # Steel gray

# Player 1 Profile (WASD Character)
p1_rect = pygame.Rect(350, 300, 50, 60)
p1_COLOR = (0, 100, 255) # Blue

# Player 2 Profile (IJKL Character)
p2_rect = pygame.Rect(880, 300, 50, 60)
p2_COLOR = (255, 50, 50) # Red

# --- PLAYER VELOCITY CONFIGURATION ---
p1_y_velocity = 0
p2_y_velocity = 0
GRAVITY = 0.5
PLAYER_SPEED = 5
JUMP_POWER = 12

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
p1_has_hit = False # Track if current swing already hit P2
p2_has_hit = False # Track if current swing already hit P1

# Hitbox Dimensions
HITBOX_WIDTH = 45
HITBOX_HEIGHT = 30
p1_hitbox = None
p2_hitbox = None

# Knockback Physics Forces
p1_kb_x = 0
p2_kb_x = 0
KNOCKBACK_DECAY = 0.88 # Smoother flight sliding deceleration curve
KNOCKBACK_force = 12 # Standardized base launching force

# --- DAMAGE & STOCK TRACKING ---
p1_stocks = 3
p2_stocks = 3
p1_damage = 0
p2_damage = 0

# UI Font Setup
ui_font = pygame.font.SysFont("Arial", 28)

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
            sys.exit()
            
        if event.type == pygame.KEYDOWN:
            # Check for instant round reset button
            if event.key == pygame.K_r:
                p1_stocks = 3
                p2_stocks = 3
                p1_damage = 0
                p2_damage = 0
                p1_x = 350.0
                p1_rect.y = 300
                p2_x = 880.0
                p2_rect.y = 300
                p1_kb_x = 0.0
                p2_kb_x = 0.0
                p1_y_velocity = 0
                p2_y_velocity = 0
                p1_jumps_left = 2
                p2_jumps_left = 2
                p1_attack_frames = 0
                p2_attack_frames = 0
                p1_has_hit = False
                p2_has_hit = False
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
                if event.key == pygame.K_w and p1_jumps_left > 0:
                    p1_y_velocity = -JUMP_POWER
                    p1_jumps_left -= 1
                    
                if event.key == pygame.K_i and p2_jumps_left > 0:
                    p2_y_velocity = -JUMP_POWER
                    p2_jumps_left -= 1
                    
                if event.key == pygame.K_f and p1_attack_frames == 0:
                    p1_attack_frames = ATTACK_DURATION
                    p1_has_hit = False
                    
                if event.key == pygame.K_h and p2_attack_frames == 0:
                    p2_attack_frames = ATTACK_DURATION
                    p2_has_hit = False

    # 2. Game Logic Updates
    keys = pygame.key.get_pressed()
    
    if game_active:
        if p1_invincible_frames > 0:
            p1_invincible_frames -= 1
        if p2_invincible_frames > 0:
            p2_invincible_frames -= 1

        # === PLAYER 1 SHIELD, STUN, & MOVEMENT ===
        if p1_shield_stun > 0:
            p1_shield_stun -= 1
            p1_is_shielding = False
        elif p1_hitstun > 0:
            p1_hitstun -= 1
            p1_is_shielding = False
        elif keys[pygame.K_s] and p1_shield_hp > 0:
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

        # P1 Movement Control
        if not p1_is_shielding and p1_shield_stun == 0 and p1_hitstun == 0:
            if keys[pygame.K_a]:
                p1_x -= PLAYER_SPEED
                p1_facing = -1
            if keys[pygame.K_d]:
                p1_x += PLAYER_SPEED
                p1_facing = 1

        # === PLAYER 2 SHIELD, STUN, & MOVEMENT ===
        if p2_shield_stun > 0:
            p2_shield_stun -= 1
            p2_is_shielding = False
        elif p2_hitstun > 0:
            p2_hitstun -= 1
            p2_is_shielding = False
        elif keys[pygame.K_k] and p2_shield_hp > 0:
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

        # P2 Movement Control
        if not p2_is_shielding and p2_shield_stun == 0 and p2_hitstun == 0:
            if keys[pygame.K_j]:
                p2_x -= PLAYER_SPEED
                p2_facing = -1
            if keys[pygame.K_l]:
                p2_x += PLAYER_SPEED
                p2_facing = 1

        # Write positions to hitboxes
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
            p2_y_velocity = -7
            p1_has_hit = True
            p2_hitstun = int(abs(p2_kb_x) * 0.75)

        if p2_hitbox and p2_hitbox.colliderect(p1_rect) and not p2_has_hit and p1_invincible_frames == 0:
            p1_damage += 12
            p1_kb_x = float((KNOCKBACK_force + (p1_damage // 2)) * p2_facing)
            p1_y_velocity = -7
            p2_has_hit = True
            p1_hitstun = int(abs(p1_kb_x) * 0.75)

        # --- STEP 4: APPLY AND DECAY ACTIVE KNOCKBACK FORCES ---
        p1_x += p1_kb_x
        p2_x += p2_kb_x
        p1_kb_x *= KNOCKBACK_DECAY
        p2_kb_x *= KNOCKBACK_DECAY
        if abs(p1_kb_x) < 0.1: p1_kb_x = 0.0
        if abs(p2_kb_x) < 0.1: p2_kb_x = 0.0

        # Sync floats to rects before collision check
        p1_rect.x = int(p1_x)
        p2_rect.x = int(p2_x)

        # --- STEP 5: PERMANENT SOLIDITY ENGINE ---
        if p1_rect.colliderect(p2_rect):
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
            p1_rect.x = int(p1_x)
            p2_rect.x = int(p2_x)

        # --- STEP 6: VERTICAL PHYSICS & FLOOR DETECTION ---
        p1_y_velocity += GRAVITY
        p2_y_velocity += GRAVITY
        p1_rect.y += int(p1_y_velocity)
        p2_rect.y += int(p2_y_velocity)

        if p1_rect.colliderect(stage_rect):
            p1_rect.bottom = stage_rect.top
            p1_y_velocity = 0
            p1_jumps_left = 2
        if p2_rect.colliderect(stage_rect):
            p2_rect.bottom = stage_rect.top
            p2_y_velocity = 0
            p2_jumps_left = 2

        # --- BLAST ZONE & RESPAWN DETECTION LOOP ---
        DEAD_ZONE_LEFT = -100
        DEAD_ZONE_RIGHT = SCREEN_WIDTH + 100
        DEAD_ZONE_BOTTOM = SCREEN_HEIGHT + 100
        DEAD_ZONE_TOP = -100

        if p1_rect.x < DEAD_ZONE_LEFT or p1_rect.x > DEAD_ZONE_RIGHT or p1_rect.y > DEAD_ZONE_BOTTOM or p1_rect.y < DEAD_ZONE_TOP:
            p1_stocks -= 1
            p1_damage = 0
            p1_x = 440.0
            p1_rect.y = 150
            p1_y_velocity = 0
            p1_kb_x = 0.0
            p1_invincible_frames = 90

        if p2_rect.x < DEAD_ZONE_LEFT or p2_rect.x > DEAD_ZONE_RIGHT or p2_rect.y > DEAD_ZONE_BOTTOM or p2_rect.y < DEAD_ZONE_TOP:
            p2_stocks -= 1
            p2_damage = 0
            p2_x = 790.0
            p2_rect.y = 150
            p2_y_velocity = 0
            p2_kb_x = 0.0
            p2_invincible_frames = 90

        if p1_stocks <= 0:
            game_active = False
            winner_text = "PLAYER 2 WINS!"
        if p2_stocks <= 0:
            game_active = False
            winner_text = "PLAYER 1 WINS!"

    # 3. Drawing / Rendering
    screen.fill((20, 20, 25))
    pygame.draw.rect(screen, STAGE_COLOR, stage_rect)

    if p1_shield_stun > 0 and (p1_shield_stun // 4) % 2 == 0:
        pygame.draw.rect(screen, (255, 255, 255), p1_rect)
    elif p1_invincible_frames > 0 and (p1_invincible_frames // 4) % 2 == 0:
        pygame.draw.rect(screen, (255, 215, 0), p1_rect)
    else:
        pygame.draw.rect(screen, p1_COLOR, p1_rect)

    if p2_shield_stun > 0 and (p2_shield_stun // 4) % 2 == 0:
        pygame.draw.rect(screen, (255, 255, 255), p2_rect)
    elif p2_invincible_frames > 0 and (p2_invincible_frames // 4) % 2 == 0:
        pygame.draw.rect(screen, (255, 215, 0), p2_rect)
    else:
        pygame.draw.rect(screen, p2_COLOR, p2_rect)

    if p1_hitbox:
        pygame.draw.rect(screen, (255, 255, 0), p1_hitbox)
    if p2_hitbox:
        pygame.draw.rect(screen, (255, 255, 0), p2_hitbox)

    if p1_is_shielding:
        p1_center = (p1_rect.x + p1_rect.width // 2, p1_rect.y + p1_rect.height // 2)
        p1_dynamic_radius = int(20 + (25 * (p1_shield_hp / MAX_SHIELD_HP)))
        pygame.draw.circle(screen, (0, 255, 255), p1_center, p1_dynamic_radius, 3)

    if p2_is_shielding:
        p2_center = (p2_rect.x + p2_rect.width // 2, p2_rect.y + p2_rect.height // 2)
        p2_dynamic_radius = int(20 + (25 * (p2_shield_hp / MAX_SHIELD_HP)))
        pygame.draw.circle(screen, (255, 0, 255), p2_center, p2_dynamic_radius, 3)

    p1_stock_text = ui_font.render(f"P1 STOCKS: {p1_stocks} | {p1_damage}%", True, (255, 255, 255))
    p2_stock_text = ui_font.render(f"{p2_damage}% | P2 STOCKS: {p2_stocks}", True, (255, 255, 255))
    screen.blit(p1_stock_text, (50, 30))
    screen.blit(p2_stock_text, (950, 30))

    if not game_active:
        end_surface = ui_font.render(winner_text, True, (255, 255, 0))
        reset_tip_surface = ui_font.render("Press 'R' to Restart Match", True, (150, 150, 150))
        screen.blit(end_surface, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50))
        screen.blit(reset_tip_surface, (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2))

    pygame.display.flip()
    clock.tick(FPS)
