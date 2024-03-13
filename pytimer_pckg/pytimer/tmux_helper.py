import os
import subprocess

def get_plugin_dir():
    path = os.path.dirname(os.path.realpath(__file__))
    path = path.split('/')[:-3]
    path = '/'.join(path)

    return path


def menu_add_option(name, key, cmd):
    entry = [name, key, cmd]

    return entry


def get_terminal_size():
    term_height = subprocess.run(["/usr/local/bin/tmux", "display-message", "-p", "#{window_height}"], capture_output=True)
    term_width = subprocess.run(["/usr/local/bin/tmux", "display-message", "-p", "#{window_width}"], capture_output=True)

    term_height = term_height.stdout.rstrip()
    term_height = int(term_height)
    term_width = term_width.stdout.rstrip()
    term_width = int(term_width)

    return term_height, term_width


def message_create(msg, delay=5000):
    cmd = ["/usr/local/bin/tmux", "display-message", "-d", f"{delay}", msg]
    subprocess.run(cmd)

    return 0


def popup_create(title, msg):
    term_height, term_width = get_terminal_size()
    if term_height % 2 == 0:
        term_height += 1

    if term_width %2 == 0:
        term_width += 1

    term_height = int(term_height/2) + 1
    term_width = int(term_width/2) + 1
    vert_padding = '\n'*(int((term_height/2)) - 1)

    cmd = f"/usr/local/bin/tmux display-popup -s fg=#d79921,align=centre -h {term_height} -w {term_width} -t"
    cmd = cmd.split(' ')
    cmd.append(f"{title}")
    cmd.append(f"echo -n '{vert_padding}{msg.center(term_width)}'")

    subprocess.run(cmd)

    return 0


def menu_create(title, pos_x, pos_y, options):
    cmd = f"/usr/local/bin/tmux display-menu -y {pos_y} -x {pos_x} -T"
    cmd = cmd.split(' ')
    cmd.append(title)

    for option in options:
        cmd += option

    subprocess.run(cmd)
