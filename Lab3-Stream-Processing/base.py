from __future__ import annotations

import logging
import os
import signal
import sys
from abc import abstractmethod, ABC
from threading import current_thread
from typing import Any, Final


class Worker(ABC):
  GROUP: Final = "worker"

  def __init__(self, **kwargs: Any):
    self.name = "worker-?"
    self.pid = -1
    self.crash = kwargs['crash'] if 'crash' in kwargs else False
    self.slow = kwargs['slow'] if 'slow' in kwargs else False
    self.cpulimit = kwargs['limit'] if 'slow' in kwargs and 'limit' in kwargs else 100

  def create_and_run(self, **kwargs: Any) -> None:
    pid = os.fork()
    assert pid >= 0
    if pid == 0:
      # Child worker process
      self.pid = os.getpid()
      self.name = f"worker-{self.pid}"
      thread = current_thread()
      thread.name = self.name
      logging.info(f"Starting")
      self.run(**kwargs)
      sys.exit()
    else:
      self.pid = pid
      self.name = f"worker-{pid}"

  @abstractmethod
  def run(self, **kwargs: Any) -> None:
    raise NotImplementedError

  def kill(self) -> None:
    logging.info(f"Killing {self.name}")
    os.kill(self.pid, signal.SIGKILL)
