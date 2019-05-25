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

TOKEN = util.prompt_for_user_token('skrul', 'playlist-modify-public',
                                   'ca917724c4c34f9e8f810372813b71a8',
                                   '29e3b125904145da9006893669126cc2',
                                   'http://skrul.com/')


def search(sp, band):
    results = sp.search(q=f'"{band.name}"', type='artist')
    #if len(results['artists']['items']) == 1:
    #    return results['artists']['items'][0]['uri']
    if len(results['artists']['items']) > 0:
        item = results['artists']['items'][0]
        if item['popularity'] > 50:
            return item['uri']
    else:
        return None


def top_tracks(sp, uri):
    results = sp.artist_top_tracks(uri)
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


def sf_less_then_twenty_next_two_weeks(show):
    two_week_past_now = datetime.now().date() + timedelta(days=14)
    return (show.price is None
            or show.price.leq(20)) and show.city == 'S.F.' and len(
                show.bands) <= 3 and show.is_before(two_week_past_now)


def bottom_of_the_hill(show):
    two_week_past_now = datetime.now().date() + timedelta(days=14)
    return show.venue == 'the Bottom of the Hill' and show.is_before(
        two_week_past_now)


def thee_parkside(show):
    two_week_past_now = datetime.now().date() + timedelta(days=14)
    return show.venue == 'thee Parkside' and show.is_before(two_week_past_now)


def refresh_playlist(sp, playlist_id, shows, filter_func):
    ordered_bands = []
    all_bands = set()
    for show in shows:
        if filter_func(show):
            for band in show.bands:
                if not band.name in all_bands:
                    ordered_bands.append(band)
                    all_bands.add(band.name)
    sp = spotipy.Spotify(auth=TOKEN)
    clear_playlist(sp, playlist_id)
    track_uris = []

    for band in ordered_bands:
        artist_uri = search(sp, band)
        if artist_uri is not None:
            tracks = top_tracks(sp, artist_uri)
            track_uris.extend(tracks)
            print(str(len(tracks)) + ' added for: ' + band.name)
        else:
            print('Nothing found for: ' + band.name)

    results = add_tracks(sp, playlist_id, track_uris)


def main():
    filename = 'examples/The List 05_17 (sf punk_funk_thrash_ska).eml'
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
    #refresh_playlist(sp, BOTH_URI, shows, bottom_of_the_hill)
    refresh_playlist(sp, PLAYLIST_URI, shows,
                     sf_less_then_twenty_next_two_weeks)
    #refresh_playlist(sp, THEE_PARKSIDE_URI, shows, thee_parkside)
    #print(search(sp, Band('Rubber Tramp', None)))


def test_search(band):
    sp = spotipy.Spotify(auth=TOKEN)
    results = sp.search(q=band, type='artist')
    pprint.pprint(results)


if __name__ == '__main__':
    main()
    #test_search('beyonce')
