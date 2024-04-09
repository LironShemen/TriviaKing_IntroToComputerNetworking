import math
import socket
import threading
import time
import random

import select

# Global variables


# Trivia questions about food
TRIVIA_QUESTIONS = {
    "Qusetion: Carrots were originally purple": ['Y', 'T', 1],
    "Qusetion: Bananas are berries.": ['F', 'N', 0],
    "Qusetion: Peanuts are not nuts, they are legumes.": ['Y', 'T', 1],
    "Qusetion: Honey never spoils.": ['Y', 'T', 1],
    "Qusetion: Eating celery burns more calories than it contains.": ['F', 'N', 0],
    "Qusetion: Almonds are a member of the peach family.": ['F', 'N', 0],
    "Qusetion: Avocados are poisonous to birds.": ['Y', 'T', 1],
    "Qusetion: Rice contains more arsenic than other grains.": ['F', 'N', 0],
    "Qusetion: Apples float in water because they are 25% air": ['Y', 'T', 1],
    "Qusetion: Carrots improve night vision": ['F', 'N', 0],
    "Qusetion: Spinach is a good source of iron": ['Y', 'T', 1],
    "Qusetion: Chocolate causes acne": ['F', 'N', 0],
    "Qusetion: Garlic can help lower blood pressure": ['Y', 'T', 1],
    "Qusetion: Milk helps to create mucus": ['F', 'N', 0],
    "Qusetion: Pineapple can tenderize meat because it contains bromelain": ['Y', 'T', 1],
    "Qusetion: Coffee stunts your growth": ['F', 'N', 0],
    "Qusetion: Eating spicy food can boost metabolism": ['Y', 'T', 1],
    "Qusetion: Turkey makes you sleepy because it contains high levels of tryptophan": ['F', 'N', 0],
    "Qusetion: Coconut water is sterile and can be used as an emergency IV hydration fluid": ['Y', 'T', 1],
    "Qusetion: Eating cheese before bed gives you nightmares": ['F', 'N', 0]
}

# Mutex for thread synchronization
mutex = threading.Lock()

# List to keep track of connected clients
connected_clients = []

# List to use connected clients socket
connected_clients_sockets = []

# Dictionary to take data from socket while playing, and get the name of the client with the socket
playerName_with_his_socket = {}

# locking the part of winning the game to prevent sync problems
lock = threading.Lock()

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
        self.game_lock = threading.Lock()
        self.GAME_OVER_Lock = threading.Lock()

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
        while not self.Game_Started:
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
        print("Game over, sending out offer requests...")
        sendallclients("Game over, sending out offer requests...", connected_clients_sockets)
        self.tcp_socket.close()
        self.udp_thread.join()
        self.udp_thread = threading.Thread(target=self.send_offer_message)
        self.udp_thread.daemon = True
        self.udp_thread.start()

    def send_offer_message(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.bind((f"{self.MY_IP}", self.UDP_PORT))
        tcp_to_bits = self.TCP_PORT
        servernameencode = self.SERVER_NAME
        offer_message = self.MAGIC_COOKIE + b'\x02' + servernameencode.encode('utf-8').ljust(32) + tcp_to_bits.to_bytes(2,                                                                                                        'big')
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
        welcome = "\n==\nWelcome to the -Sapir And Liron Magic Foodie Server #1-, where we are answering trivia questions about food.\n"
        print(welcome)
        sendallclients(welcome, connected_clients_sockets)

        for idx, player in enumerate(connected_clients, start=1):
            print(f"Player {idx}: {player}\n")
            sendallclients(f"Player {idx}: {player}\n", connected_clients_sockets)

        while not self.GAME_OVER:
            question = random.choice(list(TRIVIA_QUESTIONS.keys()))
            print("\n==")
            print(question)
            sendallclients("\n==\n", connected_clients_sockets)
            sendallclients(question+"\n", connected_clients_sockets)

            self.temp_socket_list = connected_clients_sockets
            timer = threading.Timer(10,self.time_out_handler_in_game)
            timer.start()
            threads = []

            for s in connected_clients_sockets:
                client_thread = threading.Thread(target=self.handle_client, args=(s, TRIVIA_QUESTIONS[question],))
                threads.append(client_thread)
                client_thread.start()

            # for t in threads:
            #     t.join()
            time.sleep(10)

            timer.cancel()



    def time_out_handler(self):
        global connected_clients_sockets
        if(len(connected_clients) == 1):
            message = "Can't start game with only one player. Keep waiting for another player"
            print(message)
            sendallclients(message, connected_clients_sockets)
        #connected_clients_sockets[0].sendall("Can't start game with only one player. Keep waiting for another player".encode())
        # if there are more than one client the game starts and we want to prevent the game will start over and over so we used a lock
        elif (len(connected_clients) > 1):
            with self.game_lock:
                if not self.Game_Started:
                    self.Game_Started = True
                    self.run_game()

    def time_out_handler_in_game(self):
        self.Game_Started = True

    def handle_client(self, client_socket, correct_answer):
        global connected_clients_sockets
        start_time = time.time()
        player = playerName_with_his_socket[client_socket]
        answer = self.receive_answer(client_socket,start_time)
        self.check_winner_dictionary[player] = [answer,time.time() - start_time]
        if answer in correct_answer and client_socket in self.temp_socket_list:
            lock.acquire()
            try:
                with self.GAME_OVER_Lock:
                    self.GAME_OVER = True
                self.Game_Started = False
                ###send all clients !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                print(f"{player} is correct! {player} wins!")
                sendallclients(f"{player} is correct! {player} wins!".encode(), connected_clients_sockets)
                print("Game over!")
                sendallclients("Game over!".encode(), connected_clients_sockets)
                print(f"Congratulations to the winner: {player}")
                sendallclients(f"Congratulations to the winner: {player}".encode(), connected_clients_sockets)
            finally:
                lock.release()
            ###can add game statistics
        if answer not in correct_answer:
            self.temp_socket_list.remove(client_socket)


    def receive_answer(self, client_socket, start_time):
        answer=None
        while (time.time()-start_time<10):
            # Receive answer from client
            answer = client_socket.recv(1024).decode().strip()
            if answer:
                return answer
        if not answer:
            return None




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

def sendallclients(data, clients_socket):
    for client_socket in clients_socket:
        client_socket.sendall(data.encode())

if __name__ == "__main__":
    server = FoodTriviaServer()
    server.start()
