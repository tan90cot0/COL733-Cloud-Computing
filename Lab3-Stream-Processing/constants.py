from typing import Final

LOGFILE: Final[str] = "/tmp/wc.log"
DONE: Final[str] = "DONE"

N_FILES: Final[int] = 7
N_NORMAL_WORKERS: Final[int] = 7
N_CRASHING_WORKERS: Final[int] = 0
N_SLEEPING_WORKERS: Final[int] = 2
N_CPULIMIT: Final[int] = 30
N_WORKERS: Final[int] = N_NORMAL_WORKERS + N_CRASHING_WORKERS + N_SLEEPING_WORKERS

IN: Final[bytes] = b"files"
FNAME: Final[bytes] = b"fname"
COUNT: Final[bytes] = b"count"
LATENCY: Final[bytes] = b"latency"
