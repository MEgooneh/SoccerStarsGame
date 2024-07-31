import socket
from .Models import Match, MatchRequest, MouseModel, MouseStatus, BoardUpdate, User, load_event, dump_event
from .Player import Side
from utils.socket import socket_ordered_recv_message, socket_ordered_send_message
from pydantic import BaseModel
import logging

logging.basicConfig(
            filename = 'log/client/socket.log',
            level=logging.INFO,
            format = "{asctime} - {levelname} - {message}",
            style="{",
            datefmt="%Y-%m-%d %H:%M"
)

class SocketClient:
    SERVER_ADDR = (('192.168.26.102', 3022))

    def __init__(self):
        self.user: User = None
        self.match: Match = None
        self.side: Side | None = None
        self.is_in_match: bool = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(SocketClient.SERVER_ADDR)

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
            if message is None:
                raise Exception
        except Exception as e:
            logging.error(f"Recieving from server Error: user({self.user})")
            raise Exception(f"Recieving from server Error: {e=}")
        logging.info(f"Recieving from server: user({self.user}), message({message})")

        return load_event(message)
    
    def register_user(self, user: User):
        self.user = user
        self.send_event(user)

    def make_match_request(self):
        match_req = MatchRequest()
        self.send_event(match_req)

    def match_approved(self, match: Match):
        self.match = match
        self.side = (Side.RED if self.user == match.left_user else Side.BLUE)
        self.is_in_match = True
        logging.info(f"Match Approved and started: {match=}")

    def pend_for_match_start(self):
        event = self.get_event()
        event_name, match, timestamp = event["event"], event["content"], event["timestamp"]
        if event_name == "match_start":
            self.match_approved(match)
            return match

    def get_board_from_opponent(self):
        event = self.get_event()
        event_name, board, timestamp = event["event"], event["content"], event["timestamp"]
        if event_name == "board_update":
            return board

    def exit_game(self):
        self.socket.close()

    def send_board_to_opponent(self, board_update: BoardUpdate):
        self.send_event(board_update)