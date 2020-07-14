debug_print = False
has_run_once = False


def d_print(*args, **kwargs):
    global debug_print
    global has_run_once

    if not has_run_once:
        m = "enabled" if debug_print else "disabled"
        print(f"Debug Print Mode is {m}")
        has_run_once = True

    if debug_print:
        print(*args, **kwargs)


