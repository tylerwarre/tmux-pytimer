import logging
from datetime import datetime
from ... import TmuxHelper

class JiraState:
    def __init__(self):
        self.status = ""
        self.enabled = False
        self.menu_options = []
        logging.info(f"Initializing state: {self}")

    def __str__(self):
        return self.__class__.__name__

    def next(self, timer):
        raise NotImplementedError

    def pause(self, timer):
        print(f"pause restore: {self}")

        timer.state = Paused(timer)

    def stop(self, timer):
        timer.time_start = 0
        timer.time_end = 0
        timer.iteration = 1
        timer.task = None
        timer.task_time = 0

        timer.state = Idle(timer)


class Idle(JiraState):
    def __init__(self, timer):
        self.status = ""
        self.enabled = False
        self.menu_options = [
            TmuxHelper.menu_add_option("Start", "t", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py START --blocking --timer {timer.name}\""),
            TmuxHelper.menu_add_option("", "", ""),
            TmuxHelper.menu_add_option("Set Task", "", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py TASKS --blocking --timer {timer.name}\""),
        ]

        if timer.task != None:
            self.menu_options = [TmuxHelper.menu_add_option("", "", ""), TmuxHelper.menu_add_option(f"-#[nodim]{timer.task}", "", "")] + self.menu_options

    def next(self, timer):
        timer.time_end = timer.time_work

        timer.state = Working(timer)
        
class Done(JiraState):
    def __init__(self, timer):
        self.status = "#[fg=#282828]#[bg=#427b58]#[bold] "
        self.enabled = True
        self.menu_options = [
            TmuxHelper.menu_add_option("Start", "t", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py START --blocking --timer {timer.name}\""),
            TmuxHelper.menu_add_option("", "", ""),
            TmuxHelper.menu_add_option("Set Task", "", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py TASKS --blocking --timer {timer.name}\"")
        ]

        if timer.task != None:
            self.menu_options = [TmuxHelper.menu_add_option("", "", ""), TmuxHelper.menu_add_option(f"-#[nodim]{timer.task}", "", "")] + self.menu_options

    def next(self, timer):
        timer.time_end = timer.time_work

        timer.state = Working(timer)

class Working(JiraState):
    def __init__(self, timer):
        self.status = "#[fg=#282828]#[bg=#427b58]#[bold] "
        self.enabled = True
        self.menu_options = [
            TmuxHelper.menu_add_option("Pause", "t", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py PAUSE --timer {timer.name}\""),
            TmuxHelper.menu_add_option("Stop", "x", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py STOP --timer {timer.name}\""),
            TmuxHelper.menu_add_option("", "", ""),
            TmuxHelper.menu_add_option("Set Task", "", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py TASKS --blocking --timer {timer.name}\"")
        ]

        if timer.task != None:
            self.menu_options = [TmuxHelper.menu_add_option("", "", ""), TmuxHelper.menu_add_option(f"-#[nodim]{timer.task}", "", "")] + self.menu_options

    def next(self, timer):
        timer.iteration += 1
        now = int(datetime.now().strftime("%s")) 

        if timer.iteration > timer.sessions:
            timer.time_end = now + timer.time_break_long
            timer.state = BreakLong(timer)
            TmuxHelper.popup_create(timer.name, "Session finished, take a long break")
        else:
            timer.time_end = now + timer.time_break_short
            timer.state = BreakShort(timer)
            TmuxHelper.popup_create(timer.name, "Session finished, take a short break")

        timer.time_start = now

class BreakLong(JiraState):
    def __init__(self, timer):
        self.status = "#[fg=#282828]#[bg=#427b58]#[bold] "
        self.enabled = True
        self.menu_options = [
            TmuxHelper.menu_add_option("Pause", "t", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py PAUSE --timer {timer.name}\""),
            TmuxHelper.menu_add_option("Stop", "x", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py STOP --timer {timer.name}\""),
            TmuxHelper.menu_add_option("", "", ""),
            TmuxHelper.menu_add_option("Set Task", "", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py TASKS --blocking --timer {timer.name}\"")
        ]

        if timer.task != None:
            self.menu_options = [TmuxHelper.menu_add_option("", "", ""), TmuxHelper.menu_add_option(f"-#[nodim]{timer.task}", "", "")] + self.menu_options

    def next(self, timer):
        now = int(datetime.now().strftime("%s")) 
        timer.time_end = now + timer.time_work
        timer.time_start = now

        timer.state = Working(timer)
        TmuxHelper.popup_create(timer.name, "Break finished, get back to work")

class BreakShort(JiraState):
    def __init__(self, timer):
        self.status = "#[fg=#282828]#[bg=#427b58]#[bold] "
        self.enabled = True
        self.menu_options = [
            TmuxHelper.menu_add_option("Pause", "t", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py PAUSE --timer {timer.name}\""),
            TmuxHelper.menu_add_option("Stop", "x", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py STOP --timer {timer.name}\""),
            TmuxHelper.menu_add_option("", "", ""),
            TmuxHelper.menu_add_option("Set Task", "", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py TASKS --blocking --timer {timer.name}\"")
        ]

        if timer.task != None:
            self.menu_options = [TmuxHelper.menu_add_option("", "", ""), TmuxHelper.menu_add_option(f"-#[nodim]{timer.task}", "", "")] + self.menu_options


    def next(self, timer):
        now = int(datetime.now().strftime("%s")) 
        timer.time_end = now + timer.time_work
        timer.time_start = now

        timer.state = Working(timer)
        TmuxHelper.popup_create(timer.name, "Break finished, get back to work")

class Paused(JiraState):
    def __init__(self, timer):
        self.restore_state = timer.state
        self.restore_time = timer.time_end - int(datetime.now().strftime("%s"))
        self.status = "#[fg=#282828]#[bg=#d65d0e]#[bold] "
        self.enabled = True
        self.menu_options = [
            TmuxHelper.menu_add_option("Resume", "t", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py RESUME --timer {timer.name}\""),
            TmuxHelper.menu_add_option("Stop", "x", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py STOP --timer {timer.name}\""),
            TmuxHelper.menu_add_option("", "", ""),
            TmuxHelper.menu_add_option("Set Task", "", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py TASKS --blocking --timer {timer.name}\"")
        ]

        if timer.task != None:
            self.menu_options = [TmuxHelper.menu_add_option("", "", ""), TmuxHelper.menu_add_option(f"-#[nodim]{timer.task}", "", "")] + self.menu_options

    def next(self, timer):
        now = int(datetime.now().strftime("%s")) 
        timer.time_end = now + self.restore_time
        timer.time_start = now
        timer.state = self.restore_state
