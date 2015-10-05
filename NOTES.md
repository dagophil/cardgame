## General rules:
- 52 regular cards + 4 wizards + 4 jesters.

## Server:
- Wait for n clients.
    - networking: Send status information (player joined / player left) to all players.
- Choose integer k (= number of rounds) with k*n <= 60 and k as big as possible.
- Assign the dealer button to a random player.
- In round i:
    - networking: Send "player x is the dealer" to all players.
    - Shuffle the deck.
    - Give i cards to each player.
        - networking: Send the cards to the according players.
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
    - Get the cards.
        - networking: Wait for the cards.
    - Wait until it is your turn, then say how many tricks you make.
        - networking: Wait for the answers of the other players.
        - networking: Wait for "waiting for your move" message, then send the answer.
    - Play the i tricks:
        - Wait until it is your turn, then play the card.
            - networking: Wait for the cards of the other players.
            - networking: Wait for "waiting for your move" message, then send the answer.
