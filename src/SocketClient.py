from pydantic import BaseModel

import socket
import logging

from .Models import User, UserRegisterRequest, Match, MatchRequest, MouseUpdate, MouseModel, dump_event, load_event
from .Player import Side

from utils.socket import socket_ordered_recv_message, socket_ordered_send_message

logging.basicConfig(
            filename = 'log/socket.log',
            level=logging.INFO,
            format = "{asctime} - {levelname} - {message}",
            style="{",
            datefmt="%Y-%m-%d %H:%M"
)


class SocketClient:

    BUFFER_SIZE = 1024
    SERVER_ADDR = (('127.0.0.1', 3022))

    def __init__(self):
        self.user: User = None
        self.match: Match = None
        self.side: Side | None = None
        self.is_in_match: bool = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        

    def connect(self):
        try:
            self.socket.connect(SocketClient.SERVER_ADDR)
        except BaseException as e:
            logging.error(f"Connection to server error: {self}")
            raise Exception(f"Connection error!\n:{e=}")
        logging.info(f"Connection to server Started: user({self.user})")
    
    def send_event(self, model: BaseModel):
        message = dump_event(model)
        try:
            socket_ordered_send_message(self.socket, message)
        except:
            logging.error(f"Sending to server Error: {self.user}, message=({message})")
            raise Exception("Sending to server Error")

        logging.info(f"Message sent to server: user({self.user}), message({message})")

    def get_event(self):
        try:
            message = socket_ordered_recv_message(self.socket)
        except Exception as e:
            logging.error(f"Recieving from server Error: user({self.user})")
            raise Exception(f"Recieving from server Error: {e=}")
        logging.info(f"Recieving from server: user({self.user}), message({message})")

        return load_event(message)
    
    def user_register_request(self, user_register_request: UserRegisterRequest):
        self.username = user_register_request
        self.send_event(user_register_request)

    def pend_for_user_registeration(self):
        event = self.get_event()
        self.user = event["content"]

    def register(self, user_register_request: UserRegisterRequest):
        self.user_register_request(user_register_request)
        self.pend_for_user_registeration()

    def make_match_request(self):
        match_req = MatchRequest(user=self.user)
        self.send_event(match_req)

    def send_my_mouse(self, mouse_model: MouseModel):
        mouse_update = MouseUpdate(user=self.user, match=self.match, mouse=mouse_model)
        self.send_event(mouse_update)
    
    def am_i_in_the_match(self, match: Match) -> bool:
        return self.user == match.left_side_user or self.user == match.right_side_user

    def match_approved(self, match: Match):
        self.match = match
        self.side = (Side.RED if self.user == match.left_side_user else Side.BLUE)
        self.is_in_match = True
        logging.info(f"Match Approved and started: {match=}")

    def pend_match_approve(self) -> Match:
        event = self.get_event()
        event_name, match, timestamp = event["event"], event["content"], event["timestamp"]
        if event_name == "match_start" and self.am_i_in_the_match(match):
            self.match_approved(match)
        else:
            logging.error(f"Unexpected event recieved in pend_match_approve: {event_name=}, {match=}, {timestamp=} ")
            raise Exception("Unexpected event recieved")
    
    def get_opponent_mouse_update(self) -> MouseUpdate:
        event = self.get_event()
        event_name, mouse_update, timestamp = event["event"], event["content"], event["timestamp"]
        if event_name == "mouse_update":
            logging.info(f"Mouse update: {mouse_update=} ")
            return mouse_update
        else:
            logging.error(f"Unexpected event recieved in get_opponent_mouse_update: {event_name=}, {mouse_update=}, {timestamp=} ")
            raise Exception("Unexpected event recieved")

    def __repr__(self):
        return f"SocketClient(user={self.user}, socket={self.socket})"