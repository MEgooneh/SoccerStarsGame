import pygame
import numpy as np

from .Player import Player, GoalKeeper, Defender, Striker, Side
from .Ball import Ball
from .Object import Object
import settings
from .Models import ObjectModel, MouseModel, BoardUpdate
from .Mouse import Mouse

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .Game import Game 

class Board:

    def __init__(self, game):
        self.game: Game = game
        self.mouse = Mouse(self.game)
        self.ball: Ball = None
        self.left_goalkeeper: GoalKeeper = None
        self.left_defenders: list[Defender] = []
        self.left_strikers: list[Striker] = []
        self.right_goalkeeper: GoalKeeper = None
        self.right_defenders: list[Defender] = []
        self.right_strikers: list[Striker] = []

    @property
    def left_players(self) -> list[Player]:
        return self.left_strikers + self.left_defenders + [self.left_goalkeeper]

    @property
    def right_players(self) -> list[Player]:
        return self.right_strikers + self.right_defenders + [self.right_goalkeeper]

    @property
    def all_players(self) -> list[Player]:
        return self.left_players + self.right_players
    
    @property
    def all_objects(self) -> list[Object]:
        return self.all_players + [self.ball]
    
    def init_screen(self):
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))

    def init_ball(self):
        middle_of_screen_position = np.array([
            (settings.PITCH_LEFT_BORDER + settings.PITCH_RIGHT_BORDER) // 2,
            (settings.PITCH_UP_BORDER + settings.PITCH_DOWN_BORDER) // 2
        ])
        ball = Ball(game=self.game, pos=middle_of_screen_position, velocity=np.zeros((2), dtype=np.longdouble))
        self.ball = ball

    def create_defenders_list(self, side: Side, coordinates: list):
        defenders = []
        for cor in coordinates:
            defender = Defender(
                game=self.game,
                side=side,
                pos=np.array(cor)
            )
            defenders.append(defender)
        return defenders
    
    def create_strikers_list(self, side: Side, coordinates: list):
        strikers = []
        for cor in coordinates:
            striker = Striker(
                game=self.game,
                side=side,
                pos=np.array(cor)
            )
            strikers.append(striker)
        return strikers

    def init_players(self):
        left_coordinates = settings.LEFT_SIDE_COORDINATES
        self.left_goalkeeper = GoalKeeper(
                game=self.game,
                side=Side.RED,
                pos=np.array(left_coordinates["goalkeeper"]),
            )
        self.left_defenders = self.create_defenders_list(Side.RED, left_coordinates["defenders"])
        self.left_strikers = self.create_strikers_list(Side.RED, left_coordinates["strikers"])

        right_coordinates = settings.RIGHT_SIDE_COORDINATES
        self.right_goalkeeper = GoalKeeper(
                game=self.game,
                side=Side.BLUE,
                pos=np.array(right_coordinates["goalkeeper"]),
            )
        self.right_defenders = self.create_defenders_list(Side.BLUE, right_coordinates["defenders"])
        self.right_strikers = self.create_strikers_list(Side.BLUE, right_coordinates["strikers"])
        
    def init_objects(self):
        self.init_ball()
        self.init_players()

    def reset_players_state(self):
        left_coordinates = settings.LEFT_SIDE_COORDINATES
        self.left_goalkeeper.pos = np.array(left_coordinates["goalkeeper"])
        self.left_goalkeeper.velocity = np.zeros((2), dtype=np.longdouble)
        for defender, cor in zip(self.left_defenders, left_coordinates["defenders"]):
            defender.pos = np.array(cor)
            defender.velocity = np.zeros((2), dtype=np.longdouble)
        for striker, cor in zip(self.left_strikers, left_coordinates["strikers"]):
            striker.pos = np.array(cor)
            striker.velocity = np.zeros((2), dtype=np.longdouble)

        right_coordinates = settings.RIGHT_SIDE_COORDINATES
        self.right_goalkeeper.pos = np.array(right_coordinates["goalkeeper"])
        self.right_goalkeeper.velocity = np.zeros((2), dtype=np.longdouble)
        for defender, cor in zip(self.right_defenders, right_coordinates["defenders"]):
            defender.pos = np.array(cor)
            defender.velocity = np.zeros((2), dtype=np.longdouble)
        for striker, cor in zip(self.right_strikers, right_coordinates["strikers"]):
            striker.pos = np.array(cor)
            striker.velocity = np.zeros((2), dtype=np.longdouble)
        
    def reset_ball_state(self):
        middle_of_screen_position = np.array([
            (settings.PITCH_LEFT_BORDER + settings.PITCH_RIGHT_BORDER) // 2,
            (settings.PITCH_UP_BORDER + settings.PITCH_DOWN_BORDER) // 2
        ])
        self.ball.pos = np.array(middle_of_screen_position)
        self.ball.velocity = np.zeros((2), dtype=np.longdouble)

    def reset_board_state(self):
        self.reset_ball_state()
        self.reset_players_state()

    def is_idle(self) -> bool:
        for obj in self.all_objects:
            if obj.velocity.any():
                return False
        return True

    def which_side_scored(self) -> Side | None:       
        if self.ball.is_completely_in_left_goal():
            return Side.BLUE
        elif self.ball.is_completely_in_right_goal():
            return Side.RED
        return None

    def is_goal_opened(self) -> bool:
        return self.which_side_scored() is not None

    def draw_objects(self, objects: list[Object]):
        for object in objects:
            object.draw(self.screen)

    def draw_goals(self):
        self.screen.blit(self.game.media.goals_transparent_image, (0, 0))

    def show_screen(self):
        self.screen.blit(self.game.media.pitch_image, (0, 0))

    def show_goal_ceremony(self):
        gif = self.game.media.goal_ceremony_gif
        end_time = self.game.rules_freezed_for_ceremony_finish_time
        self.game.media.play_gif(gif, end_time, self.screen)
        
    def show_winner_ceremony(self, winner):
        if winner == Side.RED:
            gif = self.game.media.red_winning_ceremony_gif
        elif winner == Side.BLUE:
            gif = self.game.media.blue_winning_ceremony_gif
        else:
            raise Exception("winner is None. can't play winner ceremony")
        
        end_time = self.game.rules_freezed_for_ceremony_finish_time
        self.game.media.play_gif(gif, end_time, self.screen)

    def show_names(self):
        red_name = self.game.left_side_name
        red_name_surface = self.game.media.font.render(red_name, True, "grey")
        red_name_rect = red_name_surface.get_rect(center=settings.SCOREBAR_PLACE_RED_NAME)
        self.screen.blit(red_name_surface, red_name_rect)

        blue_name = self.game.right_side_name
        blue_name_surface = self.game.media.font.render(blue_name, True, "grey")
        blue_name_rect = blue_name_surface.get_rect(center=settings.SCOREBAR_PLACE_BLUE_NAME)
        self.screen.blit(blue_name_surface, blue_name_rect)

    def show_scores(self):
        red_score = str(self.game.scores[Side.RED])
        red_score_surface = self.game.media.large_font.render(red_score, True, "white")
        red_score_rect = red_score_surface.get_rect(center=settings.SCOREBAR_PLACE_RED_SCORE)
        self.screen.blit(red_score_surface, red_score_rect)

        blue_score = str(self.game.scores[Side.BLUE])
        blue_score_surface = self.game.media.large_font.render(blue_score, True, "white")
        blue_score_rect = blue_score_surface.get_rect(center=settings.SCOREBAR_PLACE_BLUE_SCORE)
        self.screen.blit(blue_score_surface, blue_score_rect)

    def show_timer(self):
        remained_seconds = self.game.turn_last_second - pygame.time.get_ticks()//1000
        minutes = str(remained_seconds // 60).zfill(2)
        seconds = str(remained_seconds % 60).zfill(2)
        surface = self.game.media.font.render(f"{minutes}:{seconds}", True, "white")
        rect = surface.get_rect(center=settings.TIMER_COORDINATES)
        self.screen.blit(surface, rect)

    def show_scoreboard(self):
        self.show_scores()
        self.show_names()

    def dump_board(self) -> BoardUpdate:
        mouse = self.mouse.dump_mouse()
        objects = []
        for obj in self.all_objects:
            objects.append(obj.dump_object())
        return BoardUpdate(mouse=mouse, objects=objects)
    
    def load_board(self, board: BoardUpdate):
        self.mouse.load_mouse(board.mouse)
        for obj in board.objects:
            Object.objects_list[obj.id].load_object(obj)


    



