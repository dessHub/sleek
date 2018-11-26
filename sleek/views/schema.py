from flask_graphql import GraphQLView
import graphene
import requests

from sleek import app


class Track(graphene.ObjectType):
    id = graphene.String()
    thumb = graphene.String()
    title = graphene.String()
    uploader = graphene.String()
    length = graphene.String()
    time = graphene.String()
    get_url = graphene.String()
    suggest_url = graphene.String()
    stream_url= graphene.String()
    description =graphene.String()

    
class Query(graphene.ObjectType):
    tracks = graphene.List(Track, filter=graphene.String(), limit=graphene.Int())
    search =  graphene.List(Track, q=graphene.String())

    def resolve_tracks(self, info, filter, limit):
        res = requests.get(f"http://localhost:5000/api/v1/trending?type={filter}&number={limit}")
        data = res.json()
        l = []
        for d in data['results'][str(filter)]:
            t = Track(
                id=d['id'],
                length=d['suggest_url'],
                title=d['title'],
                get_url=d['get_url'],
                suggest_url=d['suggest_url'],
                stream_url=d['stream_url'],
                thumb = d['thumb']
            )
            l.append(t)
        return  l

    def resolve_search(self, info, q):
        res = requests.get(f"http://localhost:5000/api/v1/search?q={q}")
        data = res.json()
        l = []
        for d in data['results']:
            t = Track(
                id=d['id'],
                length=d['suggest_url'],
                title=d['title'],
                get_url=d['get_url'],
                suggest_url=d['suggest_url'],
                stream_url=d['stream_url']
            )
            l.append(t)
        return  l


schema = graphene.Schema(query=Query)

app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))