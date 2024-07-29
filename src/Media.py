import pygame
from PIL import Image

import os

from .Player import GoalKeeper, Striker, Defender
from .Ball import Ball
import settings

class MediaLoader:

    def __init__(self):
        ...

    def play_gif(self, gif: list[pygame.Surface], end_time: int, screen: pygame.Surface):
        now_time = pygame.time.get_ticks()

        frame = ((end_time - now_time)//100)%len(gif)
        middle_of_screen_position = (
            (settings.PITCH_LEFT_BORDER + settings.PITCH_RIGHT_BORDER) // 2,
            (settings.PITCH_UP_BORDER + settings.PITCH_DOWN_BORDER) // 2
        )
        image = gif[frame]
        image_rect = image.get_rect(center=middle_of_screen_position)

        screen.blit(gif[frame], image_rect)

    def load_image(self, image_filename, size: tuple[float, float] = None) -> pygame.Surface:
        image_path = os.path.join("assets", "images", image_filename)
        image = pygame.image.load(image_path).convert_alpha()
        if size:
            image = pygame.transform.smoothscale(image, size)
        return image
    
    def load_gif(self, gif_filename) -> list[pygame.Surface]:
        gif = []
        with Image.open(os.path.join("assets", "gifs", gif_filename)) as img:
            for frame in range(1, img.n_frames):
                img.seek(frame)
                frame_surface = pygame.image.fromstring(img.tobytes(), img.size, img.mode).convert_alpha()
                gif.append(frame_surface)
        return gif
    
    def load_sound(self, sound_filename) -> pygame.mixer.Sound:
        return pygame.mixer.Sound(os.path.join("assets", "sounds", sound_filename))
    
    def load_goalkeeper_images(self):
        PLAYER_IMAGE_SIZE = (2.5 * GoalKeeper.RADIUS, 2.5 * GoalKeeper.RADIUS)

        self.blue_goalkeeper_image = self.load_image("blue_goalkeeper.png", PLAYER_IMAGE_SIZE)
        self.blue_goalkeeper_activated_image = self.load_image("blue_goalkeeper_activated.png", PLAYER_IMAGE_SIZE)
        self.red_goalkeeper_image = self.load_image("red_goalkeeper.png", PLAYER_IMAGE_SIZE)
        self.red_goalkeeper_activated_image = self.load_image("red_goalkeeper_activated.png", PLAYER_IMAGE_SIZE)

    def load_defender_images(self):
        PLAYER_IMAGE_SIZE = (2.5 * Defender.RADIUS, 2.5 * Defender.RADIUS)
        
        self.blue_defender_image = self.load_image("blue_defender.png", PLAYER_IMAGE_SIZE)
        self.blue_defender_activated_image = self.load_image("blue_defender_activated.png", PLAYER_IMAGE_SIZE)
        self.red_defender_image = self.load_image("red_defender.png", PLAYER_IMAGE_SIZE)
        self.red_defender_activated_image = self.load_image("red_defender_activated.png", PLAYER_IMAGE_SIZE)

    def load_striker_images(self):
        PLAYER_IMAGE_SIZE = (2.5 * Striker.RADIUS, 2.5 * Striker.RADIUS)
        self.blue_striker_image = self.load_image("blue_striker.png", PLAYER_IMAGE_SIZE)
        self.blue_striker_activated_image = self.load_image("blue_striker_activated.png", PLAYER_IMAGE_SIZE)
        self.red_striker_image = self.load_image("red_striker.png", PLAYER_IMAGE_SIZE)
        self.red_striker_activated_image = self.load_image("red_striker_activated.png", PLAYER_IMAGE_SIZE)

    def load_player_images(self):
        self.load_goalkeeper_images()
        self.load_defender_images()
        self.load_striker_images()

    def load_ball_image(self):
        BALL_IMAGE_SIZE = (2 * Ball.RADIUS, 2 * Ball.RADIUS)
        self.ball_image = self.load_image("ball.png", BALL_IMAGE_SIZE)

    def load_pitch_image(self):
        PITCH_IMAGE_SIZE = (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
        self.pitch_image = self.load_image("bootan_field.jpg", PITCH_IMAGE_SIZE)
        self.goals_transparent_image = self.load_image("trans_goal_bootan_field.png", PITCH_IMAGE_SIZE)

    def load_images(self):
        self.load_player_images()
        self.load_ball_image()
        self.load_pitch_image()

    def load_player_sounds(self):
        self.player_collision_sound = self.load_sound("player_collision.mp3")

    def load_goal_ceremony_sounds(self):
        self.crowd_clapping_sound = self.load_sound("crowd_clapping.mp3")

    def load_ball_kick_sounds(self):
        self.ball_kick_sound = self.load_sound("soccer_ball_kick.mp3")

    def load_sounds(self):
        self.load_player_sounds()
        self.load_goal_ceremony_sounds()
        self.load_ball_kick_sounds()

    def load_fonts(self):
        self.large_font = pygame.font.SysFont('Arial', 48)
        self.font = pygame.font.SysFont('Arial', 30)
        
    def load_gifs(self):
        self.goal_ceremony_gif = self.load_gif("goal_ceremony.gif")
        self.blue_winning_ceremony_gif = self.load_gif("blue_winning.gif")
        self.red_winning_ceremony_gif = self.load_gif("red_winning.gif")

    def load_assets(self):
        self.load_images()
        self.load_sounds()
        self.load_fonts()
        self.load_gifs()

