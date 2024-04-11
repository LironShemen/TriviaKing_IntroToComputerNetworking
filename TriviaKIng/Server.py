import socket
import threading
import time
import random

# Trivia questions about food in a dictionary, so we can check if the client
# answered right on runtime
TRIVIA_QUESTIONS = {
    "True Or False: Carrots were originally purple": ['Y', 'T', '1'],
    "True Or False: Bananas are berries.": ['F', 'N', '0'],
    "True Or False: Peanuts are not nuts, they are legumes.": ['Y', 'T', '1'],
    "True Or False: Honey never spoils.": ['Y', 'T', '1'],
    "True Or False: Eating celery burns more calories than it contains.": ['F', 'N', '0'],
    "True Or False: Almonds are a member of the peach family.": ['F', 'N', '0'],
    "True Or False: Avocados are poisonous to birds.": ['Y', 'T', '1'],
    "True Or False: Rice contains more arsenic than other grains.": ['F', 'N', '0'],
    "True Or False: Apples float in water because they are 25% air": ['Y', 'T', '1'],
    "True Or False: Carrots improve night vision": ['F', 'N', '0'],
    "True Or False: Spinach is a good source of iron": ['Y', 'T', '1'],
    "True Or False: Chocolate causes acne": ['F', 'N', '0'],
    "True Or False: Garlic can help lower blood pressure": ['Y', 'T', '1'],
    "True Or False: Milk helps to create mucus": ['F', 'N', '0'],
    "True Or False: Pineapple can tenderize meat because it contains bromelain": ['Y', 'T', '1'],
    "True Or False: Coffee stunts your growth": ['F', 'N', '0'],
    "True Or False: Eating spicy food can boost metabolism": ['Y', 'T', '1'],
    "True Or False: Turkey makes you sleepy because it contains high levels of tryptophan": ['F', 'N', '0'],
    "True Or False: Coconut water is sterile and can be used as an emergency IV hydration fluid": ['Y', 'T', '1'],
    "True Or False: Eating cheese before bed gives you nightmares": ['F', 'N', '0']
}


