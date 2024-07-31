from server.python_server.SocketServer import run_server as run_python_server


if __name__ == '__main__':
    server_type = input("1) Python Server\n2) C++ server\n:")

    match server_type:
        case "1":
            run_python_server()
        case "2":
            pass
        case _:
            raise Exception("Invalid server type")