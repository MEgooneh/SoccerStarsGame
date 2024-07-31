#include <iostream>
#include <string>
#include <thread>
#include <map>
#include <vector>
#include <random>
#include <boost/asio.hpp>
#include <boost/log/trivial.hpp>
#include <boost/log/utility/setup/file.hpp>
#include <json-c/portfile.cmake>
using boost::asio::ip::tcp;

class SocketServer {
public:
    static const std::string HOST_ADDR;
    static const int PORT = 3022;

    SocketServer(boost::asio::io_context& io_context)
        : acceptor_(io_context, tcp::endpoint(tcp::v4(), PORT)) {
        start_accept();
        cout << "Starting SoccerStar socket server, listening on " << HOST_ADDR << ":" << PORT;
    }

private:
    tcp::acceptor acceptor_;
    std::map<tcp::socket*, std::string> client_users;
    std::map<int, tcp::socket*> users_client;
    std::map<tcp::socket*, tcp::socket*> opponents;
    std::vector<tcp::socket*> match_request_queue;

    void start_accept() {
        tcp::socket* new_socket = new tcp::socket(acceptor_.get_io_context());
        acceptor_.async_accept(*new_socket, [this, new_socket](boost::system::error_code ec) {
            if (!ec) {
                handle_accept(new_socket);
            } else {
                delete new_socket;
            }
            start_accept();
        });
    }

    void handle_accept(tcp::socket* client) {
        std::thread([this, client]() {
            Json::Value new_user = get_event(client);
            if (!new_user.isNull()) {
                int user_id = new_user["content"]["id"].asInt();
                client_users[client] = new_user["content"].toStyledString();
                users_client[user_id] = client;
                client_run(client, new_user["content"]);
            }
        }).detach();
    }

    void send_event(tcp::socket* client, const Json::Value& model) {
        std::string message = Json::writeString(Json::StreamWriterBuilder(), model);
        try {
            boost::asio::write(*client, boost::asio::buffer(message));
        } catch (...) {
            BOOST_LOG_TRIVIAL(error) << "Error sending message to client, message=" << message;
        }
        BOOST_LOG_TRIVIAL(info) << "Message sent to client, message=" << message;
    }

    Json::Value get_event(tcp::socket* client) {
        boost::asio::streambuf buffer;
        try {
            boost::asio::read_until(*client, buffer, "\n");
        } catch (...) {
            return Json::nullValue;
        }
        std::istream stream(&buffer);
        std::string message;
        std::getline(stream, message);
        Json::CharReaderBuilder reader;
        Json::Value event;
        std::string errs;
        Json::parseFromStream(reader, stream, &event, &errs);
        BOOST_LOG_TRIVIAL(info) << "Receiving from client, message=" << message;
        return event;
    }

    std::string game_side_lottery() {
        std::vector<std::string> sides = { "RED", "BLUE" };
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dis(0, 1);
        return sides[dis(gen)];
    }

    void event_match_request(tcp::socket* client, const Json::Value& user, const Json::Value& match_request_model) {
        if (!match_request_queue.empty()) {
            tcp::socket* opponent_client = match_request_queue.front();
            match_request_queue.erase(match_request_queue.begin());
            Json::Value opponent = client_users[opponent_client];
            std::string user_side = game_side_lottery();
            Json::Value match;
            if (user_side == "RED") {
                match["left_user"] = user;
                match["right_user"] = opponent;
            } else {
                match["left_user"] = opponent;
                match["right_user"] = user;
            }
            BOOST_LOG_TRIVIAL(info) << "Two users matched, match=" << match.toStyledString();
            send_event(client, match);
            send_event(opponent_client, match);
            opponents[client] = opponent_client;
            opponents[opponent_client] = client;
        } else {
            match_request_queue.push_back(client);
            BOOST_LOG_TRIVIAL(info) << "The match request queue is empty";
        }
    }

    void event_board_update(tcp::socket* client, const Json::Value& user, const Json::Value& board_update_model) {
        tcp::socket* opponent_client = opponents[client];
        send_event(opponent_client, board_update_model);
    }

    void close_connection(tcp::socket* client) {
        if (opponents.find(client) != opponents.end()) {
            tcp::socket* opponent_client = opponents[client];
            opponent_client->close();
        }
        client->close();
    }

    void client_run(tcp::socket* client, const Json::Value& user) {
        while (true) {
            Json::Value response = get_event(client);
            if (response.isNull()) {
                close_connection(client);
                break;
            }
            std::string event_name = response["event"].asString();
            Json::Value content = response["content"];
            if (event_name == "board_update") {
                event_board_update(client, user, content);
            } else if (event_name == "match_request") {
                event_match_request(client, user, content);
            }
        }
    }
};

const std::string SocketServer::HOST_ADDR = "0.0.0.0";

int main() {
    boost::asio::io_context io_context;
    SocketServer server(io_context);
    io_context.run();
    return 0;
}
