import re
from datetime import date

from show import Show
from band import Band
from prices import Prices

SPACE_OUTSIDE_PAREN_RE = re.compile(r' (?![^(]*\))')

AGES_RE = re.compile(r'a/a|\?/\?|\d+\+')
PRICE_RE = re.compile(r'donation|free|\$\S+')
TIME_RE = re.compile(r'[\d:/apm]+')
FEATURES_RE = re.compile(r'[*#$@^]')
LOCATION_LIST_RE = re.compile(r',(?![^(]*\))')

MONTHS = [
    'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct',
    'nov', 'dec'
]
DOWS = ['mon', 'tue', 'wed', 'thr', 'fri', 'sat', 'sun']

SINGLE_DAY_RE = re.compile(
    rf"""
^
(?P<month>{'|'.join(MONTHS)})\s+
(?P<day>\d+)\s+
(?P<dow>{'|'.join(DOWS)})
""", re.X)

MONTH_DAY_RE = re.compile(
    rf"""
^
(?P<month>{'|'.join(MONTHS)})\s+
(?P<day>\d+)
""", re.X | re.I)

DAY_RE = re.compile(rf"""
^
(?P<day>\d+)
""", re.X)

BAND_LIST_RE = re.compile(r',(?![^(]*\))')

BAND_NAME_EXTRA_RE = re.compile(
    r"""
^
(?P<name>[^(]*)
(?:\s+\((?P<extra>.*)\))?
.*$
""", re.X)


class ShowParser:
    def __init__(self, stats):
        self.stats = stats

    def parse(self, message):
        shows = []
        for raw_show in message.lines:
            self.stats.inc_count()
            if re.search(r'(cancelled|incorrect listing|postponed)',
                         raw_show) is not None:
                continue
            try:
                shows.append(self._parse_one(message, raw_show))
            except Exception as e:
                #print(raw_show)
                #raise(e)
                self.stats.log('failed to parse ' + raw_show + ': ' + str(e))
                self.stats.inc_failed()
        return shows

    def _parse_one(self, message, raw_show):
        dates, rest = self._parse_date(raw_show, message.start_date)
        if len(dates) == 0:
            raise Exception('no dates')

        i = self._find_at(rest)
        if i is None:
            raise Exception('missing at')
        bands = rest[:i]
        rest = rest[i + 4:]

        ages = None
        ages_notes = None
        price = None
        price_notes = None
        time = None
        time_notes = None
        features = []
        notes = None

        def read(regex, a):
            value, notes = None, None
            if len(a) > 0 and re.match(regex, a[0]):
                value = a.pop(0)
                if len(a) > 0 and a[0].startswith('('):
                    notes = a.pop(0)
            return value, notes

        a = re.split(SPACE_OUTSIDE_PAREN_RE, rest)
        unmatched = []
        while len(a) > 0:
            value, notes = read(AGES_RE, a)
            if value is not None:
                ages, ages_notes = value, notes
                continue
            value, notes = read(PRICE_RE, a)
            if value is not None:
                price, price_notes = value, notes
                continue
            value, notes = read(TIME_RE, a)
            if value is not None:
                time, time_notes = value, notes
                continue
            if re.match(FEATURES_RE, a[0]):
                features.append(a.pop(0))
                continue
            unmatched.append(a.pop(0))

        if unmatched[-1].startswith('('):
            note = unmatched.pop()

        loc_list = re.split(LOCATION_LIST_RE, ' '.join(unmatched), 1)
        venue = loc_list[0].strip()
        city = None
        if len(loc_list) > 1:
            city = loc_list[1].strip()
        show = Show(raw_show, dates, self._parse_bands(bands), venue, city,
                    ages, ages_notes,
                    None if price is None else Prices.from_string(price),
                    price_notes, time, time_notes, features, notes)
        return show

    def _parse_date(self, line, start_date):
        result = re.match(SINGLE_DAY_RE, line)
        if result:
            month_num = MONTHS.index(result.group('month').lower()) + 1
            day_num = int(result.group('day'))
            year = start_date.year
            if month_num < start_date.month:
                year += 1
            return ([date(year, month_num, day_num)], line[result.end() + 1:])

        last_month_num = None
        dates = []
        pos = 0
        year = start_date.year
        for p in line.split('/'):
            result = re.match(MONTH_DAY_RE, p)
            if result:
                matched_month_num = MONTHS.index(
                    result.group('month').lower()) + 1
                if last_month_num is not None and matched_month_num < last_month_num:
                    year += 1
                last_month_num = matched_month_num
                day_num = int(result.group('day'))
                dates.append(date(year, last_month_num, day_num))
                pos += result.end() + 1
            else:
                result = re.match(DAY_RE, p)
                if result:
                    dates.append(
                        date(year, last_month_num, int(result.group('day'))))
                    pos += result.end() + 1
                else:
                    break
        return (dates, line[pos:])

    def _parse_bands(self, raw_band_list):
        raw_bands = re.split(BAND_LIST_RE, raw_band_list)
        bands = []
        for raw_band in raw_bands:
            br = re.match(BAND_NAME_EXTRA_RE, raw_band.strip())
            if br:
                bands.append(Band(br.group('name').strip(), br.group('extra')))
        if len(bands) == 0:
            raise Exception("can't parse band list")
        return bands

    def _find_at(self, s):
        in_paren = False
        looking_for = ' at '
        looking_for_idx = 0
        for i, c in enumerate(s):
            if c == '(':
                in_paren = True
                looking_for_idx = 0
                continue
            if c == ')':
                in_paren = False
                looking_for_idx = 0
                continue
            if not in_paren:
                c = c.lower()
                if c == looking_for[looking_for_idx]:
                    looking_for_idx += 1
                    if looking_for_idx == len(looking_for):
                        return i - len(looking_for) + 1
                else:
                    looking_for_idx = 0
                    if c == looking_for[looking_for_idx]:
                        looking_for_idx += 1
        return None
