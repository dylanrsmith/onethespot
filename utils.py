import os, platform
from librespot.core import Session
import time
import re, json
from runtimedata import get_logger
import traceback
from spotutils import search_by_term
import subprocess


if platform.system() == "Windows":
    from winsdk.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager

logger = get_logger("utils")


def login_user(username: str, password: str, login_data_dir: str)->list:
    logger.info(f"logging in user '{username[:4]}****@****.***'")
    # Check the username and if pickled sessionfile exists load the session and append
    # Returns: [Success: Bool, Session: Session, PicklePath: str, premium: Bool]
    sessobj_pikpath = os.path.join(login_data_dir, username+"_GUZpotifylogin.json")
    os.makedirs(os.path.dirname(sessobj_pikpath), exist_ok=True)
    if os.path.isfile(sessobj_pikpath):
        logger.info(f"Session file exists for user, attempting to use it '{username[:4]}****@****.***'")
        logger.debug("Restoring user session")
        # Session exists try loading it
        try:
            config = Session.Configuration.Builder().set_stored_credential_file(sessobj_pikpath).build()
            logger.debug("Session config created")
            # For some reason initialising session as None prevents premature application exit
            session = None
            session = Session.Builder(conf=config).stored_file(sessobj_pikpath).create()
            logger.debug("Session created")
            premium = True if session.get_user_attribute("type") == "premium" else False
            logger.info(f"Login successful for user '{username[:4]}****@****.***'")
            return [True, session, sessobj_pikpath, premium]
        except (RuntimeError, Session.SpotifyAuthenticationException):
            logger.error(f"Failed logging in user '{username[:4]}****@****.***', invalid credentials")
            return [False, None, "", False]
        except Exception:
            logger.error(f"Failed to login user '{username[:4]}****@****.***' due to unexpected error: {traceback.format_exc()}")
            return [False, None, "", False]
    else:
        logger.info(f"Session file does not exist user '{username[:4]}****@****.***', attempting login with uname/pass")
        try:
            logger.info(f"logging in user '{username[:4]}****@****.***'")
            config = Session.Configuration.Builder().set_stored_credential_file(sessobj_pikpath).build()
            print("logging in !")
            session = Session.Builder(conf=config).user_pass(username, password).create()
            premium = True if session.get_user_attribute("type") == "premium" else False
            logger.info(f"Login successful for user '{username[:4]}****@****.***'")
            return [True, session, sessobj_pikpath, premium]
        except (RuntimeError, Session.SpotifyAuthenticationException):
            logger.error(f"Failed logging in user '{username[:4]}****@****.***', invalid credentials")
            return [False, None, "", False]
        except Exception:
            return [False, None, "", False]
            logger.error(f"Failed to login user '{username[:4]}****@****.***' due to unexpected error: {traceback.format_exc()}")
    return [False, None, "", False]

def remove_user(username: str, login_data_dir: str, config)->bool:
    logger.info(f"Removing user '{username[:4]}****@****.***' from saved entries")
    sessobj_pikpath = os.path.join(login_data_dir, username+"_GUZpotifylogin.json")
    if os.path.isfile(sessobj_pikpath):
        os.remove(sessobj_pikpath)
    removed = False
    accounts_copy = config.get("accounts").copy()
    print("AC CP", accounts_copy)
    accounts = config.get("accounts")
    print("AC", accounts_copy)
    for i in range(0, len(accounts)):
        if accounts[i][0] == username:
            accounts_copy.pop(i)
            removed = True
            break
    if removed:
        logger.info(f"Saved Account user '{username[:4]}****@****.***' found and removed")
        config.set_("accounts", accounts_copy)
        config.update()
    return removed


