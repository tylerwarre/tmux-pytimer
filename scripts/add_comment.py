#!/home/m83393/.tmux/tmux-venv/bin/python3

import os
import json
import argparse
from datetime import datetime
from jira_lib import Jira
from pytimer import TmuxHelper

# TODO Make comment argument optional and when not present create a display-popup that call this script with the input gathered. Must update JiraStates to use this method instead

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("task")
    parser.add_argument("comment")
    args = parser.parse_args()

    if type(args.comment) != str:
        return

    if type(args.task) != str:
        return

    if len(args.comment) == 0:
        return
    try:
        with open(f"{TmuxHelper.get_plugin_dir()}/scripts/jira.key", "r") as f:
            jira = Jira(f.read().rstrip(), verify_tls=False)

        jira.add_comment(args.task, args.comment)
    except:
        if os.path.exists("/tmp/tmux-pytimer/jira-comments.json"):
            with open("/tmp/tmux-pytimer/jira-comments.json", "r") as f:
                try:
                    comments = json.load(f)
                    comments.append({"timestamp": str(datetime.now()),"key": args.task, "comment": args.comment})
                except:
                    comments = [{"timestamp": str(datetime.now()),"key": args.task, "comment": args.comment}]
        else:
                comments = [{"timestamp": str(datetime.now()),"key": args.task, "comment": args.comment}]

        with open("/tmp/tmux-pytimer/jira-comments.json", "w") as f:
            json.dump(comments, f, indent=2)

if __name__ == "__main__":
    main()
