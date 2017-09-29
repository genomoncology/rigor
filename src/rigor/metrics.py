import time


class Timer(object):

    def __repr__(self):
        return "%.3fs" % self.interval if self.interval >= 0 else "N/A"

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start

    def get_duration(self):
        return int(getattr(self, "interval", -1) * 1000000000)
