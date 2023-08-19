import logging
from typing import Any

from base import Worker
from constants import FNAME
from mrds import MyRedis
from constants import IN, N_WORKERS, COUNT
import pandas as pd
# from tqdm import tqdm

class WcWorker(Worker):

  def run(self, **kwargs: Any) -> None:
    rds: MyRedis = kwargs['rds']

    path, res = rds.get_file(self.GROUP, self.name, IN)
    while res:
      logging.info(f"Worker started on path {path}")
      count_dict = {}
      tweets = pd.read_csv(path, lineterminator='\n')
      tweets["text"] = tweets["text"].astype(str)

      for text in tweets.loc[:,"text"]:
        if text == '\n':
            continue
        for word in text.split(" "):
            if word not in count_dict:
                count_dict[word] = 0
            count_dict[word] = count_dict[word] + 1
      
      for word, cnt in count_dict.items():
        rds.update_cnt(cnt, word)
      logging.info("Counting Done")
      path, res = rds.get_file(self.GROUP, self.name, IN)
