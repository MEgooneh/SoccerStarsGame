import numpy as np
import pygame

from .SocketClient import SocketClient
from .Models import MouseModel, MouseStatus, MousePosition
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Game import Game
    from .Models import MouseUpdate



class Mouse:
    def __init__(self, game, socket):
        self.game: Game = game
        self.socket: SocketClient = socket

    def is_my_mouse_click_down(self) -> bool:
        ls = pygame.event.get(pygame.MOUSEBUTTONDOWN)
        return bool(ls)

    def is_my_mouse_click_up(self) -> bool:
        ls = pygame.event.get(pygame.MOUSEBUTTONUP)
        return bool(ls)

    def is_my_mouse_click_hold(self) -> bool:
        ls = pygame.mouse.get_pressed()
        return bool(ls[0])

    def get_my_mouse(self) -> MouseModel:
        x, y = pygame.mouse.get_pos()
        status = MouseStatus.IDLE
        if self.is_my_mouse_click_down():
            status = MouseStatus.CLICK_DOWN
        elif self.is_my_mouse_click_up():
            status = MouseStatus.CLICK_UP
        elif self.is_my_mouse_click_hold():
            status = MouseStatus.CLICK_HOLD
        return MouseModel(pos=MousePosition(x=x, y=y), status=status)
    
    def get_opponent_mouse(self) -> MouseModel:
        mouse_update: MouseUpdate = self.socket.get_opponent_mouse_update()
        return mouse_update.mouse

    def get_mouse_in_multiplayer_game(self) -> MouseModel:
        if self.game.turn == self.socket.side:
            return self.get_my_mouse()
        elif self.socket.side and self.game.turn != self.socket.side:
            return self.get_opponent_mouse()
        else:
            return MouseModel()

    def get_mouse(self) -> MouseModel:
        if self.game.is_multiplayer:
            return self.get_mouse_in_multiplayer_game()
        else:
            return self.get_my_mouse()

