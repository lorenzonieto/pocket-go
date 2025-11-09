import socket
import selectors
import pygame

class Multiplayer:
    def __init__(self, sock, selector):
        self.socket = sock
        self.selector = selector
    # send move tuple to opponent
    def send_move(self, move):
        move_data = (str(move[0]) + " " + str(move[1])).encode()
        move_prepend = len(move_data)
        self.socket.sendall(str(move_prepend).encode() + move_data)
    # get the specified amount of bytes from the connection
    def get_bytes(self, n):
        data = b""
        data_len = 0
        while data_len < n:
            tmp = self.socket.recv(n - data_len)
            if not tmp:
                return False
            data += tmp
            data_len = len(data)
        return data
    # get the message from the connection when prepended with length
    def get_prepend_bytes(self):
        msg_len_raw = self.get_bytes(1)
        if not msg_len_raw:
            return False
        msg_len = int(msg_len_raw.decode())
        msg = self.get_bytes(msg_len)
        if not msg:
            return False
        return msg
    # get move tuple that opponent has sent
    def receive_move(self):
        data = self.get_prepend_bytes()
        if not data:
            return False
        nums = data.decode().split()
        return (int(nums[0]), int(nums[1]))
    # send game initialization variables to opponent if hosting
    def send_init_list(self, size, bonus, turn):
        size_str = str(size)
        size_len = str(len(size_str))
        bonus_str = str(bonus)
        bonus_len = str(len(bonus_str))
        if turn:
            color = "1"
        else:
            color = "0"
        string = size_len + size_str + bonus_len + bonus_str + color 
        self.socket.sendall(string.encode())
    # get game initialization variables
    def get_init(self):
        while True:
            if ready_for_read(self.socket, self.selector):
                size = int(self.get_prepend_bytes().decode())
                bonus = float(self.get_prepend_bytes().decode())
                turn = int(self.get_bytes(1).decode())
                if turn == 0:
                    turn = True
                else:
                    turn = False
                return (size, bonus, turn)
    def end(self):
        self.selector.unregister(self.socket)
        self.socket.close()
# check whether the given socket is ready for reading
# the given selector must have the socket registered for read events
def ready_for_read(sock, sel):
    ready = False
    events = sel.select(0)
    for key, mask in events:
        if key.fd == sock.fileno() and mask & selectors.EVENT_READ:
            ready = True
    return ready

# get connection to opponent
def get_connection(host, join):
    # return connection to opponent and socket selector if hosting
    if host:
        # create listening socket
        lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lsock.bind(("127.0.0.1", 33322))
        lsock.listen(1)
        # create selector to poll for events
        sel = selectors.DefaultSelector()
        sel.register(lsock, selectors.EVENT_READ, data=None)
        # listen for connection attempts, or quit
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # user has closed pygame window
                    sel.unregister(lsock)
                    lsock.close()
                    return (False, False)
            if ready_for_read(lsock, sel):
                connection, address = lsock.accept()
                sel.unregister(lsock)
                sel.register(connection, selectors.EVENT_READ, data=None)
                lsock.close()
                return (connection, sel)
    # return connection to host and socket selector if joining
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((join, 33322))

        sel = selectors.DefaultSelector()
        sel.register(sock, selectors.EVENT_READ, data=None)
        return (sock, sel)