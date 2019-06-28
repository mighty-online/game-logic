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

uninit = {'player': -1, 'suit': '', 'bid': -1, 'card': ''}  # Default uninitialized values.


class GameEngine:
    """The class to wrap all the data manipulation and processes for a game."""

    # The block below sets the types of valid calls to the GameEngine, and assigns them to a dictionary.
    # This way, invalid call types cannot be set without invoking an KeyError.
    _calls = ['bid', 'deal-miss check', 'exchange', 'trump change', 'friend call',
              'redeal', 'play', 'game over']
    calltype = {}
    for call in _calls:
        calltype[call] = call

    del _calls

    def __init__(self):
        self.hands, self.kitty = deal_deck()
        self.point_cards = [[] for _ in range(5)]

        self.mighty = uninit['card']
        self.ripper = uninit['card']

        # Play related variables
        self.tricks = []
        self.current_trick = []
        self.suit_led = uninit['suit']

        # Declarer, trump, bid, [friend, friend card]
        self.declarer = uninit['player']
        self.trump = uninit['suit']
        self.bid = uninit['bid']
        self.friend = uninit['player']
        self.friend_card = uninit['card']

        # Hand confirmation of players. (i.e. no deal-miss)
        self.hand_confirmed = [False for _ in range(5)]

        # Bidding related variables.
        self.next_bidder = uninit['player']
        self.lower_bound = 13
        self.highest_bid = uninit['bid']
        self.bids = [(uninit['suit'], uninit['bid']) for _ in range(5)]

        # Stores what call type should come next
        self.next_call = GameEngine.calltype['bid']

        # The leader of the next trick
        self.leader = uninit['player']

    def setup(self) -> list:
        """Returns the setup information of the game."""
        return [self.declarer, self.trump, self.bid, self.friend_card, self.friend]

    def proceed(self, call: str) -> int:
        """Automatically runs the appropriate method to proceed the game."""
        raise NotImplementedError

    def bidding(self, bidder: int, trump: str, bid: int) -> int:
        """Processes the bidding phase, one bid per call.

        Returns 0 on valid call.

        Returns 1 on unexpected call.
        Returns 2 on invalid bidder.
        Returns 3 on invalid trump.
        Returns 4 on invalid bid.

        Bids are saved in self.bids in player order. Each bid is a tuple of (trump, bid).
        A pass is marked by a 0.
        """

        if self.next_call != GameEngine.calltype['bid']:
            return 1

        if self.next_bidder != uninit['player']:  # Checks if the bidder is valid (i.e. is the expected one)
            if self.next_bidder != bidder:
                return 2
        else:  # If it is the first bid made, sets the next bidder as the bidder given in argument
            if bidder in range(5):
                self.next_bidder = bidder
            else:
                return 2

        if bid == 0:
            self.bids[bidder] = (uninit['suit'], 0)
        else:
            if trump == 'N':
                no_trump = 1
            else:
                if trump not in suits:
                    return 3
                no_trump = 0

            if self.highest_bid:  # i.e. if there exists a previous bid.
                if self.highest_bid >= bid + no_trump:
                    return 4
            if bid < self.lower_bound:
                return 4

            self.bids[bidder] = (trump, bid)
            self.highest_bid = bid

        if all([b[1] != uninit['bid'] for b in self.bids]):  # i.e. if everyone has passed or made a bid.
            no_pass_player_count = 0
            declarer_candidate = None
            for player in range(len(self.bids)):
                if self.bids[player][1] > 0:
                    declarer_candidate = player
                    no_pass_player_count += 1

            if no_pass_player_count == 0:  # i.e. everyone has passed.
                if self.lower_bound == 13:
                    self.lower_bound -= 1
                    self.bids = [(uninit['suit'], uninit['bid']) for _ in range(5)]
                else:  # If everyone passes even with 12 as the lower bound, there should be a redeal.
                    self.next_call = GameEngine.calltype['redeal']
                    return 0

            if no_pass_player_count == 1:  # Bidding has ended.
                self.declarer = declarer_candidate  # Declarer is set.
                self.trump, self.bid = self.bids[declarer_candidate]  # The trump suit and bid are set
                self.next_call = GameEngine.calltype['exchange']
                return 0

        # The loop below finds the next bidder, ignoring players who passed.
        while True:
            self.next_bidder = next_player(self.next_bidder)
            if self.bids[self.next_bidder][1] != 0:
                break

        return 0

    def exchange(self, discarding_cards: list) -> int:
        """Given the three cards that the declarer will discard, deals with the exchange process.

        Returns 0 on valid call.

        Returns 1 on unexpected call.
        Returns 2 on invalid discarding_cards list
        """
        if self.next_call != GameEngine.calltype['exchange']:
            return 1

        if len(discarding_cards) != 3:
            return 2

        declarer_hand = self.hands[self.declarer]

        if not all([c in declarer_hand for c in discarding_cards]):
            return 2

        # Moves the contents of the kitty into the declarer's hand.
        declarer_hand += self.kitty
        self.kitty = []

        # Discards the three cards into the declarer's point card list. (if point card)
        for card in discarding_cards:
            declarer_hand.remove(card)
            if is_pointcard(card):
                self.point_cards[self.declarer].append(card)

        self.next_call = GameEngine.calltype['trump change']
        return 0

    def trump_change(self, trump: str) -> int:
        """Given the trump to change to (or to retain), proceeds with the change.

        Returns 0 on valid call.

        Returns 1 on unexpected call.
        Returns 2 on invalid trump.
        Returns 3 if bid can't be raised.
        """
        if self.next_call != GameEngine.calltype['trump change']:
            return 1

        if trump not in suits + ['N']:
            return 2

        trump_has_changed = trump != self.trump

        if trump_has_changed:
            if trump == 'N':
                bid_increase = 1
            else:
                bid_increase = 2

            if self.bid + bid_increase > 20:
                return 3
            else:
                self.bid += bid_increase

            # Here the trump is finalized.
            self.trump = trump
            self.mighty = trump_to_mighty(self.trump)
            self.ripper = trump_to_ripper(self.trump)

        self.next_call = GameEngine.calltype['deal-miss check']
        return 0

    def deal_miss_check(self, player: int, deal_miss: bool) -> int:
        """Given player and whether that player announces a deal-miss, proceeds with the necessary steps.

        Returns 0 on valid call.

        Returns 1 on unexpected call.
        Returns 2 on invalid player.
        Returns 3 on invalid deal-miss call.
        """
        if self.next_call != GameEngine.calltype['deal-miss check']:
            return 1

        if player not in range(5):
            return 2

        if deal_miss:
            if not is_deal_miss(self.hands[player], self.mighty):  # fake deal-miss call
                return 3
            else:
                self.next_call = GameEngine.calltype['redeal']
        else:
            self.hand_confirmed[player] = True
            if all(self.hand_confirmed):
                self.next_call = GameEngine.calltype['friend call']

        return 0

    def friend_call(self, friend_card: str) -> int:
        """Given the friend card, sets up the friend.
        'NF' indicates no friend.

        Returns 0 on valid call.

        Returns 1 on unexpected call.
        Returns 2 on invalid friend_card.
        """
        if self.next_call != GameEngine.calltype['friend call']:
            return 1
        if friend_card not in cards + ['NF']:
            return 2

        self.friend_card = friend_card

        self.next_call = GameEngine.calltype['play']
        self.leader = self.declarer
        return 0

    def play(self, player: int, card: str, suit_led=uninit['suit'], activate_joker_call=False) -> int:
        """Given the player and the card played by the player, processes the trick.

        Returns 0 on valid call.

        Returns 1 on unexpected call.
        Returns 2 on invalid player.
        Returns 3 on invalid card.
        Returns 4 on invalid play.
        Returns 5 on invalid suit_led when joker is played as leader.
        """
        if self.next_call != GameEngine.calltype['play']:
            return 1

        is_leader = len(self.current_trick) == 0

        if is_leader:
            if player != self.leader:
                return 2
        else:
            if player != next_player(self.current_trick[-1][0]):
                return 2

        if card not in self.hands[player]:
            return 3

        if is_leader:
            if card == joker:
                if suit_led not in suits:
                    return 5
            else:
                suit_led = card[0]
                if card == self.ripper:
                    if activate_joker_call:
                        card = joker_call

            self.suit_led = suit_led

        if not is_valid_move(self.current_trick, self.suit_led, self.mighty, self.hands[player], card):
            return 4

        self.current_trick.append((player, card))
        self.hands[player].remove(card)

        if len(self.current_trick) == 5:
            winner = trick_winner(len(self.tricks), self.current_trick, self.trump)

            point_cards = [c for c in [play[1] for play in self.current_trick] if is_pointcard(c)]

            self.point_cards[winner] += point_cards

            self.tricks.append(self.current_trick)
            self.current_trick = []

            self.suit_led = uninit['suit']

            self.leader = winner

            if len(self.tricks) == 10:
                # TODO: Determine game winners and proceed with the scoring
                self.next_call = GameEngine.calltype['game over']

        return 0


