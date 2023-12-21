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

bot = telebot.TeleBot('token')
yandex_token = None
spotify_code = None
sp = None
user_info = None
auth_manager = None
SPOTIPY_CLIENT_ID = None
SPOTIPY_CLIENT_SECRET = None
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:8080'
transfer_link = None
vk_login = None
vk_password = None
vk_session = None
SPOTIPY_SCOPE = 'playlist-read-collaborative playlist-read-private playlist-modify-public playlist-modify-private'


def logout():
    try:
        os.remove(".spotifycache")
        print("Successfully logged out.")
    except FileNotFoundError:
        print("No cache file found. Already logged out.")


@bot.message_handler(commands=['start', "В главное меню"])
def hello_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    item_1 = types.KeyboardButton("Yandex")
    item_2 = types.KeyboardButton("Spotify")
    item_3 = types.KeyboardButton("VK")
    markup.add(item_1, item_2, item_3)
    bot.send_message(message.chat.id,
                     "Прив кд чд! Для дальнейших действий введи название платформы, с которой ты хочешь работать",
                     reply_markup=markup)


@bot.message_handler(content_types=['text'])
def main(message):
    global auth_manager
    global spotify_code
    global sp
    global user_info

    if message.text == 'Yandex':
        reg_link = 'https://chromewebstore.google.com/detail/yandex-music-token/lcbjeookjibfhjjopieifgjnhlegmkib'
        instruction = f"""
        Чтобы зайти в свой аккаунт Yandex Music, выполни следующие действия:
        1. Установи расширение в Google Chrome по этой [ссылке]({reg_link})
        2. Залогинься в свой аккаунт Яндекса через расширение
        3. Оно автоматически направит в заблокированного бота, просто закрой его
        4. Нажми на иконку расширения в браузере, снизу слева у появившегося окна есть кнопка "Скопировать токен"
        5. Отправь его ответным сообщением
        """


        bot.send_message(message.chat.id, instruction, parse_mode='Markdown')
        bot.register_next_step_handler(message, yandex_reg)
    elif message.text == 'Spotify':
        auth_manager = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                    client_secret=SPOTIPY_CLIENT_SECRET,
                                    redirect_uri=SPOTIPY_REDIRECT_URI,
                                    scope=SPOTIPY_SCOPE,
                                    cache_handler=spotipy.cache_handler.CacheFileHandler(cache_path=".spotifycache"))

        auth_url = auth_manager.get_authorize_url()
        instruction = f"""
        Чтобы зайти в свой аккаунт Spotify, выполните следующие действия:
        1. Залогинься в свой аккаунт через браузер
        2. Перейди по [ссылке]({auth_url})
        3. Скопируй все символы после «?code=» из адреса, на который тебя перенаправит ссылка
        4. Отправь скопированную строку боту
        5. Готово!!
        """

        bot.send_message(message.chat.id, instruction, parse_mode='Markdown')
        bot.register_next_step_handler(message, spotify_reg)


    elif message.text == 'VK':
        bot.send_message(message.chat.id, f'Введите логин и пароль через пробел')
        bot.register_next_step_handler(message, vk_reg)


def spotify_reg(message):
    global spotify_code
    global sp
    global user_info
    logout()
    spotify_code = message.text
    try:
        token_info = auth_manager.get_access_token(spotify_code)
    except SpotifyOauthError:
        bot.send_message(message.chat.id,
                         f'Неверный код, попробуй снова')
        bot.register_next_step_handler(message, main)
        return

    sp = spotipy.Spotify(auth=token_info['access_token'])

    user_info = sp.current_user()
    print(user_info['display_name'])
    bot.send_message(message.chat.id, f"Hello {user_info['display_name']}!")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    item_1 = types.KeyboardButton("Создать Spotify плейлист")
    item_2 = types.KeyboardButton("Получить список плейлистов")
    item_3 = types.KeyboardButton("Перенести в VK")
    item_4 = types.KeyboardButton("Перенести в Yandex")
    markup.add(item_1, item_2, item_3, item_4)
    bot.send_message(message.chat.id, f'Выполнен вход в твой Spotify аккаунт. Что ты хочешь сделать?',
                     reply_markup=markup)
    bot.register_next_step_handler(message, spotify_commands)


