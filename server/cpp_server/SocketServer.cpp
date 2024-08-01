#include <cstring> 
#include <thread>
#include <iostream> 
#include <netinet/in.h> 
#include <chrono>
#include <ctime>
#include <sys/socket.h> 
#include <random>
#include <unistd.h> 
#include <bits/stdc++.h>
#include "nlohmann/json.hpp"
using namespace std; 
using json = nlohmann::json;

struct User{
    int id; 
    std::string username; 

    User(int id, std::string username=""){
        this->id = id;
        this->username = username;
    }
};


struct SocketServer{
    int serverSocket; 
    queue<int> userid_in_match_queue;
    unordered_map<int, int> match_opponents;
    unordered_map<int, std::string> id_to_username;   
    unordered_map<int, int> client_to_userid;
    unordered_map<int, int> userid_to_client;  
    SocketServer(){
        this->serverSocket = socket(AF_INET, SOCK_STREAM, 0); 
        sockaddr_in serverAddress; 
        serverAddress.sin_family = AF_INET; 
        serverAddress.sin_port = htons(3022); 
        serverAddress.sin_addr.s_addr = INADDR_ANY; 
        bind(serverSocket, (struct sockaddr*)&serverAddress, sizeof(serverAddress)); 
        listen(serverSocket, 5); 
    }

    string get(int client){
        char buffer[4] = {0}; 
        ssize_t bytesRead = recv(client, buffer, 4, 0); 
        if (bytesRead != 4) {
            //perror("recv failed");
            return "";
        }
        int message_len;
        memcpy(&message_len, buffer, sizeof(message_len)); 
        message_len = ntohl(message_len); 

        char* messageBuffer = new char[message_len + 1];
        memset(messageBuffer, 0, message_len + 1);

        bytesRead = recv(client, messageBuffer, message_len, 0);
        if (bytesRead != message_len) {
            //perror("recv failed");
            delete[] messageBuffer;
            return "";
        }

        string message(messageBuffer);

        delete[] messageBuffer;

        return message;
    }

    json get_event(int client){
        string msg = this->get(client); 
        json serialized; 
        try{
            serialized = json::parse(msg); 
        }
        catch(...){
            //perror("parsing error!"); 
        }
        
        return serialized;
    }

    void send_event(int client, string event_name, json content){
        auto now = chrono::system_clock::now(); 
        int timestamp = chrono::system_clock::to_time_t(now);
        json message = {
            {"event", event_name},
            {"content", content},
            {"timestamp", timestamp}
        }; 
        string message_str = message.dump(); 
        uint32_t message_length = htonl(message_str.size());
        if (send(client, &message_length, sizeof(message_length), 0) != sizeof(message_length)) {
            //perror("send failed");
            return;
        }

        if (send(client, message_str.c_str(), message_str.size(), 0) != static_cast<ssize_t>(message_str.size())) {
            //perror("send failed");
            return;
        }
    }
    
    User* get_user(int client){
        json recvd = this->get_event(client);
        json res = recvd["content"]; 
        int id = res["id"].get<int>();
        string username = res["username"].get<string>();  
        this->userid_to_client[id] = client; 
        this->client_to_userid[client] = id; 
        this->id_to_username[id] = username; 
        return new User(id, username) ;
    }

    void event_match_request(int client, User* user, json content){
        if(this->userid_in_match_queue.size()){
            int opponent_id = this->userid_in_match_queue.front();
            int opponent_client = this->userid_to_client[opponent_id];  
            this->match_opponents[user->id] = opponent_id; 
            this->match_opponents[opponent_id] = user->id; 
            this->userid_in_match_queue.pop();
            int match_id = rand()%1000000000; 
            int side = rand()%2; 
            int left_user_id, right_user_id;
            string left_user_username, right_user_username; 
            if(side == 0){
                left_user_id = user->id;
                left_user_username = user->username;
                right_user_id = opponent_id; 
                right_user_username = this->id_to_username[opponent_id]; 
            }
            else{
                left_user_id = opponent_id;
                left_user_username = this->id_to_username[opponent_id] ;
                right_user_id =  user->id; 
                right_user_username = user->username; 
            }
            auto now = chrono::system_clock::now(); 
            int timestamp = chrono::system_clock::to_time_t(now);
            json match = {
                {"id", match_id},
                {"left_user", {{"id", left_user_id}, {"username", left_user_username}}},
                {"right_user", {{"id", right_user_id}, {"username", right_user_username}}},
                {"created_at", timestamp}
            };
            this->send_event(client, "match_start", match); 
            this->send_event(opponent_client, "match_start", match); 
        }   
        else{
            this->userid_in_match_queue.push(user->id); 
        }
    }

    void event_board_update(int client, User* user, json content){
        int opponent_id = this->match_opponents[user->id]; 
        int opponent_client = this->userid_to_client[opponent_id]; 
        this->send_event(opponent_client, "board_update", content); 
    }

    void event_router(int client, User* user){
        json event = this->get_event(client); 
        string name = event["event"].get<string>();
        json content = event["content"];  
        if(name == "match_request"){
            this->event_match_request(client, user, content); 
        }
        else if(name == "board_update"){
            this->event_board_update(client, user, content); 
        }
    }


    void client_run(int client, User* user){
        srand(time(0) + user->id); 
        while(true){
            this->event_router(client, user); 
        }
    }

    void run(){

        while(true){
            int clientSocket = accept(this->serverSocket, nullptr, nullptr); 
            User* user = this->get_user(clientSocket); 
            thread client_thread(&SocketServer::client_run, this, clientSocket, user); 
            client_thread.detach(); 
        }
        
        close(serverSocket); 

    }

};


int main() { 
    SocketServer server = SocketServer();
    cout << "Starting SoccerStar socket server, listening on 0.0.0.0:3022" ;
    server.run(); 
	return 0; 
}
