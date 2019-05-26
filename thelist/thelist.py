import mailbox
import eml_parser
from collections import Counter
from datetime import datetime

from show import Show
from band import Band
from stats import Stats
from message_parser import MessageParser
from show_parser import ShowParser
from message import Message
from prices import Prices


def parse_mbox():
    stats = Stats()
    mbox = mailbox.mbox('examples/thelist.mbox')
    mp = MessageParser()
    sp = ShowParser(stats)
    c = Counter()
    i = 0
    for message in mbox:
        m = mp.parse(message.get_payload())
        shows = sp.parse(m)
        for show in shows:
            c[show.price] += 1
        i += 1
        if i > 100:
            break

    print(stats.count)
    print(stats.failed)
    print((stats.failed / stats.count) * 100)

    for p in c.most_common():
        print(p)


def parse_eml():
    filename = 'examples/The List 05_24 (sf punk_funk_thrash_ska).eml'
    #filename = 'examples/The List 05_17 (sf punk_funk_thrash_ska).eml'
    #filename = 'examples/The List 05_03 (sf punk_funk_thrash_ska).eml'
    with open(filename, 'rb') as f:
        raw_email = f.read()

    parsed_eml = eml_parser.eml_parser.decode_email_b(raw_email,
                                                      include_raw_body=True)
    stats = Stats()
    mp = MessageParser()
    sp = ShowParser(stats)
    m = mp.parse(parsed_eml['body'][0]['content'])
    shows = sp.parse(m)
    c = Counter()

    for show in shows:
        if (show.price is None or show.price.leq(20)) and show.city == 'S.F.':
            c[show.venue] += 1
        # if (show.price is None or show.price.leq(20)) and show.city == 'S.F.':
        #     print(', '.join(b.name for b in show.bands))
        #c[show.venue] += 1
        #c[show.price] += 1
        #pass
        #print(show)
        # print("{0}    {1:30.30}    {2:20.20}    {3:20.20}    {4:5}    {5:10}    {6:10}".format(
        #     show.dates[0],
        #     ', '.join(b.name for b in show.bands),
        #     show.venue,
        #     show.city,
        #     show.age or '',
        #     show.price or '',
        #     show.time or '',
        #     show.features or ''
        # ))
    print(stats.count)
    print(stats.failed)
    print((stats.failed / stats.count) * 100)
    print('\n'.join(stats.log_lines))

    for p in c.most_common()[:20]:
        print(p)


def main():
    parse_eml()
    #parse_mbox()
    #print(Prices.from_string('$1-$2'))

    # s = "may 27 sun Dear Indugu (2:30pm in front of Cody's books), The Dandelion War (1pm in front of Cody's books) at LastSundays"
    # m = Message(datetime.now(), [s])
    # stats = Stats()
    # sp = ShowParser2(stats)
    # print(sp.parse(m)[0])


#     print(show.bands)

# c = Counter()
# for show in shows:
#     for band in show.bands:
#         c[band.extra] += 1

# for p in c.most_common():
#     print(p)

# dates = [
#     'oct 18 fri band band band',
#     'sep 30/oct 1/2 band band band',
#     'jul 27/28 band band band',
#     'oct 17/18/19 band band band',
#     'dec 21/22/23/26/27/28 band band band',
#     'jan 1 tue band band',
#     'dec 1/2/jan 3 band band'
# ]

# for d in dates:
#     print(d)
#     print(parse_date(d, date(2019, 3, 1)))

if __name__ == '__main__':
    main()
