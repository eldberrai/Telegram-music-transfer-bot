import vk_api
from vk_api.audio import VkAudio
import waiting



def get_all_albums(session):
    """Выводит все плейлисты пользователя"""
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
                    return vk_api.exceptions.AccessDenied


def get_songs_from_album(album, session):
    """Выводит все песни из плейлиста или альбома(пока только который создал сам человек)"""
    vkaudioforalbums = VkAudio(session)
    songs = []
    for track in vkaudioforalbums.get_iter(owner_id=album['owner_id'], album_id=album['id']):
        artist = track['artist']
        title = track['title']
        songs.append(f"{artist} - {title}")
    return songs

def captcha_handler(captcha):
    """ При возникновении капчи вызывается эта функция и ей передается объект
        капчи. Через метод get_url можно получить ссылку на изображение.
        Через метод try_again можно попытаться отправить запрос с кодом капчи
    """

    key = input("Enter captcha code {0}: ".format(captcha.get_url())).strip()

    return captcha.try_again(key)

