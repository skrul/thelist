import pprint
import eml_parser
from datetime import datetime
from datetime import timedelta
import spotipy
import spotipy.util as util

from message_parser import MessageParser
from show_parser import ShowParser
from stats import Stats
from band import Band

PLAYLIST_URI = 'spotify:user:skrul:playlist:4H3c7TmhhUOFskcgfi5UkB'
BOTH_URI = 'spotify:user:skrul:playlist:04vyWyZidXEpKLmgQ8NaXl'
THEE_PARKSIDE_URI = 'spotify:user:skrul:playlist:5WWCYjGqZ7OAHXtEHSJLCt'
RICKSHAW_STOP_URI = 'spotify:user:skrul:playlist:2PeSBTcScRdCgRmI580glf'

TOKEN = util.prompt_for_user_token('skrul', 'playlist-modify-public',
                                   'ca917724c4c34f9e8f810372813b71a8',
                                   '29e3b125904145da9006893669126cc2',
                                   'http://skrul.com/')


class SpotifyArtist:
    def __init__(self, name, uri, popularity):
        self.name = name
        self.uri = uri
        self.popularity = popularity

    def __str__(self):
        return str({
            'name': self.name,
            'uri': self.uri,
            'popularity': self.popularity
        })


class Filter:
    def __init__(self):
        self.min_spotify_popularity = None
        self.city = None
        self.venue = None
        self.price_leq = None
        self.up_to_days = None
        self.next_week = None

    def accept_show(self, message, show):
        if self.city is not None and show.city not in self.city:
            return False
        if self.venue is not None and show.venue != self.venue:
            return False
        if self.price_leq is not None and show.price is not None and not show.price.leq(
                self.price_leq):
            return False
        if self.up_to_days is not None and show.is_after(
                message.start_date.date() + timedelta(days=self.up_to_days)):
            return False
        if self.next_week:
            year, week_number, _ = (message.start_date + timedelta(days=7)).isocalendar()
            start_date = datetime.strptime(f"{year}-{week_number - 1}-2", '%Y-%W-%w').date()
            end_date = start_date + timedelta(days=9)
            return show.is_after(start_date) and show.is_before(end_date)
        return True

    def accept_artist(self, artist):
        if self.min_spotify_popularity is not None and artist.popularity < self.min_spotify_popularity:
            return False
        return True

    def get_description(self):
        a = []
        if self.city is not None:
            a.append(f'city is {self.city}')
        if self.venue is not None:
            a.append(f'venue is {self.venue}')
        if self.price_leq is not None:
            a.append(f'price <= ${self.price_leq}')
        if self.up_to_days is not None:
            a.append(f'up to {self.up_to_days} days away')
        if self.next_week is not None:
            a.append('next week (wed to wed)')
        if self.min_spotify_popularity is not None:
            a.append(
                f'minimum Spotify popularity of {self.min_spotify_popularity}')
        return ', '.join(a)


def search(sp, band):
    def sa(b, i):
        return SpotifyArtist(b, i['uri'], i['popularity'])

    results = sp.search(q=f'"{band.name}"', type='artist')
    #results = sp.search(q=f'"{band.name}"')
    #pprint.pprint(results)
    items = results['artists']['items']
    num_results = len(items)
    if num_results == 0:
        return None

    if num_results == 1:
        return sa(band, items[0])

    names = []
    for item in items:
        names.append(item['name'])
        if item['name'].lower() == band.name.lower():
            return sa(band, item)
    print('String match not found: "' + band.name + '" "' + '", "'.join(names) + '"')
    return None

def top_tracks(sp, uri):
    results = sp.artist_top_tracks(uri)
    #pprint.pprint(results)
    uris = []
    for track in results['tracks'][:1]:
        uris.append(track['uri'])
    return uris


def get_tracks(sp, playlist_id):
    items = []
    results = sp.user_playlist('skrul',
                               playlist_id=playlist_id,
                               fields='tracks,next')
    tracks = results['tracks']
    items = tracks['items']
    while tracks['next']:
        tracks = sp.next(tracks)
        items.extend(tracks['items'])

    track_uris = []
    for track in items:
        track_uris.append(track['track']['uri'])
    return track_uris


def clear_playlist(sp, playlist_uri):
    track_uris = get_tracks(sp, playlist_uri)
    for chunk in chunker(track_uris, 50):
        sp.user_playlist_remove_all_occurrences_of_tracks(
            'skrul', playlist_uri, chunk)


