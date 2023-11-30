from typing import Final

LOGFILE: Final[str] = "/tmp/wc.log"
DONE: Final[str] = "DONE"

DATA_PATH: Final[str] = '/home/baadalvm/data/split2'
N_FILES: Final[int] = 7
N_NORMAL_WORKERS: Final[int] = 9
IS_RAFT: Final[bool] = True
RAFT_PORTS: Final[list] = ["6379", "6380", "6381"] 
RAFT_CRASH_PORT: Final[int] = "6379" # In the case of RAFT, SHUTDOWN the instance running at this port.
RAFT_JOIN_PORT: Final[int] = "6380"
N_WORKERS: Final[int] = N_NORMAL_WORKERS

IN: Final[bytes] = b"files"
FNAME: Final[bytes] = b"fname"
COUNT: Final[bytes] = b"count"
LATENCY: Final[bytes] = b"latency"
FLAG: Final[bytes] = b"done"
