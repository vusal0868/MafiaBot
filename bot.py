from telegram.ext import Updater, CommandHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import random

# --- GLOBALS --- #
game_state = False  # True - currently going, false - passive
registration_state = False  # True - currently going, false - passive
players = dict()  # Key: ID of player, value: object of Player class
quantity = 0
used = []
roles = dict()  # Key: role, value: ID of player
mafioso_list = []
reg_message_id = None
game_chat_id = None
last_message_id = dict()  # Key : id of player, value: last message id

# --- CONSTANTS --- #
BOT_TOKEN = "416682801:AAHygzvxHclVevhrwIufoUuNCAgJueh2GpI"
REGISTRATION_TIME = 60  # In seconds
REQUIRED_PLAYERS = 1
LEADERS_INNOCENTS = ['detective']
SPECIAL_INNOCENTS = ['doctor', 'prostitute']
SPECIAL_MAFIOSI = ['godfather']
OTHERS = ['maniac']
'''
    QUANTITY_OF_ROLES
    It is a dictionary, keys of which are a number of players, the values are the quantities of roles:
    each value is a string, each of digits in which represents the quantity of each type of character, accordingly:
        1. Leaders of innocents. There are randomly selected from LEADERS_INNOCENTS.
        2. Simple innocents
        3. Special innocents. Randomly selected from SPECIAL_INNOCENTS
        4. Simple mafiosi
        5. Special mafiosi. Randomly selected from SPECIAL_MAFIOSI
        6. Individuals, such as maniac. Randomly selected from  OTHERS 
'''
QUANTITY_OF_ROLES = {1: '0 0 0 1 0 0', 2: '1 0 0 1 0 0', 3: '1 1 0 1 0 0', 4: '1 1 0 2 0 0', 5: '1 2 0 2 0 0',
                     6: '1 3 0 2 0 0', 7: '1 2 1 3 0 0', 8: '1 3 1 2 1 0', 9: '1 3 1 3 1 0', 10: '1 3 1 3 1 1',
                     11: '1 5 1 2 1 1', 12: '1 5 2 2 1 1', 13: '1 6 2 2 1 1', 14: '1 6 2 3 1 1', 15: '1 7 2 3 1 1',
                     16: '1 7 2 4 1 1'}
ROLES_PRIORITY = ['prostitute', 'doctor', 'mafioso', 'detective', 'maniac', 'godfather', 'innocent']
ROLE_GREETING = {
    "Detective": '\n'.join(["You are a Detective Dylan Burns. Your goal is to save innocents and to destroy mafiosi.",
                            "Your special ability is to check one's card or to kill somebody during the night.",
                            "Good luck, Detective, and let the justice prevail!"]),
    "Doctor": '\n'.join(["You are a Dr. Smolder Bravestone. Your goal is to save innocents and to stay alive.",
                         "Your special ability is to heal one person during the night",
                         "Good luck, Doctor, and let the justice prevail!"]),
    "Prostitute": '\n'.join(["You are a prostitute Sloan Giles",
                             "Your goal is to survive, however, you are helping innocents.",
                             "Your special ability is to disable one player for one round during the night.",
                             "Good luck, Sloan!"]),
    "Godfather": '\n'.join(["You are a Godfather Vittore Guarente.",
                            "Your goal is to destroy innocents and to help mafiosi.",
                            "Your special ability is to disable one player as a voter.",
                            "Good luck, Godfather, and let the dark forces win!"]),
    "Maniac": '\n'.join(["You are a Maniac Frank McStein. Your goal is to kill everybody in town.",
                         "You can kill one player during the night.",
                         "Good luck, Maniac, and let the forces of madness win!"]),
    "Innocent": '\n'.join(["You are an Innocent. You are a creature of the day, so at the night you always sleep.",
                           "Your goal is to destroy mafiosi in your town.",
                           "Good luck, Innocent, and let the law prevail!"]),
    "Mafioso": '\n'.join(["You are a Mafioso. Your special ability is to kill one player during the night.",
                          "However, you have to remember that the cooperation with other mafiosi is crucial for you.",
                          "Good luck, Mafioso, and let the dark forces prevail!"])}

updater = Updater
dispatcher = updater.dispatcher


class Player:
    def __init__(self, user):
        self.ID = user.id
        self.name = user.first_name + (' ' + user.last_name if user.last_name else '')
        self.nick = user.username
        self.card = None
        self.is_alive = True
        self.is_abilities_active = True
        self.can_be_killed = True
        self.able_to_vote = True
        self.able_to_discuss = True
        self.chat_id = None