# Player number is a value in range(5)
def next_player(prev_player: int) -> int:
    """Returns the number of the next player, given the previous player's number."""
    return (prev_player + 1) % 5


def trick_winner(trick_number: int, trick: list, trump: str) -> int:
    """Returns the winner of the trick, given the trick and the trump suit."""
    try:
        assert len(trick[0]) == 2
        assert type(trick[0][0]) == int
        assert type(trick[0][1]) == str
    except (AssertionError, TypeError):
        raise AssertionError('Tricks should be in the format of [(player_num, played_card),...]')

    # Setting the Mighty card.
    mighty = trump_to_mighty(trump)

    # Searching for Mighty.
    for player, card in trick:
        if card == mighty:
            return player

    # Searching for Joker.
    if not trick[0][1] == joker_call:  # if Joker Call is not led
        if trick_number not in (0, 9):  # if it isn't the first or last trick
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
    """Returns whether the given card is a point card."""
    if card == joker:
        return False
    else:  # If not a Joker, all cards ending with an alphabet are point cards.  (Because 10 is also X)
        return card[1].isalpha()


def unicode_card(card: str) -> str:
    """Converts standard card representation to unicode representation."""
    unicode_cards = '🂡🂢🂣🂤🂥🂦🂧🂨🂩🂪🂫🂭🂮🃁🃂🃃🃄🃅🃆🃇🃈🃉🃊🃋🃍🃎🂱🂲🂳🂴🂵🂶🂷🂸🂹🂺🂻🂽🂾🃑🃒🃓🃔🃕🃖🃗🃘🃙🃚🃛🃝🃞🃏'
    return unicode_cards[cards.index(card)]