def spotify_commands(message):
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
        reg_link = 'https://chromewebstore.google.com/detail/yandex-music-token/lcbjeookjibfhjjopieifgjnhlegmkib'
        instruction = f"""
                       Чтобы зайти в свой аккаунт Yandex Music, выполни следующие действия:
                       1. Установи расширение в Google Chrome по  [ссылке] ({reg_link})
                       2. Залогинься в свой аккаунт Яндекса через расширение
                       3. Оно автоматически направит в заблокированного бота, просто закрой его
                       4. Нажми на иконку расширения в браузере, снизу слева у появившегося окна есть кнопка "Скопировать токен"
                       5. Ответным сообщением отправь токен"""

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        item1 = types.KeyboardButton("В главное меню")
        markup.add(item1)

        if yandex_token:
            try:
                Client(yandex_token).init()
                bot.send_message(message.chat.id, f'Ты уже вошел в аккаунт\n'
                                                  f'Ответным сообщением введи ссылку на Spotify плейлист, который хочешь перенести в Yandex'
                                 ,)
                bot.register_next_step_handler(message, help_sp_t_y)
            except UnauthorizedError:
                bot.send_message(message.chat.id, instruction, parse_mode='Markdown', reply_markup=markup)
                bot.register_next_step_handler(message, yandex_reg_for_spotify)
        else:
            bot.send_message(message.chat.id, instruction, parse_mode='Markdown', reply_markup=markup)
            bot.register_next_step_handler(message, yandex_reg_for_spotify)

    elif message.text == "Перенести в VK":
        pass


##### Все для spotify


def spotify_list(message):
    playlist = message.text
    file = ''
    try:
        query = get_playlists(playlist)
    except TypeError:
        bot.send_message(message.chat.id,
                         f'Неверное название, попробуй снова \n'
                         f'Выбери, что хочешь сделать')
        bot.register_next_step_handler(message, spotify_commands)
        return
    for song in query:
        if len(file + song + '\n') > 1024:
            bot.send_message(message.chat.id, file)
            file = song + '\n'
        else:
            file += song + '\n'
    bot.send_message(message.chat.id, file)
    bot.send_message(message.chat.id,
                     f'Если ты хочешь сделать еще что-то, то нажми команду /start \n')


def yandex_reg_for_spotify(message):
    global yandex_token
    if message.text == "В главное меню":
        bot.register_next_step_handler(message, hello_message)

        return
    yandex_token = message.text
    try:
        Client(yandex_token).init()
    except UnauthorizedError:
        bot.send_message(message.chat.id,
                         f'Неверный код, попробуй снова')
        bot.register_next_step_handler(message, spotify_commands)
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    bot.send_message(message.chat.id, f'Выполнен вход в твой Yandex аккаунт.\n '
                                      f'Ответным сообщением введи ссылку на Spotify плейлист, который хочешь перенести в Yandex',
                     reply_markup=markup)
    bot.register_next_step_handler(message, help_sp_t_y)


def help_sp_t_y(message):
    global transfer_link
    transfer_link = message.text.split()[0]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    bot.send_message(message.chat.id, f'Выбери название, которое хочешь  дать новому плейлисту.\n '
                     ,
                     reply_markup=markup)
    bot.register_next_step_handler(message, spotify_to_yandex)