def add_tracks(sp, playlist_uri, track_uris):
    for chunk in chunker(track_uris, 50):
        print(chunk)
        results = sp.user_playlist_add_tracks('skrul', playlist_uri, chunk)
        print(results)


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def set_description(sp, playlist_uri, description):
    user = 'skrul'
    playlist_id = playlist_uri.split(':')[-1]
    data = {'description': description}
    sp._put("users/%s/playlists/%s" % (user, playlist_id), payload=data)


def sf_less_then_twenty_next_two_weeks():
    f = Filter()
    f.up_to_days = 14
    f.price_leq = 20
    f.city = {'S.F.'}
    f.min_spotify_popularity = 1
    return f

def sf_less_then_twenty_next_week():
    f = Filter()
    f.next_week = True
    f.price_leq = 20
    f.city = {'S.F.'}
    f.min_spotify_popularity = 1
    return f

def east_bay_less_then_twenty_next_week():
    f = Filter()
    f.next_week = True
    f.price_leq = 20
    f.city = {'Oakland', 'Berkeley', 'Albany', 'UC Berkeley Campus', 'Richmond', 'Downtown Oakland'}
    f.min_spotify_popularity = 1
    return f

def bottom_of_the_hill():
    f = Filter()
    f.up_to_days = 28
    f.venue = 'the Bottom of the Hill'
    return f


def thee_parkside():
    f = Filter()
    f.up_to_days = 28
    f.venue = 'thee Parkside'
    return f


def rickshaw_stop():
    f = Filter()
    f.up_to_days = 28
    f.venue = 'the Rickshaw Stop'
    return f


def refresh_playlist(sp, playlist_id, message, shows, fil):
    ordered_bands = []
    all_bands = set()
    for show in shows:
        if fil.accept_show(message, show):
            for band in show.bands:
                if not band.name in all_bands:
                    ordered_bands.append(band)
                    all_bands.add(band.name)
    sp = spotipy.Spotify(auth=TOKEN)
    track_uris = []

    for band in ordered_bands:
        # Random DJs
        if band.name == "dj's":
            continue
        spotify_artist = search(sp, band)
        if spotify_artist is not None:
            if fil.accept_artist(spotify_artist):
                tracks = top_tracks(sp, spotify_artist.uri)
                track_uris.extend(tracks)
                print(str(len(tracks)) + ' added for: ' + band.name)
            else:
                print('Filtered out: ' + band.name)
        else:
            print('Nothing found for: ' + band.name)

    clear_playlist(sp, playlist_id)
    results = add_tracks(sp, playlist_id, track_uris)
    d = f"Week of {message.start_date.strftime('%b %d, %Y')} ||| Filter: {fil.get_description()}"
    set_description(sp, playlist_id, d)


def main():
    filename = 'examples/The List 08_09 (sf punk_funk_thrash_ska).eml'
    with open(filename, 'rb') as f:
        raw_email = f.read()

    parsed_eml = eml_parser.eml_parser.decode_email_b(raw_email,
                                                      include_raw_body=True)
    stats = Stats()
    mp = MessageParser()
    sp = ShowParser(stats)
    m = mp.parse(parsed_eml['body'][0]['content'])
    shows = sp.parse(m)

    sp = spotipy.Spotify(auth=TOKEN)
    refresh_playlist(sp, PLAYLIST_URI, m, shows, sf_less_then_twenty_next_two_weeks())
    #refresh_playlist(sp, THEE_PARKSIDE_URI, m, shows, thee_parkside())
    #refresh_playlist(sp, RICKSHAW_STOP_URI, m, shows, rickshaw_stop())
    #refresh_playlist(sp, BOTH_URI, m, shows, bottom_of_the_hill())
    refresh_playlist(sp, 'spotify:playlist:5tXxm7fe4WAfvyvzkMzNiv', m, shows, sf_less_then_twenty_next_week())
    refresh_playlist(sp, 'spotify:playlist:64q2u7BR0xpeZEEvNYqClI', m, shows, east_bay_less_then_twenty_next_week())

    #sa = search(sp, Band('Alien Weapony', None))
    #print(top_tracks(sp, sa.uri))


def test_search(band):
    sp = spotipy.Spotify(auth=TOKEN)
    results = sp.search(q=f"artist:{band}")
    pprint.pprint(results)
    #sa = search(sp, Band(band, None))
    #pprint.pprint(sa)

if __name__ == '__main__':
    main()
    #test_search('Fox Warren')
