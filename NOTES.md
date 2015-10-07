## General rules:
- 52 regular cards + 4 wizards + 4 jesters.
- The game is played with "low 10", meaning the card order is 2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K, A.
- In round k, each player gets k cards.
- In round k, the sum of all said tricks must not be equal to k.
- If more than one player play wizards, the first wizard wins.
- If everyone plays a jester, the last player wins.

## Server:
- Wait for n clients.
    - networking: Send status information (player joined / player left) to all players.
- Play k=floor(60/n) rounds, where n is the number of players.
- Assign the dealer button to a random player.
- In round i:
    - Shuffle the deck.
    - Give i cards to each player.
        - networking: Send the cards to the according players.
    - Find a random trump and tell it the players. The chances are:
        - 4/60 no trump
        - 4/60 the first player says what is trump
        - 13/60 suit is trump (for each suit)
        - networking: Send the trump to the players. Eventually, the first player is asked for the trump.
    - Let each player say how many tricks the make. (Clockwise, starting left from the dealer).
        - networking: Send "waiting for your move" to the player and wait for the answer. Send the answer to all players.
    - Play the i tricks:
        - Wait for each player to play his card.
          (Clockwise, starting at the winner from the last trick or left from the dealer).
            - networking: Send "waiting for your move" to the player and wait for the answer. Send the answer to all players.
        - Find the winner of the trick.
            - networking: Send "player x won" to all players.
    - Compute the results.

## Client:
- Connect to the server and wait until the game starts.
    - networking: Get status information (player joined / player left) from the server.
- In round i:
    - Get the trump.
        - networking: Wait for the trump. Eventually, the first player is asked for the trump.
    - Get the cards.
        - networking: Wait for the cards.
    - Wait until it is your turn, then say how many tricks you make.
        - networking: Wait for the answers of the other players.
        - networking: Wait for "waiting for your move" message, then send the answer.
    - Play the i tricks:
        - Wait until it is your turn, then play the card.
            - networking: Wait for the cards of the other players.
            - networking: Wait for "waiting for your move" message, then send the answer.