def spotify_to_yandex(message):
    name = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    bot.send_message(message.chat.id, f'Начали переносить плейлист\n'

                     ,
                     reply_markup=markup)
    try:
        playlist_id = parser(transfer_link)
    except ValueError:
        bot.send_message(message.chat.id,
                         f'Ты ввел неверную ссылку, попробуй снова')
        bot.register_next_step_handler(message, spotify_commands)
        return
    items_to_yandex = get_playlist_by_url(playlist_id)
    not_available = list_to_yandex(name, items_to_yandex, yandex_token)
    file = ''
    if len(not_available) != 0:
        for song in not_available:
            if len(file + song + '\n') > 1024:
                bot.send_message(message.chat.id,
                                 f'Добавили выбранный плейлист в твою коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n'
                                 f'Некоторые песни не удалось добавить((\n{file}')
                file = song + '\n'
            else:
                file += song + '\n'

        bot.send_message(message.chat.id,
                         f'Добавили выбранный плейлист в твою коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n'
                         f'Некоторые песни не удалось добавить((\n{file}')
    else:

        bot.send_message(message.chat.id,
                         f'Добавили выбранный плейлист в твою коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n')


def spotify_copy(message):
    user_input = message.text.split('\n')
    name = user_input[0]
    tracks = user_input[1:]
    search_create_add(tracks, name)
    bot.send_message(message.chat.id,
                     f'Добавили выбранный плейлист в твою медиатеку!Если ты хочешь сделать еще что-то, то нажми команду /start \n')


def get_playlists(playlist_name):
    needed_playlist = None
    user = sp.current_user()
    current_playlists = sp.user_playlists(user['id'])['items']
    playlist_with_items = []
    for playlist in current_playlists:
        if playlist['name'] == playlist_name:
            needed_playlist = playlist
            break
    for pl in sp.playlist_items(needed_playlist['id'])['items']:
        sing = ''
        for i in range(len(pl['track']['artists'])):
            sing += pl['track']['artists'][i]['name']
            if i != len(pl['track']['artists']) - 1:
                sing += ', '
        playlist_with_items.append(
            sing + ' - ' + pl['track']['name'])
    return playlist_with_items


def parser(link: str):  # парсит ссылку для вывода плейлиста по ссылку
    i = 0
    playlist_id = ''
    while i < len(link):
        if link[i:i + 17] == 'open.spotify.com/':
            i += 17
            if link[i] == 'p':
                i += 9
                while i < len(link) and link[i] != '/' and link[i] != '?':
                    playlist_id += link[i]
                    i += 1
                if playlist_id:
                    return playlist_id
                else:
                    raise ValueError("Playlist ID not found")
            else:
                break
        i += 1
    raise ValueError("Invalid link")


def get_playlist_by_url(pl_id):
    current_playlist = sp.playlist_items(pl_id)
    playlist_with_items = []
    for pl in current_playlist['items']:
        sing = ''
        for i in range(len(pl['track']['artists'])):
            sing += pl['track']['artists'][i]['name']
            if i != len(pl['track']['artists']) - 1:
                sing += ', '
        playlist_with_items.append(
            sing + ' - ' + pl['track']['name'])
    return playlist_with_items


def search_create_add(query: list, wanted_name):
    uris = []
    needed_id = None
    for i in query:
        try:
            ur = sp.search(i)['tracks']['items'][0]['uri']
            uris.append(ur)
        except:
            continue
    if len(uris) >= 100:
        uris = uris[:100]
    sp.user_playlist_create(user_info['id'], name=wanted_name)
    for playlist in sp.current_user_playlists()['items']:
        if (playlist['name'] == wanted_name):
            needed_id = playlist['id']
    sp.playlist_add_items(playlist_id=needed_id, items=uris)


##########


def yandex_reg(message):
    global yandex_token
    yandex_token = message.text
    try:
        Client(yandex_token).init()
    except UnauthorizedError:
        bot.send_message(message.chat.id,
                         f'Неверный код, попробуй снова')
        bot.register_next_step_handler(message, main)
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    item_1 = types.KeyboardButton("Скопировать Yandex плейлист")
    item_2 = types.KeyboardButton("Получить список песен")
    item_3 = types.KeyboardButton("Перенести в VK")
    item_4 = types.KeyboardButton("Перенести в Spotify")
    markup.add(item_1, item_2, item_3, item_4)
    bot.send_message(message.chat.id, f'Выполнен вход в твой Yandex аккаунт. Что ты хочешь сделать?',
                     reply_markup=markup)
    bot.register_next_step_handler(message, yandex_commands)


