"""A script to play mighty in the console, using the game.py module."""

import random
import game

space = 100
card_mode = 0  # 0 for standard card string, 1 for unicode representations


def card_repr(card: str) -> str:
    if card_mode == 1:
        return game.unicode_card(card)
    elif card_mode == 0:
        return card
    else:
        return card


def random_random_player(perspective: list) -> str:
    """A very random AI player of Mighty."""
    player_num, hand, tricks, suit_led, setup = perspective
    declarer, trump, bid, friend_card, friend = setup

    trick_number = len(tricks) - 1
    trick = tricks[-1]

    valid_moves = [c for c in hand if game.is_valid_move(trick_number, trick, suit_led, trump, hand, c)]

    return random.choice(valid_moves)


def random_random_bidder(hand: list, prev_trump: str, prev_bid: int, minimum_bid: int) -> tuple:
    """A very random AI bidder of Mighty"""
    # Note that you can call one less with a no-trump
    suit_counts = {}
    for suit in game.suits:
        count = 0
        for card in hand:
            if card[0] == suit:
                count += 1
        suit_counts[suit] = count

    maximum_suit_num = max(suit_counts.values())
    trump = game.uninit['suit']
    for suit in suit_counts:
        if suit_counts[suit] == maximum_suit_num:
            trump = suit

    for bid in range(1, 21):
        if game.is_valid_bid(trump, bid, prev_trump, prev_bid, minimum_bid):
            if random.random() > bid / 21:
                if random.random() > 0.9:
                    trump = 'N'
                return trump, bid
            else:
                break

    return game.uninit['suit'], 0


def imma_call_miss_deal(hand: list, trump: str) -> bool:
    """Will always call miss-deal. That is, this function simply returns True."""
    return True


def random_random_exchanger(hand: list, trump: str) -> tuple:
    """Returns three cards to discard and the trump to change to, on a very random basis."""
    random.shuffle(hand)
    return hand[:3], trump


def mighty_joker_trump_friend_caller(hand: list, trump: str) -> str:
    """Calls the friend card, prioritizing the mighty, followed by joker, then a card of the trump suit.

    Doesn't call itself."""
    mighty = game.trump_to_mighty(trump)
    if mighty not in hand:
        return mighty
    elif game.joker not in hand:
        return game.joker
    else:
        rank_priority_order = ['A', 'K', 'Q', 'J', 'X', '9', '8', '7', '6']
        for rank in rank_priority_order:
            card = trump + rank
            if card not in hand:
                return card
        print("Nope. This can't have happened.")
        exit(1)


def random_random_suit_led_specifier(perspective: list) -> str:
    """Randomly specifies the suit led when calling the joker."""
    player_num, hand, tricks, suit_led, setup = perspective
    declarer, trump, bid, friend_card, friend = setup
    return random.choice(game.suits)


def imma_activate_joker_call(perspective: list) -> bool:
    """Always activates joker call, unless that joker is owned by itself."""
    player_num, hand, tricks, suit_led, setup = perspective
    declarer, trump, bid, friend_card, friend = setup

    if game.joker in hand:
        return False
    else:
        return True


def introduce_hands(hands: list, players: list) -> None:
    """Introduce the hands of players, revealing and hiding upon Enter."""
    for player in players:
        input("Press Enter to reveal Player {}'s hand.".format(player))
        print(' '.join([card_repr(c) for c in hands[player]]))
        input("Press Enter to clear screen.")
        print('\n' * space)


################### SETUP ####################

ai_bidder = random_random_bidder
ai_miss_deal_caller = imma_call_miss_deal
ai_exchanger = random_random_exchanger
ai_friend_caller = mighty_joker_trump_friend_caller
ai_player = random_random_player
ai_suit_led_specifier = random_random_suit_led_specifier
ai_joker_call_activator = imma_activate_joker_call

##############################################

while True:
    ai_num = '5'
    ai_num = input("How many AI agents?: ")
    print()
    if ai_num.isdigit() and int(ai_num) in range(6):
        ai_num = int(ai_num)
        break
    print("Invalid input.")

ai_players_seed = [True] * ai_num + [False] * (5 - ai_num)
random.shuffle(ai_players_seed)

ai_players = []
for i in range(len(ai_players_seed)):
    if ai_players_seed[i]:
        ai_players.append(i)

human_players = [p for p in range(5) if p not in ai_players]
if len(human_players) == 1:
    space = 0

