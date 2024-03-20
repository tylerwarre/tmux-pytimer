#!/home/m83393/.tmux/tmux-venv/bin python3
import math
from datetime import datetime
from abc import abstractmethod

class TimerInterface:
    @property
    def name(self) -> str:
        raise NotImplementedError()

    @property
    def priority(self) -> int:
        raise NotImplementedError()

    @property
    def class_name(self) -> str:
        raise NotImplementedError()

    @property
    def time_work(self) -> int:
        raise NotImplementedError()

    @property
    def time_end(self) -> int:
        raise NotImplementedError()

    @property
    def time_left(self) -> str:
        raise NotImplementedError()

    @property
    def status_work(self) -> str:
        raise NotImplementedError()

    @property
    def status_done(self) -> str:
        raise NotImplementedError()

    @property
    def notify(self) -> bool:
        raise NotImplementedError()

    @property
    def state(self) -> str:
        raise NotImplementedError()

    @property
    def cmds(self) -> list:
        raise NotImplementedError()

    @property
    def is_enabled(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def gen_menu(self):
        raise NotImplementedError()

    @abstractmethod
    def read_status(self):
        raise NotImplementedError()

    @abstractmethod
    def write_status(self):
        raise NotImplementedError()

    @abstractmethod
    def start(self):
        raise NotImplementedError()

    @abstractmethod
    def stop(self):
        raise NotImplementedError()

    def calc_time_left(self):
        delta = datetime.strptime(str(self.time_end), "%s") - datetime.now()
        self._time_left = f"{math.floor(delta.seconds / 60)}m"

