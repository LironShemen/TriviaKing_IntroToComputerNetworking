import socket
import threading
import time
import random

# Global variables
MAGIC_COOKIE = b'\xab\xcd\xdc\xba'
SERVER_NAME = "SapirAndLironMagicFoodieServer#1"
UDP_PORT = 5555
TCP_PORT = 5556
QUESTION_TIMEOUT = 10  # seconds
GAME_QUESTION_COUNT = 20
GAME_OVER = False

# Trivia questions about food
TRIVIA_QUESTIONS = [
    "Apples float in water, because they are 25% air.",
    "Carrots were originally purple.",
    "Bananas are berries.",
    "Peanuts are not nuts, they are legumes.",
    "Lemons contain more sugar than strawberries.",
    "Honey never spoils.",
    "Eating celery burns more calories than it contains.",
    "Almonds are a member of the peach family.",
    "Avocados are poisonous to birds.",
    "Rice contains more arsenic than other grains."
]

# Mutex for thread synchronization
mutex = threading.Lock()

# List to keep track of connected clients
connected_clients = []

class FoodTriviaServer:
    def __init__(self):
        self.udp_thread = threading.Thread(target=self.send_offer_message)
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_thread.daemon = True

    def start(self):
        self.udp_thread.start()
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.bind(('0.0.0.0', TCP_PORT))
        self.tcp_socket.listen(5)
        print("Server started, listening on IP address 172.1.0.4")
        while True:
            try:
                client_socket, address = self.tcp_socket.accept()
                print(f"New connection from {address}")
                client_thread = threading.Thread(target=self.handle_tcp_client, args=(client_socket,))
                client_thread.start()
            except KeyboardInterrupt:
                print("Server manually stopped.")
                break
        self.tcp_socket.close()
        print("Game over, sending out offer requests...")
        self.udp_thread.join()
        global UDP_PORT
        UDP_PORT += 1
        self.udp_thread = threading.Thread(target=self.send_offer_message)
        self.udp_thread.daemon = True
        self.udp_thread.start()

    def send_offer_message(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        offer_message = MAGIC_COOKIE + b'\x02' + SERVER_NAME.encode().ljust(32) + UDP_PORT.to_bytes(2, 'big')
        udp_socket.sendto(offer_message, ('172.1.0.4', UDP_PORT))
        udp_socket.close()

    def handle_tcp_client(self, client_socket):
        global GAME_OVER, connected_clients

        # Receive player name from client
        player_name = client_socket.recv(1024).decode().strip()
        print(f"Player connected: {player_name}")
        connected_clients.append(player_name)

        while not GAME_OVER:
            try:
                client_socket.settimeout(QUESTION_TIMEOUT)
                data = client_socket.recv(1024).decode().strip()
                if data.lower() == 'true':
                    print(f"{player_name} answered correctly!")
                    with mutex:
                        if not GAME_OVER:
                            print(f"\nGame over!\nCongratulations to the winner: {player_name}")
                            GAME_OVER = True
                else:
                    print(f"{player_name} answered incorrectly!")
                    client_socket.sendall(b"Incorrect! You are disqualified.\n")
                    connected_clients.remove(player_name)
                    client_socket.close()
                    break
            except socket.timeout:
                print(f"{player_name} didn't answer.")
                client_socket.sendall(b"No answer received. You are disqualified.\n")
                connected_clients.remove(player_name)
                client_socket.close()
                break

    def run_game(self):
        global GAME_OVER, connected_clients

        # Wait for clients to connect
        time.sleep(10)
        if not connected_clients:
            print("No players connected. Waiting for connections...")
            return

        # Choose random trivia question
        question = random.choice(TRIVIA_QUESTIONS)
        print("\n==\nWelcome to the -Sapir And Liron Magic Foodie Server #1-, where we are answering trivia questions about food.")
        for idx, player in enumerate(connected_clients, start=1):
            print(f"Player {idx}: {player}")
        print("==")
        print(question)

        # Wait for answers or timeout
        start_time = time.time()
        while time.time() - start_time < QUESTION_TIMEOUT:
            if GAME_OVER:
                return  # Game is already over, exit the loop
            time.sleep(1)  # Wait for 1 second before checking again

        # Timeout occurred, no one answered the question
        print("No one answered the question. Choosing another question...")
        return

if __name__ == "__main__":
    server = FoodTriviaServer()
    server.start()