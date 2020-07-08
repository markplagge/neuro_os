from enum import IntFlag


class PROC_STATE(IntFlag):
    WAITING = 1
    RUNNING = 2
    COMPLETE = 4
    PRE_WAIT = 8
    NO_OP = 0

class SCHEDULER_STATE(IntFlag):
        ADD = 1
        FULL = 2

class PROC_MESSAGE(IntFlag):
        SHOULD_START = 1
        SHOULD_END = 2
        SHOULD_WAIT = 4
        NO_CHANGE = 0
