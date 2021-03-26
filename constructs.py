"""This module contains all the underlying classes and functions needed for playing a game of mighty.

Classes directly connected to the GameEngine are included in the mighty_engine module instead.
"""

import random
from .cards import *
from typing import Optional, Tuple, List, Union
from copy import deepcopy
from enum import Enum, auto


class CallType(Enum):
    BID = auto()
    EXCHANGE = auto()
    TRUMP_CHANGE = auto()
    MISS_DEAL_CHECK = auto()
    FRIEND_CALL = auto()
    REDEAL = auto()
    PLAY = auto()
    GAME_OVER = auto()


class Play:
    """The class for a regular play made in the 'play' phase of the game."""

    def __init__(self, player: int, card: Card):
        self.player = player
        self.card = card
        self.suit_led = None
        self._is_joker_call = False
        self._is_leading_play = False

    def __repr__(self):
        rep_str = f"[{self.player}:{self.card}"
        if self.suit_led is not None:
            rep_str += f'|{self.suit_led.short()}'
        if self.is_joker_call():
            rep_str += '|JC'
        rep_str += ']'
        return rep_str

    def __str__(self):
        rep_str = f"[ Player {self.player} plays {self.card}"
        if self.suit_led is not None:
            rep_str += f' | {self.suit_led.short()} led'
        if self.is_joker_call():
            rep_str += ' | JC'
        rep_str += ' ]'
        return rep_str

    def is_joker_call(self) -> bool:
        return self._is_joker_call

    def is_leading_play(self) -> bool:
        return self._is_leading_play

    def __eq__(self, other):
        return isinstance(other, Play) and self.player == other.player and self.card == other.card and \
               self.suit_led == other.suit_led and self._is_joker_call == other._is_joker_call and \
               self._is_leading_play == other._is_leading_play

    def __hash__(self):
        return hash((self.player, self.card, self.suit_led, self._is_joker_call, self._is_leading_play))


class LeadingPlay(Play):
    """The class for a leading play."""

    def __init__(self, player: int, card: Card, suit_led: Optional[Suit] = None):
        super().__init__(player, card)
        if card.is_joker():
            assert isinstance(suit_led, Suit)
            self.suit_led = suit_led
        else:
            self.suit_led = self.card.suit

        self._is_leading_play = True


class JokerCall(LeadingPlay):
    """The class for a joker-call play."""

    def __init__(self, player: int, card: Card):
        super().__init__(player, card)
        self._is_joker_call = True


class FriendCall:
    """The class for a friend call.

    A friend call is either a card, or a first-trick-winner call(a.k.a. 초구프렌드).

    For initialization,
    fctype should be 0 for a card-specified friend.
    fctype should be 1 for a first-trick-winner friend.
    """

    def __init__(self, fctype: int, card: Optional[Card] = None):
        self._fctype = None
        self.card = None

        if fctype == 0:
            assert card is not None
            self._fctype = fctype
            self.card = card
        elif fctype == 1:
            self._fctype = fctype
            self.card = None
        elif fctype == 2:
            self._fctype = fctype
            self.card = None
        else:
            raise ValueError

    def is_card_specified(self) -> bool:
        return self._fctype == 0

    def is_ftw_friend(self) -> bool:
        return self._fctype == 1

    def is_no_friend(self) -> bool:
        return self._fctype == 2

    def __repr__(self):
        if self._fctype == 0:
            return f"{self.card} Friend"
        elif self._fctype == 1:
            return "FTW Friend"
        elif self._fctype == 2:
            return "No Friend"
        else:
            raise RuntimeError("Don't mess with my private attributes.")


