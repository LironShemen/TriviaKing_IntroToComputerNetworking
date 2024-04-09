import socket
import sys
import select
import Server

class TriviaGameClient:
    #Initializes the client with a player name, server address,
    # TCP socket, and buffer size. Initially, the state of the client is set to "looking_for_server".
    def __init__(self, player_name):
        self.player_name = player_name
        self.server_address = None
        self.tcp_socket = None
        self.state = "looking_for_server"
        self.buffer_size = 1024
        self.server_port = 13117

    #Starts the client by setting up a UDP socket and listening for offers from the server.
    def start(self):
        udp_socket = self.setup_udp_socket()
        self.listen_for_offers(udp_socket)

    #Sets up a UDP socket for receiving offer requests. It binds the socket to localhost on port 12345.
    def setup_udp_socket(self):
        # port = Server.find_available_port(12345)
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set SO_REUSEPORT option if available
        if hasattr(socket, 'SO_REUSEPORT'):
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        udp_socket.bind(('0.0.0.0', 13117))
        return udp_socket


    #Listens for offer requests from the server. It uses select to check if there is any
    # data available to read on the UDP socket. If an offer is received, it calls handle_offer method.
    def listen_for_offers(self, udp_socket):
        print("Client started, listening for offer requests...")

        data, addr = udp_socket.recvfrom(self.buffer_size)

        tcp_port_bytes = data[37:]
        tcp_port = int.from_bytes(tcp_port_bytes, 'big')
        self.server_port = tcp_port
        self.handle_offer(data[5:37].strip(), addr[0])

        if self.state == "connecting_to_server":
            self.connect_to_server()

        if self.state == "game_mode":
            self.game_mode()

    #Handles the offer received from the server. It sets the server address and changes
    # the state to "connecting_to_server".
    def handle_offer(self, server_name, server_address):
        self.state = "connecting_to_server"
        self.server_address = server_address
        print(f"Received offer from server {server_name} at address {server_address}, attempting to connect...")

    #Tries to connect to the server using TCP socket. If successful, it sends
    # the player name to the server and changes the state to "game_mode".
    def connect_to_server(self):
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.connect(('192.168.230.20', self.server_port))
            self.tcp_socket.sendall((self.player_name + '\n').encode('utf-8'))
            self.state = "game_mode"
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            self.state = "looking_for_server"

    # Enters the game mode where it waits for inputs from the server or user.
    # It uses select to wait for data on the TCP socket or user input from stdin.
    # It sends user input to the server and prints messages received from the server.
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

#creates an instance of TriviaGameClient, sets the player name, and starts the client.
if __name__ == "__main__":
    player_name = "TeamName"  # Change this to your desired player name
    client = TriviaGameClient(player_name)
    client.start()
