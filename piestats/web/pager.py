class PaginationHelper():
    ''' Help keep track of pagination for the web UI, in terms of correct offsets '''
    def __init__(self, bare_route, offset, interval=20, num_items=None):
        self.bare_route = bare_route
        self.interval = interval
        self.num_items = num_items

        if offset % interval or offset < 0:
            offset = 0

        self.offset = offset

    @property
    def prev_url(self):
        if self.offset is None:
            return False

        elif self.offset == self.interval:
            return self.bare_route
        elif self.offset >= self.interval:
            return self.bare_route + '/pos/%d' % (self.offset - self.interval)

    @property
    def next_url(self):
        if (self.offset + self.interval) > self.num_items:
            return False
        return self.bare_route + '/pos/%d' % (self.offset + self.interval)