class Perspective:
    """The Perspective class, containing all information from the perspective of a single player."""

    def __init__(self, player, hand, kitty_or_none, point_cards, completed_tricks, trick_winners, current_trick,
                 previous_suit_leds, declarer, trump, bid, friend, called_friend, friend_just_revealed,
                 mighty, ripper, hand_confirmed, next_bidder, minimum_bid, highest_bid, trump_candidate, bids,
                 next_calltype, leader, declarer_won, declarer_team_points, gamepoints_rewarded, hand_sizes):
        if player == declarer:
            assert kitty_or_none is not None
        self.player = player

        self.hand = hand[:]
        self.kitty = deepcopy(kitty_or_none)  # If not the declarer, the kitty should be None
        self.point_cards = deepcopy(point_cards)

        self.completed_tricks = deepcopy(completed_tricks)
        self.trick_winners = trick_winners[:]
        self.current_trick = deepcopy(current_trick)
        self.previous_suit_leds = deepcopy(previous_suit_leds)

        self.declarer = declarer
        self.trump = deepcopy(trump)
        self.bid = bid
        self.friend = friend
        self.called_friend = deepcopy(called_friend)

        self.friend_just_revealed = friend_just_revealed

        self.mighty = deepcopy(mighty)
        self.ripper = deepcopy(ripper)

        self.hand_confirmed = hand_confirmed[:]

        self.next_bidder = next_bidder
        self.minimum_bid = minimum_bid
        self.highest_bid = highest_bid
        self.trump_candidate = deepcopy(trump_candidate)
        self.bids = deepcopy(bids)

        self.next_calltype = deepcopy(next_calltype)

        self.leader = leader

        self.declarer_won = declarer_won
        self.declarer_team_points = declarer_team_points
        self.gamepoints_rewarded = gamepoints_rewarded[:]

        # This is to assist the AI
        self.hand_sizes = hand_sizes


def default_gamepoint_transfer_unit(declarer_won: bool, multiplier: int, bid: int, declarer_cards_won: int,
                                    minimum_bid) -> int:
    """Returns the unit of gamepoint transfer.

    The declarer wins (or loses) twice the unit.
    The friend and defenders win (or lose) the unit amount of gamepoint."""
    if declarer_won:
        return multiplier * ((declarer_cards_won - bid) + (bid - minimum_bid) * 2)
    else:
        return multiplier * (bid - declarer_cards_won)


def gamepoint_rewards(declarer_team_points: int, declarer: int, friend: Optional[int], bid: int, trump: Suit,
                      friend_call: FriendCall,
                      minimum_bid: int, gamepoint_transfer_unit_function=default_gamepoint_transfer_unit) -> list:
    """Returns the gamepoint rewards to each player."""
    declarer_won = declarer_team_points >= bid

    multiplier = 1
    if friend_call.is_no_friend():
        assert friend is None
        multiplier *= 2

    if trump.is_nosuit():
        multiplier *= 2
    if declarer_won and declarer_team_points == 20:  # run
        multiplier *= 2
    if not declarer_won and declarer_team_points < 10:  # back-run
        multiplier *= 2

    unit = gamepoint_transfer_unit_function(declarer_won, multiplier, bid, declarer_team_points, minimum_bid)

    rewards = [0] * 5
    # First, the gamepoints are rewarded as if the declarer won.
    for player in range(5):
        if player == declarer:
            rewards[player] = unit * 2
        elif player == friend:
            rewards[player] = unit
        else:
            rewards[player] = - unit

    # Then, if the declarer did not win, all rewarded gamepoints are flipped.
    if not declarer_won:
        for i in range(len(rewards)):
            rewards[i] *= -1

    return rewards


# Player number is a value in range(5)
def player_increment(prev_player: int) -> int:
    """Returns the number of the next player, given the previous player's number."""
    return (prev_player + 1) % 5


def next_player(next_calltype: CallType, current_trick: list, leader: int) -> Union[int, None]:
    """Returns the next player, in the PLAY phase.
    If calltype doesn't match the PLAY phase, None is returned.
    """
    if next_calltype != CallType.PLAY:
        return None
    else:
        is_leader = len(current_trick) == 0
        if is_leader:
            return leader
        else:
            return player_increment(current_trick[-1].player)


def trick_winner(trump: Suit, trick_number: int, trick: list) -> int:
    """Returns the winner of the trick, given the trick and the trump suit.

    'trick_number' is 0 based.
    """

    # Setting the Mighty card.
    mighty = trump_to_mighty(trump)

    # Searching for Mighty.
    for play in trick:
        if play.card == mighty:
            return play.player

    # Searching for Joker.
    if not trick[0].is_joker_call():  # if Joker Call is not led
        if trick_number not in (0, 9):  # if it isn't the first or last trick
            for play in trick:
                if play.card.is_joker():
                    return play.player

    suit_led = trick[0].suit_led
    # Searches for [trumps], then [plays which's suits match the suit led]
    for target_suit in (trump, suit_led):
        if not target_suit.is_nosuit():
            target_plays = [play for play in trick if play.card.suit == target_suit]
            if target_plays:
                target_plays.sort(key=lambda p: p.card.power())
                return target_plays[-1].player

    # Joker played in final trick, no suit led cards, no trump cards.
    if trick_number in (0, 9) and trick[0].card.is_joker():
        for target_suit in reversed(list(Suit.iter())):  # Will follow order of Suit value
            target_plays = [play for play in trick if play.card.suit == target_suit]
            if target_plays:
                target_plays.sort(key=lambda p: p.card.power())
                return target_plays[-1].player

    raise RuntimeError(f'No winning card found in trick:\n{trump=}\n{trick_number=}\n{trick=}')


