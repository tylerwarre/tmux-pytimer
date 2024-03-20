import json
from datetime import datetime
from jira_lib import Jira, JiraFields
from .timer_classes.timer import TimerInterface
from . import tmux_helper as tmux_helper

class JiraTimer(TimerInterface):
    def __init__(self, name="Jira", priority=0, start_complete=False, time_work=60, 
                 time_break_short=5, time_break_long=60, time_left="", 
                 sessions=3, iteration=0, status_work="#[fg=#282828]#[bg=#427b58]#[bold] ",
                 status_done="#[fg=#282828]#[bg=#427b58]#[bold] ", notify=True,
                 cmds=["ACK", "MENU", "START", "TERM", "PAUSE", "RESUME", "SET", "TASKS"], state="idle"):
        self._name = name
        self._priority = priority
        self._start_complete = start_complete
        self._time_work = time_work
        self._time_break_short = time_break_short
        self._time_break_long = time_break_long
        self._time_left = time_left
        self._sessions = sessions
        self._iteration = iteration
        self._status_work = status_work
        self._status_done = status_done
        self._notify = notify
        self._cmds = cmds
        self._is_enabled = False
        self.task = None
        if state == "idle" and self.start_complete:
            self._state = "done"
        else:
            self._state = state
        with open("jira.key", "r") as f:
            self.jira = Jira(f.read().rstrip())

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
    def time_end(self) -> int:
        return self._time_start

    @property
    def time_left(self) -> str:
        return self._time_left

    @property
    def sesssions(self) -> int:
        return self._sessions

    @property
    def iteration(self) -> int:
        return self._iteration

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
        return self._cmds

    @property
    def is_enabled(self) -> bool:
        return self._is_enabled

    @property
    def state(self) -> str:
        return self._state

    def gen_menu(self):
        options = []
        if self.state == "idle" or self.state == "done":
            options.append(tmux_helper.menu_add_option("Start", "t", f"run-shell \"{tmux_helper.get_plugin_dir()}/scripts/tmux_pytimer.py START --timer {self.class_name}\""))
        elif self.state == "paused":
            options.append(tmux_helper.menu_add_option("Resume", "t", f"run-shell \"{tmux_helper.get_plugin_dir()}/scripts/tmux_pytimer.py RESUME --timer {self.class_name}\""))
            options.append(tmux_helper.menu_add_option("Stop", "c", f"run-shell \"{tmux_helper.get_plugin_dir()}/scripts/tmux_pytimer.py STOP --timer {self.class_name}\""))
        elif self.state == "running":
            options.append(tmux_helper.menu_add_option("Pause", "t", f"run-shell \"{tmux_helper.get_plugin_dir()}/scripts/tmux_pytimer.py PAUSE --timer {self.class_name}\""))
            options.append(tmux_helper.menu_add_option("Stop", "c", f"run-shell \"{tmux_helper.get_plugin_dir()}/scripts/tmux_pytimer.py STOP --timer {self.class_name}\""))
        else:
            raise Exception(f"Unknown state {self.state}") 

        options.append(tmux_helper.menu_add_option("", "", ""))
        options.append(tmux_helper.menu_add_option("Set Task", "", f"run-shell \"{tmux_helper.get_plugin_dir()}/scripts/tmux_pytimer.py TASK --timer {self.class_name}\""))

        tmux_helper.menu_create(self.name, "R", "S", options)

    def pause(self):
        if self.state not in ["working", "short_break", "long_break"]:
            raise Exception(f"Unkown timer state for pause: {self.state}")

        self._state = "paused"
        self._time_end = self.time_end - int(datetime.now().strftime("%s"))
        self._time_left = f"*{self.time_left}"

    def resume(self):
        if self.state != "paused":
            raise Exception(f"Unkown timer state for resume: {self.state}")

        self._time_end = int(datetime.now().strftime("%s")) + self.time_end
        self.calc_time_left()


    def start(self):
        if self.task == None:
            self.gen_menu()

        if self.state == "idle":
            self._time_end = int(datetime.now().strftime("%s")) + (self.time_work * 60)
        elif self.state == "working":
            # Long break
            if self.iteration >= self.sesssions:
                self._time_end = int(datetime.now().strftime("%s")) + (self.time_break_long * 60)
            # Short break
            else:
                self._time_end = int(datetime.now().strftime("%s")) + (self.time_break_short * 60)
        elif self.state == "short_break":
            self._time_end = int(datetime.now().strftime("%s")) + (self.time_work * 60)
        elif self.state == "long_break":
            self._time_end = int(datetime.now().strftime("%s")) + (self.time_work * 60)
        else:
            raise Exception(f"Unknown timer state for start: {self.state}")

        self.calc_time_left()

    def stop(self):
        self._state = "idle"
        self._iteration = 0
        self._time_left = ""
        self._time_end = 0
    
    def read_status(self):
        try:
            with open(f"/tmp/tmux-pytimer/{self.name}.json", "r") as f:
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
            with open(f"/tmp/tmux-pytimer/{self.name}.json", "w+") as f:
                status = {
                    "time_end": self.time_end,
                    "time_left": self.time_left,
                    "state": self.state
                }

                json.dump(status, f)
        except:
            raise Exception(f"Unable to write {self.name} status file")

    def sanitize_tickets(self, tickets) -> list[dict]:
        for ticket in tickets:
            ticket[JiraFields.SUMMARY] = ticket["fields"][JiraFields.SUMMARY]
            ticket.pop("expand")
            ticket.pop("fields")

        return tickets


    def gen_tickets_menu(self):
        tickets = self.jira.get_tickets(f"{JiraFields.ASSIGNEE} = 'M83393' " \
                f"and {JiraFields.STATUS} != 'Done' " \
                f"and {JiraFields.PROJECT} = 'MDT' "\
                f"and {JiraFields.SPRINT} in openSprints()", 
                fields=[JiraFields.SUMMARY])
        tickets = self.sanitize_tickets(tickets)

        options = []
        for ticket in tickets:
            options.append(tmux_helper.menu_add_option(f"{ticket['key']}: {ticket['summary']}", "", f"run-shell \"{tmux_helper.get_plugin_dir()}/scripts/tmux_pytimer.py STOP --timer {self.class_name}\""))

        tmux_helper.menu_create("Tickets", "C", "C", options)