def distribute_roles():
    global roles
    global players
    global QUANTITY_OF_ROLES
    global LEADERS_INNOCENTS
    global SPECIAL_MAFIOSI
    global SPECIAL_INNOCENTS
    global OTHERS
    global quantity
    global mafioso_list

    print('Distributing roles...')

    roles_q = list(map(int, QUANTITY_OF_ROLES[quantity].split(' ')))

    leaders_innocents = random.sample(LEADERS_INNOCENTS, roles_q[0])
    special_innocents = random.sample(SPECIAL_INNOCENTS, roles_q[2])
    special_mafiosi = random.sample(SPECIAL_MAFIOSI, roles_q[4])
    others = random.sample(OTHERS, roles_q[5])

    rand_players = [i.ID for i in players.values()]
    random.shuffle(rand_players)

    ind = 0
    for i in range(len(leaders_innocents)):
        players[rand_players[ind]].card = leaders_innocents[i].capitalize()
        roles[leaders_innocents[i].capitalize()] = rand_players[ind]
        ind += 1

    for i in range(len(special_innocents)):
        players[rand_players[ind]].card = special_innocents[i].capitalize()
        roles[special_innocents[i].capitalize()] = rand_players[ind]
        ind += 1

    for i in range(len(special_mafiosi)):
        players[rand_players[ind]].card = special_mafiosi[i].capitalize()
        roles[special_mafiosi[i].capitalize()] = rand_players[ind]
        ind += 1

    for i in range(len(others)):
        players[rand_players[ind]].card = others[i].capitalize()
        roles[others[i].capitalize()] = rand_players[ind]
        ind += 1

    roles['Innocent'] = []
    for i in range(roles_q[1]):
        players[rand_players[ind]].card = 'Innocent'
        roles['Innocent'].append(rand_players[ind])
        ind += 1

    roles['Mafioso'] = []
    for i in range(roles_q[3]):
        players[rand_players[ind]].card = 'Mafioso'
        roles['Mafioso'].append(rand_players[ind])
        mafioso_list.append(
            '[' + players[rand_players[ind]].name + ']' + '(tg://user?id=' + str(rand_players[ind]) + ')')
        ind += 1

        print('Roles distribution finished:')
        for key, value in roles.items():
            if key == 'Mafioso':
                print('Mafiosi: {}'.format(', '.join([players[i].name for i in value])))
            elif key == 'Innocent':
                print('Innocents: {}'.format(', '.join([players[i].name for i in value])))
            else:
                print(key + ': ' + players[value].name)

    # These ifs are for debug, as situation with no mafiosi/innocents is prohibited by the rules
    if not roles['Mafioso']:
        del roles['Mafioso']

    if not roles['Innocent']:
        del roles['Innocent']


def send_roles(bot):
    global roles
    global mafioso_list
    global players
    global ROLE_GREETING
    global last_message_id

    print('Sending roles...')

    for role, player in roles.items():
        if role == 'Mafioso':
            for pl in player:
                bot.send_message(chat_id=pl, text=ROLE_GREETING[role])
                if len(mafioso_list) > 1:
                    bot.send_message(chat_id=pl, text='Other mafiosi: \n{}'.format(
                        '\n'.join(i for i in mafioso_list if not (str(pl) in i))),
                                     parse_mode='Markdown')
                last_message_id[pl] += 1
        elif role == 'Innocent':
            for pl in player:
                bot.send_message(chat_id=pl, text=ROLE_GREETING[role])
                last_message_id[pl] += 1
        else:
            bot.send_message(chat_id=player, text=ROLE_GREETING[role])
            last_message_id[player] += 1

    print('Roles were sent successfully')


# Role functions
# IMPORTANT: name functions as roles, in lowercase
def detective(bot):
    global roles
    global players

    print('Detective woke up')

    check_or_shoot = InlineKeyboardMarkup(
        [[InlineKeyboardButton('Shoot', callback_data='detective_shoot'),
          InlineKeyboardButton('Check identity', callback_data='detective_check')]])

    bot.send_message(chat_id=roles['Detective'], text='Are you feeling pacifistic tonight?',
                     reply_markup=check_or_shoot)
    last_message_id[roles['Detective']] += 1


def mafioso(bot):
    global roles
    global players
    global mafioso_list

    print('Mafiosi woke up')

    shoot_voting = []
    for role, _id in roles.items():
        if role == 'Innocent':
            for inn in _id:
                shoot_voting.append([InlineKeyboardButton(players[inn].name, callback_data='maf_kill:{}'.format(inn))])
        elif role != 'Mafioso':
            shoot_voting.append([InlineKeyboardButton(players[_id].name, callback_data='maf_kill:{}'.format(_id))])

    for i in roles['Mafioso']:
        bot.send_message(chat_id=i, text='Choose a target properly',
                         reply_markup=InlineKeyboardMarkup(shoot_voting))
        last_message_id[i] += 1


def innocent():
    print('Innocents are still asleep!')


