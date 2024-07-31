from pydantic import BaseModel
import numpy as np
from enum import Enum
from utils.time import now_time
import json, random

class Position(BaseModel):
    x: int
    y: int

    def to_ndarray(self):
        return np.array([self.x, self.y], dtype=int)

class Velocity(BaseModel):
    x: float
    y: float

    def to_ndarray(self):
        return np.array([self.x, self.y], dtype=np.longdouble)

class ObjectModel(BaseModel):
    id: int
    pos: Position
    velocity: Velocity

    def get_pos(self):
        return self.pos.to_ndarray()

class MouseStatus(Enum):
    IDLE = 0
    CLICK_DOWN = 1
    CLICK_HOLD = 2
    CLICK_UP = 3

class MouseModel(BaseModel):
    pos: Position
    status: MouseStatus = MouseStatus.IDLE
    
    def get_pos(self):
        return self.pos.to_ndarray()

    def is_click_down(self) -> bool:
        return self.status == MouseStatus.CLICK_DOWN

    def is_click_up(self) -> bool:
        return self.status == MouseStatus.CLICK_UP

    def is_click_hold(self) -> bool:
        return self.status == MouseStatus.CLICK_HOLD
    
    def is_click_idle(self) -> bool:
        return self.status == MouseStatus.IDLE

class BoardUpdate(BaseModel):
    mouse: MouseModel
    objects: list[ObjectModel]

class User(BaseModel):
    id: int = random.randint(0, 1000000000)
    username: str

class MatchRequest(BaseModel):
    created_at: float = now_time()

class Match(BaseModel):
    id: int = random.randint(0, 1000000000)
    left_user: User
    right_user: User
    created_at: float = now_time()

    def retrieve_opponent(self, user:User) -> User | None:
        if user.id == self.left_user:
            return self.right_user
        elif user.id == self.right_user:
            return self.left_user
        else:
            return None
        
EVENTS = {
    "user_registeration": User,
    "match_request": MatchRequest,
    "match_start": Match,
    "board_update": BoardUpdate
}

def dump_event(model: BaseModel) -> str:
    event_name = [key for key, value in EVENTS.items() if isinstance(model, value)][0]
    data = json.dumps(
        {
            "event": event_name, 
            "content": json.loads(model.model_dump_json()),
            "timestamp": now_time()
        }
    )
    return data

def load_event(data: str) -> dict[str, str | BaseModel | float]:
    event = json.loads(data)
    model = EVENTS[event["event"]]
    event["content"] = model(**event["content"])
    return event

