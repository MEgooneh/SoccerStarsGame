from server.python_server.SocketServer import run_server as run_python_server
import os
import subprocess
import platform
import sys

def run_cpp_server():
    compile_command = ["g++", "-o", "cppserver.out", "server/cpp_server/SocketServer.cpp"]
    print("Compiling:", " ".join(compile_command))
    compile_result = subprocess.run(compile_command, capture_output=True, text=True)
    if compile_result.returncode != 0:
        print("Compilation failed:")
        print(compile_result.stderr)
        return
    
    print("Compilation succeeded")
    
    run_command = [os.path.join(".", "cppserver.out")]
    print("Running:", " ".join(run_command))
    subprocess.run(run_command, capture_output=True, text=True)

if __name__ == '__main__':
    server_type = input("1) Python Server\n2) C++ server(only for unix-based OSs):\n>>>")

    match server_type:
        case "1":
            run_python_server()
        case "2":
            run_cpp_server()
        case _:
            raise Exception("Invalid server type")