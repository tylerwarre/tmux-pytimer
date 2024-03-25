from ..State import State

class Idle(State):
    def next(self):
        return Working()

class Working(State):
    def next(self):
        return Done()

class Done(State):
    def next(self):
        return Working()
