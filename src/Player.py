import pygame
import numpy as np

from typing import TYPE_CHECKING
from enum import Enum

from .Object import Object
import settings


if TYPE_CHECKING:
    from .Game import Game

class Side(Enum):
    RED = 1
    BLUE = 2

class Player(Object):

    def __init__(self, game:'Game', mass:float, radius:float, side: Side, pos: np.ndarray, velocity: np.ndarray):
        super().__init__(game, mass, radius, pos, velocity)
        self.side = side
    

    def is_activated(self):
        return self.game.turn == self.side and self.game.board.is_idle()

    def draw(self, screen: pygame.Surface):
        ...
    
    def collision_object_play_sound(self, other=None):
        velocity_percantage_sound_volume = 0

        if isinstance(other, __class__):
            velocity_percantage_sound_volume = np.linalg.norm(self.velocity - other.velocity) / (settings.PITCH_HEIGHT + settings.PITCH_WIDTH)

        elif other is None:
            velocity_percantage_sound_volume = np.linalg.norm(self.velocity) / (settings.PITCH_WIDTH)

        if velocity_percantage_sound_volume:
            self.game.media.player_collision_sound.set_volume(velocity_percantage_sound_volume)
            self.game.media.player_collision_sound.play()

    def __repr__(self) -> str:
        return (f"Player(side={self.side}, mass={self.mass}, radius={self.radius}, "
                f"pos={self.pos}, velocity={self.velocity})")

class GoalKeeper(Player):

    MASS = 2
    RADIUS = 30
    def __init__(self, game:'Game', side: Side, pos: np.ndarray, velocity: np.ndarray = np.zeros((2))):
        super().__init__(game, GoalKeeper.MASS, GoalKeeper.RADIUS, side, pos, velocity)

    def keep_goalkeeper_in_penalty_area(self):
        if self.side == Side.RED:
            self.pos[0] = min(self.pos[0], settings.LEFTSIDE_PENALTY_AREA_RIGHT_BORDER)
        elif self.side == Side.BLUE:
            self.pos[0] = max(self.pos[0], settings.RIGHTSIDE_PENALTY_AREA_LEFT_BORDER)

        self.pos[1] = max(settings.PENALTY_AREA_UP_BORDER + self.radius, self.pos[1])
        self.pos[1] = min(settings.PENALTY_AREA_DOWN_BORDER-self.radius, self.pos[1])


    def draw(self, screen: pygame.Surface):
        image = None
        if self.side == Side.BLUE:
            if self.is_activated():
                image = self.game.media.blue_goalkeeper_activated_image
            else:
                image = self.game.media.blue_goalkeeper_image
        elif self.side == Side.RED:
            if self.is_activated():
                image = self.game.media.red_goalkeeper_activated_image
            else:
                image = self.game.media.red_goalkeeper_image

        image_rect = image.get_rect(center=tuple(self.pos))
        

        screen.blit(image, image_rect.topleft)

    def __repr__(self) -> str:
        return (f"GoalKeeper(side={self.side}, mass={self.mass}, radius={self.radius}, "
                f"pos={self.pos}, velocity={self.velocity})")
        

class Defender(Player):

    MASS = 3
    RADIUS = 35
    def __init__(self, game:'Game', side: Side, pos: np.ndarray, velocity: np.ndarray = np.zeros((2))):
        super().__init__(game, Defender.MASS, Defender.RADIUS, side, pos, velocity)

    def draw(self, screen: pygame.Surface):
        image = None
        if self.side == Side.BLUE:
            if self.is_activated():
                image = self.game.media.blue_defender_activated_image
            else:
                image = self.game.media.blue_defender_image
        elif self.side == Side.RED:
            if self.is_activated():
                image = self.game.media.red_defender_activated_image
            else:
                image = self.game.media.red_defender_image

        image_rect = image.get_rect(center=tuple(self.pos))

        screen.blit(image, image_rect.topleft)

    def __repr__(self) -> str:
        return (f"Defender(side={self.side}, mass={self.mass}, radius={self.radius}, "
                f"pos={self.pos}, velocity={self.velocity})")
    
class Striker(Player):

    MASS = 1.5
    RADIUS = 30
    def __init__(self, game:'Game', side: Side, pos: np.ndarray, velocity: np.ndarray=np.zeros((2))):
        super().__init__(game, Striker.MASS, Striker.RADIUS, side, pos, velocity)

    def draw(self, screen: pygame.Surface):
        image = None
        if self.side == Side.BLUE:
            if self.is_activated():
                image = self.game.media.blue_striker_activated_image
            else:
                image = self.game.media.blue_striker_image
        elif self.side == Side.RED:
            if self.is_activated():
                image = self.game.media.red_striker_activated_image
            else:
                image = self.game.media.red_striker_image

        image_rect = image.get_rect(center=tuple(self.pos))

        screen.blit(image, image_rect.topleft)

    def __repr__(self) -> str:
        return (f"Striker(side={self.side}, mass={self.mass}, radius={self.radius}, "
                f"pos={self.pos}, velocity={self.velocity})")