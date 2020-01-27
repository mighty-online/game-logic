"""The game engine module of Mighty, built for the Mighty-Online project.

This module contains all the underlying classes needed for playing a game of mighty.
"""

from cards import *
import constructs as cs
from typing import List, Optional, Tuple


class CallType:
    _callnames = ['bid', 'exchange', 'trump change', 'miss-deal check', 'friend call',
                  'redeal', 'play', 'game over']

    def __init__(self, typestr: str):
        assert typestr in CallType._callnames
        self.typestr = typestr

    def __repr__(self):
        return 'CallType: ' + self.typestr

    def __eq__(self, other):
        return self.typestr == other.typestr


class GameEngine:
    """The class to wrap all the data manipulation and processes for a game.

    Public attributes are meant to be read but NOT WRITTEN TO."""
    bids: List[Tuple[Optional[Suit], Optional[int]]]

    def __init__(self):
        self.hands, self.kitty = cs.deal_deck()
        self.point_cards = [[] for _ in range(5)]

        # Play related variables
        self.completed_tricks = []
        self.trick_winners = []
        self.current_trick = []
        self.previous_suit_leds = []  # necessary to prevent the suit led information of the Joker from being lost
        self.suit_led = None

        # Setup: declarer, trump, bid, friend, friend_card
        self.declarer = None
        self.trump = None
        self.bid = None
        self.friend = None  # Only set when friend is revealed
        self.friend_card = None

        # Mighty and Ripper cards
        self.mighty = None
        self.ripper = None

        # Hand confirmation of players. (i.e. no miss-deal)
        self.hand_confirmed = [False for _ in range(5)]

        # Bidding related variables.
        self.next_bidder = 0
        self.minimum_bid = 13
        self.highest_bid = None
        self.trump_candidate = None
        self.bids = [(None, None) for _ in range(5)]

        # Stores what call type should come next
        self.next_call = CallType('bid')

        # The leader of the next trick
        self.leader = None

        # Game winners and losers, scoring
        self.declarer_won = None
        self.declarer_team_points = None
        self.gamepoints_rewarded = [0] * 5

    def _perspective_data(self, player: int) -> list:
        """Packages the perspective data of the given player."""
        return [player, self.hands[player][:], self.completed_tricks,
                self.current_trick, self.previous_suit_leds[:], self.suit_led, self.setup()]

    def _set_winners(self, gamepoint_transfer_function=None) -> None:
        """Sets the gamepoints to be rewarded to each player after game ends."""
        if gamepoint_transfer_function is None:
            gamepoint_transfer_function = cs.default_gamepoint_transfer_unit

        self.declarer_team_points = len(self.point_cards[self.declarer])

        if self.friend is not None and self.friend != self.declarer:
            self.declarer_team_points += len(self.point_cards[self.friend])

        self.declarer_won = self.declarer_team_points >= self.bid

        rewards = cs.gamepoint_rewards(self.declarer_team_points, self.declarer, self.friend, self.bid, self.trump,
                                       self.friend_card, self.minimum_bid, gamepoint_transfer_function)

        self.gamepoints_rewarded = rewards

    def __repr__(self):
        return "<GameEngine object at {}>".format(self.next_call)

    def setup(self):
        return cs.Setup(self.declarer, self.trump, self.bid, self.friend, self.friend_card)

    def perspective(self, player: int) -> cs.Perspective:
        """Returns the perspective of the given player."""
        return cs.Perspective(*self._perspective_data(player))

    def trick_complete(self):
        return self.completed_tricks and not self.current_trick

    def bidding(self, bidder: int, trump: Suit, bid: int) -> int:
        """Processes the bidding phase, one bid per call.

        Returns 0 on valid call.

        Returns 1 on unexpected call.
        Returns 2 on invalid bidder.
        Returns 3 on invalid bid.

        Bids are saved in self.bids in player order, in the form of (trump, bid).
        A pass is indicated by a bid of 0.
        """
        if self.next_call != CallType('bid'):
            return 1

        # If unexpected bidder is given
        if self.next_bidder != bidder:
            return 2

        if bid == 0:
            self.bids[bidder] = (None, 0)
        else:
            if self.trump_candidate is not None:
                is_valid = cs.is_valid_bid(trump, bid, self.minimum_bid,
                                           prev_trump=self.trump_candidate, highest_bid=self.highest_bid)
            else:
                is_valid = cs.is_valid_bid(trump, bid, self.minimum_bid)

            if not is_valid:
                return 3

            self.bids[bidder] = (trump, bid)
            self.highest_bid = bid
            self.trump_candidate = trump

            # If a no-trump bid of 20 has been made, everyone else has to pass automatically.
            if bid == 20 and trump.is_nosuit():
                for player in range(5):
                    if player != bidder:
                        self.bids[player] = (None, 0)

        if all([b[1] is not None for b in self.bids]):  # i.e. if everyone has passed or made a bid.
            no_pass_player_count = 0
            declarer_candidate = None
            for player in range(len(self.bids)):
                if self.bids[player][1] > 0:
                    declarer_candidate = player
                    no_pass_player_count += 1

            if no_pass_player_count == 0:  # i.e. everyone has passed.
                if self.minimum_bid == 13:
                    self.minimum_bid -= 1
                    self.bids = [(None, None) for _ in range(5)]
                else:  # If everyone passes even with 12 as the lower bound, there should be a redeal.
                    self.next_call = CallType('redeal')
                    return 0

            if no_pass_player_count == 1:  # Bidding has ended.
                assert isinstance(declarer_candidate, int)
                self.declarer = declarer_candidate  # Declarer is set.

                # The trump suit and bid are set (still open to change after exchange process)
                self.trump, self.bid = self.bids[declarer_candidate]
                self.mighty = cs.trump_to_mighty(self.trump)
                self.ripper = cs.trump_to_ripper(self.trump)

                self.next_call = CallType('exchange')
                return 0

        # The loop below finds the next bidder, ignoring players who passed.
        while True:
            self.next_bidder = cs.next_player(self.next_bidder)
            if self.bids[self.next_bidder][1] != 0:
                break

        return 0

    def exchange(self, discarding_cards: list) -> int:
        """Given the three cards that the declarer will discard, deals with the exchange process.

        Returns 0 on valid call.

        Returns 1 on unexpected call.
        Returns 2 on invalid discarding_cards list
        """
        if self.next_call != CallType('exchange'):
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

        # Discards the three cards back into the kitty
        self.kitty = discarding_cards
        # Appends the point cards of the discarding cards to the point card list
        for card in discarding_cards:
            declarer_hand.remove(card)
            if card.is_pointcard():
                self.point_cards[self.declarer].append(card)

        self.next_call = CallType('trump change')
        return 0

    def trump_change(self, trump: Suit) -> int:
        """Given the trump to change to (or to retain), proceeds with the change.

        Returns 0 on valid call.

        Returns 1 on unexpected call.
        Returns 2 if bid can't be raised.
        """
        if self.next_call != CallType('trump change'):
            return 1

        trump_has_changed = trump != self.trump

        if trump_has_changed:
            if trump.is_nosuit():
                bid_increase = 1
            else:
                bid_increase = 2

            if self.bid + bid_increase > 20:
                return 2
            else:
                self.bid += bid_increase

        # Here the trump is finalized.
        self.trump = trump
        self.mighty = cs.trump_to_mighty(self.trump)
        self.ripper = cs.trump_to_ripper(self.trump)

        self.next_call = CallType('miss-deal check')
        return 0

    def miss_deal_check(self, player: int, miss_deal: bool) -> int:
        """Given player and whether that player announces a miss-deal, proceeds with the necessary steps.

        Returns 0 on valid call.

        Returns 1 on unexpected call.
        Returns 2 on invalid player.
        Returns 3 on invalid miss-deal call.
        """
        if self.next_call != CallType('miss-deal check'):
            return 1

        if not 0 <= player < 5:
            return 2

        if miss_deal:
            if not cs.is_miss_deal(self.hands[player], self.mighty):  # fake miss-deal call
                return 3
            else:
                self.next_call = CallType('redeal')
        else:
            self.hand_confirmed[player] = True
            if all(self.hand_confirmed):
                self.next_call = CallType('friend call')

        return 0

    def friend_call(self, friend_card: Optional[Card]) -> int:
        """Given the friend card, sets up the friend.
        Passing in None indicates no friend.

        Returns 0 on valid call.

        Returns 1 on unexpected call.
        """
        if self.next_call != CallType('friend call'):
            return 1

        self.friend_card = friend_card

        self.next_call = CallType('play')
        self.leader = self.declarer
        return 0

    def play(self, play: cs.Play) -> int:
        """Given the player and the card played by the player, processes the trick.

        Returns 0 on valid call.

        Returns 1 on unexpected call.
        Returns 2 on invalid player.
        Returns 3 on invalid card.
        Returns 4 on invalid play.
        Returns 5 on invalid Joker Call.
        Returns 6 when suit_led is expected but not set.
        Returns 7 on unexpected suit_led value.
        """
        if self.next_call != CallType('play'):
            return 1

        is_leader = len(self.current_trick) == 0

        if is_leader:
            if play.player != self.leader:
                return 2
        else:
            if play.player != cs.next_player(self.current_trick[-1].player):
                return 2

        if play.card not in self.hands[play.player]:
            return 3

        if play.is_joker_call():
            if not (is_leader and play.card == self.ripper):
                return 5

        if is_leader:
            if not isinstance(play.suit_led, Suit):
                return 6

            self.suit_led = play.suit_led
        else:
            if play.suit_led is not None:
                return 7

        if not cs.is_valid_move(len(self.completed_tricks), self.current_trick, self.suit_led, self.trump,
                                self.hands[play.player], play):
            return 4

        if play.card == self.friend_card:
            friend_reveal = True
        else:
            friend_reveal = False

        self.current_trick.append(play)
        self.hands[play.player].remove(play.card)

        # The friend is set when the friend card has been played.
        if friend_reveal:
            self.friend = play.player

        # The trick is over
        if len(self.current_trick) == 5:
            trick_winner = cs.trick_winner(len(self.completed_tricks), self.current_trick, self.trump)

            point_cards = [play.card for play in self.current_trick if play.card.is_pointcard()]

            self.point_cards[trick_winner] += point_cards

            self.completed_tricks.append(self.current_trick)
            self.current_trick = []

            self.previous_suit_leds.append(self.suit_led)
            self.suit_led = None

            self.trick_winners.append(trick_winner)
            self.leader = trick_winner

            # when game is over
            if len(self.completed_tricks) == 10:
                self._set_winners()
                self.next_call = CallType('game over')

        return 0
