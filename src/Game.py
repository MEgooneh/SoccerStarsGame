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
    def __init__(self, is_multiplayer=False, socket_client=None):
        if Game.__singleton:
            raise Exception("Game is singleton, more than one instance is not allowed")
        Game.__singleton = True
        
        self.is_multiplayer = is_multiplayer
        self.socket = socket_client

        self.turn = None
        self.scored_side = None
        self.rules_freezed_for_ceremony_finish_time = 0
        self.scores: dict[Side, int] = {Side.RED: 0, Side.BLUE: 0}
        self.dragged_player: Player = None
        self.dragging_mouse_pos: np.ndarray = None
        self.left_side_name = "Player 1"
        self.right_side_name = "Player 2"
        self.board: Board = Board(self)    
        self.winner = None
        self.is_finished = False
        self.turn_last_second = settings.TURN_SECONDS
        self._prev_frame_board_was_idle : bool | None = True

    def is_ceremony_running(self) -> bool:
        return self.rules_freezed_for_ceremony_finish_time > pygame.time.get_ticks()
    
    def is_winner_ceremony_running(self) -> bool:
        return self.is_ceremony_running() and self.is_finished
    
    def is_goal_ceremony_running(self) -> bool:
        return self.is_ceremony_running() and not self.is_finished
    
    def end_of_turn_jobs(self):
        for player in self.board.all_players:
                player.put_player_out_of_the_goal()
        self.board.left_goalkeeper.keep_goalkeeper_in_penalty_area()
        self.board.right_goalkeeper.keep_goalkeeper_in_penalty_area()

        self.turn_last_second = pygame.time.get_ticks()//1000 + settings.TURN_SECONDS

        if self.scored_side is None:
            self.swap_turn()
        elif self.scored_side == Side.BLUE:
            self.turn = Side.RED
        else:
            self.turn = Side.BLUE
        self.scored_side = None

    def is_turns_times_up(self):
        return self.turn_last_second <= pygame.time.get_ticks()//1000

    def update_in_my_turn(self):
        objects = self.board.all_objects
        for obj in objects:
            obj.pre_update_velocity()
        
        for obj in objects:
            obj.update_velocity()

        for obj in objects:
            obj.update_pos()

        if (not self._prev_frame_board_was_idle and self.board.is_idle()) or (self.is_turns_times_up() and self.board.is_idle()):
            self.end_of_turn_jobs()

        self._prev_frame_board_was_idle = self.board.is_idle()

    def update_in_opponent_turn(self):
        if not self._prev_frame_board_was_idle and self.board.is_idle():
            self.end_of_turn_jobs()

        self._prev_frame_board_was_idle = self.board.is_idle()

    def update(self):
        if (self.is_multiplayer and self.turn == self.socket.side) or not self.is_multiplayer:
            self.update_in_my_turn()
        
        else:
            self.update_in_opponent_turn()

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
        # self.swap_turn()

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
        if self.board.mouse.is_click_down():
            players = self.board.all_players
            for player in players:
                if np.linalg.norm(self.board.mouse.get_pos() - player.pos) < player.radius:
                    if player.is_activated():
                        self.start_dragging_player(player)

        elif self.board.mouse.is_click_up():
            if self.dragged_player:
                self.releasing_dragged_player_shot()

        elif self.board.mouse.is_click_hold():
            if self.dragged_player:
                self.draw_dragged_player_shot_hint(self.board.mouse)


    def pygame_event_exit(self):
        if pygame.event.get(pygame.QUIT):
            exit()

    def pygame_event_handle(self):
        self.pygame_event_exit()

        self.pygame_event_mouse_related()
    
    def pygame_refresh_background(self):
        self.board.show_screen()

    def pygame_clock_tick_set_dt(self):
        self.DT = self.clock.tick(settings.FPS) / 1000.0

    def pygame_draw(self):
        self.board.draw_objects(self.board.all_objects)
        self.board.draw_goals()
        self.board.show_scoreboard()
        self.board.show_timer()

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

        self.scored_side = scored_side

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


    def show_opponent_board_multiplayer(self):
        board_update = self.socket.get_board_from_opponent()

        self.board.load_board(board_update)

        self.pygame_refresh_background()

        self.pygame_clock_tick_set_dt()

        self.pygame_event_handle()

        self.pygame_draw()

        self.pygame_update()

        self.check_ceremony_end()

        if not self.is_ceremony_running():
            self.pygame_goal_check()

    def run_game_in_my_turn_multiplayer(self):


        self.board.mouse.update_my_mouse()

        self.pygame_refresh_background()

        self.pygame_clock_tick_set_dt()

        self.pygame_event_handle()

        self.pygame_draw()

        self.pygame_update()

        self.check_ceremony_end()



        if not self.is_ceremony_running():
            self.pygame_goal_check()

        self.socket.send_board_to_opponent(self.board.dump_board())

    
    def run_multiplayer_game(self):
        running = True

        self.turn = Game.FIRST_TURN

        while running:
            
            if self.turn == self.socket.side:
                self.run_game_in_my_turn_multiplayer()
            else:
                self.show_opponent_board_multiplayer()


    def run_monoplayer_game(self):
        running = True

        self.turn = Game.FIRST_TURN

        while running:

            self.board.mouse.update_my_mouse()

            self.pygame_refresh_background()

            self.pygame_clock_tick_set_dt()

            self.pygame_event_handle()

            self.pygame_draw()

            self.pygame_update()

            self.check_ceremony_end()

            if not self.is_ceremony_running():
                self.pygame_goal_check()


    def run(self):
        if self.is_multiplayer:
            self.run_multiplayer_game()
        else:
            self.run_monoplayer_game()
        

    def __del__(self):
        self.pygame_quit()

