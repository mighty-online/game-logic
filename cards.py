"""Contains classes for a standard deck of playing cards, plus one joker."""


class Suit:
    """The Suit class, for suits.

    Includes the no-trump suit.
    """
    _suits_short = ['N', 'C', 'D', 'H', 'S']
    _suits_long = ['no-suit', 'Clubs', 'Diamonds', 'Hearts', 'Spades']

    def __init__(self, val: int):
        """0 for no-trump; 1, 2, 3, 4 for C, D, H, S."""
        assert 0 <= val < len(Suit._suits_short)
        self.val = val

    def short(self):
        return Suit._suits_short[self.val]

    def long(self):
        return Suit._suits_long[self.val]

    @staticmethod
    def str_to_val(suit_str: str) -> int:
        assert Suit.is_suitstr(suit_str)
        return Suit._suits_short.index(suit_str)

    @staticmethod
    def is_suitstr(suit_str: str) -> bool:
        return suit_str in Suit._suits_short

    def is_nosuit(self):
        return self.val == 0

    def is_clubs(self):
        return self.val == 1

    def is_diamonds(self):
        return self.val == 2

    def is_hearts(self):
        return self.val == 3

    def is_spades(self):
        return self.val == 4

    def __repr__(self):
        return f'<{self.long()}>'

    def __eq__(self, other):
        return isinstance(other, Suit) and self.val == other.val

    @staticmethod
    def iter(include_nosuit=False):
        start = 0 if include_nosuit else 1
        for val in range(start, len(Suit._suits_short)):
            yield Suit(val)


class Rank:
    """The Rank class, for ranks.

    Includes a no-rank rank for the joker.
    """
    _ranks_short = ['N'] + ['A'] + ['2', '3', '4', '5', '6', '7', '8', '9'] + ['10', 'J', 'Q', 'K']  # 'N' for no-rank

    def __init__(self, val: int):
        """0 for no-rank, 1-13 for Ace to King."""
        assert 0 <= val < len(Rank._ranks_short)
        self.val = val

    @staticmethod
    def str_to_val(rank_str: str) -> int:
        assert Rank.is_rankstr(rank_str)
        return Rank._ranks_short.index(rank_str)

    @staticmethod
    def is_rankstr(rank_str: str) -> bool:
        return rank_str in Rank._ranks_short

    def is_pointcard_rank(self):
        return self.val in [1, 10, 11, 12, 13]

    def is_norank(self):
        return self.val == 0

    def power(self):
        """Returns the relative strengths of the ranks.
        Only for larger-than/smaller-than comparisons. (i.e. individual values have no meaning)"""
        if self.val == 0:
            return -1
        elif self.val == 1:
            return 13
        else:
            return self.val - 1

    def short(self):
        return Rank._ranks_short[self.val]

    def __repr__(self):
        return f'{{{self.short()}}}'

    def __eq__(self, other):
        return isinstance(other, Rank) and self.val == other.val

    @staticmethod
    def iter(include_norank=False):
        start = 0 if include_norank else 1
        for val in range(start, len(Rank._ranks_short)):
            yield Rank(val)


class Card:
    """The Card class, for cards."""

    def __init__(self, suit: Suit, rank: Rank):
        if suit.is_nosuit():  # if the suit is a no-suit
            assert rank.is_norank()  # the card must be a joker, hence a no-rank
        else:
            assert not rank.is_norank()  # else the rank cannot be a no-rank

        self.suit = suit
        self.rank = rank

    @staticmethod
    def str_to_vals(card_str: str) -> tuple:
        assert Card.is_cardstr(card_str)

        suit_str = card_str[0]
        rank_str = card_str[1:]

        return Suit.str_to_val(suit_str), Rank.str_to_val(rank_str)

    @classmethod
    def str_to_card(cls, card_str: str):
        suit_val, rank_val = Card.str_to_vals(card_str)
        suit, rank = Suit(suit_val), Rank(rank_val)
        return cls(suit, rank)

    @staticmethod
    def is_cardstr(card_str: str) -> bool:
        if 2 <= len(card_str) <= 3:
            suit_str = card_str[0]
            rank_str = card_str[1:]
            return Suit.is_suitstr(suit_str) and Rank.is_rankstr(rank_str)
        else:
            return False

    def is_pointcard(self):
        return self.rank.is_pointcard_rank()

    def power(self):
        return self.rank.power()

    def is_joker(self):
        return self.suit.is_nosuit()

    def is_clubs(self):
        return self.suit.is_clubs()

    def is_diamonds(self):
        return self.suit.is_diamonds()

    def is_hearts(self):
        return self.suit.is_diamonds()

    def is_spades(self):
        return self.suit.is_spades()

    def unicode(self):
        """Converts standard card representation to unicode representation."""
        if self.suit.val == 0:
            assert self.rank.val == 0
            return '🃏'
        else:
            unicode_cards = ['🃑🃒🃓🃔🃕🃖🃗🃘🃙🃚🃛🃝🃞',
                             '🃁🃂🃃🃄🃅🃆🃇🃈🃉🃊🃋🃍🃎',
                             '🂱🂲🂳🂴🂵🂶🂷🂸🂹🂺🂻🂽🂾',
                             '🂡🂢🂣🂤🂥🂦🂧🂨🂩🂪🂫🂭🂮']
            return unicode_cards[self.suit.val - 1][self.rank.val - 1]

    def __repr__(self):
        if self.suit.val != 0:
            return f'[{self.suit.short()}{self.rank.short()}]'
        else:
            assert self.rank.val == 0
            return '[JK]'

    def __eq__(self, other):
        return isinstance(other, Card) and self.suit == other.suit and self.rank == other.rank

    @staticmethod
    def iter(include_joker=True):
        for suit in Suit.iter():
            for rank in Rank.iter():
                yield Card(suit, rank)
        if include_joker:
            yield Card.joker()

    @staticmethod
    def joker():
        """Returns a joker."""
        return Card(Suit(0), Rank(0))
