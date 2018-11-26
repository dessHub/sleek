from os import environ
import threading

from sleek import logger
from . import Scheduler
from ..helpers.data import trending_playlist
from ..helpers.trending import get_trending_videos
from ..helpers.networking import open_page
from ..helpers.database import save_trending_songs, clear_trending


class TrendingScheduler(Scheduler):

    def __init__(self, name='Trending Scheduler', period=21600, playlist=trending_playlist,
                 connection_delay=0):
        Scheduler.__init__(self, name, period)
        self.playlist = playlist[:int(environ.get('PLAYLIST_LIST_LIMIT', 1000))]
        self.connection_delay = connection_delay

    def _worker(self, pl):
        logger.info('Crawling playlist "%s"' % pl[0])

        playlist_name = pl[0]
        playlist_url = pl[1]

        html = open_page(
            url=playlist_url,
            sleep_upper_limit=self.connection_delay,
        )

        song_data = get_trending_videos(html)
        print('Fetched song data')

        clear_trending(playlist_name)
        print('Cleared playlist')
        save_trending_songs(playlist_name, song_data)
        print('Saved trending')
        logger.info('Saved playlist "%s"' % pl[0])

    def run(self):
        """
        Run the trending crawler
        """
        threads = []
        for pl in self.playlist:
            thread = threading.Thread(target=self._worker, args=(pl, ))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
