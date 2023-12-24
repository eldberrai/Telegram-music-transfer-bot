import telebot
from telebot import types
import threading
from yandex_music import Client
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyOauthError
from yandex_music.exceptions import UnauthorizedError
import vk_api
from vk_api.audio import VkAudio
import spotify
import yandexapi
import vkapi
import logging
import waiting

bot = telebot.TeleBot('None')
yandex_token = None
spotify_code = None
sp = None
user_info = None
auth_manager = None
transfer_link = None
vk_login = None
vk_password = None
vk_session = None
two_fa_code = None
logger = logging.getLogger("Playlist_transfer.log")
logger.setLevel(logging.DEBUG)
file = logging.FileHandler('playlist_transfer.log', mode='w')
file.setFormatter(logging.Formatter(fmt="%(asctime)s %(name)s %(levelname)s %(message)s"))
logger.addHandler(file)


@bot.message_handler(commands=['start', "В главное меню"])
def hello_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3, one_time_keyboard=True)
    item_1 = types.KeyboardButton("Yandex")
    item_2 = types.KeyboardButton("Spotify")
    item_3 = types.KeyboardButton("VK")
    markup.add(item_1, item_2, item_3)
    bot.send_message(message.chat.id,
                     "Привет! Для дальнейших действий введи название платформы, с которой ты хочешь работать",
                     reply_markup=markup)


@bot.message_handler(content_types=['text'])
def main(message):
    """Стартовая функция для выбора начальной платформы """

    global auth_manager
    global spotify_code
    global sp
    global user_info

    if message.text == 'Yandex':
        instruction = yandexapi.instruct()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        if yandex_token:
            try:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
                item_1 = types.KeyboardButton("Создать Yandex плейлист")
                item_2 = types.KeyboardButton("Получить список песен")
                item_3 = types.KeyboardButton("Перенести в Spotify")
                item_4 = types.KeyboardButton("В главное меню")
                markup.add(item_1, item_2, item_3, item_4)
                Client(yandex_token).init()
                bot.send_message(message.chat.id, f'Ты уже вошел в аккаунт\n'
                                                  f'Что ты хочешь сделать?'
                                 ,reply_markup=markup )
                bot.register_next_step_handler(message, yandex_commands)
            except UnauthorizedError:
                bot.send_message(message.chat.id, instruction, parse_mode='Markdown', reply_markup=markup)
                bot.register_next_step_handler(message, yandex_reg)
        else:
            bot.send_message(message.chat.id, instruction, parse_mode='Markdown', reply_markup=markup)
            bot.register_next_step_handler(message, yandex_reg)

    elif message.text == 'Spotify':
        auth_manager, instruction = spotify.login_inst()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        bot.send_message(message.chat.id, instruction, parse_mode='Markdown', reply_markup=markup)
        bot.register_next_step_handler(message, spotify_reg)

    elif message.text == 'VK':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        bot.send_message(message.chat.id, f'Введите логин и пароль через пробел', reply_markup=markup)
        bot.register_next_step_handler(message, vk_reg)

    elif message.text == "В главное меню":
        hello_message(message)


def spotify_reg(message):
    """Функция для логина в аккаунт пользователя Spotify"""
    global spotify_code
    global sp
    global user_info
    spotify.logout()
    if message.text == "В главное меню":
        hello_message(message)
        return
    spotify_code = message.text
    try:
        token_info = auth_manager.get_access_token(spotify_code)
    except SpotifyOauthError:
        bot.send_message(message.chat.id,
                         f'Неверный код, попробуй снова')
        logger.error('Couldnt log into spotify')
        bot.register_next_step_handler(message, main)
        return

    sp = spotipy.Spotify(auth=token_info['access_token'])
    logger.info('Logged into spotify')
    user_info = sp.current_user()
    bot.send_message(message.chat.id, f"Привет, {user_info['display_name']}!")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    item_1 = types.KeyboardButton("Создать Spotify плейлист")
    item_2 = types.KeyboardButton("Получить список плейлистов")
    item_3 = types.KeyboardButton("Перенести в Yandex")
    item_4 = types.KeyboardButton("В главное меню")
    markup.add(item_1, item_2, item_3, item_4)
    bot.send_message(message.chat.id, f'Выполнен вход в твой Spotify аккаунт. Что ты хочешь сделать?',
                     reply_markup=markup)
    bot.register_next_step_handler(message, spotify_commands)


