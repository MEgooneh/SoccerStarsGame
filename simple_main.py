from src.Game import Game

if __name__ == '__main__':
    game = Game()
    game.pygame_init()
    game.load_assets()
    game.board.init_objects()
    game.run()
