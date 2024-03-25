import logging
class State:

    def __init__(self):
        self.restore = None
        logging.info(f"Initializing state: {self}")

    def __str__(self):
        return self.__class__.__name__

    def next(self, *args, **kwargs):
        return

    def pause(self):
        self.restore = self
        return Paused()

class Paused(State):
    def next(self, *args, **kwargs):
        super(Paused, self).next(*args, **kwargs)
        return self.restore