def spotify_commands(message):
    """Здесь команды с функционалом, доступным для Spotify"""

    global sp
    global user_info
    user = sp.current_user()
    playlists = sp.user_playlists(user['id'])['items']

    if message.text == "Создать Spotify плейлист":
        bot.send_message(message.chat.id,
                         f'Введи название для своего плейлиста и список песен, которые хочешь туда добавить (каждую - с новой строки)')
        bot.register_next_step_handler(message, spotify_copy)
    elif message.text == "Получить список плейлистов":
        all_pl = []
        for i in playlists:
            all_pl.append(i['name'])
        if len(all_pl) == 0:
            bot.send_message(message.chat.id, f'У тебя нет плейлистов, попробуй позже.')
            bot.register_next_step_handler(message, spotify_commands)
            return
        else:
            all_pl = '\n'.join(all_pl)
        bot.send_message(message.chat.id,
                         f'Все плейлисты :\n'
                         f'{all_pl}\n'
                         f'\n'
                         f'Введи название Spotify плейлиста, список песен для которого ты хочешь получить')
        bot.register_next_step_handler(message, spotify_list)
    elif message.text == "Перенести в Yandex":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        item1 = types.KeyboardButton("В главное меню")
        markup.add(item1)
        instruction = yandexapi.instruct()
        if yandex_token:
            try:
                Client(yandex_token).init()
                bot.send_message(message.chat.id, f'Ты уже вошел в аккаунт\n'
                                                  f'Ответным сообщением введи ссылку на Spotify плейлист, который хочешь перенести в Yandex'
                                 , )
                bot.register_next_step_handler(message, help_sp_t_y)
            except UnauthorizedError:
                bot.send_message(message.chat.id, instruction, parse_mode='Markdown', reply_markup=markup)
                bot.register_next_step_handler(message, yandex_reg_for_spotify)
        else:
            bot.send_message(message.chat.id, instruction, parse_mode='Markdown', reply_markup=markup)
            bot.register_next_step_handler(message, yandex_reg_for_spotify)
    elif message.text == "В главное меню":
        hello_message(message)


##### Все для spotify


def spotify_list(message):
    """Выводит список песен из указанного плейлиста"""

    if message.text == "В главное меню":
        hello_message(message)
        return
    playlist = message.text
    file = ''
    try:
        query = spotify.get_playlists(playlist, sp)
    except TypeError:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        bot.send_message(message.chat.id,
                         f'Неверное название, попробуй снова \n'
                         f'Выбери, что хочешь сделать', reply_markup=markup)
        bot.register_next_step_handler(message, spotify_commands)
        logger.warning('Couldnt find playlist in library')
        return
    logger.info('Have found a playlist')
    for song in query:
        if len(file + song + '\n') > 1024:
            bot.send_message(message.chat.id, file)
            file = song + '\n'
        else:
            file += song + '\n'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('В главное меню')
    bot.send_message(message.chat.id, file)
    bot.send_message(message.chat.id,
                     f'Если ты хочешь сделать еще что-то, то нажми команду /start \n', reply_markup=markup)


def yandex_reg_for_spotify(message):
    """Логинится в аккаунт пользователя в яндекс"""
    global yandex_token
    if message.text == "В главное меню":
        hello_message(message)
        return
    yandex_token = message.text
    try:
        Client(yandex_token).init()
    except UnauthorizedError:
        logger.error('Couldnt log into Yandex music')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        bot.send_message(message.chat.id,
                         f'Неверный код, попробуй снова', repky_markup=markup)
        bot.register_next_step_handler(message, spotify_commands)
        return
    logger.info('Logged into yandex music for spotify')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('В главное меню')
    bot.send_message(message.chat.id, f'Выполнен вход в твой Yandex аккаунт.\n '
                                      f'Ответным сообщением введи ссылку на Spotify плейлист, который хочешь перенести в Yandex',
                     reply_markup=markup)
    bot.register_next_step_handler(message, help_sp_t_y)


def help_sp_t_y(message):
    """Вспомогательная функция для последовательного ввода ссылки и названия при переносе"""
    global transfer_link
    if message.text == "В главное меню":
        hello_message(message)
        return
    transfer_link = message.text.split()[0]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('В главное меню')
    bot.send_message(message.chat.id, f'Выбери название, которое хочешь  дать новому плейлисту.\n '
                     ,
                     reply_markup=markup)
    bot.register_next_step_handler(message, spotify_to_yandex)


