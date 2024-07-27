import pygame
import numpy as np

from .Board import Board
from .Player import Side, GoalKeeper, Defender, Striker
from .Media import MediaLoader
import settings

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .Player import Player
    from .Ball import Ball

class Game:

    FIRST_TURN = Side.RED
    DT = 15

    def pygame_init(self):
        pygame.init()
        pygame.mixer.init()
        pygame.font.init()
        self.clock = pygame.time.Clock()
        self.board.init_screen()

    def pygame_quit(self):
        pygame.quit()

    def load_assets(self):
        self.media = MediaLoader()
        self.media.load_assets()


    __singleton = False
    def __init__(self):
        if Game.__singleton:
            raise "Game is singleton, more than one instance is not allowed"
        Game.__singleton = True
        
        self.turn = None
        self.rules_freezed_for_ceremony_finish_time = 0
        self.scores: dict[Side, int] = {Side.RED: 0, Side.BLUE: 0}
        self.dragged_player: Player = None
        self.dragging_mouse_pos: np.ndarray = None
        self.board: Board = Board(self)    
        self._prev_board_idle_status : bool | None = None
        self.winner = None
        self.is_finished = False
        self.pygame_init()


    def is_ceremony_running(self) -> bool:
        return self.rules_freezed_for_ceremony_finish_time > pygame.time.get_ticks()
    
    def is_winner_ceremony_running(self) -> bool:
        return self.is_ceremony_running() and self.is_finished
    
    def is_goal_ceremony_running(self) -> bool:
        return self.is_ceremony_running() and not self.is_finished
    
    def update(self):
        objects = self.board.all_objects
        for obj in objects:
            obj.pre_update_velocity()
        
        for obj in objects:
            obj.update_velocity()

        for obj in objects:
            obj.update_pos()

        if self._prev_board_idle_status != self.board.is_idle():
            for player in self.board.all_players:
                player.put_player_out_of_the_goal()
            self.board.left_goalkeeper.keep_goalkeeper_in_penalty_area()
            self.board.right_goalkeeper.keep_goalkeeper_in_penalty_area()
        self._prev_board_idle_status = self.board.is_idle()


    def start_dragging_player(self, obj):
        self.dragged_player = obj
        self.dragging_mouse_pos = np.array(pygame.mouse.get_pos())

    def releasing_dragged_player_shot(self):
        releasing_force_booster = 2.5
        if isinstance(self.dragged_player, Striker):
            releasing_force_booster = 3.5
        self.dragged_player.velocity = releasing_force_booster*(self.dragged_player.pos - self.dragging_mouse_pos).astype('float64')
        self.dragged_player = None
        self.dragging_mouse_pos = None
        self.swap_turn()

    def draw_dragged_player_shot_hint(self):
        self.dragging_mouse_pos = np.array(pygame.mouse.get_pos())
        
        pygame.draw.line(
                surface=self.board.screen,
                color=(255, 255, 255),
                start_pos=self.dragged_player.pos,
                end_pos=self.dragged_player.pos*2 - self.dragging_mouse_pos,
                width=4
            )
        
    def pygame_mouse_event_handle(self, event=None):

        if event and event.type == pygame.MOUSEBUTTONDOWN:
            players = self.board.all_players
            for player in players:
                if np.linalg.norm(np.array(pygame.mouse.get_pos()) - player.pos) < player.radius:
                    if player.is_activated():
                        self.start_dragging_player(player)

        elif event and event.type == pygame.MOUSEBUTTONUP:
            if self.dragged_player:
                self.releasing_dragged_player_shot()


        pressed_mouse_buttons = pygame.mouse.get_pressed()
        if self.dragged_player and pressed_mouse_buttons[0]:
            self.draw_dragged_player_shot_hint()

    def pygame_event_handle(self):

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()

            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEBUTTONUP:
                self.pygame_mouse_event_handle(event)
        
        if pygame.mouse.get_pressed():
            self.pygame_mouse_event_handle()
    

    
    def pygame_refresh_background(self):
        self.board.show_screen()

    def pygame_clock_tick_set_dt(self):
        self.DT = self.clock.tick(settings.FPS) / 1000.0

    def pygame_draw(self):
        self.board.draw_objects(self.board.all_objects)
        self.board.draw_goals()
        self.board.show_scoreboard()

        if self.is_goal_ceremony_running():
            self.board.show_goal_ceremony()

        if self.is_winner_ceremony_running():
            self.board.show_winner_ceremony(self.winner)

        

    def pygame_update(self):
        self.update()
        pygame.display.flip()

    def winner_ceremony_start(self):
        self.rules_freezed_for_ceremony_finish_time = pygame.time.get_ticks() + settings.WINNER_CEREMONY_TIME
        self.play_crowd_clapping_sound()

    def winner_ceremony_end(self):
        self.pygame_quit() # TODO
        exit()

    def check_winner_ceremony_end(self):
        if (self.is_finished and
                self.rules_freezed_for_ceremony_finish_time and
                self.rules_freezed_for_ceremony_finish_time <= pygame.time.get_ticks()):
            self.winner_ceremony_end()
            self.rules_freezed_for_ceremony_finish_time = 0

    def game_finished(self):
        self.is_finished = True
        self.winner_ceremony_start()

    def play_crowd_clapping_sound(self):
        self.media.crowd_clapping_sound.play()

    def goal_ceremony_start(self):
        self.rules_freezed_for_ceremony_finish_time = pygame.time.get_ticks() + settings.GOAL_CEREMONY_TIME
        self.play_crowd_clapping_sound()

    def goal_ceremony_end(self):
        self.board.reset_board_state()

    def check_goal_ceremony_end(self):
        if (not self.is_finished and
                self.rules_freezed_for_ceremony_finish_time and
                self.rules_freezed_for_ceremony_finish_time <= pygame.time.get_ticks()):
            self.goal_ceremony_end()
            self.rules_freezed_for_ceremony_finish_time = 0

    def check_ceremony_end(self):
        self.check_goal_ceremony_end()
        self.check_winner_ceremony_end()

    def scored(self, scored_side):
        if scored_side == Side.BLUE:
            self.turn = Side.RED
        elif scored_side == Side.RED:
            self.turn = Side.BLUE

        if self.scores[scored_side] == 3:
            self.winner = scored_side
            self.game_finished()
        else:
            self.goal_ceremony_start()

    def pygame_goal_check(self):
        
        scored_side = self.board.which_side_scored()

        if scored_side is None:
            return
        
        self.scores[scored_side] += 1
        
        self.scored(scored_side)

    def swap_turn(self):
        self.turn = Side.RED if self.turn == Side.BLUE else Side.BLUE
        
    def run(self):
        running = True

        self.turn = Game.FIRST_TURN

        while running:

            self.pygame_refresh_background()

            self.pygame_clock_tick_set_dt()

            self.pygame_event_handle()

            self.pygame_draw()

            self.pygame_update()

            self.check_ceremony_end()

            if not self.is_ceremony_running():
                self.pygame_goal_check()

    def __del__(self):
        self.pygame_quit()