# Global variables
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
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)# Tcp socket to communicate after connection
        self.udp_thread.daemon = True
        self.check_winner_dictionary = {} # Use for statistics
        self.Game_Started = "No"
        self.clients_threads = []
        self.TCP_PORT = 5556 # Initialize random port
        self.MAGIC_COOKIE = b'\xab\xcd\xdc\xba' # For the udp packet
        self.SERVER_NAME = "SapirAndLironMagicFoodieServer#1"
        self.UDP_PORT = 13117
        self.GAME_OVER = False
        self.MY_IP = 0 # Initialize random ip
        self.game_lock = threading.Lock()
        self.winner = None

    def start(self):
        global TCP_PORT
        self.MY_IP = get_my_ip() #  Find the ip using helper function
        self.udp_thread.start() # Open udp connection using send_offer_message function.
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Open tcp socket
        self.TCP_PORT = find_available_port(self.TCP_PORT)  # Define the port
        self.tcp_socket.bind((self.MY_IP, self.TCP_PORT)) # Bind the ip and port to the tcp socket
        self.tcp_socket.listen() # Prepares the TCP server socket to accept incoming connections from clients
        print("\033[1m"+ "\033[1;31m"+'\033[100m'+"Server started, listening on IP address "+ f'{self.MY_IP}')
        while True: # While the server is alive
            while self.Game_Started=="No": # While the server is sending offers - a game is not started yet
                try:
                    client_socket, address = self.tcp_socket.accept() # Connect new client
                    connected_clients_sockets.append(client_socket)
                    threading.Timer(10, self.time_out_handler).start() # Wait 10 seconds after client connects
                    print("\033[1m"+"\033[1;35m"+f"New connection from {address}")
                    client_thread = threading.Thread(target=self.handle_tcp_client, args=(client_socket,)) # Get player name
                    self.clients_threads.append(client_thread)
                    client_thread.daemon = True
                    client_thread.start() # Get player name - activate handle_tcp_client function
                except TimeoutError:
                        pass
            self.tcp_socket.close() # After game ends close the old tcp socket
            self.udp_thread.join()

    # Using this fucntion the server send the broadcast via UDP
    def send_offer_message(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # Create udp socket
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.bind((f"{self.MY_IP}", self.UDP_PORT)) # Connect the socket to the por and ip of the server
        tcp_to_bits = self.TCP_PORT
        servernameencode = self.SERVER_NAME
        offer_message = self.MAGIC_COOKIE + b'\x02' + servernameencode.encode('utf-8').ljust(32) + tcp_to_bits.to_bytes(2,                                                                                                        'big')
        while self.Game_Started=="No": # To prevent broadcasting while a game is on
            try:
                udp_socket.sendto(offer_message, ('<broadcast>', self.UDP_PORT))
                time.sleep(1) # The server will broadcast once every second
            except Exception as e:
                pass
        udp_socket.close()

    # The thread of the connected client will get here to receive the player's name
    def handle_tcp_client(self, client_socket):
        global connected_clients
        # Receive player name from client
        player_name = client_socket.recv(1024).decode().strip()
        connected_clients.append(player_name)
        playerName_with_his_socket[client_socket] = player_name
        if not player_name in self.check_winner_dictionary: # Use for statistics for every player
            self.check_winner_dictionary[player_name] = 0


    # Once we have 2 or more clients that made a tcp connection, the game will start
    def run_game(self):
        global connected_clients, connected_clients_sockets, playerName_with_his_socket
        QuestionBank = list(TRIVIA_QUESTIONS.keys()) # To prevent from questions to be asked again in the same game
        list_of_socket_answers = []
        start_event = threading.Event() # Create an event to control the start of threads
        start_event.clear()  # Initially, event is not set
        self.winner = None
        self.winner_lock = threading.Lock()  # Lock for synchronizing access to self.winner
        welcome = "\n==\nWelcome to the Sapir And Liron Magic Foodie Server #1, where we are answering trivia questions about food.\n"
        print("\033[1m"+"\033[0;32m"+welcome)
        sendallclients(welcome, connected_clients_sockets) # Send to all of the connected players

        for idx, player in enumerate(connected_clients, start=1): # Prints the names and indexes of the players
            print("\033[1m"+"\033[1;31m"+f"Player {idx}: {player}\n")
            sendallclients(f"Player {idx}: {player}\n", connected_clients_sockets)


        while not self.winner and len(connected_clients_sockets)>0: # The game is running
            question = random.choice(QuestionBank) # Choose random trivia question
            QuestionBank.remove(question)
            print("\n==")
            print("\033[1m"+"\033[1;36m"+question)
            sendallclients("\n==\n", connected_clients_sockets)
            sendallclients(question + "\n", connected_clients_sockets)

            # Function to handle each client's answer from each client's thread
            def handle_client_answer(client_socket, question):
                start_event.wait()
                try:
                    answer = client_socket.recv(1024).decode().strip()
                    # print(answer)######################################################
                    list_of_socket_answers.append((answer,client_socket)) # To check the correctness of the answer
                except Exception as e: # In case a client will disconnect during the game
                    if client_socket in connected_clients_sockets:
                        connected_clients_sockets.remove(client_socket)

            # Create a thread for each connected client to handle their answer
            threads_game_running = []
            for client_socket in connected_clients_sockets:
                client_thread_run_the_game = threading.Thread(target=handle_client_answer, args=(client_socket,question))
                client_thread_run_the_game.daemon = True  # Set thread as daemon
                client_thread_run_the_game.start()
                threads_game_running.append(client_thread_run_the_game)

            # Start all threads once the event is set
            start_event.set()

            # Wait for all threads to finish or for the timeout
            timeout_seconds = 10
            start_time = time.time()
            # Check the answers during 10 seconds while winner wasn't found yet
            while time.time() - start_time < timeout_seconds and self.winner is None:
                for tup in list_of_socket_answers:
                    if tup[0] in TRIVIA_QUESTIONS[question]: # Check if the player's answer is the correct one
                        self.winner = playerName_with_his_socket[tup[1]]
                        break
                    else:
                        list_of_socket_answers.remove(tup) # Disqulified the player if answered wrong
                time.sleep(0.1)  # Reduce CPU usage while waiting for threads

            # If a winner is determined within the timeout period, break the loop to stop the game
            if self.winner:
                break

            for t in threads_game_running:
                if t.is_alive():
                    t.join(timeout=0)

            # Wait for a brief interval before proceeding to the next question
            time.sleep(2)

        if not self.winner==None: # A winner was found
            # Game over: announce the winner
            self.check_winner_dictionary[self.winner]=self.check_winner_dictionary[self.winner]+1
            print(f"{self.winner} is correct! {self.winner} wins!")
            sendallclients(f"{self.winner} is correct! {self.winner} wins!\n", connected_clients_sockets)

            print("\033[1m"+"\033[1;33m"+"Game over!\n")
            sendallclients("Game over!\n", connected_clients_sockets)
            print("\033[1m"+"\033[1;32m"+f"Congratulations to the winner: {self.winner}\n")
            sendallclients(f"Congratulations to the winner: {self.winner}\n", connected_clients_sockets)
            # Print statistics
            print("\033[1m" + "\033[1;31m" + "\t\t\tWinners Table")
            sendallclients("\t\t\tWinners Table\n", connected_clients_sockets)
            print("Player Name               | Player Score")
            sendallclients("Player Name               | Player Score\n", connected_clients_sockets)
            for player, score in self.check_winner_dictionary.items():
                print(f"{player:<25} | {score}")
                sendallclients(f"{player:<25} | {score}\n", connected_clients_sockets)
            print("\033[1m"+"\033[0;32m"+"Game over, sending out offer requests...\n")
            sendallclients("Game over, sending out offer requests...\n", connected_clients_sockets)

            # Close connections and reset game state
            self.GAME_OVER = True
            self.Game_Started = "Finish"

        else:
            self.GAME_OVER = True
            self.Game_Started = "Finish"
            print("\033[1m" + "\033[0;32m" + "Game over, sending out offer requests...\n")


    # We will get this function after 10 seconds if nobody connected after the last client who connected
    def time_out_handler(self):
        global connected_clients_sockets
        if(len(connected_clients) == 1): # If only one client connected
            message = "Can't start game with only one player. Keep waiting for another player"
            print("\033[1m"+"\033[0;33m"+message)
            sendallclients(message, connected_clients_sockets)

        # If there are more than one client the game starts and we want to prevent the game will start over and over so we used a lock
        elif (len(connected_clients) > 1):
            with self.game_lock:
                if self.Game_Started == "No":
                    self.Game_Started = "Yes"
                    self.udp_thread.join()
                    self.run_game()
        # After a game finished
        if self.Game_Started == "Finish":
            connected_clients_sockets.clear()
            connected_clients.clear()
            playerName_with_his_socket.clear()
            self.Game_Started = "No"
            self.udp_thread.join(timeout=0)
            threading.Thread(target=self.send_offer_message).start() # Back to send broadcast via udp

# Two helper functions to deal with a situation when i want to listen to a
# port that is already used by somebody else
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


# Helper function to find random available port
def find_available_port(start_port):
    port = start_port
    while is_port_in_use(start_port):
        port += 1
    return port


# Helper function to find ip in the current network
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

# Helper function to send the connected clients messages and to remove disconnected clients
def sendallclients(data, clients_socket):
    global connected_clients_sockets
    for client_socket in clients_socket:
        try:
            client_socket.sendall(data.encode())
        except Exception as e:
            connected_clients_sockets.remove(client_socket)

if __name__ == "__main__":
    server = FoodTriviaServer()
    server.start()
