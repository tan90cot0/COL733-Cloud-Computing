import logging
import os
import re
import sys
from typing import Any

import pandas as pd

from english import load_words
from base import Worker
from constants import FNAME
from mrds import MyRedis

word_set = load_words()

class WcWorker(Worker):
  def run(self, **kwargs: Any) -> None:
    rds: MyRedis = kwargs['rds']
    processed_items = 0

    while True:

      id, data = rds.read(self)
      if not id:
        # sleep(.2)
        # logging.debug("Did not get a file. Try again.")
        continue

      logging.debug(f"Got {id} {data}")

      if (processed_items == 5) and self.crash:
        logging.critical(f"CRASHING!")
        sys.exit()

      if (processed_items == 5) and self.slow:
        logging.critical(f"Sleeping!")
        os.system(f"sudo cpulimit -p {self.pid} --limit {self.cpulimit} --background")

      fname: str = data[FNAME].decode()
      wc: dict[str, int] = {}

      df = pd.read_csv(fname,lineterminator='\n')
      df["text"] = df["text"].astype(str)
      for text in df.loc[:,"text"]:
        if text == '\n':
          continue

        for word in text.split(" "):
          word = re.sub('[^a-zA-Z]', '', word)
          if word not in word_set:
            continue
          if word not in wc:
            wc[word] = 0

          wc[word] = wc[word] + 1

      rds.write(id, wc)
      processed_items += 1
