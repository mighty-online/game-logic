# game-logic
### The game logic module for Mighty-Online

Detailed explanation of functions and variables are done right in the code using comments and docstrings.

Terminology and the standard data structures for game constructs are specified below.

### Terminology
Ambiguous terminology are defined as below.
 - **Suit & Rank**: _Spades, Diamonds, Hearts_ and _Clubs_ are suits. _Ace, 2, 3, 4, ..., 10, J, Q, K_ are ranks.
 
 - **Play**: A move made by a player.
 
 - **Trick**: One round of the game, consisting of five plays from the five players.
 
 - **Trump**: The suit elevated above all others in a game of Mighty.
 
 - **Declarer**: The one who makes the highest bid.
 
 - **Joker Call**: The card which can force the Joker to be played if led in a trick.
 
 - **Hand**: The cards held by one player.
 
 - **Kitty**: The three cards dealt face down at the start of the game.
 
 - **State**: The current state of the game, consisting of the hands of the players and the point cards obtained by
 each player.
 
 - **Game**: The state plus information about previous plays, as well as the trump suit, bid, and friend card.
 
 - **Perspective**: All information a player in the game can obtain.
 
 
### Standard Data Structures for Game Constructs

When unspecified in code, the below are the expected formats in which game constructs will be implemented.

 - **Player**: An integer of range(5)
 
    Example: `0`, `1`, `4`
    
 - **Card**: A string with length 2.
 
     Example: `'H3'` or `'JK'`. 
     
     _Note that an active Joker Call is denoted as `'JC'`._
     
 - **Bid**: An integer less or equal to 20.
 
    Example: `14`
     
 - **Suit**: A single character (i.e, string with length 1). 
 
    Example: `'S'`, `'H'`
    
    _Note: both the trump suit and suit led are instances of suits, thus also single characters_
    
    _A 'no-trump' is denoted as `'N'`_
    
 - **Play**: A tuple or list of length 2, consisting of the player who made the move, and the card played.
 
    Example: `(2, 'SA')`, `[1, 'H7']`
    
 - **Trick**: A list of length 5, consisting of 5 plays. Plays are in chronological order.
 
    Example: `[(2, 'SA'), ..., (1, 'H7')]`
    
    _Note: An ongoing trick can be of less than length 5, and will still be called a trick_

 - **Hand**: A list of cards.
 
    Example: `['SA', 'S2', 'H4']`
 
 - **Hands**: A list of 'hand's, in player order. Is a 2D nested list. May contain the kitty.
 
    Example: `[hand0, hand1, hand2, hand3, hand4]`, where each element of the list is a hand.
    
 - **State**: A nested list of the list 'hands', and a list of list of point cards obtained by each player.
 
    Example: `[[hand0, ..., hand4], [points0, ..., points4]]`
    
 - **Setup**: A list containing the declarer, trump suit, bid, and [friend, friend card] list.
 
    Example: `[2, 'D', 15, [3, 'SA']]`, `[2, 'D', 15, [None, 'SA']]` 
    
    _Note: Before the friend card is played, the friend should remain as `None`_
    
 - **Game**: A list consisting of state, a list of tricks, and the setup data.
 
    Example: `[state, list_of_tricks, setup]`
 
 - **Perspective**: A list of the player's hand and previous plays, plus setup.
 
    Example: `[player0_hand, list_of_tricks, setup]`
    
 - **GameEngine**: A class to deal with the dealing and bidding process, as well as the gameplay.
 
    This is the wrapper object of a game. It will contain the game list specified above, and will act as an API.
        
