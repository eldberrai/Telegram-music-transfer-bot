import os
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:8080'

SPOTIPY_SCOPE = 'playlist-read-collaborative playlist-read-private playlist-modify-public playlist-modify-private'

auth_manager = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                            client_secret=SPOTIPY_CLIENT_SECRET,
                            redirect_uri=SPOTIPY_REDIRECT_URI,
                            scope=SPOTIPY_SCOPE,
                            cache_handler=spotipy.cache_handler.CacheFileHandler(cache_path=".spotifycache"))

auth_url = auth_manager.get_authorize_url()

print(f"Please visit this URL to authorize the application: {auth_url}")

auth_code = input("Enter the authorization code: ")

token_info = auth_manager.get_access_token(auth_code)

sp = spotipy.Spotify(auth=token_info['access_token'])

user_info = sp.current_user()
print(f"Hello {user_info['display_name']}!")


def logout(): #разлогинить пользователя (обязательно нужно если хочет зайти в другой аккаунт)
    try:
        os.remove(".spotifycache")
        print("Successfully logged out.")
    except FileNotFoundError:
        print("No cache file found. Already logged out.")


def get_playlists(playlist_name): #получает список песен из плейлиста под названием, которое кинул пользователь
    needed_playlist = None
    user = sp.current_user()
    current_playlists = sp.user_playlists(user['id'])['items']

    playlist_with_items = []
    for playlist in current_playlists:
        if (playlist['name'] == playlist_name):
            needed_playlist = playlist
            break
    if not needed_playlist:
        return 'Playlist with such name not found'
    for pl in sp.playlist_items(needed_playlist['id'])['items']:
        playlist_with_items.append(
            pl['track']['album']['artists'][0]['name'] + '-' + pl['track']['name'])
    return playlist_with_items


def parser(link: str): #парсит ссылку для вывода плейлиста по ссылку
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


def get_playlist_by_url(pl_id): #выдает список песен из плейлиста по ссылке
    current_playlist = sp.playlist_items(pl_id)
    playlist_with_items = []
    for track in current_playlist['items']:
        playlist_with_items.append(track['track']['album']['artists'][0]['name'] + '-' + track['track']['name'])
    return playlist_with_items


def search_create_add(query: list, wanted_name):#ищет все песни из переданного списка, создает новый плейлист с желаемым именем и добавляет туда песни из списка
    uris = []
    needed_id = None
    for i in query:
        ur = sp.search(i)['tracks']['items'][0]['uri']
        uris.append(ur)
    sp.user_playlist_create(user_info['id'], name=wanted_name)
    for playlist in sp.current_user_playlists()['items']:
        if (playlist['name'] == wanted_name):
            needed_id = playlist['id']
    sp.playlist_add_items(playlist_id=needed_id, items=uris)

