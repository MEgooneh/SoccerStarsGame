import pygame
import numpy as np

import settings

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .Game import Game

class Object:

    def __init__(self, game: 'Game', mass: float, radius: float, pos: np.ndarray, velocity: np.ndarray):
        self.game = game
        self.mass = mass
        self.radius = radius
        self.pos = pos
        self.velocity = velocity.astype(np.longdouble)
        self._updated_velocity = velocity.copy()

    def is_in_left_goal(self) -> bool:
        return (
            settings.GOAL_UP_BORDER <= self.pos[1] - self.radius and
            self.pos[1] + self.radius <= settings.GOAL_DOWN_BORDER and
            self.pos[0] - self.radius < settings.PITCH_LEFT_BORDER
        )

    def is_completely_in_left_goal(self) -> bool:
        return (
            self.is_in_left_goal() and
            self.pos[0] + self.radius <= settings.PITCH_LEFT_BORDER
        )

    def is_in_right_goal(self) -> bool:
        return (
            settings.GOAL_UP_BORDER <= self.pos[1] - self.radius and
            self.pos[1] + self.radius <= settings.GOAL_DOWN_BORDER and
            self.pos[0] + self.radius > settings.PITCH_RIGHT_BORDER
        )
    
    def is_completely_in_right_goal(self) -> bool:
        return (
            self.is_in_right_goal and
            self.pos[0] - self.radius > settings.PITCH_RIGHT_BORDER
        )

    def is_in_goal(self) -> bool:
        return self.is_in_left_goal() or self.is_in_right_goal()

    def is_completely_in_goal(self) -> bool:
        return self.is_completely_in_left_goal() or self.is_completely_in_right_goal()

    def collision_to_object_physical_update(self, other):
        if self.pos[0] - other.pos[0] == 0:
            theta = np.pi/2
        else:
            theta = np.arctan((self.pos[1] - other.pos[1])/(self.pos[0] - other.pos[0]))

        v1_rot = np.array([
                np.dot(self.velocity, np.array([np.cos(theta), np.sin(theta)])),
                np.dot(self.velocity, np.array([-np.sin(theta), np.cos(theta)])),
            ])
        
        v2_rot = np.array([
                np.dot(other.velocity, np.array([np.cos(theta), np.sin(theta)])),
                np.dot(other.velocity, np.array([-np.sin(theta), np.cos(theta)])),
            ])

        v1_prim_rot = np.array([
            (v1_rot[0]*(self.mass - other.mass) + 2*other.mass*v2_rot[0]) / (self.mass + other.mass),
            v1_rot[1]
        ])

        self._updated_velocity = np.array([
                v1_prim_rot[0]*np.cos(theta) - v1_prim_rot[1]*np.sin(theta),
                v1_prim_rot[0]*np.sin(theta) + v1_prim_rot[1]*np.cos(theta)
            ])
    
    def collision_object_play_sound(self, other=None):
        ...

    def collision_to_object_update(self, other):
        self.collision_to_object_physical_update(other)
        self.collision_object_play_sound(other)

    def check_collision_to_goal_border(self):
        if (settings.GOAL_LEFT_BORDER >= self.pos[0] - self.radius 
                or settings.GOAL_RIGHT_BORDER <= self.pos[0] + self.radius):
            self._updated_velocity[0] *= -1

    def check_collision_to_metal_border(self):
        collisioned = False
        
        if (self.pos[0] - settings.PITCH_LEFT_BORDER <= self.radius
                or settings.PITCH_RIGHT_BORDER - self.pos[0] <= self.radius):
            self._updated_velocity[0] *= -1
            collisioned = True
        
        if (self.pos[1] - settings.PITCH_UP_BORDER <=  self.radius 
                or settings.PITCH_DOWN_BORDER - self.pos[1] <= self.radius):
            self._updated_velocity[1] *= -1
            collisioned = True

        if collisioned:
            self.collision_object_play_sound()
    
    def check_collision_to_board(self):
        if  (settings.GOAL_UP_BORDER <= self.pos[1] - self.radius and
                self.pos[1] + self.radius <= settings.GOAL_DOWN_BORDER):
            self.check_collision_to_goal_border()
        else:
            self.check_collision_to_metal_border()

    def check_collision_to_object(self):
        other_objects = [object for object in self.game.board.all_objects if object != self]
        for obj in other_objects:
            if np.linalg.norm(obj.pos - self.pos) <= obj.radius + self.radius:
                self.collision_to_object_update(obj)

    def check_collision(self):
        self.check_collision_to_board()
        self.check_collision_to_object()
            
    def put_player_out_of_the_goal(self):
        if self.is_in_left_goal():
            self.pos[0] = settings.PITCH_LEFT_BORDER + self.radius + 1
        elif self.is_in_right_goal():
            self.pos[0] = settings.PITCH_RIGHT_BORDER - self.radius - 1
                 
    def object_stop_condition(self):
        if np.linalg.norm(self._updated_velocity) < settings.MINIMUM_OF_VELOCITY_TO_STOPPING_OBJECT:
            self._updated_velocity = np.zeros((2), dtype=np.longdouble) 

    def pre_update_velocity(self):
        self._updated_velocity = self.velocity.copy()
        self.check_collision()
    
    def friction_in_updated_velocity(self):
        speed_norm = np.linalg.norm(self._updated_velocity)
        if speed_norm:
            self._updated_velocity -= self._updated_velocity * (settings.FRICTION_A * self.mass * self.game.DT / speed_norm)

    def update_velocity(self):
        self.object_stop_condition()
        self.friction_in_updated_velocity()
        self.velocity = self._updated_velocity

    def fit_new_pos_in_the_board(self):
        
        if  (settings.GOAL_UP_BORDER <= self.pos[1] - self.radius and
                self.pos[1] + self.radius <= settings.GOAL_DOWN_BORDER):
            self.pos[0] = max(settings.GOAL_LEFT_BORDER + self.radius, self.pos[0])
            self.pos[0] = min(settings.GOAL_RIGHT_BORDER-self.radius, self.pos[0])
            
        else: 
            self.pos[0] = max(settings.PITCH_LEFT_BORDER + self.radius, self.pos[0])
            self.pos[0] = min(settings.PITCH_RIGHT_BORDER-self.radius, self.pos[0])

        self.pos[1] = max(settings.PITCH_UP_BORDER + self.radius, self.pos[1])
        self.pos[1] = min(settings.PITCH_DOWN_BORDER-self.radius, self.pos[1])

    def fit_new_pos_without_collision(self):
        objects = self.game.board.all_objects
        for obj in objects:
            if obj is self:
                continue
            if (obj.pos == self.pos).all():
                x_add = -1 if self.pos[0] == settings.PITCH_RIGHT_BORDER-self.radius else 1
                y_add = -1 if self.pos[1] == settings.PITCH_DOWN_BORDER-self.radius else 1 
                self.pos += np.array([x_add, y_add])

            if np.linalg.norm(obj.pos - self.pos) <= obj.radius + self.radius:
                self.pos =  obj.pos + (self.pos - obj.pos) / np.linalg.norm(self.pos - obj.pos) * (obj.radius + self.radius)


    def update_pos(self):
        self.pos += (self.velocity * self.game.DT).astype('int64')

        self.fit_new_pos_in_the_board()
        
        self.fit_new_pos_without_collision()

        
    def draw(self, screen: pygame.Surface): ...

    def __repr__(self) -> str:
        return (f"Object(mass={self.mass}, radius={self.radius}, "
                f"pos={self.pos}, velocity={self.velocity})")
