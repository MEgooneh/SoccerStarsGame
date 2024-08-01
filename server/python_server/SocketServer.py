from pydantic import BaseModel

import socket
import logging
import random
import select
import _thread

from src.Models import User, Match, MatchRequest, MouseModel, ObjectModel, BoardUpdate, dump_event, load_event
from src.Player import Side
from utils.socket import socket_ordered_recv_message, socket_ordered_send_message
from utils.time import now_time
import os

logging.basicConfig(
    filename = os.path.join('log', 'server', 'server.log'),
    level=logging.INFO,
    format = "{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M"
)


class SocketServer:
    HOST_ADDR = ('0.0.0.0', 3022)

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client_users: dict[socket.socket, User] = dict()
        self.users_client: dict[int, socket.socket] = dict()
        self.opponents: dict[socket.socket, socket.socket] = dict()
        self.match_request_queue: list[socket.socket] = []
        self.socket.bind(SocketServer.HOST_ADDR)
        self.socket.listen(5)
        print(f"Starting SoccerStar socket server, listening on {self.HOST_ADDR}")


    def send_event(self, client: socket.socket, model: BaseModel):
        message = dump_event(model)
        try:
            socket_ordered_send_message(client, message)
        except:
            logging.error(f"Error sending message to client{client=}, {message=}")


    def get_event(self, client: socket.socket):
        try:
            message = socket_ordered_recv_message(client)
        except:
            return None
        if message is None:
            return None

        return load_event(message)
    
    def __game_side_lottery(self):
        sides = [Side.RED, Side.BLUE]
        rand_index = random.randint(0, 1)
        return sides[rand_index]        
    
    def event_match_request(self, client: socket.socket, user: User, match_request_model: MatchRequest):
        if self.match_request_queue:
            opponent_client = self.match_request_queue.pop(0)
            opponent = self.client_users[opponent_client]
            user_side = self.__game_side_lottery()
            match user_side:
                case Side.RED:
                    match = Match(left_user=user, right_user=opponent)
                case Side.BLUE:
                    match = Match(left_user=opponent, right_user=user)

            logging.info(f"Two users matched: {match=}")            
            self.send_event(client, match)
            self.send_event(opponent_client, match)
            self.opponents[client] = opponent_client
            self.opponents[opponent_client] = client
        
        else:
            self.match_request_queue.append(client)
            logging.info("The match request queue is empty")

    def event_board_update(self, client: socket.socket, user: User, board_update_model: BoardUpdate):
        opponent_client = self.opponents[client]
        self.send_event(opponent_client, board_update_model)

    def close_connection(self, client):
        if client in self.opponents.keys():
            opponent_client = self.opponents[client]
            opponent_client.close()
        client.close()
        logging.info(f"A game finished.")

        exit()

    def client_run(self, client: socket.socket, user):
        while True:
            response = self.get_event(client)
            if response is None:
                self.close_connection(client)
                break
            event_name, content = response["event"], response["content"]
            match event_name:
                case "board_update":
                    self.event_board_update(client, user, content)
                case "match_request":
                    self.event_match_request(client, user, content)


    def run(self):
        while True:
            client, addr = self.socket.accept()

            new_user = self.get_event(client)

            user: User = new_user["content"]

            self.users_client[user.id] = client
            self.client_users[client] = user
            
            _thread.start_new_thread(self.client_run, (client, user))


        

def run_server():
    server = SocketServer()
    server.run()