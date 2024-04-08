import socket
import sys
import select

class TriviaGameClient:
    def __init__(self, player_name):
        self.player_name = player_name
        self.server_address = None
        self.tcp_socket = None
        self.state = "looking_for_server"
        self.buffer_size = 1024

    def start(self):
        udp_socket = self.setup_udp_socket()
        self.listen_for_offers(udp_socket)

    def setup_udp_socket(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set SO_REUSEPORT option if available
        if hasattr(socket, 'SO_REUSEPORT'):
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        udp_socket.bind(('localhost', 12345))
        return udp_socket

    def listen_for_offers(self, udp_socket):
        print("Client started, listening for offer requests...")

        while True:
            ready_sockets, _, _ = select.select([udp_socket], [], [], 1)

            if udp_socket in ready_sockets:
                data, addr = udp_socket.recvfrom(self.buffer_size)
                message = data.decode('utf-8')
                self.handle_offer(message, addr[0])

            if self.state == "connecting_to_server":
                self.connect_to_server()

            if self.state == "game_mode":
                self.game_mode()

    def handle_offer(self, message, server_address):
        self.state = "connecting_to_server"
        self.server_address = server_address
        print(f"Received offer from server {message} at address {server_address}, attempting to connect...")

    def connect_to_server(self):
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.connect((self.server_address, 12346))
            self.tcp_socket.sendall((self.player_name + '\n').encode('utf-8'))
            self.state = "game_mode"
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            self.state = "looking_for_server"

    def game_mode(self):
        inputs = [self.tcp_socket, sys.stdin]

        while True:
            readable, _, _ = select.select(inputs, [], [])
            for sock in readable:
                if sock == self.tcp_socket:
                    data = sock.recv(self.buffer_size)
                    if not data:
                        print("Server disconnected, listening for offer requests...")
                        self.state = "looking_for_server"
                        return
                    else:
                        print(data.decode('utf-8'), end='')
                elif sock == sys.stdin:
                    user_input = sys.stdin.readline().strip()
                    self.tcp_socket.sendall((user_input + '\n').encode('utf-8'))

if __name__ == "__main__":
    player_name = "TeamName"  # Change this to your desired player name
    client = TriviaGameClient(player_name)
    client.start()
