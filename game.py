"""The game logic module of Mighty, built for the Mighty-Online project."""

import random

__author__ = "Jake Hyun (SyphonArch)"
__copyright__ = "Copyright 2019, The Mighty-Online Team"
__credits__ = ["Jake Hyun (SyphonArch)"]
__license__ = "MIT"
__version__ = "0.1.0"
__maintainer__ = "Jake Hyun (SyphonArch)"
__email__ = "jake.hyun@hotmail.com"
__status__ = "Development"

suits = ['S', 'D', 'H', 'C']
suits_short_to_long = {'S': 'Spades', 'D': 'Diamonds', 'H': 'Hearts', 'C': 'Clubs'}
pointcard_ranks = ['X', 'J', 'Q', 'K', 'A']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9'] + pointcard_ranks

# Note that 10 is represented by X in order to keep all card name lengths consistent
joker = 'JK'
joker_call = 'JC'  # the Joker Call card should be substituted by JC if it is played as a Joker Call.
cards = ['SA', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'SX', 'SJ', 'SQ', 'SK',
         'DA', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'DX', 'DJ', 'DQ', 'DK',
         'HA', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'HX', 'HJ', 'HQ', 'HK',
         'CA', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'CX', 'CJ', 'CQ', 'CK'] + [joker]


class GameEngine:
    """The class to wrap all the data manipulation and processes for a game"""

    def __init__(self):
        self.hands, self.kitty = deal_deck()
        self.points = [[] for _ in range(5)]

        self.state = [self.hands, self.points]

        self.tricks = []

        # Declarer, trump, bid, [friend, friend card]
        self.setup = [None, None, None, [None, None]]

        self.game = [self.state, self.tricks, self.setup]

        self.next_bidder = None
        self.lower_bound = 13
        self.highest_bid = None
        self.bids = [('', -1) for _ in range(5)]  # This is how bids are initialized

        # Stores what call type should come next
        self.next_call = 'bid'  # 'bid', 'exchange', 'friend call', 'redeal'

    def proceed(self, call):
        """Automatically runs the appropriate method to proceed the game"""
        raise NotImplementedError

    def bidding(self, bidder: int, trump: str, bid: int) -> int:
        """
        Processes the bidding phase, one bid per call

        Returns 0 on a valid bid.

        Returns 1 on invalid call.
        Returns 2 on invalid bidder.
        Returns 3 on invalid trump
        Returns 4 on invalid bid.

        Bids are saved in self.bids in player order. Each bid is a tuple of (trump, bid).
        A pass is marked by a 0.
        """

        if self.setup[0] is not None:
            return 1

        if self.next_bidder is not None:  # Checks if the bidder is valid (i.e. is the expected one)
            if self.next_bidder != bidder:
                return 2
        else:  # If it is the first bid made, sets the next bidder as the bidder given in argument
            if bidder in range(5):
                self.next_bidder = bidder
            else:
                return 2

        if bid == 0:
            self.bids[bidder] = ('', 0)
        else:
            if trump == 'N':
                no_trump = 1
            else:
                if trump not in suits:
                    return 3
                no_trump = 0

            if self.highest_bid:  # If there exists a previous bid,
                if self.highest_bid >= bid + no_trump:
                    return 4
            if bid < self.lower_bound:
                return 4

            self.bids[bidder] = (trump, bid)
            self.highest_bid = bid

        if all([b[1] != -1 for b in self.bids]):  # If everyone has passed or made a bid
            no_pass_player_count = 0
            declarer_candidate = None
            for player in range(len(self.bids)):
                if self.bids[player][1] > 0:
                    declarer_candidate = player
                    no_pass_player_count += 1

            if no_pass_player_count == 0:  # Everyone has passed
                if self.lower_bound == 13:
                    self.lower_bound -= 1
                    self.bids = [('', -1) for _ in range(5)]
                else:  # If everyone passes even with 12 as the lowerbound, there should be a redeal
                    self.next_call = 'redeal'
                    return 0

            if no_pass_player_count == 1:  # Bidding has ended.
                self.setup[0] = declarer_candidate  # declarer is set
                self.setup[1], self.setup[2] = self.bids[declarer_candidate]
                self.next_call = 'exchange'
                return 0

        # The loop below finds the next bidder, ignoring players who passed
        while True:
            self.next_bidder = next_player(self.next_bidder)
            if self.bids[self.next_bidder][1] != 0:
                break

        return 0


# Player number is a value in range(5)
def next_player(prev_player: int) -> int:
    """Returns the number of the next player, given the previous player's number"""
    return (prev_player + 1) % 5


def trick_winner(trick: list, trump: str) -> int:
    """Returns the winner of the trick, given the trick and the trump suit"""
    try:
        assert len(trick[0]) == 2
        assert type(trick[0][0]) == int
        assert type(trick[0][1]) == str
    except (AssertionError, TypeError):
        raise AssertionError('Tricks should be in the format of [(player_num, played_card),...]')

    # Setting the Mighty card
    if trump == 'S':
        mighty = 'DA'
    else:
        mighty = 'SA'

    # Searching for Mighty
    for player, card in trick:
        if card == mighty:
            return player

    # Searching for Joker
    if not trick[0][1] == joker_call:  # if Joker Call is not led
        for player, card in trick:
            if card == joker:
                return player

    suit_led = trick[0][1][0]
    for target_suit in (trump, suit_led):  # Searches for trumps, then plays which match the suit led
        target_plays = [play for play in trick if play[1][0] == target_suit]
        if target_plays:
            target_plays.sort(key=lambda p: ranks.index(p[1][1]), reverse=True)
            return target_plays[0][0]

    raise RuntimeError('No winning card found in trick')


def is_pointcard(card: str) -> bool:
    """Returns whether the given card is a point card"""
    if card == joker:
        return False
    else:  # If not a Joker, all cards ending with an alphabet are point cards. (Because 10 is also X)
        return card[1].isalpha()


def unicode_card(card: str) -> str:
    """Converts standard card representation to unicode representation"""
    unicode_cards = '🂡🂢🂣🂤🂥🂦🂧🂨🂩🂪🂫🂭🂮🃁🃂🃃🃄🃅🃆🃇🃈🃉🃊🃋🃍🃎🂱🂲🂳🂴🂵🂶🂷🂸🂹🂺🂻🂽🂾🃑🃒🃓🃔🃕🃖🃗🃘🃙🃚🃛🃝🃞🃏'
    return unicode_cards[cards.index(card)]


def print_card(card: str) -> None:
    """Prints out the unicode representation of the given card to console"""
    print(unicode_card(card))


def deal_deck() -> tuple:
    """Randomly shuffles and deals the deck to 5 players and the kitty"""
    hands = []
    deck = cards[:]
    random.shuffle(deck)

    # creates the hand of each player
    for p in range(5):
        hands.append(deck[10 * p: 10 * p + 10])

    # creates the kitty
    kitty = deck[50:]

    return hands, kitty  # will contain 5 hands plus the kitty
