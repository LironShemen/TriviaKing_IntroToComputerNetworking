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
TRIVIA_QUESTIONS = {
    "Carrots were originally purple": ['Y', 'T', 1],
    "Bananas are berries.": ['F', 'N', 0],
    "Peanuts are not nuts, they are legumes.": ['Y', 'T', 1],
    "Honey never spoils.": ['Y', 'T', 1],
    "Eating celery burns more calories than it contains.": ['F', 'N', 0],
    "Almonds are a member of the peach family.": ['F', 'N', 0],
    "Avocados are poisonous to birds.": ['Y', 'T', 1],
    "Rice contains more arsenic than other grains.": ['F', 'N', 0],
    "Apples float in water because they are 25% air": ['Y', 'T', 1],
    "Carrots improve night vision": ['F', 'N', 0],
    "Spinach is a good source of iron": ['Y', 'T', 1],
    "Chocolate causes acne": ['F', 'N', 0],
    "Garlic can help lower blood pressure": ['Y', 'T', 1],
    "Milk helps to create mucus": ['F', 'N', 0],
    "Pineapple can tenderize meat because it contains bromelain": ['Y', 'T', 1],
    "Coffee stunts your growth": ['F', 'N', 0],
    "Eating spicy food can boost metabolism": ['Y', 'T', 1],
    "Turkey makes you sleepy because it contains high levels of tryptophan": ['F', 'N', 0],
    "Coconut water is sterile and can be used as an emergency IV hydration fluid": ['Y', 'T', 1],
    "Eating cheese before bed gives you nightmares": ['F', 'N', 0]
}

# Mutex for thread synchronization
mutex = threading.Lock()

# List to keep track of connected clients
connected_clients = []

class FoodTriviaServer:
    def __init__(self):
        #thread for the broadcact
        self.udp_thread = threading.Thread(target=self.send_offer_message)
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_thread.daemon = True
        self.check_winner_dictionary = {}

    def start(self):
        self.udp_thread.start()
        #open tcp socket
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.bind(('0.0.0.0', TCP_PORT))
        self.tcp_socket.listen(5)
        print("Server started, listening on IP address 172.1.0.4")
        timer_10sec_no_client = threading.Timer(10, self.time_out_handler)
        while True:
            try:
                client_socket, address = self.tcp_socket.accept()
                timer_10sec_no_client.start()
                #print(f"New connection from {address}")
                client_thread = threading.Thread(target=self.handle_tcp_client, args=(client_socket,))
                client_thread.start()
            except TimeoutError:
                if(len(connected_clients)>1):
                    self.run_game()
                #print("Server manually stopped.")
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
        #print(f"Player connected: {player_name}")
        connected_clients.append(player_name)
        self.check_winner_dictionary[player_name] = [None,0]


        # while not GAME_OVER:
        #     try:
        #         client_socket.settimeout(QUESTION_TIMEOUT)
        #         data = client_socket.recv(1024).decode().strip()
        #         if data.lower() == 'true':
        #             print(f"{player_name} answered correctly!")
        #             with mutex:
        #                 if not GAME_OVER:
        #                     print(f"\nGame over!\nCongratulations to the winner: {player_name}")
        #                     GAME_OVER = True
        #         else:
        #             print(f"{player_name} answered incorrectly!")
        #             client_socket.sendall(b"Incorrect! You are disqualified.\n")
        #             connected_clients.remove(player_name)
        #             client_socket.close()
        #             break
        #     except socket.timeout:
        #         print(f"{player_name} didn't answer.")
        #         client_socket.sendall(b"No answer received. You are disqualified.\n")
        #         connected_clients.remove(player_name)
        #         client_socket.close()
        #         break

    def run_game(self):
        global GAME_OVER, connected_clients
        # Choose random trivia question
        question = random.choice(TRIVIA_QUESTIONS.keys())
        print("\n==\nWelcome to the -Sapir And Liron Magic Foodie Server #1-, where we are answering trivia questions about food.")
        for idx, player in enumerate(connected_clients, start=1):
            print(f"Player {idx}: {player}")
        print("==")
        print(question)

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


        # Wait for answers or timeout
        start_time = time.time()
        while time.time() - start_time < QUESTION_TIMEOUT:
            if GAME_OVER:
                return  # Game is already over, exit the loop
            time.sleep(1)  # Wait for 1 second before checking again
        # Timeout occurred, no one answered the question
        print("No one answered the question. Choosing another question...")

        return

    def time_out_handler(self):
        if(len(connected_clients) == 1):
            raise TimeoutError("Can't start game with only one player. Try again later")
        else:
            raise TimeoutError()

if __name__ == "__main__":
    server = FoodTriviaServer()
    server.start()