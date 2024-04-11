import socket
import keyboard


class TriviaGameClient:
    # Initializes the client with a player name, server address,
    # TCP socket, and buffer size. Initially, the state of the client is set to "looking_for_server".
    def __init__(self, player_name):
        self.player_name = player_name
        self.server_address = None
        self.tcp_socket = None
        self.state = "looking_for_server"
        self.buffer_size = 1024
        self.server_port = 13117
        self.udp_socket = None

    # Starts the client by setting up a UDP socket and listening for offers from the server.
    def start(self):
        self.udp_socket = self.setup_udp_socket()
        self.listen_for_offers(self.udp_socket)

    # Sets up a UDP socket for receiving offer requests. It binds the socket to localhost on port 13117.
    def setup_udp_socket(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set SO_REUSEPORT option
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.bind(('', 13117))
        return udp_socket


    # Listens for offer requests from the server. It uses select to check if there is any
    # data available to read on the UDP socket. If an offer is received, it calls handle_offer method.
    def listen_for_offers(self, udp_socket):
        data = None
        while True:
            print("\033[1;36m"+'\033[100m'+"Client started, listening for offer requests..."+'\033[0m')
            while data is None:
                try:
                    data, addr = udp_socket.recvfrom(self.buffer_size)
                except Exception as e:
                    pass

            tcp_port_bytes = data[37:] # Take the tcp port from the offer message
            tcp_port = int.from_bytes(tcp_port_bytes, 'big') # encode the tcp port
            self.server_port = tcp_port
            self.handle_offer(data[5:37].decode('utf-8'), addr[0]) # Activate handle_offer function, send the server's name and address

            if self.state == "connecting_to_server":
                self.connect_to_server() # Connect to server via tcp
                self.udp_socket.close()

            if self.state == "game_mode":
                self.game_mode()




    # Handles the offer received from the server. It sets the server address and changes
    # the state to "connecting_to_server".
    def handle_offer(self, server_name, server_address):
        self.state = "connecting_to_server"
        self.server_address = server_address
        print("\033[1m"+"\033[1;34m"+'\033[100m'+f"Received offer from server {server_name} at address {server_address}, attempting to connect..."+'\033[0m')

    # Tries to connect to the server using TCP socket. If successful, it sends
    # the player name to the server and changes the state to "game_mode".
    def connect_to_server(self):
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.connect((self.server_address, self.server_port))
            self.tcp_socket.sendall((self.player_name + '\n').encode('utf-8'))
            self.state = "game_mode"
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            self.state = "looking_for_server"

    # Enters the game mode where it waits for inputs from the server or user.
    # It uses recvfrom to wait for data on the TCP socket or user input from keyboard.
    # It sends user input to the server and prints messages received from the server.
    def game_mode(self):
        while self.state == "game_mode":
            try:
                data, _ = self.tcp_socket.recvfrom(self.buffer_size) #recive the data from the tcp socket
                if not data:
                    continue
                decoded_data = data.decode()
                if not decoded_data.startswith("Game over, sending out offer requests..."): # The game is on
                    print("\033[1;35m"+data.decode())

                if "Game over, sending out offer requests..." in decoded_data: # The game is ended, a winner is found
                    print("\033[0;31m"+"Server disconnected, listening for offer requests...")
                    self.tcp_socket.close()
                    self.state = "looking_for_server"
                    self.udp_socket = self.setup_udp_socket()
                    self.listen_for_offers(self.udp_socket) # Back to listening for offers
                    break
                if "True Or False: " in decoded_data: # If get a question from the server
                    key = keyboard.read_event().name # Get input from user by keyboard press
                    print("\n")
                    self.tcp_socket.sendall(key.encode())

            except socket.error as e: # If the server disconnect
                self.tcp_socket.close()
                self.state = "looking_for_server"
                print("\033[0;31m" + "Server disconnected, listening for offer requests...")
                self.udp_socket = self.setup_udp_socket()
                self.listen_for_offers(self.udp_socket)
                break  # Exit the loop



#creates an instance of TriviaGameClient, sets the player name, and starts the client.
if __name__ == "__main__":
    player_name = "RoniTheBitch"  # Change this to your desired player name
    client = TriviaGameClient(player_name)
    client.start()