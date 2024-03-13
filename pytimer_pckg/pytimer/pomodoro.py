import json
from .timer_classes.timer import TimerInterface
from . import tmux_helper as tmux_helper

class PomodoroTimer(TimerInterface):
    def __init__(self, name="Pomodoro", priority=0, start_complete=False, time_work=60, 
                 time_break_short=5, time_break_long=60, time_start=0, time_left=0, 
                 status_work="#[fg=#282828]#[bg=#427b58]#[bold] ",
                 status_done="#[fg=#282828]#[bg=#427b58]#[bold] ", notify=True,
                 cmds=["ACK", "START", "TERM", "PAUSE", "RESUME"], state="idle"):
        self._name = name
        self._priority = priority
        self._start_complete = start_complete
        self._time_work = time_work
        self._time_break_short = time_break_short
        self._time_break_long = time_break_long
        self._time_start = time_start
        self._time_left = time_left
        self._status_work = status_work
        self._status_done = status_done
        self._notify = notify
        self._cmds = cmds
        if state == "idle" and self.start_complete:
            self._state = "done"
        else:
            self._state = state

        self.write_status()

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def priority(self) -> int:
        return self._priority

    @property
    def class_name(self) -> str:
        return self.__class__.__name__

    @property
    def start_complete(self) -> bool:
        return self._start_complete

    @property
    def time_work(self) -> int:
        return self._time_work

    @property
    def time_break_short(self) -> int:
        return self._time_break_short

    @property
    def time_break_long(self) -> int:
        return self._time_break_long

    @property
    def time_start(self) -> int:
        return self._time_start

    @property
    def time_left(self) -> int:
        return self._time_left

    @property
    def status_work(self) -> str:
        return self._status_work

    @property
    def status_done(self) -> str:
        return self._status_done

    @property
    def notify(self) -> bool:
        return self._notify

    @property
    def cmds(self) -> list:
        raise self._cmds

    @property
    def state(self) -> str:
        return self._state

    def gen_menu(self):
        options = []
        if self.state == "idle" or self.state == "done":
            options.append(tmux_helper.menu_add_option("Start", "t", f"run-shell \"{tmux_helper.get_plugin_dir()}/scripts/tmux_pytimer.py --timer {self.class_name} --action start\""))
        elif self.state == "paused":
            options.append(tmux_helper.menu_add_option("Resume", "t", f"run-shell \"{tmux_helper.get_plugin_dir()}/scripts/tmux_pytimer.py --timer {self.class_name} --action resume\""))
            options.append(tmux_helper.menu_add_option("Stop", "c", f"run-shell \"{tmux_helper.get_plugin_dir()}/scripts/tmux_pytimer.py --timer {self.class_name} --action stop\""))
        elif self.state == "running":
            options.append(tmux_helper.menu_add_option("Pause", "t", f"run-shell \"{tmux_helper.get_plugin_dir()}/scripts/tmux_pytimer.py --timer {self.class_name} --action pause\""))
            options.append(tmux_helper.menu_add_option("Stop", "c", f"run-shell \"{tmux_helper.get_plugin_dir()}/scripts/tmux_pytimer.py --timer {self.class_name} --action stop\""))
        else:
            raise Exception(f"Unknown state {self.state}") 

        tmux_helper.menu_create(self.name, "R", "S", options)

    def pause(self):
        pass

    def resume(self):
        raise NotImplementedError()

    def start(self):
        pass

    def stop(self):
        pass
    
    def read_status(self):
        try:
            with open(f"/tmp/tmux-pytimers/{self.name}.json", "r") as f:
                status = json.load(f)
        except:
            raise Exception(f"Unable to access {self.name} status file")

        try:
            self._time_start = status["time_start"]
            self._time_left = status["time_left"]
            self._state = status["state"]
        except:
            raise Exception(f"Unable to read status {self.name} status file")

    def write_status(self):
        try:
            with open(f"/tmp/tmux-pytimers/{self.name}.json", "w+") as f:
                status = {
                    "time_start": self.time_start,
                    "time_left": self.time_left,
                    "state": self.state
                }

                json.dump(status, f)
        except:
            raise Exception(f"Unable to write {self.name} status file")


test = PomodoroTimer()
test.gen_menu()

