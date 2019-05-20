class Stats:
    def __init__(self):
        self.count = 0
        self.failed = 0

    def inc_count(self):
        self.count += 1

    def inc_failed(self):
        self.failed += 1