def deal_deck() -> Tuple[List[List[Card]], List[Card]]:
    """Randomly shuffles and deals the deck to 5 players and the kitty."""
    hands = []
    deck = list(Card.iter())
    random.shuffle(deck)

    # creates the hand of each player
    for p in range(5):
        hands.append(deck[10 * p: 10 * p + 10])

    # creates the kitty
    kitty = deck[50:]

    return hands, kitty  # will contain 5 hands plus the kitty


def trump_to_mighty(trump: Suit) -> Card:
    """Given the trump suit, returns the mighty card."""
    if trump.is_spades():
        mighty = Card(Suit(2), Rank(1))  # [DA]
    else:
        mighty = Card(Suit(4), Rank(1))  # [SA]

    return mighty


def trump_to_ripper(trump: Suit) -> Card:
    """Given the trump suit, returns the ripper card."""
    if trump.is_clubs():
        ripper = Card(Suit(4), Rank(3))  # [S3]
    else:
        ripper = Card(Suit(1), Rank(3))  # [C3]

    return ripper


def is_miss_deal(hand: list, mighty: Card) -> bool:
    """Determines whether the given hand qualifies as a miss-deal."""
    point_card_count = 0
    for card in hand:
        if card.is_pointcard() and card != mighty:
            point_card_count += 1

    if point_card_count <= 1:
        return True
    else:
        return False


def is_valid_move(trick_number: int, trick: list, trump: Suit, hand: list, play: Play) -> bool:
    """Given information about the ongoing trick, returns whether a card is valid to be played."""
    if play.card not in hand:
        return False
    if len(trick) == 0:
        if trick_number == 0:
            # For the first card of the game, a non-trump card must be played - if available.
            if any([card.suit != trump for card in hand]) and play.card.suit == trump:
                return False
            # Cannot activate Joker Call during the first trick.
            elif play.is_joker_call():
                return False
            else:
                return True
        else:
            return True
    else:
        if play.card == trump_to_mighty(trump):
            return True
        else:
            if trick[0].is_joker_call() and any([c.is_joker() for c in hand]) and trick_number != 0:
                if play.card.is_joker():
                    return True
                else:
                    return False
            else:
                if play.card.is_joker():
                    return True
                else:
                    suit_led = trick[0].suit_led
                    if suit_led.is_nosuit():
                        return True
                    else:
                        # i.e. if a card of the suit led is in the hand
                        if any([c.suit == suit_led for c in hand]):
                            if play.card.suit == suit_led:
                                return True
                            else:
                                return False
                        else:
                            return True


def legal_plays(player, hand, completed_tricks, current_trick, trump, next_calltype, leader) -> List[Play]:
    if player != next_player(next_calltype, current_trick, leader):
        raise RuntimeError("It is not the player's turn.")
    plays = []
    ripper = trump_to_ripper(trump)
    play_candidates = []
    for card in hand:
        if len(current_trick) == 0:
            if card.is_joker():
                for specifying_suit_led in Suit.iter(True):
                    play_candidates.append(LeadingPlay(player, card, specifying_suit_led))
            else:
                play_candidates.append(LeadingPlay(player, card))
                if card == ripper:
                    play_candidates.append(JokerCall(player, card))
        else:
            play_candidates.append(Play(player, card))

    for play in play_candidates:
        if is_valid_move(len(completed_tricks), current_trick, trump, hand, play):
            plays.append(play)
    return plays


def is_valid_bid(trump: Suit, bid: int, minimum_bid: int, prev_trump: Optional[Suit] = None,
                 highest_bid: Optional[int] = None) -> bool:
    """Given information about a bid and the previous one made, returns whether the bid is valid."""
    if prev_trump is None:  # i.e. if there is no previous bid
        if trump.is_nosuit():
            lower_bound = minimum_bid - 1
        else:
            lower_bound = minimum_bid
    else:
        if trump.is_nosuit() and not prev_trump.is_nosuit():
            lower_bound = highest_bid
        else:
            lower_bound = highest_bid + 1

    if lower_bound <= bid <= 20:
        return True
    else:
        return False
