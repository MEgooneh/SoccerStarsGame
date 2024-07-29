from src.Game import Game
from src.Models import User, UserRegisterRequest, Match, MatchRequest
from src.SocketClient import SocketClient

import logging

if __name__ == '__main__':
    me = UserRegisterRequest(username="user2")
    socket = SocketClient()
    socket.connect()
    socket.register(user_register_request=me)
    game = Game(is_multiplayer=True, socket_client=socket)
    game.pygame_init()
    game.load_assets()
    game.board.init_objects()
    
    ans = input("are you want to make game request? [y/n] ")

    if ans == "y":
        socket.make_match_request()
    elif ans == "n":
        exit()
    else:
        raise Exception("Invalid command")
    
    socket.pend_match_approve()

    game.run()
