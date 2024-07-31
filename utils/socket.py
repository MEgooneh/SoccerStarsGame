import socket
import struct


def socket_ordered_send_message(socket: socket.socket, message: str):
    # prefix each message with a 4-byte 'length' . which is length of the message
    message = message.encode('utf-8')
    message_length = struct.pack('!I', len(message))
    socket.sendall(message_length + message)

def socket_ordered_recvall(socket: socket.socket, n: int | None):
    data = b''
    while len(data) < n:
        packet = socket.recv(n - len(data))
        if not packet:
            raise Exception("Connection Closed")
        data += packet
    return data

def socket_ordered_recv_message(socket: socket.socket):
    try:
        raw_msglen = socket_ordered_recvall(socket, 4)
    except:
        raise Exception("Connection Closed")
    if not raw_msglen:
        raise Exception("Connection Closed")
    msglen = struct.unpack('!I', raw_msglen)[0]
    return socket_ordered_recvall(socket, msglen)
