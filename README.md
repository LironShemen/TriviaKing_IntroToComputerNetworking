# TriviaKing_IntroToComputerNetworking

The is a client-server application that implements a trivia contest.
Every ten seconds the server send to the players an intersting statement which is either true or false about food.
The winner is the first one to answer correctly.


## Creators:
* **Liron Miriam Shemen** - (https://github.com/LironShemen)
* **Sapir Tzaig** - (https://github.com/SapirTzaig)

## Methods and structure to accomplish our goals
- The server is a multithreaded to handle each client
- The client is a single-threaded and has three states: looking for a server, connecting a server and game mode.
- We used both TCP and UDP protocols:
  - The server send brodcast offers using UDP connection for clients to join the game
  - The clients connect through the UDP connection
  - After connection is maded they connect through a TCP connection ducring the whole game


## Game Files:

- `Server.py`
- `Client.py`

## ChatGPT links:
- https://chat.openai.com/share/b2a8339d-9b2c-4dec-b41e-be0e4d312d6d
- https://chat.openai.com/share/91ab56a2-2396-42ad-8ed9-a716385857b9

## Run APP:
- run command: `py Server.py`, `py Client.py`

-You should run at least 2 clients in order to start the game

## Have Fun!