def regex_input_for_urls(search_input):
    logger.info(f"Parsing url '{search_input}'")
    track_uri_search = re.search(
        r"^spotify:track:(?P<TrackID>[0-9a-zA-Z]{22})$", search_input)
    track_url_search = re.search(
        r"^(https?://)?open\.spotify\.com/track/(?P<TrackID>[0-9a-zA-Z]{22})(\?si=.+?)?$",
        search_input,
    )

    album_uri_search = re.search(
        r"^spotify:album:(?P<AlbumID>[0-9a-zA-Z]{22})$", search_input)
    album_url_search = re.search(
        r"^(https?://)?open\.spotify\.com/album/(?P<AlbumID>[0-9a-zA-Z]{22})(\?si=.+?)?$",
        search_input,
    )

    playlist_uri_search = re.search(
        r"^spotify:playlist:(?P<PlaylistID>[0-9a-zA-Z]{22})$", search_input)
    playlist_url_search = re.search(
        r"^(https?://)?open\.spotify\.com/playlist/(?P<PlaylistID>[0-9a-zA-Z]{22})(\?si=.+?)?$",
        search_input,
    )

    episode_uri_search = re.search(
        r"^spotify:episode:(?P<EpisodeID>[0-9a-zA-Z]{22})$", search_input)
    episode_url_search = re.search(
        r"^(https?://)?open\.spotify\.com/episode/(?P<EpisodeID>[0-9a-zA-Z]{22})(\?si=.+?)?$",
        search_input,
    )

    show_uri_search = re.search(
        r"^spotify:show:(?P<ShowID>[0-9a-zA-Z]{22})$", search_input)
    show_url_search = re.search(
        r"^(https?://)?open\.spotify\.com/show/(?P<ShowID>[0-9a-zA-Z]{22})(\?si=.+?)?$",
        search_input,
    )

    artist_uri_search = re.search(
        r"^spotify:artist:(?P<ArtistID>[0-9a-zA-Z]{22})$", search_input)
    artist_url_search = re.search(
        r"^(https?://)?open\.spotify\.com/artist/(?P<ArtistID>[0-9a-zA-Z]{22})(\?si=.+?)?$",
        search_input,
    )

    if track_uri_search is not None or track_url_search is not None:
        track_id_str = (track_uri_search
                        if track_uri_search is not None else
                        track_url_search).group("TrackID")
    else:
        track_id_str = None

    if album_uri_search is not None or album_url_search is not None:
        album_id_str = (album_uri_search
                        if album_uri_search is not None else
                        album_url_search).group("AlbumID")
    else:
        album_id_str = None

    if playlist_uri_search is not None or playlist_url_search is not None:
        playlist_id_str = (playlist_uri_search
                           if playlist_uri_search is not None else
                           playlist_url_search).group("PlaylistID")
    else:
        playlist_id_str = None

    if episode_uri_search is not None or episode_url_search is not None:
        episode_id_str = (episode_uri_search
                          if episode_uri_search is not None else
                          episode_url_search).group("EpisodeID")
    else:
        episode_id_str = None

    if show_uri_search is not None or show_url_search is not None:
        show_id_str = (show_uri_search
                       if show_uri_search is not None else
                       show_url_search).group("ShowID")
    else:
        show_id_str = None

    if artist_uri_search is not None or artist_url_search is not None:
        artist_id_str = (artist_uri_search
                         if artist_uri_search is not None else
                         artist_url_search).group("ArtistID")
    else:
        artist_id_str = None
    return track_id_str, album_id_str, playlist_id_str, episode_id_str, show_id_str, artist_id_str

def get_url_data(url):
    track_id_str, album_id_str, playlist_id_str, episode_id_str, show_id_str, artist_id_str = regex_input_for_urls(url)
    if track_id_str is not None:
        logger.info(f"Parse result for url '{url}'-> track, {track_id_str}")
        return "track", track_id_str
    elif album_id_str is not None:
        logger.info(f"Parse result for url '{url}'-> album, {album_id_str}")
        return "album", album_id_str
    elif playlist_id_str is not None:
        logger.info(f"Parse result for url '{url}'-> playlist, {playlist_id_str}")
        return "playlist", playlist_id_str
    elif episode_id_str is not None:
        logger.info(f"Parse result for url '{url}'-> episode, {episode_id_str}")
        return "episode", episode_id_str
    elif show_id_str is not None:
        logger.info(f"Parse result for url '{url}'-> podcast, {show_id_str}")
        return "podcast", show_id_str
    elif artist_id_str is not None:
        logger.info(f"Parse result for url '{url}'-> artist, {artist_id_str}")
        return "artist", artist_id_str
    else:
        logger.error(f"Parse result for url '{url}' failed, invalid spotify url !")
        return None, None

def get_now_playing_local(session):
    if platform.system() == "Linux":
        logger.debug("Linux detected ! Use playerctl to get current track information..")
        playctl_out = subprocess.check_output(["playerctl", "-p", "spotify", "metadata"])
        found = re.search(r"((spotify xesam:url).*https:\/\/open.spotify.*\n)", playctl_out.decode())
        if found:
            spotify_url = found.group(1).replace("spotify xesam:url", "").strip()
            return spotify_url
        else:
            return ""
    elif platform.system() == "Windows":
        logger.debug("Windows detected ! Using unreliable search method to get media info")
        info_dict = None
        sessions = MediaManager.request_async()
        current_session = sessions.get_current_session()
        if current_session:
            if current_session.source_app_user_model_id == "Spotify.exe":
                info = current_session.try_get_media_properties_async()
                info_dict = {song_attr: info.__getattribute__(song_attr) for song_attr in dir(info) if song_attr[0] != '_'}
                info_dict['genres'] = list(info_dict['genres'])
        if info_dict:
            query_str = f"{info_dict['title']} {info_dict['artist']} {info_dict['album_title']}".strip()
            results = search_by_term(session, query_str, max_results=1, content_types=["track"])
            if len(results["tracks"]) > 0:
                return results["tracks"][0]["external_urls"]["spotify"]
            else:
                return ""
    else:
        logger.debug("Unsupported platform for auto download !")
        return ""