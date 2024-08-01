import tkinter as tk
from tkinter import messagebox
from tkinter import font as tkfont
import threading
import json

from src.Game import Game
from src.Models import User, Match, MatchRequest
from src.SocketClient import SocketClient

from pygame.display import set_caption as set_pygame_window_title




def searching_for_opponent(username, socket):
    me = User(username=username)
    socket.register_user(user=me)
    game = Game(is_multiplayer=True, socket_client=socket)
    socket.make_match_request()
    match = socket.pend_for_match_start()
    

    game.left_side_name = match.left_user.username
    game.right_side_name = match.right_user.username
    game.pygame_init()
    game.load_assets()
    game.board.init_objects()
    set_pygame_window_title(username)
    root.destroy()
    game.run()
    

def setup_initial_ui():
    for widget in root.winfo_children():
        widget.destroy()

    multiplayer_button = tk.Button(root, text="MULTIPLAYER", command=multiplayer_action, 
                                   font=button_font, bg=button_color, fg=text_color, width=15, height=2)
    multiplayer_button.pack(pady=10)

    monoplayer_button = tk.Button(root, text="MONOPLAYER", command=monoplayer_action, 
                                  font=button_font, bg=button_color, fg=text_color, width=15, height=2)
    monoplayer_button.pack(pady=10)

    exit_button = tk.Button(root, text="EXIT", command=root.destroy, 
                            font=button_font, bg=exit_button_color, fg=text_color, width=15, height=2)
    exit_button.pack(pady=10)

def monoplayer_action():
    root.destroy()
    game = Game()
    game.pygame_init()
    game.load_assets()
    game.board.init_objects()
    game.run()

def submit_username(username, socket):
    if username:
        tk.Label(root, text="Please wait...", font=button_font, bg=bg_color, fg=text_color).pack(pady=10)
        searching_for_opponent(username, socket)
    else:
        messagebox.showwarning("Warning", "Username cannot be empty!")

def get_username(socket):
    for widget in root.winfo_children():
        widget.destroy()
    
    tk.Label(root, text="Enter Username:", font=button_font, bg=bg_color, fg=text_color).pack(pady=10)
    username_entry = tk.Entry(root, font=button_font)
    username_entry.pack(pady=10)

    submit_button = tk.Button(root, text="Submit", command=lambda: submit_username(username_entry.get(), socket), 
                              font=button_font, bg=button_color, fg=text_color, width=15, height=2)
    submit_button.pack(pady=10)

    exit_button = tk.Button(root, text="EXIT", command=root.destroy, 
                            font=button_font, bg=exit_button_color, fg=text_color, width=15, height=2)
    exit_button.pack(pady=10)

def server_select_action(ip, port):
    try:
        socket = SocketClient(server_addr=(ip, port))
    except:
        messagebox.showwarning(title="Network error", message=f"Connection to server Refused! make sure server is up and accessible by you\n {ip=}:{port=}")
    else:
        get_username(socket)
    
def multiplayer_action():
    for widget in root.winfo_children():
        widget.destroy()
    
    tk.Label(root, text="Select a server:", font=button_font, bg=bg_color, fg=text_color).pack(pady=10)
    
    servers_list = []
    with open("servers.json") as f:
        servers_list = json.load(f)

    for addr in servers_list:
        ip = str(addr[0])
        port = int(addr[1])
        tk.Button(root, text=f"{addr[0]}:{addr[1]}", command=lambda ip=ip, port=port: server_select_action(ip, port),font=button_font, bg=bg_color, fg=text_color).pack(pady=10)


    exit_button = tk.Button(root, text="EXIT", command=root.destroy, 
                            font=button_font, bg=exit_button_color, fg=text_color, width=15, height=2)
    exit_button.pack(pady=10)



def display_loading_animation():
    global loading_label, loading_animation_running
    loading_label = tk.Label(root, text="", font=button_font, bg=bg_color, fg=text_color)
    loading_label.pack(pady=10)
    loading_animation_running = True
    searching_for_opponent_animate_loading(0)

def searching_for_opponent_animate_loading(step):
    if loading_animation_running:
        loading_text = "." * (step % 4)
        loading_label.config(text=f"Searching for your opponent{loading_text}")
        root.after(500, searching_for_opponent_animate_loading, step + 1)

def stop_loading_animation():
    global loading_animation_running
    loading_animation_running = False



root = tk.Tk()
root.title("Game Menu")
root.geometry("700x400")

bg_color = "#2e2e2e"
button_color = "#4CAF50"
exit_button_color = "#F44336"
text_color = "#FFFFFF"
button_font = tkfont.Font(family="Helvetica", size=14, weight="bold")

root.configure(bg=bg_color)

loading_label = None
loading_animation_running = False

setup_initial_ui()

root.mainloop()
