from pydantic import BaseModel

import socket
import logging
import random
import select

from src.Models import User, UserRegisterRequest, Match, MatchRequest, MouseUpdate, dump_event, load_event
from src.Player import Side
from utils.socket import socket_ordered_recv_message, socket_ordered_send_message
from utils.time import now_time
from uuid import UUID

logging.basicConfig(
    filename = 'log/server/server.log',
    level=logging.INFO,
    format = "{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M"
)


class SocketServer:

    BUFFER_SIZE = 4096
    HOST_SERVER_ADDR = ('0.0.0.0', 8080)

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.users: list[User] = []
        self.connections: list[socket.socket] = []
        self.addresses: dict[socket.socket, tuple[str, int]] = dict()
        self.users_client: dict[UUID, socket.socket] = dict()
        self.client_users: dict[socket.socket, User] = dict()
        self.running_matches: list[Match] = []
        self.match_request_queue: list[MatchRequest] = []
        self.bind()
        self.listen()

    def bind(self):
        self.socket.bind(SocketServer.HOST_SERVER_ADDR)

    def listen(self):
        self.socket.listen(5)
        print(f"Starting SoccerStar socket server, listening on {self.HOST_SERVER_ADDR}")
        logging.info(f"starting listenting on {self.HOST_SERVER_ADDR=}")

    def send_event(self, client: socket.socket, model: BaseModel):
        message = dump_event(model)
        try:
            socket_ordered_send_message(client, message)
        except Exception as e:
            logging.error(f"Sending to client Error: {client=}, {message=}")
            raise Exception("Sending to client Error" + str(e))

        logging.info(f"Message sent to client: {client=}, {message=}")

    def get_event(self, client: socket.socket):
        client
        try:
            message = socket_ordered_recv_message(client)
        except:
            logging.error(f"Recieving from client Error: {client=}")
            raise Exception("Recieving to client Error")
        
        logging.info(f"Recieving from client: {client=}, {message=}")

        return load_event(message)
    

    def new_user_joined(self, client, addr):
        self.addresses[client] = addr
        user = User(ip=addr[0], port=addr[1])
        self.users.append(user)
        self.users_client[user.uid] = client 
        self.client_users[client] = user
        logging.info(f"New connection has set. {user=}")
        return user  

    def retrieve_user(self, client) -> User:
        return self.client_users[client]

    def retrieve_match_of_user(self, user: User) -> Match | None:
        for match in self.running_matches:
            if match.left_side_user == user or match.right_side_user == user:
                return match

    def event_mouse_update(self, client: socket.socket, user: User, mouse_update_model: MouseUpdate):
        opponent = mouse_update_model.match.retrieve_opponent(user)
        if opponent is None:
            logging.error(f"Wrong Match. user is not in the match. {user=}, {mouse_update_model=}")
            raise Exception("Wrong Match. user is not in the match")
        
        opponent_client = self.users_client[opponent.uid]
        self.send_event(opponent_client, mouse_update_model)

    def __game_side_lottery(self):
        sides = [Side.RED, Side.BLUE]
        rand_index = random.randint(0, 1)
        return sides[rand_index]

    def event_match_request(self, client: socket.socket, user: User, match_request_model: MatchRequest):
        if self.match_request_queue:
            opponent_request = self.match_request_queue.pop(0)
            opponent = opponent_request.user
            user_side = self.__game_side_lottery()
            match user_side:
                case Side.RED:
                    match = Match(left_side_user=user, right_side_user=opponent)
                case Side.BLUE:
                    match = Match(left_side_user=opponent, right_side_user=user)

            opponent_client = self.users_client[opponent.uid]
            logging.info(f"Two users matched: {match=}")            
            self.send_event(client, match)
            self.send_event(opponent_client, match)
            self.running_matches.append(match)

        else:
            self.match_request_queue.append(match_request_model)
            logging.info("The match request queue is empty")            

    def event_user_intro(self, client, user: User, user_model: UserRegisterRequest):
        user.username = user_model.username
        self.send_event(client, user)
        logging.info(f"New user has registered. {user=}")  

    def run_event_router(self, client: socket.socket, user: User):
        response = self.get_event(client)
        event_name, content = response["event"], response["content"]
        match event_name:
            case "mouse_update":
                self.event_mouse_update(client, user, content)
            case "match_request":
                print("salam")
                self.event_match_request(client, user, content)
            case "user_intro":
                self.event_user_intro(client, user, content)

    def remove_expired_match_request(self):
        EXPIRATION_OF_MATCH_REQ = 300
        self.match_request_queue = [
            match_req for match_req in self.match_request_queue if now_time() - match_req.created_at <= EXPIRATION_OF_MATCH_REQ
            ]
        
    def run(self):
        self.connections = [self.socket]
        while True:
            insock, outsock, exceptsock = select.select(self.connections, [], [])
            
            self.remove_expired_match_request()

            for s in insock:
                if s == self.socket:

                    client, addr = self.socket.accept()

                    self.connections.append(client)

                    user = self.new_user_joined(client, addr)

                    self.run_event_router(client, user)
                else:
                    client = s

                    user = self.retrieve_user(client)

                    self.run_event_router(client, user)  
    

        

    def match_approved(self, match: Match):
        self.match = match
        self.side = (Side.RED if self.user == match.left_side_user else Side.BLUE)
        self.is_in_match = True
        logging.info(f"Match Approved and started: {match=}")

    def pend_match_approve(self) -> Match:
        event_name, match, timestamp = self.get_event()
        if event_name == "match_start" and self.am_i_in_the_match(match):
            self.match_approved(match)
        else:
            logging.error(f"Unexpected event recieved in pend_match_approve: {event_name=}, {match=}, {timestamp=} ")
            raise Exception("Unexpected event recieved")
    
    def get_opponent_mouse_update(self) -> MouseUpdate:
        event_name, mouse_update, timestamp = self.get_event()
        if event_name == "mouse_update":
            return mouse_update
        else:
            logging.error(f"Unexpected event recieved in get_opponent_mouse_update: {event_name=}, {mouse_update=}, {timestamp=} ")
            raise Exception("Unexpected event recieved")

    def __repr__(self):
        return f"SocketServer(user={self.user}, socket={self.socket})"
    

if __name__ == '__main__':
    server = SocketServer()
    server.run()