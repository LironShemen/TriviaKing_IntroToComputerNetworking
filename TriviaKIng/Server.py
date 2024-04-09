import math
import socket
import threading
import time
import random

import select

# Global variables


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

# List to use connected clients socket
connected_clients_sockets = []

# Dictionary to take data from socket while playing, and get the name of the client with the socket
playerName_with_his_socket = {}

class FoodTriviaServer:
    def __init__(self):
        #thread for the broadcact
        self.udp_thread = threading.Thread(target=self.send_offer_message)
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_thread.daemon = True
        self.check_winner_dictionary = {}
        self.Game_Started = False
        self.clients_threads = []
        self.is_player_answer_right = False
        self.TCP_PORT = 5556
        # Helper list to disqualifies wrong player for one round
        self.temp_socket_list = []
        self.MAGIC_COOKIE = b'\xab\xcd\xdc\xba'
        self.SERVER_NAME = "SapirAndLironMagicFoodieServer#1"
        self.UDP_PORT = 13117
        self.QUESTION_TIMEOUT = 10  # seconds
        self.GAME_QUESTION_COUNT = 20
        self.GAME_OVER = False
        self.MY_IP = 0

    def start(self):
        global TCP_PORT
        self.MY_IP = get_my_ip()
        self.udp_thread.start()
        #open tcp socket
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.TCP_PORT = find_available_port(self.TCP_PORT)
        self.tcp_socket.bind((self.MY_IP, self.TCP_PORT))
        self.tcp_socket.listen()
        print("Server started, listening on IP address "+ f'{self.MY_IP}')
        # timer_10sec_no_client = threading.Timer(10, self.time_out_handler)
        while True:
            try:
                client_socket, address = self.tcp_socket.accept()
                connected_clients_sockets.append(client_socket)
                threading.Timer(10, self.time_out_handler).start()
                print(f"New connection from {address}")
                client_thread = threading.Thread(target=self.handle_tcp_client, args=(client_socket,))
                self.clients_threads.append(client_thread)
                client_thread.start()
            except TimeoutError:
                # if(len(connected_clients)==1):
                #     print("Can't start game with only one player. Keep waiting for another player")
                    pass
                #print("Server manually stopped.")
        self.tcp_socket.close()
        print("Game over, sending out offer requests...")
        self.udp_thread.join()
        # global UDP_PORT
        # UDP_PORT += 1
        self.udp_thread = threading.Thread(target=self.send_offer_message)
        self.udp_thread.daemon = True
        self.udp_thread.start()

    def send_offer_message(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.bind((f"{self.MY_IP}", self.UDP_PORT))
        tcp_to_bits = self.TCP_PORT
        servernameencode = self.SERVER_NAME
        offer_message = self.MAGIC_COOKIE + b'\x02' + servernameencode.encode().ljust(32) + tcp_to_bits.to_bytes(2,                                                                                                        'big')
        while not self.Game_Started:
            try:
                udp_socket.sendto(offer_message, ('<broadcast>', self.UDP_PORT))
                # time.sleep(1)  # Adjust as needed to control the rate of message sending
            except Exception as e:
                print("Error sending UDP offer message:", e)
                # Handle the error condition appropriately
        udp_socket.close()

    def handle_tcp_client(self, client_socket):
        global connected_clients
        # Receive player name from client
        player_name = client_socket.recv(1024).decode().strip()
        #print(f"Player connected: {player_name}")
        connected_clients.append(player_name)
        playerName_with_his_socket[client_socket] = player_name
        self.check_winner_dictionary[player_name] = [None,0]


    def run_game(self):
        global connected_clients, connected_clients_sockets
        # Choose random trivia question
        question = random.choice(list(TRIVIA_QUESTIONS.keys()))
        print("\n==\nWelcome to the -Sapir And Liron Magic Foodie Server #1-, where we are answering trivia questions about food.")
        #SEND WELCOME TO ALL CLIENTS!!!!!!!!!!!!!!!!!!!
        for idx, player in enumerate(connected_clients, start=1):
            print(f"Player {idx}: {player}")
        print("==")
        print(question)
        for client_socket in connected_clients_sockets:
            client_socket.sendall(question.encode())

        while not self.GAME_OVER:
            self.temp_socket_list = connected_clients_sockets
            timer = threading.Timer(10,threading.Event().set)
            timer.start()
            threads = []

            for s in connected_clients_sockets:
                client_thread = threading.Thread(target=self.handle_client, args=(s, TRIVIA_QUESTIONS[question],))
                threads.append(client_thread)
                client_thread.start()

            for t in threads:
                t.join()

            timer.cancel()



    def time_out_handler(self):
        if(len(connected_clients) == 1):
            print("Can't start game with only one player. Keep waiting for another player")
            #connected_clients_sockets[0].sendall("Can't start game with only one player. Keep waiting for another player".encode())
        elif (len(connected_clients) > 1):
                self.Game_Started = True
                self.run_game()

    def handle_client(self, client_socket, correct_answer):
        start_time = time.time()
        player = playerName_with_his_socket[client_socket]
        answer = self.receive_answer(client_socket)
        self.check_winner_dictionary[player] = [answer,time.time() - start_time]
        if answer in correct_answer and client_socket in self.temp_socket_list:
            self.GAME_OVER = True
            self.Game_Started = False
            ###########SENT TO ALL CLIENTS!!!!!!!!!!!!!!!!!!
            print(f"{player} is correct! {player} wins!")
            client_socket.sendall(f"{player} is correct! {player} wins!".encode())
            print("Game over!")
            client_socket.sendall("Game over!".encode())
            print(f"Congratulations to the winner: {player}")
            client_socket.sendall(f"Congratulations to the winner: {player}".encode())
            ###can add game statistics
        if answer not in correct_answer:
            self.temp_socket_list.remove(client_socket)


    def receive_answer(self, client_socket):
        while True:
            ready, _, _ = select.select([client_socket], [], [], 1)  # Wait for 1 second for input

            if ready:
                # Receive answer from client
                answer = client_socket.recv(1024).decode().strip()
                return answer




# Two helper functions to deal with a situation when i want to listen to a
# port that is already used by somebody else
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port):
    port = start_port
    while is_port_in_use(start_port):
        port += 1
    return port


def get_my_ip():
    try:
        # Create a socket object
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect to a known address
        s.connect(("8.8.8.8", 80))
        # Get the socket's own address
        ip_address = s.getsockname()[0]
        # Close the socket
        s.close()
        return ip_address
    except Exception as e:
        print("Error occurred while retrieving IP address:", e)
        return None

if __name__ == "__main__":
    server = FoodTriviaServer()
    server.start()