def yandex_commands(message):
    if message.text == "Скопировать Yandex плейлист":
        bot.send_message(message.chat.id,
                         f'Введи ссылку на Yandex плейлист, который ты хочешь скопировать и название, которое хочешь ему дать, через пробел')
        bot.register_next_step_handler(message, yandex_copy)
    elif message.text == "Получить список песен":
        bot.send_message(message.chat.id,
                         f'Введи ссылку на Yandex плейлист, список песен для которого ты хочешь получить')
        bot.register_next_step_handler(message, yandex_list)
    elif message.text == "Перенести в Spotify":
        global auth_manager
        auth_manager = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                    client_secret=SPOTIPY_CLIENT_SECRET,
                                    redirect_uri=SPOTIPY_REDIRECT_URI,
                                    scope=SPOTIPY_SCOPE,
                                    cache_handler=spotipy.cache_handler.CacheFileHandler(cache_path=".spotifycache"))

        auth_url = auth_manager.get_authorize_url()
        instruction = f"""
                Чтобы зайти в свой аккаунт Spotify, выполните следующие действия:
                1. Залогинься в свой аккаунт через браузер
                2. Перейди по [ссылке]({auth_url})
                3. Скопируй все символы после «?code=» из адреса, на который тебя перенаправит ссылка
                4. Отправь скопированную строку боту
                5. Готово!!\n
                ** Пока бот может перенести только 100 песен из одного плейлиста
                """
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

    elif message.text == "Перенести в VK":
        pass


def spotify_reg_for_yandex(message):
    global spotify_code
    global sp
    global user_info
    logout()
    spotify_code = message.text
    try:
        token_info = auth_manager.get_access_token(spotify_code)
    except SpotifyOauthError:
        bot.send_message(message.chat.id,
                         f'Неверный код, попробуй снова')
        bot.register_next_step_handler(message, yandex_commands)
        return

    sp = spotipy.Spotify(auth=token_info['access_token'])

    user_info = sp.current_user()

    bot.send_message(message.chat.id, f"Hello {user_info['display_name']}!")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    bot.send_message(message.chat.id, f'Выполнен вход в твой Spotify аккаунт.\n'
                                      f'Введи ссылку на Yandexmusic плейлист, который хочешь перенести в Spotify\n'
                     ,
                     reply_markup=markup)
    bot.register_next_step_handler(message, help_y_t_sp)


def help_y_t_sp(message):
    global transfer_link
    transfer_link = message.text.split()[0]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    bot.send_message(message.chat.id, f'Выбери название, которое хочешь  дать новому плейлисту.\n '
                     ,
                     reply_markup=markup)
    bot.register_next_step_handler(message, yandex_to_spotify)


def yandex_copy(message):
    yandex_link = message.text.split()[0]
    name = message.text[len(yandex_link):]
    list_to_yandex(name, yandex_to_list(yandex_link, yandex_token, message), yandex_token)
    bot.send_message(message.chat.id,
                     f'Добавили выбранный плейлист в вашу коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n')


def yandex_to_spotify(message):
    global spotify_code
    global sp
    global user_info
    global transfer_link
    name = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    bot.send_message(message.chat.id, f'Начали переносить плейлист\n'

                     ,
                     reply_markup=markup)
    transfer_list = yandex_to_list(transfer_link, yandex_token, message)
    if transfer_list is None:
        bot.register_next_step_handler(message, yandex_commands)
        return
    search_create_add(transfer_list, name)
    bot.send_message(message.chat.id,
                     f'Добавили выбранный плейлист в вашу коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n')


def yandex_list(message):
    link = message.text
    file = ''
    for song in yandex_to_list(link, yandex_token, message):
        if len(file + song + '\n') > 1024:
            bot.send_message(message.chat.id, file)
            file = song + '\n'
        else:
            file += song + '\n'
    bot.send_message(message.chat.id, file)
    bot.send_message(message.chat.id,
                     f'Если ты хочешь сделать еще что-то, то нажми команду /start \n')


