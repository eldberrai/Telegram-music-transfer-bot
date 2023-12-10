from yandex_music import Client


def get_playlist(playlist_id, user_id, client):
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


def yandex_to_list(link: str, client):
    try:
        i = 0
        while i < len(link):
            if link[i:i+16] == 'music.yandex.ru/':
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


def list_to_yandex(name: str, tracks: list, token):
    client = Client(token).init()
    playlist = client.users_playlists_create(name, visibility='private', user_id=token)
    i = 0
    for track in tracks:
        i += 1
        best_search = client.search(track).best
        client.users_playlists_insert_track(playlist.kind, best_search.result.id, best_search.result.albums[0].id, revision=i)


def yandex_to_yandex(name, link, token):
    client = Client(token).init()
    list_to_yandex(name, yandex_to_list(link, client), token)
