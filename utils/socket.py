import socket
import struct


def socket_ordered_send_message(socket: socket.socket, message: str):
    # prefix each message with a 4-byte 'length' . which is length of the message
    message = message.encode('utf-8')
    message_length = struct.pack('!I', len(message))
    socket.sendall(message_length + message)

def socket_ordered_recvall(socket: socket.socket, n: int):
    data = b''
    while len(data) < n:
        packet = socket.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def socket_ordered_recv_message(socket: socket.socket):
    raw_msglen = socket_ordered_recvall(socket, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('!I', raw_msglen)[0]
    return socket_ordered_recvall(socket, msglen)
