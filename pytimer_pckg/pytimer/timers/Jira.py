import os
import json
import logging
from datetime import datetime, date
import subprocess
from jira_lib import Jira, JiraFields
from .. import TmuxHelper
from .states import JiraStates

class JiraTimer:
    # add_comment seems to be broken again...
    # TODO merge all task properties into one dictionary
    # TODO implement loading properties from file

    # TODO add timeout to popup so that timers continue if away
        # TODO Add a carry_over time property that uses the exta time passed the session in a future break or subtract from a future work session. Maybe use the tmux display-popup -E option.
    def __init__(self, name="Jira", priority=0, time_work=60, 
                 time_break_short=5, time_break_long=60, sessions=3, iteration=1, notify=True, verify_tls=True):
        self.name = name
        self.priority = priority
        self.time_work = time_work*60
        self.time_break_short = time_break_short*60
        self.time_break_long = time_break_long*60
        self.time_end = 0
        self.time_start = 0
        self.sessions = sessions
        self.iteration = iteration
        self.notify = notify
        self.cmds = ["ACK", "MENU", "START", "STOP", "PAUSE", "RESUME", "SET", "TASKS"]
        self.task = None
        self.task_time = 0
        self.task_code = ""
        self.verify_tls=verify_tls

        os.makedirs(f"{TmuxHelper.get_plugin_dir()}/jira", exist_ok=True)

        with open(f"{TmuxHelper.get_plugin_dir()}/scripts/jira.key", "r") as f:
            self.jira = Jira(f.read().rstrip(), verify_tls=verify_tls)

        self.state = JiraStates.Idle(self)

        self.write_status()

    def get_status(self) -> str: 
        return self.state.status

    def gen_menu(self):
        TmuxHelper.menu_create(self.name, "R", "S", self.state.menu_options)

    def pause(self):
        self.state = self.state.pause(self)

        self.write_status()
        self.update()
        TmuxHelper.refresh()

    def resume(self):
        self.state.next(self)

        self.write_status()
        self.update()
        TmuxHelper.refresh()

    def start(self):
        if self.task == None:
            self.gen_tickets_menu()

        self.state.next(self)

        self.write_status()
        self.update()
        TmuxHelper.refresh()

    def stop(self):
        self.log_work()
        if self.task != None:
            self.comment()
        self.state = self.state.stop(self)

        self.write_status()
        self.update()
        TmuxHelper.refresh()

    def set_task(self, task_key):
        if self.task != None:
            self.task = task_key
            self.comment()
        else:
            self.task = task_key

        tickets = self.jira.get_tickets(f"{JiraFields.ASSIGNEE} = 'M83393' " \
                f"and {JiraFields.KEY} = {self.task}", 
                fields=[JiraFields.SUMMARY, JiraFields.CHARGE_CODE])
        tickets = self.sanitize_tickets(tickets)

        if len(tickets) != 1:
            logging.critical(f"Unable to get charge code for {self.task}")
        else:
            tickets = tickets[0]
            self.task_code = tickets[JiraFields.CHARGE_CODE]

        self.state.update(self)

    def comment(self):
        cmd = f"{TmuxHelper.get_plugin_dir()}/scripts/add_comment.py \"{self.name}\" \"{self.task}\""
        cmd = cmd.split(' ')
        subprocess.run(cmd)

    #TODO
    def log_work(self):
        if self.task == None:
            return

        self.task_time += int(datetime.now().strftime("%s")) - self.time_start
        if os.path.exists(f"{TmuxHelper.get_plugin_dir()}/jira/{self.name}-work-log.json"):
            with open(f"{TmuxHelper.get_plugin_dir()}/jira/{self.name}-work-log.json", "r") as f:
                try:
                    work_log = json.load(f)
                    if str(date.today()) not in work_log:
                        work_log[str(date.today())] = {}

                    work_log[str(date.today())][self.task] = {"task": self.task, "charge_code": self.task_code, "task_time": self.task_time}
                except:
                    work_log = {}
                    work_log[str(date.today())] = {}
                    work_log[str(date.today())][self.task] = {"task": self.task, "charge_code": self.task_code, "task_time": self.task_time}
        else:
            work_log = {}
            work_log[str(date.today())] = {}
            work_log[str(date.today())][self.task] = {"task": self.task, "charge_code": self.task_code, "task_time": self.task_time}

        with open(f"{TmuxHelper.get_plugin_dir()}/jira/{self.name}-work-log.json", "w") as f:
            json.dump(work_log, f, indent=2)

    def verify_state(self, state):
        if type(state["name"]) != str:
            return False

        if type(state["properties"]) != dict:
            return False

        mod_classes = list(JiraStates.STATES.keys())
                                                                      
        if state["name"] not in mod_classes:
            return False
                                                                      
        # Returns an instantiation of the matched class
        return JiraStates.STATES[state["name"]](self)
                                                                      

    def verify_time_end(self, time_end):
        if type(time_end) != int:
            return False

        return time_end


    def verify_time_start(self, time_start):
        if type(time_start) != int:
            return False

        if int(datetime.now().strftime("%s")) < time_start:
            return False

        return time_start


    def verify_iteration(self, iteration):
        if type(iteration) != int:
            return False

        if iteration > self.sessions or iteration <= 0:
            return False

        return iteration

    def read_status(self):
        try:
            with open(f"/tmp/tmux-pytimer/{self.name}.json", "r") as f:
                status = json.load(f)
        except Exception as e:
            raise Exception(f"Unable to access {self.name} status file")

        fail_flag = False
        try:
            # Validate time_end
            time_end = self.verify_time_end(status["time_end"])
            if time_end != False:
                self.time_end = time_end
            else:
                fail_flag = True

            # Validate time_start
            time_start = self.verify_time_start(status["time_start"])
            if time_start != False:
                self.time_start = time_start
            else:
                fail_flag = True

            # Validate iteration
            iteration = self.verify_iteration(status["iteration"])
            if iteration != False:
                self.iteration = iteration
            else:
                fail_flag = True

            # Validate state
            state = self.verify_state(status["state"])
            if state != False:
                if str(state) != str(self.state):
                    self.state = state
                else:
                    del state

                self.state.restore_properties(self, status["state"]["properties"])
            else:
                fail_flag = True

        except:
            raise Exception(f"Unable to read status {self.name} status file")
        finally:
            if fail_flag:
                self.state = JiraStates.Idle(self)
                self.state.stop(self)

    def write_status(self):
        try:
            with open(f"/tmp/tmux-pytimer/{self.name}.json", "w+") as f:
                status = {
                    "time_end": self.time_end,
                    "time_start": self.time_start,
                    "iteration": self.iteration,
                    "state": {
                        "name": str(self.state),
                        "properties": self.state.get_properties()
                    }
                }

                json.dump(status, f, indent=2)
        except Exception as e:
            raise Exception(f"Unable to write {self.name} status file")

    def sanitize_tickets(self, tickets) -> list[dict]:
        for ticket in tickets:
            ticket[JiraFields.SUMMARY] = ticket["fields"][JiraFields.SUMMARY]
            ticket[JiraFields.CHARGE_CODE] = ticket["fields"][JiraFields.CHARGE_CODE]
            ticket.pop("expand")
            ticket.pop("fields")

        return tickets


    def gen_tickets_menu(self):
        tickets = self.jira.get_tickets(f"{JiraFields.ASSIGNEE} = 'M83393' " \
                f"and {JiraFields.STATUS} != 'Done' " \
                f"and {JiraFields.PROJECT} = 'MDT' "\
                f"and {JiraFields.SPRINT} in openSprints()", 
                fields=[JiraFields.SUMMARY, JiraFields.CHARGE_CODE])
        tickets = self.sanitize_tickets(tickets)

        options = []
        for ticket in tickets:
            options.append(TmuxHelper.menu_add_option(
                f"{ticket['key']}: {ticket['summary']}",
                "",
                f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py SET --timer {self.name} --value {ticket['key']}\"")
            )

        TmuxHelper.menu_create("Tickets", "C", "C", options)


    def update(self) -> str:
        self.read_status()

        now = int(datetime.now().strftime("%s"))
        self.task_time = now - self.time_start

        if str(self.state) in ["Working", "BreakLong", "BreakShort"]:
            self.log_work()
            if now >= self.time_end:
                self.state.next(self)
        else:
            self.state.update(self)

        self.write_status()

        return f"{self.state.status} "
