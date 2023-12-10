import vk_api
from vk_api.audio import VkAudio


def auth_handler():
    """Для двухфакторной авторизации"""
    key = input("Введите код аутентификации: ")
    return key, True


def getsongs(session):
    """Выводит все песни человека"""
    vkaudiofortracks = VkAudio(session)
    for track in vkaudiofortracks.get_iter():
        artist = track['artist']
        title = track['title']

        print(f"Название: {title}, \t Исполнитель: {artist}")


def get_all_albums(session):
    vk_audio_instance = VkAudio(session)
    user_id = session.get_api().users.get()[0]['id']

    albums = vk_audio_instance.get_albums(user_id)
    for album in albums:
        print(f"Название альбома: {album['title']}")


def get_album_by_name(session, name):
    """Выводит альбомы и плейлисты по названию"""
    vk_audio_for_albums = VkAudio(session)
    user_id = session.get_api().users.get()[0]['id']
    albums = vk_audio_for_albums.get_albums(user_id)

    for album in albums:
        if album['title'].lower() == name.lower():
            return album
    return None


def get_songs_from_album(album, session):
    """Выводит все песни из плейлиста или альбома(пока только который создал сам человек)"""
    vkaudioforalbums = VkAudio(session)
    for track in vkaudioforalbums.get_iter(owner_id=album['owner_id'], album_id=album['id']):
        artist = track['artist']
        title = track['title']
        print(f"Название: {title}, \t Исполнитель: {artist}")


def main():
    login = input("Введите ваш логин (email или телефон): ")
    password = input("Введите ваш пароль: ")

    vk_session = vk_api.VkApi(login, password, auth_handler=auth_handler, app_id=2685278)
    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        print(error_msg)
        return
    # getsongs(vk_session) #выводит все песни пользователя
    # get_all_albums(vk_session) #выводит все альбомы
    """Выводит альбом по названию"""
    # album_name = input("Введите название альбома: ")
    # wanted_album = get_album_by_name(vk_session, album_name)
    #
    # if wanted_album:
    #     get_songs_from_album(wanted_album, vk_session)
    # else:
    #     print("Альбом/Плейлист с таким названием не найден.")


if __name__ == '__main__':
    main()
