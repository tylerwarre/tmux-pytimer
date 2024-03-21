import json
from datetime import datetime
from jira_lib import Jira, JiraFields
from .timer_classes.timer import TimerInterface
from . import tmux_helper as tmux_helper

class JiraTimer(TimerInterface):
    def __init__(self, name="Jira", priority=0, start_complete=False, time_work=60, 
                 time_break_short=5, time_break_long=60, sessions=3, iteration=1,
                 status_work="#[fg=#282828]#[bg=#427b58]#[bold] ",
                 status_done="#[fg=#282828]#[bg=#427b58]#[bold] ", notify=True,
                 cmds=["ACK", "MENU", "START", "STOP", "PAUSE", "RESUME", "SET", "TASKS"], state="idle"):
        self._name = name
        self._priority = priority
        self._start_complete = start_complete
        self._time_work = time_work
        self._time_break_short = time_break_short
        self._time_break_long = time_break_long
        self._time_end = 0
        self._sessions = sessions
        self._iteration = iteration
        self._status_work = status_work
        self._status_done = status_done
        self._notify = notify
        self._cmds = cmds
        self._is_enabled = False
        self._task = None
        self._restore_state = None
        self._restore_time = None
        if state == "idle" and self.start_complete:
            self._state = "done"
            self._status = status_done
        else:
            self._state = state
            self._status = ""
        with open(f"{tmux_helper.get_plugin_dir()}/scripts/jira.key", "r") as f:
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
        return self._time_end

    @property
    def sesssions(self) -> int:
        return self._sessions

    @property
    def iteration(self) -> int:
        return self._iteration

    @property
    def status(self) -> str: 
        if self.state == "idle":
            self._status = ""
        elif self.state == "working":
            self._status = f"{self.status_work} {self.iteration}/{self.sesssions} {self.time_left}"
        elif self.state == "short_break":
            self._status = f"{self.status_done} {self.time_left}"
        elif self.state == "long_break":
            self._status = f"{self.status_done} {self.time_left}"
        elif self.state == "paused":
            if self.restore_state in ["short_break", "long_break"]:
                self._status = f"{self.status_done} {self.time_left}"
            elif self.restore_state == "working":
                self._status = f"{self.status_work} {self.time_left}"
            else:
                raise Exception(f"Unknown timer state when getting paused status: {self.state}")
        else:
            raise Exception(f"Unknown timer state when getting status: {self.state}")

        return self._status

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
    def task(self) -> str|None:
        return self._task

    @property
    def restore_state(self) -> str|None:
        return self._restore_state

    @property
    def restore_time(self) -> int|None:
        return self._restore_time

    @property
    def is_enabled(self) -> bool:
        if self.state in ["working", "long_break", "short_break", "paused"]:
            self._is_enabled = True
        else:
            self._is_enabled = False

        return self._is_enabled

    @property
    def state(self) -> str:
        return self._state

    def gen_menu(self):
        options = []
        if self.state == "idle" or self.state == "done":
            options.append(tmux_helper.menu_add_option("Start", "t", f"run-shell \"{tmux_helper.get_plugin_dir()}/scripts/tmux_pytimer.py START --timer {self.name}\""))
        elif self.state == "paused":
            options.append(tmux_helper.menu_add_option("Resume", "t", f"run-shell \"{tmux_helper.get_plugin_dir()}/scripts/tmux_pytimer.py RESUME --timer {self.name}\""))
            options.append(tmux_helper.menu_add_option("Stop", "x", f"run-shell \"{tmux_helper.get_plugin_dir()}/scripts/tmux_pytimer.py STOP --timer {self.name}\""))
        elif self.state == "working":
            options.append(tmux_helper.menu_add_option("Pause", "t", f"run-shell \"{tmux_helper.get_plugin_dir()}/scripts/tmux_pytimer.py PAUSE --timer {self.name}\""))
            options.append(tmux_helper.menu_add_option("Stop", "x", f"run-shell \"{tmux_helper.get_plugin_dir()}/scripts/tmux_pytimer.py STOP --timer {self.name}\""))
        else:
            raise Exception(f"Unknown state when generating timer menu for {self.name}: {self.state}") 

        options.append(tmux_helper.menu_add_option("", "", ""))
        options.append(tmux_helper.menu_add_option("Set Task", "", f"run-shell \"{tmux_helper.get_plugin_dir()}/scripts/tmux_pytimer.py TASKS --timer {self.name}\""))

        tmux_helper.menu_create(self.name, "R", "S", options)

    def pause(self):
        if self.state not in ["working", "short_break", "long_break"]:
            raise Exception(f"Unkown timer state for pause: {self.state}")

        self._restore_state = self.state
        self._state = "paused"
        self._restore_time = self.time_end - int(datetime.now().strftime("%s"))

        self.write_status()
        self.update()
        tmux_helper.refresh()

    def resume(self):
        if self.state != "paused":
            raise Exception(f"Unkown timer state for resume: {self.state}")

        if self.restore_state not in ["working", "short_break", "long_break"]:
            raise Exception(f"Unkown timer restore state: {self.restore_state}")

        if self.restore_time == None:
            raise Exception(f"Trying to resume {self.name}, but restore_time is set to None")

        self._state = self.restore_state
        self._time_end = int(datetime.now().strftime("%s")) + self.restore_time
        self._restore_state = None
        self._restore_time = None

        self.write_status()
        self.update()
        tmux_helper.refresh()


    def start(self):
        #if self.task == None:
        #    self.gen_tickets_menu()

        if self.state == "idle":
            self._time_end = int(datetime.now().strftime("%s")) + (self.time_work * 60)
            self._state = "working"
        elif self.state == "working":
            # Long break
            if self.iteration >= self.sesssions:
                self._time_end = int(datetime.now().strftime("%s")) + (self.time_break_long * 60)
                self._state = "long_break"
            # Short break
            else:
                self._time_end = int(datetime.now().strftime("%s")) + (self.time_break_short * 60)
                self._state = "short_break"
        elif self.state == "short_break":
            self._time_end = int(datetime.now().strftime("%s")) + (self.time_work * 60)
            self._state = "working"
        elif self.state == "long_break":
            self._time_end = int(datetime.now().strftime("%s")) + (self.time_work * 60)
            self._state = "working"
        else:
            raise Exception(f"Unknown timer state for start: {self.state}")

        self.write_status()
        self.update()
        tmux_helper.refresh()

    def stop(self):
        self._state = "idle"
        self._iteration = 1
        self._time_end = 0

        self.write_status()
        self.update()
        tmux_helper.refresh()
    
    def read_status(self):
        try:
            with open(f"/tmp/tmux-pytimer/{self.name}.json", "r") as f:
                status = json.load(f)
        except:
            raise Exception(f"Unable to access {self.name} status file")

        try:
            self._time_end = status["time_end"]
            self._iteration = status["iteration"]
            self._state = status["state"]
        except:
            raise Exception(f"Unable to read status {self.name} status file")

    def write_status(self):
        try:
            with open(f"/tmp/tmux-pytimer/{self.name}.json", "w+") as f:
                status = {
                    "time_end": self.time_end,
                    "time_left": self.time_left,
                    "iteration": self.iteration,
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


    def update(self) -> str:
        self.read_status()

        if int(datetime.now().strftime("%s")) >= self.time_end:
            if self.state == "working":
                self._iteration += 1
                # Long break
                if self.iteration > self.sesssions:
                    self._time_end = int(datetime.now().strftime("%s")) + (self.time_break_long * 60)
                    self._state = "long_break"
                    tmux_helper.popup_create(self.name, "Session finished, take a long break")
                else:
                    self._time_end = int(datetime.now().strftime("%s")) + (self.time_break_short * 60)
                    self._state = "short_break"
                    tmux_helper.popup_create(self.name, "Session finished, take a short break")
            elif self.state == "short_break":
                self._time_end = int(datetime.now().strftime("%s")) + (self.time_work * 60)
                self._state = "working"
                tmux_helper.popup_create(self.name, "Break finished, get back to work")
            elif self.state == "long_break":
                self._iteration = 1
                self._time_end = int(datetime.now().strftime("%s")) + (self.time_work * 60)
                self._state = "working"
                tmux_helper.popup_create(self.name, "Break finished, get back to work")
        elif self.state == "paused":
            if self.restore_time == None:
                raise Exception(f"restore_time of {self.name} is set to None, but is currently paused")

            self._time_end = int(datetime.now().strftime("%s")) + self.restore_time

        self.write_status()

        return self.status
