import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyOauthError
import os

SPOTIPY_CLIENT_ID = None
SPOTIPY_CLIENT_SECRET = None
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:8080'
SPOTIPY_SCOPE = 'playlist-read-collaborative playlist-read-private playlist-modify-public playlist-modify-private'

def login_inst():
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
    return auth_manager, instruction


def logout():
    try:
        os.remove(".spotifycache")
        print("Successfully logged out.")
    except FileNotFoundError:
        print("No cache file found. Already logged out.")

def get_playlists(playlist_name, sp):
    """Получает доступ ко всем песням из плейлиста в медиатеке пользователя по его названию"""
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


def parser(link: str):
    """Вспомогательная функция для парсинга ссылки

    Данная функция извлекает уникальный id номер плейлиста для дальнейшего его поиска в медиатеке пользователя."""
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


def get_playlist_by_url(pl_id, sp):
    """

    :param pl_id: уникальный айди плейлиста, полученный после парсинга ссылки
    :param sp: объект класса Spootify, через который и производится доступ к аккаунт юзера
    :return: все песни из плейлиста под уникальным номером pl_id
    """
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


def search_create_add(query: list, wanted_name, sp):
    """
    Функция ищет песню(а точнее ее уникальный uri код) и добавляет в плейлист с заданным названием

    :param query: список песен на добавление
    :param wanted_name: имя нового плейлиста
    :param sp:объект класса Spootify, через который и производится доступ к аккаунт юзера
    :return: новый плейлист будет добавлен в медиатеку
    """
    user_info = sp.current_user()
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
