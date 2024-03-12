#!/usr/bin/env python
from abc import abstractmethod

class PomodoroInterface():
    @property
    def timer_type(self) -> str:
        return str()

    @property
    def start_complete(self) -> bool:
        return bool()

    @property
    def time_work(self) -> int:
        return int()

    @property
    def sessions(self) -> int:
        return int()

    @property
    def time_short_break(self) -> int:
        return int()

    @property
    def time_long_break(self) -> int:
        return int()

    @property
    def status_work(self) -> str:
        return str()

    @property
    def status_break(self) -> str:
        return str()

    @property
    def notify(self) -> bool:
        return bool()

    @property
    def state(self) -> dict:
        return dict()
    
    @abstractmethod
    def gen_menu(self):
        pass
    
    @abstractmethod
    def get_status(self):
        pass
