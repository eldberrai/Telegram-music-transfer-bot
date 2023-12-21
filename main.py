import telebot
from telebot import types
import threading
from yandex_music import Client
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

bot = telebot.TeleBot('TOKEN')
yandex_token = None
spotify_code = None
sp = None
user_info = None
auth_manager = None

SPOTIPY_CLIENT_ID = None
SPOTIPY_CLIENT_SECRET = None
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:8080'

SPOTIPY_SCOPE = 'playlist-read-collaborative playlist-read-private playlist-modify-public playlist-modify-private'


@bot.message_handler(commands=['start'])
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
        Чтобы зайти в свой аккаунт Yandex Music, выполните следующие действия:
        1. Установите расширение в Google Chrome по этой [ссылке]({reg_link})
        2. Залогиньтесь в свой аккаунт Яндекса через расширение
        3. Оно вас автоматически направит в заблокированного бота, просто закройте его
        4. Нажмите на иконку расширения в браузере, снизу слева у появившегося окна есть кнопка "Скопировать токен"
        5. Отправьте его ответным сообщением
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
        1. Залогиньтесь в свой аккаунт через браузер
        2. Перейдите по [ссылке]({auth_url}), которую отправит вам бот после введения команды “Spotify”
        3. Скопируйте все символы после «?code=» из адреса, на который вас перенаправит ссылка
        4. Отправьте скопированную строку боту
        5. Готово!!
        """
        bot.send_message(message.chat.id, instruction, parse_mode='Markdown')
        bot.register_next_step_handler(message, spotify_reg)

    elif message.text == 'VK':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
        item_1 = types.KeyboardButton("Скопировать VK плейлист")
        item_2 = types.KeyboardButton("Получить список песен")
        item_3 = types.KeyboardButton("Перенести в Yandex")
        item_4 = types.KeyboardButton("Перенести в Spotify")
        markup.add(item_1, item_2, item_3, item_4)
        bot.send_message(message.chat.id, f'Что ты хочешь сделать?', reply_markup=markup)
        bot.register_next_step_handler(message, vk_on_click)


def spotify_reg(message):
    global spotify_code
    global sp

    spotify_code = message.text
    token_info = auth_manager.get_access_token(spotify_code)

    sp = spotipy.Spotify(auth=token_info['access_token'])

    user_info = sp.current_user()

    bot.send_message(message.chat.id, f"Hello {user_info['display_name']}!")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    item_1 = types.KeyboardButton("Скопировать Spotify плейлист")
    item_2 = types.KeyboardButton("Получить список песен")
    item_3 = types.KeyboardButton("Перенести в VK")
    item_4 = types.KeyboardButton("Перенести в Yandex")
    markup.add(item_1, item_2, item_3, item_4)
    bot.send_message(message.chat.id, f'Выполнен вход в твой Spotify аккаунт. Что ты хочешь сделать?',
                     reply_markup=markup)
    bot.register_next_step_handler(message, spotify_commands)


def spotify_commands(message):
    if message.text == "Создать Spotify плейлист":
        bot.send_message(message.chat.id,
                         f'Введи название для своего плейлиста и список песен, которые хочешь туда добавить (каждую - с новой строки)')
        bot.register_next_step_handler(message, spotify_copy)
    elif message.text == "Получить список песен":
        bot.send_message(message.chat.id,
                         f'Введи название Spotify плейлиста, список песен для которого ты хочешь получить')
        bot.register_next_step_handler(message, spotify_list)
    elif message.text == "Перенести в Yandex":
        bot.send_message(message.chat.id,
                         f"""
                         Введи ссылку на Spotify плейлист, который хочешь перенести в Yandex, и название, которое хочешь ему дать, через пробел
                         P.S. Данная функция будет работать, если ты ранее входил в Yandex с помощью этого бота, в противном случае вернись в главное меню и выполни вход в Yandex:)
                         """)
        bot.register_next_step_handler(message, yandex_to_spotify)
    elif message.text == "Перенести в VK":
        pass


def spotify_list(message):
    playlist = message.text
    file = ''
    for song in get_playlists(playlist):
        if len(file + song + '\n') > 1024:
            bot.send_message(message.chat.id, file)
            file = song + '\n'
        else:
            file += song + '\n'
    bot.send_message(message.chat.id, file)


def spotify_to_yandex(message):
    spotify_link = message.text.split()[0]
    name = message.text[len(spotify_link):]
    transfer_list = yandex_to_list(spotify_link, yandex_token)
    list_to_yandex(name, transfer_list, yandex_token)
    bot.send_message(message.chat.id, f'Добавили выбранный плейлист в твою коллекцию!')


def spotify_copy(message):
    user_input = message.text.split('\n')
    name = user_input[0]
    tracks = user_input[1:]
    search_create_add(tracks, name)


def yandex_reg(message):
    global yandex_token
    yandex_token = message.text
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
        bot.send_message(message.chat.id,
                         f"""
                         Введи ссылку на Yandex плейлист, который хочешь перенести в Spotify, и название, которое хочешь ему дать, через пробел
                         P.S. Данная функция будет работать, если ты ранее входил в Spotify с помощью этого бота, в противном случае вернись в главное меню и выполни вход в Spotify:)
                         """)
        bot.register_next_step_handler(message, yandex_to_spotify)
    elif message.text == "Перенести в VK":
        pass


def yandex_copy(message):
    yandex_link = message.text.split()[0]
    name = message.text[len(yandex_link):]
    list_to_yandex(name, yandex_to_list(yandex_link, yandex_token), yandex_token)
    bot.send_message(message.chat.id, f'Добавили выбранный плейлист в твою коллекцию!')


def yandex_to_spotify(message):
    yandex_link = message.text.split()[0]
    name = message.text[len(yandex_link):]
    transfer_list = yandex_to_list(yandex_link, yandex_token)
    search_create_add(transfer_list, name)
    bot.send_message(message.chat.id, f'Добавили выбранный плейлист в твою коллекцию!')


def yandex_list(message):
    link = message.text
    file = ''
    for song in yandex_to_list(link, yandex_token):
        if len(file + song + '\n') > 1024:
            bot.send_message(message.chat.id, file)
            file = song + '\n'
        else:
            file += song + '\n'
    bot.send_message(message.chat.id, file)


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


def yandex_to_list(link: str, token):  # по ссылке на яндекс музыку возвращает лист песен
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
        raise ValueError('Incorrect link')
    except:
        raise ValueError('Probably, not enough rights, please try logging in your account')


def list_to_yandex(name: str, tracks: list, token):  # по листу создает плейлист и добавляет в коллекции
    client = Client(token).init()
    playlist = client.users_playlists_create(name, visibility='private', user_id=token)
    i = 0
    for track in tracks:
        i += 1
        best_search = client.search(track).best
        client.users_playlists_insert_track(playlist.kind, best_search.result.id, best_search.result.albums[0].id,
                                            revision=i)


def yandex_to_yandex(name, link, token):  # копирует существующий альбом/плейлист к вам в коллекции
    list_to_yandex(name, yandex_to_list(link, token), token)


def logout():
    try:
        os.remove(".spotifycache")
        print("Successfully logged out.")
    except FileNotFoundError:
        print("No cache file found. Already logged out.")


def get_playlists(playlist_name):
    needed_playlist = None
    user = sp.current_user()
    current_playlists = sp.user_playlists(user['id'])['items']

    playlist_with_items = []
    for playlist in current_playlists:
        if (playlist['name'] == playlist_name):
            needed_playlist = playlist
            break
    for pl in sp.playlist_items(needed_playlist['id'])['items']:
        playlist_with_items.append(
            pl['track']['album']['artists'][0]['name'] + '-' + pl['track']['name'])
    return playlist_with_items


def parser(link: str):
    i = 0
    playlist_id = ''
    while i < len(link):
        if link[i:i + 17] == 'open.spotify.com/':
            i += 17
            if link[i] == 'p':
                i += 9
                while i < len(link) and link[i] != '/':
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
    for track in current_playlist['items']:
        playlist_with_items.append(track['track']['album']['artists'][0]['name'] + '-' + track['track']['name'])
    return playlist_with_items


def search_create_add(query: list):
    uris = []
    needed_id = None
    for i in query:
        ur = sp.search(i)['tracks']['items'][0]['uri']
        uris.append(ur)
    print(uris)
    sp.user_playlist_create(user_info['id'], name='New_try')
    for playlist in sp.current_user_playlists()['items']:
        if (playlist['name'] == 'New_try'):
            needed_id = playlist['id']
    sp.playlist_add_items(playlist_id=needed_id, items=uris)


bot.polling(none_stop=True)
