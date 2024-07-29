from pydantic import BaseModel, IPvAnyAddress
import numpy as np

from .Player import Side
from utils.time import now_time

from uuid import UUID, uuid4
import json
from enum import Enum
import logging



class User(BaseModel):
    uid: UUID = uuid4()
    ip: IPvAnyAddress
    port: int
    username: str | None = None

    

class UserRegisterRequest(BaseModel):
    username: str = ""
    created_at: float = now_time()

class Match(BaseModel):
    uid: UUID = uuid4()
    left_side_user: User
    right_side_user: User
    created_at: float = now_time()

    def retrieve_opponent(self, user: User) -> User | None:
        if user == self.left_side_user:
            return self.right_side_user
        elif user == self.right_side_user:
            return self.left_side_user
        else:
            return None

class MatchRequest(BaseModel):
    user: User
    created_at: float = now_time()

class MouseStatus(Enum):
    CLICK_DOWN = 0
    CLICK_UP = 1
    CLICK_HOLD = 2
    IDLE = 3

class MousePosition(BaseModel):
    x: int = 0
    y: int = 0

    def to_ndarray(self):
        return np.array((self.x, self.y))
    
class MouseModel(BaseModel):
    pos: MousePosition = MousePosition()
    status: MouseStatus = MouseStatus.IDLE

    def get_pos(self) -> np.ndarray:
        return self.pos.to_ndarray()

    def is_click_down(self) -> bool:
        return self.status == MouseStatus.CLICK_DOWN

    def is_click_up(self) -> bool:
        return self.status == MouseStatus.CLICK_UP

    def is_click_hold(self) -> bool:
        return self.status == MouseStatus.CLICK_HOLD

class MouseUpdate(BaseModel):
    user:User
    match: Match
    mouse: MouseModel
    created_at: float = now_time()

class SwapTurn(BaseModel):
    side: Side
    match: Match
    created_at: float = now_time()


class Score(BaseModel):
    match: UUID
    left_side: int
    right_side: int
    created_at: float = now_time()


EVENT_NAMES = {
    "mouse_update": MouseUpdate,
    "match_request": MatchRequest,
    "match_start": Match,
    "user_intro": UserRegisterRequest,
    "user_registred": User
}

class BadEventRequest(Exception):
    ...

def dump_event(model: BaseModel) -> str:
    try:
        event_name = [key for key, value in EVENT_NAMES.items() if isinstance(model, value)][0]
    except IndexError:
        raise BadEventRequest
    data = json.dumps(
        {
            "event": event_name, 
            "content": json.loads(model.model_dump_json()),
            "timestamp": now_time()
        }
    )
    return data

def load_event(data: str) -> dict[str, str | BaseModel | float]:
    try:
        event = json.loads(data)
        model = EVENT_NAMES[event["event"]]
        event["content"] = model(**event["content"])
        return event
    except Exception as e:
        logging.error(f"Error while loading data from server. Bad data from server. {e=}, {data=}")
        raise Exception("BadDataFromServer")