ai_nums_str = ', '.join([str(x) for x in ai_players])
print('Player numbers {} are AI agents.'.format(ai_nums_str))
print()

# Initiating the game object.
mighty_game = game.GameEngine()
feedback = -1
final_trump = game.uninit['suit']

introduce_hands(mighty_game.hands, human_players)

# Here starts the game loop.
while True:
    call_type = mighty_game.next_call
    if call_type == game.GameEngine.calltype['bid']:
        print("Player {}'s turn to make a bid.".format(mighty_game.next_bidder))

        if mighty_game.highest_bid == game.uninit['bid']:
            lower_bound = mighty_game.minimum_bid
        else:
            lower_bound = mighty_game.highest_bid + 1

        print("Bid must be greater or equal to {}.".format(lower_bound))

        if mighty_game.next_bidder in ai_players:

            trump, bid = ai_bidder(mighty_game.hands[mighty_game.next_bidder], mighty_game.trump_candidate,
                                   mighty_game.highest_bid, mighty_game.minimum_bid)
        else:
            print("To pass, enter 0 for the bid.")
            while True:
                while True:
                    trump = input("Enter trump: ")
                    bid = input("Enter bid: ")
                    if (trump in game.suits + ['N'] and bid.isdigit()) or bid == '0':
                        bid = int(bid)
                        break
                    print('Invalid bid.')
                if game.is_valid_bid(trump, bid, mighty_game.trump_candidate, mighty_game.highest_bid,
                                     mighty_game.minimum_bid) or bid == 0:
                    break
                print("Invalid bid.")

        if bid != 0:
            print("Player {} bids {} {}.".format(mighty_game.next_bidder, game.suits_short_to_long[trump], bid))
        else:
            print("Player {} passes.".format(mighty_game.next_bidder))

        feedback = mighty_game.bidding(mighty_game.next_bidder, trump, bid)

    elif call_type == game.GameEngine.calltype['exchange']:
        print('Declarer: {}'.format(mighty_game.declarer))
        print("Final bid: {} {}".format(game.suits_short_to_long[mighty_game.trump], mighty_game.bid))
        print("Card exchange in process.")
        if mighty_game.declarer in ai_players:
            to_discard, final_trump = ai_exchanger(mighty_game.hands[mighty_game.declarer] + mighty_game.kitty,
                                                   mighty_game.trump)
        else:
            input('Player {} - Press Enter to reveal the kitty'.format(mighty_game.declarer))
            print(' '.join(mighty_game.kitty))
            while True:
                to_discard = input("Enter the three cards to discard, space seperated: ")
                to_discard = to_discard.split()
                if to_discard and all(
                        [x in mighty_game.hands[mighty_game.declarer] + mighty_game.kitty for x in to_discard]):
                    break
                print("Invalid input.")

            print('\n' * space)

        print('Exchange over.')
        feedback = mighty_game.exchange(to_discard)

    elif call_type == game.GameEngine.calltype['trump change']:
        prev_trump = mighty_game.trump
        if mighty_game.declarer in human_players:
            while True:
                final_trump = input("Finalize your trump: ")
                if final_trump in game.suits + [game.no_trump]:
                    feedback = mighty_game.trump_change(final_trump)
                    if feedback == 0:
                        break
                print("Invalid trump.")
        else:
            feedback = mighty_game.trump_change(final_trump)

        new_trump = mighty_game.trump

        changed_or_fixed = 'changed' if new_trump != prev_trump else 'fixed'

        print("The trump suit has been {} to {}.".format(changed_or_fixed, game.suits_short_to_long[final_trump]))
        print('The final bid is {} {}.'.format(game.suits_short_to_long[mighty_game.trump], mighty_game.bid))

    elif call_type == game.GameEngine.calltype['miss-deal check']:
        print("Miss-deal check in process.")
        deal_miss = [False] * 5
        for player in range(5):
            call_miss_deal = False
            if game.is_miss_deal(mighty_game.hands[player], mighty_game.mighty):
                if player in ai_players:
                    call_miss_deal = ai_miss_deal_caller(mighty_game.hands[player], mighty_game.trump)
                else:
                    yes_or_no = input('Player {} - Call miss-deal?: '.format(player))
                    if yes_or_no.lower() in ('y', 'yes'):
                        call_miss_deal = True
                if call_miss_deal:
                    print("Player {} announces miss-deal!".format(player))
                    print(' '.join(mighty_game.hands[player]))
                deal_miss[player] = call_miss_deal

        for player in range(5):
            feedback = mighty_game.miss_deal_check(player, deal_miss[player])
            if feedback:
                print('Fuck.')
                print(feedback)
                exit(1)
            if mighty_game.next_call != game.GameEngine.calltype['miss-deal check']:
                break

    elif call_type == game.GameEngine.calltype['friend call']:
        print("Friend to be called.")
        if mighty_game.declarer in ai_players:
            friend_card = ai_friend_caller(mighty_game.hands[mighty_game.declarer], mighty_game.trump)
        else:
            while True:
                friend_card = input("Enter friend card: ")
                if friend_card in game.cards:
                    break
                print("Invalid card.")

        print("{} friend called.".format(card_repr(friend_card)))
        feedback = mighty_game.friend_call(friend_card)

    elif call_type == game.GameEngine.calltype['redeal']:
        print("REDEAL IN PROCESS.")
        mighty_game = game.GameEngine()
        print("REDEAL COMPLETE.")
        print()
        introduce_hands(mighty_game.hands, human_players)

    elif call_type == game.GameEngine.calltype['play']:

        # Below block finds whose turn it is.
        player = mighty_game.leader
        for _ in range(len(mighty_game.current_trick)):
            player = game.next_player(player)

        if player == mighty_game.leader:
            print("Trick #{}".format(len(mighty_game.completed_tricks) + 1))
            print()

        for p, c in mighty_game.current_trick:
            print("Player {}: {}".format(p, card_repr(c)))
        print()
        print("Player {}'s turn to play.".format(player))

        perspective = mighty_game.perspective(player)

        if player in ai_players:
            card = ai_player(perspective)
        else:
            while True:
                card = input("Player {} - Enter card to play: ".format(player))
                if game.is_valid_move(len(mighty_game.completed_tricks), mighty_game.current_trick,
                                      mighty_game.suit_led, mighty_game.trump, mighty_game.hands[player], card):
                    break
                print("Invalid play.")

        suit_led = game.uninit['suit']
        activate_joker_call = False

        print("Player {} plays {}.".format(player, card_repr(card)))

        if card == game.joker and player == mighty_game.leader:
            if player in ai_players:
                suit_led = ai_suit_led_specifier(mighty_game.perspective(player))
            else:
                while True:
                    suit_led = input("Specify the suit led: ")
                    if suit_led in game.suits:
                        break
                    print("Invalid suit.")
            print("Suit led is {}.".format(suit_led))
        elif card == mighty_game.ripper and player == mighty_game.leader:
            if player in ai_players:
                activate_joker_call = ai_joker_call_activator(mighty_game.perspective(player))
            else:
                yes_or_no = input("Activate joker call?: ")
                if yes_or_no.lower() in ('yes', 'y'):
                    activate_joker_call = True
            if activate_joker_call:
                print("Joker call activated!")

        feedback = mighty_game.play(player, card, suit_led, activate_joker_call)

    elif call_type == game.GameEngine.calltype['game over']:
        break

    else:
        print("CRITICAL: There is no method of handling specified for call type '{}'".format(call_type))
        exit(1)

    if feedback:
        print('Calltype: {}, Error #{}'.format(mighty_game.next_call, feedback))
        exit(1)

    if mighty_game.recent_winner != game.uninit['player']:
        print("Trick won by Player {}!".format(mighty_game.recent_winner))
        for p in range(5):
            if p not in (mighty_game.declarer, mighty_game.friend):
                print('Player {}: {} points'.format(p, len(mighty_game.point_cards[p])))
        print()

    print('-------------------------------')

print("The game is over.")
print("The bid was {} {}.".format(game.suits_short_to_long[mighty_game.trump], mighty_game.bid))
print("The Declarer and Friend collected {} points.".format(mighty_game.declarer_team_points))
print("Did the Declarer win?: {}".format(mighty_game.declarer_won))
print("The following gamepoints are rewarded to each player:")
for player in range(len(mighty_game.gamepoints_rewarded)):
    formated_points = mighty_game.gamepoints_rewarded[player]
    if formated_points > 0:
        formated_points = '+' + str(formated_points)
    else:
        formated_points = str(formated_points)
    print("Player {}: {} gamepoints".format(player, formated_points))
