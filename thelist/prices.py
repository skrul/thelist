class Prices:
    def __init__(self, ranges):
        self.ranges = ranges

    def __str__(self):
        return ', '.join(str(r) for r in self.ranges)

    def from_string(s):
        def to_num(x):
            if x == 'free':
                return 0
            return float(x) if '.' in x else int(x)

        ranges = []
        s = s.replace('$', '')
        if s.find('/') > 0:
            a = s.split('/')
            for p in a:
                if p.endswith('+'):
                    ranges.append((to_num(p[:-1]), None))
                else:
                    ranges.append((to_num(p), to_num(p)))
        elif s.find('-') > 0:
            if s.endswith('+'):
                s = s[:-1]
            a = sorted(s.split('-'))
            ranges.append((to_num(a[0]), to_num(a[1])))
        else:
            if s.endswith('+'):
                ranges.append((to_num(s[:-1]), None))
            else:
                ranges.append((to_num(s), to_num(s)))
        return Prices(ranges)

    def leq(self, n):
        for r in self.ranges:
            if r[0] <= n:
                return True
        return False
