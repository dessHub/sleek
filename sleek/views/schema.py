from flask_graphql import GraphQLView
import graphene
import requests
from urllib.parse import urlparse, parse_qs


from sleek import app
from sleek.helpers.search import get_search_results_html, get_videos, get_video_attrs
from sleek.helpers.helpers import get_download_link_youtube
from sleek.helpers.encryption import get_key, encode_data, decode_data
from sleek.helpers.redis_utils import get_or_create_video_download_link
from sleek.helpers.lyrics import Lyrics


class Meta(graphene.ObjectType):
    q = graphene.String()
    count = graphene.Int()


class Track(graphene.ObjectType):
    id = graphene.String()
    thumb = graphene.String()
    title = graphene.String()
    uploader = graphene.String()
    length = graphene.String()
    time = graphene.String()
    get_url = graphene.String()
    suggest_url = graphene.String()
    stream_url = graphene.String()
    description = graphene.String()
    views = graphene.String()
    lyrics = graphene.String()
    track_id = graphene.String()
    # metadata = graphene.ObjectType(Meta)

class Lyric(graphene.ObjectType):
    lyrics =  graphene.String()
    track = graphene.Field(Track)

class Query(graphene.ObjectType):
    tracks = graphene.List(Track, filter=graphene.String(), limit=graphene.Int())
    search = graphene.List(Track, q=graphene.String())
    lyrics = graphene.Field(Lyric, track = graphene.String())

    def resolve_tracks(self, info, filter, limit):
        res = requests.get(f"http://localhost:5000/api/v1/trending?type={filter}&number={limit}")
        data = res.json()
        l = []
        for d in data['results'][str(filter)]:
            t = Track(
                id=d['id'],
                length=d['length'],
                title=d['title'],
                get_url=d['get_url'],
                suggest_url=d['suggest_url'],
                stream_url=d['stream_url'],
                thumb = d['thumb'],
                track_id = encode_data(get_key(), id=d['id'], title=d['title'], length=d['length']).decode("utf-8"),
            )
            l.append(t)
        return  l

    def resolve_search(self, info, q):
        raw_html = get_search_results_html(q)
        videos = get_videos(raw_html)
        return_videos = []
        for _ in videos:
            temp = get_video_attrs(_)
            if temp:
                track = Track(
                    id=temp['id'],
                    track_id = encode_data(get_key(), id=temp['id'], title=temp['title'], length=temp['length']).decode("utf-8"),
                    description = temp['description'],
                    length=temp['length'],
                    time = temp['time'],
                    thumb = temp['thumb'],
                    uploader = temp['uploader'],
                    views = temp['views'],
                    title=temp['title'],
                    get_url= '/api/v1' +  temp['get_url'],
                    stream_url='/api/v1' + temp['stream_url']
                )
                return_videos.append(track)

        return return_videos

    def resolve_lyrics(self, info, track):
        data = decode_data(get_key(), track)
        title  = data['title']

        lyrics = Lyrics.get_lyrics(title)

        return Lyric(
            lyrics=lyrics
        )


schema = graphene.Schema(query=Query)

app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))
