#!/usr/bin/env python

import json
from pytime_timers import timer, tmux_helper

class PasswordSpray(timer.TimerInterface):
    time_start: int
    time_left: int
    state: str

    def __init__(self, time_start=0, time_left=0, state="idle"):
        self.time_start = time_start
        self.time_left = time_left
        if state == "idle" and self.start_complete:
            self.state = "done"
        else:
            self.state = state

        self.write_status()

    @property
    def name(self) -> str:
        return "Password Spray"
    
    @property
    def priority(self) -> int:
        return 0

    @property
    def class_name(self) -> str:
        return self.__class__.__name__

    @property
    def start_complete(self) -> bool:
        return True

    @property
    def time_work(self) -> int:
        return 30

    @property
    def status_work(self) -> str:
        return "#[fg=#282828]#[bg=#427b58]#[bold] "

    @property
    def status_done(self) -> str:
        return "#[fg=#282828]#[bg=#427b58]#[bold] "

    @property
    def notify(self) -> bool:
        return True

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

    def start(self):
        pass

    def stop(self):
        pass
    
    def read_status(self):
        with open(f"/tmp/tmux-timers/{self.name}.json", "r") as f:
            status = json.load(f)

        try:
            self.time_start = status["time_start"]
            self.time_left = status["time_left"]
            self.state = status["state"]
        except:
            raise Exception(f"Unable to read status {self.name} status file")

    def write_status(self):
        with open(f"/tmp/tmux-timers/{self.name}.json", "w+") as f:
            status = {
                "time_start": self.time_start,
                "time_left": self.time_left,
                "state": self.state
            }

            json.dump(status, f)
