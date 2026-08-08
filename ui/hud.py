import pygame
from settings import *


def draw(screen, ui_font, p1, p2, p1_hitbox, p2_hitbox, stage_rect, game_active, winner_text):
    screen.fill((20, 20, 25))
    pygame.draw.rect(screen, STAGE_COLOR, stage_rect)

    def draw_player_effect(player, color, spin_color):
        # Draw slam particles underneath player (so they appear at feet)
        for part in getattr(player, 'slam_particles', []):
            life = part['life']
            alpha = max(40, min(200, int(255 * (life / 26.0))))
            surf = pygame.Surface((6, 6), pygame.SRCALPHA)
            surf.fill((120, 100, 80, alpha))
            screen.blit(surf, (int(part['x']) - 3, int(part['y']) - 3))

        def draw_shape(surface, body_color, origin_x=0, origin_y=0):
            cx = player.rect.centerx - origin_x
            top = player.rect.y - origin_y

            if PLAYER_DRAW_PLACEHOLDER:
                head_radius = 14
                head_center = (cx, top + head_radius)
                body_rect = pygame.Rect(cx - 18, top + 28, player.rect.width - 36, player.rect.height - 40)
                pygame.draw.rect(surface, body_color, body_rect, border_radius=10)
                pygame.draw.circle(surface, body_color, head_center, head_radius)
                return

            head_radius = 14
            head_center = (cx, top + head_radius)
            neck = (cx, top + 28)
            pelvis = (cx, top + 70)

            left_elbow_center = (cx - 24, top + 42)
            left_hand = (cx - 32, top + 58)
            right_elbow_center = (cx + 24, top + 42)
            right_hand = (cx + 32, top + 58)

            left_knee = (cx - 16, top + 95)
            left_foot = (cx - 20, top + 120)
            right_knee = (cx + 16, top + 95)
            right_foot = (cx + 20, top + 120)

            line_thickness = 4
            elbow_radius = 4
            joint_radius = 6

            pygame.draw.line(surface, body_color, neck, pelvis, line_thickness)
            pygame.draw.line(surface, body_color, neck, left_elbow_center, line_thickness)
            pygame.draw.line(surface, body_color, left_elbow_center, left_hand, line_thickness)
            pygame.draw.line(surface, body_color, neck, right_elbow_center, line_thickness)
            pygame.draw.line(surface, body_color, right_elbow_center, right_hand, line_thickness)
            pygame.draw.line(surface, body_color, pelvis, left_knee, line_thickness)
            pygame.draw.line(surface, body_color, left_knee, left_foot, line_thickness)
            pygame.draw.line(surface, body_color, pelvis, right_knee, line_thickness)
            pygame.draw.line(surface, body_color, right_knee, right_foot, line_thickness)

            pygame.draw.circle(surface, body_color, head_center, head_radius, line_thickness)

            pygame.draw.circle(surface, body_color, left_elbow_center, elbow_radius)
            pygame.draw.circle(surface, body_color, right_elbow_center, elbow_radius)
            for joint in [left_hand, right_hand, left_foot, right_foot]:
                pygame.draw.circle(surface, body_color, joint, joint_radius)

        # If prone (lying on stomach), draw a flatter silhouette.
        if getattr(player, 'prone', False):
            stomach = pygame.Rect(player.rect.x + 10, player.rect.bottom - 16, player.rect.width - 20, 12)
            pygame.draw.rect(screen, (max(0, color[0] - 30), max(0, color[1] - 30), max(0, color[2] - 30)), stomach)
            pygame.draw.circle(screen, color, (player.rect.centerx, player.rect.bottom - 18), 6)
            return

        if getattr(player, 'is_spinning', False) and getattr(player, 'spin_frames', 0) > 0:
            pulse = 180 + (player.spin_frames % 2) * 40
            hue = (spin_color[0], min(255, spin_color[1] + pulse // 2), min(255, spin_color[2] + pulse // 3))
            w, h = player.rect.size
            tmp = pygame.Surface((w, h), pygame.SRCALPHA)
            tmp_rect = tmp.get_rect()
            draw_shape(tmp, hue, player.rect.x, player.rect.y)
            angle = getattr(player, 'spin_angle', 0.0)
            rotated = pygame.transform.rotate(tmp, angle)
            rx = player.rect.centerx - rotated.get_width() // 2
            ry = player.rect.centery - rotated.get_height() // 2
            screen.blit(rotated, (rx, ry))
            pygame.draw.circle(screen, (255, 255, 255), player.rect.center, player.rect.width // 2 + 6, 2)
        elif player.shield_stun > 0 and (player.shield_stun // 4) % 2 == 0:
            draw_shape(screen, (255, 255, 255))
        elif player.invincible_frames > 0 and (player.invincible_frames // 4) % 2 == 0:
            draw_shape(screen, (255, 215, 0))
        else:
            draw_shape(screen, color)

    draw_player_effect(p1, P1_COLOR, (255, 120, 40))
    draw_player_effect(p2, P2_COLOR, (200, 50, 255))

    if p1_hitbox:
        # Draw active attack hitboxes in yellow so you can see spacing.
        pygame.draw.rect(screen, (255, 255, 0), p1_hitbox)
        if getattr(p1, 'current_attack', None) and getattr(p1, 'attack_frames', 0) > 0:
            name_surf = ui_font.render(p1.current_attack.get('name', ''), True, (255, 255, 255))
            screen.blit(name_surf, (p1_hitbox.x, max(0, p1_hitbox.y - 22)))
    if p2_hitbox:
        pygame.draw.rect(screen, (255, 255, 0), p2_hitbox)
        if getattr(p2, 'current_attack', None) and getattr(p2, 'attack_frames', 0) > 0:
            name_surf = ui_font.render(p2.current_attack.get('name', ''), True, (255, 255, 255))
            screen.blit(name_surf, (p2_hitbox.x, max(0, p2_hitbox.y - 22)))

    if p1.is_shielding:
        # Draw a shield bubble around player 1 to show block state.
        p1_center = (p1.rect.x + p1.rect.width // 2, p1.rect.y + p1.rect.height // 2)
        pygame.draw.circle(screen, (0, 255, 255), p1_center, int(20 + (25 * (p1.shield_hp / MAX_SHIELD_HP))), 3)

    if p2.is_shielding:
        # Draw a shield bubble around player 2 to show block state.
        p2_center = (p2.rect.x + p2.rect.width // 2, p2.rect.y + p2.rect.height // 2)
        pygame.draw.circle(screen, (255, 0, 255), p2_center, int(20 + (25 * (p2.shield_hp / MAX_SHIELD_HP))), 3)

    screen.blit(ui_font.render(f"P1 STOCKS: {p1.stocks} | {p1.damage}%", True, (255, 255, 255)), (50, 30))
    screen.blit(ui_font.render(f"{p2.damage}% | P2 STOCKS: {p2.stocks}", True, (255, 255, 255)), (950, 30))

    # Show current attack names above player rects while active
    if getattr(p1, 'current_attack', None) and getattr(p1, 'attack_frames', 0) > 0:
        a = p1.current_attack.get('name', '')
        screen.blit(ui_font.render(a, True, (200, 200, 255)), (p1.rect.x, max(0, p1.rect.y - 20)))
    if getattr(p2, 'current_attack', None) and getattr(p2, 'attack_frames', 0) > 0:
        a = p2.current_attack.get('name', '')
        screen.blit(ui_font.render(a, True, (200, 200, 255)), (p2.rect.x, max(0, p2.rect.y - 20)))

    if not game_active:
        screen.blit(ui_font.render(winner_text, True, (255, 255, 0)), (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50))
        screen.blit(ui_font.render("Press 'R' to Restart Match", True, (150, 150, 150)), (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2))

    pygame.display.flip()
