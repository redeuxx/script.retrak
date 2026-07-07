# -*- coding: utf-8 -*-
#
import logging
import os
import time
from json import dumps, loads
from typing import Any, Dict, List, Optional, Union
from resources.lib import deviceAuthDialog
from resources.lib.kodiUtilities import (
    checkAndConfigureProxy,
    getSetting,
    getSettingAsInt,
    getString,
    notification,
    setSetting,
)
from resources.lib.utilities import (
    findEpisodeMatchInList,
    findMovieMatchInList,
    findSeasonMatchInList,
    findShowMatchInList,
)
from resources.lib.obfuscation import deobfuscate
from trakt import Trakt
from trakt.objects import Movie, Show

# read settings
__addon__ = xbmcaddon.Addon("script.retrak")
__addonversion__ = __addon__.getAddonInfo("version")

logger = logging.getLogger(__name__)


class traktAPI(object):
    # Placeholders for build-time injection
    __client_id: Union[List[int], str] = [33, 118, 118, 119, 118, 122, 114, 112, 122, 38, 33, 38, 122, 36, 113, 115, 39, 123, 32, 39, 39, 119, 119, 113, 115, 122, 119, 116, 112, 39, 116, 39, 119, 38, 39, 32, 122, 119, 112, 118, 36, 119, 33, 35, 113, 39, 117, 117, 39, 115, 116, 117, 36, 38, 113, 32, 115, 33, 123, 33, 39, 113, 122, 114]
    __client_secret: Union[List[int], str] = [38, 118, 119, 113, 32, 33, 114, 117, 32, 33, 36, 118, 112, 36, 117, 112, 39, 113, 123, 115, 119, 117, 115, 119, 35, 119, 112, 117, 119, 38, 123, 123, 38, 39, 122, 113, 122, 115, 36, 36, 114, 114, 117, 33, 122, 118, 38, 112, 114, 39, 122, 123, 39, 38, 115, 114, 117, 114, 113, 115, 114, 33, 122, 123]
    authorization: Optional[Dict] = None
    authDialog: Optional[deviceAuthDialog.DeviceAuthDialog] = None

    def __init__(self, force: bool = False) -> None:
        logger.debug("Initializing ReTrak API.")

        proxyURL = checkAndConfigureProxy()
        if proxyURL:
            Trakt.http.proxies = {"http": proxyURL, "https": proxyURL}

        # Configure URL
        retrak_url = getSetting("retrak_url")
        if not retrak_url:
            retrak_url = "https://retrak.tv"
        retrak_url = retrak_url.strip().rstrip("/")
        if not retrak_url.endswith("/api"):
            retrak_url += "/api"

        # Override Base URL for trakt.py
        import trakt.core
        trakt.core.BASE_URL = retrak_url + "/"
        logger.debug("Setting ReTrak Base URL: %s" % trakt.core.BASE_URL)

        # Configure Client Credentials
        client_id = os.environ.get("RETRAK_CLIENT_ID")
        client_secret = os.environ.get("RETRAK_CLIENT_SECRET")

        if not client_id or not client_secret:
            client_id = deobfuscate(self.__client_id)
            client_secret = deobfuscate(self.__client_secret)

        Trakt.configuration.defaults.client(
            id=client_id,
            secret=client_secret,
        )

        user_agent = "Kodi script.retrak/%s" % __addonversion__
        if getattr(Trakt.http, "headers", None) is None:
            Trakt.http.headers = {}

        Trakt.http.headers["User-Agent"] = user_agent
        Trakt.http.headers["retrak-api-version"] = "2"
        Trakt.http.headers["retrak-api-key"] = client_id

        # Bind event
        Trakt.on("oauth.token_refreshed", self.on_token_refreshed)

        # Load ReTrak API key and construct authorization token
        retrak_api_key = getSetting("retrak_api_key")
        if retrak_api_key:
            self.authorization = {
                "access_token": retrak_api_key,
                "token_type": "bearer",
                "refresh_token": "",
                "expires_in": 315360000,
                "scope": "public",
                "created_at": int(time.time())
            }
            setSetting("authorization", dumps(self.authorization))
        else:
            self.authorization = None
            setSetting("authorization", "")
            last_reminder = getSettingAsInt("last_reminder")
            now = int(time.time())
            if last_reminder >= 0 and last_reminder < now - (24 * 60 * 60) or force:
                self.login()

    def login(self) -> None:
        logger.debug("ReTrak API Key not configured.")
        notification("ReTrak", "Please enter your ReTrak API Key in settings.", 6000)

    def on_aborted(self) -> None:
        pass

    def on_authenticated(self, token: Dict) -> None:
        pass

    def on_expired(self) -> None:
        pass

    def on_poll(self, callback: Any) -> None:
        pass

    def on_token_refreshed(self, response: Dict) -> None:
        pass

    def updateUser(self) -> None:
        user = self.getUser()
        if user and "user" in user:
            setSetting("user", user["user"]["username"])
        else:
            setSetting("user", "")

    def scrobbleEpisode(self, show: Dict, episode: Dict, percent: float, status: str) -> Optional[Dict]:
        result = None

        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True):
                if status == "start":
                    result = Trakt["scrobble"].start(
                        show=show, episode=episode, progress=percent
                    )
                elif status == "pause":
                    result = Trakt["scrobble"].pause(
                        show=show, episode=episode, progress=percent
                    )
                elif status == "stop":
                    result = Trakt["scrobble"].stop(
                        show=show, episode=episode, progress=percent
                    )
                else:
                    logger.debug("scrobble() Bad scrobble status")
        return result

    def scrobbleMovie(self, movie: Dict, percent: float, status: str) -> Optional[Dict]:
        result = None

        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True):
                if status == "start":
                    result = Trakt["scrobble"].start(movie=movie, progress=percent)
                elif status == "pause":
                    result = Trakt["scrobble"].pause(movie=movie, progress=percent)
                elif status == "stop":
                    result = Trakt["scrobble"].stop(movie=movie, progress=percent)
                else:
                    logger.debug("scrobble() Bad scrobble status")
        return result

    def getShowsCollected(self, shows: Dict) -> Dict:
        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True, timeout=90):
                Trakt["sync/collection"].shows(shows, exceptions=True)
        return shows

    def getMoviesCollected(self, movies: Dict) -> Dict:
        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True, timeout=90):
                Trakt["sync/collection"].movies(movies, exceptions=True)
        return movies

    def getShowsWatched(self, shows: Dict) -> Dict:
        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True, timeout=90):
                Trakt["sync/watched"].shows(shows, exceptions=True)
        return shows

    def getMoviesWatched(self, movies: Dict) -> Dict:
        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True, timeout=90):
                Trakt["sync/watched"].movies(movies, exceptions=True)
        return movies

    def getShowsRated(self, shows: Dict) -> Dict:
        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True, timeout=90):
                Trakt["sync/ratings"].shows(store=shows, exceptions=True)
        return shows

    def getEpisodesRated(self, shows: Dict) -> Dict:
        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True, timeout=90):
                Trakt["sync/ratings"].episodes(store=shows, exceptions=True)
        return shows

    def getMoviesRated(self, movies: Dict) -> Dict:
        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True, timeout=90):
                Trakt["sync/ratings"].movies(store=movies, exceptions=True)
        return movies

    def addToCollection(self, mediaObject: Dict) -> Optional[Dict]:
        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True):
                result = Trakt["sync/collection"].add(mediaObject)
        return result

    def removeFromCollection(self, mediaObject: Dict) -> Optional[Dict]:
        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True):
                result = Trakt["sync/collection"].remove(mediaObject)
        return result

    def addToHistory(self, mediaObject: Dict) -> Optional[Dict]:
        with Trakt.configuration.oauth.from_response(self.authorization):
            # don't try this call it may cause multiple watches
            result = Trakt["sync/history"].add(mediaObject)
        return result

    def addToWatchlist(self, mediaObject: Dict) -> Optional[Dict]:
        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True):
                result = Trakt["sync/watchlist"].add(mediaObject)
        return result

    def getShowRatingForUser(self, showId: str, idType: str = "tvdb") -> Dict:
        ratings = {}
        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True):
                Trakt["sync/ratings"].shows(store=ratings)
        return findShowMatchInList(showId, ratings, idType)

    def getSeasonRatingForUser(self, showId: str, season: int, idType: str = "tvdb") -> Dict:
        ratings = {}
        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True):
                Trakt["sync/ratings"].seasons(store=ratings)
        return findSeasonMatchInList(showId, season, ratings, idType)

    def getEpisodeRatingForUser(self, showId: str, season: int, episode: int, idType: str = "tvdb") -> Dict:
        ratings = {}
        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True):
                Trakt["sync/ratings"].episodes(store=ratings)
        return findEpisodeMatchInList(showId, season, episode, ratings, idType)

    def getMovieRatingForUser(self, movieId: str, idType: str = "imdb") -> Dict:
        ratings = {}
        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True):
                Trakt["sync/ratings"].movies(store=ratings)
        return findMovieMatchInList(movieId, ratings, idType)

    # Send a rating to Trakt as mediaObject so we can add the rating
    def addRating(self, mediaObject: Dict) -> Optional[Dict]:
        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True):
                result = Trakt["sync/ratings"].add(mediaObject)
        return result

    # Send a rating to Trakt as mediaObject so we can remove the rating
    def removeRating(self, mediaObject: Dict) -> Optional[Dict]:
        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True):
                result = Trakt["sync/ratings"].remove(mediaObject)
        return result

    def getMoviePlaybackProgress(self) -> List["Movie"]:
        progressMovies = []

        # Fetch playback
        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True):
                playback = Trakt["sync/playback"].movies(exceptions=True)

                for _, item in list(playback.items()):
                    if type(item) is Movie:
                        progressMovies.append(item)

        return progressMovies

    def getEpisodePlaybackProgress(self) -> List["Show"]:
        progressEpisodes = []

        # Fetch playback
        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True):
                playback = Trakt["sync/playback"].episodes(exceptions=True)

                for _, item in list(playback.items()):
                    if type(item) is Show:
                        progressEpisodes.append(item)

        return progressEpisodes

    def getMovieSummary(self, movieId: str, extended: Optional[str] = None) -> "Movie":
        with Trakt.configuration.http(retry=True):
            return Trakt["movies"].get(movieId, extended=extended)

    def getShowSummary(self, showId: str) -> "Show":
        with Trakt.configuration.http(retry=True):
            return Trakt["shows"].get(showId)

    def getShowWithAllEpisodesList(self, showId: str) -> List:
        with Trakt.configuration.http(retry=True, timeout=90):
            return Trakt["shows"].seasons(showId, extended="episodes")

    def getEpisodeSummary(self, showId: str, season: int, episode: int, extended: Optional[str] = None) -> Any:
        with Trakt.configuration.http(retry=True):
            return Trakt["shows"].episode(showId, season, episode, extended=extended)

    def getIdLookup(self, id: str, id_type: str) -> Optional[List]:
        with Trakt.configuration.http(retry=True):
            result = Trakt["search"].lookup(id, id_type)
            if result and not isinstance(result, list):
                result = [result]
            return result

    def getTextQuery(self, query: str, type: str, year: Optional[int]) -> Optional[List]:
        with Trakt.configuration.http(retry=True, timeout=90):
            result = Trakt["search"].query(query, type, year)
            if result and not isinstance(result, list):
                result = [result]
            return result

    def getUser(self) -> Optional[Dict]:
        with Trakt.configuration.oauth.from_response(self.authorization):
            with Trakt.configuration.http(retry=True):
                result = Trakt["users/settings"].get()
                return result
