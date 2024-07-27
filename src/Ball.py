import pygame
import numpy as np
from typing import TYPE_CHECKING

from .Object import Object
import settings

if TYPE_CHECKING:
    from .Game import Game

class Ball(Object):

    MASS = 1
    RADIUS = 15

    def __init__(self, game:'Game', pos: np.ndarray, velocity: np.ndarray):
        super().__init__(game, Ball.MASS, Ball.RADIUS, pos, velocity)
    
    def draw(self, screen: pygame.Surface):
        image = self.game.media.ball_image
        image_rect = image.get_rect(center=self.pos)

        screen.blit(image, image_rect.topleft)

    def collision_object_play_sound(self, other=None):
        super().collision_object_play_sound(other)
        velocity_percantage_sound_volume = 0

        if other:
            velocity_percantage_sound_volume = np.linalg.norm(self.velocity - other.velocity)**2 / (2*settings.PITCH_WIDTH)**2

        else:
            velocity_percantage_sound_volume = np.linalg.norm(self.velocity)**2 / (settings.PITCH_WIDTH)**2

        if velocity_percantage_sound_volume:
            self.game.media.ball_kick_sound.set_volume(min(0.8, velocity_percantage_sound_volume))
            self.game.media.ball_kick_sound.play()
    
    def __repr__(self):
        return f"Ball(pos={self.pos}, velocity={self.velocity})"
