import socket
import sys
import time

import select
import Server
import keyboard

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
        self.udp_socket = None

    #Starts the client by setting up a UDP socket and listening for offers from the server.
    def start(self):
        self.udp_socket = self.setup_udp_socket()
        self.listen_for_offers(self.udp_socket)

    #Sets up a UDP socket for receiving offer requests. It binds the socket to localhost on port 12345.
    def setup_udp_socket(self):
        # port = Server.find_available_port(12345)
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #Set SO_REUSEPORT option if available
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.bind(('', 13117))
        return udp_socket


    #Listens for offer requests from the server. It uses select to check if there is any
    # data available to read on the UDP socket. If an offer is received, it calls handle_offer method.
    def listen_for_offers(self, udp_socket):
        print("Client started, listening for offer requests...")

        data, addr = udp_socket.recvfrom(self.buffer_size)

        tcp_port_bytes = data[37:]
        tcp_port = int.from_bytes(tcp_port_bytes, 'big')
        self.server_port = tcp_port
        self.handle_offer(data[5:37].decode('utf-8'), addr[0])

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
            self.tcp_socket.connect((self.server_address, self.server_port))
            self.tcp_socket.sendall((self.player_name + '\n').encode('utf-8'))
            self.state = "game_mode"
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            self.state = "looking_for_server"

    # Enters the game mode where it waits for inputs from the server or user.
    # It uses select to wait for data on the TCP socket or user input from stdin.
    # It sends user input to the server and prints messages received from the server.
    def game_mode(self):
        # while True:
        #     try:
        #         data, _ = self.tcp_socket.recvfrom(self.buffer_size)
        #         if not data:
        #             continue
        #         decoded_data = data.decode()
        #         if not decoded_data.startswith("Game over, sending out offer requests..."):
        #             print(data.decode())
        #         # Get input from the user
        #         if decoded_data.startswith("Game over, sending out offer requests..."):
        #             print("Server disconnected, listening for offer requests...")
        #             self.tcp_socket.close()
        #             self.state = "looking_for_server"
        #             self.listen_for_offers(self.udp_socket)
        #         if decoded_data.startswith("Qusetion: "):
        #             key = keyboard.read_event().name
        #             print("\n")
        #             if key.strip():  # Check if the answer is not empty (user input something)
        #                 self.tcp_socket.sendall(key.encode())  # Send the answer to the server
        #             else:  # If the user didn't input an answer
        #                 self.tcp_socket.sendall(b"\n")
        #     except:
        #         pass
        while True:
            try:
                # List of sockets to check for input
                sockets_list = [self.tcp_socket]

                # Use select to wait for input on sockets
                read_sockets, _, _ = select.select(sockets_list, [], [])

                for socks in read_sockets:
                    if socks == self.tcp_socket:
                        # Receive data from the server
                        message = socks.recv(2048)
                        print(message.decode())  # Print received message
                    else:
                        # Read input from the keyboard
                        message = sys.stdin.readline()
                        self.tcp_socket.send(message.encode())  # Send input to the server
                        sys.stdout.flush()

            except Exception as e:
                print(f"Error occurred: {e}")
                break



#creates an instance of TriviaGameClient, sets the player name, and starts the client.
if __name__ == "__main__":
    player_name = "SapirLetMeWin"  # Change this to your desired player name
    client = TriviaGameClient(player_name)
    client.start()
