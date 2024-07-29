import pygame
import numpy as np

from .Board import Board
from .Player import Side, GoalKeeper, Defender, Striker
from .Media import MediaLoader
from .Mouse import Mouse
import settings


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .Player import Player
    from .Ball import Ball


from .Models import User, Match

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
    def __init__(self, is_multiplayer=False, socket_client=None,):
        if Game.__singleton:
            raise Exception("Game is singleton, more than one instance is not allowed")
        Game.__singleton = True
        
        self.is_multiplayer = is_multiplayer
        self.socket = socket_client
        self.mouse_handler = Mouse(self, socket_client)

        self.turn = None
        self.rules_freezed_for_ceremony_finish_time = 0
        self.scores: dict[Side, int] = {Side.RED: 0, Side.BLUE: 0}
        self.dragged_player: Player = None
        self.dragging_mouse_pos: np.ndarray = None
        self.left_side_name = "Player 1"
        self.right_side_name = "Player 2"
        self.board: Board = Board(self)    
        self._prev_frame_board_was_idle : bool | None = None
        self.winner = None
        self.is_finished = False

    def is_ceremony_running(self) -> bool:
        return self.rules_freezed_for_ceremony_finish_time > pygame.time.get_ticks()
    
    def is_winner_ceremony_running(self) -> bool:
        return self.is_ceremony_running() and self.is_finished
    
    def is_goal_ceremony_running(self) -> bool:
        return self.is_ceremony_running() and not self.is_finished
    
    def end_of_turn_jobs(self):
        pass

    def update(self):
        objects = self.board.all_objects
        for obj in objects:
            obj.pre_update_velocity()
        
        for obj in objects:
            obj.update_velocity()

        for obj in objects:
            obj.update_pos()

        if self._prev_frame_board_was_idle != self.board.is_idle():
            for player in self.board.all_players:
                player.put_player_out_of_the_goal()
            self.board.left_goalkeeper.keep_goalkeeper_in_penalty_area()
            self.board.right_goalkeeper.keep_goalkeeper_in_penalty_area()
        self._prev_frame_board_was_idle = self.board.is_idle()

    def swap_turn(self):
        self.turn = Side.RED if self.turn == Side.BLUE else Side.BLUE

    def start_dragging_player(self, player):
        self.dragged_player = player

    def releasing_dragged_player_shot(self):
        releasing_force_booster = 2.5
        if isinstance(self.dragged_player, Striker):
            releasing_force_booster = 3.5
        self.dragged_player.velocity = releasing_force_booster*(self.dragged_player.pos - self.dragging_mouse_pos).astype(np.longdouble)
        self.dragged_player = None
        self.dragging_mouse_pos = None
        self.swap_turn()

    def draw_dragged_player_shot_hint(self, mouse):
        self.dragging_mouse_pos = mouse.get_pos()
        
        pygame.draw.line(
                surface=self.board.screen,
                color=(255, 255, 255),
                start_pos=self.dragged_player.pos,
                end_pos=self.dragged_player.pos*2 - self.dragging_mouse_pos,
                width=4
            )
        
    def pygame_event_mouse_related(self):
        mouse = self.mouse_handler.get_mouse() 
        if mouse.is_click_down():
            players = self.board.all_players
            for player in players:
                if np.linalg.norm(mouse.get_pos() - player.pos) < player.radius:
                    if player.is_activated():
                        self.start_dragging_player(player)

        elif mouse.is_click_up():
            if self.dragged_player:
                self.releasing_dragged_player_shot()

        elif mouse.is_click_hold():
            if self.dragged_player:
                self.draw_dragged_player_shot_hint(mouse)


    def pygame_event_exit(self):
        if pygame.event.get(pygame.QUIT):
            exit()

    def pygame_event_handle(self):
        self.pygame_event_mouse_related()
        
        self.pygame_event_exit()
    

    
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

    def play_crowd_clapping_sound(self):
        self.media.crowd_clapping_sound.play()

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

        self.scores[scored_side] += 1

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
        
        self.scored(scored_side)

    def multiplayer_updates(self):
        if self.socket.is_in_match:
            self.left_side_name = self.socket.match.left_side_user.username
            self.right_side_name = self.socket.match.right_side_user.username
        
    def run(self):
        running = True

        self.turn = Game.FIRST_TURN

        while running:
            
            if self.is_multiplayer:
                self.multiplayer_updates()

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

