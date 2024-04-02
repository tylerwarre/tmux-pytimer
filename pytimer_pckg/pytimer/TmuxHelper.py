import os
import subprocess

def get_plugin_dir():
    path = os.path.dirname(os.path.realpath(__file__))
    path = path.split('.tmux')[0]
    path = f"{path}.tmux/plugins/tmux-pytimer"

    return path


def menu_add_option(name, key, cmd):
    entry = [name, key, cmd]

    return entry


def get_tmux_option(key):
    cmd = ["/usr/local/bin/tmux", "show-option", "-gqv", f"{key}"]

    result = subprocess.run(cmd, capture_output=True)
    
    return result.stdout.decode().rstrip()


def set_tmux_option(key, value):
    cmd = ["/usr/local/bin/tmux", "set-option", "-g", f"{key}", f"{value}"]

    subprocess.run(cmd)


def get_terminal_size():
    term_height = subprocess.run(["/usr/local/bin/tmux", "display-message", "-p", "#{window_height}"], capture_output=True)
    term_width = subprocess.run(["/usr/local/bin/tmux", "display-message", "-p", "#{window_width}"], capture_output=True)

    term_height = term_height.stdout.rstrip()
    term_height = int(term_height)
    term_width = term_width.stdout.rstrip()
    term_width = int(term_width)

    return term_height, term_width


def message_create(msg, delay=5000):
    cmd = ["/usr/local/bin/tmux", "display-message", "-d", f"{delay}", f"\"{msg}\""]
    subprocess.run(cmd)

    return 0


def popup_create(title, msg, x_pos="C", y_pos="C", height=50, width=50, input=False):
    term_height, term_width = get_terminal_size()
    if term_height % 2 == 0:
        term_height += 1

    if term_width % 2 == 0:
        term_width += 1

    term_height = int(term_height * (height/100)) + 1
    term_width = int(term_width * (width/100)) + 1
    if input:
        cmd = f"/usr/local/bin/tmux display-popup -S fg=#fe8019 -h {term_height} -w {term_width} -x {x_pos} -y {y_pos} -E"

        cmd = cmd.split(' ')
        cmd += ["-T", f"#[fg=#ebdbb2]\"{title}\""]
        cmd.append(f"read response; \"{msg}\"")
    else:
        vert_padding = '\n'*(int((term_height/2)) - 1)
        cmd = f"/usr/local/bin/tmux display-popup -S fg=#fe8019,align=centre -h {term_height} -w {term_width} -x {x_pos} -y {y_pos}"

        cmd = cmd.split(' ')
        cmd += ["-T", f"#[fg=#ebdbb2]\"{title}\""]
        cmd += ["echo", "-n", f"\a\a\a{vert_padding}{msg.center(term_width)}"]

    subprocess.run(cmd)

    return


def menu_create(title, pos_x, pos_y, options):
    cmd = f"/usr/local/bin/tmux display-menu -y {pos_y} -x {pos_x} -T"
    cmd = cmd.split(' ')
    cmd.append(title)

    for option in options:
        cmd += option

    subprocess.run(cmd)


def refresh():
    cmd = "tmux refresh-client -S"
    cmd = cmd.split(' ')

    subprocess.run(cmd)