def vk_on_click(message):
    if message.text == "Скопировать VK плейлист":
        pass
    elif message.text == "Получить список песен":
        pass
    elif message.text == "Перенести в Spotify":
        pass
    elif message.text == "Перенести в Yandex":
        pass


def get_playlist(playlist_id, user_id, client):  # вспомогательная функция
    playlist = client.users_playlists(playlist_id, user_id)
    tracks = []
    for track in playlist.tracks:
        track_name = ''
        for i, artist in enumerate(track.track.artists):
            if i != 0:
                track_name += ', '
            track_name += artist.name
        track_name += ' - '
        track_name += track.track.title
        tracks.append(track_name)
    return tracks


def get_album(album_id, client):  # вспомогательная функция
    album = client.albums_with_tracks(album_id)
    tracks = []
    for volume in album.volumes:
        for track in volume:
            track_name = ''
            for i, artist in enumerate(track.artists):
                if i != 0:
                    track_name += ', '
                track_name += artist.name
            track_name += ' - '
            track_name += track.title
            tracks.append(track_name)
    return tracks


def yandex_to_list(link: str, token, message):  # по ссылке на яндекс музыку возвращает лист песен
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
                    return get_playlist(playlist_id, user_id, client)
                elif link[i] == 'a':
                    i += 6
                    album_id = link[i:]
                    return get_album(album_id, client)
            i += 1
        raise ValueError
    except ValueError:
        bot.send_message(message.chat.id,
                         f'Ты ввел неверную ссылку, попробуйт снова.\n'
                         f'Нажми на кнопку "Перенести в spotify и повтори процедуру еще раз')

    except:
        bot.send_message(message.chat.id,
                         f'Нет прав для просмотра, попробуй залогиниться снова.\n'
                         f'Нажми на кнопку "Перенести в spotify и повтори процедуру еще раз')
        bot.register_next_step_handler(message, main)


def list_to_yandex(name: str, tracks: list, token):
    client = Client(token).init()
    playlist = client.users_playlists_create(name, visibility='private', user_id=token)
    j = 1
    not_added = []
    for track in tracks:
        try:
            best_search = client.search(track).best
            name = ''
            for i, artist in enumerate(best_search.result.artists):
                if i != 0:
                    name += ', '
                name += artist.name
            name += ' - '
            name += best_search.result.title
            if track == name:
                client.users_playlists_insert_track(playlist.kind, best_search.result.id,
                                                    best_search.result.albums[0].id, revision=j)
                j += 1
            else:
                not_added.append(f'{track}  лучшее совпадение в поиске: {name}')
        except:
            not_added.append(track + '  невозможно найти трек')
    return not_added


def yandex_to_yandex(name, link, token, message):  # копирует существующий альбом/плейлист к вам в коллекции
    list_to_yandex(name, yandex_to_list(link, token, message), token)
    bot.send_message(message.chat.id,
                     f'Добавили выбранный плейлист в вашу коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n')


### Все для вк
def auth_handler():
    """Для двухфакторной авторизации"""
    key = input("Введите код аутентификации: ")
    return key, True


def vk_reg(message):
    global vk_login
    global vk_password
    global vk_session
    vk_login, vk_password = message.text.split()
    bot.send_message(message.chat.id,
                     f'Введи код, присланный на номер телефона или отправь прочерк(-), если двухфакторка не подключена')
    bot.register_next_step_handler(message, vk_code)
    vk_session = vk_api.VkApi(vk_login, vk_password, auth_handler=auth_handler, app_id=2685278)
    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        print(error_msg)
        return


#
#
def vk_code(message):
    global vk_login
    global vk_password
    global vk_session
    code = message.text
    vk_session = vk_api.VkApi(vk_login, vk_password, auth_handler=(code, True), app_id=2685278)
    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        print(error_msg)
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    item_2 = types.KeyboardButton("Получить список плейлистов")
    item_3 = types.KeyboardButton("Перенести в Spotify")
    item_4 = types.KeyboardButton("Перенести в Yandex")
    markup.add(item_2, item_3, item_4)
    bot.send_message(message.chat.id, f'Выполнен вход в твой VK аккаунт. Что ты хочешь сделать?',
                     reply_markup=markup)
    bot.register_next_step_handler(message, vk_commands)


