import json
import math
import logging
from datetime import datetime
import os
from ... import TmuxHelper

class JiraState:
    def __init__(self):
        self.status = ""
        self.status_base = ""
        self.enabled = False
        self.menu_base_options = []

    def state_init(self):
        logging.info(f"Initializing state: {self}")

    def __str__(self):
        return self.__class__.__name__

    def next(self, timer):
        raise NotImplementedError

    def pause(self, timer):
        logging.debug(f"pause restore: {self}")

        return Paused(timer)

    def stop(self, timer):
        timer.time_start = 0
        timer.time_end = 0
        timer.iteration = 1
        timer.task = {"key": None, "task_time": 0, "charge_code": None}

        return Idle(timer)

    def update_status(self, timer):
        pass

    def get_properties(self):
        return {}

    def restore_properties(self, timer, properties: dict):
        pass

    def update(self, timer):
        self.menu_options = self.menu_base_options
        if timer.task["key"] != None:
            self.menu_options = [TmuxHelper.menu_add_option("", "", ""), TmuxHelper.menu_add_option(f"-#[nodim]{timer.task['key']}", "", ""), TmuxHelper.menu_add_option("", "", "")] + self.menu_options

        self.update_status(timer)

class Idle(JiraState):
    STATUS_ICON = ""
    STATUS_STYLE = "#[fg=#282828]#[bg=#427b58]#[bold]"

    def __init__(self, timer):
        self.state_init()
        self.status = ""
        self.enabled = False
        self.menu_options = []
        self.menu_base_options = [
            TmuxHelper.menu_add_option("Start", "t", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py START --timer {timer.name}\""),
            TmuxHelper.menu_add_option("", "", ""),
            TmuxHelper.menu_add_option("Set Task", "", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py TASKS --timer {timer.name}\""),
        ]

        self.update(timer)

    def next(self, timer):
        now = int(datetime.now().strftime("%s")) 
        timer.time_end = now + timer.time_work
        timer.time_start = now

        timer.state = Working(timer)

        
class Working(JiraState):
    STATUS_ICON = ""
    STATUS_STYLE = "#[fg=#282828]#[bg=#427b58]#[bold]"

    def __init__(self, timer):
        self.state_init()
        self.status = ""
        self.enabled = True
        self.menu_options = []
        self.menu_base_options = [
            TmuxHelper.menu_add_option("Pause", "t", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py PAUSE --timer {timer.name}\""),
            TmuxHelper.menu_add_option("Stop", "x", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py STOP --timer {timer.name}\""),
            TmuxHelper.menu_add_option("", "", ""),
            TmuxHelper.menu_add_option("Set Task", "", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py TASKS --timer {timer.name}\"")
        ]

        self.update(timer)

    def next(self, timer):
        timer.iteration += 1

        if timer.iteration > timer.sessions:
            timer.iteration = 1
            duration = timer.time_break_long
            timer.state = BreakLong(timer)
            TmuxHelper.popup_create(timer.name, "Session finished, take a long break")
        else:
            duration = timer.time_break_short
            timer.state = BreakShort(timer)
            TmuxHelper.popup_create(timer.name, "Session finished, take a short break")

        timer.comment()

        now = int(datetime.now().strftime("%s")) 
        timer.time_start = now
        timer.time_end = now + duration

    def update_status(self, timer):
        now = int(datetime.now().strftime("%s")) 
        time_left = f"{math.floor((timer.time_end - now)/60)}m"
        self.status = f"{self.STATUS_STYLE} {self.STATUS_ICON} {timer.iteration}/{timer.sessions} {time_left}"

