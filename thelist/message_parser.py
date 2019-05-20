import re
from enum import Enum
from datetime import datetime

from message import Message

HEADER_RE = re.compile(
    r"""
^
funk-punk-thrash-ska.*
\b(?P<month>\w+)\s+
(?P<day>\d+),\s+
(?P<year>\d+)
""", re.X)

FIX_MONTH = {
    'Febuary': 'February',
    'Feburary': 'February',
    'Feb': 'February',
    'Apr': 'April',
    'Aug': 'August',
    'Mar': 'March',
    'Dec': 'December',
    'Jul': 'July',
    'Nov': 'November',
    'Sep': 'September',
    'Jun': 'June',
    'Jan': 'January',
    'Oct': 'October'
}

TYPOS = [
    (r'Squareat 924', 'Square at 924'),
    (r'Amerian', 'American')
]


class State(Enum):
    expecting_header = 1
    expecting_space = 2
    expecting_start_show = 3
    in_show = 4


class MessageParser:
    def parse(self, raw_message):

        for pattern, repl in TYPOS:
            raw_message = re.sub(pattern, repl, raw_message)

        state = State.expecting_header
        current_show = []
        raw_shows = []
        start_date = None
        for line in raw_message.split("\n"):
            if state == State.expecting_header:
                result = re.match(HEADER_RE, line)
                if result:
                    state = State.expecting_space
                    month = result.group('month')
                    month = FIX_MONTH.get(month, month)
                    date_string = f"{month} {result.group('day')}, {result.group('year')}"
                    start_date = datetime.strptime(date_string, '%B %d, %Y')
                continue
            if state == State.expecting_space:
                if line.strip() == '':
                    state = State.expecting_start_show
                continue
            if state == State.expecting_start_show:
                current_show.append(line.strip())
                state = State.in_show
                continue
            if state == State.in_show:
                if line.startswith(' '):
                    current_show.append(line.strip())
                elif line.strip() == '':
                    raw_shows.append(' '.join(current_show))
                    break
                else:
                    raw_shows.append(' '.join(current_show))
                    current_show = [line.strip()]

        return Message(start_date, raw_shows)