def vk_commands(message):
    if message.text == "Получить список песен":
        all_pl = []
        for i in get_all_albums(vk_session):
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
                         f'Введи название Vk плейлиста, список песен для которого ты хочешь получить')
        bot.register_next_step_handler(message, vk_list)
    elif message.text == "Перенести в Spotify":
        global auth_manager
        auth_manager = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                    client_secret=SPOTIPY_CLIENT_SECRET,
                                    redirect_uri=SPOTIPY_REDIRECT_URI,
                                    scope=SPOTIPY_SCOPE,
                                    cache_handler=spotipy.cache_handler.CacheFileHandler(cache_path=".spotifycache"))

        auth_url = auth_manager.get_authorize_url()
        instruction = f"""
                        Чтобы зайти в свой аккаунт Spotify, выполните следующие действия:
                        1. Залогинься в свой аккаунт через браузер
                        2. Перейди по [ссылке]({auth_url})
                        3. Скопируй все символы после «?code=» из адреса, на который тебя перенаправит ссылка
                        4. Отправь скопированную строку боту
                        5. Готово!!\n
                        ** Пока бот может перенести только 100 песен из одного плейлиста
                        """
        bot.send_message(message.chat.id, instruction, parse_mode='Markdown')
        bot.register_next_step_handler(message, spotify_reg_for_vk)
    elif message.text == "Перенести в Yandex":
        reg_link = 'https://chromewebstore.google.com/detail/yandex-music-token/lcbjeookjibfhjjopieifgjnhlegmkib'
        instruction = f"""
                               Чтобы зайти в свой аккаунт Yandex Music, выполни следующие действия:
                               1. Установи расширение в Google Chrome по  [ссылке] ({reg_link})
                               2. Залогинься в свой аккаунт Яндекса через расширение
                               3. Оно автоматически направит в заблокированного бота, просто закрой его
                               4. Нажми на иконку расширения в браузере, снизу слева у появившегося окна есть кнопка "Скопировать токен"
                               5. Ответным сообщением отправь токен"""

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        item1 = types.KeyboardButton("В главное меню")
        markup.add(item1)
        bot.send_message(message.chat.id, instruction, parse_mode='Markdown', reply_markup=markup)

        bot.register_next_step_handler(message, yandex_reg_for_vk)


#
def spotify_reg_for_vk(message):
    global spotify_code
    global sp
    global user_info
    logout()
    spotify_code = message.text
    try:
        token_info = auth_manager.get_access_token(spotify_code)
    except SpotifyOauthError:
        bot.send_message(message.chat.id,
                         f'Неверный код, попробуй снова')
        bot.register_next_step_handler(message, yandex_commands)
        return

    sp = spotipy.Spotify(auth=token_info['access_token'])

    user_info = sp.current_user()

    bot.send_message(message.chat.id, f"Hello {user_info['display_name']}!")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    bot.send_message(message.chat.id, f'Выполнен вход в твой Spotify аккаунт.\n'
                                      f'Введи название плейлиста, который хочешь перенести в Spotify\n'
                     ,
                     reply_markup=markup)
    bot.register_next_step_handler(message, vk_to_spotify)


def yandex_reg_for_vk(message):
    global yandex_token
    if message.text == "В главное меню":
        bot.register_next_step_handler(message, hello_message)

        return
    yandex_token = message.text
    try:
        Client(yandex_token).init()
    except UnauthorizedError:
        bot.send_message(message.chat.id,
                         f'Неверный код, попробуй снова')
        bot.register_next_step_handler(message, spotify_commands)
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    bot.send_message(message.chat.id, f'Выполнен вход в твой Yandex аккаунт.\n '
                                      f'Ответным сообщением введи название плейлиста из VK, который хочешь перенести в Yandex',
                     reply_markup=markup)
    bot.register_next_step_handler(message, vk_to_yandex)