class BreakLong(JiraState):
    STATUS_ICON = ""
    STATUS_STYLE = "#[fg=#282828]#[bg=#427b58]#[bold]"

    def __init__(self, timer):
        self.state_init()
        self.status = ""
        self.enabled = True
        self.menu_options = []
        self.menu_base_options = [
            TmuxHelper.menu_add_option("Pause", "t", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py PAUSE --timer {timer.name}\""),
            TmuxHelper.menu_add_option("Stop", "x", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py STOP --timer {timer.name}\""),
            TmuxHelper.menu_add_option("", "", ""),
            TmuxHelper.menu_add_option("Set Task", "", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py TASKS --timer {timer.name}\""),
        ]

        self.update(timer)


    def next(self, timer):
        TmuxHelper.popup_create(timer.name, "Break finished, get back to work")

        now = int(datetime.now().strftime("%s")) 
        timer.time_end = now + timer.time_work
        timer.time_start = now

        timer.state = Working(timer)


    def update_status(self, timer):
        now = int(datetime.now().strftime("%s")) 
        time_left = f"{math.floor((timer.time_end - now)/60)}m"
        self.status = f"{self.STATUS_STYLE} {self.STATUS_ICON} {timer.iteration}/{timer.sessions} {time_left}"


class BreakShort(JiraState):
    STATUS_ICON = ""
    STATUS_STYLE = "#[fg=#282828]#[bg=#427b58]#[bold]"

    def __init__(self, timer):
        self.state_init()
        self.status = ""
        self.enabled = True
        self.menu_options = []
        self.menu_base_options = [
            TmuxHelper.menu_add_option("Pause", "t", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py PAUSE --timer {timer.name}\""),
            TmuxHelper.menu_add_option("Stop", "x", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py STOP --timer {timer.name}\""),
            TmuxHelper.menu_add_option("", "", ""),
            TmuxHelper.menu_add_option("Set Task", "", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py TASKS --timer {timer.name}\"")
        ]

        self.update(timer)


    def next(self, timer):
        TmuxHelper.popup_create(timer.name, "Break finished, get back to work")

        now = int(datetime.now().strftime("%s")) 
        timer.time_end = now + timer.time_work
        timer.time_start = now

        timer.state = Working(timer)

    
    def update_status(self, timer):
        now = int(datetime.now().strftime("%s")) 
        time_left = f"{math.floor((timer.time_end - now)/60)}m"
        self.status = f"{self.STATUS_STYLE} {self.STATUS_ICON} {timer.iteration}/{timer.sessions} {time_left}"

class Paused(JiraState):
    STATUS_ICON = ""
    STATUS_STYLE = "#[fg=#282828]#[bg=#d65d0e]#[bold]"

    def __init__(self, timer):
        self.state_init()
        self.restore_state = timer.state
        self.restore_time = timer.time_end - int(datetime.now().strftime("%s"))
        self.status = ""
        self.enabled = True
        self.menu_options = []
        self.menu_base_options = [
            TmuxHelper.menu_add_option("Resume", "t", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py RESUME --timer {timer.name}\""),
            TmuxHelper.menu_add_option("Stop", "x", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py STOP --timer {timer.name}\""),
            TmuxHelper.menu_add_option("", "", ""),
            TmuxHelper.menu_add_option("Set Task", "", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py TASKS --timer {timer.name}\"")
        ]

        self.update(timer)


    def next(self, timer):
        now = int(datetime.now().strftime("%s")) 
        timer.time_end = now + self.restore_time
        timer.time_start = now
        timer.state = self.restore_state

    def get_properties(self):
        properties = {
            "restore_state": str(self.restore_state),
            "restore_time": self.restore_time
        }

        return properties
    
    def restore_properties(self, timer, properties: dict):
        if properties == None:
            raise Exception(f"{self} requires properties to be specified when restoring")

        if properties["restore_state"] not in list(STATES.keys()):
            raise Exception(f"{properties['restore_state']} is not a valid restore state")

        if type(properties["restore_time"]) != int:
            raise Exception(f"{properties['restore_time']} is not an integer")

        if properties["restore_time"] < 0:
            raise Exception(f"{properties['restore_time']} can not be negative")

        state = STATES[properties["restore_state"]](timer)
        if str(state) != str(self.restore_state):
            self.restore_state = state
        else:
            del state
        self.restore_time = properties["restore_time"]

    def update_status(self, timer):
        time_left = f"{math.floor(self.restore_time/60)}m"
        self.status = f"{self.STATUS_STYLE} {self.restore_state.STATUS_ICON} {timer.iteration}/{timer.sessions} {time_left}"


STATES = {
    "Idle": Idle,
    "Working": Working,
    "BreakShort": BreakShort,
    "BreakLong": BreakLong,
    "Paused": Paused
}
