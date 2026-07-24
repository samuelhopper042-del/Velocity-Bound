import os
import pygame

pygame.init()

output_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "characters")
os.makedirs(output_dir, exist_ok=True)

surf = pygame.Surface((72, 120), pygame.SRCALPHA)
surf.fill((0, 0, 0, 0))

# torso
pygame.draw.rect(surf, (150, 100, 50), (18, 36, 36, 64), border_radius=12)
# legs
pygame.draw.rect(surf, (110, 70, 40), (18, 100, 14, 18), border_radius=6)
pygame.draw.rect(surf, (110, 70, 40), (40, 100, 14, 18), border_radius=6)
# boots
pygame.draw.rect(surf, (60, 30, 20), (18, 114, 14, 6))
pygame.draw.rect(surf, (60, 30, 20), (40, 114, 14, 6))
# arms
pygame.draw.rect(surf, (150, 100, 50), (4, 42, 18, 12), border_radius=8)
pygame.draw.rect(surf, (150, 100, 50), (50, 42, 18, 12), border_radius=8)
# hat
pygame.draw.ellipse(surf, (90, 55, 25), (8, 0, 56, 18))
pygame.draw.rect(surf, (100, 60, 30), (22, 6, 28, 18), border_radius=8)
# face
pygame.draw.circle(surf, (220, 180, 140), (36, 30), 12)
pygame.draw.circle(surf, (0, 0, 0), (30, 28), 2)
pygame.draw.circle(surf, (0, 0, 0), (42, 28), 2)
pygame.draw.line(surf, (110, 70, 40), (30, 36), (42, 36), 2)
# belt
pygame.draw.rect(surf, (80, 50, 30), (18, 70, 36, 10), border_radius=6)
# badge
pygame.draw.circle(surf, (220, 210, 120), (36, 76), 5)

filename = os.path.join(output_dir, "p1.png")
pygame.image.save(surf, filename)
print(f"Created asset: {filename}")
