from src.Game import Game
from src.Models import User, Match, MatchRequest
from src.SocketClient import SocketClient


def multiplayer_game():
    username = input("type your username:\n")
    me = User(username=username)
    socket = SocketClient()
    socket.register_user(user=me)
    game = Game(is_multiplayer=True, socket_client=socket)
    ans = input("are you want to make game request? [y/n] ")

    if ans == "y":
        socket.make_match_request()
    elif ans == "n":
        exit()
    else:
        raise Exception("Invalid command")
    
    print("Finding your opponent...")
    match = socket.pend_for_match_start()
    game.left_side_name = match.left_user.username
    game.right_side_name = match.right_user.username
    game.pygame_init()
    game.load_assets()
    game.board.init_objects()
    game.run()

def monoplayer_game():
    game = Game()
    game.pygame_init()
    game.load_assets()
    game.board.init_objects()
    game.run()



if __name__ == '__main__':
    game_type = input("1) Monoplayer(Offline)\n2) Multiplayer(Online)\n:")
    match game_type:
        case "1":
            monoplayer_game()
        case "2":
            multiplayer_game()
        case _:
            raise Exception("Invalid game type.")