def print_card(card: str) -> None:
    """Prints out the unicode representation of the given card to console."""
    print(unicode_card(card))


def deal_deck() -> tuple:
    """Randomly shuffles and deals the deck to 5 players and the kitty."""
    hands = []
    deck = cards[:]
    random.shuffle(deck)

    # creates the hand of each player
    for p in range(5):
        hands.append(deck[10 * p: 10 * p + 10])

    # creates the kitty
    kitty = deck[50:]

    return hands, kitty  # will contain 5 hands plus the kitty


def trump_to_mighty(trump: str) -> str:
    if trump == 'S':
        mighty = 'DA'
    else:
        mighty = 'SA'

    return mighty


def trump_to_ripper(trump: str) -> str:
    if trump == 'C':
        ripper = 'S3'
    else:
        ripper = 'C3'

    return ripper


def is_deal_miss(hand: list, mighty: str) -> bool:
    point_card_count = 0
    for card in hand:
        if is_pointcard(card) and card != mighty:
            point_card_count += 1

    if point_card_count <= 1:
        return True
    else:
        return False


def is_valid_move(trick: list, suit_led: str, mighty: str, hand: list, card: str) -> bool:
    if len(trick) == 0:
        return True
    else:
        if trick[0][1] == joker_call and joker in hand:
            if card == joker:
                return True
            else:
                return False
        else:
            if card in (mighty, joker):
                return True
            else:
                if any([c[0] == suit_led for c in hand]):  # i.e. if a card of the suit led is in the hand
                    if card[0] == suit_led:
                        return True
                    else:
                        return False
                else:
                    return True
