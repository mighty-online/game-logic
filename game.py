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
no_trump = 'N'
suits_short_to_long = {'S': 'Spades', 'D': 'Diamonds', 'H': 'Hearts', 'C': 'Clubs', 'N': 'no-trump'}
pointcard_ranks = ['X', 'J', 'Q', 'K', 'A']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9'] + pointcard_ranks

# Note that 10 is represented by X in order to keep all card name lengths consistent
joker = 'JK'
joker_call = 'JC'  # the Joker Call card should be substituted by JC if it is played as a Joker Call.
cards = ['SA', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'SX', 'SJ', 'SQ', 'SK',
         'DA', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'DX', 'DJ', 'DQ', 'DK',
         'HA', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'HX', 'HJ', 'HQ', 'HK',
         'CA', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'CX', 'CJ', 'CQ', 'CK'] + [joker]

uninit = {'player': -1, 'suit': '', 'bid': -1, 'card': '', 'points': -1}  # Default uninitialized values.


class GameEngine:
    """The class to wrap all the data manipulation and processes for a game."""

    # The block below sets the types of valid calls to the GameEngine, and assigns them to a dictionary.
    # This way, invalid call types cannot be set without invoking an KeyError.
    _calls = ['bid', 'exchange', 'trump change', 'miss-deal check', 'friend call',
              'redeal', 'play', 'game over']

    calltype = {}
    # Jaehyeong Here
    call = ''
    for call in _calls:
        calltype[call] = call
    del call
    del _calls

    def __init__(self):
        self.hands, self.kitty = deal_deck()
        self.point_cards = [[] for _ in range(5)]

        self.mighty = uninit['card']
        self.ripper = uninit['card']

        # Play related variables
        self.completed_tricks = []
        self.current_trick = []
        self.suit_led = uninit['suit']
        self.recent_winner = uninit['player']

        # Declarer, trump, bid, [friend, friend card]
        self.declarer = uninit['player']
        self.trump = uninit['suit']
        self.bid = uninit['bid']
        self.friend = uninit['player']
        self.friend_card = uninit['card']

        # Hand confirmation of players. (i.e. no miss-deal)
        self.hand_confirmed = [False for _ in range(5)]

        # Bidding related variables.
        self.next_bidder = 0
        self.minimum_bid = 13
        self.highest_bid = uninit['bid']
        self.trump_candidate = uninit['suit']
        self.bids = [(uninit['suit'], uninit['bid']) for _ in range(5)]

        # Stores what call type should come next
        self.next_call = GameEngine.calltype['bid']

        # The leader of the next trick
        self.leader = uninit['player']

        # Game winners and losers, scoring
        self.declarer_won = None
        self.declarer_team_points = uninit['points']
        self.multiplier = 1
        self.gamepoints_rewarded = [0] * 5

    def setup(self) -> list:
        """Returns the setup information of the game."""
        return [self.declarer, self.trump, self.bid, self.friend_card, self.friend]

    def tricks(self):
        """Returns previous and current tricks together in a list."""
        return self.completed_tricks + [self.current_trick]

    def perspective(self, player):
        """Returns the perspective of the given player."""
        return [player, self.hands[player], self.tricks(), self.suit_led, self.setup()]

    def bidding(self, bidder: int, trump: str, bid: int) -> int:
        """Processes the bidding phase, one bid per call.

        Returns 0 on valid call.

        Returns 1 on unexpected call.
        Returns 2 on invalid bidder.
        Returns 3 on invalid trump.
        Returns 4 on invalid bid.

        Bids are saved in self.bids in player order. Each bid is a tuple of (trump, bid).
        A pass is indicated by a bid of 0.
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
            if trump not in suits + ['N']:
                return 3

            if not is_valid_bid(trump, bid, self.trump_candidate, self.highest_bid, self.minimum_bid):
                return 4

            self.bids[bidder] = (trump, bid)
            self.highest_bid = bid
            self.trump_candidate = trump

            # If a no-trump bid of 20 has been made, everyone else has to pass automatically.
            if bid == 20 and trump == 'N':
                for player in range(5):
                    if player != bidder:
                        self.bids[player] = (uninit['suit'], 0)

        if all([b[1] != uninit['bid'] for b in self.bids]):  # i.e. if everyone has passed or made a bid.
            no_pass_player_count = 0
            declarer_candidate = None
            for player in range(len(self.bids)):
                if self.bids[player][1] > 0:
                    declarer_candidate = player
                    no_pass_player_count += 1

            if no_pass_player_count == 0:  # i.e. everyone has passed.
                if self.minimum_bid == 13:
                    self.minimum_bid -= 1
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

        # Moves the contents of the kitty into the declarer's hand.
        declarer_hand += self.kitty
        self.kitty = []

        # Checks that all discarding cards are in the declarer's hand.
        if not all([c in declarer_hand for c in discarding_cards]):
            return 2

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

        self.next_call = GameEngine.calltype['miss-deal check']
        return 0

    def miss_deal_check(self, player: int, miss_deal: bool) -> int:
        """Given player and whether that player announces a miss-deal, proceeds with the necessary steps.

        Returns 0 on valid call.

        Returns 1 on unexpected call.
        Returns 2 on invalid player.
        Returns 3 on invalid miss-deal call.
        """
        if self.next_call != GameEngine.calltype['miss-deal check']:
            return 1

        if player not in range(5):
            return 2

        if miss_deal:
            if not is_miss_deal(self.hands[player], self.mighty):  # fake miss-deal call
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
            self.recent_winner = uninit['player']
            if player != self.leader:
                return 2
        else:
            if player != next_player(self.current_trick[-1][0]):
                return 2

        if card not in self.hands[player]:
            return 3

        # The check for friend card should be located before the joker call substitution.
        if card == self.friend_card:
            friend_reveal = True
        else:
            friend_reveal = False

        if is_leader:
            if card == joker:
                if suit_led not in suits:
                    return 5
            else:
                suit_led = card[0]
                if card == self.ripper:
                    if activate_joker_call:
                        card = joker_call  # the joker call substitution

            self.suit_led = suit_led

        if not is_valid_move(len(self.completed_tricks), self.current_trick, self.suit_led, self.trump,
                             self.hands[player], card):
            return 4

        self.current_trick.append((player, card))
        self.hands[player].remove(card)

        # The friend is set when the friend card has been played.
        if friend_reveal:
            self.friend = player

        if len(self.current_trick) == 5:
            self.recent_winner = trick_winner(len(self.completed_tricks), self.current_trick, self.trump)

            point_cards = [c for c in [play[1] for play in self.current_trick] if is_pointcard(c)]

            self.point_cards[self.recent_winner] += point_cards

            self.completed_tricks.append(self.current_trick)
            self.current_trick = []

            self.suit_led = uninit['suit']

            self.leader = self.recent_winner

            # when game is over
            if len(self.completed_tricks) == 10:
                self.set_winners()
                self.next_call = GameEngine.calltype['game over']

        return 0

    def set_winners(self, gamepoint_transfer_function=None) -> None:
        """Sets the gamepoints to be rewarded to each player after game ends."""
        if gamepoint_transfer_function is None:
            gamepoint_transfer_function = default_gamepoint_transfer

        self.declarer_team_points = len(self.point_cards[self.declarer])

        if self.friend != -1 and self.friend != self.declarer:
            self.declarer_team_points += len(self.point_cards[self.friend])

        self.declarer_won = self.declarer_team_points >= self.bid

        if self.friend_card == 'NF':
            self.multiplier *= 2
        if self.trump == 'N':
            self.multiplier *= 2
        if self.declarer_won and self.declarer_team_points == 20:  # run
            self.multiplier *= 2
        if not self.declarer_won and self.declarer_team_points < 10:  # back-run
            self.multiplier *= 2

        unit = gamepoint_transfer_function(self.declarer_won, self.multiplier, self.bid, self.declarer_team_points,
                                           self.minimum_bid)

        # First, the gamepoints are rewarded as if the declarer won.
        for player in range(5):
            if player == self.declarer:
                self.gamepoints_rewarded[player] = unit * 2
            elif player == self.friend:
                self.gamepoints_rewarded[player] = unit
            else:
                self.gamepoints_rewarded[player] = - unit

        # Then, if the declarer did not win, all rewarded gamepoints are flipped.
        if not self.declarer_won:
            for i in range(len(self.gamepoints_rewarded)):
                self.gamepoints_rewarded[i] *= -1


def default_gamepoint_transfer(declarer_won: bool, multiplier: int, bid: int, declarer_cards_won: int,
                               lower_bid_bound) -> int:
    """Returns the unit of gamepoint transfer.

    The declarer wins (or loses) twice the unit.
    The friend and defenders win (or lose) the unit amount of gamepoint."""
    if declarer_won:
        return multiplier * (declarer_cards_won - bid) + (bid - lower_bid_bound) * 2
    else:
        return multiplier * (bid - declarer_cards_won)


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
    """Given the trump suit, returns the mighty card."""
    if trump == 'S':
        mighty = 'DA'
    else:
        mighty = 'SA'

    return mighty


def trump_to_ripper(trump: str) -> str:
    """Given the trump suit, returns the ripper card."""
    if trump == 'C':
        ripper = 'S3'
    else:
        ripper = 'C3'

    return ripper


def is_miss_deal(hand: list, mighty: str) -> bool:
    """Determines whether the given hand qualifies as a miss-deal."""
    point_card_count = 0
    for card in hand:
        if is_pointcard(card) and card != mighty:
            point_card_count += 1

    if point_card_count <= 1:
        return True
    else:
        return False


def is_valid_move(trick_number: int, trick: list, suit_led: str, trump: str, hand: list, card: str) -> bool:
    """Given information about the ongoing trick, returns whether a card is valid to be played."""
    if card not in hand:
        return False
    if len(trick) == 0:
        # Cannot play a card of the trump suit as the first card of the game
        if trick_number == 0 and card[0] == trump:
            return False
        else:
            return True
    else:
        if trick[0][1] == joker_call and joker in hand:
            if card == joker:
                return True
            else:
                return False
        else:
            if card in (trump_to_mighty(trump), joker):
                return True
            else:
                if any([c[0] == suit_led for c in hand]):  # i.e. if a card of the suit led is in the hand
                    if card[0] == suit_led:
                        return True
                    else:
                        return False
                else:
                    return True


def is_valid_bid(trump: str, bid: int, prev_trump: str, prev_bid: int, minimum_bid: int) -> bool:
    """Given information about a bid and the previous one made, returns whether the bid is valid.

    If no previous bid has been made, the argument to prev_trump should be uninit['suit'].
    """
    if prev_trump == uninit['suit']:  # i.e. if there is no previous bid
        if trump == 'N':
            lower_bound = minimum_bid - 1
        else:
            lower_bound = minimum_bid
    else:
        if trump == 'N' and prev_trump != 'N':
            lower_bound = prev_bid
        else:
            lower_bound = prev_bid + 1

    if lower_bound <= bid <= 20:
        return True
    else:
        return False
