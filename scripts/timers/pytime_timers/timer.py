#!/home/m83393/.tmux/tmux-venv/bin python3
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
    def start_complete(self) -> bool:
        raise NotImplementedError()

    @property
    def time_work(self) -> int:
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

    @abstractmethod
    def gen_menu(self):
        pass
    
    @abstractmethod
    def read_status(self):
        pass

    @abstractmethod
    def write_status(self):
        pass

    @abstractmethod
    def pause(self):
        pass

    @abstractmethod
    def resume(self):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass
