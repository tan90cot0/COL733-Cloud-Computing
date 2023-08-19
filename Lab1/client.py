import glob
import logging
import os
import signal
import sys
from threading import current_thread

from constants import LOGFILE, N_WORKERS, DATA_PATH
from worker import WcWorker
from mrds import MyRedis

workers: list[WcWorker] = []
def sigterm_handler(signum, frame):
  logging.info('Killing main process!')
  for w in workers:
    w.kill()
  sys.exit()


if __name__ == "__main__":
  # Clear the log file
  open(LOGFILE, 'w').close()
  logging.basicConfig(# filename=LOGFILE,
                      level=logging.DEBUG,
                      force=True,
                      format='%(asctime)s [%(threadName)s] %(levelname)s: %(message)s')
  thread = current_thread()
  thread.name = "client"
  logging.debug('Done setting up loggers.')

  rds = MyRedis()

  for file in glob.glob(DATA_PATH):
    rds.add_file(file)

  signal.signal(signal.SIGTERM, sigterm_handler)
  for i in range(N_WORKERS):
    workers.append(WcWorker(rds=rds))

  for w in workers:
    w.create_and_run(rds=rds)

  logging.debug('Created all the workers')
  while True:
    try:
      pid_killed, status = os.wait()
      logging.info(f"Worker-{pid_killed} died with status {status}!")
    except:
      break

  for word, c in rds.top(3):
    logging.info(f"{word.decode()}: {c}")