def spotify_to_yandex(message):
    """Функция для вывода сообщения о добавлении нового плейлиста в медиатеку в яндексе и вывода недоступных на платформе песен"""
    if message.text == "В главное меню":
        hello_message(message)
        return
    name = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('В главное меню')
    bot.send_message(message.chat.id, f'Начали переносить плейлист\n'

                     ,
                     reply_markup=markup)
    try:
        playlist_id = spotify.parser(transfer_link
                                     )
    except ValueError:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        bot.send_message(message.chat.id,
                         f'Ты ввел неверную ссылку, попробуй снова', reply_markup=markup)
        bot.register_next_step_handler(message, spotify_commands)
        logger.warning('Couldnt find a playlist to transfer from spotify to yandex')
        return

    items_to_yandex = spotify.get_playlist_by_url(playlist_id, sp)
    not_available = yandexapi.list_to_yandex(name, items_to_yandex, yandex_token)
    logger.info('Have trasfered playlist from spotify to yandex')
    file = ''
    if len(not_available) != 0:
        for song in not_available:
            if len(file + song + '\n') > 1024:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                markup.row('В главное меню')
                bot.send_message(message.chat.id,
                                 f'Добавили выбранный плейлист в твою коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n'
                                 f'Некоторые песни не удалось добавить((\n{file}', reply_markup=markup)
                file = song + '\n'
            else:
                file += song + '\n'
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        bot.send_message(message.chat.id,
                         f'Добавили выбранный плейлист в твою коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n'
                         f'Некоторые песни не удалось добавить((\n{file}', reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        bot.send_message(message.chat.id,
                         f'Добавили выбранный плейлист в твою коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n',
                         reply_markup=markup)


def spotify_copy(message):
    """Функция для оповещения пользователя о добавлении плейлиста в медиатеку spotify"""
    if message.text == "В главное меню":
        hello_message(message)
        return
    user_input = message.text.split('\n')
    name = user_input[0]
    tracks = user_input[1:]
    spotify.search_create_add(tracks, name, sp)
    logger.info('Have added a playlist to spotify')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('В главное меню')
    bot.send_message(message.chat.id,
                     f'Добавили выбранный плейлист в твою медиатеку!Если ты хочешь сделать еще что-то, то нажми команду /start \n',
                     reply_markup=markup)


##########


def yandex_reg(message):
    """Функция для логина в аккаунт пользователя Yandex"""
    global yandex_token
    if message.text == "В главное меню":
        hello_message(message)
        return
    yandex_token = message.text
    try:
        Client(yandex_token).init()
    except UnauthorizedError:
        bot.send_message(message.chat.id,
                         f'Неверный код, попробуй снова')
        logger.error('Couldnt log intp yandex music')
        bot.register_next_step_handler(message, main)
        return
    logger.info('Logged into yandex music')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    item_1 = types.KeyboardButton("Создать Yandex плейлист")
    item_2 = types.KeyboardButton("Получить список песен")
    item_3 = types.KeyboardButton("Перенести в Spotify")
    item_4 = types.KeyboardButton("В главное меню")
    markup.add(item_1, item_2, item_3, item_4)
    bot.send_message(message.chat.id, f'Выполнен вход в твой Yandex аккаунт. Что ты хочешь сделать?',
                     reply_markup=markup)
    bot.register_next_step_handler(message, yandex_commands)


def yandex_commands(message):
    global auth_manager
    """Здесь команды с функционалом, доступным для Spotify"""
    if message.text == "Создать Yandex плейлист":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        bot.send_message(message.chat.id,
                         f'Введи название для своего плейлиста и список песен, которые хочешь туда добавить (каждую - с новой строки)'
                         ,
                         reply_markup=markup)
        bot.register_next_step_handler(message, yandex_copy)
    elif message.text == "Получить список песен":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        bot.send_message(message.chat.id,
                         f'Введи ссылку на Yandex плейлист, список песен для которого ты хочешь получить',
                         reply_markup=markup)
        bot.register_next_step_handler(message, yandex_list)
    elif message.text == "Перенести в Spotify":
        auth_manager, instruction = spotify.login_inst()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        if spotify_code:
            try:
                token_info = auth_manager.get_access_token(spotify_code)
                bot.send_message(message.chat.id, f'Ты уже вошел в аккаунт \n'
                                                  f'Ответным сообщением введи ссылку на Spotify плейлист, который хочешь перенести в Yandex'
                                 , )
                bot.register_next_step_handler(message, help_y_t_sp)
            except SpotifyOauthError:
                bot.send_message(message.chat.id, instruction, parse_mode='Markdown')
                bot.register_next_step_handler(message, spotify_reg_for_yandex)
        else:
            bot.send_message(message.chat.id, instruction, parse_mode='Markdown')
            bot.register_next_step_handler(message, spotify_reg_for_yandex)
    elif message.text == "В главное меню":
        hello_message(message)


def spotify_reg_for_yandex(message):
    """Логинится в аккаунт пользователя в Spotify"""
    global spotify_code
    global sp
    global user_info
    spotify.logout()
    if message.text == "В главное меню":
        hello_message(message)
        return
    spotify_code = message.text
    try:
        token_info = auth_manager.get_access_token(spotify_code)
    except SpotifyOauthError:
        bot.send_message(message.chat.id,
                         f'Неверный код, попробуй снова')
        logger.error('Couldnt log into spotify')
        bot.register_next_step_handler(message, yandex_commands)
        return

    sp = spotipy.Spotify(auth=token_info['access_token'])
    logger.info('Logged into spotify for work with yandex')
    user_info = sp.current_user()

    bot.send_message(message.chat.id, f"Привет, {user_info['display_name']}!")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('В главное меню')
    bot.send_message(message.chat.id, f'Выполнен вход в твой Spotify аккаунт.\n'
                                      f'Введи ссылку на Yandex music плейлист, который хочешь перенести в Spotify\n'
                     ,
                     reply_markup=markup)
    bot.register_next_step_handler(message, help_y_t_sp)


def help_y_t_sp(message):
    """Вспомогательная функция для последовательного ввода ссылки и названия плейлиста"""
    global transfer_link
    if message.text == "В главное меню":
        hello_message(message)
        return
    transfer_link = message.text.split()[0]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('В главное меню')
    bot.send_message(message.chat.id, f'Выбери название, которое хочешь  дать новому плейлисту.\n '
                     ,
                     reply_markup=markup)
    bot.register_next_step_handler(message, yandex_to_spotify)


def yandex_copy(message):
    """
    Создает новый плейлист и добавляет в него песни из списка пользователя"
    """
    if message.text == "В главное меню":
        hello_message(message)
        return
    user_input = message.text.split('\n')
    name = user_input[0]
    tracks = user_input[1:]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('В главное меню')
    not_available = yandexapi.list_to_yandex(name, tracks, yandex_token)
    logger.info('Have added new playlist to yandex music')
    file = ''
    if len(not_available) != 0:
        for song in not_available:
            if len(file + song + '\n') > 1024:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                markup.row('В главное меню')
                bot.send_message(message.chat.id,
                                 f'Добавили выбранный плейлист в твою коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n'
                                 f'Некоторые песни не удалось добавить((\n{file}', reply_markup=markup)
                file = song + '\n'
            else:
                file += song + '\n'
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.row('В главное меню')
            bot.send_message(message.chat.id,
                             f'Добавили выбранный плейлист в твою коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n'
                             f'Некоторые песни не удалось добавить((\n{file}', reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        bot.send_message(message.chat.id,
                         f'Добавили выбранный плейлист в твою коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n',
                         reply_markup=markup)


def yandex_to_spotify(message):
    """Функция для оповещения пользователя о начале переноса плейлиста"""
    global spotify_code
    global sp
    global user_info
    global transfer_link
    if message.text == "В главное меню":
        hello_message(message)
        return
    name = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('В главное меню')
    bot.send_message(message.chat.id, f'Начали переносить плейлист\n'

                     ,
                     reply_markup=markup)
    transfer_list = yandex_to_list(transfer_link, yandex_token, message)
    if transfer_list is None:
        bot.register_next_step_handler(message, yandex_commands)
        logger.warning('Couldnt transfer a playlist from yandex to spotify')
        return
    logger.info('Have transferred a playlist from yandex to spotify')
    spotify.search_create_add(transfer_list, name, sp)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('В главное меню')
    bot.send_message(message.chat.id,
                     f'Добавили выбранный плейлист в вашу коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n',
                     reply_markup=markup)


def yandex_list(message):
    """ Функция для вывода песен из плейлиста пользователя"""
    if message.text == "В главное меню":
        hello_message(message)
        return
    link = message.text
    file = ''
    for song in yandex_to_list(link, yandex_token, message):
        logger.info('Have found a playlist in yandex music')
        if len(file + song + '\n') > 1024:
            bot.send_message(message.chat.id, file)
            file = song + '\n'
        else:
            file += song + '\n'
    bot.send_message(message.chat.id, file)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('В главное меню')
    bot.send_message(message.chat.id,
                     f'Если ты хочешь сделать еще что-то, то нажми команду /start \n', reply_markup=markup)


def yandex_to_list(link: str, token, message):
    """По ссылке на плейлист в яндекс музыке возвращает лист песен"""
    client = Client(token).init()
    try:
        i = 0
        while i < len(link):
            if link[i:i + 16] == 'music.yandex.ru/':
                i += 16
                if link[i] == 'u':
                    i += 6
                    user_id = ''
                    while link[i] != '/':
                        user_id += link[i]
                        i += 1
                    i += 11
                    playlist_id = link[i:]
                    return yandexapi.get_playlist(playlist_id, user_id, client)
                elif link[i] == 'a':
                    i += 6
                    album_id = link[i:]
                    return yandexapi.get_album(album_id, client)
            i += 1
        raise ValueError
    except ValueError:
        bot.send_message(message.chat.id,
                         f'Ты ввел неверную ссылку, попробуйт снова.\n'
                         f'Нажми на кнопку "Перенести в spotify и повтори процедуру еще раз')
        logger.warning('Invalid link for yandex music')

    except:
        bot.send_message(message.chat.id,
                         f'Нет прав для просмотра, попробуй залогиниться снова.\n'
                         f'Нажми на кнопку "Перенести в spotify и повтори процедуру еще раз')
        bot.register_next_step_handler(message, main)
        logger.warning('Have no access to yandex music playlist')


### Все для вк

def captcha_handler(captcha):
    """ При возникновении капчи вызывается эта функция и ей передается объект
        капчи. Через метод get_url можно получить ссылку на изображение.
        Через метод try_again можно попытаться отправить запрос с кодом капчи
    """

    key = input("Enter captcha code {0}: ".format(captcha.get_url())).strip()

    return captcha.try_again(key)



def vk_reg(message):
    global vk_login
    global vk_password
    global vk_session
    if message.text == "В главное меню":
        hello_message(message)
        return
    vk_login, vk_password = message.text.split()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('В главное меню')
    bot.send_message(message.chat.id,
                     f'Введи код, присланный на номер телефона или отправь прочерк(-), если двухфакторка не подключена',
                     reply_markup=markup)
    bot.register_next_step_handler(message, two_fa_code_handler)
    vk_session = vk_api.VkApi(vk_login, vk_password, auth_handler=auth_handler, app_id=2685278)
    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        logger.error('Couldnt log into VK')
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    item_2 = types.KeyboardButton("Получить список плейлистов")
    item_3 = types.KeyboardButton("Перенести в Spotify")
    item_4 = types.KeyboardButton("Перенести в Yandex")
    item_5 = types.KeyboardButton("В главное меню")
    markup.add(item_2, item_3, item_4, item_5)
    bot.send_message(message.chat.id, f'Выполнен вход в твой VK аккаунт. Что ты хочешь сделать?',
                     reply_markup=markup)
    bot.register_next_step_handler(message, vk_commands)

def two_fa_code_handler(message):
    global two_fa_code
    two_fa_code = message.text


def auth_handler():
    """Для двухфакторной авторизации"""
    global two_fa_code

    return waiting.wait(lambda: two_fa_code), True


def vk_commands(message):
    """Функция с командами доступными для ВК"""
    if message.text == "Получить список плейлистов":

        all_pl = []
        for i in vkapi.get_all_albums(vk_session):
            logger.info("Have access to users playlists")
            all_pl.append(i['title'])
        if len(all_pl) == 0:
            bot.send_message(message.chat.id, f'У тебя нет плейлистов, попробуй позже.')
            bot.register_next_step_handler(message, spotify_commands)
            return
        else:
            all_pl = '\n'.join(all_pl)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        bot.send_message(message.chat.id,
                         f'Все плейлисты :\n'
                         f'{all_pl}\n'
                         f'\n'
                         f'Введи название Vk плейлиста, список песен для которого ты хочешь получить',
                         reply_markup=markup)
        bot.register_next_step_handler(message, vk_list)
    elif message.text == "Перенести в Spotify":
        global auth_manager
        auth_manager, instruction = spotify.login_inst()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        if spotify_code:
            try:

                token_info = auth_manager.get_access_token(spotify_code)
                bot.send_message(message.chat.id, f'Ты уже вошел в аккаунт \n'
                                                  f'Введи название плейлиста, который хочешь перенести в Spotify\n'
                                 , )
                bot.register_next_step_handler(message, help_vk_t_sp)
            except SpotifyOauthError:
                bot.send_message(message.chat.id, instruction, parse_mode='Markdown')
                bot.register_next_step_handler(message, spotify_reg_for_vk)
        else:
            bot.send_message(message.chat.id, instruction, parse_mode='Markdown')
            bot.register_next_step_handler(message, spotify_reg_for_vk)
    elif message.text == "Перенести в Yandex":
        instruction = yandexapi.instruct()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        if yandex_token:
            try:
                Client(yandex_token).init()
                bot.send_message(message.chat.id, f'Ты уже вошел в аккаунт\n'
                                                  f'Ответным сообщением введи название плейлиста в Vk, который ты хочешь перенести'
                                 , )
                bot.register_next_step_handler(message, help_vk_to_y)
            except UnauthorizedError:
                bot.send_message(message.chat.id, instruction, parse_mode='Markdown', reply_markup=markup)
                bot.register_next_step_handler(message, yandex_reg_for_vk)
        else:
            bot.send_message(message.chat.id, instruction, parse_mode='Markdown', reply_markup=markup)
            bot.register_next_step_handler(message, yandex_reg_for_vk)
    elif message.text == "В главное меню":
        hello_message(message)


#
def spotify_reg_for_vk(message):
    """Логинится в Spotify"""
    global spotify_code
    global sp
    global user_info
    spotify.logout()
    if message.text == "В главное меню":
        hello_message(message)
        return
    spotify_code = message.text
    try:
        token_info = auth_manager.get_access_token(spotify_code)
    except SpotifyOauthError:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        bot.send_message(message.chat.id,
                         f'Неверный код, попробуй снова', reply_markup=markup)
        logger.error('Couldnt log into spotify')
        bot.register_next_step_handler(message, yandex_commands)
        return

    sp = spotipy.Spotify(auth=token_info['access_token'])
    logger.info("Logged into spotify")
    user_info = sp.current_user()

    bot.send_message(message.chat.id, f"Hello {user_info['display_name']}!")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('В главное меню')
    bot.send_message(message.chat.id, f'Выполнен вход в твой Spotify аккаунт.\n'
                                      f'Введи название плейлиста, который хочешь перенести в Spotify\n'
                     , reply_markup=markup)
    bot.register_next_step_handler(message,  help_vk_t_sp)


def help_vk_t_sp(message):
    """Вспомогательная функция для последовательного ввода ссылки и названия плейлиста"""
    global transfer_link
    if message.text == "В главное меню":
        hello_message(message)
        return
    name = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('В главное меню')

    try:
        transfer_link = vkapi.get_album_by_name(message,vk_session, name)

    except vk_api.exceptions.AccessDenied:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        bot.send_message(message.chat.id, "Это не твой созданный плейлист, ты обманул", reply_markup=markup)
        bot.register_next_step_handler(message, vk_commands)
        logger.warning('No playlist to transfer from Vk to spotify')
        return

    bot.send_message(message.chat.id, f'Выбери название, которое хочешь  дать новому плейлисту.\n '
                     ,
                     reply_markup=markup)
    bot.register_next_step_handler(message, vk_to_spotify)

def yandex_reg_for_vk(message):
    """Логинится в Yandex"""
    global yandex_token
    if message.text == "В главное меню":
        hello_message(message)
        return
    yandex_token = message.text
    try:
        Client(yandex_token).init()
    except UnauthorizedError:
        bot.send_message(message.chat.id,
                         f'Неверный код, попробуй снова')
        bot.register_next_step_handler(message, spotify_commands)
        logger.error('Couldnt login into yandex music')
        return
    logger.info("Logged into yandex music for VK")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('В главное меню')
    bot.send_message(message.chat.id, f'Выполнен вход в твой Yandex аккаунт.\n '
                                      f'Ответным сообщением введи название плейлиста из VK, который хочешь перенести в Yandex',
                     reply_markup=markup)
    bot.register_next_step_handler(message, help_vk_to_y)


def vk_list(message):
    """Выводит список песен по названию плейлиста или альбома"""
    global vk_session
    if message.text == "В главное меню":
        hello_message(message)
        return
    name = message.text
    file = ''
    try:
        songs = vkapi.get_album_by_name(message, vk_session, name)
    except vk_api.exceptions.AccessDenied:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        bot.send_message(message.chat.id, "Это не твой созданный плейлист, ты обманул", reply_markup=markup)
        bot.register_next_step_handler(message, vk_commands)
        logger.warning('Have no Vk playlist with such name')
        return
    except ValueError:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        bot.send_message(message.chat.id, "Альбом/Плейлист с таким названием не найден.", reply_markup=markup)
        logger.warning('Have no playlists in Vk to show')
    if songs:
        for song in songs:
            logger.warning('Получен доступ к плейлисту Vk')
            if len(file + song + '\n') > 1024:
                bot.send_message(message.chat.id, file)
                file = song + '\n'
            else:
                file += song + '\n'
    bot.send_message(message.chat.id, file)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('В главное меню')
    bot.send_message(message.chat.id,
                     f'Если ты хочешь сделать еще что-то, то нажми команду /start \n', reply_markup=markup)


def vk_to_spotify(message):
    """Оповещает пользователя о добавлении плейлиста в медиатеку Spotify"""
    global sp
    global transfer_link
    if message.text == "В главное меню":
        hello_message(message)
        return
    name = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('В главное меню')
    bot.send_message(message.chat.id, f'Начали переносить плейлист\n'

                     ,
                     reply_markup=markup)

    spotify.search_create_add(transfer_link, name, sp)
    logger.info('Have transferred a playlist from spotify to vk')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('В главное меню')
    bot.send_message(message.chat.id,
                     f'Добавили выбранный плейлист в вашу коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n',
                     reply_markup=markup)


def help_vk_to_y(message):
    global transfer_link
    if message.text == "В главное меню":
        hello_message(message)
        return
    name = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('В главное меню')
    try:
        transfer_link = vkapi.get_album_by_name(message, vk_session, name)
    except vk_api.exceptions.AccessDenied:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        bot.send_message(message.chat.id, "Это не твой созданный плейлист, ты обманул", reply_markup=markup)
        bot.register_next_step_handler(message, vk_commands)
        logger.warning('Have no playlist to transfer from Vk to yandex music')
        return
    except ValueError:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        bot.send_message(message.chat.id, "Альбом/Плейлист с таким названием не найден.", reply_markup=markup)
        logger.warning('Have no playlist with such name to transfer from Vk to yandex music')
    bot.send_message(message.chat.id, f'Выбери название, которое хочешь  дать новому плейлисту.\n '
                     ,
                     reply_markup=markup)
    bot.register_next_step_handler(message, vk_to_yandex)


def vk_to_yandex(message):
    global transfer_link
    """Оповещает пользователя о добавлении плейлиста в медиатеку Yandex"""
    if message.text == "В главное меню":
        hello_message(message)
        return
    name = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('В главное меню')
    bot.send_message(message.chat.id, f'Начали переносить плейлист\n'

                     ,
                     reply_markup=markup)

    not_available = yandexapi.list_to_yandex(name, transfer_link, yandex_token)
    logger.info('Have transferred playlist from Vk to yandex music')
    file = ''
    if len(not_available) != 0:
        for song in not_available:
            if len(file + song + '\n') > 1024:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                markup.row('В главное меню')
                bot.send_message(message.chat.id,
                                 f'Добавили выбранный плейлист в твою коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n'
                                 f'Некоторые песни не удалось добавить((\n{file}', reply_markup=markup)
                file = song + '\n'
            else:
                file += song + '\n'
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        bot.send_message(message.chat.id,
                         f'Добавили выбранный плейлист в твою коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n'
                         f'Некоторые песни не удалось добавить((\n{file}', reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('В главное меню')
        bot.send_message(message.chat.id,
                         f'Добавили выбранный плейлист в твою коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n',
                         reply_markup=markup)


bot.polling(none_stop=True)
