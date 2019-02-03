import re
import urllib.request
from bs4 import BeautifulSoup


class Lyrics:
    @staticmethod
    def resolve_lyrics(artist, song_title):
        artist = artist.lower().split(',')[0]
        artist = artist.lower().split('&')[0].replace('!', 'i')
        song_title = song_title.lower().split('ft')[0]
        # remove all except alphanumeric characters from artist and song_title
        artist = re.sub('[^A-Za-z0-9]+', "", artist)
        song_title = re.sub('[^A-Za-z0-9]+', "", song_title)
        # remove starting 'the' from artist e.g. the who -> who
        if artist.startswith("the"):
            artist = artist[3:]
        url = "http://azlyrics.com/lyrics/"+artist+"/"+song_title+".html"
        print(url)

        try:
            content = urllib.request.urlopen(url).read()
            soup = BeautifulSoup(content, 'html.parser')
            lyrics = str(soup)
            # lyrics lies between up_partition and down_partition
            up_partition = '<!-- Usage of azlyrics.com content by any third-party lyrics provider is prohibited by our licensing agreement. Sorry about that. -->'
            down_partition = '<!-- MxM banner -->'
            lyrics = lyrics.split(up_partition)[1]
            lyrics = lyrics.split(down_partition)[0]
            lyrics = lyrics.replace('<br>', '').replace(
                '</br>', '').replace('</div>', '').strip()
            return lyrics
        except Exception as e:
            return str(e)

    @staticmethod
    def get_lyrics(title):
        title = title.split('(')[0]
        title = title.split('[')[0]
        [artist, track, *rest] = title.split('-') \
            if len(title.split('-')) > 1 else ['', title]
        lyrics = Lyrics.resolve_lyrics(artist, track)
        return '' if lyrics == 'HTTP Error 404: Not Found' else lyrics