def vk_list(message):
    global vk_session
    name = message.text
    file = ''
    songs = get_album_by_name(message, vk_session, name)
    if songs:
        for song in songs:
            if len(file + song + '\n') > 1024:
                bot.send_message(message.chat.id, file)
                file = song + '\n'
            else:
                file += song + '\n'
    bot.send_message(message.chat.id, file)


def vk_to_spotify(message):
    global spotify_code
    global sp
    global user_info
    global transfer_link
    name = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    bot.send_message(message.chat.id, f'Начали переносить плейлист\n'

                     ,
                     reply_markup=markup)
    transfer_list = get_album_by_name(message, vk_session, name)
    if transfer_list is None:
        bot.register_next_step_handler(message, vk_commands)
        return
    search_create_add(transfer_list, name)
    bot.send_message(message.chat.id,
                     f'Добавили выбранный плейлист в вашу коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n')


def vk_to_yandex(message):
    name = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    bot.send_message(message.chat.id, f'Начали переносить плейлист\n'

                     ,
                     reply_markup=markup)
    items_to_yandex = get_album_by_name(message, vk_session, name)
    not_available = list_to_yandex(name, items_to_yandex, yandex_token)
    file = ''
    if len(not_available) != 0:
        for song in not_available:
            if len(file + song + '\n') > 1024:
                bot.send_message(message.chat.id,
                                 f'Добавили выбранный плейлист в твою коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n'
                                 f'Некоторые песни не удалось добавить((\n{file}')
                file = song + '\n'
            else:
                file += song + '\n'

        bot.send_message(message.chat.id,
                         f'Добавили выбранный плейлист в твою коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n'
                         f'Некоторые песни не удалось добавить((\n{file}')
    else:

        bot.send_message(message.chat.id,
                         f'Добавили выбранный плейлист в твою коллекцию! Если ты хочешь сделать еще что-то, то нажми команду /start \n')


#
#
def captcha_handler(captcha):
    """ При возникновении капчи вызывается эта функция и ей передается объект
        капчи. Через метод get_url можно получить ссылку на изображение.
        Через метод try_again можно попытаться отправить запрос с кодом капчи
    """

    key = input("Enter captcha code {0}: ".format(captcha.get_url())).strip()

    return captcha.try_again(key)


#
# # def getsongs(session):
# #     """Выводит все песни человека"""
# #     vkaudiofortracks = VkAudio(session)
# #     for track in vkaudiofortracks.get_iter():
# #         artist = track['artist']
# #         title = track['title']
# #
# #         print(f"Название: {title}, \t Исполнитель: {artist}")
#
#
def get_all_albums(session):
    vk_audio_instance = VkAudio(session)
    user_id = session.get_api().users.get()[0]['id']

    albums = vk_audio_instance.get_albums(user_id)
    return albums


def get_album_by_name(message, session, album_name):
    """Выводит альбомы и плейлисты по названию"""
    vk_audio_for_albums = VkAudio(session)
    user_id = session.get_api().users.get()[0]['id']
    albums = vk_audio_for_albums.get_albums(user_id)

    for album in albums:
        if album['title'].lower() == album_name.lower():
            if album:
                try:
                    return get_songs_from_album(album, session)
                except vk_api.exceptions.AccessDenied:
                    bot.send_message(message.chat.id, "Это не твой созданный плейлист, ты обманул")
                    return
            else:
                bot.send_message(message.chat.id, "Альбом/Плейлист с таким названием не найден.")



def get_songs_from_album(album, session):
    """Выводит все песни из плейлиста или альбома(пока только который создал сам человек)"""
    vkaudioforalbums = VkAudio(session)
    songs = []
    for track in vkaudioforalbums.get_iter(owner_id=album['owner_id'], album_id=album['id']):
        artist = track['artist']
        title = track['title']
        songs.append(f"{artist} - {title}")
    return songs


bot.polling(none_stop=True)
