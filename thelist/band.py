class Band:
    def __init__(self, name, extra):
        self.name = name
        self.extra = extra

    def __str__(self):
        return str({'name': self.name, 'extra': self.extra})
