import re
import traceback

from sleek.helpers.encryption import get_key, encode_data

from sleek.helpers.helpers import html_unescape
from .networking import open_page

INF = float("inf")
SEARCH_SUFFIX = ' (song|full song|remix|karaoke|instrumental)'

area_of_concern_regex = re.compile(r'<div .*? class=\"watch-sidebar\"(.*?)<div id="footer-container"', re.DOTALL)
videos_html_regex = re.compile(r'<li class=\"video-list-item.*?>(.*?)</li>', re.DOTALL)
single_video_regex = {
    'id': re.compile(r'v\=(.*?)\"'),
    'title': re.compile(r'title=\"(.*?)\"', re.DOTALL),
    'duration': re.compile(r'Duration: (.*?)\.', re.DOTALL),
    'uploader': re.compile(r'attribution\".<span.*?>(.*?)</span>', re.DOTALL),
    'views': re.compile(r'view-count\".(.*?)</span>', re.DOTALL)
}


def get_search_results_html(search_term):
    """
    gets search results html code for a search term
    """
    proxy_search_term = search_term + SEARCH_SUFFIX
    link = 'https://www.youtube.com/results?search_query=%s' % proxy_search_term
    link += '&sp=EgIQAQ%253D%253D'  # for only video
    link += '&gl=IN'
    raw_html = open_page(link)
    return raw_html


def get_videos(html):
    """
    separate videos in html
    """
    first = html.find('yt-lockup-tile')
    html = html[first + 2:]
    vid = []
    while True:
        pos = html.find('yt-lockup-tile')
        if pos == -1:
            pos = INF
            vid.append(html)
            break
        vid.append(html[:pos + 2])
        html = html[pos + 3:]
    return vid


def get_video_attrs(html):
    """
    get video attributes from html
    """
    result = {}
    # get video id and description
    regex = 'yt\-lockup\-title.*?href.*?watch\?v\=(.*?[^\"]+)'
    regex += '.*? title\=\"(.*?[^\"]+)'
    temp = re.findall(regex, html)
    if len(temp) and len(temp[0]) == 2:
        result['id'] = temp[0][0]
        result['title'] = html_unescape(temp[0][1])
    # length
    length_regex = 'video\-time.*?\>([^\<]+)'
    temp = re.findall(length_regex, html)
    if len(temp) > 0:
        result['length'] = temp[0].strip()
    # uploader
    upl_regex = 'yt\-lockup\-byline.*?\>.*?\>([^\<]+)'
    temp = re.findall(upl_regex, html)
    if len(temp) > 0:
        result['uploader'] = temp[0].strip()
    # time ago
    time_regex = 'yt\-lockup\-meta\-info.*?\>.*?\>([^\<]+).*?([0-9\,]+)'
    temp = re.findall(time_regex, html)
    if len(temp) and len(temp[0]) == 2:
        result['time'] = temp[0][0]
        result['views'] = temp[0][1]
    # thumbnail
    if 'id' in result:
        thumb = 'https://img.youtube.com/vi/%s/0.jpg' % result['id']
        result['thumb'] = thumb
    else:
        return None
    # Description
    desc_regex = 'yt-lockup-description.*?>(.*?)<'
    temp = re.findall(desc_regex, html)
    if len(temp) > 0:
        result['description'] = temp[0]
    else:
        result['description'] = ''

    # check if all items present. If not present, usually some problem in parsing
    if len(result) != 8:
        return None
    # return
    result['get_url'] = '/g?url=' + encode_data(
        get_key(), id=result['id'],
        title=result['title'], length=result['length']
    ).decode('utf-8')
    result['stream_url'] = result['get_url'].replace('/g?', '/stream?', 1)
    return result


def extends_length(length, limit):
    """
    Return True if length more than limit
    """
    try:
        metrics = [int(i.strip()) for i in length.split(':')]
        secs = 0
        for metric in metrics:
            secs = 60 * secs + metric
        return secs > limit
    except Exception:
        return True


def get_suggestions(vid_id, get_url_prefix='/api/v1'):
    url = "https://www.youtube.com/watch?v=" + vid_id
    raw_html = open_page(url)

    area_of_concern = ' '.join(area_of_concern_regex.findall(raw_html, re.DOTALL))

    videos_html = videos_html_regex.findall(area_of_concern, re.DOTALL)

    ret_list = []
    for video in videos_html:
        try:
            _id = single_video_regex['id'].findall(video)[0]
            if '&amp;list=' in _id:
                continue
            title = single_video_regex['title'].findall(video)[0]
            duration = single_video_regex['duration'].findall(video)[0]
            uploader = single_video_regex['uploader'].findall(video)[0]
            views = single_video_regex['views'].findall(video)[0]
            encoded_data = encode_data(get_key(), id=_id, title=title, length=duration).decode('utf-8')
            get_url = get_url_prefix + '/g?url=' + encoded_data
            stream_url = get_url.replace('/g?', '/stream?', 1)
            suggest_url = get_url.replace('/g?', '/suggest?', 1)

            ret_list.append(
                {
                    "id": _id,
                    "title": html_unescape(title),
                    "length": duration,
                    "uploader": uploader,
                    "thumb": 'https://img.youtube.com/vi/%s/0.jpg' % _id,
                    "get_url": get_url,
                    "stream_url": stream_url,
                    "views": views,
                    "suggest_url": suggest_url
                }
            )
        except Exception:
            print('Error while getting suggestion at video \n' + video)
            traceback.print_exc()

    return ret_list


def make_search_api_response(term, results, endpoint):
    """
    Returns the search API response given the above parameters
    """
    return {
        'metadata': {
            'q': term,
            'count': len(results)
        },
        'results': results,
        'status': 200,
        'requestLocation': endpoint
    }