# Main
def game(bot, chat_id):
    global game_state
    global players
    global roles
    global ROLES_PRIORITY

    game_state = True
    print('Game started')
    bot.send_message(chat_id=chat_id, text='Game is started. And may the strongest win.')

    distribute_roles()
    send_roles(bot)

    ordered_roles = sorted(roles.keys(),
                           key=lambda x: ROLES_PRIORITY.index(x.lower()))

    for i in ordered_roles:
        exec(i.lower() + '(bot)')  # Functions for each role are named identically to roles themselves


# Starts on '/game'
def registration_command(bot, update):
    global game_state
    global quantity
    global registration_state
    global players
    global reg_message_id
    global game_chat_id

    if not (game_state or registration_state):
        bot.send_message(chat_id=update.message.chat_id, text='And may the odds be ever in your favor')
        registration_state = True

        keyboard = [[InlineKeyboardButton('Register!', url="https://t.me/goodgoosebot?start=Register")]]
        msg_markup = InlineKeyboardMarkup(keyboard)

        reg_message_id = update.message.message_id + 2
        game_chat_id = update.message.chat_id
        bot.send_message(chat_id=update.message.chat_id, text='*Registration is active!*',
                         parse_mode="Markdown", reply_markup=msg_markup)

        bot.pin_chat_message(chat_id=update.message.chat_id, message_id=reg_message_id, disable_notification=True)
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Currently running')


# On '/stop'
def stop_command(bot, update):
    global game_state
    global registration_state
    global quantity
    global players
    global mafioso_list
    global roles
    global reg_message_id
    global registration_state

    if game_state or registration_state:
        bot.send_message(chat_id=update.message.chat_id, text='¡Sí, señor!')

        if registration_state:
            bot.delete_message(chat_id=update.message.chat_id, message_id=reg_message_id)
            bot.delete_message(chat_id=update.message.chat_id, message_id=reg_message_id - 1)

        game_state = False
        registration_state = False

        quantity = 0
        players.clear()
        roles.clear()
        used.clear()
        mafioso_list.clear()

        bot.send_message(chat_id=update.message.chat_id, text='Game aborted successfully.')
    else:
        bot.send_message(chat_id=update.message.chat_id, text='There is no active game to stop :(')


# On '/start'
def reg_player_command(bot, update):
    global registration_state
    global quantity
    global reg_message_id
    global game_chat_id
    global last_message_id

    if registration_state:
        new_user = Player(update.message.from_user)

        if new_user.ID in used:
            bot.send_message(chat_id=update.message.chat_id,
                             text='You are already registered. Please wait for other players :)')
            return

        players[new_user.ID] = new_user
        quantity += 1

        print('Player {}: {}, {}'.format(quantity, new_user.name, new_user.ID))

        last_message_id[new_user.ID] = update.message.message_id
        used.append(new_user.ID)

        keyboard = [[InlineKeyboardButton('Register!', url="https://t.me/goodgoosebot?start=Register")]]
        msg_markup = InlineKeyboardMarkup(keyboard)

        bot.edit_message_text(chat_id=game_chat_id, message_id=reg_message_id,
                              text='Registration is active!\n\n*Registered players:* \n{}\n\nTotal: *{}*'.format(
                                  ', '.join(
                                      ['[' + i.name + ']' + '(tg://user?id=' + str(i.ID) + ')' for _, i in
                                       players.items()]),
                                  str(quantity)), parse_mode="Markdown", reply_markup=msg_markup)
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text='Registration is not active right now. Please call "/game" to start registration')


# On '/begin_game'
def begin_game_command(bot, update):
    global quantity
    global registration_state
    global game_state
    global REQUIRED_PLAYERS
    global reg_message_id

    if game_state:
        bot.send_message(chat_id=update.message.chat_id, text='Game is already running!')
        return

    if registration_state:
        if quantity >= REQUIRED_PLAYERS:
            bot.send_message(chat_id=update.message.chat_id,
                             text='Registration was successful! Game is starting...')
            registration_state = False

            bot.delete_message(chat_id=update.message.chat_id, message_id=reg_message_id)
            bot.delete_message(chat_id=update.message.chat_id, message_id=reg_message_id - 1)

            game(bot, update.message.chat_id)
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text='\n'.join(['Too small amount of players :(',
                                             'Current amount of players: {}'.format(quantity),
                                             'Amount of players required: {}.'.format(REQUIRED_PLAYERS)]))
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Please call "/game" to begin the registration.')


game_command_handler = CommandHandler('game', registration_command)
stop_command_handler = CommandHandler('stop', stop_command)
reg_command_handler = CommandHandler('start', reg_player_command)
start_command_handler = CommandHandler('begin_game', begin_game_command)

dispatcher.add_handler(game_command_handler)
dispatcher.add_handler(stop_command_handler)
dispatcher.add_handler(reg_command_handler)
dispatcher.add_handler(start_command_handler)

updater.start_polling(clean=True)
