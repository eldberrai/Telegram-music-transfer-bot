from yandex_music import Client
from yandex_music.exceptions import UnauthorizedError


def get_playlist(playlist_id, user_id, client):
    """Получает доступ ко всем песням из плейлиста в медиатеке пользователя по id плейлиста"""

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


def get_album(album_id, client):
    """Получает доступ ко всем песням из альбома (не обязательно из медиатеки пользователя) по id альбома"""

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

def instruct():
    reg_link = 'https://chromewebstore.google.com/detail/yandex-music-token/lcbjeookjibfhjjopieifgjnhlegmkib'
    instruction = f"""
                           Чтобы зайти в свой аккаунт Yandex Music, выполни следующие действия:
                           1. Установи расширение в Google Chrome по  [ссылке] ({reg_link})
                           2. Залогинься в свой аккаунт Яндекса через расширение
                           3. Оно автоматически направит в заблокированного бота, просто закрой его
                           4. Нажми на иконку расширения в браузере, снизу слева у появившегося окна есть кнопка "Скопировать токен"
                           5. Ответным сообщением отправь токен"""
    return instruction
