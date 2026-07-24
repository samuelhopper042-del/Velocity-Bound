import pygame


def create_stage():
    # Build the main platform and small ledge-grab zones at each edge.
    stage_rect = pygame.Rect(240, 500, 800, 50)
    LEDGE_WIDTH, LEDGE_HEIGHT = 10, 6

    # The ledge grab rectangles are narrow and positioned slightly below the top
    # edge of the platform. They are used by the ledge grab logic in physics.
    ledge_y = stage_rect.top + 8
    left_ledge = pygame.Rect(stage_rect.left - 5, ledge_y, LEDGE_WIDTH, LEDGE_HEIGHT)
    right_ledge = pygame.Rect(stage_rect.right - 5, ledge_y, LEDGE_WIDTH, LEDGE_HEIGHT)

    # Return the stage outline and the two grab zones for the physics system.
    return stage_rect, left_ledge, right_ledge
