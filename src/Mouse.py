import numpy as np
import pygame

from .SocketClient import SocketClient
from .Models import MouseModel, MouseStatus, Position
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Game import Game



class Mouse:
    def __init__(self, game):
        self.game: Game = game
        self.socket: SocketClient = self.game.socket
        self.pos = np.zeros((2))
        self.status = MouseStatus.IDLE
    
    def is_my_mouse_click_down(self) -> bool:
        ls = pygame.event.get(pygame.MOUSEBUTTONDOWN)
        return bool(ls)

    def is_my_mouse_click_up(self) -> bool:
        ls = pygame.event.get(pygame.MOUSEBUTTONUP)
        return bool(ls)

    def is_my_mouse_click_hold(self) -> bool:
        ls = pygame.mouse.get_pressed()
        return bool(ls[0])

    def is_click_down(self):
        return self.status == MouseStatus.CLICK_DOWN

    def is_click_up(self):
        return self.status == MouseStatus.CLICK_UP
    
    def is_click_hold(self):
        return self.status == MouseStatus.CLICK_HOLD
    
    def is_idle(self):
        return self.status == MouseStatus.IDLE

    def get_pos(self):
        return self.pos

    def update_my_mouse(self):
        x, y = pygame.mouse.get_pos()
        status = MouseStatus.IDLE
        if self.is_my_mouse_click_down():
            status = MouseStatus.CLICK_DOWN
        elif self.is_my_mouse_click_up():
            status = MouseStatus.CLICK_UP
        elif self.is_my_mouse_click_hold():
            status = MouseStatus.CLICK_HOLD

        self.pos = np.array((x, y), dtype=int)
        self.status = status

    def update(self):
        self.update_my_mouse()

    def load_mouse(self, mouse_model: MouseModel):
        self.pos = mouse_model.pos.to_ndarray()
        self.status = mouse_model.status


    def dump_mouse(self) -> MouseModel:
        return MouseModel(pos=Position(x=self.pos[0], y=self.pos[1]), status=self.status)